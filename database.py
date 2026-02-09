import sqlite3
from datetime import datetime
import calendar

class Database:
    def __init__(self, db_name='hoc_tap.db'):
        self.conn = sqlite3.connect(db_name)
        self.init_db()

    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS progress (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date TEXT, name TEXT, class_name TEXT, 
                            status TEXT, content TEXT, is_highlighted INTEGER DEFAULT 0)''')
        
        # Bảng quản lý hồ sơ học sinh
        cursor.execute('''CREATE TABLE IF NOT EXISTS students (
                            student_id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            phone TEXT,
                            parent_name TEXT,
                            date_of_birth TEXT,
                            address TEXT,
                            notes TEXT,
                            class_name TEXT,
                            registration_date TEXT)''')
        self.conn.commit()

    def get_filtered_progress(self, name="", class_name="Tất cả lớp", date=None):
        cursor = self.conn.cursor()
        query = "SELECT * FROM progress WHERE name LIKE ?"
        params = [f"%{name}%"]
        
        if class_name != "Tất cả lớp":
            query += " AND class_name = ?"
            params.append(class_name)
        if date:
            query += " AND date = ?"
            params.append(date)

        query += " ORDER BY date DESC, id DESC"
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_distinct_student_names(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM progress")
        return [row[0] for row in cursor.fetchall()]

    def insert_entry(self, date, name, class_name, status, content, is_highlighted):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO progress (date, name, class_name, status, content, is_highlighted) VALUES (?,?,?,?,?,?)",
            (date, name, class_name, status, content, is_highlighted)
        )
        self.conn.commit()

    def update_entry(self, entry_id, date, name, class_name, status, content, is_highlighted):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE progress SET date=?, name=?, class_name=?, status=?, content=?, is_highlighted=? WHERE id=?",
            (date, name, class_name, status, content, is_highlighted, entry_id)
        )
        self.conn.commit()

    def get_entry_by_id(self, entry_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM progress WHERE id=?", (entry_id,))
        return cursor.fetchone()

    def delete_entries(self, id_list):
        cursor = self.conn.cursor()
        for row_id in id_list:
            cursor.execute("DELETE FROM progress WHERE id=?", (row_id,))
        self.conn.commit()

    def bulk_insert_attendance(self, selected_data):
        cursor = self.conn.cursor()
        for name, cls, chosen_date in selected_data:
            # Kiểm tra xem đã có bản ghi chưa
            cursor.execute("SELECT id FROM progress WHERE name = ? AND date = ?", (name, chosen_date))
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO progress (date, name, class_name, status, content, is_highlighted) VALUES (?,?,?,?,?,?)",
                    (chosen_date, name, cls, "Đi học", "(Chưa có nhận xét cuối buổi)", 0)
                )
        self.conn.commit()

    def update_entries_content(self, id_list, content):
        cursor = self.conn.cursor()
        for entry_id in id_list:
            cursor.execute(
                "UPDATE progress SET content=? WHERE id=?",
                (content, entry_id)
            )
        self.conn.commit()

    # =========================
    # QUẢN LÝ HỒ SƠ HỌC SINH
    # =========================
    
    def get_all_students(self):
        """Lấy danh sách tất cả học sinh"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM students ORDER BY student_id")
        return cursor.fetchall()
    
    def get_student_by_id(self, student_id):
        """Lấy thông tin học sinh theo ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
        return cursor.fetchone()
    
    def insert_student(self, student_id, name, phone, parent_name, date_of_birth, address, notes, class_name, registration_date):
        """Thêm học sinh mới"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO students (student_id, name, phone, parent_name, date_of_birth, address, notes, class_name, registration_date) VALUES (?,?,?,?,?,?,?,?,?)",
            (student_id, name, phone, parent_name, date_of_birth, address, notes, class_name, registration_date)
        )
        self.conn.commit()
    
    def update_student(self, student_id, name, phone, parent_name, date_of_birth, address, notes, class_name, registration_date):
        """Cập nhật thông tin học sinh"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE students SET name=?, phone=?, parent_name=?, date_of_birth=?, address=?, notes=?, class_name=?, registration_date=? WHERE student_id=?",
            (name, phone, parent_name, date_of_birth, address, notes, class_name, registration_date, student_id)
        )
        self.conn.commit()
    
    def delete_student(self, student_id):
        """Xóa học sinh"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM students WHERE student_id=?", (student_id,))
        self.conn.commit()
    
    def search_students(self, keyword=""):
        """Tìm kiếm học sinh theo tên hoặc ID"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM students WHERE student_id LIKE ? OR name LIKE ? ORDER BY student_id",
            (f"%{keyword}%", f"%{keyword}%")
        )
        return cursor.fetchall()
    
    def get_student_attendance_stats(self, student_id=None, name=None):
        """Thống kê số buổi học của học sinh"""
        cursor = self.conn.cursor()
        
        # Lấy tên học sinh từ ID nếu có
        if student_id and not name:
            cursor.execute("SELECT name FROM students WHERE student_id=?", (student_id,))
            result = cursor.fetchone()
            if result:
                name = result[0]
        
        if name:
            # Tổng số buổi đi học
            cursor.execute(
                "SELECT COUNT(*) FROM progress WHERE name=? AND status='Đi học'",
                (name,)
            )
            attended = cursor.fetchone()[0] or 0
            
            # Tổng số buổi nghỉ
            cursor.execute(
                "SELECT COUNT(*) FROM progress WHERE name=? AND status='Nghỉ học'",
                (name,)
            )
            absent = cursor.fetchone()[0] or 0
            
            return {
                'student_id': student_id,
                'name': name,
                'attended': attended,
                'absent': absent,
                'total': attended + absent
            }
        
        return None
    
    def count_expected_sessions(self, class_name, start_date_str, end_date_str):
        """
        Tính số buổi học dự kiến trong khoảng thời gian
        Dựa trên lịch học: Sáng T7, Chiều T7, Sáng CN, Chiều CN
        """
        # Ánh xạ tên lớp sang ngày trong tuần
        # calendar.weekday: 0=Monday, 1=Tuesday, ..., 5=Saturday, 6=Sunday
        class_schedule = {
            "Sáng T7": [5],      # Saturday
            "Chiều T7": [5],     # Saturday
            "Sáng CN": [6],      # Sunday
            "Chiều CN": [6]      # Sunday
        }
        
        if class_name not in class_schedule:
            return 0
        
        target_weekdays = class_schedule[class_name]
        
        # Parse dates
        from datetime import datetime, timedelta
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        # Đếm số buổi
        count = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in target_weekdays:
                count += 1
            current_date += timedelta(days=1)
        
        return count
    
    def get_all_students_with_attendance(self, start_date_str=None, end_date_str=None):
        """
        Lấy danh sách tất cả học sinh kèm thống kê số buổi học
        Tính số buổi dự kiến dựa trên lịch học, tính tất cả các lớp học sinh được ghi danh
        start_date_str, end_date_str format: "YYYY-MM-DD"
        """
        cursor = self.conn.cursor()
        
        # Nếu không cung cấp date range, lấy tất cả dữ liệu
        if not start_date_str or not end_date_str:
            cursor.execute("SELECT MIN(date), MAX(date) FROM progress")
            date_range = cursor.fetchone()
            if date_range and date_range[0]:
                start_date_str = date_range[0]
                end_date_str = date_range[1]
            else:
                return []
        
        cursor.execute("SELECT student_id, name, class_name FROM students ORDER BY student_id")
        students = cursor.fetchall()
        
        result = []
        for student_id, name, class_name in students:
            # Đếm số buổi đi học (Đi học)
            cursor.execute(
                "SELECT COUNT(*) FROM progress WHERE name=? AND status='Đi học' AND date BETWEEN ? AND ?",
                (name, start_date_str, end_date_str)
            )
            attended = cursor.fetchone()[0] or 0
            
            # LẤY TẤT CẢ các class_name mà học sinh được ghi danh trong khoảng thời gian
            cursor.execute(
                "SELECT DISTINCT class_name FROM progress WHERE name=? AND date BETWEEN ? AND ? ORDER BY class_name",
                (name, start_date_str, end_date_str)
            )
            classes_in_period = [row[0] for row in cursor.fetchall()]
            
            # Tính số buổi dự kiến dựa trên TẤT CẢ các lớp
            total_expected = 0
            if classes_in_period:
                for cls in classes_in_period:
                    total_expected += self.count_expected_sessions(cls, start_date_str, end_date_str)
            else:
                # Nếu không có records trong khoảng thời gian, dùng class_name dari students table
                total_expected = self.count_expected_sessions(class_name, start_date_str, end_date_str)
            
            # Số buổi nghỉ = số buổi dự kiến - số buổi đi học
            absent = max(0, total_expected - attended)
            
            # Hiển thị tất cả các lớp nếu học sinh học nhiều hơn 1 lớp
            display_class = ", ".join(classes_in_period) if classes_in_period else class_name
            
            result.append((student_id, name, display_class, attended, absent, total_expected))
        
        return result
    
    def get_students_without_profile(self):
        """Lấy danh sách học sinh từ bảng progress mà chưa có hồ sơ trong bảng students"""
        cursor = self.conn.cursor()
        # Lấy các tên học sinh từ progress nhưng chưa có trong students
        # Lấy class_name của lần ghi dữ liệu gần nhất
        cursor.execute("""
            SELECT p.name, p.class_name, COUNT(DISTINCT p.date) as attendance_count
            FROM progress p
            LEFT JOIN students s ON p.name = s.name
            WHERE s.name IS NULL
            GROUP BY p.name
            ORDER BY p.name
        """)
        result = []
        for row in cursor.fetchall():
            name, attendance_count = row[0], row[2]
            # Lấy class_name gần nhất (ORDER BY date DESC LIMIT 1)
            cursor.execute("SELECT class_name FROM progress WHERE name = ? ORDER BY date DESC LIMIT 1", (name,))
            class_row = cursor.fetchone()
            class_name = class_row[0] if class_row else ""
            result.append((name, class_name, attendance_count))
        return result