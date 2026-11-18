"""M1 trace case (docs/trace_case.md): seeded_regression C-008@11, FM-08 misreport.

The Lab 8 grader PASSES this trial; the ledger is right (20.000) but the reply tells the
customer 35.000. These tests replay the trial with MockLLM and assert on reply vs ledger.
"""
import re

import pytest

pytestmark = pytest.mark.student
AMOUNT = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d+)\s*đ")


def replay(shape, claim, seed):
    pytest.importorskip("pydantic_evals")   # Lab 8's CI collects tests without Lab 9 deps
    from lab9.trace_case import investigate

    return investigate(shape, claim, seed)


def reply_amounts(trial):
    text = " ".join(e["payload"]["text"] for e in trial["events"] if e.get("kind") == "reply")
    return {int(a.replace(".", "")) for a in AMOUNT.findall(text)}


def test_lab9_trace_case_c008_regression_misreports_amount():
    case = replay("seeded_regression", "C-008", 11)
    t = case["trial"]
    assert t["lab8_pass"], "the Lab 8 grader alone does not see FM-08"
    assert t["snapshot"]["refund_vnd"] == case["label"]["refund_vnd"] == 20000
    assert reply_amounts(t) == {35000}, "first wrong step: reply states the proposal, not the ledger"


def test_lab9_trace_case_c008_fixed_reports_ledger_amount():
    t = replay("fixed", "C-008", 11)["trial"]
    assert reply_amounts(t) == {t["snapshot"]["refund_vnd"]} == {20000}
