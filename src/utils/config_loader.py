"""Application configuration loader with theme-aware color/size/font access."""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from src.utils.paths import get_config_file


@dataclass
class ThemeColors:
    timestamp: str
    rx_text: str
    rx_label: str
    tx_text: str
    tx_label: str
    sys_text: str
    sys_label: str


@dataclass
class ButtonColors:
    command_combo_active: str
    command_combo_connecting: str
    command_combo_inactive: str
    command_cpu1_active: str
    command_cpu1_connecting: str
    command_cpu1_inactive: str
    command_cpu2_active: str
    command_cpu2_connecting: str
    command_cpu2_inactive: str
    command_tlm_active: str
    command_tlm_connecting: str
    command_tlm_inactive: str
    command_text_active: str
    command_text_connecting: str
    command_text_inactive: str


@dataclass
class FontConfig:
    default_family: str
    default_size: int
    title_size: int
    button_size: int
    monospace_family: str
    monospace_size: int


@dataclass
class SizeConfig:
    window_min_width: int
    window_min_height: int
    window_default_width: int
    window_default_height: int
    left_panel_min_width: int
    left_panel_max_width: int
    center_panel_min_width: int
    right_panel_min_width: int
    right_panel_max_width: int
    layout_spacing: int
    layout_margin: int
    toolbar_spacing: int
    toolbar_margin: int
    button_min_height: int
    button_max_width: int
    button_clear_max_width: int
    button_save_max_width: int
    input_min_height: int
    search_field_max_width: int


@dataclass
class ConsoleConfig:
    """Конфигурация консоли/логов."""

    max_html_length: int
    max_document_lines: int
    trim_chunk_size: int
    max_cache_lines: int


