import logging

from typing import *
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class Reference(BaseModel):
    expectile: float
    variation: float

    def __str__(self):
        return f"({self.expectile}, {self.variation})"

    def __repr__(self):
        return f"({self.expectile}, {self.variation})"


class KeypressModel(BaseModel):
    auth_phrase: str
    references: list[Reference]
