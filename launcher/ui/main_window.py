from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from launcher.models import FeishuChannelState, LauncherViewState, QqChannelState, WechatChannelState, WecomChannelState
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
        self.check_update_button: QPushButton | None = None
        self.import_update_button: QPushButton | None = None
        self.restore_update_backup_button: QPushButton | None = None
        self.factory_reset_button: QPushButton | None = None
        self.reconfigure_button: QPushButton | None = None
        self.feishu_app_id_input: QLineEdit | None = None
        self.feishu_app_secret_input: QLineEdit | None = None
        self.feishu_bot_name_input: QLineEdit | None = None
        self.feishu_status_label: QLabel | None = None
        self.feishu_status_detail_label: QLabel | None = None
        self.save_feishu_button: QPushButton | None = None
        self.test_feishu_button: QPushButton | None = None
        self.enable_feishu_button: QPushButton | None = None
        self.disable_feishu_button: QPushButton | None = None
        self.open_feishu_help_button: QPushButton | None = None
        self.wechat_status_label: QLabel | None = None
        self.wechat_status_detail_label: QLabel | None = None
        self.install_wechat_button: QPushButton | None = None
        self.login_wechat_button: QPushButton | None = None
        self.confirm_wechat_button: QPushButton | None = None
        self.open_wechat_help_button: QPushButton | None = None
        self.enable_wechat_button: QPushButton | None = None
        self.disable_wechat_button: QPushButton | None = None
        self.qq_app_id_input: QLineEdit | None = None
        self.qq_app_secret_input: QLineEdit | None = None
        self.qq_status_label: QLabel | None = None
        self.qq_status_detail_label: QLabel | None = None
        self.open_qq_help_button: QPushButton | None = None
        self.save_qq_button: QPushButton | None = None
        self.test_qq_button: QPushButton | None = None
        self.enable_qq_button: QPushButton | None = None
        self.disable_qq_button: QPushButton | None = None
        self.wecom_bot_id_input: QLineEdit | None = None
        self.wecom_secret_input: QLineEdit | None = None
        self.wecom_status_label: QLabel | None = None
        self.wecom_status_detail_label: QLabel | None = None
        self.install_wecom_button: QPushButton | None = None
        self.save_wecom_button: QPushButton | None = None
        self.test_wecom_button: QPushButton | None = None
        self.enable_wecom_button: QPushButton | None = None
        self.disable_wecom_button: QPushButton | None = None
        self._buttons_by_action: dict[str, QPushButton] = {}
        self._default_button_texts: dict[QPushButton, str] = {}
        self._build_ui()

    def primary_action_texts(self) -> list[str]:
        return [button.text() for button in self._primary_buttons]

    def secondary_action_texts(self) -> list[str]:
        return [button.text() for button in self._secondary_buttons]

    def bind_handlers(self, *, on_start, on_stop, on_restart, on_open_webui, on_export_diagnostics, on_check_update, on_import_update, on_restore_update_backup, on_factory_reset, on_reconfigure) -> None:
        self.start_button.clicked.connect(on_start)
        self.stop_button.clicked.connect(on_stop)
        self.restart_button.clicked.connect(on_restart)
        self.open_webui_button.clicked.connect(on_open_webui)
        self.export_diagnostics_button.clicked.connect(on_export_diagnostics)
        self.check_update_button.clicked.connect(on_check_update)
        self.import_update_button.clicked.connect(on_import_update)
        self.restore_update_backup_button.clicked.connect(on_restore_update_backup)
        self.factory_reset_button.clicked.connect(on_factory_reset)
        self.reconfigure_button.clicked.connect(on_reconfigure)

    def bind_feishu_handlers(self, *, on_save, on_test, on_enable, on_disable, on_open_help) -> None:
        self.save_feishu_button.clicked.connect(on_save)
        self.test_feishu_button.clicked.connect(on_test)
        self.enable_feishu_button.clicked.connect(on_enable)
        self.disable_feishu_button.clicked.connect(on_disable)
        self.open_feishu_help_button.clicked.connect(on_open_help)

    def bind_social_channel_handlers(
        self,
        *,
        on_install_wechat,
        on_login_wechat,
        on_confirm_wechat,
        on_open_wechat_help,
        on_enable_wechat,
        on_disable_wechat,
        on_open_qq_help,
        on_save_qq,
        on_test_qq,
        on_enable_qq,
        on_disable_qq,
        on_install_wecom,
        on_save_wecom,
        on_test_wecom,
        on_enable_wecom,
        on_disable_wecom,
    ) -> None:
        self.install_wechat_button.clicked.connect(on_install_wechat)
        self.login_wechat_button.clicked.connect(on_login_wechat)
        self.confirm_wechat_button.clicked.connect(on_confirm_wechat)
        self.open_wechat_help_button.clicked.connect(on_open_wechat_help)
        self.enable_wechat_button.clicked.connect(on_enable_wechat)
        self.disable_wechat_button.clicked.connect(on_disable_wechat)
        self.open_qq_help_button.clicked.connect(on_open_qq_help)
        self.save_qq_button.clicked.connect(on_save_qq)
        self.test_qq_button.clicked.connect(on_test_qq)
        self.enable_qq_button.clicked.connect(on_enable_qq)
        self.disable_qq_button.clicked.connect(on_disable_qq)
        self.install_wecom_button.clicked.connect(on_install_wecom)
        self.save_wecom_button.clicked.connect(on_save_wecom)
        self.test_wecom_button.clicked.connect(on_test_wecom)
        self.enable_wecom_button.clicked.connect(on_enable_wecom)
        self.disable_wecom_button.clicked.connect(on_disable_wecom)

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

    def apply_feishu_channel_state(self, state: FeishuChannelState) -> None:
        self.feishu_app_id_input.setText(state.app_id)
        self.feishu_app_secret_input.setText(state.app_secret)
        self.feishu_bot_name_input.setText(state.bot_app_name)
        self.feishu_status_label.setText(state.status_label)
        self.feishu_status_detail_label.setText(state.status_detail)
        self.enable_feishu_button.setEnabled(not state.enabled)
        self.disable_feishu_button.setEnabled(state.enabled)

    def apply_wechat_channel_state(self, state: WechatChannelState) -> None:
        self.wechat_status_label.setText(state.status_label)
        self.wechat_status_detail_label.setText(state.status_detail)
        self.enable_wechat_button.setEnabled(not state.enabled)
        self.disable_wechat_button.setEnabled(state.enabled)

    def apply_qq_channel_state(self, state: QqChannelState) -> None:
        self.qq_app_id_input.setText(state.app_id)
        self.qq_app_secret_input.setText(state.app_secret)
        self.qq_status_label.setText(state.status_label)
        self.qq_status_detail_label.setText(state.status_detail)
        self.enable_qq_button.setEnabled(not state.enabled)
        self.disable_qq_button.setEnabled(state.enabled)

    def apply_wecom_channel_state(self, state: WecomChannelState) -> None:
        self.wecom_bot_id_input.setText(state.bot_id)
        self.wecom_secret_input.setText(state.secret)
        self.wecom_status_label.setText(state.status_label)
        self.wecom_status_detail_label.setText(state.status_detail)
        self.enable_wecom_button.setEnabled(not state.enabled)
        self.disable_wecom_button.setEnabled(state.enabled)

    def set_action_busy(self, action: str, busy: bool) -> None:
        runtime_actions = {
            "start_runtime": (self.start_button, "启动中..."),
            "stop_runtime": (self.stop_button, "停止中..."),
            "restart_runtime": (self.restart_button, "重启中..."),
        }
        if action in runtime_actions:
            active_button, busy_text = runtime_actions[action]
            for button in (self.start_button, self.stop_button, self.restart_button):
                button.setEnabled(not busy)
                button.setText(self._default_button_texts[button])
            if busy:
                active_button.setText(busy_text)
            return
        button = self._buttons_by_action.get(action)
        if not button:
            return
        button.setEnabled(not busy)
        if action == "check_update":
            button.setText("正在检查..." if busy else "检查更新")
        elif action == "import_update":
            button.setText("正在导入..." if busy else "导入更新包")
        elif action == "restore_update_backup":
            button.setText("正在恢复..." if busy else "恢复更新备份")

        elif action == "test_feishu_channel":
            button.setText("正在测试..." if busy else "测试连接")
        elif action == "enable_feishu_channel":
            button.setText("正在启用..." if busy else "启用飞书私聊")

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
        self.check_update_button = make_button("检查更新")
        self.import_update_button = make_button("导入更新包")
        self.restore_update_backup_button = make_button("恢复更新备份")
        self.factory_reset_button = make_button("恢复出厂")
        self.reconfigure_button = make_button("重新配置")
        self._default_button_texts = {
            button: button.text()
            for button in (
                self.start_button,
                self.stop_button,
                self.restart_button,
                self.check_update_button,
                self.import_update_button,
                self.restore_update_backup_button,
            )
        }
        self._buttons_by_action = {
            "check_update": self.check_update_button,
            "import_update": self.import_update_button,
            "restore_update_backup": self.restore_update_backup_button,
        }
        self._primary_buttons = [self.start_button, self.stop_button, self.restart_button]
        self._secondary_buttons = [
            self.open_webui_button,
            self.export_diagnostics_button,
            self.check_update_button,
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

        feishu_card = QFrame()
        feishu_card.setObjectName("SectionCard")
        apply_card_shadow(feishu_card, blur_radius=24, offset_y=8)
        feishu_layout = QVBoxLayout(feishu_card)
        feishu_layout.setContentsMargins(24, 24, 24, 24)
        feishu_layout.setSpacing(14)
        feishu_layout.addWidget(make_label("飞书私聊渠道", "HeroTitle", size=18, weight=700))
        feishu_layout.addWidget(make_label("配置飞书应用凭据，测试通过后启用私聊 Bot。", "MutedText"))

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        self.feishu_app_id_input = QLineEdit()
        self.feishu_app_id_input.setPlaceholderText("cli_xxx")
        self.feishu_app_secret_input = QLineEdit()
        self.feishu_app_secret_input.setPlaceholderText("App Secret")
        self.feishu_app_secret_input.setEchoMode(QLineEdit.Password)
        self.feishu_bot_name_input = QLineEdit()
        self.feishu_bot_name_input.setPlaceholderText("OpenClaw Bot")
        form.addWidget(make_label("App ID", "MetricLabel"), 0, 0)
        form.addWidget(self.feishu_app_id_input, 0, 1)
        form.addWidget(make_label("App Secret", "MetricLabel"), 1, 0)
        form.addWidget(self.feishu_app_secret_input, 1, 1)
        form.addWidget(make_label("Bot 名称", "MetricLabel"), 2, 0)
        form.addWidget(self.feishu_bot_name_input, 2, 1)
        feishu_layout.addLayout(form)

        self.feishu_status_label = make_label("未配置", "HeroTitle", size=14, weight=700)
        self.feishu_status_detail_label = make_label(
            "填写 App ID 和 App Secret 后，先测试连接再启用飞书私聊。",
            "MutedText",
        )
        feishu_layout.addWidget(self.feishu_status_label)
        feishu_layout.addWidget(self.feishu_status_detail_label)

        feishu_actions = QHBoxLayout()
        feishu_actions.setSpacing(12)
        self.save_feishu_button = make_button("保存飞书配置")
        self.test_feishu_button = make_button("测试连接", primary=True)
        self.enable_feishu_button = make_button("启用飞书私聊")
        self.disable_feishu_button = make_button("停用")
        self.open_feishu_help_button = make_button("接入帮助", subtle=True)
        for button in (
            self.save_feishu_button,
            self.test_feishu_button,
            self.enable_feishu_button,
            self.disable_feishu_button,
            self.open_feishu_help_button,
        ):
            feishu_actions.addWidget(button)
        feishu_actions.addStretch(1)
        feishu_layout.addLayout(feishu_actions)
        self._buttons_by_action.update(
            {
                "test_feishu_channel": self.test_feishu_button,
                "enable_feishu_channel": self.enable_feishu_button,
            }
        )
        self._default_button_texts.update(
            {
                self.test_feishu_button: self.test_feishu_button.text(),
                self.enable_feishu_button: self.enable_feishu_button.text(),
            }
        )
        layout.addWidget(feishu_card)

        social_grid = QGridLayout()
        social_grid.setHorizontalSpacing(16)
        social_grid.setVerticalSpacing(16)

        wechat_card = QFrame()
        wechat_card.setObjectName("SectionCard")
        apply_card_shadow(wechat_card, blur_radius=20, offset_y=6)
        wechat_layout = QVBoxLayout(wechat_card)
        wechat_layout.setContentsMargins(24, 24, 24, 24)
        wechat_layout.setSpacing(12)
        wechat_layout.addWidget(make_label("微信 ClawBot", "HeroTitle", size=18, weight=700))
        wechat_layout.addWidget(make_label("安装腾讯微信通道插件，扫码后用私聊连接 OpenClaw。", "MutedText"))
        self.wechat_status_label = make_label("未安装", "HeroTitle", size=14, weight=700)
        self.wechat_status_detail_label = make_label("先安装微信插件，再打开扫码窗口完成登录。", "MutedText")
        wechat_layout.addWidget(self.wechat_status_label)
        wechat_layout.addWidget(self.wechat_status_detail_label)
        wechat_actions = QHBoxLayout()
        wechat_actions.setSpacing(10)
        self.install_wechat_button = make_button("安装微信插件")
        self.login_wechat_button = make_button("扫码登录", primary=True)
        self.confirm_wechat_button = make_button("确认已扫码")
        self.open_wechat_help_button = make_button("接入帮助", subtle=True)
        self.enable_wechat_button = make_button("启用微信")
        self.disable_wechat_button = make_button("停用")
        for button in (
            self.install_wechat_button,
            self.login_wechat_button,
            self.confirm_wechat_button,
            self.open_wechat_help_button,
            self.enable_wechat_button,
            self.disable_wechat_button,
        ):
            wechat_actions.addWidget(button)
        wechat_actions.addStretch(1)
        wechat_layout.addLayout(wechat_actions)

        qq_card = QFrame()
        qq_card.setObjectName("SectionCard")
        apply_card_shadow(qq_card, blur_radius=20, offset_y=6)
        qq_layout = QVBoxLayout(qq_card)
        qq_layout.setContentsMargins(24, 24, 24, 24)
        qq_layout.setSpacing(12)
        qq_layout.addWidget(make_label("QQ Bot", "HeroTitle", size=18, weight=700))
        qq_layout.addWidget(make_label("QQ 扩展已随包内置，填入开放平台 AppID 和 AppSecret 即可启用。", "MutedText"))
        qq_form = QGridLayout()
        qq_form.setHorizontalSpacing(12)
        qq_form.setVerticalSpacing(10)
        self.qq_app_id_input = QLineEdit()
        self.qq_app_id_input.setPlaceholderText("QQ Bot AppID")
        self.qq_app_secret_input = QLineEdit()
        self.qq_app_secret_input.setPlaceholderText("AppSecret")
        self.qq_app_secret_input.setEchoMode(QLineEdit.Password)
        qq_form.addWidget(make_label("AppID", "MetricLabel"), 0, 0)
        qq_form.addWidget(self.qq_app_id_input, 0, 1)
        qq_form.addWidget(make_label("AppSecret", "MetricLabel"), 1, 0)
        qq_form.addWidget(self.qq_app_secret_input, 1, 1)
        qq_layout.addLayout(qq_form)
        self.qq_status_label = make_label("未配置", "HeroTitle", size=14, weight=700)
        self.qq_status_detail_label = make_label("创建 QQ 机器人后，把 AppID 和 AppSecret 填到这里。", "MutedText")
        qq_layout.addWidget(self.qq_status_label)
        qq_layout.addWidget(self.qq_status_detail_label)
        qq_actions = QHBoxLayout()
        qq_actions.setSpacing(10)
        self.open_qq_help_button = make_button("接入帮助", subtle=True)
        self.save_qq_button = make_button("保存 QQ 配置")
        self.test_qq_button = make_button("检查 QQ 配置")
        self.enable_qq_button = make_button("启用 QQ", primary=True)
        self.disable_qq_button = make_button("停用")
        for button in (
            self.open_qq_help_button,
            self.save_qq_button,
            self.test_qq_button,
            self.enable_qq_button,
            self.disable_qq_button,
        ):
            qq_actions.addWidget(button)
        qq_actions.addStretch(1)
        qq_layout.addLayout(qq_actions)

        wecom_card = QFrame()
        wecom_card.setObjectName("SectionCard")
        apply_card_shadow(wecom_card, blur_radius=20, offset_y=6)
        wecom_layout = QVBoxLayout(wecom_card)
        wecom_layout.setContentsMargins(24, 24, 24, 24)
        wecom_layout.setSpacing(12)
        wecom_layout.addWidget(make_label("企业微信", "HeroTitle", size=18, weight=700))
        wecom_layout.addWidget(make_label("安装企业微信插件后，填入机器人凭据启用 WebSocket 通道。", "MutedText"))
        wecom_form = QGridLayout()
        wecom_form.setHorizontalSpacing(12)
        wecom_form.setVerticalSpacing(10)
        self.wecom_bot_id_input = QLineEdit()
        self.wecom_bot_id_input.setPlaceholderText("Bot ID")
        self.wecom_secret_input = QLineEdit()
        self.wecom_secret_input.setPlaceholderText("Secret")
        self.wecom_secret_input.setEchoMode(QLineEdit.Password)
        wecom_form.addWidget(make_label("Bot ID", "MetricLabel"), 0, 0)
        wecom_form.addWidget(self.wecom_bot_id_input, 0, 1)
        wecom_form.addWidget(make_label("Secret", "MetricLabel"), 1, 0)
        wecom_form.addWidget(self.wecom_secret_input, 1, 1)
        wecom_layout.addLayout(wecom_form)
        self.wecom_status_label = make_label("未配置", "HeroTitle", size=14, weight=700)
        self.wecom_status_detail_label = make_label("先安装企业微信插件，再填写凭据启用。", "MutedText")
        wecom_layout.addWidget(self.wecom_status_label)
        wecom_layout.addWidget(self.wecom_status_detail_label)
        wecom_actions = QHBoxLayout()
        wecom_actions.setSpacing(10)
        self.install_wecom_button = make_button("安装企业微信插件")
        self.save_wecom_button = make_button("保存企业微信配置")
        self.test_wecom_button = make_button("检查企业微信配置")
        self.enable_wecom_button = make_button("启用企业微信", primary=True)
        self.disable_wecom_button = make_button("停用")
        for button in (
            self.install_wecom_button,
            self.save_wecom_button,
            self.test_wecom_button,
            self.enable_wecom_button,
            self.disable_wecom_button,
        ):
            wecom_actions.addWidget(button)
        wecom_actions.addStretch(1)
        wecom_layout.addLayout(wecom_actions)

        social_grid.addWidget(wechat_card, 0, 0)
        social_grid.addWidget(qq_card, 0, 1)
        social_grid.addWidget(wecom_card, 1, 0, 1, 2)
        layout.addLayout(social_grid)

        self._buttons_by_action.update(
            {
                "install_wechat_channel": self.install_wechat_button,
                "login_wechat_channel": self.login_wechat_button,
                "confirm_wechat_channel": self.confirm_wechat_button,
                "enable_wechat_channel": self.enable_wechat_button,
                "test_qq_channel": self.test_qq_button,
                "enable_qq_channel": self.enable_qq_button,
                "install_wecom_channel": self.install_wecom_button,
                "test_wecom_channel": self.test_wecom_button,
                "enable_wecom_channel": self.enable_wecom_button,
            }
        )
        self._default_button_texts.update(
            {
                self.install_wechat_button: self.install_wechat_button.text(),
                self.login_wechat_button: self.login_wechat_button.text(),
                self.confirm_wechat_button: self.confirm_wechat_button.text(),
                self.enable_wechat_button: self.enable_wechat_button.text(),
                self.test_qq_button: self.test_qq_button.text(),
                self.enable_qq_button: self.enable_qq_button.text(),
                self.install_wecom_button: self.install_wecom_button.text(),
                self.test_wecom_button: self.test_wecom_button.text(),
                self.enable_wecom_button: self.enable_wecom_button.text(),
            }
        )
        layout.addStretch(1)

        self.setCentralWidget(root)
