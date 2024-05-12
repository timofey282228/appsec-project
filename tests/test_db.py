import pytest

from appsec_project.model import KeypressModel, Reference
from appsec_project.storage import Storage, LoginResult


DB_NAME = "db.db"


def test_create(tmp_path):
    db_path = tmp_path / DB_NAME
    ms = Storage(db_path)


@pytest.fixture
def empty_model_storage(tmp_path):
    db_path = tmp_path / DB_NAME
    return Storage(db_path)


def test_set_model(empty_model_storage):
    ms = empty_model_storage
    ms.set_model(
        "TestUser",
        KeypressModel(
            auth_phrase="testphrase",
            references=[
                Reference(expectile=104001840.0, variation=0.22817294373314803)
            ],
        ),
    )


@pytest.fixture
def w_entry_model_storage(empty_model_storage) -> Storage:
    empty_model_storage.set_model(
        "TestUser",
        KeypressModel(
            auth_phrase="testphrase",
            references=[
                Reference(expectile=104001840.0, variation=0.22817294373314803)
            ],
        ),
    )

    return empty_model_storage


def test_update_existing(w_entry_model_storage):
    assert (
        w_entry_model_storage.set_model(
            "TestUser",
            KeypressModel(
                auth_phrase="testphrase",
                references=[
                    Reference(
                        expectile=109002916.66666667, variation=0.2646791252130323
                    )
                ],
            ),
        )
        == True
    )


def test_expand_existing(w_entry_model_storage):
    w_entry_model_storage.update_model(
        "TestUser",
        KeypressModel(
            auth_phrase="testphrase",
            references=[
                Reference(expectile=109002916.66666667, variation=0.2646791252130323)
            ],
        ),
    )

def test_insert_stats(w_entry_model_storage):
    w_entry_model_storage.update_stats(
        "TestUser",
        True,
        LoginResult.Accepted
    )

    w_entry_model_storage.update_stats(
        "TestUser",
        True,
        LoginResult.Rejected
    )

    w_entry_model_storage.update_stats(
        "TestUser",
        False,
        LoginResult.Rejected
    )

    w_entry_model_storage.update_stats(
        "TestUser",
        False,
        LoginResult.Rejected
    )

@pytest.fixture
def w_stats_model_storage(w_entry_model_storage) -> Storage:
    w_entry_model_storage.update_stats(
        "TestUser",
        True,
        LoginResult.Accepted
    )

    w_entry_model_storage.update_stats(
        "TestUser",
        True,
        LoginResult.Accepted
    )

    w_entry_model_storage.update_stats(
        "TestUser",
        True,
        LoginResult.Rejected
    )

    w_entry_model_storage.update_stats(
        "TestUser",
        False,
        LoginResult.Accepted
    )

    w_entry_model_storage.update_stats(
        "TestUser",
        False,
        LoginResult.Rejected
    )

    w_entry_model_storage.update_stats(
        "TestUser",
        False,
        LoginResult.Accepted
    )

    return w_entry_model_storage

def test_update_stats(w_stats_model_storage):
    w_stats_model_storage.update_stats(
        "TestUser",
        False,
        LoginResult.Rejected
    )

def test_far_frr(w_stats_model_storage):
    print(w_stats_model_storage.get_far())
    print(w_stats_model_storage.get_frr())