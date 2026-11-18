from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from afterclick.api import create_app
from afterclick.domain import seed
from afterclick.infrastructure.db import Database


@pytest.fixture
def db():
    database = Database("ac_test_" + uuid4().hex)
    database.migrate()
    seed(database)
    yield database
    database.drop_experiment()


@pytest.fixture
def client(db):
    with TestClient(create_app(db)) as client:
        yield client
