import os

# Enable High DPI scaling before creating QApplication
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "RoundPreferFloor")

from src.bootstrap.app_bootstrap import run_bootstrap


def main() -> int:
    return run_bootstrap()


if __name__ == "__main__":
    raise SystemExit(main())
