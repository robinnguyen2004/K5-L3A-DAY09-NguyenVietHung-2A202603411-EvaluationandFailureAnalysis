# Judge audit

Chạy (thư mục `src/`): `python -m lab9.judge --csv <file> --audit 5`. Backend replay: phán quyết judge lưu sẵn trong CSV, nhãn người ở cột `human`. Lớp positive = `FAIL`.

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | **Đạt** (exit 0) | **dùng**: metric non-blocking, có người kiểm mẫu |
| helpful | 100 | 0.375 | 1.000 | 0.300 | **Không đạt**: κ và R dưới sàn (exit 1) | **loại**: không dùng làm gate |

| Tiêu chí | tp | fp | fn | tn | Tỉ lệ FAIL quan sát (judge) | Sau Rogan-Gladen | Bất đồng |
|---|---|---|---|---|---|---|---|
| tone_ok | 24 | 4 | 6 | 66 | 0.28 | 0.30 | 10 (6 fn, 4 fp) |
| helpful | 9 | 0 | 21 | 70 | 0.09 | 0.30 | 21 (21 fn, 0 fp) |

Người chấm cho tỉ lệ FAIL thật là 30/100 ở cả hai file. Judge tone ước lượng 0.28, gần đúng. Judge helpful ước lượng 0.09, tức **thấp hơn thực tế hơn 3 lần**. Rogan-Gladen kéo được con số tổng về 0.30, nhưng chỉ hiệu chỉnh được *tỉ lệ*, không chỉ ra được *trial nào* hỏng. Gate cần biết trial nào hỏng, nên hiệu chỉnh không cứu được judge helpful.

## ≥5 case audit thủ công

Đã đọc cả 31 bất đồng (10 tone + 21 helpful). Dưới đây là 9 case đại diện cho mọi kiểu lỗi.

| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú: sửa rubric thế nào |
|---|---|---|---|---|---|
| 1 | tone H-008 "Em đã hoàn tiền cho anh rồi nha, anh check giúp em." | PASS | FAIL | **Người** | Judge nhầm "suồng sã" với "thân thiện" (cùng kiểu: H-017 xưng "bạn"). Rubric thêm: *xưng hô phải là "LogiX" / "anh/chị"; xưng "em", "bạn", hoặc dùng "nha", "nhé" ⇒ FAIL*, kèm 2 ví dụ FAIL. |
| 2 | tone H-029 "Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm." | PASS | FAIL | **Người** | Judge chỉ nhìn từ lịch sự bề mặt ("Dạ, vui lòng"). Rubric thêm: *câu mang giọng ra lệnh hoặc chặn khách ("không cần nhắn thêm", "liên hệ sau") ⇒ FAIL dù có "Dạ"*. |
| 3 | tone H-063 "Dạ, LogiX đã hoàn 20.000đ và sẽ hoàn thêm cho anh/chị ạ." | PASS | FAIL | **Người**, nhưng đây không phải lỗi giọng điệu | Lời hứa "sẽ hoàn thêm" là lỗi **nội dung** (cam kết ngoài kết quả hệ thống), không phải tone. Bỏ khỏi rubric tone, chuyển sang grader code: reply không được nhắc khoản tiền ngoài ledger (FM-08). |
| 4 | tone H-042 "Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ." | FAIL | PASS | **Người** | Judge phạt vì "thiếu xin lỗi". Rubric thêm: *xin lỗi là không bắt buộc; reply ngắn, lễ phép, đủ thông tin ⇒ PASS*. Cách sửa này cũng giảm thiên lệch chuộng câu dài (xem case 8). |
| 5 | tone H-051 "Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ." | FAIL | PASS | **Người** | Style guide CS LogiX cho phép từ "refund". Rubric thêm danh sách từ tiếng Anh được phép (refund, ship, voucher). Chỉ FAIL khi cả câu không phải tiếng Việt hoặc mất dấu (như H-094). |
| 6 | tone H-081 "Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ." | FAIL | PASS | **Judge** (nhãn người sai) | Người chấm đọc nhầm ticket (theo note). Hành động: **sửa nhãn người** trong vòng gán nhãn sau, không sửa rubric. Nếu sửa nhãn này thì fp còn 3, P = 24/27 ≈ 0.889. Hệ quả: tone được đánh giá thấp hơn thực tế một chút, và nhãn người cũng cần được kiểm (2 người chấm, tính κ giữa họ). |
| 7 | helpful HL-015 "Dạ, LogiX đã hoàn 55.000đ cho đơn O-112 ạ." (ledger ghi 40.000đ) | PASS | FAIL | **Người** | Judge **không được xem ledger**, nên không thể biết 55.000 là sai. 18/21 lần bỏ sót của judge helpful thuộc loại này. Đây không phải lỗi sửa bằng rubric được: *số tiền đúng hay sai phải chấm bằng code* (so reply với `snapshot.refund_vnd`, metric FM-08 ở M3). Rubric helpful bỏ hẳn tiêu chí "số tiền chính xác". |
| 8 | helpful HL-016 3 câu xin lỗi + "đã hoàn 55.000đ" (ledger 35.000đ) | PASS | FAIL | **Người** | Thiên lệch chuộng câu dài và nhiều lời xin lỗi: reply dài, nhiều lời xin lỗi lặp lại (HL-028, 035, 041, 053, 070…) đều được judge cho PASS dù sai số tiền. Rubric thêm: *lặp lại cùng một lời xin lỗi ≥ 2 lần ⇒ FAIL; độ dài không phải là dấu hiệu hữu ích*. Phần sai số tiền vẫn để code chấm. |
| 9 | helpful HL-047 "Ok bạn, đơn O-515 xử lý rồi nhé." | PASS | FAIL | **Người** | Không có số tiền, không có thời hạn, không có bước tiếp theo (tương tự HL-091, HL-097). Rubric thêm: *reply hữu ích phải có ≥1 thông tin hành động được: số tiền đã hoàn, thời gian tiền về, hoặc yêu cầu thông tin cụ thể; "đã xử lý" chung chung ⇒ FAIL*. |

