from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from launcher.core.config_store import LauncherConfig
from launcher.core.paths import PortablePaths


@dataclass(frozen=True)
class RuntimeHealth:
    ok: bool
    details: dict[str, Any] | None = None
    error: str | None = None


@dataclass(frozen=True)
class RuntimeStatus:
    state: str
    port: int | None = None
    message: str | None = None
    pid: int | None = None
    uptime_seconds: int | None = None


class RuntimeAdapter(ABC):
    @abstractmethod
    def prepare(self, config: LauncherConfig, paths: PortablePaths) -> None:
        raise NotImplementedError

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def status(self) -> RuntimeStatus:
        raise NotImplementedError

    @abstractmethod
    def webui_url(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def healthcheck(self) -> RuntimeHealth:
        raise NotImplementedError
