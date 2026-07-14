"""SmartScrape PyQt6 client: generation hub, live pipeline, and vault."""

from __future__ import annotations

import html
import random
from typing import Any

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QAbstractButton,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QLayout,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from theme import COLOR, EXTRUSION, LAYOUT, SPACE, TYPE_SIZE, build_stylesheet, configure_retro_font, make_retro_font
from music import BackgroundMusicController
from workers import ApiWorker, PipelineWorker


class GalaxyWidget(QWidget):
    """Procedural, resolution-independent retro star field."""

    def paintEvent(self, event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(COLOR["space_800"]))
        gradient.setColorAt(0.55, QColor(COLOR["space_900"]))
        gradient.setColorAt(1.0, QColor(COLOR["space_950"]))
        painter.fillRect(self.rect(), gradient)

        rng = random.Random(2001)
        star_colors = [QColor(COLOR["star"]), QColor(COLOR["yellow"]), QColor(COLOR["cyan"])]
        for _ in range(max(70, (self.width() * self.height()) // 9000)):
            x = rng.randrange(max(1, self.width()))
            y = rng.randrange(max(1, self.height()))
            size = rng.choice((1, 1, 1, 2, 2, 3))
            color = rng.choice(star_colors)
            color.setAlpha(rng.randrange(100, 235))
            painter.fillRect(x, y, size, size, color)
            if size == 3:
                painter.fillRect(x - 2, y + 1, 7, 1, color)
                painter.fillRect(x + 1, y - 2, 1, 7, color)


def _draw_retro_text(
    painter: QPainter,
    rect: QRectF,
    text: str,
    pixel_size: int,
    offset: QPointF = QPointF(),
    glow_boost: int = 0,
    dark_outline: bool = True,
    core_color: str = "yellow_light",
) -> None:
    """Paint shared arcade-marquee text with bloom, outline, and extrusion."""

    font = make_retro_font(pixel_size, weight=QFont.Weight.Black)
    path = QPainterPath()
    path.addText(0, 0, font, text)
    bounds = path.boundingRect()
    path.translate(
        rect.center().x() - bounds.center().x() + offset.x(),
        rect.center().y() - bounds.center().y() + offset.y(),
    )

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for width, alpha in ((18, 28 + glow_boost), (12, 48 + glow_boost), (7, 86 + glow_boost)):
        glow = QColor(COLOR["yellow_glow"])
        glow.setAlpha(min(150, alpha))
        painter.setPen(QPen(glow, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)

    painter.setPen(Qt.PenStyle.NoPen)
    maximum_depth = 12
    for depth in range(maximum_depth, 0, -1):
        layer = QPainterPath(path)
        layer.translate(depth, depth)
        shade_index = round((depth - 1) / (maximum_depth - 1) * (len(EXTRUSION) - 1))
        painter.setBrush(QColor(EXTRUSION[shade_index]))
        painter.drawPath(layer)

    painter.setBrush(QColor(COLOR[core_color]))
    if dark_outline:
        painter.setPen(
            QPen(
                QColor(COLOR["ink"]),
                3,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
    else:
        painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPath(path)
    if dark_outline:
        highlight = QPainterPath(path)
        highlight.translate(-1, -1)
        shine = QColor(COLOR["star"])
        shine.setAlpha(190)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(shine, 1.25))
        painter.drawPath(highlight)
    painter.restore()


class RetroGlowLabel(QWidget):
    """Reusable title primitive shared by the Generation Hub and Vault."""

    def __init__(self, text: str, pixel_size: int, *, dark_outline: bool = True, core_color: str = "yellow_light") -> None:
        super().__init__()
        self.text = text
        self.pixel_size = pixel_size
        self.dark_outline = dark_outline
        self.core_color = core_color
        self.setAccessibleName(text)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def sizeHint(self) -> QSize:
        metrics = QFontMetrics(make_retro_font(self.pixel_size, QFont.Weight.Black))
        return QSize(metrics.horizontalAdvance(self.text) + 44, self.pixel_size + 46)

    def setText(self, text: str) -> None:
        self.text = text
        self.setAccessibleName(text)
        self.updateGeometry()
        self.update()

    def paintEvent(self, event: Any) -> None:
        painter = QPainter(self)
        _draw_retro_text(
            painter,
            QRectF(self.rect()).adjusted(12, 8, -12, -18),
            self.text,
            self.pixel_size,
            dark_outline=self.dark_outline,
            core_color=self.core_color,
        )


class RetroGenerateButton(QPushButton):
    """Large solid-yellow Generate control using the shared QSS bevel."""

    def __init__(self) -> None:
        super().__init__("Generate()")
        self.setObjectName("generateButton")
        self.setFixedSize(390, 116)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class AudioToggleButton(QAbstractButton):
    """Accessible session audio toggle rendered as a pixel-arcade control."""

    def __init__(self) -> None:
        super().__init__()
        self.setCheckable(True)
        self.setChecked(False)
        self.setFixedSize(QSize(54, 54))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Mute app audio")
        self.setAccessibleName("Mute app audio")
        self.toggled.connect(self._update_accessible_text)

    def _update_accessible_text(self, muted: bool) -> None:
        text = "Enable app audio" if muted else "Mute app audio"
        self.setToolTip(text)
        self.setAccessibleName(text)
        self.update()

    def paintEvent(self, event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        border = QColor(COLOR["focus"] if self.hasFocus() else COLOR["yellow"])
        painter.fillRect(1, 1, 52, 52, QColor(COLOR["yellow_shadow"]))
        painter.fillRect(1, 1, 48, 48, border)
        painter.fillRect(4, 4, 44, 44, QColor(COLOR["panel_hover"] if self.underMouse() else COLOR["panel_raised"]))
        painter.fillRect(7, 7, 38, 3, QColor(COLOR["cyan_shadow"]))

        painter.setPen(Qt.PenStyle.NoPen)
        shadow = QPolygonF(
            [QPointF(11, 23), QPointF(18, 23), QPointF(26, 16), QPointF(26, 39), QPointF(18, 32), QPointF(11, 32)]
        )
        painter.setBrush(QColor(COLOR["cyan_shadow"]))
        painter.drawPolygon(shadow)
        speaker = QPolygonF(
            [QPointF(10, 21), QPointF(17, 21), QPointF(25, 14), QPointF(25, 37), QPointF(17, 30), QPointF(10, 30)]
        )
        painter.setBrush(QColor(COLOR["yellow_light"]))
        painter.drawPolygon(speaker)

        # Stepped brackets read as sound waves while retaining a pixel-grid silhouette.
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(COLOR["yellow"]), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap))
        for x, top, bottom in ((29, 19, 33), (34, 15, 37), (39, 11, 41)):
            painter.drawLine(x, top, x + 3, top)
            painter.drawLine(x + 3, top, x + 3, bottom)
            painter.drawLine(x, bottom, x + 3, bottom)
        if self.isChecked():
            painter.setPen(QPen(QColor(COLOR["yellow_light"]), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap))
            painter.drawLine(QPointF(9, 9), QPointF(45, 45))
            painter.setPen(QPen(QColor(COLOR["red_hover"]), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap))
            painter.drawLine(QPointF(9, 9), QPointF(45, 45))


class GenerationOverlay(QFrame):
    save_requested = pyqtSignal(dict)
    cancel_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("retroPanel")
        self.clusters: list[dict[str, Any]] = []
        self.decisions: dict[int, str] = {}
        self.current_index = -1
        self.stream_complete = False
        self.stream_failed = False
        self.save_in_progress = False

        self.status_label = QLabel("Connecting to the pipeline...")
        self.status_label.setObjectName("statusText")
        self.status_label.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(True)

        self.title_label = QLabel("Waiting for the first story cluster...")
        self.title_label.setObjectName("clusterTitle")
        self.title_label.setWordWrap(True)
        self.mode_badge = QLabel("WAITING")
        self.mode_badge.setObjectName("modeBadge")
        self.mode_badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.summary_label = QLabel("Results will appear here live as the pipeline produces them.")
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        content = QWidget()
        content.setObjectName("clusterContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(SPACE["2"], SPACE["2"], SPACE["2"], SPACE["2"])
        content_layout.setSpacing(SPACE["3"])
        content_layout.addWidget(self.title_label)
        content_layout.addWidget(self.mode_badge, 0, Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(self.summary_label)
        content_layout.addStretch()
        scroll = QScrollArea()
        scroll.setObjectName("clusterScroll")
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        scroll.setMinimumHeight(180)

        self.previous_button = QPushButton("← Previous")
        self.previous_button.setAccessibleName("Show previous cluster")
        self.next_button = QPushButton("Next →")
        self.next_button.setAccessibleName("Show next cluster")
        self.previous_button.clicked.connect(lambda: self.show_index(self.current_index - 1))
        self.next_button.clicked.connect(lambda: self.show_index(self.current_index + 1))

        self.counter_label = QLabel("0 of 0")
        self.counter_label.setObjectName("muted")
        nav = QHBoxLayout()
        nav.addWidget(self.previous_button)
        nav.addStretch()
        nav.addWidget(self.counter_label)
        nav.addStretch()
        nav.addWidget(self.next_button)

        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("saveButton")
        self.discard_button = QPushButton("Discard")
        self.discard_button.setObjectName("discardButton")
        self.save_button.clicked.connect(self._request_save)
        self.discard_button.clicked.connect(self._discard)
        actions = QHBoxLayout()
        actions.addWidget(self.save_button)
        actions.addWidget(self.discard_button)

        review_page = QWidget()
        review_layout = QVBoxLayout(review_page)
        review_layout.setContentsMargins(SPACE["6"], SPACE["6"], SPACE["6"], SPACE["6"])
        review_layout.setSpacing(SPACE["4"])
        review_layout.addWidget(self.status_label)
        review_layout.addWidget(self.progress)
        review_layout.addWidget(scroll, 1)
        review_layout.addLayout(nav)
        review_layout.addLayout(actions)

        completion_panel = QFrame()
        completion_panel.setObjectName("completionPanel")
        self.completion_title = RetroGlowLabel("FINISHED", TYPE_SIZE["section"])
        self.completion_summary = QLabel()
        self.completion_summary.setObjectName("completionSummary")
        self.completion_summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.completion_summary.setWordWrap(True)
        self.finish_button = QPushButton("Return to Generation Hub")
        self.finish_button.setObjectName("finishButton")
        self.finish_button.setAccessibleDescription("Close this review and return to the Generation Hub")
        completion_layout = QVBoxLayout(completion_panel)
        completion_layout.setContentsMargins(SPACE["10"], SPACE["10"], SPACE["10"], SPACE["10"])
        completion_layout.setSpacing(SPACE["6"])
        completion_layout.addStretch()
        completion_layout.addWidget(self.completion_title, 0, Qt.AlignmentFlag.AlignCenter)
        completion_layout.addWidget(self.completion_summary)
        completion_layout.addWidget(self.finish_button, 0, Qt.AlignmentFlag.AlignCenter)
        completion_layout.addStretch()

        completion_page = QWidget()
        completion_page_layout = QVBoxLayout(completion_page)
        completion_page_layout.setContentsMargins(SPACE["6"], SPACE["6"], SPACE["6"], SPACE["6"])
        completion_page_layout.addWidget(completion_panel)

        self.state_pages = QStackedWidget()
        self.state_pages.setStyleSheet("QStackedWidget { background: transparent; }")
        self.state_pages.addWidget(review_page)
        self.state_pages.addWidget(completion_page)

        self.cancel_button = QPushButton("X")
        self.cancel_button.setObjectName("overlayCloseButton")
        self.cancel_button.setAccessibleName("Cancel generation")
        self.cancel_button.setToolTip("Cancel generation and return to the Generation Hub")
        self.cancel_button.clicked.connect(self.cancel_requested)
        close_row = QHBoxLayout()
        close_row.setContentsMargins(0, 0, 0, 0)
        close_row.addStretch()
        close_row.addWidget(self.cancel_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE["3"], SPACE["3"], SPACE["3"], SPACE["3"])
        layout.setSpacing(0)
        layout.addLayout(close_row)
        layout.addWidget(self.state_pages)
        self._sync_controls()

    def reset(self) -> None:
        self.clusters.clear()
        self.decisions.clear()
        self.current_index = -1
        self.stream_complete = False
        self.stream_failed = False
        self.save_in_progress = False
        self.state_pages.setCurrentIndex(0)
        self.status_label.setText("Connecting to the pipeline...")
        self.progress.setRange(0, 0)
        self.title_label.setText("Waiting for the first story cluster...")
        self.mode_badge.setText("WAITING")
        self.summary_label.setText("Results will appear here live as the pipeline produces them.")
        self._sync_controls()

    def handle_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("event_type")
        processed = int(event.get("processed_count", 0))
        total = int(event.get("total_expected", 0))
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(min(processed, total))
        if event_type == "fetched":
            self.status_label.setText(f"Fetching articles... {processed} of {total or '?'} processed")
        elif event_type == "clustered":
            self.status_label.setText(f"Clustering stories... {processed} of {total or '?'} processed")
        elif event_type == "cluster_ready" and isinstance(event.get("current_cluster"), dict):
            self.clusters.append(event["current_cluster"])
            if self.current_index < 0:
                self.show_index(0)
            else:
                self.status_label.setText(f"A new cluster arrived — {len(self.clusters)} available.")
                self._sync_controls()
        elif event_type == "completed":
            self.stream_complete = True
            self.progress.setRange(0, 1)
            self.progress.setValue(1)
            self.status_label.setText("Generation complete. Review each cluster to finish.")
            self._sync_controls()

    def show_index(self, index: int) -> None:
        if not 0 <= index < len(self.clusters):
            return
        self.current_index = index
        cluster = self.clusters[index]
        self.title_label.setText(str(cluster.get("title", "Untitled cluster")))
        self.mode_badge.setText(str(cluster.get("mode", "short")).upper())
        self.summary_label.setText(str(cluster.get("summary", "No summary available.")))
        self._sync_controls()

    def save_succeeded(self) -> None:
        self.save_in_progress = False
        if self.current_index >= 0:
            self.decisions[self.current_index] = "saved"
            self.status_label.setText("Saved to the Vault.")
        self._advance_after_decision()

    def save_failed(self, message: str) -> None:
        self.save_in_progress = False
        self.status_label.setText(f"Could not save this cluster: {message}")
        self._sync_controls()

    def show_pipeline_error(self, message: str) -> None:
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.status_label.setText(f"Pipeline connection failed: {message}")
        # Treat the interrupted stream as closed so the reviewed items (or an
        # empty run) can be finished and the user is never trapped here.
        self.stream_complete = True
        self.stream_failed = True
        self._sync_controls()

    def _request_save(self) -> None:
        if self.current_index < 0 or self.save_in_progress:
            return
        self.save_in_progress = True
        self.status_label.setText("Saving to the Vault...")
        self._sync_controls()
        self.save_requested.emit(self.clusters[self.current_index])

    def _discard(self) -> None:
        if self.current_index < 0:
            return
        self.decisions[self.current_index] = "discarded"
        self.status_label.setText("Cluster discarded.")
        self._advance_after_decision()

    def _advance_after_decision(self) -> None:
        for index in range(self.current_index + 1, len(self.clusters)):
            if index not in self.decisions:
                self.show_index(index)
                return
        self._sync_controls()

    def _sync_controls(self) -> None:
        count = len(self.clusters)
        has_cluster = self.current_index >= 0
        decided = has_cluster and self.current_index in self.decisions
        self.counter_label.setText(f"{self.current_index + 1 if has_cluster else 0} of {count}")
        self.previous_button.setEnabled(has_cluster and self.current_index > 0)
        self.next_button.setEnabled(has_cluster and self.current_index < count - 1)
        self.save_button.setEnabled(has_cluster and not decided and not self.save_in_progress)
        self.discard_button.setEnabled(has_cluster and not decided and not self.save_in_progress)
        self.save_button.setText("Saving..." if self.save_in_progress else "Saved" if decided and self.decisions.get(self.current_index) == "saved" else "Save")
        self.discard_button.setText("Discarded" if decided and self.decisions.get(self.current_index) == "discarded" else "Discard")
        all_decided = len(self.decisions) == count
        if self.stream_complete and all_decided:
            saved = sum(decision == "saved" for decision in self.decisions.values())
            discarded = sum(decision == "discarded" for decision in self.decisions.values())
            if self.stream_failed:
                self.completion_title.setText("RUN ENDED")
                lead = "The connection ended, but every received cluster has been reviewed."
            else:
                self.completion_title.setText("FINISHED")
                lead = "Review complete. Every generated cluster has a decision."
            self.completion_summary.setText(
                f"{lead}\n\n{count} reviewed  •  {saved} saved  •  {discarded} discarded"
            )
            self.state_pages.setCurrentIndex(1)
            self.finish_button.setFocus()
        else:
            self.state_pages.setCurrentIndex(0)


class GenerationPage(GalaxyWidget):
    generate_requested = pyqtSignal()
    vault_requested = pyqtSignal()
    audio_muted_changed = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.vault_button = QPushButton("Vault")
        self.vault_button.setAccessibleName("Open the Vault")
        self.vault_button.clicked.connect(self.vault_requested)
        self.audio_toggle = AudioToggleButton()
        self.audio_toggle.toggled.connect(self.audio_muted_changed)
        top = QHBoxLayout()
        top.addWidget(self.vault_button)
        top.addStretch()
        top.addWidget(self.audio_toggle)

        self.hero_title = RetroGlowLabel(
            "SMARTSCRAPE",
            TYPE_SIZE["hero"],
            dark_outline=False,
            core_color="yellow",
        )

        self.generate_button = RetroGenerateButton()
        self.generate_button.setAccessibleDescription("Start generating news clusters")
        self.generate_button.clicked.connect(self.generate_requested)
        hero = QWidget()
        hero_layout = QVBoxLayout(hero)
        hero_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.setSpacing(SPACE["8"])
        hero_layout.addWidget(self.hero_title, 0, Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(self.generate_button, 0, Qt.AlignmentFlag.AlignCenter)

        self.body = QStackedWidget()
        self.body.setStyleSheet("QStackedWidget { background: transparent; }")
        self.body.addWidget(hero)
        overlay_host = QWidget()
        overlay_layout = QVBoxLayout(overlay_host)
        overlay_layout.setContentsMargins(0, SPACE["4"], 0, SPACE["6"])
        self.overlay = GenerationOverlay()
        self.overlay.setFixedWidth(LAYOUT["overlay_max"])
        self.overlay.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        overlay_layout.addWidget(self.overlay, 1, Qt.AlignmentFlag.AlignHCenter)
        self.body.addWidget(overlay_host)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE["5"], SPACE["4"], SPACE["5"], SPACE["4"])
        layout.addLayout(top)
        layout.addWidget(self.body, 1)

    def resizeEvent(self, event: Any) -> None:
        """Keep the review frame aligned with the Vault detail width."""

        available_width = max(520, self.width() - (SPACE["5"] * 2))
        self.overlay.setFixedWidth(min(LAYOUT["overlay_max"], available_width))
        super().resizeEvent(event)

    def show_overlay(self) -> None:
        self.overlay.reset()
        self.body.setCurrentIndex(1)
        self.generate_button.setEnabled(False)

    def close_overlay(self) -> None:
        self.body.setCurrentIndex(0)
        self.generate_button.setEnabled(True)
        self.generate_button.setFocus()


class TrashButton(QAbstractButton):
    """Small custom-painted trash icon without font or emoji dependencies."""

    def __init__(self, title: str) -> None:
        super().__init__()
        self.entry_title = title
        self.setObjectName("trashButton")
        self.setFixedSize(30, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Delete {title}")
        self.setAccessibleName(f"Delete {title}")

    def set_deleting(self, deleting: bool) -> None:
        self.setEnabled(not deleting)
        self.setToolTip("Deleting..." if deleting else f"Delete {self.entry_title}")

    def paintEvent(self, event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        role = "disabled" if not self.isEnabled() else "error" if self.underMouse() else "cyan"
        color = QColor(COLOR[role])
        painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(8, 9, 22, 9)
        painter.drawLine(12, 6, 18, 6)
        painter.drawRect(10, 11, 10, 12)
        painter.drawLine(13, 14, 13, 20)
        painter.drawLine(17, 14, 17, 20)


class WarningIcon(QWidget):
    """Compact painted warning mark for the delete confirmation."""

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(48, 48)
        self.setAccessibleName("Warning")

    def paintEvent(self, event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        triangle = QPolygonF([QPointF(24, 4), QPointF(45, 42), QPointF(3, 42)])
        painter.setPen(QPen(QColor(COLOR["yellow_light"]), 2))
        painter.setBrush(QColor(COLOR["yellow_shadow"]))
        painter.drawPolygon(triangle)
        painter.setPen(QPen(QColor(COLOR["ink"]), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(24, 16), QPointF(24, 29))
        painter.drawPoint(QPointF(24, 35))


class DeleteConfirmationDialog(QDialog):
    """Balanced, content-sized destructive confirmation dialog."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("deleteConfirmation")
        self.setWindowTitle("Delete saved story")
        self.setModal(True)

        prompt = QLabel("Are you sure you want to delete this?")
        prompt.setObjectName("deletePrompt")
        story_title = QLabel(title)
        story_title.setObjectName("deleteStoryTitle")
        story_title.setWordWrap(True)
        story_title.setMaximumWidth(340)

        copy = QVBoxLayout()
        copy.setContentsMargins(0, 0, 0, 0)
        copy.setSpacing(SPACE["2"])
        copy.addWidget(prompt)
        copy.addWidget(story_title)

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(SPACE["4"])
        content.addWidget(WarningIcon(), 0, Qt.AlignmentFlag.AlignVCenter)
        content.addLayout(copy)

        self.delete_button = QPushButton("Delete story")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setDefault(True)
        self.delete_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.delete_button)

        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.setContentsMargins(SPACE["6"], SPACE["6"], SPACE["6"], SPACE["6"])
        layout.setSpacing(SPACE["5"])
        layout.addLayout(content)
        layout.addLayout(buttons)


class VaultListRow(QFrame):
    """Vault result with distinct row-open and delete interactions."""

    open_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, entry_id: int, title: str, created_at: str) -> None:
        super().__init__()
        self.entry_id = entry_id
        self.setMinimumHeight(LAYOUT["list_row_height"])
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        title_label = QLabel(title)
        title_label.setObjectName("vaultRowTitle")
        title_label.setWordWrap(True)
        title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        date_label = QLabel(created_at)
        date_label.setObjectName("vaultRowDate")
        date_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        date_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.delete_button = TrashButton(title)
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self.entry_id))
        metadata = QVBoxLayout()
        metadata.setContentsMargins(0, 0, 0, 0)
        metadata.setSpacing(SPACE["1"])
        metadata.addWidget(self.delete_button, 0, Qt.AlignmentFlag.AlignRight)
        metadata.addWidget(date_label, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACE["4"], SPACE["3"], SPACE["4"], SPACE["3"])
        layout.setSpacing(SPACE["4"])
        layout.addWidget(title_label, 1)
        layout.addLayout(metadata)

    def mouseReleaseEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_requested.emit(self.entry_id)
            event.accept()
            return
        super().mouseReleaseEvent(event)


class VaultPage(GalaxyWidget):
    home_requested = pyqtSignal()
    search_requested = pyqtSignal(str)
    detail_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.back_home_button = QPushButton("← Generation Hub")
        self.back_home_button.clicked.connect(self.home_requested)
        self.header_title = RetroGlowLabel(
            "THE VAULT",
            TYPE_SIZE["vault_title"],
            dark_outline=False,
            core_color="yellow",
        )
        header = QGridLayout()
        header.addWidget(self.back_home_button, 0, 0, Qt.AlignmentFlag.AlignLeft)
        header.addWidget(self.header_title, 0, 0, Qt.AlignmentFlag.AlignCenter)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search saved stories...")
        self.search_input.setAccessibleName("Search the Vault")
        self.search_button = QPushButton("Search")
        self.search_input.returnPressed.connect(self._submit_search)
        self.search_button.clicked.connect(self._submit_search)
        search_row = QHBoxLayout()
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.search_button)

        self.results_status = QLabel("Loading saved stories...")
        self.results_status.setObjectName("statusText")
        self.results = QListWidget()
        self.results.setAccessibleName("Vault search results")
        self.results.itemClicked.connect(self._open_item)
        self.results.itemActivated.connect(self._open_item)
        list_page = QWidget()
        list_page.setMaximumWidth(LAYOUT["content_max"])
        list_page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        list_layout = QVBoxLayout(list_page)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.addLayout(search_row)
        list_layout.addWidget(self.results_status)
        list_layout.addWidget(self.results, 1)
        list_host = QWidget()
        list_host_layout = QHBoxLayout(list_host)
        list_host_layout.setContentsMargins(0, 0, 0, 0)
        list_host_layout.addStretch()
        list_host_layout.addWidget(list_page, 1)
        list_host_layout.addStretch()

        self.detail_title = QLabel()
        self.detail_title.setObjectName("detailTitle")
        self.detail_title.setWordWrap(True)
        self.detail_summary = QLabel()
        self.detail_summary.setObjectName("detailSummary")
        self.detail_summary.setWordWrap(True)
        self.detail_summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.detail_url = QLabel()
        self.detail_url.setObjectName("detailUrl")
        self.detail_url.setWordWrap(True)
        self.detail_url.setOpenExternalLinks(True)
        self.detail_url.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.detail_error = QLabel()
        self.detail_error.setObjectName("errorText")
        self.detail_error.setWordWrap(True)
        back_results = QPushButton("← Back to results")
        back_results.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        detail_content = QWidget()
        detail_content.setObjectName("detailContent")
        detail_layout = QVBoxLayout(detail_content)
        detail_layout.setContentsMargins(SPACE["5"], SPACE["5"], SPACE["5"], SPACE["5"])
        detail_layout.setSpacing(SPACE["5"])
        detail_layout.addWidget(back_results, 0, Qt.AlignmentFlag.AlignLeft)
        detail_layout.addWidget(self.detail_error)
        detail_layout.addWidget(self.detail_title)
        detail_layout.addWidget(self.detail_summary)
        detail_layout.addWidget(self.detail_url)
        detail_layout.addStretch()
        detail_scroll = QScrollArea()
        detail_scroll.setObjectName("detailScroll")
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setWidget(detail_content)
        detail_scroll.setMaximumWidth(LAYOUT["content_max"])
        detail_host = QWidget()
        detail_host_layout = QHBoxLayout(detail_host)
        detail_host_layout.setContentsMargins(0, 0, 0, 0)
        detail_host_layout.addStretch()
        detail_host_layout.addWidget(detail_scroll, 1)
        detail_host_layout.addStretch()

        self.pages = QStackedWidget()
        self.pages.setStyleSheet("QStackedWidget { background: transparent; }")
        self.pages.addWidget(list_host)
        self.pages.addWidget(detail_host)
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACE["6"], SPACE["5"], SPACE["6"], SPACE["6"])
        root.setSpacing(SPACE["4"])
        root.addLayout(header)
        root.addWidget(self.pages, 1)

    def load_entries(self, entries: object) -> None:
        self.results.clear()
        if not isinstance(entries, list) or not entries:
            self.results_status.setText("No saved stories found.")
            return
        self.results_status.setText(f"{len(entries)} saved {'story' if len(entries) == 1 else 'stories'}")
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry_id = entry.get("id")
            if entry_id is None:
                continue
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, int(entry_id))
            row = VaultListRow(
                int(entry_id),
                str(entry.get("title", "Untitled")),
                str(entry.get("created_at", "Date unavailable")),
            )
            row.open_requested.connect(self._open_entry_id)
            row.delete_requested.connect(
                lambda row_id, title=str(entry.get("title", "this story")): self._confirm_delete(row_id, title)
            )
            item.setSizeHint(QSize(0, max(LAYOUT["list_row_height"], row.sizeHint().height())))
            self.results.addItem(item)
            self.results.setItemWidget(item, row)

    def _confirm_delete(self, entry_id: int, title: str) -> None:
        dialog = DeleteConfirmationDialog(title, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.set_entry_deleting(entry_id, True)
            self.delete_requested.emit(entry_id)

    def set_entry_deleting(self, entry_id: int, deleting: bool) -> None:
        row = self._row_for_entry(entry_id)
        if row is not None:
            row.delete_button.set_deleting(deleting)

    def remove_entry(self, entry_id: int) -> None:
        for index in range(self.results.count()):
            item = self.results.item(index)
            if item.data(Qt.ItemDataRole.UserRole) != entry_id:
                continue
            row = self.results.itemWidget(item)
            self.results.takeItem(index)
            if row is not None:
                row.deleteLater()
            break
        count = self.results.count()
        self.results_status.setText(
            "No saved stories found."
            if count == 0
            else f"{count} saved {'story' if count == 1 else 'stories'}"
        )

    def _row_for_entry(self, entry_id: int) -> VaultListRow | None:
        for index in range(self.results.count()):
            item = self.results.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == entry_id:
                row = self.results.itemWidget(item)
                return row if isinstance(row, VaultListRow) else None
        return None

    def show_results_error(self, message: str) -> None:
        self.results.clear()
        self.results_status.setText(f"Could not load the Vault: {message}")

    def show_detail(self, detail: object) -> None:
        self.pages.setCurrentIndex(1)
        self.detail_error.clear()
        if not isinstance(detail, dict):
            self.detail_title.setText("Story not found")
            self.detail_summary.setText("This Vault entry no longer exists.")
            self.detail_url.clear()
            return
        self.detail_title.setText(str(detail.get("title", "Untitled")))
        self.detail_summary.setText(str(detail.get("summary", "No summary available.")))
        url = str(detail.get("url", ""))
        safe_url = html.escape(url, quote=True)
        self.detail_url.setText(f'<a style="color:{COLOR["cyan"]}" href="{safe_url}">{html.escape(url)}</a>' if url else "No source URL available.")

    def show_detail_error(self, message: str) -> None:
        self.pages.setCurrentIndex(1)
        self.detail_title.setText("Could not load story")
        self.detail_summary.clear()
        self.detail_url.clear()
        self.detail_error.setText(message)

    def _submit_search(self) -> None:
        self.results_status.setText("Searching...")
        self.search_requested.emit(self.search_input.text().strip())

    def _open_item(self, item: QListWidgetItem) -> None:
        entry_id = item.data(Qt.ItemDataRole.UserRole)
        if entry_id is not None:
            self._open_entry_id(int(entry_id))

    def _open_entry_id(self, entry_id: int) -> None:
        self.detail_title.setText("Loading story...")
        self.detail_summary.clear()
        self.detail_url.clear()
        self.pages.setCurrentIndex(1)
        self.detail_requested.emit(entry_id)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.pipeline_worker: PipelineWorker | None = None
        self.api_workers: set[ApiWorker] = set()
        self.sound_enabled = True

        self.setWindowTitle("SmartScrape")
        self.resize(980, 700)
        self.setMinimumSize(760, 560)
        configure_retro_font()
        self.setStyleSheet(build_stylesheet())

        self.generation_page = GenerationPage()
        self.vault_page = VaultPage()
        self.pages = QStackedWidget()
        self.pages.addWidget(self.generation_page)
        self.pages.addWidget(self.vault_page)
        self.setCentralWidget(self.pages)

        self.background_music = BackgroundMusicController.for_application(self)
        self.background_music.start(enabled=self.sound_enabled)

        self.generation_page.generate_requested.connect(self.start_generation)
        self.generation_page.vault_requested.connect(self.open_vault)
        self.generation_page.audio_muted_changed.connect(self._set_audio_muted)
        self.generation_page.overlay.save_requested.connect(self.save_cluster)
        self.generation_page.overlay.cancel_requested.connect(self.cancel_generation)
        self.generation_page.overlay.finish_button.clicked.connect(self.finish_generation)
        self.vault_page.home_requested.connect(lambda: self.pages.setCurrentIndex(0))
        self.vault_page.search_requested.connect(self.search_vault)
        self.vault_page.detail_requested.connect(self.load_vault_detail)
        self.vault_page.delete_requested.connect(self.delete_vault_entry)
        self.statusBar().showMessage("Ready")

    def _play_click_sound(self) -> None:
        """No-op audio hook. Wire client/assets/sounds/click.mp3 here later."""

        # Intentionally silent for now: the client has no audio asset or playback
        # dependency yet. Keeping this method makes the future integration local.
        return

    def _set_audio_muted(self, muted: bool) -> None:
        self.sound_enabled = not muted
        self.background_music.set_enabled(self.sound_enabled)
        self.statusBar().showMessage("App audio muted" if muted else "App audio enabled", 2500)

    def start_generation(self) -> None:
        if self.pipeline_worker is not None and self.pipeline_worker.isRunning():
            return
        if self.sound_enabled:
            self._play_click_sound()
        self.generation_page.show_overlay()
        self.statusBar().showMessage("Generating...")
        worker = PipelineWorker()
        self.pipeline_worker = worker
        worker.event_received.connect(self.generation_page.overlay.handle_event)
        worker.failed.connect(self.generation_page.overlay.show_pipeline_error)
        worker.finished.connect(self._pipeline_thread_finished)
        worker.start()

    def _pipeline_thread_finished(self) -> None:
        worker = self.pipeline_worker
        self.pipeline_worker = None
        if worker is not None:
            worker.deleteLater()

    def finish_generation(self) -> None:
        self.generation_page.close_overlay()
        self.statusBar().showMessage("Generation review complete", 3000)

    def cancel_generation(self) -> None:
        worker = self.pipeline_worker
        if worker is not None and worker.isRunning():
            worker.stop()
        self.generation_page.close_overlay()
        self.statusBar().showMessage("Generation cancelled", 3000)

    def save_cluster(self, cluster: dict[str, Any]) -> None:
        self._start_api_worker(
            ApiWorker("save", cluster),
            lambda _data: self.generation_page.overlay.save_succeeded(),
            lambda message: self.generation_page.overlay.save_failed(message),
        )

    def open_vault(self) -> None:
        self.pages.setCurrentIndex(1)
        self.vault_page.pages.setCurrentIndex(0)
        self.vault_page.results_status.setText("Loading saved stories...")
        self.search_vault("")

    def search_vault(self, query: str) -> None:
        operation = "search" if query else "entries"
        self._start_api_worker(
            ApiWorker(operation, query),
            self.vault_page.load_entries,
            self.vault_page.show_results_error,
        )

    def load_vault_detail(self, entry_id: int) -> None:
        self._start_api_worker(
            ApiWorker("detail", entry_id),
            self.vault_page.show_detail,
            self.vault_page.show_detail_error,
        )

    def delete_vault_entry(self, entry_id: int) -> None:
        self.vault_page.set_entry_deleting(entry_id, True)

        def handle_success(_data: object) -> None:
            self.vault_page.remove_entry(entry_id)
            self.statusBar().showMessage("Saved story deleted", 3500)

        def handle_failure(message: str) -> None:
            self.vault_page.set_entry_deleting(entry_id, False)
            self.statusBar().showMessage(f"Could not delete story: {message}", 6000)

        self._start_api_worker(
            ApiWorker("delete", entry_id),
            handle_success,
            handle_failure,
        )

    def _start_api_worker(self, worker: ApiWorker, on_success: Any, on_failure: Any) -> None:
        self.api_workers.add(worker)

        def handle_success(_operation: str, data: object) -> None:
            on_success(data)

        def handle_failure(_operation: str, message: str) -> None:
            on_failure(message)

        def cleanup() -> None:
            self.api_workers.discard(worker)
            worker.deleteLater()

        worker.succeeded.connect(handle_success)
        worker.failed.connect(handle_failure)
        worker.finished.connect(cleanup)
        worker.start()

    def closeEvent(self, event: Any) -> None:
        self.background_music.stop()
        # Let short-lived REST calls finish before Qt destroys their QThread wrappers.
        for worker in list(self.api_workers):
            worker.requestInterruption()
            worker.wait(1000)
        if self.pipeline_worker is not None and self.pipeline_worker.isRunning():
            self.pipeline_worker.stop()
            self.pipeline_worker.wait(2000)
        event.accept()
