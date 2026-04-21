from __future__ import annotations

from PySide6.QtGui import QColor, QFont


ACCENT = "#0F6CBD"
ACCENT_DEEP = "#094A87"
SURFACE = "#F5F8FC"
TEXT = "#13253A"
MUTED = "#5B6B7E"
BORDER = "rgba(19, 37, 58, 0.08)"


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
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(255, 255, 255, 0.96),
                stop: 1 rgba(238, 245, 255, 0.92)
            );
            border: 1px solid rgba(15, 108, 189, 0.10);
            border-radius: 28px;
        }}
        QFrame#SectionCard {{
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid {BORDER};
            border-radius: 24px;
        }}
        QFrame#MetricCard {{
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(15, 108, 189, 0.08);
            border-radius: 18px;
        }}
        QLabel#Eyebrow {{
            color: {ACCENT};
            background: rgba(15, 108, 189, 0.10);
            border-radius: 14px;
            padding: 6px 12px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }}
        QLabel#DisplayTitle {{
            font-size: 34px;
            font-weight: 700;
        }}
        QLabel#HeroStatusTitle {{
            font-size: 28px;
            font-weight: 700;
        }}
        QLabel#SectionTitle {{
            font-size: 18px;
            font-weight: 700;
        }}
        QLabel#SectionStatus {{
            font-size: 14px;
            font-weight: 700;
        }}
        QLabel#HeroSubtitle, QLabel#MutedText {{
            color: {MUTED};
            line-height: 1.5;
        }}
        QLabel#StatusBadge {{
            color: #0B7A0B;
            background: rgba(11, 122, 11, 0.10);
            border-radius: 16px;
            padding: 8px 14px;
            font-weight: 600;
        }}
        QLabel#MetricLabel {{
            color: {MUTED};
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.8px;
        }}
        QLabel#MetricValue {{
            font-size: 22px;
            font-weight: 700;
        }}
        QPushButton {{
            min-height: 44px;
            border-radius: 16px;
            padding: 0 18px;
            border: 1px solid rgba(19, 37, 58, 0.08);
            background: rgba(255, 255, 255, 0.96);
        }}
        QPushButton:hover {{
            background: rgba(15, 108, 189, 0.06);
        }}
        QPushButton#PrimaryButton {{
            background: {ACCENT};
            color: white;
            font-weight: 600;
            border: none;
        }}
        QPushButton#PrimaryButton:hover {{
            background: {ACCENT_DEEP};
        }}
        QPushButton#SubtleButton {{
            background: rgba(15, 108, 189, 0.08);
            color: {ACCENT};
            border: 1px solid rgba(15, 108, 189, 0.12);
            font-weight: 600;
        }}
        QLineEdit, QComboBox {{
            min-height: 42px;
            border-radius: 14px;
            border: 1px solid rgba(19, 37, 58, 0.12);
            background: white;
            padding: 0 14px;
        }}
        QTextEdit, QPlainTextEdit {{
            border-radius: 18px;
            border: 1px solid rgba(19, 37, 58, 0.12);
            background: white;
            padding: 12px;
        }}
        QStackedWidget {{
            background: transparent;
        }}
    """


def shadow_color() -> QColor:
    return QColor(18, 37, 58, 30)
