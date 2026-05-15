import re

with open("launcher/services/controller.py", "r", encoding="utf-8") as f:
    content = f.read()

# First fix the missing restore_update_backup block
missing_part = """        self._prepared = False
        return result.imported_version

    def restore_update_backup(self, backup_root):
        self.runtime_adapter.stop()
        result = self.restore_update_backup_service.restore_backup(backup_root)
        self._prepared = False
        return result.restored_version

    def check_for_updates(self):
        return self.online_update_service.check_for_updates(self._current_package_version())

    def download_and_import_update(self, metadata):
        self.runtime_adapter.stop()
        package_root = self.online_update_service.download_update_package(metadata)
        result = self.local_update_service.import_package(package_root)
        self._prepared = False
        return result.imported_version

    def install_feishu_channel(self):
        self._apply_channel_runtime_mutation(
            lambda: (
                self.feishu_channel_service.install_feishu_plugin(),
                self._reproject_feishu_runtime_if_configured(),
            )
        )
        return self.load_feishu_channel_state()

    def load_feishu_channel_state(self):
        if not self.store.is_first_run():
            self._refresh_feishu_runtime_status()
        state = self.feishu_channel_service.build_view_state()
        if self.runtime_mode != "openclaw" and state.enabled and state.status_label == "待启用":
            from dataclasses import replace
            return replace(
                state,
                status_detail="当前仍在 Node mock runtime。测试连接只校验 App 凭据；切到真实 OpenClaw runtime 并启动后，才能建立飞书私聊链路。",
            )
        return state

    def save_feishu_channel(self, app_id: str, app_secret: str, bot_app_name: str = "OpenClaw Bot"):
        current = self.feishu_channel_service.load_config()
"""

# Replace from `def import_update_package` down to `config = FeishuChannelConfig(`
pattern = re.compile(r'    def import_update_package\(.*?import_package\(package_root\).*?        config = FeishuChannelConfig\(', re.DOTALL)

def replacement(m):
    return "    def import_update_package(self, package_root):\n        self.runtime_adapter.stop()\n        result = self.local_update_service.import_package(package_root)\n" + missing_part + "        config = FeishuChannelConfig("

new_content = pattern.sub(replacement, content)

with open("launcher/services/controller.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Patched successfully")
