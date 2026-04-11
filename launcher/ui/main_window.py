from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from launcher.models import LauncherViewState
from launcher.ui.theme import app_stylesheet, preferred_font
from launcher.ui.widgets import HeroPanel, MetricCard, apply_card_shadow, make_button, make_label


DEFAULT_VIEW_STATE = LauncherViewState(
    status_label="运行中",
    status_detail="当前正在使用本地 mock runtime 进行联调。",
    port_label="127.0.0.1:18789",
    runtime_detail="Node mock runtime / Phase 1 开发版",
    provider_label="通义千问 / qwen-max",
    message="当前为开发版 MVP，已为真实 OpenClaw 适配层预留边界。",
    webui_url="http://127.0.0.1:18789",
    offline_mode=False,
)


class OpenClawLauncherWindow(QMainWindow):
    def __init__(self, view_state: LauncherViewState | None = None) -> None:
        super().__init__()
        self.view_state = view_state or DEFAULT_VIEW_STATE
        self._primary_buttons: list[QPushButton] = []
        self._secondary_buttons: list[QPushButton] = []
        self.start_button: QPushButton | None = None
        self.stop_button: QPushButton | None = None
        self.restart_button: QPushButton | None = None
        self.open_webui_button: QPushButton | None = None
        self.export_diagnostics_button: QPushButton | None = None
        self.import_update_button: QPushButton | None = None
        self.restore_update_backup_button: QPushButton | None = None
        self.factory_reset_button: QPushButton | None = None
        self.reconfigure_button: QPushButton | None = None
        self._build_ui()

    def primary_action_texts(self) -> list[str]:
        return [button.text() for button in self._primary_buttons]

    def secondary_action_texts(self) -> list[str]:
        return [button.text() for button in self._secondary_buttons]

    def bind_handlers(self, *, on_start, on_stop, on_restart, on_open_webui, on_export_diagnostics, on_import_update, on_restore_update_backup, on_factory_reset, on_reconfigure) -> None:
        self.start_button.clicked.connect(on_start)
        self.stop_button.clicked.connect(on_stop)
        self.restart_button.clicked.connect(on_restart)
        self.open_webui_button.clicked.connect(on_open_webui)
        self.export_diagnostics_button.clicked.connect(on_export_diagnostics)
        self.import_update_button.clicked.connect(on_import_update)
        self.restore_update_backup_button.clicked.connect(on_restore_update_backup)
        self.factory_reset_button.clicked.connect(on_factory_reset)
        self.reconfigure_button.clicked.connect(on_reconfigure)

    def apply_view_state(self, view_state: LauncherViewState) -> None:
        self.view_state = view_state
        self.status_card.set_value(view_state.status_label)
        self.port_card.set_value(view_state.port_label)
        self.runtime_card.set_value(view_state.runtime_detail)
        self.provider_card.set_value(view_state.provider_label)
        self.message_label.setText(view_state.message)
        self.status_detail_label.setText(view_state.status_detail)
        self.footnote_label.setText(
            f"地址 {view_state.webui_url or '尚未启动'}  ·  "
            f"{'离线模式已开启' if view_state.offline_mode else '已配置 API Key，可进入联调'}"
        )

    def _build_ui(self) -> None:
        self.setWindowTitle("OpenClaw Portable")
        self.setMinimumSize(1240, 860)
        self.setStyleSheet(app_stylesheet())
        self.setFont(preferred_font())

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(22)

        hero = HeroPanel(
            "把复杂启动过程，包进一个可靠的桌面控制台。",
            "面向小白用户的便携启动器外壳，默认安全、默认清晰、默认可恢复。",
        )
        layout.addWidget(hero)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(16)
        metrics.setVerticalSpacing(16)
        self.status_card = MetricCard("服务状态", self.view_state.status_label)
        self.port_card = MetricCard("监听地址", self.view_state.port_label)
        self.runtime_card = MetricCard("运行时", self.view_state.runtime_detail)
        self.provider_card = MetricCard("当前模型", self.view_state.provider_label)
        metrics.addWidget(self.status_card, 0, 0)
        metrics.addWidget(self.port_card, 0, 1)
        metrics.addWidget(self.runtime_card, 0, 2)
        metrics.addWidget(self.provider_card, 0, 3)
        layout.addLayout(metrics)

        control_card = QFrame()
        control_card.setObjectName("SectionCard")
        apply_card_shadow(control_card, blur_radius=28, offset_y=10)
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(24, 24, 24, 24)
        control_layout.setSpacing(18)
        control_layout.addWidget(make_label("主控制台", "HeroTitle", size=18, weight=700))
        self.message_label = make_label(self.view_state.message, "MutedText")
        control_layout.addWidget(self.message_label)
        self.status_detail_label = make_label(self.view_state.status_detail, "MutedText")
        control_layout.addWidget(self.status_detail_label)

        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        self.start_button = make_button("启动服务", primary=True)
        self.stop_button = make_button("停止服务")
        self.restart_button = make_button("重新启动")
        self.open_webui_button = make_button("打开 WebUI", subtle=True)
        self.export_diagnostics_button = make_button("导出诊断")
        self.import_update_button = make_button("导入更新包")
        self.restore_update_backup_button = make_button("恢复更新备份")
        self.factory_reset_button = make_button("恢复出厂")
        self.reconfigure_button = make_button("重新配置")
        self._primary_buttons = [self.start_button, self.stop_button, self.restart_button]
        self._secondary_buttons = [
            self.open_webui_button,
            self.export_diagnostics_button,
            self.import_update_button,
            self.restore_update_backup_button,
            self.factory_reset_button,
            self.reconfigure_button,
        ]
        for button in self._primary_buttons + self._secondary_buttons:
            button_row.addWidget(button)
        button_row.addStretch(1)
        control_layout.addLayout(button_row)

        self.footnote_label = QLabel(
            f"地址 {self.view_state.webui_url}  ·  "
            f"{'离线模式已开启' if self.view_state.offline_mode else '已配置 API Key，可进入联调'}"
        )
        self.footnote_label.setObjectName("MutedText")
        self.footnote_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        control_layout.addWidget(self.footnote_label)

        layout.addWidget(control_card)
        layout.addStretch(1)

        self.setCentralWidget(root)
