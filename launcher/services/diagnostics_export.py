from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from launcher.core.config_store import LauncherConfigStore
from launcher.core.paths import PortablePaths


class DiagnosticsExporter:
    def __init__(
        self,
        paths: PortablePaths,
        *,
        store: LauncherConfigStore | None = None,
        runtime_mode: str = "mock",
    ) -> None:
        self.paths = paths
        self.store = store or LauncherConfigStore(paths)
        self.runtime_mode = runtime_mode

    def export_bundle(self) -> Path:
        self.paths.ensure_directories()
        export_dir = self.paths.state_dir / "backups"
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        bundle_path = export_dir / f"openclaw-diagnostics-{timestamp}.zip"
        logs = sorted(path for path in self.paths.logs_dir.glob("*.log") if path.is_file())

        with ZipFile(bundle_path, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr(
                "manifest.json",
                json.dumps(
                    {
                        "createdAt": datetime.now().isoformat(timespec="seconds"),
                        "runtimeMode": self.runtime_mode,
                        "logsIncluded": [path.name for path in logs],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            archive.writestr(
                "config-summary.json",
                json.dumps(self._config_summary(), ensure_ascii=False, indent=2),
            )
            version_file = self.paths.project_root / "version.json"
            if version_file.exists():
                archive.writestr("version.json", version_file.read_text(encoding="utf-8"))
            for log_file in logs:
                archive.write(log_file, arcname=f"logs/{log_file.name}")
        return bundle_path

    def _config_summary(self) -> dict[str, object]:
        if self.store.is_first_run():
            return {
                "firstRun": True,
                "runtimeMode": self.runtime_mode,
                "apiKeyConfigured": False,
                "adminPasswordConfigured": False,
            }

        config, sensitive = self.store.load()
        return {
            "firstRun": False,
            "runtimeMode": self.runtime_mode,
            "providerId": config.provider_id,
            "providerName": config.provider_name,
            "baseUrl": config.base_url,
            "model": config.model,
            "gatewayPort": config.gateway_port,
            "bindHost": config.bind_host,
            "firstRunCompleted": config.first_run_completed,
            "apiKeyConfigured": bool(sensitive.api_key),
            "adminPasswordConfigured": bool(config.admin_password),
        }
