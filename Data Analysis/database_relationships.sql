-- ==========================================================
-- TỔNG HỢP CÁC RÀNG BUỘC KHÓA NGOẠI (FOREIGN KEYS) HỆ THỐNG EMS
-- ==========================================================

ALTER TABLE `accounts_user_groups`
  ADD CONSTRAINT `accounts_user_groups_group_id_bd11a704_fk_auth_group_id`
  FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `accounts_user_groups`
  ADD CONSTRAINT `accounts_user_groups_user_id_52b62117_fk_accounts_user_id`
  FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `accounts_user_user_permissions`
  ADD CONSTRAINT `accounts_user_user_p_permission_id_113bb443_fk_auth_perm`
  FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `accounts_user_user_permissions`
  ADD CONSTRAINT `accounts_user_user_p_user_id_e4f0a161_fk_accounts_`
  FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `attendance_attendance`
  ADD CONSTRAINT `attendance_attendanc_employee_id_63b4db5a_fk_employees`
  FOREIGN KEY (`employee_id`) REFERENCES `employees_employee` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `auth_group_permissions`
  ADD CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id`
  FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `auth_group_permissions`
  ADD CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm`
  FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `auth_permission`
  ADD CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co`
  FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `departments_department`
  ADD CONSTRAINT `departments_department_manager_id_54b667cc_fk_accounts_user_id`
  FOREIGN KEY (`manager_id`) REFERENCES `accounts_user` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `departments_department`
  ADD CONSTRAINT `departments_departme_parent_id_cc8b848e_fk_departmen`
  FOREIGN KEY (`parent_id`) REFERENCES `departments_department` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `departments_position`
  ADD CONSTRAINT `departments_position_department_id_8b23d744_fk_departmen`
  FOREIGN KEY (`department_id`) REFERENCES `departments_department` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `django_admin_log`
  ADD CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co`
  FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `django_admin_log`
  ADD CONSTRAINT `django_admin_log_user_id_c564eba6_fk_accounts_user_id`
  FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `employees_employee`
  ADD CONSTRAINT `employees_employee_department_id_410c23c8_fk_departmen`
  FOREIGN KEY (`department_id`) REFERENCES `departments_department` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `employees_employee`
  ADD CONSTRAINT `employees_employee_manager_id_2f52c91e_fk_employees_employee_id`
  FOREIGN KEY (`manager_id`) REFERENCES `employees_employee` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `employees_employee`
  ADD CONSTRAINT `employees_employee_position_id_19059adb_fk_departmen`
  FOREIGN KEY (`position_id`) REFERENCES `departments_position` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `employees_employee`
  ADD CONSTRAINT `employees_employee_user_id_27bed289_fk_accounts_user_id`
  FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `leave_leaverequest`
  ADD CONSTRAINT `leave_leaverequest_employee_id_bf5f2be5_fk_employees_employee_id`
  FOREIGN KEY (`employee_id`) REFERENCES `employees_employee` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `notifications_notification`
  ADD CONSTRAINT `notifications_notification_user_id_b5e8c0ff_fk_accounts_user_id`
  FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `payroll_payroll`
  ADD CONSTRAINT `payroll_payroll_employee_id_cd24ccf6_fk_employees_employee_id`
  FOREIGN KEY (`employee_id`) REFERENCES `employees_employee` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `performance_performancereview`
  ADD CONSTRAINT `performance_performa_employee_id_3c08abd5_fk_employees`
  FOREIGN KEY (`employee_id`) REFERENCES `employees_employee` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `performance_performancereview`
  ADD CONSTRAINT `performance_performa_reviewer_id_fa353eac_fk_employees`
  FOREIGN KEY (`reviewer_id`) REFERENCES `employees_employee` (`id`)
  ON DELETE CASCADE ON UPDATE CASCADE;

