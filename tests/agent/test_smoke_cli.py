import json
from dataclasses import asdict

import pytest

from afterclick.agent.modal_policy import Limits, ModalConfig
from afterclick.evaluation import modal_smoke
from tests.agent.test_modal_policy import visible


@pytest.mark.parametrize("live", [False, True])
def test_preparation_and_unapproved_live_never_invoke_provider(tmp_path, monkeypatch, live):
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "config": asdict(
                    ModalConfig("https://unconfigured.us-west.modal.direct", "unconfigured")
                ),
                "limits": asdict(Limits()),
            }
        )
    )
    task, observation, history = visible()
    inputs = tmp_path / "inputs.json"
    inputs.write_text(json.dumps([{"task": task, "observation": observation, "history": history}]))
    output = tmp_path / "output"
    argv = [
        "modal_smoke",
        "--config",
        str(config),
        "--inputs",
        str(inputs),
        "--output",
        str(output),
    ]
    if live:
        argv.append("--live")
    monkeypatch.setattr("sys.argv", argv)
    monkeypatch.setattr(modal_smoke, "source_manifest", lambda: {"test_only": True})

    def forbidden(*args, **kwargs):
        raise AssertionError("Preparation cannot instantiate a provider")

    monkeypatch.setattr(modal_smoke, "ModalPolicy", forbidden)
    if live:
        with pytest.raises(SystemExit) as error:
            modal_smoke.main()
        assert error.value.code == 2 and not output.exists()
    else:
        modal_smoke.main()
        metrics = json.loads((output / "metrics.json").read_text())
        assert metrics["status"] == "prepared_only" and metrics["live_model_calls"] == 0
        assert not (output / "model_calls.jsonl").read_text()
