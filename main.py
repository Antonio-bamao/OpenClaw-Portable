from __future__ import annotations

from launcher.app import OpenClawLauncherApplication


def main() -> int:
    return OpenClawLauncherApplication().run()


if __name__ == "__main__":
    raise SystemExit(main())
