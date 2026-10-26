import json

from bridge.audit import AuditLog


def test_audit_writes_jsonl_and_publishes(tmp_path):
    sent = []
    log = AuditLog(str(tmp_path / "logs" / "audit.jsonl"), publish=sent.append)
    log.record(topic="f/l/d/cmd/led_1", signal="led_1", requested=True, previous=False, result="written")
    log.record(topic="f/l/d/cmd/x", signal="x", requested="5", previous=None, result="rejected",
               reason="not writable")
    lines = (tmp_path / "logs" / "audit.jsonl").read_text().splitlines()
    assert [json.loads(l)["result"] for l in lines] == ["written", "rejected"]
    assert len(sent) == 2 and json.loads(sent[1])["reason"] == "not writable"
