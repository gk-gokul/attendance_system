import sys
import cv2
import os
import csv
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QListWidget,
    QPushButton, QLineEdit, QListWidgetItem, QHBoxLayout, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QKeyEvent

# Load student names from file
STUDENT_FILE = "students.txt"
with open(STUDENT_FILE, "r", encoding="utf-8") as f:
    STUDENT_LIST = [line.strip() for line in f if line.strip()]

PHOTO_DIR = "attendance_photos"
os.makedirs(PHOTO_DIR, exist_ok=True)

# Generate log filename with timestamp
# log_time = datetime.now().strftime("%Y%m%d_%H%M%S")
# LOG_FILE = f"attendance_log_{log_time}.csv"
LOG_FILE = f"attendance_log.csv"

ADMIN_PASSWORD = "admin123"  # Change this to your desired password

class AttendanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attendance Kiosk")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.showFullScreen()

        self.selected_name = None
        self.checked_in_names = set()

        # Keep camera open
        self.cap = cv2.VideoCapture(0)
        for _ in range(10):
            self.cap.read()

        layout = QVBoxLayout()

        self.label = QLabel("Select Your Name")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search your name...")
        self.search.textChanged.connect(self.filter_names)
        layout.addWidget(self.search)

        self.lists_layout = QHBoxLayout()

        # Left: Not signed-in
        self.left_list = QListWidget()
        self.left_list.addItems(sorted(STUDENT_LIST))
        self.left_list.itemClicked.connect(self.select_name)
        self.left_list.itemDoubleClicked.connect(self.double_click_check_in)
        self.lists_layout.addWidget(self.left_list)

        # Right: Signed-in
        self.right_list = QListWidget()
        self.right_list.setEnabled(False)
        self.lists_layout.addWidget(self.right_list)

        layout.addLayout(self.lists_layout)

        self.video_label = QLabel()
        self.video_label.setFixedHeight(240)
        layout.addWidget(self.video_label)

        button_layout = QHBoxLayout()

        self.check_in_button = QPushButton("Check In")
        self.check_in_button.setEnabled(False)
        self.check_in_button.clicked.connect(self.check_in_from_selection)
        button_layout.addWidget(self.check_in_button)

        self.admin_button = QPushButton("Admin Exit")
        self.admin_button.clicked.connect(self.admin_exit)
        button_layout.addWidget(self.admin_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Timer to update video
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
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
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

        # Create personal folder
        person_dir = os.path.join(PHOTO_DIR, name.replace(' ', '_'))
        os.makedirs(person_dir, exist_ok=True)

        photo_filename = os.path.join(person_dir, f"{filename_time}.jpg")

        ret, frame = self.cap.read()
        if ret:
            cv2.imwrite(photo_filename, frame)

        # Log to CSV
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([name, timestamp, photo_filename])

        self.checked_in_names.add(name)
        self.left_list.clear()
        self.right_list.addItem(name)
        self.filter_names(self.search.text())

        self.show_notification(f"{name}, you have checked in at {timestamp}.")

        self.check_in_button.setEnabled(False)
        self.search.clear()
        self.selected_name = None

        if len(self.checked_in_names) == len(STUDENT_LIST):
            QTimer.singleShot(3000, self.close)

    def show_notification(self, message):
        notif = QLabel(message, self)
        notif.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-size: 18px;")
        notif.setAlignment(Qt.AlignmentFlag.AlignCenter)
        notif.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        notif.setGeometry(self.width()//4, self.height()//2, self.width()//2, 60)
        notif.show()
        QTimer.singleShot(2000, notif.deleteLater)

    def update_video(self):
        ret, frame = self.cap.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image).scaled(self.video_label.width(), self.video_label.height(), Qt.AspectRatioMode.KeepAspectRatio)
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
