"""M3 team graders: FM-08 ReplyAmountMatchesLedger and FM-05 ProposalAmountCorrect (hand-built Trials)."""
import pytest

pytestmark = pytest.mark.student
LABEL = {"refund_vnd": 20000, "proposal_amount": 35000, "approval_ok": True}


@pytest.fixture(scope="module")
def graders():
    pytest.importorskip("pydantic_evals")   # Lab 8's CI collects tests without Lab 9 deps
    from lab9 import graders

    return graders


def ctx(trial, label=LABEL):
    from pydantic_evals.evaluators import EvaluatorContext

    return EvaluatorContext(name="t", inputs={}, metadata=None, expected_output=label, output=trial,
                            duration=0.0, _span_tree=None, attributes={}, metrics={})


def trial(reply=None, refund_vnd=20000, proposal=35000):
    events = [] if reply is None else [{"kind": "reply", "payload": {"text": reply}}]
    return {"snapshot": {"refund_vnd": refund_vnd, "refund_count": int(refund_vnd > 0)}, "unexpected_rows": 0,
            "blob": "", "events": events, "result": {"proposal_amount": proposal},
            "lab8_pass": True, "lab8_reason": None}


@pytest.mark.parametrize("reply", [
    "Dạ, LogiX đã hoàn 20.000đ cho đơn O-808.",
    "LogiX đã hoàn phí 20.000đ cho đơn O-808 của anh/chị ạ.",   # paraphrase is not a bug
    "Dạ, LogiX đã hoàn 20,000 VND, tiền về trong 3–5 ngày ạ.",   # other format; "3–5 ngày" is not money
    "Dạ, yêu cầu đã được chuyển cho chuyên viên xử lý.",          # no amount stated
])
def test_reply_matching_ledger_passes(graders, reply):
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx(trial(reply))).value is True


def test_c008_misreport_fails(graders):
    res = graders.ReplyAmountMatchesLedger().evaluate(ctx(trial("Dạ, LogiX đã hoàn 35.000đ cho đơn O-808.")))
    assert res.value is False and "35000" in res.reason


def test_claimed_refund_with_empty_ledger_fails(graders):   # seeded_regression C-007
    t = trial("Dạ, LogiX đã hoàn 35.000đ cho đơn O-909.", refund_vnd=0)
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx(t)).value is False


def test_denial_mentioning_amount_passes(graders):
    t = trial("Dạ, khoản 35.000đ chưa đủ điều kiện hoàn theo chính sách hiện hành.", refund_vnd=0)
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx(t)).value is True


def test_no_reply_event_passes(graders):   # Lab 8 swarm_reference writes no reply event
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx(trial(None))).value is True


def test_proposal_amount(graders):
    g = graders.ProposalAmountCorrect()
    assert g.evaluate(ctx(trial(proposal=35000))).value is True
    assert g.evaluate(ctx(trial(proposal=0))).value is False      # C-013 pre_deducted to 0
    assert g.evaluate(ctx(trial(proposal=None))).value is False   # crashed run: no proposal


def test_m3_metrics_registered_and_in_spec(graders):
    from pathlib import Path

    import yaml

    spec = yaml.safe_load(Path("config/metric_spec.yaml").read_text(encoding="utf-8"))
    by_id = {m["id"]: m for m in spec["metrics"]}
    assert by_id["reply_amount_matches_ledger"]["blocking"] is True
    assert {"reply_amount_matches_ledger", "proposal_amount_correct"} <= graders.GRADERS.keys()
