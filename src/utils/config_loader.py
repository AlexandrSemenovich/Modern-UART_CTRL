"""Application configuration loader with theme-aware color/size/font access."""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from src.utils.paths import get_config_file


class Margins(NamedTuple):
    """Immutable margins tuple (left, top, right, bottom)."""
    left: int
    top: int
    right: int
    bottom: int


@dataclass
class ThemeColors:
    timestamp: str
    rx_text: str
    rx_label: str
    tx_text: str
    tx_label: str
    sys_text: str
    sys_label: str
    
    def __repr__(self) -> str:
        return f"ThemeColors(timestamp={self.timestamp!r}, rx_text={self.rx_text!r}, ...)"


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
    
    def __repr__(self) -> str:
        return f"ButtonColors(command_combo_active={self.command_combo_active!r}, ...)"


@dataclass
class FontConfig:
    default_family: str
    default_size: int
    title_size: int
    button_size: int
    caption_size: int
    monospace_family: str
    monospace_size: int
    
    def __repr__(self) -> str:
        return f"FontConfig(default_family={self.default_family!r}, default_size={self.default_size!r}, ...)"


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
    
    def __repr__(self) -> str:
        return f"SizeConfig(window_min_width={self.window_min_width}, ...)"


@dataclass
class PaletteColors:
    """QPalette colors for theme application."""

    window: str
    base: str
    window_text: str
    text: str
    button: str
    button_text: str
    link: str
    highlight: str
    highlighted_text: str
    
    def __repr__(self) -> str:
        return f"PaletteColors(window={self.window!r}, base={self.base!r}, ...)"


@dataclass
class ConsoleConfig:
    """Конфигурация консоли/логов."""

    max_html_length: int
    max_document_lines: int
    trim_chunk_size: int
    max_cache_lines: int
    
    def __repr__(self) -> str:
        return f"ConsoleConfig(max_html_length={self.max_html_length}, max_document_lines={self.max_document_lines}, ...)"


@dataclass
class ToastConfig:
    """Конфигурация toast-уведомлений."""

    toast_min_width: int
    toast_max_width: int
    toast_duration_ms: int
    toast_spacing: int
    toast_icon_size: int
    toast_close_button_size: int
    toast_margins: Margins
    toast_corner_radius: int
    
    def __repr__(self) -> str:
        return f"ToastConfig(toast_min_width={self.toast_min_width}, toast_duration_ms={self.toast_duration_ms}, ...)"


