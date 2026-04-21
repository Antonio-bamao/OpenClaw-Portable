from __future__ import annotations


def format_runtime_error(exc: Exception) -> str:
    message = str(exc)
    if _is_missing_openclaw_runtime(message):
        return (
            "缺少 OpenClaw 运行时文件。请先运行 scripts/prepare-openclaw-runtime.ps1 "
            "重建 runtime/openclaw，或重新解压一份完整的便携包。"
        )
    if _is_openclaw_startup_timeout(exc, message):
        return (
            "OpenClaw 启动时间超过预期。首次启动可能需要稍等一会儿；"
            "如果重试后仍失败，请把系统临时目录 OpenClawPortable\\logs\\openclaw-runtime.err.log 发给售后排查。"
        )
    if "OpenClaw runtime exited before becoming healthy" in message:
        return (
            "OpenClaw 在启动阶段退出。请检查系统临时目录 OpenClawPortable\\logs\\openclaw-runtime.err.log，"
            "并将该日志发给售后排查。"
        )
    return message


def _is_missing_openclaw_runtime(message: str) -> bool:
    return (
        "OpenClaw runtime package not found" in message
        or "OpenClaw runtime entrypoint not found" in message
    )


def _is_openclaw_startup_timeout(exc: Exception, message: str) -> bool:
    return isinstance(exc, TimeoutError) and "OpenClaw runtime did not become healthy" in message
