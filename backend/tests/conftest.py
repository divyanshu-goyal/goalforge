import os
import tempfile
from pathlib import Path


def pytest_configure(config):
    test_directory = Path(tempfile.mkdtemp(prefix="goalforge-tests-"))
    config.goalforge_test_directory = test_directory
    os.environ["DATABASE_URL"] = f"sqlite:///{test_directory / 'goalforge-test.db'}"


def pytest_unconfigure(config):
    test_directory = getattr(config, "goalforge_test_directory", None)
    if test_directory is not None:
        for path in test_directory.iterdir():
            path.unlink()
        test_directory.rmdir()
