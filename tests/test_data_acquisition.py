import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from acquire_tinystories_subset import (  # noqa: E402
    EXPECTED_SHA256, EXPECTED_SIZE, UPSTREAM_FILENAME, UPSTREAM_REVISION, valid,
)


def test_locked_upstream_identity_and_local_subset():
    assert UPSTREAM_REVISION == "f54c09fd23315a6f9c86f9dc80f725de7d8f9c64"
    assert UPSTREAM_FILENAME == "TinyStoriesV2-GPT4-train.txt"
    assert EXPECTED_SIZE == 59_999_181
    assert EXPECTED_SHA256 == "a0240e31a0d572d0d727e7a0c2b49a766ee6cf8c059a57ccdaadf2cce3c66cca"
    assert valid(ROOT / "data" / "raw" / "base.txt")
