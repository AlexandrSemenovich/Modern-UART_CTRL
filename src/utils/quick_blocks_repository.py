"""YAML-based repository for Quick Blocks configuration."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from threading import RLock
from typing import Iterable
import uuid

import yaml

from src.utils.service_container import service_container
from src.utils.paths import get_config_file


@dataclass(slots=True)
class QuickBlock:
    id: str
    title: str
    command_on: str
    command_off: str | None = None
    send_to_combo: bool = True
    group_id: str | None = None
    order: int = 0
    mode: str = "dual"  # dual | single
    icon: str | None = None
    port: str | None = None
    hotkey: str | None = None


@dataclass(slots=True)
class QuickGroup:
    id: str
    name: str
    collapsed: bool = False
    blocks: list[QuickBlock] = field(default_factory=list)
    order: int = 0


class QuickBlocksRepository:
    """Thread-safe repository backed by YAML file."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._path = config_path or get_config_file("quick_blocks.yaml")
        self._lock = RLock()
        self._groups: list[QuickGroup] = []
        self._ensure_file_exists()
        self.load()

    # ------------------ Public API ------------------
    def list_groups(self) -> list[QuickGroup]:
        with self._lock:
            return [self._clone_group(g) for g in self._groups]

    def add_block(self, block: QuickBlock) -> None:
        with self._lock:
            group = self._get_group(block.group_id)
            block.group_id = group.id
            block.order = len(group.blocks)
            group.blocks.append(block)
            self._save()
    
    def get_block(self, block_id: str) -> QuickBlock | None:
        with self._lock:
            for group in self._groups:
                for block in group.blocks:
                    if block.id == block_id:
                        return replace(block)
        return None

    def update_block(self, block: QuickBlock) -> None:
        with self._lock:
            group = self._get_group(block.group_id)
            for idx, existing in enumerate(group.blocks):
                if existing.id == block.id:
                    group.blocks[idx] = block
                    break
            else:
                raise ValueError(f"Block {block.id} not found")
            self._save()

    def remove_block(self, block_id: str) -> None:
        with self._lock:
            for group in self._groups:
                for idx, block in enumerate(group.blocks):
                    if block.id == block_id:
                        group.blocks.pop(idx)
                        self._reorder(group.blocks)
                        self._save()
                        return
        raise ValueError(f"Block {block_id} not found")

    def reorder_blocks(self, group_id: str, new_order: list[str]) -> None:
        with self._lock:
            group = self._get_group(group_id)
            lookup = {block.id: block for block in group.blocks}
            group.blocks = [lookup[bid] for bid in new_order if bid in lookup]
            self._reorder(group.blocks)
            self._save()

    def add_group(self, name: str) -> QuickGroup:
        with self._lock:
            group = QuickGroup(id=self._new_id(), name=name, order=len(self._groups))
            self._groups.append(group)
            self._save()
            return self._clone_group(group)

    def update_group(self, group: QuickGroup) -> None:
        with self._lock:
            for idx, existing in enumerate(self._groups):
                if existing.id == group.id:
                    self._groups[idx] = group
                    self._save()
                    return
        raise ValueError(f"Group {group.id} not found")

    def remove_group(self, group_id: str) -> None:
        with self._lock:
            for idx, group in enumerate(self._groups):
                if group.id == group_id:
                    if group.blocks:
                        raise ValueError("Cannot remove non-empty group")
                    self._groups.pop(idx)
                    self._reorder_groups()
                    self._save()
                    return
        raise ValueError(f"Group {group_id} not found")

    def reorder_groups(self, new_order: list[str]) -> None:
        with self._lock:
            lookup = {group.id: group for group in self._groups}
            ordered = [lookup[gid] for gid in new_order if gid in lookup]
            remaining = [group for group in self._groups if group.id not in new_order]
            self._groups = ordered + remaining
            self._reorder_groups()
            self._save()

    def set_group_collapsed(self, group_id: str, collapsed: bool) -> None:
        with self._lock:
            group = self._get_group(group_id)
            if group.collapsed == collapsed:
                return
            group.collapsed = collapsed
            self._save()

    def move_block(
        self,
        block_id: str,
        target_group_id: str,
        target_index: int | None = None,
    ) -> None:
        with self._lock:
            source_group, block, block_index = self._find_block(block_id)
            if block is None or source_group is None:
                raise ValueError(f"Block {block_id} not found")
            target_group = self._get_group(target_group_id)
            source_group.blocks.pop(block_index)
            insert_at = target_index if target_index is not None else len(target_group.blocks)
            insert_at = max(0, min(insert_at, len(target_group.blocks)))
            block.group_id = target_group.id
            target_group.blocks.insert(insert_at, block)
            self._reorder(source_group.blocks)
            if source_group is not target_group:
                self._reorder(target_group.blocks)
            self._save()

    def reload(self) -> None:
        self.load()

    # ------------------ Persistence ------------------
    def load(self) -> None:
        with self._lock:
            with open(self._path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
            groups = []
            for order, group_data in enumerate(data.get("groups", [])):
                blocks = [
                    QuickBlock(
                        id=item.get("id", self._new_id()),
                        title=item.get("title", "Unnamed"),
                        command_on=item.get("command_on", ""),
                        command_off=item.get("command_off"),
                        send_to_combo=item.get("send_to_combo", True),
                        group_id=group_data.get("id"),
                        order=item.get("order", 0),
                        mode=item.get("mode", "dual"),
                        icon=item.get("icon"),
                        port=item.get("port"),
                        hotkey=item.get("hotkey"),
                    )
                    for item in group_data.get("blocks", [])
                ]
                self._reorder(blocks)
                groups.append(
                    QuickGroup(
                        id=group_data.get("id", self._new_id()),
                        name=group_data.get("name", "Unnamed"),
                        collapsed=group_data.get("collapsed", False),
                        blocks=blocks,
                        order=order,
                    )
                )
            self._groups = groups

    def _save(self) -> None:
        with open(self._path.with_suffix(".tmp"), "w", encoding="utf-8") as fh:
            yaml.safe_dump(
                {
                    "version": 1,
                    "groups": [self._group_to_dict(group) for group in self._groups],
                },
                fh,
                allow_unicode=True,
                sort_keys=False,
            )
        self._path.with_suffix(".tmp").replace(self._path)

    # ------------------ Helpers ------------------
    def _ensure_file_exists(self) -> None:
        if self._path.exists():
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as fh:
            yaml.safe_dump({"version": 1, "groups": []}, fh)

    def _get_group(self, group_id: str | None) -> QuickGroup:
        for group in self._groups:
            if group.id == group_id:
                return group
        raise ValueError(f"Group {group_id} not found")

    def _find_block(self, block_id: str) -> tuple[QuickGroup | None, QuickBlock | None, int]:
        for group in self._groups:
            for idx, block in enumerate(group.blocks):
                if block.id == block_id:
                    return group, block, idx
        return None, None, -1

    @staticmethod
    def _reorder(blocks: Iterable[QuickBlock]) -> None:
        for idx, block in enumerate(blocks):
            block.order = idx

    def _reorder_groups(self) -> None:
        for idx, group in enumerate(self._groups):
            group.order = idx

    @staticmethod
    def _new_id() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def _group_to_dict(group: QuickGroup) -> dict:
        return {
            "id": group.id,
            "name": group.name,
            "collapsed": group.collapsed,
            "order": group.order,
            "blocks": [
                {
                    "id": block.id,
                    "title": block.title,
                    "command_on": block.command_on,
                    "command_off": block.command_off,
                    "send_to_combo": block.send_to_combo,
                    "order": block.order,
                    "mode": block.mode,
                    "icon": block.icon,
                    "port": block.port,
                    "hotkey": block.hotkey,
                    "group_id": block.group_id,
                }
                for block in group.blocks
            ],
        }

    @staticmethod
    def _clone_group(group: QuickGroup) -> QuickGroup:
        return QuickGroup(
            id=group.id,
            name=group.name,
            collapsed=group.collapsed,
            blocks=[replace(block) for block in group.blocks],
            order=group.order,
        )


repository = QuickBlocksRepository()
service_container.register_singleton("quick_blocks_repository", lambda: repository)
