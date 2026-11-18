# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi nhóm 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `<shape> <claim>@<seed>`, run ID trong report |
| Triệu chứng | Grader nào fail; reply nói gì so với ledger ghi gì |
| Bước sai đầu tiên | Số thứ tự event + kind + trích payload (≤1 dòng) |
| Vì sao là bước *đầu tiên* | Các bước trước đó đúng ra sao (dẫn số event) |
| Failure mode | Mã FM-xx trong `docs/failure_taxonomy.md` |
| Đối chứng | Cùng claim@seed trên shape `fixed`: bước đó khác thế nào |
| Regression test | Tên test + grader/assert nào bắt được; đã thấy fail trên variant lỗi và pass trên `fixed` chưa |
| Chưa chắc chắn | Điều trace không chứng minh được |

## Case của nhóm: `seeded_regression` C-008@11 (FM-08 misreport)

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-008 --seed 11
python -m lab9.trace_case --shape fixed --claim C-008 --seed 11
```

```
== seeded_regression C-008@11  lab8 grader: PASS (ok)
   1 handoff            {"claim_id": "C-008", "contract_version": "handoff.v1", ...}
   2 investigator       {"lookup_order": {"visible": true, "order": {"order_id": "O-808", "status": "delivered_late", ...}}}
   3 quote              {"amount_vnd": 35000, "reason": "entitled", "clause_ids": ["SHIP-LATE-03"], ...}
   4 refund_history     {"refund_count": 0, "refunded_vnd": 0}
   5 reply              {"text": "Dạ, LogiX đã hoàn 35.000đ cho đơn O-808."}
-- ledger vs label
  refund_vnd     ledger=20000    label=20000
  refund_count   ledger=1        label=1
  status         result=resolved label=resolved
```

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-008@11`, run ID `R-seeded_regression-C-008-s11`. Lặp lại trên cả 5 seed (11/22/33/44/55). |
| Triệu chứng | Grader Lab 8 (`pass_rate`) **PASS**, `refund_amount_correct` PASS (ledger 20.000 = nhãn). Nhưng reply nói với khách "đã hoàn **35.000đ**" trong khi ledger chỉ ghi **20.000**. Khách được hứa 15.000đ không có thật. |
| Bước sai đầu tiên | Event **5 `reply`**: `"Dạ, LogiX đã hoàn 35.000đ cho đơn O-808."` |
| Vì sao là bước *đầu tiên* | Event 2: DB đúng (O-808, `delivered_late`). Event 3: quote 35.000 theo SHIP-LATE-03 giống hệt `fixed`. Event 4: lịch sử hoàn = 0, không có gì để trừ. Host tự giới hạn khoản chi còn 20.000 (khớp nhãn `proposal_amount` 35.000 → `refund_vnd` 20.000). Đến event 5, agent báo số **mình đề xuất** chứ không báo số **host đã ghi**. |
| Failure mode | **FM-08** misreport (`docs/failure_taxonomy.md`) |
| Đối chứng | `fixed` C-008@11: event 1–3 giống hệt, không có event 4; event 4 `reply` = "Dạ, LogiX đã hoàn **20.000đ** cho đơn O-808." Reply khớp ledger. |
| Regression test | `src/tests/test_lab9_trace_case.py`. `test_lab9_trace_case_c008_regression_misreports_amount` xác nhận trên variant lỗi: lab8 PASS, ledger 20.000, reply {35.000}. `test_lab9_trace_case_c008_fixed_reports_ledger_amount` xác nhận `fixed` có reply = ledger = 20.000. Cả hai đã chạy và xanh. Item E-008 nằm trong eval set với `failure_modes: ["FM-08"]` và `provenance.from_trace = "seeded_regression:C-008@11"`. Từ M3, grader `ReplyAmountMatchesLedger` và metric `reply_amount_matches_ledger` (min 1.0, blocking) trong `metric_spec.yaml` chấm case này là FAIL. Trên `seeded_regression`, metric này = 0.7857 (C-007, C-008, C-014 fail); trên `fixed` = 1.0. |
| Chưa chắc chắn | Trace không ghi phản hồi của host (`issue_refund` → 20.000). Số 20.000 chỉ suy ra từ ledger snapshot, nên lý do host giới hạn (trần theo đơn? theo approval A-008?) không chứng minh được từ trace. Regex số tiền trong test chỉ hiểu định dạng "35.000đ"; nếu agent diễn đạt khác (ví dụ "35 nghìn") thì grader FM-08 ở M3 cần xử lý thêm. |

**Bài học:** grader dựa trên outcome (ledger, status) bỏ sót lỗi giao tiếp. Grader FM-08 phải đọc **cả** reply lẫn ledger.

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
