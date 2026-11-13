import os

from app import config


def test_env_file_fills_missing_values_but_real_env_wins(tmp_path, monkeypatch):
    # make sure both names exist so monkeypatch restores them afterwards
    monkeypatch.setenv("ENVTEST_NEW", "x")
    monkeypatch.delenv("ENVTEST_NEW")
    monkeypatch.setenv("ENVTEST_KEEP", "from-real-env")

    f = tmp_path / ".env"
    f.write_text('# comment\n\nENVTEST_NEW="from-file"\nENVTEST_KEEP=from-file\nbad line\n')
    loaded = config.load_env_file(f)

    assert os.environ["ENVTEST_NEW"] == "from-file"
    assert os.environ["ENVTEST_KEEP"] == "from-real-env"
    assert loaded == 1


def test_missing_env_file_is_fine(tmp_path):
    assert config.load_env_file(tmp_path / "nope.env") == 0


def test_defaults_still_apply_without_env(monkeypatch):
    monkeypatch.delenv("ASK_TIMEOUT_SECONDS", raising=False)
    assert config.ask_timeout() == 20.0
