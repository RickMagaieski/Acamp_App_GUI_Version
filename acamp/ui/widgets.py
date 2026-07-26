"""Reusable widgets shared by the Phase 1 page shells."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .theme import DARK_GREEN, OLIVE, ORANGE


class SidebarButton(QPushButton):
    def __init__(self, icon_text: str, label: str, parent: QWidget | None = None):
        super().__init__(f"{icon_text}    {label}", parent)
        self.setObjectName("sidebarButton")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(50)


class PrimaryButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setObjectName("primaryButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)


class PageHeader(QWidget):
    def __init__(
        self,
        title: str,
        subtitle: str,
        icon_text: str,
        action: QPushButton | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        icon = QLabel(icon_text)
        icon.setObjectName("headerIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(64, 64)
        layout.addWidget(icon)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)
        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)
        layout.addLayout(text_layout, 1)

        if action is not None:
            layout.addWidget(action, 0, Qt.AlignmentFlag.AlignVCenter)


class Card(QFrame):
    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(20, 18, 20, 18)
        self.body.setSpacing(10)

        if title:
            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")
            title_label.setWordWrap(True)
            self.body.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("cardSubtitle")
            subtitle_label.setWordWrap(True)
            self.body.addWidget(subtitle_label)

    def add_placeholder(self, text: str = "Conteúdo disponível em uma próxima fase.") -> QLabel:
        label = QLabel(text)
        label.setObjectName("placeholderText")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        self.body.addWidget(label, 1)
        return label


class MetricCard(Card):
    def __init__(self, title: str, accent: str = OLIVE, parent: QWidget | None = None):
        super().__init__(title, parent=parent)
        self.setMinimumSize(150, 170)
        value = QLabel("—")
        value.setObjectName("metricValue")
        value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value.setStyleSheet(f"color: {accent};")
        self.body.addWidget(value, 1)


class PageScaffold(QScrollArea):
    def __init__(
        self,
        title: str,
        subtitle: str,
        icon_text: str,
        action: QPushButton | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("pageScroll")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.canvas = QWidget()
        self.canvas.setObjectName("pageCanvas")
        self.content = QVBoxLayout(self.canvas)
        self.content.setContentsMargins(30, 26, 30, 20)
        self.content.setSpacing(20)
        self.content.addWidget(PageHeader(title, subtitle, icon_text, action))

        separator = QFrame()
        separator.setObjectName("separator")
        self.content.addWidget(separator)
        self.setWidget(self.canvas)


class PlaceholderTable(Card):
    def __init__(self, columns: list[str], rows: int = 4, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.body.setSpacing(0)
        header = QHBoxLayout()
        header.setSpacing(1)
        for column in columns:
            label = QLabel(column.upper())
            label.setObjectName("tableHeader")
            header.addWidget(label, 1)
        self.body.addLayout(header)

        for _ in range(rows):
            row = QFrame()
            row.setFixedHeight(48)
            row.setStyleSheet("border-bottom: 1px solid #ebe8df;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 0, 10, 0)
            for _column in columns:
                marker = QLabel("—")
                marker.setObjectName("placeholderText")
                row_layout.addWidget(marker, 1)
            self.body.addWidget(row)


class ChartPlaceholder(QLabel):
    def __init__(self, text: str = "GRÁFICO", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setObjectName("chartPlaceholder")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(110, 110)


class CampLandscape(QWidget):
    """Small code-drawn landscape motif inspired by the reference footer."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumHeight(105)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming convention
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = self.width()
        height = self.height()

        back = QPainterPath()
        back.moveTo(0, height)
        back.lineTo(0, height * 0.63)
        back.cubicTo(width * 0.18, height * 0.25, width * 0.32, height * 0.75, width * 0.48, height * 0.48)
        back.cubicTo(width * 0.64, height * 0.2, width * 0.78, height * 0.72, width, height * 0.42)
        back.lineTo(width, height)
        back.closeSubpath()
        painter.fillPath(back, QColor("#c8c9b5"))

        front = QPainterPath()
        front.moveTo(0, height)
        front.lineTo(0, height * 0.78)
        front.cubicTo(width * 0.2, height * 0.5, width * 0.35, height, width * 0.55, height * 0.68)
        front.cubicTo(width * 0.75, height * 0.42, width * 0.86, height * 0.88, width, height * 0.64)
        front.lineTo(width, height)
        front.closeSubpath()
        painter.fillPath(front, QColor("#788765"))

        center_x = width * 0.52
        ground_y = height * 0.91
        painter.setPen(QPen(QColor(DARK_GREEN), 3))
        painter.setBrush(QColor(DARK_GREEN))
        tent = QPainterPath()
        tent.moveTo(center_x - 35, ground_y)
        tent.lineTo(center_x, height * 0.42)
        tent.lineTo(center_x + 38, ground_y)
        tent.closeSubpath()
        painter.drawPath(tent)
        painter.setBrush(QColor("#e8e5d8"))
        opening = QPainterPath()
        opening.moveTo(center_x - 4, ground_y)
        opening.lineTo(center_x, height * 0.52)
        opening.lineTo(center_x + 16, ground_y)
        opening.closeSubpath()
        painter.drawPath(opening)

        painter.setPen(QPen(QColor(ORANGE), 2))
        painter.drawLine(int(center_x), int(height * 0.42), int(center_x), int(height * 0.25))
        painter.drawLine(int(center_x), int(height * 0.25), int(center_x + 14), int(height * 0.3))