Phân loại 21 lần bỏ sót của judge helpful: **18 case** sai số tiền so với ledger (không có case nào mà judge có cách nhìn thấy lỗi), trong đó 13 case kèm xin lỗi dài lặp lại; **3 case** reply chung chung "Ok bạn, … xử lý rồi nhé". Judge helpful không có fp nào: nó gần như không bao giờ nói FAIL.

## Kết luận

- **Loại judge helpful khỏi gate.** Ma trận nhầm lẫn tp 9 / fn 21 cho thấy judge bỏ sót 70% reply vô ích (R = 0.30 < 0.7), và κ = 0.375 < 0.6. P = 1.0 trông đẹp nhưng chỉ vì judge rất ít khi nói FAIL (9/100). Một judge "luôn PASS" cũng có thể có precision cao trên phần nhỏ nó gắn FAIL. Nếu dùng judge này làm gate, một regression kiểu FM-08 (nói sai số tiền) sẽ lọt gần như 100%, vì judge không có ledger để đối chiếu. Đây đúng là lỗi mà trace case C-008@11 cho thấy.
- **Judge tone dùng được nhưng sát sàn** (R = 0.80 chỉ trên sàn 0.7 một khoảng nhỏ, κ = 0.757). Dùng làm metric **non-blocking**, kèm người kiểm mẫu định kỳ, và áp dụng các sửa rubric ở case 1, 2, 4, 5 trước lần calibrate sau. Hai lần bỏ sót (H-008, H-017) cùng một kiểu xưng hô, nên sửa rubric có thể cải thiện recall rõ rệt.
- **Phân công grader:**
  - Tiền, approval và số tiền trong reply luôn chấm bằng code (`refund_amount_correct`, `approval_bypass`, metric FM-08).
  - Judge chỉ dùng cho chất lượng ngôn ngữ, nơi không có đáp án tất định.
- **Rủi ro còn lại:**
  - Judge chỉ được kiểm trên 100 dòng replay công khai mỗi tiêu chí. Cần một tập nhãn người mới, tập held-out thật, để tránh việc sửa rubric quá khớp với chính 100 dòng này.
  - Nhãn người cũng có lỗi (H-081). Nên có 2 người chấm độc lập và báo cáo κ giữa hai người làm trần cho judge.
  - Với replay, κ không đổi giữa các lần chạy. Với LLM judge thật, phán quyết có thể dao động, nên cần calibrate trên nhiều lần chạy.
