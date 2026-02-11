"""Application configuration loader with theme-aware color/size/font access."""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


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


class ConfigLoader:
    """Loads application settings from config/config.ini with defaults."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._config = configparser.ConfigParser()
        root = Path(__file__).resolve().parents[1]
        default_path = root / "config" / "config.ini"
        self._config.read(config_path or default_path, encoding="utf-8")

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


config_loader = ConfigLoader()
