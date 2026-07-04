"""
QThread / signal pattern used here:

PyQt applications run their user interface on the main Qt event loop. If slow
work such as a network request or time.sleep() runs on that same thread, the
window cannot repaint, buttons cannot respond, and the app appears frozen.

To avoid that, RefreshWorker subclasses QThread and does the simulated slow
work inside run(). When the work finishes, it emits a Qt signal containing the
article data. Qt delivers that signal back to MainWindow on the GUI thread,
where it is safe to update widgets. The worker never touches UI widgets
directly; it only sends data through signals.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class Article:
    title: str
    source: str
    snippet: str


SAMPLE_ARTICLES = [
    Article(
        title="Madrid Edges Rivals in Late Football Thriller",
        source="Football Desk",
        snippet="A stoppage-time winner capped a tense match defined by quick transitions and disciplined defending.",
    ),
    Article(
        title="Young Midfielder Turns Training Buzz Into Matchday Impact",
        source="Pitch Notes",
        snippet="Coaches praised the player's composure after a breakout performance against a compact back line.",
    ),
    Article(
        title="New Archive Reveals Trade Routes of the Ancient Mediterranean",
        source="History Ledger",
        snippet="Freshly cataloged records point to a wider network of ports, merchants, and diplomatic ties.",
    ),
    Article(
        title="How a Medieval Siege Changed City Planning",
        source="Past & Present",
        snippet="Historians trace later fortification designs to lessons learned during one unusually long campaign.",
    ),
    Article(
        title="Classic Rock Producer Revisits a Landmark Studio Session",
        source="Vinyl Weekly",
        snippet="The engineer recalls analog tape experiments that helped define a decade of guitar-heavy records.",
    ),
    Article(
        title="Lost Live Recording Adds Spark to a Beloved Rock Era",
        source="Backbeat Journal",
        snippet="A restored concert tape captures a band stretching familiar songs into louder, looser arrangements.",
    ),
]


class RefreshWorker(QThread):
    articles_ready = pyqtSignal(list)

    def run(self) -> None:
        time.sleep(2)
        self.articles_ready.emit(SAMPLE_ARTICLES)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.refresh_worker: RefreshWorker | None = None

        self.setWindowTitle("SmartScrape")
        self.resize(760, 520)

        self.article_list = QListWidget()
        self.article_list.setSpacing(8)
        self.article_list.setAlternatingRowColors(True)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_articles)

        header_layout = QHBoxLayout()
        title_label = QLabel("News Feed")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_button)

        layout = QVBoxLayout()
        layout.addLayout(header_layout)
        layout.addWidget(self.article_list)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.statusBar().showMessage("Ready")
        self.setStyleSheet(
            """
            QListWidget {
                border: 1px solid #cfcfcf;
                background: #ffffff;
            }
            QLabel#articleTitle {
                font-weight: 600;
            }
            QLabel#articleSource {
                color: #555555;
            }
            QLabel#articleSnippet {
                color: #333333;
            }
            """
        )

        self.update_articles(SAMPLE_ARTICLES)

    def refresh_articles(self) -> None:
        if self.refresh_worker is not None and self.refresh_worker.isRunning():
            return

        self.statusBar().showMessage("Refreshing...")
        self.refresh_button.setEnabled(False)

        self.refresh_worker = RefreshWorker()
        self.refresh_worker.articles_ready.connect(self.handle_articles_ready)
        self.refresh_worker.finished.connect(self.refresh_worker.deleteLater)
        self.refresh_worker.finished.connect(self.handle_refresh_finished)
        self.refresh_worker.start()

    def handle_articles_ready(self, articles: list[Article]) -> None:
        self.update_articles(articles)
        self.statusBar().showMessage("Updated")

    def handle_refresh_finished(self) -> None:
        self.refresh_button.setEnabled(True)
        self.refresh_worker = None

    def update_articles(self, articles: list[Article]) -> None:
        self.article_list.clear()

        for article in articles:
            item = QListWidgetItem()
            widget = self.create_article_widget(article)
            item.setSizeHint(widget.sizeHint())
            self.article_list.addItem(item)
            self.article_list.setItemWidget(item, widget)

    def create_article_widget(self, article: Article) -> QWidget:
        title = QLabel(article.title)
        title.setObjectName("articleTitle")
        title.setWordWrap(True)

        source = QLabel(article.source)
        source.setObjectName("articleSource")

        snippet = QLabel(article.snippet)
        snippet.setObjectName("articleSnippet")
        snippet.setWordWrap(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        layout.addWidget(title)
        layout.addWidget(source)
        layout.addWidget(snippet)

        article_widget = QFrame()
        article_widget.setFrameShape(QFrame.Shape.NoFrame)
        article_widget.setLayout(layout)
        article_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        return article_widget
