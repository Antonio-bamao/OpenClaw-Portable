from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QDialog, QFrame, QHBoxLayout, QVBoxLayout

from launcher.services.window_preferences import CloseAction
from launcher.ui.theme import BORDER, PANEL, PRIMARY, SURFACE, TEXT
from launcher.ui.widgets import apply_card_shadow, make_button, make_label


class CloseActionDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._selected_action: CloseAction | None = None
        self.setWindowTitle("关闭 OpenClaw Portable")
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {SURFACE};
                color: {TEXT};
            }}
            QFrame#CloseDialogCard {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 4px;
            }}
            QCheckBox {{
                color: {PRIMARY};
                spacing: 8px;
                font-size: 14px;
            }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(0)

        card = QFrame()
        card.setObjectName("CloseDialogCard")
        apply_card_shadow(card, blur_radius=16, offset_y=5)
        root.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        layout.addWidget(make_label("关闭窗口时要怎么处理 OpenClaw？", "SectionTitle", size=18, weight=700))
        layout.addWidget(
            make_label(
                "最小化会把程序留在 Windows 右下角托盘；完全退出会停止本地 OpenClaw 服务和相关运行时进程。",
                "MutedText",
            )
        )

        self.remember_checkbox = QCheckBox("以后点击 X 直接最小化到托盘，不再提醒")
        layout.addWidget(self.remember_checkbox)

        actions = QHBoxLayout()
        actions.setSpacing(12)
        actions.addStretch(1)

        self.minimize_button = make_button("最小化到托盘")
        self.exit_button = make_button("完全退出", primary=True)
        self.minimize_button.clicked.connect(self._choose_minimize)
        self.exit_button.clicked.connect(self._choose_exit)
        actions.addWidget(self.minimize_button)
        actions.addWidget(self.exit_button)
        layout.addLayout(actions)

    @property
    def selected_action(self) -> CloseAction | None:
        return self._selected_action

    def remember_choice(self) -> bool:
        return self.remember_checkbox.isChecked()

    def _choose_minimize(self) -> None:
        self._selected_action = CloseAction.MINIMIZE_TO_TRAY
        self.accept()

    def _choose_exit(self) -> None:
        self._selected_action = CloseAction.EXIT
        self.accept()
