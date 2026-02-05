"""
Pydantic schemas for structured task outputs.
"""

import json
from typing import Optional, Any
from pydantic import BaseModel, Field, model_validator


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

    @model_validator(mode="before")
    @classmethod
    def coerce_invalid_payload(cls, payload: Any) -> Any:
        """
        Convert non-compliant agent payloads into the typed schema instead of raising validation errors.
        """
        if not isinstance(payload, dict):
            return payload

        required = {"task_completed", "result", "actions_taken", "final_value", "error"}
        if required.issubset(payload.keys()):
            return payload

        raw_text = json.dumps(payload, ensure_ascii=False)
        return {
            "task_completed": payload.get("task_completed", False),
            "result": payload.get("result", raw_text),
            "actions_taken": payload.get(
                "actions_taken", "Agent response did not include structured actions."
            ),
            "final_value": payload.get("final_value"),
            "error": payload.get(
                "error",
                "Agent returned invalid TaskCompletionOutput payload; see result for raw content.",
            ),
        }
