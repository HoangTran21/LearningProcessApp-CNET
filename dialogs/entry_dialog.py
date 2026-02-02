from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QGroupBox,
                             QPushButton, QLineEdit, QComboBox, QDateEdit,
                             QTextEdit, QMessageBox, QCompleter)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon


class EntryDialog(QDialog):
    def __init__(self, parent=None, data=None, student_list=None, db_conn=None):
        super().__init__(parent)
        self.setWindowTitle("Thông tin tiến độ")
        self.setFixedWidth(500)
        self.setWindowIcon(QIcon("logo_app.png"))
        self.db_conn = db_conn
        
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QGroupBox { 
                font-weight: bold; border: 1px solid #d1d1d1;
                border-radius: 8px; background-color: #ffffff; 
                margin-top: 25px;
            }
            QLineEdit, QComboBox, QDateEdit, QTextEdit { 
                border: 1px solid #ccc; border-radius: 4px; padding: 8px; background-color: white;
            }
        """)

        layout = QVBoxLayout(self)
        form_group = QGroupBox("Chi tiết học tập")
        form_layout = QFormLayout(form_group)
        form_layout.setContentsMargins(10, 25, 10, 10)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.fromString(data[1], "yyyy-MM-dd") if data else QDate.currentDate())

        self.name_edit = QLineEdit(data[2] if data else "")
        
        self.class_edit = QComboBox()
        self.class_edit.addItems(["Sáng T7", "Chiều T7", "Sáng CN", "Chiều CN"])
        if data: 
            self.class_edit.setCurrentText(data[3])

        if student_list:
            completer = QCompleter(student_list)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.name_edit.setCompleter(completer)
            self.name_edit.editingFinished.connect(lambda: self.auto_fill_class(self.name_edit.text()))
        

        self.status_edit = QComboBox()
        self.status_edit.addItems(["Đi học", "Nghỉ học"])
        if data: 
            self.status_edit.setCurrentText(data[4])
        
        self.content_edit = QTextEdit(data[5] if data else "")
        self.content_edit.setPlaceholderText("Nhập nội dung bài học...")
        self.content_edit.setMinimumHeight(150)

        self.highlight_cb = QComboBox()
        self.highlight_cb.addItems(["Bình thường", "Cần chú ý", "Học tốt", "Báo động"])
        if data: 
            self.highlight_cb.setCurrentIndex(data[6])

        form_layout.addRow("Ngày:", self.date_edit)
        form_layout.addRow("Học sinh:", self.name_edit)
        form_layout.addRow("Lớp:", self.class_edit)
        form_layout.addRow("Trạng thái:", self.status_edit)
        form_layout.addRow("Nội dung:", self.content_edit)
        form_layout.addRow("Đánh giá:", self.highlight_cb)
        
        layout.addWidget(form_group)
        
        self.btn_save = QPushButton("LƯU DỮ LIỆU")
        self.btn_save.setFixedHeight(40)
        self.btn_save.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_save.clicked.connect(self.validate_and_accept)
        layout.addWidget(self.btn_save)

    def auto_fill_class(self, name):
        if self.db_conn and name:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT class_name FROM progress WHERE name = ? ORDER BY date DESC LIMIT 1", (name,))
            res = cursor.fetchone()
            if res: 
                self.class_edit.setCurrentText(res[0])

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập tên học sinh!")
            return
        self.accept()

    def get_data(self):
        return (
            self.date_edit.date().toString("yyyy-MM-dd"), 
            self.name_edit.text().strip(), 
            self.class_edit.currentText(), 
            self.status_edit.currentText(), 
            self.content_edit.toPlainText(), 
            self.highlight_cb.currentIndex()
        )
