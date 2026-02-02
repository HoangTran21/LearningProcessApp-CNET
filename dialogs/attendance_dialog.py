from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QDateEdit, QCheckBox, QListWidget, 
                             QListWidgetItem, QGroupBox, QPushButton, QApplication)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QScreen


class AttendanceDialog(QDialog):
    def __init__(self, parent, db_conn):
        super().__init__(parent)
        self.setWindowTitle("Điểm danh học sinh")
        self.setFixedSize(500, 680)
        self.db_conn = db_conn
        self.all_students = []
        
        self.center_dialog()

        self.setStyleSheet("""
            QDialog { background-color: #f8f9fa; }
            QGroupBox { 
                font-weight: bold; border: 1px solid #d1d1d1; 
                border-radius: 8px; margin-top: 15px; background-color: white;
            }
            QListWidget { border: none; outline: none; background: white; }
            
            QListWidget::item { 
                padding: 12px; 
                border-bottom: 1px solid #f0f0f0; 
                color: #333; 
            }
            QListWidget::item:hover { background-color: #f1faff; }
            
            QCheckBox { font-weight: bold; color: #007bff; }
            
            QListWidget::indicator { width: 20px; height: 20px; border: 2px solid #ccc; border-radius: 4px; }
            QListWidget::indicator:checked { background-color: #28a745; border: 2px solid #28a745; }
            
            QCheckBox#SelectAll {
                font-size: 16px;
                spacing: 8px;
                color: #d63384;
                font-weight: bold;
                padding: 8px;
                background-color: #ffffff;
                border-radius: 5px;
            }
            QCheckBox#SelectAll:hover {
                background-color: #d63384;
                color: #ffffff;
            }
            QCheckBox#SelectAll::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #d63384;
                border-radius: 4px;
                background-color: white;
            }

            QCheckBox#SelectAll::indicator:hover {
                border: 2px solid #b02a6f;
                background-color: #f8d7da;
            }

            QCheckBox#SelectAll::indicator:checked {
                background-color: #28a745;
                border: 2px solid #1e7e34;
            }
            
            QCheckBox#SelectAll::indicator:checked:pressed {
                background-color: #1e7e34;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Lọc lớp học:")
        self.class_filter = QComboBox()
        self.class_filter.addItems(["Tất cả lớp", "Sáng T7", "Chiều T7", "Sáng CN", "Chiều CN"])
        self.class_filter.setStyleSheet("""
            QComboBox { 
                padding: 5px; border: 1px solid #ccc; border-radius: 4px; font-weight: bold; color: #d63384; 
            }
        """)
        self.class_filter.currentTextChanged.connect(self.refresh_list)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.class_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        date_layout = QHBoxLayout()
        date_label = QLabel("Ngày điểm danh:")
        self.attendance_date = QDateEdit()
        self.attendance_date.setCalendarPopup(True)
        self.attendance_date.setDate(QDate.currentDate())
        self.attendance_date.setStyleSheet("""
            QDateEdit { 
                padding: 5px; border: 1px solid #ccc; border-radius: 4px; font-weight: bold; color: #d63384; 
            }
        """)
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.attendance_date)
        date_layout.addStretch()
        layout.addLayout(date_layout)

        # Checkbox chọn tất cả
        self.cb_select_all = QCheckBox("Chọn tất cả học viên")
        self.cb_select_all.setObjectName("SelectAll") 
        self.cb_select_all.setCursor(Qt.PointingHandCursor)
        self.cb_select_all.stateChanged.connect(self.toggle_select_all)
        layout.addWidget(self.cb_select_all)

        self.group_box = QGroupBox("Danh sách học viên")
        group_layout = QVBoxLayout(self.group_box)
        group_layout.setContentsMargins(10, 25, 10, 10)
        self.list_widget = QListWidget()
        group_layout.addWidget(self.list_widget)
        layout.addWidget(self.group_box)

        btn_box = QHBoxLayout()
        self.btn_confirm = QPushButton("XÁC NHẬN ĐIỂM DANH")
        self.btn_confirm.setFixedHeight(40)
        self.btn_confirm.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; border-radius: 5px;")
        self.btn_confirm.clicked.connect(self.accept)
        
        self.btn_close = QPushButton("Đóng")
        self.btn_close.setFixedHeight(40)
        self.btn_close.clicked.connect(self.reject)
        
        btn_box.addWidget(self.btn_close)
        btn_box.addWidget(self.btn_confirm)
        layout.addLayout(btn_box)

        self.load_students()

    def toggle_select_all(self, state):
        # Chọn hoặc bỏ chọn tất cả học viên
        new_state = Qt.Checked if state == 2 else Qt.Unchecked
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole):
                item.setCheckState(new_state)

    def refresh_list(self):
        self.list_widget.clear()
        self.cb_select_all.blockSignals(True)
        self.cb_select_all.setCheckState(Qt.Unchecked)
        self.cb_select_all.blockSignals(False)
        
        filter_text = self.class_filter.currentText()
        for name, cls in self.all_students:
            if filter_text == "Tất cả lớp" or filter_text == cls:
                item = QListWidgetItem(f"{name}  |  Lớp: {cls}")
                # Lưu tuple (tên, lớp) vào UserRole
                item.setData(Qt.UserRole, (name, cls))
                # Đặt flags để có thể check
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.list_widget.addItem(item)
        
        self.group_box.setTitle(f"Học viên lớp {filter_text} ({self.list_widget.count()})")

    def get_selected_data(self):
        selected = []
        chosen_date = self.attendance_date.date().toString("yyyy-MM-dd")
        
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                data = item.data(Qt.UserRole)
                if data:
                    selected.append((data[0], data[1], chosen_date))
        return selected

    def center_dialog(self):
        qr = self.frameGeometry()
        cp = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def load_students(self):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT name, class_name FROM progress 
                WHERE id IN (SELECT MAX(id) FROM progress GROUP BY name)
                ORDER BY class_name, name
            """)
            self.all_students = cursor.fetchall()
            self.refresh_list()
        except Exception as e:
            print(f"Lỗi DB: {e}")
