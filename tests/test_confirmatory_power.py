import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from simulate_confirmatory_power import design_rows  # noqa: E402


def test_power_design_uses_both_scales_and_requested_seed_count():
    bank_path = Path(__file__).resolve().parents[1] / "configs" / "confirmatory" / "canary_bank.json"
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    frame = design_rows(bank, 3)
    assert len(frame) == 3 * 4 * 2 * 40
    assert set(frame.scale) == {"14m", "48m"}
    assert set(frame.architecture) == {"baseline", "learned_pos", "mha", "layernorm"}
    assert set(frame.frequency) == {1, 10, 50, 100, 500}
    assert abs(frame.log10_frequency.mean()) < 1e-12
