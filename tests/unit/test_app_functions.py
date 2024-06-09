"""Contains all application utility functions."""

from pytest import MonkeyPatch

from shop_db2 import get_app_name, get_app_version


def test_get_app_name() -> None:
    assert "shop-db2" == get_app_name()


def test_get_app_version(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("shop_db2.__version__", "42.0.0")
    assert "42.0.0" == get_app_version()
