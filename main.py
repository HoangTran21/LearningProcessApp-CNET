import sys
import sqlite3
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QTableWidget, 
                             QTableWidgetItem, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QHeaderView, QComboBox, 
                             QLineEdit, QTextEdit, QLabel, QDialog, QFormLayout, 
                             QMessageBox, QGroupBox, QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from docx import Document

class EntryDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Thông tin tiến độ")
        self.setFixedWidth(500)
        
        # GIỮ NGUYÊN STYLE CŨ CỦA BẠN
        self.setStyleSheet("""
            QDialog { background-color: #f4f7f6; }
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #d1d1d1; 
                border-radius: 8px; 
                margin-top: 10px; 
                background-color: white;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLineEdit, QComboBox { 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                padding: 8px; 
                background-color: #ffffff;
            }
            QTextEdit { 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                padding: 8px; 
                background-color: #ffffff;
                selection-background-color: #007bff;
            }
            QLabel { color: #444; font-size: 13px; }
        """)

        layout = QVBoxLayout(self)
        form_group = QGroupBox("Chi tiết học tập")
        form_layout = QFormLayout(form_group)
        
        today = datetime.now().strftime("%Y-%m-%d")
        self.date_edit = QLineEdit(data[1] if data else today)
        self.name_edit = QLineEdit(data[2] if data else "")
        
        self.class_edit = QComboBox()
        self.class_edit.addItems(["Sáng T7", "Chiều T7", "Sáng CN", "Chiều CN"])
        if data: self.class_edit.setCurrentText(data[3])
        
        self.status_edit = QLineEdit(data[4] if data else "Đi học")
        
        self.content_edit = QTextEdit(data[5] if data else "")
        self.content_edit.setPlaceholderText("Nhập nội dung chi tiết bài học tại đây...")
        self.content_edit.setMinimumHeight(150)

        self.highlight_cb = QComboBox()
        self.highlight_cb.addItems(["Bình thường", "Cần chú ý (Highlight)"])
        if data: self.highlight_cb.setCurrentIndex(data[6])

        form_layout.addRow("Ngày (YYYY-MM-DD):", self.date_edit)
        form_layout.addRow("Tên học sinh:", self.name_edit)
        form_layout.addRow("Lớp:", self.class_edit)
        form_layout.addRow("Trạng thái:", self.status_edit)
        form_layout.addRow("Nội dung bài học:", self.content_edit)
        form_layout.addRow("Mức độ:", self.highlight_cb)
        
        layout.addWidget(form_group)

        self.btn_save = QPushButton("Lưu dữ liệu")
        self.btn_save.setFixedHeight(40)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #007bff; 
                color: white; 
                font-weight: bold; 
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        self.btn_save.clicked.connect(self.accept)
        layout.addWidget(self.btn_save)

    def get_data(self):
        return (self.date_edit.text(), self.name_edit.text(), self.class_edit.currentText(),
                self.status_edit.text(), self.content_edit.toPlainText(), self.highlight_cb.currentIndex())

