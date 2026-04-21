from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from launcher.models import WizardStep
from launcher.services.provider_registry import ProviderTemplate
from launcher.services.setup_wizard import SetupWizardSession
from launcher.ui.theme import app_stylesheet, preferred_font
from launcher.ui.widgets import HeroPanel, apply_card_shadow, make_button, make_label


DEFAULT_STEPS = [
    WizardStep("设置密码", "先为本地 WebUI 设置管理密码，默认安全从这里开始。"),
    WizardStep("选择 Provider", "选一个模型提供商，先把可用入口配置对。"),
    WizardStep("填写 API Key", "敏感信息只写入 state/.env，不落到公开配置文件。"),
    WizardStep("测试连接", "在进入主面板前先确认端口、网络和 Key 都正常。"),
    WizardStep("完成配置", "保存设置并准备启动本地运行时。"),
]


class SetupWizardWindow(QMainWindow):
    def __init__(self, provider_templates: list[ProviderTemplate] | None = None) -> None:
        super().__init__()
        self._steps = DEFAULT_STEPS
        self._stack = QStackedWidget()
        self._provider_templates = provider_templates or [
            ProviderTemplate("dashscope", "通义千问", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-max", 10),
            ProviderTemplate("deepseek", "DeepSeek", "https://api.deepseek.com/v1", "deepseek-chat", 20),
            ProviderTemplate("openrouter", "OpenRouter", "https://openrouter.ai/api/v1", "openai/gpt-4.1-mini", 30),
            ProviderTemplate("custom", "自定义", "", "", 99),
        ]
        self.session = SetupWizardSession(self._provider_templates)
        self.on_complete = None
        self.on_cancel = None
        self._build_ui()

    def step_titles(self) -> list[str]:
        return [step.title for step in self._steps]

    def bind_handlers(self, *, on_complete, on_cancel) -> None:
        self.on_complete = on_complete
        self.on_cancel = on_cancel

    def _build_ui(self) -> None:
        self.setWindowTitle("OpenClaw Portable")
        self.setMinimumSize(1240, 860)
        self.setStyleSheet(app_stylesheet())
        self.setFont(preferred_font())

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(22)

        layout.addWidget(
            HeroPanel(
                "首次启动向导",
                "把第一次配置做成一条清晰、低焦虑、对小白友好的路径。",
            )
        )

        shell = QFrame()
        shell.setObjectName("SectionCard")
        apply_card_shadow(shell, blur_radius=28, offset_y=10)
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(24, 24, 24, 24)
        shell_layout.setSpacing(16)

        shell_layout.addWidget(make_label("五步完成首启配置", "SectionTitle", size=18, weight=700))
        self.caption_label = make_label("每一步都只解决一件事，避免把太多技术细节一次性丢给用户。", "MutedText")
        shell_layout.addWidget(self.caption_label)

        for page in self._build_pages():
            self._stack.addWidget(page)
        shell_layout.addWidget(self._stack, stretch=1)

        footer = QHBoxLayout()
        footer.setSpacing(12)
        self.back_button = make_button("上一步")
        self.next_button = make_button("下一步", primary=True)
        self.skip_button = make_button("稍后再说")
        self.back_button.clicked.connect(self._go_previous)
        self.next_button.clicked.connect(self._handle_primary_action)
        self.skip_button.clicked.connect(self._handle_skip)
        footer.addWidget(self.back_button)
        footer.addWidget(self.next_button)
        footer.addStretch(1)
        footer.addWidget(self.skip_button)
        shell_layout.addLayout(footer)

        layout.addWidget(shell)
        self.setCentralWidget(root)
        self._sync_ui()

    def _build_pages(self) -> list[QWidget]:
        return [
            self._password_page(),
            self._provider_page(),
            self._api_key_page(),
            self._test_connection_page(),
            self._done_page(),
        ]

    def _password_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        layout.addWidget(make_label(self._steps[0].title, "SectionTitle", size=18, weight=700))
        layout.addWidget(make_label(self._steps[0].description, "MutedText"))

        form = QFormLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        form.addRow("管理密码", self.password_input)
        form.addRow("确认密码", self.confirm_password_input)
        layout.addLayout(form)
        layout.addStretch(1)
        return page

    def _provider_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        layout.addWidget(make_label(self._steps[1].title, "SectionTitle", size=18, weight=700))
        layout.addWidget(make_label(self._steps[1].description, "MutedText"))

        self.provider_combo = QComboBox()
        self.provider_combo.addItems([template.display_name for template in self._provider_templates])
        layout.addWidget(self.provider_combo)
        layout.addWidget(make_label("首版默认推荐通义千问，后续可在重新配置中调整。", "MutedText"))
        layout.addStretch(1)
        return page

    def _api_key_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        layout.addWidget(make_label(self._steps[2].title, "SectionTitle", size=18, weight=700))
        layout.addWidget(make_label(self._steps[2].description, "MutedText"))

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("请输入 API Key，或留空进入离线模式")
        layout.addWidget(self.api_key_input)
        layout.addWidget(make_label("后续真实运行时接入后，敏感值依旧只会落到 state/.env。", "MutedText"))
        layout.addStretch(1)
        return page

    def _test_connection_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        layout.addWidget(make_label(self._steps[3].title, "SectionTitle", size=18, weight=700))
        layout.addWidget(make_label(self._steps[3].description, "MutedText"))

        self.connection_output = QPlainTextEdit()
        self.connection_output.setReadOnly(True)
        self.connection_output.setPlainText("准备检查：端口、网络、Provider 与 API Key 是否可用。")
        layout.addWidget(self.connection_output)

        actions = QHBoxLayout()
        actions.setSpacing(12)
        self.test_button = make_button("开始测试", primary=True)
        self.offline_button = make_button("跳过并进入离线模式")
        self.test_button.clicked.connect(self._simulate_connection_test)
        self.offline_button.clicked.connect(self._switch_to_offline_mode)
        actions.addWidget(self.test_button)
        actions.addWidget(self.offline_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addStretch(1)
        return page

    def _done_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        layout.addWidget(make_label(self._steps[4].title, "SectionTitle", size=18, weight=700))
        layout.addWidget(make_label(self._steps[4].description, "MutedText"))

        summary = QLabel("配置文件将写入 state/openclaw.json，敏感信息写入 state/.env，随后准备进入主控制面板。")
        summary.setObjectName("MutedText")
        summary.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        summary.setWordWrap(True)
        layout.addWidget(summary)

        finish_row = QHBoxLayout()
        finish_row.setSpacing(12)
        self.finish_button = make_button("保存并启动", primary=True)
        self.save_button = make_button("仅保存配置")
        self.finish_button.clicked.connect(self._emit_complete)
        self.save_button.clicked.connect(self._emit_complete)
        finish_row.addWidget(self.finish_button)
        finish_row.addWidget(self.save_button)
        finish_row.addStretch(1)
        layout.addLayout(finish_row)
        layout.addStretch(1)
        return page

    def _sync_session_from_inputs(self) -> None:
        self.session.admin_password = self.password_input.text().strip()
        current_index = max(self.provider_combo.currentIndex(), 0)
        self.session.selected_provider_id = self._provider_templates[current_index].identifier
        self.session.api_key = self.api_key_input.text().strip()

    def _sync_ui(self) -> None:
        self._stack.setCurrentIndex(self.session.current_step)
        step = self._steps[self.session.current_step]
        self.caption_label.setText(step.description)
        self.back_button.setEnabled(self.session.current_step > 0)
        self.next_button.setVisible(self.session.current_step < len(self._steps) - 1)
        self.skip_button.setVisible(self.session.current_step < len(self._steps) - 1)

    def _go_previous(self) -> None:
        self._sync_session_from_inputs()
        self.session.previous_step()
        self._sync_ui()

    def _handle_primary_action(self) -> None:
        self._sync_session_from_inputs()
        self.session.next_step()
        self._sync_ui()

    def _handle_skip(self) -> None:
        if self.session.current_step == 2:
            self.api_key_input.clear()
        self._handle_primary_action()

    def _simulate_connection_test(self) -> None:
        self._sync_session_from_inputs()
        if self.session.api_key:
            self.connection_output.setPlainText("✅ 已模拟通过连接测试，后续接真实运行时时会替换为真实探测。")
        else:
            self.connection_output.setPlainText("⚠ 未提供 API Key，将以离线模式继续。")

    def _switch_to_offline_mode(self) -> None:
        self.api_key_input.clear()
        self._simulate_connection_test()

    def _emit_complete(self) -> None:
        self._sync_session_from_inputs()
        if self.on_complete:
            self.on_complete(*self.session.build_configuration())
