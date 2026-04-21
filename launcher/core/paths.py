from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PortablePaths:
    project_root: Path
    runtime_dir: Path
    state_dir: Path
    assets_dir: Path
    tools_dir: Path
    temp_root: Path
    logs_dir: Path
    cache_dir: Path
    config_file: Path
    env_file: Path
    provider_templates_dir: Path
    workspace_dir: Path
    runtime_config_file: Path | None = None
    feishu_channel_dir: Path | None = None
    feishu_channel_config_file: Path | None = None
    feishu_channel_status_file: Path | None = None

    def __post_init__(self) -> None:
        feishu_channel_dir = self.feishu_channel_dir or (self.state_dir / "channels" / "feishu")
        runtime_config_file = self.runtime_config_file or (self.state_dir / "runtime" / "openclaw.json")
        feishu_channel_config_file = self.feishu_channel_config_file or (feishu_channel_dir / "config.json")
        feishu_channel_status_file = self.feishu_channel_status_file or (feishu_channel_dir / "status.json")
        object.__setattr__(self, "runtime_config_file", runtime_config_file)
        object.__setattr__(self, "feishu_channel_dir", feishu_channel_dir)
        object.__setattr__(self, "feishu_channel_config_file", feishu_channel_config_file)
        object.__setattr__(self, "feishu_channel_status_file", feishu_channel_status_file)

    @classmethod
    def for_root(cls, project_root: Path, temp_base: Path | None = None) -> "PortablePaths":
        resolved_temp_base = temp_base or Path(os.environ.get("TEMP") or tempfile.gettempdir())
        temp_root = resolved_temp_base / "OpenClawPortable"
        state_dir = project_root / "state"
        feishu_channel_dir = state_dir / "channels" / "feishu"
        return cls(
            project_root=project_root,
            runtime_dir=project_root / "runtime",
            state_dir=state_dir,
            assets_dir=project_root / "assets",
            tools_dir=project_root / "tools",
            temp_root=temp_root,
            logs_dir=temp_root / "logs",
            cache_dir=temp_root / "cache",
            config_file=state_dir / "openclaw.json",
            runtime_config_file=state_dir / "runtime" / "openclaw.json",
            env_file=state_dir / ".env",
            provider_templates_dir=state_dir / "provider-templates",
            workspace_dir=state_dir / "workspace",
            feishu_channel_dir=feishu_channel_dir,
            feishu_channel_config_file=feishu_channel_dir / "config.json",
            feishu_channel_status_file=feishu_channel_dir / "status.json",
        )

    def ensure_directories(self) -> None:
        directories = (
            self.project_root,
            self.runtime_dir,
            self.state_dir,
            self.assets_dir,
            self.tools_dir,
            self.temp_root,
            self.logs_dir,
            self.cache_dir,
            self.provider_templates_dir,
            self.workspace_dir,
            self.workspace_dir / "skills",
            self.workspace_dir / "memory",
            self.state_dir / "sessions",
            self.state_dir / "channels",
            self.runtime_config_file.parent,
            self.state_dir / "backups",
            self.feishu_channel_dir,
        )
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
