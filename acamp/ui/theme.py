"""Central visual tokens and Qt stylesheet for the GUI shell."""

from __future__ import annotations

DARK_GREEN = "#1f3928"
DEEP_GREEN = "#182f22"
OLIVE = "#64784a"
OLIVE_LIGHT = "#89996e"
CREAM = "#f4f1e8"
PANEL = "#faf8f2"
CARD = "#fffdf8"
TEXT = "#172019"
MUTED = "#667067"
ORANGE = "#d55a17"
BORDER = "#ddd9cd"

APP_STYLESHEET = f"""
* {{
    font-family: "Segoe UI", "Arial";
    color: {TEXT};
}}

QMainWindow, QWidget#applicationRoot {{
    background: {DEEP_GREEN};
}}

QWidget#sidebar {{
    background: {DARK_GREEN};
}}

QWidget#contentPanel {{
    background: {CREAM};
    border-top-left-radius: 24px;
    border-bottom-left-radius: 24px;
}}

QLabel#brandTitle {{
    color: white;
    font-size: 30px;
    font-weight: 800;
}}

QLabel#brandYear {{
    color: {ORANGE};
    font-size: 20px;
    font-weight: 700;
}}

QLabel#brandTagline, QLabel#sidebarFooter {{
    color: #d7ddcf;
    font-size: 12px;
}}

QPushButton#sidebarButton {{
    background: transparent;
    border: none;
    border-radius: 12px;
    color: #eef1e9;
    font-size: 15px;
    text-align: left;
    padding: 14px 18px;
}}

QPushButton#sidebarButton:hover {{
    background: rgba(255, 255, 255, 0.08);
}}

QPushButton#sidebarButton:checked {{
    background: {OLIVE};
    color: white;
    font-weight: 600;
}}

QScrollArea#pageScroll {{
    background: transparent;
    border: none;
}}

QWidget#pageCanvas {{
    background: transparent;
}}

QLabel#headerIcon {{
    background: {DARK_GREEN};
    border-radius: 12px;
    color: white;
    font-size: 26px;
    font-weight: 700;
}}

QLabel#pageTitle {{
    color: {TEXT};
    font-size: 31px;
    font-weight: 750;
}}

QLabel#pageSubtitle {{
    color: {MUTED};
    font-size: 14px;
}}

QFrame#separator {{
    background: {BORDER};
    border: none;
    min-height: 1px;
    max-height: 1px;
}}

QFrame#card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 16px;
}}

QLabel#cardTitle {{
    color: {TEXT};
    font-size: 15px;
    font-weight: 700;
}}

QLabel#cardSubtitle, QLabel#placeholderText {{
    color: {MUTED};
    font-size: 13px;
}}

QLabel#metricValue {{
    color: {OLIVE};
    font-size: 30px;
    font-weight: 700;
}}

QPushButton#primaryButton {{
    background: {DARK_GREEN};
    border: none;
    border-radius: 9px;
    color: white;
    font-size: 14px;
    font-weight: 600;
    padding: 10px 18px;
}}

QPushButton#primaryButton:hover {{
    background: {OLIVE};
}}

QPushButton#primaryButton:pressed {{
    background: {DEEP_GREEN};
}}

QPushButton#primaryButton:disabled {{
    background: #a7ad9f;
    color: #f0f0ec;
}}

QLineEdit#placeholderSearch {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    color: {MUTED};
    font-size: 14px;
    padding: 11px 14px;
}}

QLabel#tableHeader {{
    background: #eeece4;
    color: {TEXT};
    font-size: 12px;
    font-weight: 700;
    padding: 10px;
}}

QLabel#chartPlaceholder {{
    background: #f1efe7;
    border: 2px dashed #c8c6bb;
    border-radius: 42px;
    color: {OLIVE};
    font-size: 12px;
    font-weight: 600;
}}

QTableView#participantTable {{
    background: {CARD};
    alternate-background-color: {CARD};
    border: none;
    border-radius: 16px;
    color: {TEXT};
    font-size: 13px;
    selection-background-color: #edf0e5;
}}

QTableView#inventoryTable {{
    background: {CARD};
    border: none;
    border-radius: 16px;
    color: {TEXT};
    font-size: 13px;
    selection-background-color: #edf0e5;
}}

QTableView#paymentTable {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    color: {TEXT};
    font-size: 13px;
}}

QTableView#teamTable,
QTableView#teamMemberTable,
QTableView#teamRankingTable {{
    background: {CARD};
    border: none;
    border-radius: 16px;
    color: {TEXT};
    font-size: 13px;
    selection-background-color: #e4ead8;
}}

QTableView#teamTable::item,
QTableView#teamMemberTable::item,
QTableView#teamRankingTable::item {{
    border-bottom: 1px solid #ebe8df;
    padding: 6px 10px;
}}

QTableView#paymentTable::item {{
    border-bottom: 1px solid #ebe8df;
    padding: 6px 10px;
}}

QTableView#inventoryTable::item {{
    border-bottom: 1px solid #ebe8df;
    padding: 6px 10px;
}}

QTableView#participantTable::item {{
    border-bottom: 1px solid #ebe8df;
    padding: 6px 10px;
}}

QHeaderView::section {{
    background: #eeece4;
    border: none;
    border-bottom: 1px solid {BORDER};
    color: {TEXT};
    font-size: 12px;
    font-weight: 700;
    padding: 10px 8px;
}}

QLabel#participantState {{
    color: {MUTED};
    font-size: 15px;
    padding: 30px;
}}

QLabel#inventoryState {{
    color: {MUTED};
    font-size: 15px;
    padding: 30px;
}}

QLabel#participantTotal {{
    color: {MUTED};
    font-size: 14px;
    font-weight: 600;
}}

QLabel#inventoryTotal {{
    color: {MUTED};
    font-size: 14px;
    font-weight: 600;
}}

QLabel#inventoryError, QLabel#dialogError {{
    background: #fff0e9;
    border: 1px solid #e8a17e;
    border-radius: 8px;
    color: #a83d15;
    font-size: 13px;
    padding: 9px 12px;
}}

QLabel#financeWarning {{
    background: #fff6dc;
    border: 1px solid #e5bd63;
    border-radius: 9px;
    color: #795813;
    font-size: 13px;
    padding: 10px 13px;
}}

QLabel#teamError {{
    background: #fff0e9;
    border: 1px solid #e8a17e;
    border-radius: 8px;
    color: #a83d15;
    font-size: 13px;
    padding: 9px 12px;
}}

QLabel#teamState {{
    color: {MUTED};
    font-size: 15px;
    padding: 30px;
}}

QLabel#teamSelection {{
    color: {DARK_GREEN};
    font-size: 14px;
    font-weight: 600;
}}

QLabel#selectedTeamName {{
    color: {DARK_GREEN};
    font-size: 20px;
    font-weight: 700;
}}

QLabel#selectedTeamScore {{
    color: {ORANGE};
    font-size: 18px;
    font-weight: 700;
}}

QLabel#teamTotal {{
    color: {MUTED};
    font-size: 14px;
    font-weight: 600;
}}

QWidget#financeValueRow {{
    border-bottom: 1px solid #ebe8df;
}}

QLabel#financeLabel {{
    color: {TEXT};
    font-size: 13px;
}}

QLabel#financeValue {{
    color: {OLIVE};
    font-size: 14px;
    font-weight: 700;
}}

QLabel#financeEmptyState {{
    color: {MUTED};
    font-size: 15px;
}}

QDialog#inventoryDialog {{
    background: {CREAM};
}}

QDialog#paymentDialog {{
    background: {CREAM};
}}

QDialog#teamDialog {{
    background: {CREAM};
}}

QDialog#inventoryDialog QLineEdit,
QDialog#inventoryDialog QSpinBox,
QDialog#inventoryDialog QTextEdit,
QDialog#teamDialog QLineEdit {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 8px;
}}

QLabel#dialogTitle {{
    color: {TEXT};
    font-size: 21px;
    font-weight: 700;
}}

QLabel#pageInformation {{
    color: {MUTED};
    font-size: 13px;
    min-width: 100px;
}}

QPushButton#paginationButton {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    color: {DARK_GREEN};
    font-size: 20px;
    font-weight: 600;
    min-width: 40px;
    min-height: 38px;
}}

QPushButton#paginationButton:hover {{
    background: #eeece4;
}}

QPushButton#paginationButton:disabled {{
    color: #b9bbb5;
    background: #efede7;
}}
"""
