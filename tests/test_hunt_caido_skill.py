"""hunt-caido must carry concrete driver and safety contracts."""
import pathlib

SKILL = (
    pathlib.Path(__file__).resolve().parents[1]
    / "skills" / "caido" / "hunt-caido" / "SKILL.md"
).read_text()


def test_drives_core_caido_capabilities_by_name():
    for operation in ("search", "edit", "create-automate-session", "create-finding", "export-curl"):
        assert operation in SKILL, "hunt-caido missing driver ref for %s" % operation


def test_wires_transport_and_scope_sync():
    assert "caido-transport.sh" in SKILL
    assert "caido-scope-sync.py" in SKILL


def test_carries_passive_first_candidate_sweep():
    assert "Passive-first candidate sweep" in SKILL
    assert "idor-sweep.py" in SKILL


def test_uses_interactsh_for_oob_proof():
    assert "interactsh" in SKILL.lower()
    assert "oob.md" in SKILL
