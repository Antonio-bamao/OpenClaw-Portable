from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from launcher.ui.theme import preferred_font, shadow_color


def apply_card_shadow(widget: QWidget, blur_radius: int = 40, offset_y: int = 12) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur_radius)
    effect.setColor(shadow_color())
    effect.setOffset(0, offset_y)
    widget.setGraphicsEffect(effect)


def make_button(text: str, *, primary: bool = False, subtle: bool = False) -> QPushButton:
    button = QPushButton(text)
    button.setCursor(Qt.PointingHandCursor)
    if primary:
        button.setObjectName("PrimaryButton")
    elif subtle:
        button.setObjectName("SubtleButton")
    return button


def make_label(text: str, object_name: str, *, size: int | None = None, weight: int | None = None) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setObjectName(object_name)
    font = preferred_font()
    if size is not None:
        font.setPointSize(size)
    if weight is not None:
        font.setWeight(QFont.Weight(weight))
    label.setFont(font)
    return label


class MetricCard(QFrame):
    def __init__(self, label: str, value: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MetricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)
        layout.addWidget(make_label(label, "MetricLabel", size=9, weight=QFont.DemiBold))
        self.value_label = make_label(value, "MetricValue", size=16, weight=QFont.Bold)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class HeroPanel(QFrame):
    def __init__(self, title: str, subtitle: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("HeroCard")
        apply_card_shadow(self)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(24)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(12)
        text_layout.addWidget(make_label("OpenClaw Portable / Launcher", "Eyebrow", size=9, weight=QFont.DemiBold))
        text_layout.addWidget(make_label(title, "DisplayTitle", size=24, weight=QFont.Bold))
        text_layout.addWidget(make_label(subtitle, "HeroSubtitle"))
        text_layout.addStretch(1)

        status_layout = QVBoxLayout()
        status_layout.setSpacing(10)
        status_layout.addWidget(make_label("当前状态", "MutedText", size=10, weight=QFont.DemiBold))
        status_layout.addWidget(make_label("运行中 / 可联调", "HeroStatusTitle", size=18, weight=QFont.Bold))
        status_layout.addWidget(make_label("健康检查与本地 WebUI 已预留。", "MutedText"))
        status_layout.addWidget(make_label("可靠性占优", "StatusBadge", size=10, weight=QFont.DemiBold))
        status_layout.addStretch(1)

        layout.addLayout(text_layout, stretch=2)
        layout.addLayout(status_layout, stretch=1)
