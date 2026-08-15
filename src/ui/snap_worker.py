"""
QThread worker for running the snap automation workflow.
Keeps the UI responsive while the snap process runs in a background thread.
"""
from PyQt6.QtCore import QThread, pyqtSignal


class SnapWorker(QThread):
    """
    Worker thread that runs the snap workflow.

    Signals:
        progress(int, str):        Emitted with (step_number, description) as each step starts.
        finished_snap(bytes, str): Emitted on success with (screenshot_png_bytes, share_text).
        error(str):                Emitted on failure with an error description.
        hide_dialog():             Emitted just before game-window interaction so the progress
                                   dialog is hidden and doesn't overlap the game.
        show_dialog():             Emitted after the game interaction is complete so the
                                   progress dialog can be restored.
    """
    progress    = pyqtSignal(int, str)
    finished_snap = pyqtSignal(bytes, str)
    error       = pyqtSignal(str)
    hide_dialog = pyqtSignal()
    show_dialog = pyqtSignal()

    def run(self):
        """Execute the snap workflow in a background thread."""
        try:
            from ..services.snap_service import run_snap_workflow, SnapError
            from ..config import (
                SNAP_CAPTURE_DEFAULT_OFFSET_X,
                SNAP_CAPTURE_DEFAULT_SIZE,
                SNAP_CAPTURE_MAX_DIMENSION,
            )
            from PyQt6.QtCore import QSettings

            settings = QSettings("NikkiBook", "App")
            mode = settings.value("snap_mode", "album")
            skip_album = (mode == "nikkibook_only")

            def capture_dimension(key: str, default: int) -> int:
                raw_value = settings.value(key, "")
                try:
                    value = int(raw_value)
                except (TypeError, ValueError):
                    return default
                return min(max(value, 1), SNAP_CAPTURE_MAX_DIMENSION)

            capture_width = capture_dimension(
                "snap_capture_width", SNAP_CAPTURE_DEFAULT_SIZE[0]
            )
            capture_height = capture_dimension(
                "snap_capture_height", SNAP_CAPTURE_DEFAULT_SIZE[1]
            )

            raw_offset = settings.value("snap_capture_offset_x", "")
            try:
                capture_offset_x = int(raw_offset)
            except (TypeError, ValueError):
                capture_offset_x = SNAP_CAPTURE_DEFAULT_OFFSET_X
            capture_offset_x = min(
                max(capture_offset_x, 0), SNAP_CAPTURE_MAX_DIMENSION
            )

            screenshot_bytes, share_text = run_snap_workflow(
                progress_callback=self._on_progress,
                hide_ui_callback=self._on_hide,
                show_ui_callback=self._on_show,
                skip_album=skip_album,
                capture_width=capture_width,
                capture_height=capture_height,
                capture_offset_x=capture_offset_x,
            )

            self.finished_snap.emit(screenshot_bytes, share_text)

        except SnapError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Unexpected error during snap: {e}")

    def _on_progress(self, step: int, description: str):
        """Forward progress from the snap service to the UI thread."""
        self.progress.emit(step, description)

    def _on_hide(self):
        """Tell the UI thread to hide the progress dialog."""
        self.hide_dialog.emit()

    def _on_show(self):
        """Tell the UI thread to show the progress dialog again."""
        self.show_dialog.emit()