# --- Cửa sổ Tổng kết (Thêm mới theo yêu cầu) ---
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
        self.summary_table.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        self.summary_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        
        layout.addWidget(QLabel("Bảng tổng hợp học sinh:"))
        layout.addWidget(self.summary_table)
        
        btn_layout = QHBoxLayout()
        self.btn_export = QPushButton("XUẤT FILE WORD")
        self.btn_export.setFixedSize(200, 40)
        self.btn_export.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_export.clicked.connect(self.export_to_word)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_export)
        layout.addLayout(btn_layout)
        
        self.load_students_list()

    def load_students_list(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT name, class_name FROM progress ORDER BY class_name, name")
        rows = cursor.fetchall()
        self.summary_table.setRowCount(len(rows))
        for i, (name, cls) in enumerate(rows):
            self.summary_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.summary_table.setItem(i, 1, QTableWidgetItem(name))
            self.summary_table.setItem(i, 2, QTableWidgetItem(cls))
            self.summary_table.setItem(i, 3, QTableWidgetItem(""))

    def export_to_word(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file Word", f"TongKet_Thang_{datetime.now().month}.docx", "Word Files (*.docx)")
        if not path: return
        
        doc = Document()
        doc.add_heading(f'BÁO CÁO TỔNG KẾT THÁNG {datetime.now().month}/{datetime.now().year}', 0)
        
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'STT'
        hdr_cells[1].text = 'Học sinh'
        hdr_cells[2].text = 'Lớp'
        hdr_cells[3].text = 'Nhận xét tháng'
        
        for r in range(self.summary_table.rowCount()):
            row_cells = table.add_row().cells
            row_cells[0].text = self.summary_table.item(r, 0).text()
            row_cells[1].text = self.summary_table.item(r, 1).text()
            row_cells[2].text = self.summary_table.item(r, 2).text()
            row_cells[3].text = self.summary_table.item(r, 3).text() if self.summary_table.item(r, 3) else ""

        doc.save(path)
        QMessageBox.information(self, "Thành công", "Đã xuất báo cáo Word thành công!")

class StudentManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sổ tay Giáo viên 2026")
        self.resize(1100, 750)
        
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: white; color: #333; }
            QTableWidget { gridline-color: #ddd; border: 1px solid #ccc; background-color: #fdfdfd; }
            QHeaderView::section { background-color: #f8f9fa; padding: 5px; border: 1px solid #ddd; font-weight: bold; }
            QLineEdit { border: 1px solid #ccc; padding: 5px; border-radius: 3px; }
        """)

        self.conn = sqlite3.connect('hoc_tap.db')
        self.init_db()
        self.setup_ui()
        self.load_data()

    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS progress (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date TEXT, name TEXT, class_name TEXT, 
                            status TEXT, content TEXT, is_highlighted INTEGER DEFAULT 0)''')
        self.conn.commit()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        self.search_name = QLineEdit()
        self.search_name.setPlaceholderText("Tìm theo tên học sinh...")
        self.search_name.textChanged.connect(self.load_data)
        
        self.search_date = QLineEdit()
        self.search_date.setPlaceholderText("Tìm theo ngày (YYYY-MM-DD)...")
        self.search_date.textChanged.connect(self.load_data)

        self.filter_class = QComboBox()
        self.filter_class.addItems(["Tất cả lớp", "Sáng T7", "Chiều T7", "Sáng CN", "Chiều CN"])
        self.filter_class.currentTextChanged.connect(self.load_data)
        
        search_layout.addWidget(QLabel("Lọc lớp:"))
        search_layout.addWidget(self.filter_class)
        search_layout.addWidget(QLabel("Tìm kiếm:"))
        search_layout.addWidget(self.search_name)
        search_layout.addWidget(self.search_date)
        main_layout.addLayout(search_layout)

        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("+ Thêm mới")
        self.btn_edit = QPushButton("✎ Sửa")
        self.btn_delete = QPushButton("🗑 Xóa")
        # Nút tổng kết tháng
        self.btn_summary = QPushButton("📊 Tổng kết tháng")
        
        for btn in [self.btn_add, self.btn_edit, self.btn_delete, self.btn_summary]:
            btn.setFixedWidth(130)
            btn.setFixedHeight(35)
            toolbar.addWidget(btn)
        
        self.btn_add.clicked.connect(self.add_entry)
        self.btn_edit.clicked.connect(self.edit_entry)
        self.btn_delete.clicked.connect(self.delete_entry)
        self.btn_summary.clicked.connect(self.open_summary)
        
        toolbar.addStretch()
        main_layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Ngày", "Học sinh", "Lớp học", "Trạng thái", "Nội dung bài học"])
        self.table.hideColumn(0)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        main_layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def load_data(self):
        name_q = self.search_name.text()
        date_q = self.search_date.text()
        cls_q = self.filter_class.currentText()
        cursor = self.conn.cursor()
        query = "SELECT * FROM progress WHERE name LIKE ? AND date LIKE ?"
        params = [f'%{name_q}%', f'%{date_q}%']
        if cls_q != "Tất cả lớp":
            query += " AND class_name = ?"
            params.append(cls_q)
        query += " ORDER BY date DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        self.table.setRowCount(0)
        for row_data in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data[:-1]):
                item = QTableWidgetItem(str(value))
                if row_data[6] == 1:
                    item.setBackground(QColor("#fff3cd"))
                    item.setForeground(QColor("#856404"))
                self.table.setItem(row_idx, col_idx, item)

    def open_summary(self):
        dialog = SummaryDialog(self, self.conn)
        dialog.exec()

    def add_entry(self):
        dialog = EntryDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.conn.cursor().execute("INSERT INTO progress (date, name, class_name, status, content, is_highlighted) VALUES (?,?,?,?,?,?)", data)
            self.conn.commit()
            self.load_data()

    def edit_entry(self):
        curr_row = self.table.currentRow()
        if curr_row < 0: return
        row_id = self.table.item(curr_row, 0).text()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM progress WHERE id=?", (row_id,))
        dialog = EntryDialog(self, cursor.fetchone())
        if dialog.exec():
            data = dialog.get_data()
            cursor.execute("UPDATE progress SET date=?, name=?, class_name=?, status=?, content=?, is_highlighted=? WHERE id=?", (*data, row_id))
            self.conn.commit()
            self.load_data()

    def delete_entry(self):
        curr_row = self.table.currentRow()
        if curr_row < 0: return
        if QMessageBox.question(self, "Xác nhận", "Xóa dòng này?") == QMessageBox.Yes:
            row_id = self.table.item(curr_row, 0).text()
            self.conn.cursor().execute("DELETE FROM progress WHERE id=?", (row_id,))
            self.conn.commit()
            self.load_data()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudentManager()
    window.show()
    sys.exit(app.exec())