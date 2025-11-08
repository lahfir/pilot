"""
Pydantic schemas for structured task outputs.
"""

from pydantic import BaseModel, Field
from typing import Optional


class TaskCompletionOutput(BaseModel):
    """
    Structured output for completed tasks.
    Forces agents to return properly typed results.
    """

    task_completed: bool = Field(
        ..., description="Whether the task was successfully completed"
    )
    result: str = Field(..., description="The result or output from the task execution")
    actions_taken: str = Field(
        ..., description="Summary of actions taken to complete the task"
    )
    final_value: Optional[str] = Field(
        None, description="Final value if task involves calculation or data extraction"
    )
    error: Optional[str] = Field(None, description="Error message if task failed")
