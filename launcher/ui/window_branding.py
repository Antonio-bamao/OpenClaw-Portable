from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QWidget


def resolve_app_icon_path(assets_dir: Path) -> Path | None:
    for relative_path in ("app-icon.ico", "app-icon.png", "branding/app-icon.ico", "branding/app-icon.png"):
        candidate = assets_dir / relative_path
        if candidate.exists():
            return candidate
    return None


def load_app_icon(assets_dir: Path) -> QIcon | None:
    icon_path = resolve_app_icon_path(assets_dir)
    if not icon_path:
        return None
    icon = QIcon(str(icon_path))
    if icon.isNull():
        return None
    return icon


def apply_app_icon(app: QApplication | None, window: QWidget | None, assets_dir: Path) -> None:
    icon = load_app_icon(assets_dir)
    if not icon:
        return
    if app is not None:
        app.setWindowIcon(icon)
    if window is not None:
        window.setWindowIcon(icon)


def _colorref_from_hex(hex_color: str) -> int:
    normalized = hex_color.lstrip("#")
    if len(normalized) != 6:
        raise ValueError(f"Expected #RRGGBB color, got: {hex_color}")
    red = int(normalized[0:2], 16)
    green = int(normalized[2:4], 16)
    blue = int(normalized[4:6], 16)
    return red | (green << 8) | (blue << 16)


def apply_windows_title_bar_palette(
    window: QWidget,
    *,
    caption_color: str,
    text_color: str,
    border_color: str,
) -> bool:
    if sys.platform != "win32":
        return False

    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return False

    hwnd = int(window.winId())
    if not hwnd:
        return False

    DWMWA_BORDER_COLOR = 34
    DWMWA_CAPTION_COLOR = 35
    DWMWA_TEXT_COLOR = 36

    attributes = (
        (DWMWA_CAPTION_COLOR, _colorref_from_hex(caption_color)),
        (DWMWA_TEXT_COLOR, _colorref_from_hex(text_color)),
        (DWMWA_BORDER_COLOR, _colorref_from_hex(border_color)),
    )

    dwmapi = ctypes.windll.dwmapi
    for attribute, colorref in attributes:
        color_value = wintypes.DWORD(colorref)
        result = dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            ctypes.c_uint(attribute),
            ctypes.byref(color_value),
            ctypes.sizeof(color_value),
        )
        if result != 0:
            return False
    return True
