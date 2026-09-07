"""tests/test_dev_gate.py — Step 3: default-deny debug gating.

st.secrets is monkeypatched (auto-undone) so the tests are hermetic —
no dependence on whether the developer's machine happens to carry a
secrets.toml. The un-mocked behavior (no secrets file -> False) is the
production posture on Cloud."""
from utils import dev_gate as dev_gate_module
from utils.dev_gate import dev_tools_enabled


class _FakeSecrets:
    def __init__(self, data):
        self._d = data

    def get(self, key, default=None):
        return self._d.get(key, default)


def test_dev_tools_disabled_when_secret_absent(monkeypatch):
    monkeypatch.setattr(dev_gate_module.st, "secrets", _FakeSecrets({}))
    assert dev_tools_enabled() is False


def test_dev_tools_enabled_when_secret_true(monkeypatch):
    monkeypatch.setattr(dev_gate_module.st, "secrets",
                        _FakeSecrets({"dev_tools": True}))
    assert dev_tools_enabled() is True