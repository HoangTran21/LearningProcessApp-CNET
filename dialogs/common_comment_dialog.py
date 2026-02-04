from PySide6.QtWidgets import QDialog, QVBoxLayout, QGroupBox, QFormLayout, QTextEdit, QPushButton, QMessageBox
from PySide6.QtGui import QIcon


class CommonCommentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nhận xét chung")
        self.setFixedWidth(500)
        self.setWindowIcon(QIcon("logo_app.png"))

        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QGroupBox {
                font-weight: bold; border: 1px solid #d1d1d1;
                border-radius: 8px; background-color: #ffffff;
                margin-top: 25px;
            }
            QTextEdit {
                border: 1px solid #ccc; border-radius: 4px; padding: 8px; background-color: white;
            }
        """)

        layout = QVBoxLayout(self)
        form_group = QGroupBox("Nhận xét chung cho nhiều học sinh")
        form_layout = QFormLayout(form_group)
        form_layout.setContentsMargins(10, 25, 10, 10)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Nhập nhận xét chung...")
        self.content_edit.setMinimumHeight(150)

        form_layout.addRow("Nội dung:", self.content_edit)
        layout.addWidget(form_group)

        self.btn_save = QPushButton("LƯU NHẬN XÉT")
        self.btn_save.setFixedHeight(40)
        self.btn_save.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_save.clicked.connect(self.validate_and_accept)
        layout.addWidget(self.btn_save)

    def validate_and_accept(self):
        if not self.content_edit.toPlainText().strip():
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập nhận xét chung!")
            return
        self.accept()

    def get_content(self):
        return self.content_edit.toPlainText().strip()
