import os
import shutil
import unittest
import uuid
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from launcher.bootstrap import AppRoute, LauncherBootstrap
from launcher.core.config_store import LauncherConfig, LauncherConfigStore, SensitiveConfig
from launcher.core.paths import PortablePaths
from launcher.models import FeishuChannelState, LauncherViewState, QqChannelState, WechatChannelState, WecomChannelState
from launcher.ui.main_window import OpenClawLauncherWindow
from launcher.ui.wizard import SetupWizardWindow


def make_workspace_temp_dir() -> Path:
    temp_root = Path.cwd() / "tmp"
    temp_root.mkdir(exist_ok=True)
    created = temp_root / f"bootstrap-{uuid.uuid4().hex[:8]}"
    created.mkdir(parents=True, exist_ok=True)
    return created


def make_paths(temp_dir: Path) -> PortablePaths:
    return PortablePaths.for_root(temp_dir / "OpenClaw-Portable", temp_base=temp_dir / "system-temp")


def make_config(port: int = 18789) -> LauncherConfig:
    return LauncherConfig(
        admin_password="demo-pass",
        provider_id="dashscope",
        provider_name="通义千问",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-max",
        gateway_port=port,
        bind_host="127.0.0.1",
        first_run_completed=True,
    )


class LauncherBootstrapTests(unittest.TestCase):
    def test_routes_to_setup_wizard_on_first_run(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            bootstrap = LauncherBootstrap(make_paths(temp_dir))
            self.assertEqual(bootstrap.initial_route(), AppRoute.SETUP_WIZARD)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_routes_to_main_dashboard_when_config_exists(self) -> None:
        temp_dir = make_workspace_temp_dir()
        try:
            paths = make_paths(temp_dir)
            store = LauncherConfigStore(paths)
            store.save(make_config(), SensitiveConfig(api_key="sk-demo"))

            bootstrap = LauncherBootstrap(paths)
            self.assertEqual(bootstrap.initial_route(), AppRoute.MAIN_DASHBOARD)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class LauncherUiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_builds_main_window_with_primary_actions(self) -> None:
        window = OpenClawLauncherWindow()

        self.assertEqual(window.windowTitle(), "OpenClaw Portable")
        self.assertEqual(window.primary_action_texts(), ["启动服务", "停止服务", "重新启动"])
        self.assertEqual(window.secondary_action_texts(), ["打开 WebUI", "导出诊断", "检查更新", "导入更新包", "恢复更新备份", "恢复出厂", "重新配置"])
        self.assertIn("mock runtime", window.status_detail_label.text())

    def test_main_window_updates_status_detail_text(self) -> None:
        window = OpenClawLauncherWindow()
        updated_state = LauncherViewState(
            status_label="运行中",
            status_detail="本地运行时正在响应请求，已运行 01:05。",
            port_label="127.0.0.1:18789",
            runtime_detail="OpenClaw gateway / v2026.4.8",
            provider_label="通义千问 / qwen-max",
            message="当前正在使用真实 OpenClaw gateway，本地控制台由便携运行时提供。",
            webui_url="http://127.0.0.1:18791",
            offline_mode=False,
        )

        window.apply_view_state(updated_state)

        self.assertEqual(window.status_detail_label.text(), updated_state.status_detail)

    def test_main_window_disables_check_update_button_while_busy(self) -> None:
        window = OpenClawLauncherWindow()

        window.set_action_busy("check_update", True)

        self.assertFalse(window.check_update_button.isEnabled())
        self.assertEqual(window.check_update_button.text(), "正在检查...")

        window.set_action_busy("check_update", False)

        self.assertTrue(window.check_update_button.isEnabled())
        self.assertEqual(window.check_update_button.text(), "检查更新")

    def test_main_window_disables_runtime_buttons_while_starting(self) -> None:
        window = OpenClawLauncherWindow()

        window.set_action_busy("start_runtime", True)

        self.assertFalse(window.start_button.isEnabled())
        self.assertFalse(window.stop_button.isEnabled())
        self.assertFalse(window.restart_button.isEnabled())
        self.assertEqual(window.start_button.text(), "启动中...")

        window.set_action_busy("start_runtime", False)

        self.assertTrue(window.start_button.isEnabled())
        self.assertTrue(window.stop_button.isEnabled())
        self.assertTrue(window.restart_button.isEnabled())
        self.assertEqual(window.start_button.text(), "启动服务")

    def test_main_window_shows_feishu_channel_controls(self) -> None:
        window = OpenClawLauncherWindow()

        self.assertEqual(window.test_feishu_button.text(), "测试连接")
        self.assertEqual(window.enable_feishu_button.text(), "启用飞书私聊")
        self.assertEqual(window.open_feishu_help_button.text(), "接入帮助")

    def test_main_window_applies_feishu_channel_state(self) -> None:
        window = OpenClawLauncherWindow()
        state = FeishuChannelState(
            app_id="cli_xxx",
            app_secret="secret",
            bot_app_name="Support Bot",
            enabled=True,
            status_label="已连接",
            status_detail="飞书私聊链路已就绪，可接收私聊消息。",
        )

        window.apply_feishu_channel_state(state)

        self.assertEqual(window.feishu_app_id_input.text(), "cli_xxx")
        self.assertEqual(window.feishu_bot_name_input.text(), "Support Bot")
        self.assertEqual(window.feishu_status_label.text(), "已连接")
        self.assertFalse(window.enable_feishu_button.isEnabled())
        self.assertTrue(window.disable_feishu_button.isEnabled())

    def test_main_window_shows_wechat_qq_and_wecom_channel_controls(self) -> None:
        window = OpenClawLauncherWindow()

        self.assertEqual(window.install_wechat_button.text(), "安装微信插件")
        self.assertEqual(window.login_wechat_button.text(), "扫码登录")
        self.assertEqual(window.open_wechat_help_button.text(), "接入帮助")
        self.assertEqual(window.qq_app_id_input.placeholderText(), "QQ Bot AppID")
        self.assertEqual(window.open_qq_help_button.text(), "接入帮助")
        self.assertEqual(window.install_wecom_button.text(), "安装企业微信插件")

    def test_main_window_applies_wechat_qq_and_wecom_states(self) -> None:
        window = OpenClawLauncherWindow()

        window.apply_wechat_channel_state(
            WechatChannelState(enabled=True, installed=True, status_label="已启用", status_detail="wechat ready")
        )
        window.apply_qq_channel_state(
            QqChannelState(app_id="123456", app_secret="secret", enabled=True, status_label="已启用", status_detail="qq ready")
        )
        window.apply_wecom_channel_state(
            WecomChannelState(
                bot_id="wwbot",
                secret="wecom-secret",
                enabled=True,
                connection_mode="websocket",
                status_label="已启用",
                status_detail="wecom ready",
            )
        )

        self.assertEqual(window.wechat_status_label.text(), "已启用")
        self.assertFalse(window.enable_wechat_button.isEnabled())
        self.assertEqual(window.qq_app_id_input.text(), "123456")
        self.assertFalse(window.enable_qq_button.isEnabled())
        self.assertEqual(window.wecom_bot_id_input.text(), "wwbot")
        self.assertFalse(window.enable_wecom_button.isEnabled())

    def test_builds_wizard_with_expected_steps(self) -> None:
        window = SetupWizardWindow()

        self.assertEqual(window.step_titles(), ["设置密码", "选择 Provider", "填写 API Key", "测试连接", "完成配置"])


    def test_feishu_offline_help_page_is_packaged(self) -> None:
        help_page = Path.cwd() / "assets" / "guide" / "setup-feishu.html"

        self.assertTrue(help_page.exists())
        self.assertIn("飞书私聊接入帮助", help_page.read_text(encoding="utf-8"))

    def test_wechat_and_qq_offline_help_pages_are_packaged(self) -> None:
        wechat_help = Path.cwd() / "assets" / "guide" / "setup-wechat.html"
        qq_help = Path.cwd() / "assets" / "guide" / "setup-qq.html"

        self.assertTrue(wechat_help.exists())
        self.assertTrue(qq_help.exists())
        self.assertIn("微信", wechat_help.read_text(encoding="utf-8"))
        self.assertIn("QQ Bot", qq_help.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
