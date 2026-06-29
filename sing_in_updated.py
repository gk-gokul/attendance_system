import sys
import cv2
import os
import csv
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QListWidget,
    QPushButton, QLineEdit, QListWidgetItem, QHBoxLayout, QInputDialog, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QImage, QPixmap, QKeyEvent
from PyQt6.QtWidgets import QGraphicsOpacityEffect

# Load and format student names
STUDENT_FILE = "students.txt"
with open(STUDENT_FILE, "r", encoding="utf-8") as f:
    STUDENT_LIST = [
        ", ".join(reversed(line.strip().split(",", 1))).strip() if "," in line else line.strip()
        for line in f if line.strip()
    ]

PHOTO_DIR = "attendance_photos"
os.makedirs(PHOTO_DIR, exist_ok=True)
LOG_FILE = "attendance_log.csv"
ADMIN_PASSWORD = "admin123"

class AttendanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attendance Kiosk")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.showFullScreen()

        self.selected_name = None
        self.checked_in_names = set()
        self.cap = cv2.VideoCapture(0)
        for _ in range(10):
            self.cap.read()

        layout = QVBoxLayout()

        # Title
        self.label = QLabel("📋 Attendance Kiosk")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("Title")
        layout.addWidget(self.label)

        # Search bar
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search your name...")
        self.search.textChanged.connect(self.filter_names)
        layout.addWidget(self.search)

        # Name Lists
        self.lists_layout = QHBoxLayout()

        left_section = QVBoxLayout()
        left_header = QLabel("🔵 Not Checked In")
        left_header.setObjectName("Header")
        left_section.addWidget(left_header)

        self.left_list = QListWidget()
        self.left_list.addItems(sorted(STUDENT_LIST))
        self.left_list.itemClicked.connect(self.select_name)
        self.left_list.itemDoubleClicked.connect(self.double_click_check_in)
        left_section.addWidget(self.left_list)
        self.lists_layout.addLayout(left_section)

        right_section = QVBoxLayout()
        right_header = QLabel("✅ Checked In")
        right_header.setObjectName("Header")
        right_section.addWidget(right_header)

        self.right_list = QListWidget()
        self.right_list.setEnabled(False)
        right_section.addWidget(self.right_list)
        self.lists_layout.addLayout(right_section)

        layout.addLayout(self.lists_layout)

        # Camera
        self.video_label = QLabel()
        self.video_label.setFixedHeight(240)
        self.video_label.setObjectName("Video")
        layout.addWidget(self.video_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.check_in_button = QPushButton("✅ Check In")
        self.check_in_button.setEnabled(False)
        self.check_in_button.clicked.connect(self.check_in_from_selection)
        button_layout.addWidget(self.check_in_button)

        self.admin_button = QPushButton("🔒 Admin Exit")
        self.admin_button.clicked.connect(self.admin_exit)
        button_layout.addWidget(self.admin_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Apply Styles
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI';
                font-size: 16px;
                background-color: #eaf1f8;
            }
            QLabel#Title {
    font-size: 32px;
    font-weight: bold;
    color: #007BFF;  /* Solid color instead of gradient */
    padding: 12px;
}

            QLabel#Header {
                font-weight: bold;
                color: #2d3748;
                padding-left: 6px;
            }
           QLineEdit {
    padding: 10px;
    font-size: 16px;
    border: 1px solid #ccc;
    border-radius: 8px;
    background-color: #ffffff;
    color: black; 
}

            QListWidget {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid #ccc;
                border-radius: 12px;
                padding: 6px;
                color: #1a202c;
                font-size: 18px;
            }
            QListWidget::item:selected {
                background-color: #007BFF;
                color: white;
                border-radius: 6px;
                padding: 4px;
            }
            QLabel#Video {
                background-color: rgba(255, 255, 255, 0.3);
                border-radius: 12px;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)

        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_video)
        self.video_timer.start(100)
        self.left_list.setFocus()

    def filter_names(self, text):
        self.left_list.clear()
        for name in sorted(STUDENT_LIST):
            if text.lower() in name.lower() and name not in self.checked_in_names:
                self.left_list.addItem(name)

    def select_name(self, item: QListWidgetItem):
        self.selected_name = item.text()
        self.check_in_button.setEnabled(True)
        self.check_in_button.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")

    def double_click_check_in(self, item: QListWidgetItem):
        self.selected_name = item.text()
        self.check_in(item.text())

    def keyPressEvent(self, event: QKeyEvent):
        if self.left_list.hasFocus():
            key = event.key()
            current_row = self.left_list.currentRow()
            if key == Qt.Key.Key_Up:
                self.left_list.setCurrentRow(max(0, current_row - 1))
            elif key == Qt.Key.Key_Down:
                self.left_list.setCurrentRow(min(self.left_list.count() - 1, current_row + 1))
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                current_item = self.left_list.currentItem()
                if current_item:
                    self.check_in(current_item.text())
            elif key == Qt.Key.Key_Escape:
                self.admin_exit()

    def check_in_from_selection(self):
        current_item = self.left_list.currentItem()
        if current_item:
            self.check_in(current_item.text())

    def check_in(self, name):
        if not name or name in self.checked_in_names:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        person_dir = os.path.join(PHOTO_DIR, name.replace(' ', '_'))
        os.makedirs(person_dir, exist_ok=True)

        photo_filename = os.path.join(person_dir, f"{filename_time}.jpg")
        ret, frame = self.cap.read()
        if ret:
            cv2.imwrite(photo_filename, frame)

        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([name, timestamp, photo_filename])

        self.checked_in_names.add(name)
        self.left_list.clear()
        self.right_list.addItem(name)
        self.filter_names(self.search.text())

        self.show_notification(f"{name}, you have checked in at {timestamp}.")
        self.check_in_button.setEnabled(False)
        self.check_in_button.setStyleSheet("")  # Reset
        self.search.clear()
        self.selected_name = None

        if len(self.checked_in_names) == len(STUDENT_LIST):
            QTimer.singleShot(3000, self.close)

    def show_notification(self, message):
        notif = QLabel(message, self)
        notif.setStyleSheet("""
            background-color: #4CAF50;
            color: white;
            padding: 15px;
            font-size: 20px;
            border-radius: 10px;
            border: 1px solid #388E3C;
        """)
        notif.setAlignment(Qt.AlignmentFlag.AlignCenter)
        notif.setGeometry(self.width()//4, self.height()//2 - 30, self.width()//2, 60)
        notif.setParent(self)
        notif.show()

        effect = QGraphicsOpacityEffect()
        notif.setGraphicsEffect(effect)

        self._animation = QPropertyAnimation(effect, b"opacity")
        self._animation.setDuration(4000)
        self._animation.setStartValue(1.0)
        self._animation.setEndValue(0.0)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._animation.finished.connect(notif.deleteLater)
        self._animation.start()

    def update_video(self):
        ret, frame = self.cap.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image).scaled(
                self.video_label.width(), self.video_label.height(), Qt.AspectRatioMode.KeepAspectRatio
            )
            self.video_label.setPixmap(pixmap)

    def admin_exit(self):
        password, ok = QInputDialog.getText(self, "Admin Exit", "Enter admin password:", QLineEdit.EchoMode.Password)
        if ok and password == ADMIN_PASSWORD:
            self.close()

    def closeEvent(self, event):
        self.cap.release()
        self.video_timer.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AttendanceApp()
    window.show()
    sys.exit(app.exec())
