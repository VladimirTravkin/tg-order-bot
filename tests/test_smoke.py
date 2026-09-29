"""Smoke test to verify the test infrastructure works.

Ensures the package is importable and exposes a valid version string.
"""

from tg_order_bot import __version__


def test_version_is_defined() -> None:
    """Ensure the package version is a non-empty string."""
    assert isinstance(__version__, str)
    assert __version__ != ""


def test_settings_are_importable() -> None:
    """Ensure the Settings class can be imported (config wiring works)."""
    from tg_order_bot.config import Settings

    assert Settings is not None
