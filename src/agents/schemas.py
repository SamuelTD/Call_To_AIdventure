from typing import List
from pydantic import BaseModel, Field, field_validator


class ChoiceOutput(BaseModel):
    choices: List[str] = Field(
        description="Exactly three distinct short player actions."
    )

    @field_validator("choices")
    @classmethod
    def validate_choices(cls, value: List[str]) -> List[str]:
        if len(value) != 3:
            raise ValueError("choices must contain exactly 3 items")

        cleaned = [item.strip() for item in value]

        if any(not item for item in cleaned):
            raise ValueError("choices cannot contain empty strings")

        if any(len(item.split()) > 6 for item in cleaned):
            raise ValueError("each choice must be at most 6 words long")

        lowered = [item.lower() for item in cleaned]
        if len(set(lowered)) != 3:
            raise ValueError("choices must be distinct")

        return cleaned


class GoalEvaluationOutput(BaseModel):
    completed_goals: List[str] = Field(
        default_factory=list,
        description="Goals from the provided ongoing goals list that are now clearly complete.",
    )


class RoomCompletionOutput(BaseModel):
    room_completed: bool = Field(
        default=False,
        description="Whether the latest resolved narrative clearly completes the current room objective.",
    )
    reason: str = Field(
        default="",
        description="Short explanation grounded in the latest narrative.",
    )
