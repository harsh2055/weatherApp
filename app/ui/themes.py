"""
Application theme definitions — dark and light modes.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Theme:
    name: str
    bg_primary: str
    bg_secondary: str
    bg_card: str
    bg_input: str
    text_primary: str
    text_secondary: str
    text_muted: str
    accent: str
    accent_hover: str
    border: str
    success: str
    warning: str
    error: str
    gradient_start: str
    gradient_end: str


DARK_THEME = Theme(
    name="dark",
    bg_primary="#0f1117",
    bg_secondary="#1a1d2e",
    bg_card="#1e2235",
    bg_input="#252840",
    text_primary="#f0f4ff",
    text_secondary="#b0b8d4",
    text_muted="#6b7494",
    accent="#4f8ef7",
    accent_hover="#6fa3ff",
    border="#2d3254",
    success="#2ecc71",
    warning="#f1c40f",
    error="#e74c3c",
    gradient_start="#1a1d2e",
    gradient_end="#0f1117",
)

LIGHT_THEME = Theme(
    name="light",
    bg_primary="#f0f4f8",
    bg_secondary="#e2eaf4",
    bg_card="#ffffff",
    bg_input="#f5f7fb",
    text_primary="#1a2340",
    text_secondary="#3d5070",
    text_muted="#8a9bc0",
    accent="#2563eb",
    accent_hover="#1d4ed8",
    border="#c8d4e8",
    success="#16a34a",
    warning="#d97706",
    error="#dc2626",
    gradient_start="#e2eaf4",
    gradient_end="#f0f4f8",
)

THEMES = {"dark": DARK_THEME, "light": LIGHT_THEME}


def get_stylesheet(theme: Theme) -> str:
    t = theme
    return f"""
    QMainWindow, QDialog {{
        background-color: {t.bg_primary};
    }}
    QWidget#central_widget {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {t.gradient_start},
            stop:1 {t.gradient_end}
        );
    }}
    QWidget {{
        color: {t.text_primary};
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
    }}
    /* Cards */
    QFrame#weather_card, QFrame#forecast_card, QFrame#info_card {{
        background-color: {t.bg_card};
        border: 1px solid {t.border};
        border-radius: 12px;
        padding: 16px;
    }}
    /* Input */
    QLineEdit {{
        background-color: {t.bg_input};
        border: 1.5px solid {t.border};
        border-radius: 8px;
        padding: 8px 14px;
        color: {t.text_primary};
        font-size: 14px;
    }}
    QLineEdit:focus {{
        border-color: {t.accent};
    }}
    /* Buttons */
    QPushButton {{
        background-color: {t.accent};
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 9px 20px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {t.accent_hover};
    }}
    QPushButton:pressed {{
        background-color: {t.accent};
        opacity: 0.85;
    }}
    QPushButton#secondary_btn {{
        background-color: transparent;
        color: {t.accent};
        border: 1.5px solid {t.accent};
    }}
    QPushButton#secondary_btn:hover {{
        background-color: {t.accent};
        color: #ffffff;
    }}
    QPushButton#icon_btn {{
        background-color: transparent;
        border: none;
        padding: 4px;
    }}
    /* Tabs */
    QTabWidget::pane {{
        background-color: {t.bg_secondary};
        border: 1px solid {t.border};
        border-radius: 8px;
    }}
    QTabBar::tab {{
        background-color: {t.bg_input};
        color: {t.text_secondary};
        padding: 8px 18px;
        border-radius: 6px 6px 0 0;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background-color: {t.accent};
        color: #ffffff;
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {t.border};
    }}
    /* Scroll bars */
    QScrollArea {{ background: transparent; border: none; }}
    QScrollBar:vertical {{
        background: {t.bg_secondary};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {t.border};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {t.accent}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    /* List widget */
    QListWidget {{
        background-color: {t.bg_card};
        border: 1px solid {t.border};
        border-radius: 8px;
    }}
    QListWidget::item {{ padding: 8px 12px; }}
    QListWidget::item:hover {{ background-color: {t.bg_input}; }}
    QListWidget::item:selected {{ background-color: {t.accent}; color: white; }}
    /* Combo box */
    QComboBox {{
        background-color: {t.bg_input};
        border: 1.5px solid {t.border};
        border-radius: 8px;
        padding: 6px 12px;
        color: {t.text_primary};
    }}
    QComboBox::drop-down {{ border: none; }}
    QComboBox QAbstractItemView {{
        background-color: {t.bg_card};
        selection-background-color: {t.accent};
        border: 1px solid {t.border};
    }}
    /* Status bar */
    QStatusBar {{
        background-color: {t.bg_secondary};
        color: {t.text_muted};
        font-size: 11px;
    }}
    /* Labels */
    QLabel#temp_label {{
        font-size: 64px;
        font-weight: 700;
        color: {t.text_primary};
    }}
    QLabel#city_label {{
        font-size: 22px;
        font-weight: 600;
        color: {t.text_primary};
    }}
    QLabel#condition_label {{
        font-size: 15px;
        color: {t.text_secondary};
    }}
    QLabel#stat_label {{
        font-size: 12px;
        color: {t.text_muted};
    }}
    QLabel#stat_value {{
        font-size: 14px;
        font-weight: 600;
        color: {t.text_primary};
    }}
    QLabel#section_title {{
        font-size: 14px;
        font-weight: 700;
        color: {t.text_secondary};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    /* Tooltip */
    QToolTip {{
        background-color: {t.bg_card};
        color: {t.text_primary};
        border: 1px solid {t.border};
        border-radius: 6px;
        padding: 6px;
    }}
    """
