import calendar
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QPushButton, QAbstractItemView, QFileDialog, 
                             QMessageBox, QGroupBox, QDateEdit)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QGuiApplication, QColor
from docx import Document


class StatisticsDialog(QDialog):
    def __init__(self, parent, db_conn):
        super().__init__(parent)
        self.setWindowTitle("Báo cáo thống kê đào tạo")
        self.resize(1000, 750)
        self.db_conn = db_conn
        
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel#Title { font-size: 18px; font-weight: bold; color: #2c3e50; }
            QTableWidget { border: 1px solid #dee2e6; gridline-color: #eee; }
            QHeaderView::section { background-color: #f8f9fa; font-weight: bold; border: 1px solid #dee2e6; }
            QPushButton#ExportBtn { background-color: #2b5797; color: white; font-weight: bold; }
        """)

        layout = QVBoxLayout(self)
        
        title = QLabel("BÁO CÁO THỐNG KÊ TÌNH HÌNH LỚP HỌC")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        filter_group = QGroupBox("Chọn khoảng thời gian thống kê")
        filter_layout = QHBoxLayout(filter_group)
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))# Ngày bắt đầu lọc mặc định là 7 ngày trước ngày hiện tại
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        
        btn_refresh = QPushButton("🔄 Tải dữ liệu")
        btn_refresh.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold; font-size :14px;")
        btn_refresh.clicked.connect(self.calculate_stats)
        
        filter_layout.addWidget(QLabel("Từ ngày:"))
        filter_layout.addWidget(self.start_date)
        filter_layout.addWidget(QLabel("Đến ngày:"))
        filter_layout.addWidget(self.end_date)
        filter_layout.addWidget(btn_refresh)
        filter_layout.addStretch()
        layout.addWidget(filter_group)

        # Bảng 1: Thống kê tóm tắt
        layout.addWidget(QLabel("<b>1. Tóm tắt tỉ lệ chuyên cần theo lớp:</b> (Di chuột bôi đen và nhấn Ctrl+C để copy)"))
        self.summary_table = QTableWidget(0, 5)
        self.summary_table.setHorizontalHeaderLabels(["Tên lớp", "Sĩ số", "Số bạn đi học", "Số bạn nghỉ", "Tỉ lệ (%)"])
        
        self.summary_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.summary_table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.summary_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.summary_table.setFixedHeight(200)
        layout.addWidget(self.summary_table)

        # Bảng 2: Chi tiết học sinh & Nhận xét
        layout.addWidget(QLabel("<b>2. Chi tiết học viên và nhận xét:</b>"))
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(5)
        self.detail_table.setHorizontalHeaderLabels([
            "Ngày", "Lớp", "Tên học sinh", "Chuyên cần tháng", "Nhận xét cuối buổi"
        ])
        self.detail_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.detail_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.detail_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.detail_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        layout.addWidget(self.detail_table)
        
        btn_box = QHBoxLayout()
        self.btn_export_word = QPushButton("📄 XUẤT FILE WORD")
        self.btn_export_word.setObjectName("ExportBtn")
        self.btn_export_word.setFixedSize(180, 40)
        self.btn_export_word.clicked.connect(self.export_to_word)
        
        btn_close = QPushButton("Đóng")
        btn_close.setFixedSize(100, 40)
        btn_close.clicked.connect(self.close)
        
        btn_box.addStretch()
        btn_box.addWidget(self.btn_export_word)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

        self.calculate_stats()
    
    def keyPressEvent(self, event):
        #Xử lý bôi đen rồi Ctrl+C để copy từ bảng (cho báo cáo)
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
            table = self.focusWidget()
            if isinstance(table, QTableWidget):
                selected_ranges = table.selectedRanges()
                if not selected_ranges:
                    return

                text = ""
                for r_range in selected_ranges:
                    for r in range(r_range.topRow(), r_range.bottomRow() + 1):
                        row_data = []
                        for c in range(r_range.leftColumn(), r_range.rightColumn() + 1):
                            item = table.item(r, c)
                            row_data.append(item.text() if item else "")
                        text += "\t".join(row_data) + "\n"
                
                QGuiApplication.clipboard().setText(text)
        else:
            super().keyPressEvent(event)

    def count_weekends_in_month(self, year, month):
        count = 0
        num_days = calendar.monthrange(year, month)[1]
        for day in range(1, num_days + 1):
            # 5 là Thứ 7, 6 là Chủ nhật trong thư viện calendar
            if calendar.weekday(year, month, day) in [5, 6]:
                count += 1
        return count
    
    def calculate_stats(self):
        d1 = self.start_date.date().toString("yyyy-MM-dd")
        d2 = self.end_date.date().toString("yyyy-MM-dd")
        cursor = self.db_conn.cursor()
        
        classes = ["Sáng T7", "Chiều T7", "Sáng CN", "Chiều CN"]
        
        # 1. Xử lý Bảng Tóm Tắt
        self.summary_table.setRowCount(0)
        for class_name in classes:
            # Sĩ số: Lấy số lượng học sinh duy nhất của lớp đó
            cursor.execute("SELECT COUNT(DISTINCT name) FROM progress WHERE class_name = ?", (class_name,))
            total = cursor.fetchone()[0] or 0
            
            # Số buổi đi học thực tế
            cursor.execute("SELECT COUNT(*) FROM progress WHERE class_name = ? AND status = 'Đi học' AND date BETWEEN ? AND ?", 
                           (class_name, d1, d2))
            present = cursor.fetchone()[0] or 0
            
            absent = total - present if total > present else 0
            percent = (present / total * 100) if total > 0 else 0

            row = self.summary_table.rowCount()
            self.summary_table.insertRow(row)
            self.summary_table.setItem(row, 0, QTableWidgetItem(class_name))
            self.summary_table.setItem(row, 1, QTableWidgetItem(str(total)))
            self.summary_table.setItem(row, 2, QTableWidgetItem(str(present)))
            self.summary_table.setItem(row, 3, QTableWidgetItem(str(absent)))
            self.summary_table.setItem(row, 4, QTableWidgetItem(f"{int(percent)}%"))

        # 2. Xử lý Bảng Chi Tiết
        self.detail_table.setRowCount(0)
        cursor.execute("""
            SELECT date, class_name, name, content 
            FROM progress 
            WHERE date BETWEEN ? AND ? 
            ORDER BY date DESC, class_name ASC
        """, (d1, d2))
        
        details = cursor.fetchall()
        for r_date, c_name, s_name, content in details:
            # Tách năm và tháng từ ngày
            year = int(r_date[:4])
            month = int(r_date[5:7])
            current_month_str = r_date[:7]  # Dạng "YYYY-MM"

            # A. Tính tổng số buổi có trong tháng (Các ngày T7, CN)
            total_weekends = self.count_weekends_in_month(year, month)
            
            # B. Tính số buổi học sinh này ĐÃ ĐI HỌC trong tháng đó
            cursor.execute("""
                SELECT COUNT(*) FROM progress 
                WHERE name = ? AND status = 'Đi học' AND date LIKE ?
            """, (s_name, f"{current_month_str}%"))
            attended = cursor.fetchone()[0] or 0
            
            attendance_ratio = f"{attended}/{total_weekends}"

            row = self.detail_table.rowCount()
            self.detail_table.insertRow(row)
            self.detail_table.setItem(row, 0, QTableWidgetItem(r_date))
            self.detail_table.setItem(row, 1, QTableWidgetItem(c_name))
            self.detail_table.setItem(row, 2, QTableWidgetItem(s_name))
            
            ratio_item = QTableWidgetItem(attendance_ratio)
            ratio_item.setTextAlignment(Qt.AlignCenter)
            
            # Đổi màu chữ: Nếu nghỉ quá 2 buổi thì hiện màu đỏ cảnh báo
            if total_weekends - attended >= 2:
                ratio_item.setForeground(QColor("#dc3545"))  # Đỏ
            else:
                ratio_item.setForeground(QColor("#28a745"))  # Xanh lá
                
            self.detail_table.setItem(row, 3, ratio_item)
            self.detail_table.setItem(row, 4, QTableWidgetItem(str(content)))

    def export_to_word(self):
        #Xuất báo cáo ra file Word
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Lưu báo cáo", 
            f"Bao_cao_hoc_tap_{QDate.currentDate().toString('ddMMyy')}.docx", 
            "Word Files (*.docx)"
        )
        if not path:
            return

        try:
            doc = Document()
            doc.add_heading('BÁO CÁO TÌNH HÌNH HỌC TẬP', 0)
            
            # Thông tin thời gian
            time_str = f"Từ ngày: {self.start_date.date().toString('dd/MM/yyyy')} đến ngày: {self.end_date.date().toString('dd/MM/yyyy')}"
            doc.add_paragraph(time_str)

            # 1. Bảng tóm tắt
            doc.add_heading('1. Thống kê chuyên cần theo lớp', level=1)
            table1 = doc.add_table(rows=1, cols=5)
            table1.style = 'Table Grid'
            hdr_cells = table1.rows[0].cells
            hdr_cells[0].text = 'Tên lớp'
            hdr_cells[1].text = 'Sĩ số'
            hdr_cells[2].text = 'Đi học'
            hdr_cells[3].text = 'Nghỉ học'
            hdr_cells[4].text = 'Tỉ lệ (%)'

            for r in range(self.summary_table.rowCount()):
                row_cells = table1.add_row().cells
                for c in range(5):
                    row_cells[c].text = self.summary_table.item(r, c).text()

            doc.add_paragraph("\n")

            # 2. Bảng chi tiết
            doc.add_heading('2. Chi tiết nội dung và nhận xét', level=1)
            table2 = doc.add_table(rows=1, cols=4)
            table2.style = 'Table Grid'
            hdr_cells2 = table2.rows[0].cells
            hdr_cells2[0].text = 'Ngày'
            hdr_cells2[1].text = 'Lớp'
            hdr_cells2[2].text = 'Học viên'
            hdr_cells2[3].text = 'Nhận xét'

            for r in range(self.detail_table.rowCount()):
                row_cells = table2.add_row().cells
                for c in range(4):
                    row_cells[c].text = self.detail_table.item(r, c).text()

            doc.save(path)
            QMessageBox.information(self, "Thành công", f"Đã xuất báo cáo tại:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất file: {str(e)}")
