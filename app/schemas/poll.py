from typing import Dict

from pydantic import BaseModel


class VoteRequest(BaseModel):
    option_id: str


class PollResults(BaseModel):
    poll_id: str
    results: Dict[str, int]
    served_via: str