class ConfigLoader:
    """Loads application settings from config/config.ini with defaults."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._config = configparser.ConfigParser()
        # Single entry point for configuration
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
                timestamp="#757575",
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
                command_combo_active="#2563eb",
                command_combo_connecting="#3b82f6",
                command_combo_inactive="#1e3a5f",
                command_cpu1_active="#2563eb",
                command_cpu1_connecting="#3b82f6",
                command_cpu1_inactive="#1e3a5f",
                command_cpu2_active="#2563eb",
                command_cpu2_connecting="#3b82f6",
                command_cpu2_inactive="#1e3a5f",
                command_tlm_active="#2563eb",
                command_tlm_connecting="#3b82f6",
                command_tlm_inactive="#1e3a5f",
                command_text_active="#f8fafc",
                command_text_connecting="#0f172a",
                command_text_inactive="#7f8596",
            ),
            "light": ButtonColors(
                command_combo_active="#2563eb",
                command_combo_connecting="#3b82f6",
                command_combo_inactive="#dbeafe",
                command_cpu1_active="#2563eb",
                command_cpu1_connecting="#3b82f6",
                command_cpu1_inactive="#dbeafe",
                command_cpu2_active="#2563eb",
                command_cpu2_connecting="#3b82f6",
                command_cpu2_inactive="#dbeafe",
                command_tlm_active="#2563eb",
                command_tlm_connecting="#3b82f6",
                command_tlm_inactive="#dbeafe",
                command_text_active="#ffffff",
                command_text_connecting="#0f172a",
                command_text_inactive="#5a6370",
            ),
        }

        # Default QPalette colors for theme application
        self._default_palette_colors = {
            "dark": PaletteColors(
                window="#020617",
                base="#020617",
                window_text="#e5e7eb",
                text="#e5e7eb",
                button="#020617",
                button_text="#e5e7eb",
                link="#60a5fa",
                highlight="#1d4ed8",
                highlighted_text="#f9fafb",
            ),
            "light": PaletteColors(
                window="#f4f6fb",
                base="#ffffff",
                window_text="#0f172a",
                text="#0f172a",
                button="#e3edff",
                button_text="#0f172a",
                link="#2563eb",
                highlight="#2563eb",
                highlighted_text="#ffffff",
            ),
        }

    def _get_section(self, section: str) -> dict[str, str]:
        if self._config.has_section(section):
            return dict(self._config[section])
        return {}

    @staticmethod
    def _parse_int_value(value: object, default: int) -> int:
        """Convert config values to int while ignoring inline comments and spaces."""
        if isinstance(value, int):
            return value
        if value is None:
            return default
        if isinstance(value, str):
            cleaned = value.strip()
            for comment in (";", "#"):
                if comment in cleaned:
                    cleaned = cleaned.split(comment, 1)[0].strip()
            cleaned = cleaned.replace(" ", "").replace("\t", "").replace("_", "")
            if not cleaned:
                return default
            try:
                return int(cleaned)
            except ValueError:
                return default
        return default

    def _get_int(self, section: dict[str, str], key: str, default: int) -> int:
        return self._parse_int_value(section.get(key, default), default)

    def get_colors(self, theme: str) -> ThemeColors:
        section = self._get_section(f"colors.{theme}")
        defaults = self._default_colors.get(theme, self._default_colors["dark"])
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
        defaults = self._default_button_colors.get(theme, self._default_button_colors["dark"])

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

    def get_palette_colors(self, theme: str) -> PaletteColors:
        """Get QPalette colors for theme application."""
        section = self._get_section(f"palette.{theme}")
        defaults = self._default_palette_colors.get(theme, self._default_palette_colors["dark"])

        def _get(key: str, fallback: str) -> str:
            return section.get(key, fallback)

        return PaletteColors(
            window=_get("window", defaults.window),
            base=_get("base", defaults.base),
            window_text=_get("window_text", defaults.window_text),
            text=_get("text", defaults.text),
            button=_get("button", defaults.button),
            button_text=_get("button_text", defaults.button_text),
            link=_get("link", defaults.link),
            highlight=_get("highlight", defaults.highlight),
            highlighted_text=_get("highlighted_text", defaults.highlighted_text),
        )

    def get_fonts(self) -> FontConfig:
        section = self._get_section("fonts")
        return FontConfig(
            default_family=section.get("default_family", "Segoe UI"),
            default_size=self._get_int(section, "default_size", 12),
            title_size=self._get_int(section, "title_size", 12),
            button_size=self._get_int(section, "button_size", 12),
            caption_size=self._get_int(section, "caption_size", 12),
            monospace_family=section.get("monospace_family", "Courier New"),
            monospace_size=self._get_int(section, "monospace_size", 10),
        )

    def get_sizes(self) -> SizeConfig:
        section = self._get_section("sizes")
        return SizeConfig(
            window_min_width=self._get_int(section, "window_min_width", 800),
            window_min_height=self._get_int(section, "window_min_height", 600),
            window_default_width=self._get_int(section, "window_default_width", 1_200),
            window_default_height=self._get_int(section, "window_default_height", 800),
            left_panel_min_width=self._get_int(section, "left_panel_min_width", 320),
            left_panel_max_width=self._get_int(section, "left_panel_max_width", 380),
            center_panel_min_width=self._get_int(section, "center_panel_min_width", 400),
            right_panel_min_width=self._get_int(section, "right_panel_min_width", 200),
            right_panel_max_width=self._get_int(section, "right_panel_max_width", 350),
            layout_spacing=self._get_int(section, "layout_spacing", 5),
            layout_margin=self._get_int(section, "layout_margin", 5),
            toolbar_spacing=self._get_int(section, "toolbar_spacing", 5),
            toolbar_margin=self._get_int(section, "toolbar_margin", 0),
            button_min_height=self._get_int(section, "button_min_height", 26),
            button_max_width=self._get_int(section, "button_max_width", 110),
            button_clear_max_width=self._get_int(section, "button_clear_max_width", 80),
            button_save_max_width=self._get_int(section, "button_save_max_width", 80),
            input_min_height=self._get_int(section, "input_min_height", 32),
            search_field_max_width=self._get_int(section, "search_field_max_width", 200),
        )

    def get_serial_config(self) -> dict[str, str]:
        return self._get_section("serial_config")

    def get_ports_config(self) -> dict[str, str]:
        return self._get_section("ports")

    def get_serial_timing(self) -> dict[str, float]:
        """Get serial worker timing settings."""
        section = self._get_section("serial")
        return {
            "default_read_interval": float(section.get("default_read_interval", "0.02")),
            "connection_timeout": float(section.get("connection_timeout", "5.0")),
            "connection_retry_delay": float(section.get("connection_retry_delay", "0.5")),
            "max_connection_attempts": int(section.get("max_connection_attempts", "3")),
            "max_consecutive_errors": int(section.get("max_consecutive_errors", "3")),
        }

    def get_app_version(self) -> str:
        """Get application version from [app] section."""
        section = self._get_section("app")
        return section.get("version", "0.0.0")

    def get_default_theme(self) -> str:
        """
        Get default theme from [default_theme] section with validation
        against [themes].supported when available.
        """
        default_section = self._get_section("default_theme")
        theme = default_section.get("theme", "dark").strip()

        themes_section = self._get_section("themes")
        supported_raw = themes_section.get("supported", "")

        if supported_raw:
            supported = {item.strip() for item in supported_raw.split(",") if item.strip()}
            if theme not in supported and supported:
                # Fallback order: system -> dark -> light -> first supported
                for candidate in ("system", "dark", "light"):
                    if candidate in supported:
                        return candidate
                return next(iter(supported))
        return theme

    def get_console_config(self) -> ConsoleConfig:
        """
        Лимиты консоли/логов.

        Берутся из секции [console], при отсутствии — используются безопасные значения по умолчанию.
        """
        section = self._get_section("console")
        return ConsoleConfig(
            max_html_length=self._get_int(section, "max_html_length", 10_000),
            max_document_lines=self._get_int(section, "max_document_lines", 1_000),
            trim_chunk_size=self._get_int(section, "trim_chunk_size", 500),
            max_cache_lines=self._get_int(section, "max_cache_lines", 10_000),
        )

    def get_toast_config(self) -> ToastConfig:
        """
        Конфигурация toast-уведомлений.

        Берутся из секции [toast], при отсутствии — используются безопасные значения по умолчанию.
        """
        section = self._get_section("toast")
        
        # Parse margins tuple
        margins_str = section.get("toast_margins", "12, 8, 12, 8")
        try:
            values = tuple(int(x.strip()) for x in margins_str.split(","))
            if len(values) != 4:
                values = (12, 8, 12, 8)
        except ValueError:
            values = (12, 8, 12, 8)
        margins = Margins(*values)
        
        return ToastConfig(
            toast_min_width=self._get_int(section, "toast_min_width", 300),
            toast_max_width=self._get_int(section, "toast_max_width", 500),
            toast_duration_ms=self._get_int(section, "toast_duration_ms", 4000),
            toast_spacing=self._get_int(section, "toast_spacing", 8),
            toast_icon_size=self._get_int(section, "toast_icon_size", 20),
            toast_close_button_size=self._get_int(section, "toast_close_button_size", 20),
            toast_margins=margins,
            toast_corner_radius=self._get_int(section, "toast_corner_radius", 6),
        )


config_loader = ConfigLoader()
