import sys
import sqlite3
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QTableWidget, 
                             QTableWidgetItem, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QHeaderView, QComboBox, 
                             QLineEdit, QTextEdit, QLabel, QDialog, QFormLayout, 
                             QMessageBox, QGroupBox, QFileDialog, QDateEdit, 
                             QAbstractItemView, QCompleter)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QIcon, QScreen
from docx import Document

class EntryDialog(QDialog):
    def __init__(self, parent=None, data=None, student_list=None, db_conn=None):
        super().__init__(parent)
        self.setWindowTitle("Thông tin tiến độ")
        self.setFixedWidth(500)
        self.setWindowIcon(QIcon("logo_app.ico"))
        self.db_conn = db_conn 
        
        self.setStyleSheet("""
            QDialog { background-color: #f4f7f6; }
            QGroupBox { 
                font-weight: bold; border: 2px solid #d1d1d1; 
                border-radius: 8px; margin-top: 10px; background-color: white;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLineEdit, QComboBox, QDateEdit, QTextEdit { 
                border: 1px solid #ccc; border-radius: 4px; padding: 8px; background-color: #ffffff;
            }
            QLabel { color: #444; font-size: 13px; }
        """)

        layout = QVBoxLayout(self)
        form_group = QGroupBox("Chi tiết học tập")
        form_layout = QFormLayout(form_group)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        if data:
            self.date_edit.setDate(QDate.fromString(data[1], "yyyy-MM-dd"))
        else:
            self.date_edit.setDate(QDate.currentDate())

        self.name_edit = QLineEdit(data[2] if data else "")
        self.class_edit = QComboBox()
        self.class_edit.addItems(["Sáng T7", "Chiều T7", "Sáng CN", "Chiều CN"])
        if data: self.class_edit.setCurrentText(data[3])

        if student_list:
            completer = QCompleter(student_list)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            self.name_edit.setCompleter(completer)
            completer.activated.connect(self.auto_fill_class)
            self.name_edit.editingFinished.connect(lambda: self.auto_fill_class(self.name_edit.text()))
        
        self.status_edit = QComboBox()
        self.status_edit.addItems(["Đi học", "Nghỉ học"])
        if data: self.status_edit.setCurrentText(data[4])
        
        self.content_edit = QTextEdit(data[5] if data else "")
        self.content_edit.setPlaceholderText("Nhập nội dung chi tiết bài học tại đây...")
        self.content_edit.setMinimumHeight(150)

        self.highlight_cb = QComboBox()
        self.highlight_cb.addItems(["Bình thường", "Cần chú ý (Highlight)", "Học tốt"])
        if data: self.highlight_cb.setCurrentIndex(data[6])

        form_layout.addRow("Chọn ngày:", self.date_edit)
        form_layout.addRow("Tên học sinh:", self.name_edit)
        form_layout.addRow("Lớp:", self.class_edit)
        form_layout.addRow("Trạng thái:", self.status_edit)
        form_layout.addRow("Nội dung bài học:", self.content_edit)
        form_layout.addRow("Mức độ:", self.highlight_cb)
        
        layout.addWidget(form_group)

        self.btn_save = QPushButton("Lưu dữ liệu")
        self.btn_save.setFixedHeight(40)
        self.btn_save.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_save.clicked.connect(self.validate_and_accept)
        layout.addWidget(self.btn_save)

    def auto_fill_class(self, name):
        if self.db_conn and name:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT class_name FROM progress WHERE name = ? ORDER BY date DESC LIMIT 1", (name,))
            res = cursor.fetchone()
            if res: self.class_edit.setCurrentText(res[0])

    def validate_and_accept(self):
        if not self.name_edit.text().strip() or not self.content_edit.toPlainText().strip():
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập đầy đủ thông tin!")
            return
        self.accept()

    def get_data(self):
        return (self.date_edit.date().toString("yyyy-MM-dd"), self.name_edit.text().strip(), 
                self.class_edit.currentText(), self.status_edit.currentText(), 
                self.content_edit.toPlainText(), self.highlight_cb.currentIndex())

