"""Central visual tokens and Qt stylesheet for the GUI shell."""

from __future__ import annotations

DARK_GREEN = "#29412f"
DEEP_GREEN = "#203628"
OLIVE = "#718052"
OLIVE_LIGHT = "#929c76"
CREAM = "#eeece3"
PANEL = "#f5f2ea"
CARD = "#fbfaf5"
TEXT = "#172019"
MUTED = "#59645b"
ORANGE = "#d95b12"
BORDER = "#d5d2c7"
CHART_COLORS = (
    "#64784a",
    "#d55a17",
    "#89996e",
    "#b9975b",
    "#315b40",
    "#c4774e",
    "#9a9f91",
)

APP_STYLESHEET = f"""
* {{
    font-family: "Segoe UI", "Arial";
    color: {TEXT};
}}

QMainWindow, QWidget#applicationRoot {{
    background: {DEEP_GREEN};
}}

QWidget#sidebar {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #243a2a,
        stop:0.55 #2b4431,
        stop:1 #1f3526
    );
}}

QWidget#contentPanel {{
    background: {CREAM};
    border-top-left-radius: 22px;
    border-bottom-left-radius: 22px;
}}

QLabel#brandTitle {{
    color: white;
    font-size: 36px;
    font-weight: 800;
}}

QLabel#brandYear {{
    color: white;
    font-size: 21px;
    font-weight: 700;
}}

QLabel#brandTagline {{
    color: #eef0e8;
    font-size: 11px;
    letter-spacing: 1px;
}}

QPushButton#sidebarButton {{
    background: transparent;
    border: none;
    border-radius: 11px;
    color: #f2f2eb;
    font-size: 16px;
    text-align: left;
    padding: 12px 17px;
}}

QPushButton#sidebarButton:hover {{
    background: rgba(255, 255, 255, 0.08);
}}

QPushButton#sidebarButton:checked {{
    background: rgba(151, 161, 112, 0.62);
    color: white;
    font-weight: 500;
}}

QFrame#sidebarFooterCard {{
    background: #f3efe5;
    border: 1px solid #d6d0c2;
    border-radius: 14px;
}}

QLabel#sidebarHelp {{
    border: 1px solid {DARK_GREEN};
    border-radius: 13px;
    color: {DARK_GREEN};
    font-size: 16px;
    font-weight: 600;
}}

QLabel#sidebarFooterText {{
    color: #29342c;
    font-size: 13px;
    line-height: 1.45;
}}

QLabel#sidebarHeart {{
    color: {ORANGE};
    font-size: 22px;
}}

QScrollArea#pageScroll {{
    background: transparent;
    border: none;
}}

QWidget#pageCanvas {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #f4f2e9,
        stop:0.55 #eeece3,
        stop:1 #f5f2ea
    );
}}

QLabel#headerIcon {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #243d2a,
        stop:1 #718052
    );
    border-radius: 12px;
}}

QLabel#pageTitle {{
    color: #17251b;
    font-size: 34px;
    font-weight: 700;
}}

QLabel#pageSubtitle {{
    color: #39453c;
    font-size: 14px;
}}

QFrame#separator {{
    background: {BORDER};
    border: none;
    min-height: 1px;
    max-height: 1px;
}}

QFrame#card,
QFrame#heroCard {{
    background: rgba(253, 252, 248, 0.92);
    border: 1px solid #d3d0c4;
    border-radius: 15px;
}}

QFrame#card[clickable="true"]:hover {{
    border: 1px solid {OLIVE_LIGHT};
    background: #f9f8f1;
}}

QLabel#cardTitle {{
    color: #223525;
    font-size: 16px;
    font-weight: 650;
}}

QLabel#cardSubtitle {{
    color: #4f5a51;
    font-size: 12px;
}}

QLabel#sectionIcon {{
    background: #ecece2;
    border-radius: 22px;
}}

QLabel#metricValue {{
    color: {OLIVE};
    font-size: 31px;
    font-weight: 650;
}}

QLabel#metricIcon {{
    font-size: 22px;
    font-weight: 700;
}}

QLabel#metricDetails {{
    color: {MUTED};
    font-size: 11px;
}}

QPushButton#primaryButton {{
    background: {DARK_GREEN};
    border: 1px solid #1e3525;
    border-radius: 8px;
    color: white;
    font-size: 14px;
    font-weight: 500;
    padding: 10px 19px;
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

QPushButton#destructiveButton {{
    background: transparent;
    border: 1px solid {ORANGE};
    border-radius: 8px;
    color: {ORANGE};
    font-weight: 600;
    padding: 7px 18px;
}}

QPushButton#destructiveButton:hover {{
    background: #fff0e7;
}}

QPushButton#orangeButton,
QPushButton#searchButton {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #cf4d10,
        stop:1 #e46b17
    );
    border: 1px solid #c94e12;
    border-radius: 8px;
    color: white;
    font-size: 14px;
    font-weight: 550;
    padding: 10px 20px;
}}

QPushButton#orangeButton:hover,
QPushButton#searchButton:hover {{
    background: #c94f14;
}}

QPushButton#syncButton {{
    background: rgba(252, 251, 247, 0.86);
    border: 1px solid #cbc8bd;
    border-radius: 10px;
    color: {DARK_GREEN};
    font-size: 14px;
    font-weight: 550;
    padding: 12px 20px;
}}

QPushButton#syncButton:hover {{
    background: white;
    border-color: {OLIVE};
}}

QLabel#welcomeIcon {{
    background: #ecebe2;
    border-radius: 27px;
    color: {DARK_GREEN};
    font-size: 34px;
}}

QPushButton#secondaryButton {{
    background: transparent;
    border: 1px solid {OLIVE};
    border-radius: 8px;
    color: {DARK_GREEN};
    padding: 9px 14px;
}}

QPushButton#quietButton {{
    background: transparent;
    border: none;
    color: {MUTED};
    padding: 9px 12px;
}}

QLineEdit#placeholderSearch {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    color: {TEXT};
    font-size: 15px;
    padding: 12px 16px;
}}

QLineEdit#placeholderSearch:focus {{
    border: 1px solid {OLIVE};
}}

QTableView#participantTable {{
    background: {CARD};
    alternate-background-color: {CARD};
    border: 1px solid #d7d4c9;
    border-radius: 13px;
    color: {TEXT};
    font-size: 13px;
    selection-background-color: #edf0e5;
}}

QTableView#inventoryTable {{
    background: {CARD};
    border: 1px solid #d7d4c9;
    border-radius: 13px;
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
    border: 1px solid #d7d4c9;
    border-radius: 13px;
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
    background: #e5e4da;
    border: none;
    border-bottom: 1px solid {BORDER};
    color: {TEXT};
    font-size: 12px;
    font-weight: 600;
    padding: 11px 8px;
}}

QLabel#participantState {{
    color: {MUTED};
    font-size: 15px;
    padding: 30px;
}}

QLabel#participantOperationStatus {{
    background: #eef2e8;
    border: 1px solid #bdc9ac;
    border-radius: 9px;
    color: {DARK_GREEN};
    font-size: 13px;
    font-weight: 600;
    padding: 10px 13px;
}}

QLabel#participantCacheWarning {{
    background: #fff0e9;
    border: 1px solid #e8a17e;
    border-radius: 9px;
    color: #8d3514;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 13px;
}}

QLabel#inventoryState {{
    color: {MUTED};
    font-size: 15px;
    padding: 30px;
}}

QLabel#participantTotal {{
    color: {DARK_GREEN};
    font-size: 15px;
    font-weight: 550;
}}

QLabel#inventoryTotal {{
    background: #e8e7dd;
    border-radius: 9px;
    color: {DARK_GREEN};
    font-size: 14px;
    font-weight: 550;
    padding: 10px 14px;
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

QLabel#dashboardWarning {{
    background: #fff6dc;
    border: 1px solid #e5bd63;
    border-radius: 9px;
    color: #795813;
    font-size: 13px;
    padding: 10px 13px;
}}

QLabel#dashboardSyncStatus {{
    color: {MUTED};
    font-size: 10px;
}}

QWidget#dashboardSummaryRow {{
    border-bottom: 1px solid #ebe8df;
}}

QLabel#dashboardSummaryLabel {{
    color: {TEXT};
    font-size: 13px;
}}

QLabel#dashboardSummaryValue {{
    color: {OLIVE};
    font-size: 14px;
    font-weight: 700;
}}

QLabel#dashboardTeamLeader {{
    color: {DARK_GREEN};
    font-size: 20px;
    font-weight: 700;
}}

QLabel#dashboardTeamScore {{
    color: {ORANGE};
    font-size: 16px;
    font-weight: 700;
}}

QLabel#dashboardRankingPreview {{
    color: {MUTED};
    font-size: 13px;
    line-height: 1.4;
}}

QLabel#dashboardWelcomeTitle {{
    color: {TEXT};
    font-size: 27px;
    font-weight: 650;
}}

QLabel#reportWarning {{
    background: #fff6dc;
    border: 1px solid #e5bd63;
    border-radius: 9px;
    color: #795813;
    font-size: 13px;
    padding: 10px 13px;
}}

QLabel#reportTotal {{
    color: {DARK_GREEN};
    font-size: 34px;
    font-weight: 750;
}}

QLabel#reportTotalCaption,
QLabel#reportEmptyState,
QLabel#reportRanking {{
    color: {MUTED};
    font-size: 13px;
}}

QLabel#reportFinanceLabel {{
    color: {TEXT};
    font-size: 13px;
}}

QLabel#reportFinanceValue {{
    color: {OLIVE};
    font-size: 16px;
    font-weight: 700;
}}

QFrame#reportMetric {{
    background: #f3f1e8;
    border: 1px solid #e3dfd3;
    border-radius: 11px;
}}

QGraphicsView#reportChart {{
    background: transparent;
    border: none;
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

QLabel#pageInformation {{
    background: {ORANGE};
    border-radius: 7px;
    color: white;
    font-size: 14px;
    font-weight: 600;
    min-width: 88px;
    padding: 9px 12px;
}}

QDialog#dataSetupDialog {{
    background: {CREAM};
}}

QLabel#setupTitle {{
    color: {DARK_GREEN};
    font-size: 25px;
    font-weight: 700;
}}

QLabel#setupIntroduction,
QLabel#setupChoiceBody,
QLabel#setupStatus {{
    color: {MUTED};
    font-size: 13px;
}}

QFrame#setupChoiceCard {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 13px;
}}

QLabel#setupChoiceTitle,
QLabel#setupStatusTitle {{
    color: {DARK_GREEN};
    font-size: 15px;
    font-weight: 650;
}}

QFrame#setupStatusPanel {{
    background: #e8eadf;
    border: 1px solid #c9cfb9;
    border-radius: 11px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background: #b7b9a9;
    border-radius: 4px;
    min-height: 32px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""
