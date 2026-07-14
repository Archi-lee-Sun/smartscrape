"""Independent looping background-music playback for SmartScrape."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Sequence

from PyQt6.QtCore import QObject, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer


LOGGER = logging.getLogger(__name__)
DEFAULT_MUSIC_VOLUME = 0.30


class BackgroundMusicController(QObject):
    """Play local tracks sequentially, skipping failures and looping forever."""

    def __init__(
        self,
        track_paths: Sequence[Path],
        parent: QObject | None = None,
        *,
        player: Any | None = None,
        audio_output: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self.track_paths = tuple(Path(path).resolve() for path in track_paths)
        self.player = player if player is not None else QMediaPlayer(self)
        self.audio_output = audio_output if audio_output is not None else QAudioOutput(self)
        self.audio_output.setVolume(DEFAULT_MUSIC_VOLUME)
        self.player.setAudioOutput(self.audio_output)
        self.player.mediaStatusChanged.connect(self._handle_media_status)
        self.player.errorOccurred.connect(self._handle_error)

        self._current_index = -1
        self._consecutive_failures = 0
        self._playback_enabled = True
        self._exhausted = False

    @classmethod
    def for_application(cls, parent: QObject | None = None) -> "BackgroundMusicController":
        music_directory = Path(__file__).resolve().parent / "assets" / "music"
        tracks = tuple(music_directory / f"track{number}.mp3" for number in range(1, 5))
        return cls(tracks, parent)

    def start(self, enabled: bool = True) -> None:
        """Load track one and begin playback when the shared audio state allows it."""

        self._playback_enabled = enabled
        self._consecutive_failures = 0
        self._exhausted = False
        if not self.track_paths:
            LOGGER.warning("Background music is disabled because no tracks are configured.")
            return
        self._current_index = 0
        self._load_current_track()

    def set_enabled(self, enabled: bool) -> None:
        """Pause or resume the same player/source without resetting its position."""

        self._playback_enabled = enabled
        if not enabled:
            self.player.pause()
            return
        if self._exhausted or self._current_index < 0:
            self.start(enabled=True)
            return
        self.player.play()

    def stop(self) -> None:
        self.player.stop()

    def _load_current_track(self) -> None:
        path = self.track_paths[self._current_index]
        if not path.is_file():
            LOGGER.warning("Background music track is missing; skipping: %s", path)
            self._advance(failed=True)
            return

        self.player.setSource(QUrl.fromLocalFile(str(path)))
        if self._playback_enabled:
            self.player.play()

    def _handle_media_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._advance(failed=False)

    def _handle_error(self, _error: QMediaPlayer.Error, error_string: str) -> None:
        current = self.track_paths[self._current_index] if self._current_index >= 0 else "unknown track"
        LOGGER.warning("Background music failed for %s; skipping. %s", current, error_string)
        self._advance(failed=True)

    def _advance(self, *, failed: bool) -> None:
        if failed:
            self._consecutive_failures += 1
            if self._consecutive_failures >= len(self.track_paths):
                self._exhausted = True
                LOGGER.warning("No playable background music tracks were found.")
                return
        else:
            self._consecutive_failures = 0

        self._current_index = (self._current_index + 1) % len(self.track_paths)
        self._load_current_track()
