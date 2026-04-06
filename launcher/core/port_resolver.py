from __future__ import annotations

import socket
from dataclasses import dataclass


@dataclass(frozen=True)
class PortResolution:
    port: int
    message: str | None


class PortResolver:
    def resolve(self, host: str, requested_port: int, max_attempts: int = 20) -> PortResolution:
        if self._is_available(host, requested_port):
            return PortResolution(port=requested_port, message=None)

        for candidate in range(requested_port + 1, requested_port + max_attempts + 1):
            if self._is_available(host, candidate):
                return PortResolution(
                    port=candidate,
                    message=f"端口 {requested_port} 被占用，已自动切换到 {candidate}",
                )

        raise RuntimeError(f"无法为 {host} 找到可用端口，起始端口为 {requested_port}")

    def _is_available(self, host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind((host, port))
            except OSError:
                return False
        return True
