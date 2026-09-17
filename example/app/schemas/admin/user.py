from pydantic import BaseModel
from typing import Literal


class CurrentUser(BaseModel):
    user_id: str
    role:  Literal["customer", "agent", "admin"] = "customer"

