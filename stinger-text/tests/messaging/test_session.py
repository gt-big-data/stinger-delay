import pytest

from app.messaging import session
from app.models import LatLng


class Clock:
    t = 1000.0

    def __call__(self) -> float:
        return self.t


@pytest.fixture
def clk(monkeypatch: pytest.MonkeyPatch) -> Clock:
    c = Clock()
    monkeypatch.setattr(session, "_now", c)
    session.reset_all()
    yield c
    session.reset_all()


def test_location_expires(clk: Clock) -> None:
    loc = LatLng(33.7772, -84.3956)
    session.set_location("u", loc)
    clk.t += 14 * 60 + 59
    assert session.get_location("u") == loc
    clk.t += 2
    assert session.get_location("u") is None
    assert session.get_location("other") is None


def test_pending_expiry_and_pop(clk: Clock) -> None:
    session.set_pending("u", "q")
    assert session.pop_pending("u") == "q"
    assert session.pop_pending("u") is None
    session.set_pending("u", "q2")
    clk.t += 10 * 60 + 1
    assert session.get_pending("u") is None


def test_mark_seen(clk: Clock) -> None:
    assert session.mark_seen("g") is True
    assert session.mark_seen("g") is False
    clk.t += 10 * 60 + 1
    assert session.mark_seen("g") is True


def test_cap(clk: Clock) -> None:
    for i in range(2001):
        session.mark_seen(f"g{i}")
    assert len(session._store) <= 2000
    assert session.mark_seen("g2000") is False
    assert session.mark_seen("g0") is True
