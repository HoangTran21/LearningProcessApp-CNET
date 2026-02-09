import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
                             QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QLabel,
                             QAbstractItemView, QMessageBox, QPushButton, QLineEdit,
                             QComboBox, QDateEdit)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QScreen, QIcon

from database import Database
from styles import MAIN_STYLE
from dialogs.entry_dialog import EntryDialog
from dialogs.attendance_dialog import AttendanceDialog
from dialogs.statistics_dialog import StatisticsDialog
from dialogs.common_comment_dialog import CommonCommentDialog
from dialogs.student_profile_dialog import StudentProfileDialog


class StudentManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setWindowTitle("Sổ tay Python 2026 - Quản lý tiến độ")
        self.setWindowIcon(QIcon("logo_app.png"))
        self.resize(1150, 800)
        self.center_window()
        
        self.setStyleSheet(MAIN_STYLE)
        self.setup_ui()
        
        self.load_data()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        main_layout.addLayout(self._create_filter_bar())
        main_layout.addLayout(self._create_toolbar())
        main_layout.addWidget(self._create_data_table())

    def _create_filter_bar(self):
        layout = QHBoxLayout()
        
        self.search_name = QLineEdit()
        self.search_name.setPlaceholderText("🔍 Tên học sinh...")
        
        self.filter_class = QComboBox()
        self.filter_class.addItems(["Tất cả lớp", "Sáng T7", "Chiều T7", "Sáng CN", "Chiều CN"])
        
        self.check_date = QComboBox()
        self.check_date.addItems(["Tất cả thời gian", "Theo ngày"])
        self.check_date.setFixedWidth(100)
        
        self.search_date = QDateEdit()
        self.search_date.setCalendarPopup(True)
        self.search_date.setDisplayFormat("yyyy-MM-dd")
        self.search_date.setDate(QDate.currentDate())
        self.search_date.setEnabled(False)
        self.check_date.currentIndexChanged.connect(lambda i: self.search_date.setEnabled(i == 1))

        self.btn_filter = QPushButton("Lọc")
        self.btn_filter.setFixedWidth(80)
        self.btn_filter.setStyleSheet("background-color: #f8f9fa; border: 1px solid #ccc; padding: 5px;")
        self.btn_filter.clicked.connect(self.load_data)

        layout.addWidget(QLabel("Lớp:"))
        layout.addWidget(self.filter_class)
        layout.addWidget(QLabel("Học sinh:"))
        layout.addWidget(self.search_name)
        layout.addWidget(self.check_date)
        layout.addWidget(self.search_date)
        layout.addWidget(self.btn_filter)
        
        return layout

    def _create_toolbar(self):
        layout = QHBoxLayout()
        
        # Các nút chức năng
        self.btn_att = QPushButton("✓ ĐIỂM DANH")
        self.btn_att.setStyleSheet("background-color: #28a745; color: white;")
        self.btn_att.setFixedSize(140, 35)
        self.btn_att.clicked.connect(self.open_attendance)
        
        self.btn_common = QPushButton("✍ Nhận xét chung")
        self.btn_common.setStyleSheet("background-color: #007bff; color: white;")
        self.btn_common.setFixedSize(160, 35)
        self.btn_common.clicked.connect(self.add_common_comment)
        
        self.btn_edit = QPushButton("✎ Viết nhận xét")
        self.btn_edit.setStyleSheet("background-color: #ffc107; color: #222;")
        self.btn_edit.setFixedSize(140, 35)
        self.btn_edit.clicked.connect(self.edit_entry)
        
        self.btn_del = QPushButton("🗑 Xóa")
        self.btn_del.setStyleSheet("background-color: #dc3545; color: white;")
        self.btn_del.setFixedSize(140, 35)
        self.btn_del.clicked.connect(self.delete_entry)
        
        self.btn_stats = QPushButton("📊 THỐNG KÊ")
        self.btn_stats.setStyleSheet("background-color: #17a2b8; color: white;")
        self.btn_stats.setFixedSize(140, 35)
        self.btn_stats.clicked.connect(self.open_statistics)
        
        self.btn_profile = QPushButton("👤 HỒ SƠ HỌC SINH")
        self.btn_profile.setStyleSheet("background-color: #6f42c1; color: white;")
        self.btn_profile.setFixedSize(160, 35)
        self.btn_profile.clicked.connect(self.open_student_profile)
        
        layout.addWidget(self.btn_att)
        layout.addWidget(self.btn_common)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_del)
        layout.addStretch()
        layout.addWidget(self.btn_profile)
        layout.addWidget(self.btn_stats)
        
        return layout

    def _create_data_table(self):
        # Cấu hình bảng dl
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Ngày", "Học sinh", "Lớp", "Trạng thái", "Nội dung bài học (Cập nhật cuối buổi)"
        ])
        self.table.hideColumn(0)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        return self.table

    def load_data(self):
        try:
            # Lấy dl từ db
            rows = self.db.get_filtered_progress(
                name=self.search_name.text(),
                class_name=self.filter_class.currentText(),
                date=self.search_date.date().toString("yyyy-MM-dd") if self.check_date.currentIndex() == 1 else None
            )
            self._update_table_view(rows)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {e}")

    def _update_table_view(self, rows):
        self.table.setRowCount(0)
        for row_data in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            
            # Duyệt qua các cột (trừ cột cuối)
            for c, val in enumerate(row_data[:-1]):
                item = QTableWidgetItem(str(val))
                
                # Xử lý màu highlight theo is_highlighted
                if row_data[6] == 1:  # Cần chú ý
                    item.setBackground(QColor("#fff3cd"))
                elif row_data[6] == 2:  # Học tốt
                    item.setBackground(QColor("#d4edda"))
                elif row_data[6] == 3:  # Báo động
                    item.setBackground(QColor("#f8d7da"))
                
                # Xử lý màu chữ cho nội dung chưa có
                if c == 5 and val == "(Chưa có nhận xét cuối buổi)":
                    item.setForeground(QColor("#d9534f"))
                    font = item.font()
                    font.setItalic(True)
                    item.setFont(font)
                
                self.table.setItem(r, c, item)

    def open_attendance(self):
        dialog = AttendanceDialog(self, self.db.conn)
        if dialog.exec():
            selected_data = dialog.get_selected_data()
            if selected_data:
                self.db.bulk_insert_attendance(selected_data)
                self.load_data()
                QMessageBox.information(self, "Thành công", 
                                      f"Đã điểm danh cho {len(selected_data)} học sinh.")

    def add_common_comment(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn các học sinh cần nhận xét chung!")
            return

        dialog = CommonCommentDialog(self)
        if dialog.exec():
            content = dialog.get_content()
            ids_to_update = [self.table.item(row.row(), 0).text() for row in selected_rows]
            try:
                self.db.update_entries_content(ids_to_update, content)
                self.load_data()
                QMessageBox.information(self, "Thành công", f"Đã cập nhật nhận xét cho {len(ids_to_update)} học sinh.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật nhận xét: {e}")

    def edit_entry(self):
        curr = self.table.currentRow()
        if curr < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một dòng học sinh để viết nhận xét!")
            return
        
        row_id = self.table.item(curr, 0).text()
        row_data = list(self.db.get_entry_by_id(row_id))
        
        #Sau khi điểm danh
        if row_data[5] == "(Chưa có nhận xét cuối buổi)":
            row_data[5] = ""
        
        student_list = self.db.get_distinct_student_names()
        dialog = EntryDialog(self, data=row_data, student_list=student_list, db_conn=self.db.conn)
        if dialog.exec():
            data = dialog.get_data()
            self.db.update_entry(row_id, *data)
            self.load_data()

    def delete_entry(self):
        #Xử lý xóa nhiều dòng
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn dòng cần xóa!")
            return

        count = len(selected_rows)
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Xác nhận xóa")
        msg_box.setText(f"<h3>Bạn có chắc chắn muốn xóa {count} bản ghi đã chọn?</h3>")
        msg_box.setInformativeText("Hành động này không thể hoàn tác.")
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        msg_box.setStyleSheet("""
            QMessageBox { background-color: #ffffff; }
            QLabel { color: #333; font-size: 14px; }
            QPushButton { 
                border-radius: 4px; padding: 6px 20px; font-weight: bold; min-width: 70px; 
            }
            QPushButton[text="&Yes"] { background-color: #dc3545; color: white; }
            QPushButton[text="&No"] { background-color: #f8f9fa; border: 1px solid #ccc; }
        """)
        
        if msg_box.exec() == QMessageBox.Yes:
            ids_to_delete = [self.table.item(row.row(), 0).text() for row in selected_rows]
            try:
                self.db.delete_entries(ids_to_delete)
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa dữ liệu: {e}")

    def open_statistics(self):
        dialog = StatisticsDialog(self, self.db.conn)
        dialog.exec()

    def open_student_profile(self):
        dialog = StudentProfileDialog(self, self.db)
        dialog.exec()
        self.load_data()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudentManager()
    window.show()
    sys.exit(app.exec())