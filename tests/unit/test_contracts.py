import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from afterclick.api import Patch
from afterclick.infrastructure.db import Database, digest


@given(st.dictionaries(st.text(), st.integers()))
def test_canonical_hash_is_key_order_independent(value):
    assert digest(value) == digest(dict(reversed(list(value.items()))))


@pytest.mark.parametrize("schema", ["public", "flowboard; DROP DATABASE x", "ac_bad-name"])
def test_schema_identifiers_reject_unsafe_values(schema):
    with pytest.raises(ValueError):
        Database(schema)


def test_payload_rejects_hidden_state_write():
    with pytest.raises(ValidationError):
        Patch(expected_version=1, operation_id="a", changes={"ready": True})