class ConfigLoader:
    """Loads application settings from config/config.ini with defaults."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._config = configparser.ConfigParser()
        # Единая точка входа для конфигурации
        default_path = get_config_file("config.ini")
        
        # Error handling for config parsing with fallback to defaults
        try:
            self._config.read(config_path or default_path, encoding="utf-8")
        except (configparser.Error, OSError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to parse config file: {e}. Using default values.")

        # defaults
        self._default_colors = {
            "dark": ThemeColors(
                timestamp="#aaaaaa",
                rx_text="#c7f0c7",
                rx_label="#4caf50",
                tx_text="#fff7d6",
                tx_label="#ffdd57",
                sys_text="#cccccc",
                sys_label="#bbbbbb",
            ),
            "light": ThemeColors(
                timestamp="#666666",
                rx_text="#2b6d2b",
                rx_label="#1f7a1f",
                tx_text="#a06b00",
                tx_label="#c78a00",
                sys_text="#666666",
                sys_label="#888888",
            ),
        }

        self._default_button_colors = {
            "dark": ButtonColors(
                command_combo_active="#8b5cf6",
                command_combo_connecting="#a78bfa",
                command_combo_inactive="#2b2440",
                command_cpu1_active="#16a34a",
                command_cpu1_connecting="#22c55e",
                command_cpu1_inactive="#1f2d26",
                command_cpu2_active="#0891b2",
                command_cpu2_connecting="#22d3ee",
                command_cpu2_inactive="#192a30",
                command_tlm_active="#e11d48",
                command_tlm_connecting="#fb7185",
                command_tlm_inactive="#2f1d24",
                command_text_active="#f8fafc",
                command_text_connecting="#0f172a",
                command_text_inactive="#7f8596",
            ),
            "light": ButtonColors(
                command_combo_active="#5b21b6",
                command_combo_connecting="#8b5cf6",
                command_combo_inactive="#dcd5f7",
                command_cpu1_active="#15803d",
                command_cpu1_connecting="#34d399",
                command_cpu1_inactive="#d6f2e3",
                command_cpu2_active="#0f766e",
                command_cpu2_connecting="#2dd4bf",
                command_cpu2_inactive="#d3f3f0",
                command_tlm_active="#be123c",
                command_tlm_connecting="#fb7185",
                command_tlm_inactive="#fdd8e1",
                command_text_active="#ffffff",
                command_text_connecting="#0b1120",
                command_text_inactive="#4b5563",
            ),
        }

    def _get_section(self, section: str) -> Dict[str, str]:
        if self._config.has_section(section):
            return dict(self._config[section])
        return {}

    def get_colors(self, theme: str) -> ThemeColors:
        section = self._get_section(f"colors.{theme}")
        defaults = self._default_colors["dark" if theme not in self._default_colors else theme]
        return ThemeColors(
            timestamp=section.get("timestamp", defaults.timestamp),
            rx_text=section.get("rx_text", defaults.rx_text),
            rx_label=section.get("rx_label", defaults.rx_label),
            tx_text=section.get("tx_text", defaults.tx_text),
            tx_label=section.get("tx_label", defaults.tx_label),
            sys_text=section.get("sys_text", defaults.sys_text),
            sys_label=section.get("sys_label", defaults.sys_label),
        )

    def get_button_colors(self, theme: str) -> ButtonColors:
        section = self._get_section(f"button_colors.{theme}")
        defaults = self._default_button_colors["dark" if theme not in self._default_button_colors else theme]

        def _get(key: str, fallback: str) -> str:
            return section.get(key, fallback)

        return ButtonColors(
            command_combo_active=_get("command_combo_active", defaults.command_combo_active),
            command_combo_connecting=_get("command_combo_connecting", defaults.command_combo_connecting),
            command_combo_inactive=_get("command_combo_inactive", defaults.command_combo_inactive),
            command_cpu1_active=_get("command_cpu1_active", defaults.command_cpu1_active),
            command_cpu1_connecting=_get("command_cpu1_connecting", defaults.command_cpu1_connecting),
            command_cpu1_inactive=_get("command_cpu1_inactive", defaults.command_cpu1_inactive),
            command_cpu2_active=_get("command_cpu2_active", defaults.command_cpu2_active),
            command_cpu2_connecting=_get("command_cpu2_connecting", defaults.command_cpu2_connecting),
            command_cpu2_inactive=_get("command_cpu2_inactive", defaults.command_cpu2_inactive),
            command_tlm_active=_get("command_tlm_active", defaults.command_tlm_active),
            command_tlm_connecting=_get("command_tlm_connecting", defaults.command_tlm_connecting),
            command_tlm_inactive=_get("command_tlm_inactive", defaults.command_tlm_inactive),
            command_text_active=_get("command_text_active", defaults.command_text_active),
            command_text_connecting=_get("command_text_connecting", defaults.command_text_connecting),
            command_text_inactive=_get("command_text_inactive", defaults.command_text_inactive),
        )

    def get_fonts(self) -> FontConfig:
        section = self._get_section("fonts")
        return FontConfig(
            default_family=section.get("default_family", "Segoe UI"),
            default_size=int(section.get("default_size", 10)),
            title_size=int(section.get("title_size", 14)),
            button_size=int(section.get("button_size", 10)),
            monospace_family=section.get("monospace_family", "Courier New"),
            monospace_size=int(section.get("monospace_size", 9)),
        )

    def get_sizes(self) -> SizeConfig:
        section = self._get_section("sizes")
        get_int = lambda key, default: int(section.get(key, default))
        return SizeConfig(
            window_min_width=get_int("window_min_width", 800),
            window_min_height=get_int("window_min_height", 600),
            window_default_width=get_int("window_default_width", 1200),
            window_default_height=get_int("window_default_height", 800),
            left_panel_min_width=get_int("left_panel_min_width", 320),
            left_panel_max_width=get_int("left_panel_max_width", 380),
            center_panel_min_width=get_int("center_panel_min_width", 400),
            right_panel_min_width=get_int("right_panel_min_width", 200),
            right_panel_max_width=get_int("right_panel_max_width", 350),
            layout_spacing=get_int("layout_spacing", 5),
            layout_margin=get_int("layout_margin", 5),
            toolbar_spacing=get_int("toolbar_spacing", 5),
            toolbar_margin=get_int("toolbar_margin", 0),
            button_min_height=get_int("button_min_height", 26),
            button_max_width=get_int("button_max_width", 110),
            button_clear_max_width=get_int("button_clear_max_width", 80),
            button_save_max_width=get_int("button_save_max_width", 80),
            input_min_height=get_int("input_min_height", 32),
            search_field_max_width=get_int("search_field_max_width", 200),
        )

    def get_serial_config(self) -> Dict[str, str]:
        return self._get_section("serial_config")

    def get_console_config(self) -> ConsoleConfig:
        """
        Console / log configuration.

        Values are taken from [console] section with safe defaults.
        """
        section = self._get_section("console")
        get_int = lambda key, default: int(section.get(key, default))
        return ConsoleConfig(
            max_html_length=get_int("max_html_length", 10_000),
            max_document_lines=get_int("max_document_lines", 1_000),
            trim_chunk_size=get_int("trim_chunk_size", 500),
            max_cache_lines=get_int("max_cache_lines", 10_000),
        )

    def get_app_version(self) -> str:
        """Get application version from [app] section."""
        section = self._get_section("app")
        return section.get("version", "0.0.0")

    def get_console_config(self) -> ConsoleConfig:
        """
        Лимиты консоли/логов.

        Берутся из секции [console], при отсутствии — используются безопасные значения по умолчанию.
        """
        section = self._get_section("console")
        get_int = lambda key, default: int(section.get(key, default))
        return ConsoleConfig(
            max_html_length=get_int("max_html_length", 10_000),
            max_document_lines=get_int("max_document_lines", 1_000),
            trim_chunk_size=get_int("trim_chunk_size", 500),
            max_cache_lines=get_int("max_cache_lines", 10_000),
        )


config_loader = ConfigLoader()
