"""Pydantic схемы для quick_blocks.yaml с валидацией."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class QuickBlockModel(BaseModel):
    """Модель отдельного блока Quick Block."""

    id: str
    title: str
    command_on: str = Field(min_length=1)
    command_off: str | None = None
    send_to_combo: bool = True
    group_id: str | None = None
    order: int = 0
    mode: Literal["dual", "single"] = "dual"
    icon: str | None = None
    port: str | None = None
    hotkey: str | None = None

    @field_validator("command_off", mode="before")
    @classmethod
    def _strip_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class QuickGroupModel(BaseModel):
    """Модель группы блоков."""

    id: str
    name: str
    collapsed: bool = False
    order: int = 0
    blocks: list[QuickBlockModel] = Field(default_factory=list)


class QuickBlocksDocument(BaseModel):
    """Корневой документ quick_blocks.yaml."""

    configuration_version: int = Field(1, ge=1)
    groups: list[QuickGroupModel] = Field(default_factory=list)

    model_config = {
        "validate_by_name": True,
        "extra": "allow",
    }

    @model_validator(mode="before")
    @classmethod
    def _backfill_version(cls, values: dict) -> dict:
        if "configuration_version" not in values:
            # Поддерживаем старое поле version
            legacy = values.get("version")
            if legacy is not None:
                values["configuration_version"] = legacy
        return values

