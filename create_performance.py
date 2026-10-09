with open('templates/employees.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Modify content for performance.html
content = content.replace('Quản lý Nhân viên - Hệ Thống Quản Lý Nhân Sự', 'Đánh giá Hiệu suất - Hệ Thống Quản Lý Nhân Sự')
content = content.replace('Danh sách Nhân viên', 'Đánh giá Hiệu suất')
content = content.replace('Quản lý hồ sơ và thông tin nhân sự trong công ty.', 'Theo dõi và quản lý đánh giá hiệu quả công việc của nhân sự.')
content = content.replace('Tìm kiếm nhân viên...', 'Tìm kiếm theo tên hoặc kỳ đánh giá...')
content = content.replace('employees %}', 'reviews %}')
content = content.replace('emp.', 'rev.')

# Replace filters
filter_start = content.find('<div class="filters">')
filter_end = content.find('</form>')
filters_html = '''<div class="filters">
            <button type="submit" class="btn btn-secondary">Lọc</button>
            {% if request.user.role == 'admin' or request.user.role == 'hr' or request.user.role == 'manager' %}
            <button type="button" id="addNew" class="btn btn-primary" onclick="openCrudModal('/admin/performance/performancereview/add/?_popup=1', 'Thêm Đánh giá mới'); return false;">+ Thêm mới</button>
            {% endif %}
        </div>
    '''
content = content[:filter_start] + filters_html + content[filter_end:]

# Replace table
table_start = content.find('<table class="data-table">')
table_end = content.find('</table>') + 8
table_html = '''<table class="data-table">
            <thead>
                <tr>
                    <th>Kỳ đánh giá</th>
                    <th>Nhân viên</th>
                    <th>Người đánh giá</th>
                    <th>Điểm số</th>
                    <th>Nhận xét</th>
                    <th>Thao tác</th>
                </tr>
            </thead>
            <tbody>
                {% for rev in reviews %}
                <tr>
                    <td><strong>{{ rev.period }}</strong></td>
                    <td>
                        <strong>{{ rev.employee.user.get_full_name }}</strong><br>
                        <small style="color:var(--text-secondary)">{{ rev.employee.employee_id }}</small>
                    </td>
                    <td>{{ rev.reviewer.user.get_full_name|default:"-" }}</td>
                    <td>
                        <span class="badge {% if rev.score >= 8 %}badge-success{% elif rev.score >= 5 %}badge-warning{% else %}badge-danger{% endif %}">
                            {{ rev.score }}/10
                        </span>
                    </td>
                    <td style="max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{{ rev.feedback }}</td>
                    <td>
                        {% if request.user.role in 'admin,hr,manager' %}
                        <a href="#" onclick="openCrudModal('/admin/performance/performancereview/{{ rev.id }}/change/?_popup=1', 'Sửa Đánh giá'); return false;" class="btn-action">Sửa</a>
                        {% endif %}
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="6" style="text-align:center; padding: 30px; color: var(--text-secondary);">
                        Không tìm thấy đánh giá nào.
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>'''

content = content[:table_start] + table_html + content[table_end:]

with open('templates/performance.html', 'w', encoding='utf-8') as f:
    f.write(content)
