"""Finite continuation on the existing CPU sandbox after a reader-path correction."""

import hashlib
import json
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "artifacts/research_runs/publication-20261126-linux-reproduction-v2"


def main():
    sandbox = modal.Sandbox.from_id(json.loads((RUN / "sandbox.json").read_text())["sandbox_id"])
    files = [
        ROOT / "research_ops/publication" / name
        for name in [
            "normalize.py",
            "verify_normalized.py",
            "analyze_existing.py",
            "obligation_audit.py",
            "verify_actuator.py",
        ]
    ]
    amendment = dict(
        reason=(
            "Reader-only relocation of old absolute trace inventory paths; "
            "no raw data, frozen source, outcomes or tests changed."
        ),
        files={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        max_seconds=480,
        provider_calls=0,
        model_calls=0,
        output="/result/corrected-v3",
    )
    (RUN / "portability-amendment.json").write_text(json.dumps(amendment, indent=2) + "\n")
    for p in files:
        sandbox.filesystem.copy_from_local(p, "/work/afterclick-v12/" + str(p.relative_to(ROOT)))
    script = """import subprocess,json,time,os
from pathlib import Path
out=Path('/result/corrected-v3');out.mkdir(exist_ok=False)
os.chdir('/work/afterclick-v12');os.environ['PYTHONPATH']=os.getcwd()
steps=[]
for name,args in [
('normalize',['--output',str(out/'normalized')]),
('verify_normalized',['--data',str(out/'normalized'),'--output',str(out/'verified')]),
('analyze_existing',['--data',str(out/'normalized'),'--output',str(out/'analysis')]),
('obligation_audit',['--data',str(out/'normalized'),'--output',str(out/'obligations')]),
('verify_actuator',['--run','artifacts/research_runs/v12-31-complex-controlled-enforcement-v1','--output',str(out/'actuator-verification')])]:
 t=time.time()
 p=subprocess.run(['python','-m','research_ops.publication.'+name,*args],
                  capture_output=True,text=True,timeout=360)
 (out/(name+'.log')).write_text(p.stdout+p.stderr)
 r=dict(name=name,returncode=p.returncode,elapsed=time.time()-t)
 steps.append(r);print(json.dumps(r),flush=True)
 if p.returncode:break
report=dict(complete=len(steps)==5,
 all_steps_passed=len(steps)==5 and all(s['returncode']==0 for s in steps),
 steps=steps,model_calls=0,provider_calls=0)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\\n')
"""
    (RUN / "corrected-run-source.py").write_text(script)
    sandbox.filesystem.write_text(script, "/input/corrected-run.py")
    process = sandbox.exec("python", "-u", "/input/corrected-run.py", timeout=480)
    with (RUN / "corrected-stdout.log").open("w") as f:
        for line in process.stdout:
            f.write(line)
            f.flush()
            print(line, end="", flush=True)
    (RUN / "corrected-stderr.log").write_text(process.stderr.read())
    process.wait()
    (RUN / "corrected-process.json").write_text(
        json.dumps(dict(returncode=process.returncode)) + "\n"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    if parser.parse_args().execute:
        state = json.loads((ROOT / "research_ops/publication/FINANCE_STATE.json").read_text())
        assert state["active"]["run_id"] == RUN.name
        assert not (RUN / "portability-amendment.json").exists(), "Completed continuation"
        main()
    else:
        print("Explicit --execute and an active reserved CPU lifecycle are required.")
