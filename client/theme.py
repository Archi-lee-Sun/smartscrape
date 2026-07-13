"""Central design tokens and QSS for the SmartScrape desktop client."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication


# Primitive tokens live here so widgets never invent their own colors or sizing.
COLOR = {
    "space_950": "#08051d",
    "space_900": "#10082f",
    "space_800": "#211052",
    "space_700": "#382078",
    "panel": "#17113f",
    "panel_raised": "#24185c",
    "panel_hover": "#30206f",
    "text": "#fff8d8",
    "text_muted": "#c7bde8",
    "yellow": "#ffe45c",
    "yellow_light": "#fff3a0",
    "yellow_glow": "#ffd43b",
    "gold": "#e7a92f",
    "yellow_shadow": "#9f6818",
    "ink": "#171014",
    "green": "#15803d",
    "green_hover": "#1f9d4d",
    "red": "#b4232f",
    "red_hover": "#d23140",
    "cyan": "#62e4ff",
    "cyan_shadow": "#197a9a",
    "focus": "#ffffff",
    "disabled": "#645d7e",
    "border": "#7562b5",
    "error": "#ff8791",
    "star": "#ffffff",
}

SPACE = {"1": 4, "2": 8, "3": 12, "4": 16, "5": 20, "6": 24, "8": 32, "10": 40, "12": 48}
RADIUS = {"sm": 4, "md": 8, "lg": 14}
TYPE_SIZE = {"body": 15, "meta": 12, "cluster": 22, "button_hero": 38, "section": 44, "hero": 58}
LAYOUT = {"content_max": 820, "overlay_max": 840, "list_row_height": 80}
FONT_FAMILY = "monospace"


def configure_retro_font() -> str:
    """Load a known system mono font when Qt's platform plugin cannot discover it."""

    global FONT_FAMILY
    candidates = (
        Path("C:/Windows/Fonts/consola.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    )
    for path in candidates:
        if not path.exists():
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id >= 0:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                FONT_FAMILY = families[0]
                return FONT_FAMILY
    app = QApplication.instance()
    if app is not None:
        FONT_FAMILY = app.font().family()
    return FONT_FAMILY


def make_retro_font(pixel_size: int, weight: QFont.Weight = QFont.Weight.Bold) -> QFont:
    """Return the shared display/body font at a tokenized size."""

    font = QFont(FONT_FAMILY)
    font.setPixelSize(pixel_size)
    font.setWeight(weight)
    font.setStyleHint(QFont.StyleHint.Monospace)
    return font


def build_stylesheet() -> str:
    """Resolve semantic tokens into the single application QSS theme."""

    c = COLOR
    return f"""
    QWidget {{
        color: {c['text']};
        font-family: "{FONT_FAMILY}";
        font-size: {TYPE_SIZE['body']}px;
    }}
    QMainWindow, QStackedWidget {{ background: {c['space_950']}; }}
    QLabel#clusterTitle, QLabel#detailTitle {{
        color: {c['yellow_light']}; font-size: {TYPE_SIZE['cluster']}px; font-weight: 800;
    }}
    QLabel#detailSummary {{ color: {c['text']}; }}
    QLabel#completionSummary {{ color: {c['text']}; font-size: 17px; font-weight: 700; }}
    QLabel#vaultRowTitle {{ color: {c['yellow_light']}; font-size: 16px; font-weight: 800; }}
    QLabel#vaultRowDate {{ color: {c['cyan']}; font-size: {TYPE_SIZE['meta']}px; }}
    QLabel#muted, QLabel#statusText {{ color: {c['text_muted']}; }}
    QLabel#errorText {{ color: {c['error']}; font-weight: 700; }}
    QLabel#modeBadge {{
        color: {c['ink']}; background: {c['cyan']}; border-radius: {RADIUS['sm']}px;
        padding: {SPACE['1']}px {SPACE['2']}px; font-weight: 800;
    }}
    QFrame#retroPanel {{
        background: {c['panel']};
        border: 2px solid {c['border']};
        border-radius: {RADIUS['lg']}px;
    }}
    QFrame#completionPanel {{
        background: {c['space_900']};
        border: 3px solid {c['yellow']};
        border-radius: {RADIUS['lg']}px;
    }}
    QPushButton, QToolButton {{
        min-height: 28px;
        padding: {SPACE['2']}px {SPACE['4']}px;
        color: {c['text']};
        background: {c['panel_raised']};
        border: 2px solid {c['border']};
        border-radius: {RADIUS['md']}px;
        font-weight: 700;
    }}
    QPushButton:hover, QToolButton:hover {{ background: {c['panel_hover']}; }}
    QPushButton:pressed, QToolButton:pressed {{ border-color: {c['cyan']}; }}
    QPushButton:focus, QToolButton:focus, QLineEdit:focus, QListWidget:focus {{
        border: 2px solid {c['focus']};
    }}
    QPushButton:disabled, QToolButton:disabled {{
        color: {c['text_muted']}; background: {c['disabled']}; border-color: {c['disabled']};
    }}
    QPushButton#generateButton {{
        min-width: 390px; max-width: 390px;
        min-height: 116px; max-height: 116px;
        padding: 0; border: none; background: transparent;
    }}
    QPushButton#finishButton {{
        color: {c['ink']}; background: {c['yellow']}; border-color: {c['yellow_light']};
        min-height: 46px; font-size: 17px; font-weight: 900;
    }}
    QPushButton#finishButton:hover {{ background: {c['yellow_light']}; }}
    QPushButton#saveButton {{
        color: {c['yellow']}; background: {c['green']}; border-color: {c['yellow']};
        min-height: 42px; font-size: 16px;
    }}
    QPushButton#saveButton:hover {{ background: {c['green_hover']}; }}
    QPushButton#discardButton {{
        color: {c['yellow']}; background: {c['red']}; border-color: {c['yellow']};
        min-height: 42px; font-size: 16px;
    }}
    QPushButton#discardButton:hover {{ background: {c['red_hover']}; }}
    QLineEdit {{
        min-height: 34px; padding: {SPACE['2']}px {SPACE['3']}px;
        color: {c['text']}; background: {c['panel']};
        border: 2px solid {c['border']}; border-radius: {RADIUS['md']}px;
        selection-background-color: {c['space_700']};
    }}
    QListWidget {{
        color: {c['text']}; background: {c['panel']};
        border: 2px solid {c['border']}; border-radius: {RADIUS['md']}px;
        outline: none;
    }}
    QListWidget::item {{ padding: 0; border-bottom: 1px solid {c['space_700']}; }}
    QListWidget::item:hover {{ background: {c['panel_hover']}; }}
    QListWidget::item:selected {{
        color: {c['text']}; background: {c['panel_hover']}; border: 2px solid {c['cyan']};
    }}
    QProgressBar {{
        min-height: 18px; color: {c['text']}; background: {c['space_900']};
        border: 1px solid {c['border']}; border-radius: {RADIUS['sm']}px; text-align: center;
    }}
    QProgressBar::chunk {{ background: {c['cyan']}; }}
    QScrollArea {{ background: transparent; border: none; }}
    QScrollBar:vertical {{ background: {c['space_900']}; width: 14px; }}
    QScrollBar::handle:vertical {{ background: {c['border']}; min-height: 28px; border-radius: 6px; }}
    QStatusBar {{ color: {c['text_muted']}; background: {c['space_900']}; }}
    """
