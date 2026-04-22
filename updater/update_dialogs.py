from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
)


def ask_update(message: str) -> bool:
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setWindowTitle("Обновление")
    msg.setText(f"{message}\n\nОбновить сейчас?")
    msg.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    msg.setDefaultButton(QMessageBox.StandardButton.Yes)
    msg.setWindowModality(Qt.WindowModality.ApplicationModal)
    msg.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

    reply = msg.exec()
    return reply == QMessageBox.StandardButton.Yes


class UpdateWindow(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Обновление MVideo Bidder")
        self.resize(700, 420)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        layout = QVBoxLayout(self)

        self.title_label = QLabel("Выполняется обновление программы...")
        self.status_label = QLabel("Подготовка...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_output)

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def set_progress(self, value: int) -> None:
        self.progress_bar.setValue(max(0, min(100, int(value))))

    def append_log(self, text: str) -> None:
        self.log_output.append(text)
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def show_update_window(app: QApplication) -> UpdateWindow:
    window = UpdateWindow()
    window.show()
    app.processEvents()
    return window