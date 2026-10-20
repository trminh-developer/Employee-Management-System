---
name: persistent-project-memory
description: Hướng dẫn AI duy trì trí nhớ dự án, tối ưu ngữ cảnh, theo dõi trạng thái task và phục hồi kiến thức giữa các phiên làm việc mà không cần rà soát lại toàn bộ repository.
---

# 🧠 AI Persistent Project Memory Skill

## 1. MỤC ĐÍCH CỐT LÕI
Skill này cung cấp cơ chế để AI ghi nhớ dự án lâu dài, đọc đúng ngữ cảnh cần thiết và duy trì sự nhất quán giữa các phiên làm việc (sessions).
**Nguyên tắc cốt lõi: Đọc bộ nhớ trước → Xác định phạm vi → Kiểm tra mục tiêu → Thực thi → Kiểm thử → Cập nhật bộ nhớ.**

## 2. VÒNG ĐỜI MỘT NHIỆM VỤ (TASK LIFECYCLE)
Mỗi khi bắt đầu nhận một nhiệm vụ mới, AI **BẮT BUỘC** phải tuân theo 6 Phase sau:

### Phase 1: Recall (Khôi phục trí nhớ)
- Tìm và đọc các file trong thư mục `.ai-memory/` (đặc biệt là `PROJECT_MEMORY.md` và `TASK_STATE.md`).
- KHÔNG giả định ngữ cảnh cũ vẫn còn nguyên vẹn.

### Phase 2: Scope (Khoanh vùng)
- Dựa vào yêu cầu và bộ nhớ, xác định chính xác danh sách file/module bị ảnh hưởng.
- KHÔNG rà soát toàn bộ source code (VD: sửa UI thì chỉ đọc view/template, không đọc cấu trúc db nếu không liên quan).

### Phase 3: Verify (Xác minh)
- Dùng công cụ đọc/tìm kiếm để kiểm tra code thực tế tại các vùng đã Scope.
- Đối chiếu code thực tế với bộ nhớ. Nếu mâu thuẫn, **Sự thật nằm ở source code hiện tại**. Cập nhật lại bộ nhớ ngay.

### Phase 4: Execute (Thực thi)
- Chỉnh sửa code trong phạm vi đã xác định.
- Tuyệt đối không thay đổi (refactor) các phần không liên quan.

### Phase 5: Validate (Kiểm chứng)
- Viết test, chạy lệnh kiểm tra lỗi, hoặc review lại logic vừa sửa. Báo cáo trung thực kết quả.

### Phase 6: Consolidate (Lưu bộ nhớ)
- Cập nhật lại trạng thái vào `TASK_STATE.md` và `CHANGELOG.md`.
- Nếu có cấu trúc mới, cập nhật `ARCHITECTURE.md` và `PROJECT_MEMORY.md`.

## 3. CƠ CHẾ BỘ NHỚ
Dự án được lưu trữ ngữ cảnh trong các file sau tại `.ai-memory/`:
- `PROJECT_MEMORY.md`: Cấu trúc tổng quan, stack công nghệ, quy tắc code.
- `ARCHITECTURE.md`: Luồng dữ liệu, database schema, thiết kế hệ thống.
- `TASK_STATE.md`: Task đang làm, task tồn đọng, blocker.
- `CHANGELOG.md`: Lịch sử các thay đổi lớn.

## 4. TỐI ƯU HÓA TOKEN
- Chỉ load nội dung từ `.ai-memory/` khi bắt đầu phiên mới.
- Chỉ đọc (`cat` / `view_file`) những file trực tiếp liên quan đến yêu cầu.
- Nếu file quá lớn, dùng grep/search để lấy đoạn code cần thiết.
- Cập nhật bộ nhớ ngắn gọn, súc tích, dùng bullet points.

## 5. AN TOÀN BẢO MẬT
- KHÔNG ĐƯỢC ghi API keys, mật khẩu, JWT secrets vào file bộ nhớ.
- KHÔNG chạy git commit/push/reset khi chưa được người dùng cho phép rõ ràng.
