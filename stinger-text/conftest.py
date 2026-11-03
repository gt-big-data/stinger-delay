import pytest

@pytest.fixture(autouse=True)
def _no_trigger_word(monkeypatch):
    # The live config may set TRIGGER_WORD for the demo; tests opt in explicitly.
    monkeypatch.setenv("TRIGGER_WORD", "")
