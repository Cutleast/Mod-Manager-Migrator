# type: ignore
"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class ShadowOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.top_shadow_visible = False
        self.bottom_shadow_visible = True
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )  # Let clicks pass through
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)

    def update_shadows(self, top_visible, bottom_visible):
        self.top_shadow_visible = top_visible
        self.bottom_shadow_visible = bottom_visible
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient_height = 20
        width = self.width()

        # Draw top shadow if visible
        if self.top_shadow_visible:
            top_gradient = QLinearGradient(0, 0, 0, gradient_height)
            top_gradient.setColorAt(0.0, QColor(0, 0, 0, 80))
            top_gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.fillRect(0, 0, width, gradient_height, top_gradient)

        # Draw bottom shadow if visible
        if self.bottom_shadow_visible:
            bottom_gradient = QLinearGradient(
                0, self.height() - gradient_height, 0, self.height()
            )
            bottom_gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
            bottom_gradient.setColorAt(1.0, QColor(0, 0, 0, 80))
            painter.fillRect(
                0,
                self.height() - gradient_height,
                width,
                gradient_height,
                bottom_gradient,
            )

        painter.end()


class ShadowScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.overlay = ShadowOverlay(self.viewport())  # Overlay on top of the viewport
        self.verticalScrollBar().valueChanged.connect(self.update_overlay)
        self.update_overlay()  # Initial update

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.resize(self.viewport().size())  # Resize overlay with the viewport

    def update_overlay(self):
        scrollbar = self.verticalScrollBar()
        top_visible = scrollbar.value() > 0
        bottom_visible = scrollbar.value() < scrollbar.maximum()
        self.overlay.update_shadows(top_visible, bottom_visible)


# Example usage
class ExampleApp(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        scroll_area = ShadowScrollArea()
        content = QWidget()
        content_layout = QVBoxLayout(content)

        # Add a bunch of labels to make the area scrollable
        for i in range(50):
            content_layout.addWidget(QPushButton(f"Item {i + 1}"))

        scroll_area.setWidget(content)
        layout.addWidget(scroll_area)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = ExampleApp()
    window.resize(400, 600)
    window.show()
    sys.exit(app.exec())
