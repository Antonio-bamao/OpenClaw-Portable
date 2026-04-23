from __future__ import annotations

from PySide6.QtGui import QColor, QFont


PRIMARY = "#2F3233"
ACCENT = "#D66A1F"
ACCENT_DEEP = "#A64D16"
SUCCESS = "#4F6F52"
SURFACE = "#E8E5DC"
PANEL = "#F7F5EF"
TEXT = "#1F2020"
MUTED = "#63625D"
BORDER = "#C9C5BA"
FIELD = "#FCFBF7"
METAL = "#D8D5CC"
RING = "#2F3233"


def preferred_font() -> QFont:
    font = QFont()
    font.setFamilies(
        [
            "Segoe UI Variable Text",
            "Microsoft YaHei UI",
            "Microsoft YaHei",
            "Segoe UI",
            "Noto Sans SC",
            "Noto Sans CJK SC",
        ]
    )
    font.setPointSize(10)
    return font


def app_stylesheet() -> str:
    return f"""
        QWidget {{
            color: {TEXT};
            background: transparent;
            font-size: 14px;
        }}
        QMainWindow {{
            background: {SURFACE};
        }}
        QFrame#HeroCard {{
            background: {PANEL};
            border: 1px solid {BORDER};
            border-top: 4px solid {PRIMARY};
            border-radius: 4px;
        }}
        QFrame#SectionCard {{
            background: {PANEL};
            border: 1px solid {BORDER};
            border-radius: 4px;
        }}
        QFrame#MetricCard {{
            background: #FDFBF6;
            border: 1px solid {BORDER};
            border-radius: 4px;
        }}
        QLabel#Eyebrow {{
            color: {PRIMARY};
            background: #ECE8DD;
            border: 1px solid {BORDER};
            border-bottom: 2px solid {ACCENT};
            border-radius: 3px;
            padding: 5px 11px;
            font-weight: 700;
        }}
        QLabel#DisplayTitle {{
            color: {PRIMARY};
            font-size: 32px;
            font-weight: 700;
        }}
        QLabel#HeroStatusTitle {{
            color: {PRIMARY};
            font-size: 24px;
            font-weight: 700;
        }}
        QLabel#SectionTitle {{
            color: {PRIMARY};
            font-size: 18px;
            font-weight: 700;
        }}
        QLabel#SectionStatus {{
            color: {PRIMARY};
            font-size: 14px;
            font-weight: 700;
        }}
        QLabel#HeroSubtitle, QLabel#MutedText {{
            color: {MUTED};
            line-height: 1.5;
        }}
        QFrame#HeroCard QLabel#MutedText {{
            color: {MUTED};
        }}
        QLabel#StatusBadge {{
            color: {PRIMARY};
            background: #EFECE3;
            border: 1px solid {BORDER};
            border-left: 4px solid {ACCENT};
            border-radius: 3px;
            padding: 7px 12px;
            font-weight: 700;
        }}
        QLabel#MetricLabel {{
            color: {MUTED};
            font-size: 12px;
            font-weight: 600;
        }}
        QLabel#MetricValue {{
            color: {PRIMARY};
            font-size: 21px;
            font-weight: 700;
        }}
        QPushButton {{
            min-height: 42px;
            border-radius: 3px;
            padding: 0 16px;
            border: 1px solid #B8B3A8;
            background: #F9F7F1;
            color: {PRIMARY};
            font-weight: 700;
        }}
        QPushButton:hover {{
            background: #F1EEE6;
            border-color: #8F8A80;
        }}
        QPushButton:pressed {{
            background: {METAL};
            border-color: {PRIMARY};
        }}
        QPushButton:focus {{
            border: 2px solid {RING};
        }}
        QPushButton:disabled {{
            color: #9A9890;
            background: #E4E0D7;
            border-color: #D0CCC2;
        }}
        QPushButton#PrimaryButton {{
            background: {ACCENT};
            color: #FFFFFF;
            font-weight: 800;
            border: 1px solid {ACCENT_DEEP};
        }}
        QPushButton#PrimaryButton:hover {{
            background: {ACCENT_DEEP};
            border-color: {ACCENT_DEEP};
        }}
        QPushButton#PrimaryButton:pressed {{
            background: #7E3C12;
        }}
        QPushButton#SubtleButton {{
            background: {METAL};
            color: {PRIMARY};
            border: 1px solid #AAA69B;
            font-weight: 700;
        }}
        QPushButton#SubtleButton:hover {{
            background: #E4E0D7;
            border-color: #878177;
        }}
        QPushButton#DangerButton {{
            background: #F7F5EF;
            color: {PRIMARY};
            border: 1px solid #AFA99E;
            border-left: 4px solid {ACCENT};
            font-weight: 700;
        }}
        QPushButton#DangerButton:hover {{
            background: #EFECE3;
            border-color: {ACCENT_DEEP};
        }}
        QToolButton#ChannelSelectorButton {{
            min-height: 94px;
            border-radius: 4px;
            padding: 10px 12px;
            border: 1px solid #B8B3A8;
            background: #FDFBF6;
            color: {PRIMARY};
            font-weight: 700;
        }}
        QToolButton#ChannelSelectorButton:hover {{
            background: #F3F0E8;
            border-color: #8F8A80;
        }}
        QToolButton#ChannelSelectorButton:checked {{
            background: #EFECE3;
            border: 2px solid {PRIMARY};
            border-bottom: 3px solid {ACCENT};
        }}
        QToolButton#ChannelSelectorButton:focus {{
            border: 2px solid {PRIMARY};
        }}
        QLineEdit, QComboBox {{
            min-height: 42px;
            border-radius: 3px;
            border: 1px solid #B8B3A8;
            background: {FIELD};
            padding: 0 14px;
        }}
        QLineEdit:focus, QComboBox:focus {{
            border: 2px solid {PRIMARY};
            background: #FFFFFF;
        }}
        QTextEdit, QPlainTextEdit {{
            border-radius: 3px;
            border: 1px solid #B8B3A8;
            background: {FIELD};
            padding: 12px;
        }}
        QPlainTextEdit#ConsoleOutput {{
            color: #E8E5DC;
            background: #242626;
            border: 1px solid #151616;
            selection-background-color: {ACCENT};
        }}
        QStackedWidget {{
            background: transparent;
        }}
        QStackedWidget#ChannelDetailStack {{
            border-top: 1px solid {BORDER};
            margin-top: 4px;
            background: transparent;
        }}
        QScrollArea {{
            border: none;
            background: {SURFACE};
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: #AFA99E;
            border-radius: 3px;
            min-height: 36px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {PRIMARY};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
    """


def shadow_color() -> QColor:
    return QColor(47, 50, 51, 18)
