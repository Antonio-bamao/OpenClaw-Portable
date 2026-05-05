from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLineEdit, QVBoxLayout

from launcher.ui.theme import app_stylesheet, preferred_font
from launcher.ui.widgets import make_button, make_label


class UnlockDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        title: str = "需要解锁 OpenClaw Portable",
        description: str = "检测到新的电脑环境或当前设备密钥不可用。请输入管理密码解锁本地保险箱，解锁后模型 Key 和各渠道凭据才会被加载。",
        button_text: str = "解锁",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("OpenClaw Portable")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setStyleSheet(app_stylesheet())
        self.setFont(preferred_font())
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.trust_device_checkbox = QCheckBox("信任这台电脑，以后在此电脑上免输入密码")
        self.trust_device_checkbox.setChecked(True)
        self._title = title
        self._description = description
        self._button_text = button_text
        self._build_ui()

    @property
    def password(self) -> str:
        return self.password_input.text()

    @property
    def trust_device(self) -> bool:
        return self.trust_device_checkbox.isChecked()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(make_label(self._title, "SectionTitle", size=18, weight=700))
        layout.addWidget(make_label(self._description, "MutedText"))
        self.password_input.setPlaceholderText("管理密码")
        layout.addWidget(self.password_input)
        layout.addWidget(self.trust_device_checkbox)

        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel_button = make_button("取消")
        unlock_button = make_button(self._button_text, primary=True)
        cancel_button.clicked.connect(self.reject)
        unlock_button.clicked.connect(self.accept)
        actions.addWidget(cancel_button)
        actions.addWidget(unlock_button)
        layout.addLayout(actions)
