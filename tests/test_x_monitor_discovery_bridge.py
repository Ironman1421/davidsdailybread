from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_evening_bake_uses_private_ephemeral_x_monitor_snapshot():
    workflow = (ROOT / ".github/workflows/ddb-bake.yml").read_text(encoding="utf-8")
    snapshot_step = workflow.split(
        "- name: Prepare X Monitor discovery snapshot", 1
    )[1].split("- name: Install Claude Code", 1)[0]
    bake_step = workflow.split("- name: Bake (research, write, render)", 1)[1].split(
        "- name: Guard the changed files", 1
    )[0]

    assert "steps.cfg.outputs.slot == 'evening'" in snapshot_step
    assert "steps.cfg.outputs.mode == 'daily'" in snapshot_step
    assert "secrets.X_MONITOR_SITES_BYPASS_TOKEN" in snapshot_step
    assert "OAI-Sites-Authorization: Bearer" in snapshot_step
    assert "/api/trends?windowEnd=" in snapshot_step
    assert "/api/discovery-export?hours=48&limit=12" in snapshot_step
    assert "$RUNNER_TEMP/x-monitor-discovery.json" in snapshot_step
    assert "X_BEARER_TOKEN" not in workflow

    assert "X_MONITOR_SITES_BYPASS_TOKEN" not in bake_step
    assert "X_MONITOR_DISCOVERY_PATH" in bake_step
    assert "discovery lead only" in bake_step
    assert "Never use an X post as the factual source or trend source" in bake_step


def test_bake_spec_keeps_x_monitor_discovery_only_and_non_blocking():
    bake = (ROOT / "BAKE.md").read_text(encoding="utf-8")

    assert "David's approved X Monitor is" in bake
    assert "connected for daily evening runs" in bake
    assert "An X post never satisfies" in bake
    assert "continue with the normal source ladder" in bake
    assert "Never fail or pad" in bake
