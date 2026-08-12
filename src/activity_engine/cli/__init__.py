"""Command-line interface for the Activity Engine."""

from .main import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
