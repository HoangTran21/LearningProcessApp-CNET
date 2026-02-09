from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLineEdit, QLabel,
                             QHeaderView, QAbstractItemView, QMessageBox, 
                             QFormLayout, QGroupBox, QDateEdit, QTextEdit, QComboBox,
                             QCheckBox, QSpinBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from collections import defaultdict


class StudentProfileDialog(QDialog):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Quản lý hồ sơ học sinh")
        self.resize(1100, 700)
        
        self.setStyleSheet("""
            QDialog { background-color: #f8f9fa; }
            QLabel#Title { font-size: 18px; font-weight: bold; color: #2c3e50; }
            QTableWidget { 
                border: 1px solid #dee2e6; 
                gridline-color: #eee; 
                background-color: white;
            }
            QHeaderView::section { 
                background-color: #343a40; 
                color: white;
                font-weight: bold; 
                border: 1px solid #454d55; 
                padding: 5px;
            }
            QPushButton {
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
                min-width: 100px;
            }
            QLineEdit, QDateEdit, QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
            }
        """)
        
        self.setup_ui()
        self.load_students()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tiêu đề
        title = QLabel("📋 HỒ SƠ HỌC SINH")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Thanh tìm kiếm
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Tìm kiếm:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Nhập ID hoặc tên học sinh...")
        self.search_box.textChanged.connect(self.search_students)
        search_layout.addWidget(self.search_box)
        
        self.btn_import = QPushButton("📥 Import từ tiến độ học tập")
        self.btn_import.setStyleSheet("background-color: #20c997; color: white; font-weight: bold;")
        self.btn_import.setFixedHeight(35)
        self.btn_import.clicked.connect(self.import_from_progress)
        search_layout.addWidget(self.btn_import)
        
        layout.addLayout(search_layout)
        
        # Bảng danh sách học sinh
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID học sinh", "Họ tên", "Điện thoại", "Tên phụ huynh", 
            "Ngày sinh", "Địa chỉ", "Lớp", "Ngày đăng ký", "Ghi chú"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)
        
        # Các nút chức năng
        btn_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("➕ Thêm học sinh")
        self.btn_add.setStyleSheet("background-color: #28a745; color: white;")
        self.btn_add.clicked.connect(self.add_student)
        
        self.btn_edit = QPushButton("✏️ Sửa thông tin")
        self.btn_edit.setStyleSheet("background-color: #ffc107; color: #222;")
        self.btn_edit.clicked.connect(self.edit_student)
        
        self.btn_delete = QPushButton("🗑️ Xóa học sinh")
        self.btn_delete.setStyleSheet("background-color: #dc3545; color: white;")
        self.btn_delete.clicked.connect(self.delete_student)
        
        self.btn_view_stats = QPushButton("📊 Xem số buổi học")
        self.btn_view_stats.setStyleSheet("background-color: #17a2b8; color: white;")
        self.btn_view_stats.clicked.connect(self.view_student_stats)
        
        btn_close = QPushButton("Đóng")
        btn_close.setStyleSheet("background-color: #6c757d; color: white;")
        btn_close.clicked.connect(self.close)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_view_stats)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
    
    def load_students(self):
        """Tải danh sách học sinh vào bảng"""
        self.table.setRowCount(0)
        students = self.db.get_all_students()
        
        for row_data in students:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value) if value else "")
                self.table.setItem(row, col, item)
    
    def search_students(self):
        """Tìm kiếm học sinh"""
        keyword = self.search_box.text()
        self.table.setRowCount(0)
        students = self.db.search_students(keyword)
        
        for row_data in students:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value) if value else "")
                self.table.setItem(row, col, item)
    
    def add_student(self):
        """Thêm học sinh mới"""
        dialog = StudentFormDialog(self, self.db)
        if dialog.exec():
            self.load_students()
    
    def edit_student(self):
        """Sửa thông tin học sinh"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn học sinh cần sửa!")
            return
        
        student_id = self.table.item(current_row, 0).text()
        student_data = self.db.get_student_by_id(student_id)
        
        dialog = StudentFormDialog(self, self.db, student_data)
        if dialog.exec():
            self.load_students()
    
    def delete_student(self):
        """Xóa học sinh"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn học sinh cần xóa!")
            return
        
        student_id = self.table.item(current_row, 0).text()
        student_name = self.table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa học sinh <b>{student_name}</b> (ID: {student_id})?<br><br>"
            "Lưu ý: Dữ liệu tiến độ học tập của học sinh này sẽ KHÔNG bị xóa.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_student(student_id)
                self.load_students()
                QMessageBox.information(self, "Thành công", "Đã xóa học sinh!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa: {e}")
    
    def view_student_stats(self):
        """Xem thống kê số buổi học của học sinh"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn học sinh cần xem thống kê!")
            return
        
        student_id = self.table.item(current_row, 0).text()
        student_name = self.table.item(current_row, 1).text()
        
        stats = self.db.get_student_attendance_stats(student_id=student_id, name=student_name)
        
        if stats:
            msg = f"""
            <h3>📊 Thống kê buổi học</h3>
            <p><b>ID học sinh:</b> {stats['student_id']}</p>
            <p><b>Họ tên:</b> {stats['name']}</p>
            <hr>
            <p><b>✅ Số buổi đi học:</b> <span style='color: green; font-size: 16px;'>{stats['attended']}</span></p>
            <p><b>❌ Số buổi nghỉ:</b> <span style='color: red; font-size: 16px;'>{stats['absent']}</span></p>
            <p><b>📌 Tổng số buổi:</b> <span style='font-size: 16px;'>{stats['total']}</span></p>
            """
            QMessageBox.information(self, "Thống kê học sinh", msg)
        else:
            QMessageBox.warning(self, "Thông báo", "Không tìm thấy dữ liệu học tập của học sinh này!")
    
    def import_from_progress(self):
        """Import học sinh từ bảng tiến độ học tập"""
        students_to_import = self.db.get_students_without_profile()
        
        if not students_to_import:
            QMessageBox.information(self, "Thông báo", "Tất cả học sinh đã có hồ sơ hoặc không có dữ liệu tiến độ!")
            return
        
        # Phân tích số buổi/tuần cho mỗi học sinh
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT DISTINCT name, class_name FROM progress')
        all_records = cursor.fetchall()
        
        student_sessions = defaultdict(set)
        for name, class_name in all_records:
            student_sessions[name].add(class_name)
        
        # Loại bỏ duplicates dựa trên name (vì get_students_without_profile chỉ trả 1 dòng/học sinh)
        seen_names = set()
        students_with_sessions = []
        
        for name, class_name, attendance_count in students_to_import:
            if name not in seen_names:
                num_sessions = len(student_sessions.get(name, set()))
                students_with_sessions.append((name, class_name, attendance_count, num_sessions))
                seen_names.add(name)
        
        dialog = StudentImportDialog(self, self.db, students_with_sessions)
        if dialog.exec():
            self.load_students()


class StudentFormDialog(QDialog):
    """Dialog form để thêm/sửa thông tin học sinh"""
    def __init__(self, parent, db, data=None):
        super().__init__(parent)
        self.db = db
        self.data = data
        self.is_edit_mode = data is not None
        
        self.setWindowTitle("Sửa thông tin học sinh" if self.is_edit_mode else "Thêm học sinh mới")
        self.setFixedWidth(550)
        
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QGroupBox { 
                font-weight: bold;
                border: 2px solid #007bff;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #007bff;
            }
            QLineEdit, QDateEdit, QTextEdit, QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            QPushButton {
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        
        self.setup_ui()
        
        if self.is_edit_mode:
            self.fill_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_group = QGroupBox("Thông tin học sinh")
        form_layout = QFormLayout(form_group)
        form_layout.setContentsMargins(15, 25, 15, 15)
        form_layout.setSpacing(12)
        
        # ID học sinh
        self.student_id_input = QLineEdit()
        self.student_id_input.setPlaceholderText("VD: HS001, HS002...")
        if self.is_edit_mode:
            self.student_id_input.setEnabled(False)  # Không cho sửa ID
        
        # Họ tên
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nhập họ và tên đầy đủ")
        
        # Điện thoại
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Số điện thoại liên hệ")
        
        # Tên phụ huynh
        self.parent_name_input = QLineEdit()
        self.parent_name_input.setPlaceholderText("Họ tên phụ huynh")
        
        # Ngày sinh
        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDisplayFormat("yyyy-MM-dd")
        self.dob_input.setDate(QDate.currentDate().addYears(-10))
        
        # Địa chỉ
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Địa chỉ nơi ở")
        
        # Lớp học
        self.class_input = QComboBox()
        self.class_input.addItems(["Sáng T7", "Chiều T7", "Sáng CN", "Chiều CN"])
        
        # Ngày đăng ký
        self.reg_date_input = QDateEdit()
        self.reg_date_input.setCalendarPopup(True)
        self.reg_date_input.setDisplayFormat("yyyy-MM-dd")
        self.reg_date_input.setDate(QDate.currentDate())
        
        # Ghi chú
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Ghi chú thêm về học sinh...")
        self.notes_input.setMaximumHeight(80)
        
        form_layout.addRow("ID học sinh:", self.student_id_input)
        form_layout.addRow("Họ và tên:", self.name_input)
        form_layout.addRow("Điện thoại:", self.phone_input)
        form_layout.addRow("Tên phụ huynh:", self.parent_name_input)
        form_layout.addRow("Ngày sinh:", self.dob_input)
        form_layout.addRow("Địa chỉ:", self.address_input)
        form_layout.addRow("Lớp học:", self.class_input)
        form_layout.addRow("Ngày đăng ký:", self.reg_date_input)
        form_layout.addRow("Ghi chú:", self.notes_input)
        
        layout.addWidget(form_group)
        
        # Nút lưu
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 LƯU THÔNG TIN")
        self.btn_save.setStyleSheet("background-color: #007bff; color: white; font-size: 14px;")
        self.btn_save.setFixedHeight(45)
        self.btn_save.clicked.connect(self.save_student)
        
        btn_cancel = QPushButton("Hủy")
        btn_cancel.setStyleSheet("background-color: #6c757d; color: white;")
        btn_cancel.setFixedHeight(45)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def fill_data(self):
        """Điền dữ liệu khi ở chế độ sửa"""
        if self.data:
            self.student_id_input.setText(self.data[0])
            self.name_input.setText(self.data[1] if self.data[1] else "")
            self.phone_input.setText(self.data[2] if self.data[2] else "")
            self.parent_name_input.setText(self.data[3] if self.data[3] else "")
            if self.data[4]:
                self.dob_input.setDate(QDate.fromString(self.data[4], "yyyy-MM-dd"))
            self.address_input.setText(self.data[5] if self.data[5] else "")
            self.notes_input.setPlainText(self.data[6] if self.data[6] else "")
            if self.data[7]:
                self.class_input.setCurrentText(self.data[7])
            if self.data[8]:
                self.reg_date_input.setDate(QDate.fromString(self.data[8], "yyyy-MM-dd"))
    
    def save_student(self):
        """Lưu thông tin học sinh"""
        student_id = self.student_id_input.text().strip()
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        parent_name = self.parent_name_input.text().strip()
        dob = self.dob_input.date().toString("yyyy-MM-dd")
        address = self.address_input.text().strip()
        notes = self.notes_input.toPlainText().strip()
        class_name = self.class_input.currentText()
        reg_date = self.reg_date_input.date().toString("yyyy-MM-dd")
        
        # Validate
        if not student_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập ID học sinh!")
            return
        
        if not name:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập tên học sinh!")
            return
        
        try:
            if self.is_edit_mode:
                self.db.update_student(student_id, name, phone, parent_name, dob, address, notes, class_name, reg_date)
                QMessageBox.information(self, "Thành công", "Đã cập nhật thông tin học sinh!")
            else:
                # Kiểm tra ID đã tồn tại chưa
                existing = self.db.get_student_by_id(student_id)
                if existing:
                    QMessageBox.warning(self, "Cảnh báo", f"ID học sinh '{student_id}' đã tồn tại!")
                    return
                
                self.db.insert_student(student_id, name, phone, parent_name, dob, address, notes, class_name, reg_date)
                QMessageBox.information(self, "Thành công", "Đã thêm học sinh mới!")
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu thông tin: {e}")


class StudentImportDialog(QDialog):
    """Dialog import học sinh từ tiến độ học tập"""
    def __init__(self, parent, db, students_list):
        super().__init__(parent)
        self.db = db
        self.students_list = students_list  # Giờ là tuple (name, class_name, attendance_count, num_sessions)
        self.selected_students = []
        
        self.setWindowTitle("Import học sinh từ tiến độ học tập")
        self.resize(900, 500)
        
        self.setStyleSheet("""
            QDialog { background-color: #f8f9fa; }
            QTableWidget { 
                border: 1px solid #dee2e6; 
                gridline-color: #eee; 
                background-color: white;
            }
            QHeaderView::section { 
                background-color: #343a40; 
                color: white;
                font-weight: bold; 
                border: 1px solid #454d55; 
                padding: 5px;
            }
            QPushButton {
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tiêu đề
        title = QLabel("📥 IMPORT HỌC SINH TỪ TIẾN ĐỘ HỌC TẬP")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        info_label = QLabel(f"Tìm thấy {len(self.students_list)} học sinh chưa có hồ sơ. Chọn những học sinh cần tạo hồ sơ:")
        layout.addWidget(info_label)
        
        # Bảng danh sách học sinh cần import
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Chọn", "Tên học sinh", "Lớp", "Số buổi/tuần", "Số lần có mặt"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        for idx, (name, class_name, attendance_count, num_sessions) in enumerate(self.students_list):
            self.table.insertRow(idx)
            
            # Checkbox chọn
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.table.setCellWidget(idx, 0, checkbox)
            
            # Tên học sinh
            self.table.setItem(idx, 1, QTableWidgetItem(name))
            
            # Lớp
            self.table.setItem(idx, 2, QTableWidgetItem(class_name if class_name else ""))
            
            # Số buổi/tuần
            sessions_item = QTableWidgetItem(str(num_sessions))
            sessions_item.setTextAlignment(Qt.AlignCenter)
            # Tô màu khác cho những học sinh học 2 buổi/tuần
            if num_sessions == 2:
                sessions_item.setBackground(QColor("#fff3cd"))
                sessions_item.setForeground(QColor("#856404"))
            self.table.setItem(idx, 3, sessions_item)
            
            # Số lần có mặt
            attendance_item = QTableWidgetItem(str(attendance_count))
            attendance_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 4, attendance_item)
        
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        # Nút lưu
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("✅ Tạo hồ sơ cho những học sinh được chọn")
        self.btn_save.setStyleSheet("background-color: #28a745; color: white; font-size: 13px;")
        self.btn_save.setFixedHeight(40)
        self.btn_save.clicked.connect(self.create_profiles)
        
        btn_cancel = QPushButton("Hủy")
        btn_cancel.setStyleSheet("background-color: #6c757d; color: white;")
        btn_cancel.setFixedHeight(40)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def create_profiles(self):
        """Tạo hồ sơ cho những học sinh được chọn"""
        # Lấy những học sinh được chọn (loại bỏ duplicates dựa trên name)
        selected_students_info = []
        seen_names = set()
        
        for idx in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(idx, 0)
            if checkbox and checkbox.isChecked():
                name = self.table.item(idx, 1).text()
                # Chỉ thêm nếu chưa thêm học sinh này
                if name not in seen_names:
                    class_name = self.table.item(idx, 2).text()
                    num_sessions = int(self.table.item(idx, 3).text())
                    selected_students_info.append((name, class_name, num_sessions))
                    seen_names.add(name)
        
        if not selected_students_info:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ít nhất một học sinh!")
            return
        
        # Tạo dialog input để nhập ID và các thông tin
        dialog = QDialog(self)
        dialog.setWindowTitle("Tạo ID học sinh tự động")
        dialog.setFixedWidth(400)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Tạo ID tự động theo định dạng:"))
        
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Tiền tố:"))
        prefix_input = QLineEdit("HS")
        prefix_input.setFixedWidth(80)
        format_layout.addWidget(prefix_input)
        
        format_layout.addWidget(QLabel("Bắt đầu từ số:"))
        start_spin = QSpinBox()
        start_spin.setValue(1)
        start_spin.setMinimum(1)
        start_spin.setMaximum(9999)
        format_layout.addWidget(start_spin)
        
        format_layout.addStretch()
        layout.addLayout(format_layout)
        
        layout.addWidget(QLabel("Ví dụ: HS001, HS002, ..."))
        
        # Chú thích cho học sinh 2 buổi/tuần
        note_label = QLabel(
            "<b>Lưu ý:</b> Học sinh học 2 buổi/tuần sẽ được gán <b>1 ID duy nhất</b> "
            "(không tạo ID riêng cho từng buổi)."
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #ff9800; background-color: #fff3cd; padding: 10px; border-radius: 4px;")
        layout.addWidget(note_label)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Tạo")
        btn_ok.setStyleSheet("background-color: #007bff; color: white;")
        btn_cancel = QPushButton("Hủy")
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)
        
        if dialog.exec():
            prefix = prefix_input.text() or "HS"
            start_num = start_spin.value()
            
            try:
                count = 0
                id_counter = start_num
                
                for name, class_name, num_sessions in selected_students_info:
                    # Tạo ID tự động (chỉ tạo 1 ID dù học 1 hay 2 buổi/tuần)
                    student_id = f"{prefix}{id_counter:03d}"
                    
                    # Kiểm tra ID đã tồn tại chưa
                    if self.db.get_student_by_id(student_id):
                        id_counter += 1
                        continue
                    
                    # Tạo hồ sơ mới từ dữ liệu tiến độ
                    self.db.insert_student(
                        student_id=student_id,
                        name=name,
                        phone="",
                        parent_name="",
                        date_of_birth="",
                        address="",
                        notes=f"Tạo từ import tiến độ học tập ({num_sessions} buổi/tuần)",
                        class_name=class_name,
                        registration_date=QDate.currentDate().toString("yyyy-MM-dd")
                    )
                    count += 1
                    id_counter += 1
                
                QMessageBox.information(
                    self, 
                    "Thành công", 
                    f"Đã tạo hồ sơ cho {count} học sinh!\n\n"
                    f"ID được tạo từ {prefix}{start_num:03d} trở đi\n\n"
                    f"<b>Lưu ý:</b> Những học sinh học 2 buổi/tuần được gán 1 ID duy nhất"
                )
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể tạo hồ sơ: {e}")
