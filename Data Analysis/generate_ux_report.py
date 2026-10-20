import pandas as pd
import xlsxwriter

def create_report():
    file_name = 'UX_UI_Error_Report.xlsx'
    
    # Dữ liệu giả định
    summary_data = {
        'Hạng mục': ['Tổng số lỗi HTTP', 'Lỗi 404 (Not Found)', 'Lỗi 500 (Server Error)', 'Lỗi 403 (Forbidden)', 'Đánh giá mức độ nghiêm trọng'],
        'Giá trị': ['1,245', '809 (65%)', '249 (20%)', '187 (15%)', 'Trung bình - Cao']
    }
    df_summary = pd.DataFrame(summary_data)
    
    error_data = {
        'URL Lỗi': ['/payroll/export-pdf/', '/employees/old-profile.php', '/admin/departments/delete/', '/api/employees/?limit=1000', '/leave/request-form/'],
        'Mã Lỗi': [500, 404, 403, 500, 404],
        'Lượt gặp': [185, 420, 150, 64, 215],
        'Mức Ưu tiên': ['Cao (Khẩn cấp)', 'Thấp', 'Trung bình', 'Cao', 'Cao'],
        'Nguyên nhân (Root Cause)': ['Lỗi tràn bộ nhớ (Timeout)', 'Bookmark từ hệ thống cũ', 'Lỗi phân quyền UI', 'N+1 Query quá tải API', 'Sai URL trên giao diện Mobile'],
        'Giải pháp UX/UI & Kỹ thuật': ['Chuyển sang xử lý nền (Async) + Thêm Toast Notification', 'Thiết kế trang 404 tùy chỉnh + Redirect 301', 'Ẩn nút Xóa khỏi giao diện người dùng không có quyền', 'Phân trang API (Pagination)', 'Sửa lại liên kết trên Mobile UI']
    }
    df_errors = pd.DataFrame(error_data)
    
    writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
    
    # Sheet 1: Executive Summary
    df_summary.to_excel(writer, sheet_name='Tóm tắt chung', index=False, startrow=2)
    workbook = writer.book
    worksheet1 = writer.sheets['Tóm tắt chung']
    
    # Định dạng
    header_format = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white', 'border': 1})
    title_format = workbook.add_format({'bold': True, 'font_size': 14})
    
    worksheet1.write('A1', 'BÁO CÁO PHÂN TÍCH UX/UI VÀ LỖI HỆ THỐNG', title_format)
    for col_num, value in enumerate(df_summary.columns.values):
        worksheet1.write(2, col_num, value, header_format)
        
    worksheet1.set_column('A:A', 30)
    worksheet1.set_column('B:B', 20)
    
    # Sheet 2: Chi tiết Lỗi và UX/UI
    df_errors.to_excel(writer, sheet_name='Chi tiết Lỗi & Giải pháp UX', index=False, startrow=2)
    worksheet2 = writer.sheets['Chi tiết Lỗi & Giải pháp UX']
    
    worksheet2.write('A1', 'MA TRẬN ƯU TIÊN VÀ HƯỚNG DẪN CẢI THIỆN UX/UI', title_format)
    
    for col_num, value in enumerate(df_errors.columns.values):
        worksheet2.write(2, col_num, value, header_format)
        
    worksheet2.set_column('A:A', 30)
    worksheet2.set_column('B:B', 10)
    worksheet2.set_column('C:C', 10)
    worksheet2.set_column('D:D', 15)
    worksheet2.set_column('E:E', 30)
    worksheet2.set_column('F:F', 50)
    
    # Highlight ưu tiên
    format_high = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
    format_med = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
    
    worksheet2.conditional_format('D4:D8', {'type': 'cell', 'criteria': '==', 'value': '"Cao (Khẩn cấp)"', 'format': format_high})
    worksheet2.conditional_format('D4:D8', {'type': 'cell', 'criteria': '==', 'value': '"Cao"', 'format': format_high})
    worksheet2.conditional_format('D4:D8', {'type': 'cell', 'criteria': '==', 'value': '"Trung bình"', 'format': format_med})

    writer.close()
    print(f"Report generated successfully: {file_name}")

if __name__ == '__main__':
    create_report()
