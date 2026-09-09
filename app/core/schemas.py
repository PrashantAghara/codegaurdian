from pydantic import BaseModel


class ReviewTriggerRequest(BaseModel):
    repo_full_name: str
    pr_number: int


class ReviewTriggerResponse(BaseModel):
    final_summary: str
    publish_result: dict | None = None
