import os

with open('templates/employees.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Modify content for user_list.html
content = content.replace('Quản lý Nhân viên - Hệ Thống Quản Lý Nhân Sự', 'Quản lý Tài khoản - Hệ Thống Quản Lý Nhân Sự')
content = content.replace('Danh sách Nhân viên', 'Danh sách Tài khoản')
content = content.replace('Quản lý hồ sơ và thông tin nhân sự trong công ty.', 'Quản lý tài khoản đăng nhập và phân quyền hệ thống.')
content = content.replace('Tìm kiếm nhân viên...', 'Tìm kiếm tài khoản (Tên, Email)...')

# Replace filters
filter_start = content.find('<div class="filters">')
filter_end = content.find('</form>')
filters_html = '''<div class="filters">
            <select name="role" class="form-select">
                <option value="">Tất cả vai trò</option>
                <option value="admin" {% if request.GET.role == 'admin' %}selected{% endif %}>Administrator</option>
                <option value="hr" {% if request.GET.role == 'hr' %}selected{% endif %}>HR Manager</option>
                <option value="manager" {% if request.GET.role == 'manager' %}selected{% endif %}>Manager</option>
                <option value="employee" {% if request.GET.role == 'employee' %}selected{% endif %}>Employee</option>
            </select>
            <button type="submit" class="btn btn-secondary">Lọc</button>
            {% if request.user.role == 'admin' %}
            <button type="button" id="addNew" class="btn btn-primary" onclick="openCrudModal('/admin/accounts/user/add/?_popup=1', 'Thêm Tài khoản mới'); return false;">+ Thêm mới</button>
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
                    <th>Tên đăng nhập</th>
                    <th>Email</th>
                    <th>Họ Tên</th>
                    <th>Vai trò (Role)</th>
                    <th>Trạng thái</th>
                    <th>Thao tác</th>
                </tr>
            </thead>
            <tbody>
                {% for u in users %}
                <tr>
                    <td><strong>{{ u.username }}</strong></td>
                    <td>{{ u.email|default:"-" }}</td>
                    <td>{{ u.get_full_name|default:"-" }}</td>
                    <td>
                        <span class="badge {% if u.role == 'admin' %}badge-success{% else %}badge-warning{% endif %}">
                            {{ u.get_role_display }}
                        </span>
                    </td>
                    <td>
                        {% if u.is_active %}
                        <span class="badge badge-success">Hoạt động</span>
                        {% else %}
                        <span style="color: var(--text-secondary);">Đã khóa</span>
                        {% endif %}
                    </td>
                    <td>
                        <a href="#" onclick="openCrudModal('/admin/accounts/user/{{ u.id }}/change/?_popup=1', 'Chỉnh sửa tài khoản'); return false;" class="btn-action">Sửa</a>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="6" style="text-align:center; padding: 30px; color: var(--text-secondary);">
                        Không tìm thấy tài khoản nào.
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>'''

content = content[:table_start] + table_html + content[table_end:]

os.makedirs('templates/accounts', exist_ok=True)
with open('templates/accounts/user_list.html', 'w', encoding='utf-8') as f:
    f.write(content)
