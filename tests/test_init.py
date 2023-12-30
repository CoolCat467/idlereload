from __future__ import annotations

import idlereload


def test_has_callables() -> None:
    assert hasattr(idlereload, "check_installed")
    assert callable(idlereload.check_installed)
    assert hasattr(idlereload, "idlereload")
    assert hasattr(idlereload.idlereload, "reload")
    assert callable(idlereload.idlereload.reload)