class SummaryDialog(QDialog):
    def __init__(self, parent, db_connection):
        super().__init__(parent)
        self.setWindowTitle("Tổng kết tháng")
        self.resize(900, 600)
        self.conn = db_connection
        self.setStyleSheet("background-color: #f4f7f6;")
        layout = QVBoxLayout(self)
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(4)
        self.summary_table.setHorizontalHeaderLabels(["STT", "Học sinh", "Lớp", "Nhận xét của giáo viên"])
        self.summary_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(QLabel("Bảng tổng hợp học sinh (Chỉ nhập nhận xét vào cột cuối):"))
        layout.addWidget(self.summary_table)
        
        self.btn_export = QPushButton("XUẤT FILE WORD")
        self.btn_export.setFixedSize(200, 40)
        self.btn_export.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_export.clicked.connect(self.export_to_word)
        layout.addWidget(self.btn_export, alignment=Qt.AlignRight)
        self.load_students_list()

    def load_students_list(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT name, class_name FROM progress ORDER BY class_name, name")
        rows = cursor.fetchall()
        self.summary_table.setRowCount(len(rows))
        for i, (name, cls) in enumerate(rows):
            for col, val in enumerate([str(i+1), name, cls]):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.summary_table.setItem(i, col, item)
            self.summary_table.setItem(i, 3, QTableWidgetItem(""))

    def export_to_word(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file Word", f"TongKet_Thang_{datetime.now().month}.docx", "Word Files (*.docx)")
        if not path: return
        doc = Document()
        doc.add_heading(f'BÁO CÁO TỔNG KẾT THÁNG {datetime.now().month}/{datetime.now().year}', 0)
        table = doc.add_table(rows=1, cols=4); table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'STT'; hdr_cells[1].text = 'Học sinh'; hdr_cells[2].text = 'Lớp'; hdr_cells[3].text = 'Nhận xét tháng'
        for r in range(self.summary_table.rowCount()):
            row_cells = table.add_row().cells
            for c in range(4): row_cells[c].text = self.summary_table.item(r, c).text() if self.summary_table.item(r, c) else ""
        doc.save(path)
        QMessageBox.information(self, "Thành công", "Đã xuất báo cáo Word thành công!")

class StudentManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sổ tay các lớp Python 2026")
        self.resize(1150, 800)
        self.center_window()
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: white; color: #333; }
            QTableWidget { gridline-color: #ddd; border: 1px solid #ccc; background-color: #fdfdfd; }
            QHeaderView::section { background-color: #f8f9fa; padding: 5px; border: 1px solid #ddd; font-weight: bold; }
            QLineEdit, QDateEdit, QComboBox { border: 1px solid #ccc; padding: 5px; border-radius: 4px; }
            
            QPushButton { border-radius: 4px; font-weight: bold; }
            QPushButton#btn_add { background-color: #007bff; color: white; }
            QPushButton#btn_add:hover { background-color: #0056b3; }
            QPushButton#btn_edit { background-color: #ffc107; color: #333; }
            QPushButton#btn_edit:hover { background-color: #e0a800; }
            QPushButton#btn_delete { background-color: #dc3545; color: white; }
            QPushButton#btn_delete:hover { background-color: #c82333; }
            QPushButton#btn_summary { background-color: #17a2b8; color: white; }
            QPushButton#btn_summary:hover { background-color: #138496; }
            
            QPushButton#btn_filter { background-color: #6c757d; color: white; padding: 5px 15px; }
            QPushButton#btn_filter:hover { background-color: #5a6268; }
            QPushButton#btn_reset { background-color: #f8f9fa; color: #333; border: 1px solid #ccc; padding: 5px 15px; }
            QPushButton#btn_reset:hover { background-color: #e2e6ea; }
        """)
        self.conn = sqlite3.connect('hoc_tap.db')
        self.init_db()
        self.setup_ui()
        self.load_data(is_reset=True)

    def center_window(self):
        qr = self.frameGeometry()
        cp = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        qr.moveCenter(cp); self.move(qr.topLeft())

    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS progress (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date TEXT, name TEXT, class_name TEXT, 
                            status TEXT, content TEXT, is_highlighted INTEGER DEFAULT 0)''')
        self.conn.commit()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        filter_layout = QHBoxLayout()
        self.search_name = QLineEdit(); self.search_name.setPlaceholderText("Tên học sinh...")
        
        self.search_date = QDateEdit(); self.search_date.setCalendarPopup(True)
        self.search_date.setDisplayFormat("yyyy-MM-dd"); self.search_date.setDate(QDate.currentDate())
        self.search_date.setFixedWidth(100)
        
        self.filter_class = QComboBox()
        self.filter_class.addItems(["Tất cả lớp", "Sáng T7", "Chiều T7", "Sáng CN", "Chiều CN"])
        
        self.btn_filter = QPushButton("Lọc dữ liệu"); self.btn_filter.setObjectName("btn_filter")
        self.btn_filter.clicked.connect(lambda: self.load_data(is_reset=False))
        
        self.btn_reset = QPushButton("Hiện tất cả"); self.btn_reset.setObjectName("btn_reset")
        self.btn_reset.clicked.connect(lambda: self.load_data(is_reset=True))
        
        filter_layout.addWidget(QLabel("Lớp:")); filter_layout.addWidget(self.filter_class)
        filter_layout.addWidget(QLabel("Tên:")); filter_layout.addWidget(self.search_name)
        filter_layout.addWidget(QLabel("Ngày:")); filter_layout.addWidget(self.search_date)
        filter_layout.addWidget(self.btn_filter); filter_layout.addWidget(self.btn_reset)
        main_layout.addLayout(filter_layout)

        # Toolbar chức năng
        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("+ Thêm mới"); self.btn_add.setObjectName("btn_add")
        self.btn_edit = QPushButton("✎ Sửa"); self.btn_edit.setObjectName("btn_edit")
        self.btn_delete = QPushButton("🗑 Xóa"); self.btn_delete.setObjectName("btn_delete")
        self.btn_summary = QPushButton("📊 Tổng kết"); self.btn_summary.setObjectName("btn_summary")
        
        for btn in [self.btn_add, self.btn_edit, self.btn_delete, self.btn_summary]:
            btn.setFixedWidth(130); btn.setFixedHeight(35); toolbar.addWidget(btn)
        
        self.btn_add.clicked.connect(self.add_entry)
        self.btn_edit.clicked.connect(self.edit_entry)
        self.btn_delete.clicked.connect(self.delete_entry)
        self.btn_summary.clicked.connect(self.open_summary)
        toolbar.addStretch(); main_layout.addLayout(toolbar)

        self.table = QTableWidget(); self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Ngày", "Học sinh", "Lớp học", "Trạng thái", "Nội dung bài học"])
        self.table.hideColumn(0); self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True); self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        main_layout.addWidget(self.table)
        container = QWidget(); container.setLayout(main_layout); self.setCentralWidget(container)

    def load_data(self, is_reset=False):
        cursor = self.conn.cursor()
        if is_reset:
            self.search_name.clear()
            self.filter_class.setCurrentIndex(0)
            self.search_date.setDate(QDate.currentDate())
            query = "SELECT * FROM progress ORDER BY date DESC"
            params = []
        else:
            name_q = self.search_name.text()
            date_q = self.search_date.date().toString("yyyy-MM-dd")
            cls_q = self.filter_class.currentText()
            query = "SELECT * FROM progress WHERE name LIKE ? AND date = ?"
            params = [f'%{name_q}%', date_q]
            if cls_q != "Tất cả lớp":
                query += " AND class_name = ?"
                params.append(cls_q)
            query += " ORDER BY date DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        self.table.setRowCount(0)
        for row_data in rows:
            row_idx = self.table.rowCount(); self.table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data[:-1]):
                item = QTableWidgetItem(str(value))
                if row_data[6] == 1: item.setBackground(QColor("#fff3cd"))
                elif row_data[6] == 2: item.setBackground(QColor("#d4edda"))
                self.table.setItem(row_idx, col_idx, item)

    def get_existing_names(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM progress")
        return [row[0] for row in cursor.fetchall()]

    def open_summary(self):
        SummaryDialog(self, self.conn).exec()

    def add_entry(self):
        dialog = EntryDialog(self, student_list=self.get_existing_names(), db_conn=self.conn)
        if dialog.exec():
            self.conn.cursor().execute("INSERT INTO progress (date, name, class_name, status, content, is_highlighted) VALUES (?,?,?,?,?,?)", dialog.get_data())
            self.conn.commit(); self.load_data(is_reset=True)

    def edit_entry(self):
        curr_row = self.table.currentRow()
        if curr_row < 0: return
        row_id = self.table.item(curr_row, 0).text()
        cursor = self.conn.cursor(); cursor.execute("SELECT * FROM progress WHERE id=?", (row_id,))
        dialog = EntryDialog(self, cursor.fetchone(), self.get_existing_names(), self.conn)
        if dialog.exec():
            self.conn.cursor().execute("UPDATE progress SET date=?, name=?, class_name=?, status=?, content=?, is_highlighted=? WHERE id=?", (*dialog.get_data(), row_id))
            self.conn.commit(); self.load_data(is_reset=True)

    def delete_entry(self):
        curr_row = self.table.currentRow()
        if curr_row >= 0 and QMessageBox.question(self, "Xác nhận", "Xóa dòng này?") == QMessageBox.Yes:
            self.conn.cursor().execute("DELETE FROM progress WHERE id=?", (self.table.item(curr_row, 0).text(),))
            self.conn.commit(); self.load_data(is_reset=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudentManager(); window.show()
    sys.exit(app.exec())