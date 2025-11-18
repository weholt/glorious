"""Domain models for automations skill."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Automation(SQLModel, table=True):
    """Automation rule definition.

    Represents an event-driven automation with triggers,
    conditions, and actions to execute.
    """

    __tablename__ = "automations"

    id: str = Field(primary_key=True, max_length=200)
    name: str = Field(max_length=200, unique=True, index=True)
    description: str | None = Field(default=None, max_length=2000)
    trigger_topic: str = Field(max_length=200, index=True)
    trigger_condition: str | None = Field(default=None, max_length=1000)
    actions: str = Field()  # JSON string
    enabled: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "auto-abc123",
                "name": "Log on issue creation",
                "trigger_topic": "issue_created",
                "actions": '[{"type": "log", "message": "Issue created"}]',
                "enabled": True,
            }
        }


class AutomationExecution(SQLModel, table=True):
    """Automation execution record.

    Tracks each time an automation is triggered and executed,
    including status, results, and errors.
    """

    __tablename__ = "automation_executions"

    id: int | None = Field(default=None, primary_key=True)
    automation_id: str = Field(max_length=200, index=True, foreign_key="automations.id")
    trigger_data: str | None = Field(default=None)  # JSON string
    status: str = Field(max_length=50, index=True)
    result: str | None = Field(default=None)  # JSON string
    error: str | None = Field(default=None, max_length=2000)
    executed_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "automation_id": "auto-abc123",
                "status": "success",
                "result": '[{"type": "log", "success": true}]',
            }
        }
