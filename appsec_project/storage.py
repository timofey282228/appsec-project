import os
import logging
import enum

from .model import *
from sqlite3 import *

LIMIT = 100

logger = logging.getLogger(__name__)


class LoginResult(enum.Enum):
    Accepted = enum.auto()
    Rejected = enum.auto()


class Storage:
    def __init__(self, file) -> None:
        if not os.path.exists(file):
            self.connection = connect(file)
            self.connection.execute(
                "CREATE TABLE Users (username TEXT CONSTRAINT UsersPrimary PRIMARY KEY, model TEXT)"
            )
            self.connection.execute(
                """CREATE TABLE Stats (
                    username TEXT,
                    claims_legit BOOLEAN,
                    accepted INTEGER,
                    rejected INTEGER,
                    CONSTRAINT StatsPrimary PRIMARY KEY (
                        username, 
                        claims_legit
                        )
                    )"""
            )
        else:
            self.connection = connect(file)

    def set_model(self, username: str, model: KeypressModel) -> bool:
        updated = False

        # apply limit
        if len(model.references) > LIMIT:
            model.references = model.references[len(model.references) - LIMIT :]

        try:
            self.connection.execute(
                "INSERT INTO Users VALUES (?, ?)", (username, model.model_dump_json())
            )

        except IntegrityError as e:
            if e.sqlite_errorcode == 1555:
                updated = True

            self.connection.execute(
                "UPDATE Users SET model = ? WHERE username = ?",
                (model.model_dump_json(), username),
            )

        self.connection.commit()
        logging.debug(f"Model of {username} set")
        return updated

    def update_model(self, username: str, reference: Reference):
        model_str = self.connection.execute(
            "SELECT model FROM Users WHERE username = ?", (username,)
        ).fetchone()[0]
        model = KeypressModel.model_validate_json(model_str)
        model.references.append(reference)
        if len(model.references) > LIMIT:
            model.references.pop(0)

        self.connection.execute(
            "UPDATE Users SET model = ? WHERE username = ?",
            (model.model_dump_json(), username),
        )

        self.connection.commit()
        logging.debug(f"Model of {username} updated")

    def get_model(self, username: str) -> KeypressModel:
        model = self.connection.execute(
            "SELECT * FROM Users WHERE username = ?", (username,)
        ).fetchone()

        if model is not None:
            model = KeypressModel.model_validate_json(model[1])
        else:
            logger.debug("Tried reading inexistent user")

        return model

    def update_stats(self, username: str, claims_legit: bool, result: LoginResult):
        match result:
            case LoginResult.Accepted:
                cursor = self.connection.execute(
                    """INSERT INTO Stats VALUES (?, ?, ?, ?)
                        ON CONFLICT DO
                            UPDATE SET accepted = accepted + 1
                                WHERE username = ? AND claims_legit = ?""",
                    (username, claims_legit, 1, 0, username, claims_legit),
                )

            case LoginResult.Rejected:
                cursor = self.connection.execute(
                    """INSERT INTO Stats VALUES (?, ?, ?, ?)
                        ON CONFLICT DO
                            UPDATE SET rejected = rejected + 1
                                WHERE username = ? AND claims_legit = ?""",
                    (username, claims_legit, 0, 1, username, claims_legit),
                )

        cursor.connection.commit()

    def get_frr(self):
        return self.connection.execute(
            """SELECT CAST(SUM(rejected) AS FLOAT) / CAST((SELECT SUM(accepted) + SUM(rejected) FROM Stats
                WHERE claims_legit = TRUE) AS FLOAT)
            FROM Stats WHERE claims_legit = TRUE"""
        ).fetchone()[0] or 0.0

    def get_far(self):
        return self.connection.execute(
            """SELECT CAST(SUM(accepted) AS FLOAT) / CAST((SELECT SUM(accepted) + SUM(rejected) FROM Stats
                WHERE claims_legit = FALSE) AS FLOAT)
            FROM Stats WHERE claims_legit = FALSE"""
        ).fetchone()[0] or 0.0
