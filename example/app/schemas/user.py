from pydantic import BaseModel
from typing import Literal


class CurrentUser(BaseModel):
    username: str
    role:  Literal["customer", "agent", "admin"] = "customer"

