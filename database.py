import sqlite3

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