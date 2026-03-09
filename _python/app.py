"""Svelda — PyQt6 desktop application for AI-powered product image processing.

Processes product photos using the Gemini Vision API, applying photography-style
prompts (neutral white background, studio lighting, upscaling, etc.) to batches
of images. Results are shown as job cards with live thumbnail previews.

Usage:
    conda run -n svelda python _python/app.py
"""

from __future__ import annotations

import sys
import os
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "libs"))
from svelda import (
    apply_prompts_to_products,
    NEUTRAL_WHITE_PROMPT,
    CATS_PROMPTS_STUDIO,
    CATS_PROMPTS_HOME,
    UPSCALE_PROMPT,
    client as _gemini_client,
)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QButtonGroup, QRadioButton,
    QComboBox, QCheckBox, QProgressBar, QFileDialog, QGroupBox,
    QScrollArea, QFrame, QDialog, QGridLayout,
    QTabWidget, QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
)
from PyQt6.QtGui import QPixmap, QCursor, QDragEnterEvent, QDropEvent, QColor, QPainter, QPen, QImage, QDesktopServices
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QRect, QUrl

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IMAGE_EXTS   = ('.png', '.jpg', '.jpeg')  # supported input formats
THUMB_SIZE   = 88    # px — thumbnail strip cell size
RESULT_THUMB = 160   # px — result grid cell size
PREVIEW_MAX  = 400   # px — hover popup max dimension
CARD_THUMB   = 52    # px — job card inline thumbnail size
BA_IMG_MAX   = 480   # px — before/after dialog max image side
MAX_HISTORY  = 50    # max job history entries to persist on disk

# ---------------------------------------------------------------------------
# Prompt registry
# ---------------------------------------------------------------------------

def _prepare(key: str, prompt_list: list[str]) -> tuple[list[str], list[str]]:
    """Normalise a prompt source entry into a (prompts, codes) tuple.

    Multi-part prompts are joined with double newlines so the Gemini API
    receives a single combined instruction string.
    """
    if len(prompt_list) > 1:
        return (["\n\n".join(prompt_list)], [key])
    return (prompt_list, [key])


ALL_PROMPTS: dict[str, tuple[list[str], list[str]]] = {}
for _src in [NEUTRAL_WHITE_PROMPT, CATS_PROMPTS_STUDIO, CATS_PROMPTS_HOME, UPSCALE_PROMPT]:
    for _key, _plist in _src.items():
        ALL_PROMPTS[_key] = _prepare(_key, _plist)

# Ordered list of built-in keys (preserves source order, deduplicated)
_BUILTIN_KEYS_ORDERED: list[str] = []
_BUILTIN_KEYS: set[str] = set()
for _src in [NEUTRAL_WHITE_PROMPT, CATS_PROMPTS_STUDIO, CATS_PROMPTS_HOME, UPSCALE_PROMPT]:
    for _k in _src:
        if _k not in _BUILTIN_KEYS:
            _BUILTIN_KEYS_ORDERED.append(_k)
            _BUILTIN_KEYS.add(_k)

PROMPT_LABELS: dict[str, str] = {
    'NEUTRAL_WHITE':              'White BG — centered',
    'NEUTRAL_WHITE_FRAMING':      'White BG — preserve framing',
    'DARK_STUDIO':                'Dark studio — dramatic',
    'WARM_LIFESTYLE':             'Warm lifestyle — golden light',
    'CATS_STUDIO_MOSAIC':         'Cats — studio mosaic',
    'CATS_HOME_MOSAIC_GALLERY':   'Cats — home gallery mosaic',
    'CATS_HOME_MOSAIC_EVERYDAY':  'Cats — home everyday mosaic',
    'CATS_HOME_MOSAIC_LUXURY':    'Cats — home luxury mosaic',
    'UPSCALE':                    'Upscale to 8K',
}

# ---------------------------------------------------------------------------
# Custom prompts persistence
# ---------------------------------------------------------------------------

CUSTOM_PROMPTS_FILE = Path(__file__).parent / "custom_prompts.json"
CUSTOM_PROMPT_TEXTS: dict[str, str] = {}


def _load_custom_data() -> dict:
    """Load persisted label overrides and custom prompts from disk.

    Returns an empty structure if the file is absent or corrupt.
    """
    if CUSTOM_PROMPTS_FILE.exists():
        try:
            return json.loads(CUSTOM_PROMPTS_FILE.read_text())
        except Exception:
            pass
    return {"label_overrides": {}, "custom_prompts": {}}


def _save_custom_data(data: dict) -> None:
    """Serialise custom prompt data to disk as formatted JSON."""
    CUSTOM_PROMPTS_FILE.write_text(json.dumps(data, indent=2))


def _apply_custom_data() -> None:
    """Merge persisted custom data into the in-memory prompt registries.

    Called once at startup so the Run tab reflects any saved customisations.
    """
    data = _load_custom_data()
    for key, label in data.get("label_overrides", {}).items():
        if key in PROMPT_LABELS:
            PROMPT_LABELS[key] = label
    for key, d in data.get("custom_prompts", {}).items():
        text  = d.get("text", "")
        label = d.get("label", key)
        ALL_PROMPTS[key]         = ([text], [key])
        PROMPT_LABELS[key]       = label
        CUSTOM_PROMPT_TEXTS[key] = text


_apply_custom_data()


def _get_builtin_text(key: str) -> str:
    """Return the raw prompt text for a built-in key, joined across parts."""
    for src in [NEUTRAL_WHITE_PROMPT, CATS_PROMPTS_STUDIO, CATS_PROMPTS_HOME, UPSCALE_PROMPT]:
        if key in src:
            return "\n\n".join(src[key])
    return ""


def _prompt_tooltip(key: str) -> str:
    """Return a truncated prompt snippet suitable for a tooltip (≤ 600 chars)."""
    if key in CUSTOM_PROMPT_TEXTS:
        text = CUSTOM_PROMPT_TEXTS[key]
        return text[:600] + ("…" if len(text) > 600 else "")
    for src in [NEUTRAL_WHITE_PROMPT, CATS_PROMPTS_STUDIO, CATS_PROMPTS_HOME, UPSCALE_PROMPT]:
        if key not in src:
            continue
        items = src[key]
        text  = "\n\n".join(items[1:3]) if len(items) > 1 else items[0]
        return text[:600] + ("…" if len(text) > 600 else "")
    return ""


# ---------------------------------------------------------------------------
# Job history persistence
# ---------------------------------------------------------------------------

JOBS_HISTORY_FILE = Path(__file__).parent / "jobs_history.json"


def _load_jobs_history() -> list[dict]:
    """Load the persisted job history from disk.

    Returns an empty list if the file is absent or corrupt.
    """
    if JOBS_HISTORY_FILE.exists():
        try:
            return json.loads(JOBS_HISTORY_FILE.read_text())
        except Exception:
            pass
    return []


def _save_jobs_history(items: list[dict]) -> None:
    """Persist job history to disk, keeping only the most recent MAX_HISTORY entries."""
    JOBS_HISTORY_FILE.write_text(json.dumps(items[-MAX_HISTORY:], indent=2))


# ---------------------------------------------------------------------------
# Proto history persistence
# ---------------------------------------------------------------------------

PROTO_HISTORY_FILE = Path(__file__).parent / "proto_history.json"


def _load_proto_history() -> list[dict]:
    """Load the persisted proto history from disk.

    Returns an empty list if the file is absent or corrupt.
    """
    if PROTO_HISTORY_FILE.exists():
        try:
            return json.loads(PROTO_HISTORY_FILE.read_text())
        except Exception:
            pass
    return []


def _save_proto_history(items: list[dict]) -> None:
    """Persist proto history to disk, keeping only the most recent MAX_HISTORY entries."""
    PROTO_HISTORY_FILE.write_text(json.dumps(items[-MAX_HISTORY:], indent=2))


# ---------------------------------------------------------------------------
# Mosaic cell cropping helper
# ---------------------------------------------------------------------------

def _crop_mosaic_cell(src_path: str, cell_idx: int, dst_path: str) -> bool:
    """Crop one cell from a 3×3 mosaic image and save it to *dst_path*.

    Returns True on success, False if the source image cannot be loaded.
    Cell indices run row-major from 0 (top-left) to 8 (bottom-right).
    """
    img = QImage(src_path)
    if img.isNull():
        return False
    col = cell_idx % 3
    row = cell_idx // 3
    cw  = img.width()  // 3
    ch  = img.height() // 3
    return img.copy(col * cw, row * ch, cw, ch).save(dst_path)


# ---------------------------------------------------------------------------
# Gemini prompt generator
# ---------------------------------------------------------------------------

_META_PROMPT = """\
You are an AI prompt engineer for luxury product photography.

The user wants: {user_input}

Write a photography AI prompt using this exact structure:
[One sentence describing the overall aesthetic and style.]
MANDATE: [What must be strictly preserved — the product's exact framing, scale, position, shape, texture, material, and color. Be specific and absolute.]
ENVIRONMENT: [Background, surface, and setting. Specify materials (e.g. warm oak, polished marble), depth, and atmosphere.]
LIGHTING: [Direction, quality, color temperature, shadow characteristics, and any specular or rim highlights.]
OUTPUT: Clean, sharp, 4K resolution, luxury commercial aesthetic.

Also provide:
- nickname: a short human-readable display name (3–5 words, title case)
- key: a Python constant name (SCREAMING_SNAKE_CASE, 2–4 words, no spaces)

Respond ONLY with valid JSON — no markdown, no code fences, just the raw JSON object:
{{"nickname": "...", "key": "...", "prompt": "..."}}
"""


class PromptGeneratorWorker(QThread):
    """Background thread that calls Gemini to generate a photography prompt.

    Emits ``result`` with a parsed dict on success, or ``error`` with a
    message string on failure.
    """

    result = pyqtSignal(dict)
    error  = pyqtSignal(str)

    def __init__(self, user_input: str) -> None:
        super().__init__()
        self.user_input = user_input

    def run(self) -> None:
        """Send the meta-prompt to Gemini and parse the JSON response."""
        try:
            contents = _META_PROMPT.format(user_input=self.user_input)
            response = _gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
            )
            text = response.text.strip()
            # Strip markdown code fences if the model added them despite instructions
            if text.startswith("```"):
                lines = text.splitlines()
                text  = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
            data = json.loads(text)
            self.result.emit(data)
        except Exception as e:
            self.error.emit(str(e))


# ---------------------------------------------------------------------------
# Mosaic prompt generator (proto mode)
# ---------------------------------------------------------------------------

_MOSAIC_META_PROMPT = """\
You are an AI prompt engineer for luxury product photography.
The user's concept: {user_concept}

Write a prompt for an AI image generator that produces a SINGLE image:
a 3×3 mosaic of nine distinct square variations of the concept.

Use MANDATE / ENVIRONMENT / LIGHTING / OUTPUT structure.
ENVIRONMENT must describe each of the 9 distinct variations, numbered 1–9.
Respond with ONLY the prompt text — no JSON, no markdown, no code fences.\
"""


class MosaicPromptGeneratorWorker(QThread):
    """Background thread that generates a mosaic prompt via Gemini."""

    result = pyqtSignal(str)
    error  = pyqtSignal(str)

    def __init__(self, user_concept: str) -> None:
        super().__init__()
        self.user_concept = user_concept

    def run(self) -> None:
        try:
            contents = _MOSAIC_META_PROMPT.format(user_concept=self.user_concept)
            response = _gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
            )
            self.result.emit(response.text.strip())
        except Exception as e:
            self.error.emit(str(e))


# ---------------------------------------------------------------------------
# Proto worker
# ---------------------------------------------------------------------------

class ProtoWorker(QThread):
    """Background thread that runs a single-image mosaic generation job."""

    progress     = pyqtSignal(int, int, str)
    output_known = pyqtSignal(str)
    finished     = pyqtSignal(str)
    error        = pyqtSignal(str)

    def __init__(
        self,
        image_path: str,
        prompt_text: str,
        image_size: str,
        run_code: str,
    ) -> None:
        super().__init__()
        self.image_path  = image_path
        self.prompt_text = prompt_text
        self.image_size  = image_size
        self.run_code    = run_code

    def run(self) -> None:
        try:
            output_dir = os.path.join(os.path.dirname(self.image_path), self.run_code)
            self.output_known.emit(output_dir)
            apply_prompts_to_products(
                folders_or_files=[self.image_path],
                is_folder=False,
                prompts=[self.prompt_text],
                codes=[self.run_code],
                image_size=self.image_size,
                aspect="1:1",
                replace=True,
                save_to=os.path.dirname(self.image_path),
                on_progress=lambda c, t, f: self.progress.emit(c, t, f),
            )
            self.finished.emit(output_dir)
        except Exception as e:
            self.error.emit(str(e))


# ---------------------------------------------------------------------------
# Hover image preview popup (singleton)
# ---------------------------------------------------------------------------

class ImagePreviewPopup(QWidget):
    """Frameless tooltip-style popup showing a large image preview.

    Implemented as a singleton — call ``ImagePreviewPopup.get()`` rather than
    constructing directly.  Repositions itself to stay within screen bounds.
    """

    _instance: ImagePreviewPopup | None = None

    @classmethod
    def get(cls) -> ImagePreviewPopup:
        """Return the shared singleton instance, creating it if necessary."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet(
            "background: white; border: 1px solid #bbb; border-radius: 6px;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self._lbl = QLabel()
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._lbl)

    def show_for(self, path: str) -> None:
        """Display a scaled preview of the image at *path* near the cursor."""
        pix = QPixmap(path)
        if pix.isNull():
            return
        pix = pix.scaled(PREVIEW_MAX, PREVIEW_MAX,
                         Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
        self._lbl.setPixmap(pix)
        self._lbl.setFixedSize(pix.size())
        self.adjustSize()
        self._reposition()
        self.show()
        self.raise_()

    def _reposition(self) -> None:
        """Move the popup so it stays within the current screen bounds."""
        pos    = QCursor.pos()
        screen = QApplication.screenAt(pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        sg = screen.geometry()
        x  = pos.x() + 20
        y  = pos.y() + 20
        if x + self.width()  > sg.right():
            x = pos.x() - self.width()  - 12
        if y + self.height() > sg.bottom():
            y = pos.y() - self.height() - 12
        self.move(x, y)


# ---------------------------------------------------------------------------
# Mixin: hover image preview
# ---------------------------------------------------------------------------

class HoverPreviewMixin:
    """Mixin that adds delayed-hover image preview to any QWidget subclass.

    The host widget must:
    - Call ``_init_hover()`` in its ``__init__``.
    - Expose a ``path`` attribute containing the image file path.
    """

    _DELAY_MS = 350  # milliseconds before the preview popup appears

    def _init_hover(self) -> None:
        """Initialise the hover timer.  Must be called from __init__."""
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._show_preview)

    def enterEvent(self, event) -> None:
        if getattr(self, "path", None):
            self._hover_timer.start(self._DELAY_MS)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover_timer.stop()
        ImagePreviewPopup.get().hide()
        super().leaveEvent(event)

    def _show_preview(self) -> None:
        if getattr(self, "path", None):
            ImagePreviewPopup.get().show_for(self.path)


# ---------------------------------------------------------------------------
# Worker thread (image processing)
# ---------------------------------------------------------------------------

class Worker(QThread):
    """Background thread that sends images to the Gemini Vision API.

    Signals
    -------
    progress(current, total, filename):
        Emitted after each image is processed.
    output_known(output_dir):
        Emitted before processing begins so the UI can make the job card
        clickable as soon as the output directory is known.
    finished(output_dir):
        Emitted when all images have been processed successfully.
    error(message):
        Emitted if an unhandled exception occurs.
    """

    progress     = pyqtSignal(int, int, str)
    output_known = pyqtSignal(str)
    finished     = pyqtSignal(str)
    error        = pyqtSignal(str)

    def __init__(
        self,
        path: str | list[str],
        is_folder: bool,
        prompt_key: str,
        image_size: str,
        replace: bool,
    ) -> None:
        super().__init__()
        self.path       = path
        self.is_folder  = is_folder
        self.prompt_key = prompt_key
        self.image_size = image_size
        self.replace    = replace

    def run(self) -> None:
        """Process all images and emit progress/finished/error signals."""
        try:
            prompts, codes = ALL_PROMPTS[self.prompt_key]

            # Determine output directory before any API calls so the UI can
            # display a clickable card immediately.
            if self.is_folder:
                output_dir = os.path.join(self.path, f"processed_{codes[0]}")
            else:
                output_dir = os.path.join(os.path.dirname(self.path[0]), codes[0])
            self.output_known.emit(output_dir)

            def on_progress(current: int, total: int, filename: str) -> None:
                self.progress.emit(current, total, filename)

            if self.is_folder:
                apply_prompts_to_products(
                    folders_or_files=self.path, is_folder=True,
                    prompts=prompts, codes=codes,
                    image_size=self.image_size, replace=self.replace,
                    on_progress=on_progress,
                )
            else:
                apply_prompts_to_products(
                    folders_or_files=self.path, is_folder=False,
                    prompts=prompts, codes=codes,
                    image_size=self.image_size, replace=self.replace,
                    save_to=os.path.dirname(self.path[0]),
                    on_progress=on_progress,
                )

            self.finished.emit(output_dir)
        except Exception as e:
            self.error.emit(str(e))


# ---------------------------------------------------------------------------
# Thumbnail button (preview strip)
# ---------------------------------------------------------------------------

class ThumbButton(HoverPreviewMixin, QLabel):
    """Clickable thumbnail cell used inside SelectableThumbnailStrip."""

    clicked_signal = pyqtSignal()

    def __init__(
        self,
        path: str = "",
        label_text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.path = path
        self._init_hover()
        self.setFixedSize(THUMB_SIZE, THUMB_SIZE)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._unselect()

        if label_text:
            self.setText(label_text)
        elif path:
            pix = QPixmap(path)
            if not pix.isNull():
                pix = pix.scaled(THUMB_SIZE - 6, THUMB_SIZE - 6,
                                 Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
                self.setPixmap(pix)
            else:
                self.setText("?")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked_signal.emit()

    def set_selected(self, on: bool) -> None:
        """Highlight or de-highlight this thumbnail cell."""
        if on:
            self.setStyleSheet(
                "border: 2px solid #007AFF; border-radius: 4px; background: #ddeeff;"
            )
        else:
            self._unselect()

    def _unselect(self) -> None:
        self.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")


# ---------------------------------------------------------------------------
# Selectable thumbnail strip
# ---------------------------------------------------------------------------

class SelectableThumbnailStrip(QScrollArea):
    """Horizontal scrollable strip of image thumbnails with selection state.

    The first cell is always an "All (N)" button representing the whole
    folder/file list.  Subsequent cells represent individual images.

    Signals
    -------
    selection_changed(path_or_folder, is_folder):
        Emitted when the user clicks a cell.  ``path_or_folder`` is either a
        folder path string (is_folder=True) or a list of file paths.
    """

    selection_changed = pyqtSignal(object, bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setFixedHeight(THUMB_SIZE + 24)

        container  = QWidget()
        self._row  = QHBoxLayout(container)
        self._row.setSpacing(6)
        self._row.setContentsMargins(4, 4, 4, 4)
        self._row.addStretch()
        self.setWidget(container)

        self._folder_path: str | None       = None
        self._all_files:   list[str]        = []
        self._buttons:     list[ThumbButton] = []

    def set_folder(self, folder_path: str, files: list[str]) -> None:
        """Populate the strip from a folder; "All" emits the folder path."""
        self._folder_path = folder_path
        self._all_files   = files
        self._rebuild()

    def set_files(self, files: list[str]) -> None:
        """Populate the strip from an explicit file list."""
        self._folder_path = None
        self._all_files   = files
        self._rebuild()

    def select_file(self, path: str) -> None:
        """Programmatically select the cell for *path*, as if the user clicked it."""
        try:
            idx = self._all_files.index(path)
            self._on_click(idx + 1)  # +1 because index 0 is the "All" button
        except ValueError:
            pass

    def _rebuild(self) -> None:
        """Discard existing buttons and rebuild from the current file list."""
        self._buttons.clear()
        while self._row.count() > 1:  # keep the trailing stretch item
            item = self._row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        all_btn = ThumbButton(label_text=f"All\n{len(self._all_files)}")
        all_btn.clicked_signal.connect(lambda: self._on_click(0))
        self._buttons.append(all_btn)
        self._row.insertWidget(0, all_btn)

        for i, path in enumerate(self._all_files[:40]):
            btn = ThumbButton(path=path)
            btn.clicked_signal.connect(lambda idx=i + 1: self._on_click(idx))
            self._buttons.append(btn)
            self._row.insertWidget(self._row.count() - 1, btn)

        self._highlight(0)

    def _on_click(self, idx: int) -> None:
        self._highlight(idx)
        if idx == 0:
            if self._folder_path:
                self.selection_changed.emit(self._folder_path, True)
            else:
                self.selection_changed.emit(self._all_files, False)
        else:
            self.selection_changed.emit([self._all_files[idx - 1]], False)

    def _highlight(self, idx: int) -> None:
        for i, btn in enumerate(self._buttons):
            btn.set_selected(i == idx)


# ---------------------------------------------------------------------------
# Before / after split view dialog
# ---------------------------------------------------------------------------

class BeforeAfterDialog(QDialog):
    """Side-by-side comparison dialog showing the original and processed image.

    The original image is located by assuming svelda.py's naming convention:
    output files have the same filename as their source, stored one directory
    level below the processed subfolder:

        <folder>/processed_<code>/<filename>  →  original at  <folder>/<filename>
    """

    def __init__(self, result_path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        filename = os.path.basename(result_path)
        self.setWindowTitle(f"{filename} — Before / After")
        self.setMinimumSize(800, 500)

        # Derive original path: go two levels up from the result file
        original_path = os.path.normpath(
            os.path.join(result_path, "..", "..", filename)
        )
        has_original = os.path.isfile(original_path)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        body = QHBoxLayout()
        body.setSpacing(12)

        def _make_side(path: str, title: str, exists: bool) -> QWidget:
            """Build one comparison panel (title + image + Finder button)."""
            w  = QWidget()
            vb = QVBoxLayout(w)
            vb.setSpacing(4)
            vb.setContentsMargins(0, 0, 0, 0)

            hdr = QLabel(f"<b>{title}</b>")
            hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vb.addWidget(hdr)

            img_lbl = QLabel()
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_lbl.setMinimumSize(BA_IMG_MAX // 2, BA_IMG_MAX // 2)
            if exists:
                pix = QPixmap(path)
                if not pix.isNull():
                    pix = pix.scaled(BA_IMG_MAX, BA_IMG_MAX,
                                     Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
                    img_lbl.setPixmap(pix)
            else:
                img_lbl.setText("Original not found")
                img_lbl.setStyleSheet("color: grey; font-size: 11px;")
            vb.addWidget(img_lbl, stretch=1)

            if exists:
                open_btn = QPushButton("Open in Finder")
                open_btn.setFlat(True)
                open_btn.setStyleSheet(
                    "QPushButton { color: grey; font-size: 11px; text-decoration: underline; border: none; }"
                    "QPushButton:hover { color: #333; }"
                )
                open_btn.clicked.connect(lambda: subprocess.run(["open", path]))
                vb.addWidget(open_btn)
            return w

        body.addWidget(_make_side(original_path, "Original", has_original), stretch=1)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setFrameShadow(QFrame.Shadow.Sunken)
        body.addWidget(div)

        body.addWidget(_make_side(result_path, "Processed", True), stretch=1)
        layout.addLayout(body, stretch=1)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)


# ---------------------------------------------------------------------------
# Result image cell (grid item in ResultsDialog)
# ---------------------------------------------------------------------------

class ResultImageCell(HoverPreviewMixin, QWidget):
    """A single processed-image cell within the ResultsDialog grid.

    Features:
    - Click on the image → opens BeforeAfterDialog (or falls back to Finder).
    - Star button → toggles gold star and emits ``star_toggled`` signal.
    - Hover → shows the full-size preview popup.
    """

    star_toggled = pyqtSignal(str, bool)  # (path, is_starred)

    def __init__(self, path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.path     = path
        self._starred = False
        self._init_hover()
        self.setToolTip("Click for before/after  •  hover for preview")

        outer = QVBoxLayout(self)
        outer.setSpacing(2)
        outer.setContentsMargins(0, 0, 0, 0)

        img_lbl = QLabel()
        img_lbl.setFixedSize(RESULT_THUMB, RESULT_THUMB)
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_lbl.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        pix = QPixmap(path)
        if not pix.isNull():
            pix = pix.scaled(RESULT_THUMB, RESULT_THUMB,
                             Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
            img_lbl.setPixmap(pix)
        outer.addWidget(img_lbl)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(2)

        name_lbl = QLabel(os.path.basename(path))
        name_lbl.setStyleSheet("font-size: 10px; color: grey;")
        name_lbl.setFixedWidth(RESULT_THUMB - 26)
        name_lbl.setWordWrap(True)
        bottom_row.addWidget(name_lbl, stretch=1)

        self._star_btn = QPushButton("☆")
        self._star_btn.setFixedSize(22, 22)
        self._star_btn.setFlat(True)
        self._star_btn.setStyleSheet("QPushButton { font-size: 14px; color: #bbb; border: none; padding: 0; }")
        self._star_btn.clicked.connect(self._toggle_star)
        bottom_row.addWidget(self._star_btn)

        outer.addLayout(bottom_row)

        # Attach click handler directly to the image label, not the whole cell,
        # to avoid interfering with the star button.
        img_lbl.mousePressEvent = self._on_img_click

    def _on_img_click(self, event) -> None:
        """Open before/after dialog on left-click; fall back to Finder."""
        if event.button() != Qt.MouseButton.LeftButton:
            return
        original = os.path.normpath(
            os.path.join(self.path, "..", "..", os.path.basename(self.path))
        )
        if os.path.isfile(original):
            BeforeAfterDialog(self.path, self).exec()
        else:
            subprocess.run(["open", self.path])

    def _toggle_star(self) -> None:
        """Toggle the starred state and emit ``star_toggled``."""
        self._starred = not self._starred
        if self._starred:
            self._star_btn.setText("★")
            self._star_btn.setStyleSheet(
                "QPushButton { font-size: 14px; color: #FFC300; border: none; padding: 0; }"
            )
        else:
            self._star_btn.setText("☆")
            self._star_btn.setStyleSheet(
                "QPushButton { font-size: 14px; color: #bbb; border: none; padding: 0; }"
            )
        self.star_toggled.emit(self.path, self._starred)


# ---------------------------------------------------------------------------
# Results dialog
# ---------------------------------------------------------------------------

class ResultsDialog(QDialog):
    """Modal grid of processed images with star/picks and before/after support.

    Header row shows the output folder path (clickable → Finder) and a
    "Copy picks (N)" button that copies starred files to a ``picks/`` subfolder.
    """

    def __init__(
        self,
        output_dir: str,
        prompt_key: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._output_dir      = output_dir
        self._picks: set[str] = set()
        self.setWindowTitle(f"Results — {PROMPT_LABELS.get(prompt_key, prompt_key)}")
        self.setMinimumSize(640, 520)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ── Header row: folder path + copy-picks button ──
        header_row      = QHBoxLayout()
        open_folder_btn = QPushButton(output_dir)
        open_folder_btn.setFlat(True)
        open_folder_btn.setStyleSheet(
            "QPushButton { color: grey; font-size: 11px; text-align: left;"
            "  text-decoration: underline; border: none; padding: 0; }"
            "QPushButton:hover { color: #333; }"
        )
        open_folder_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_folder_btn.setToolTip("Click to open folder in Finder")
        open_folder_btn.clicked.connect(lambda: subprocess.run(["open", output_dir]))
        header_row.addWidget(open_folder_btn, stretch=1)

        self._copy_btn = QPushButton("Copy picks (0)")
        self._copy_btn.setEnabled(False)
        self._copy_btn.setToolTip("Copy starred images to picks/ subfolder")
        self._copy_btn.clicked.connect(self._copy_picks)
        header_row.addWidget(self._copy_btn)
        layout.addLayout(header_row)

        self._copy_status = QLabel("")
        self._copy_status.setStyleSheet("color: green; font-size: 11px;")
        self._copy_status.hide()
        layout.addWidget(self._copy_status)

        # ── Image grid ──
        scroll    = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid      = QGridLayout(container)
        grid.setSpacing(12)
        grid.setContentsMargins(8, 8, 8, 8)
        scroll.setWidget(container)

        files: list[str] = []
        if os.path.isdir(output_dir):
            files = sorted([
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if f.lower().endswith(IMAGE_EXTS)
            ])

        cols = 3
        for i, path in enumerate(files):
            cell = ResultImageCell(path)
            cell.star_toggled.connect(self._on_star_toggled)
            grid.addWidget(cell, i // cols, i % cols)

        if not files:
            empty = QLabel("No output images yet.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(empty, 0, 0)

        layout.addWidget(scroll)

        # ── Footer hint ──
        hint = QLabel(
            "Click image for before/after  •  ☆ to star  •  hover for preview"
            "  •  click folder to open in Finder"
        )
        hint.setStyleSheet("color: grey; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def _on_star_toggled(self, path: str, starred: bool) -> None:
        """Update the picks set and refresh the copy button label."""
        if starred:
            self._picks.add(path)
        else:
            self._picks.discard(path)
        n = len(self._picks)
        self._copy_btn.setText(f"Copy picks ({n})")
        self._copy_btn.setEnabled(n > 0)
        self._copy_status.hide()

    def _copy_picks(self) -> None:
        """Copy all starred files to ``<output_dir>/picks/``."""
        picks_dir = os.path.join(self._output_dir, "picks")
        os.makedirs(picks_dir, exist_ok=True)
        for path in self._picks:
            shutil.copy2(path, os.path.join(picks_dir, os.path.basename(path)))
        n = len(self._picks)
        self._copy_status.setText(f"Copied {n} file{'s' if n != 1 else ''} to picks/")
        self._copy_status.show()


# ---------------------------------------------------------------------------
# Job card
# ---------------------------------------------------------------------------

class JobCard(QFrame):
    """Card widget representing one processing job in the jobs list.

    Layout::

        ┌──────────────────────────────────────────────────┐
        │ <prompt label>  ·  <source>              [↺]    │
        │ [progress bar]              [live thumbnails]    │
        │ <status text>                                    │
        └──────────────────────────────────────────────────┘

    The card becomes clickable as soon as the output directory is known
    (emitted via ``Worker.output_known`` before any API calls complete).
    """

    reprocess_requested = pyqtSignal(dict)

    def __init__(self, config: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config        = config
        self._output_dir: str | None  = None
        self._shown_files: set[str]   = set()
        self._is_done      = False
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 8, 10, 8)

        # ── Title row ──
        header = QHBoxLayout()
        label  = PROMPT_LABELS.get(config['prompt_key'], config['prompt_key'])
        src    = (
            os.path.basename(config['path']) if config['is_folder']
            else f"{len(config['path'])} image{'s' if len(config['path']) != 1 else ''}"
        )
        self.title_lbl = QLabel(f"<b>{label}</b>  ·  {src}")
        reprocess_btn  = QPushButton("↺")
        reprocess_btn.setFixedWidth(28)
        reprocess_btn.setToolTip("Load into form")
        reprocess_btn.clicked.connect(lambda: self.reprocess_requested.emit(self.config))
        header.addWidget(self.title_lbl, stretch=1)
        header.addWidget(reprocess_btn)
        layout.addLayout(header)

        # ── Body: progress (left) + live thumbnails (right) ──
        body   = QHBoxLayout()
        body.setSpacing(8)

        left_v = QVBoxLayout()
        left_v.setSpacing(3)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%v / %m")
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setValue(0)
        left_v.addWidget(self.progress_bar)
        self.status_lbl = QLabel("Starting…")
        self.status_lbl.setStyleSheet("color: grey; font-size: 11px;")
        left_v.addWidget(self.status_lbl)
        left_v.addStretch()
        body.addLayout(left_v, stretch=1)

        # Right side: scrollable live thumbnail strip
        self._thumb_scroll = QScrollArea()
        self._thumb_scroll.setFixedHeight(CARD_THUMB + 12)
        self._thumb_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._thumb_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._thumb_scroll.setWidgetResizable(True)
        self._thumb_scroll.setFrameShape(QFrame.Shape.NoFrame)
        thumb_container = QWidget()
        self._thumb_row = QHBoxLayout(thumb_container)
        self._thumb_row.setSpacing(4)
        self._thumb_row.setContentsMargins(2, 2, 2, 2)
        self._thumb_row.addStretch()
        self._thumb_scroll.setWidget(thumb_container)
        body.addWidget(self._thumb_scroll, stretch=1)

        layout.addLayout(body)

    def set_output_dir(self, output_dir: str) -> None:
        """Record the output directory and make the card clickable."""
        self._output_dir = output_dir
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Click to preview results")

    def update_progress(self, current: int, total: int, filename: str) -> None:
        """Advance the progress bar and refresh the live thumbnail strip."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_lbl.setText(f"Processing: {os.path.basename(filename)}")
        self._refresh_thumbs()

    def mark_done(self, output_dir: str) -> None:
        """Mark the job as complete and show a green status label."""
        self._output_dir = output_dir
        self._is_done    = True
        self.progress_bar.setValue(self.progress_bar.maximum() or 1)
        self.status_lbl.setText("✓  Done — click to view results")
        self.status_lbl.setStyleSheet("color: green; font-size: 11px;")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Click to view results")
        self._refresh_thumbs()

    def mark_error(self, message: str) -> None:
        """Display an error message in red."""
        self.status_lbl.setText(f"✗  {message}")
        self.status_lbl.setStyleSheet("color: red; font-size: 11px;")

    def _refresh_thumbs(self) -> None:
        """Scan the output directory and append any new result thumbnails."""
        if not self._output_dir or not os.path.isdir(self._output_dir):
            return
        files = sorted([
            os.path.join(self._output_dir, f)
            for f in os.listdir(self._output_dir)
            if f.lower().endswith(IMAGE_EXTS)
        ])
        for path in files:
            if path in self._shown_files:
                continue
            self._shown_files.add(path)
            lbl = QLabel()
            lbl.setFixedSize(CARD_THUMB, CARD_THUMB)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pix = QPixmap(path)
            if not pix.isNull():
                pix = pix.scaled(CARD_THUMB - 2, CARD_THUMB - 2,
                                 Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
                lbl.setPixmap(pix)
            self._thumb_row.insertWidget(self._thumb_row.count() - 1, lbl)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._output_dir:
            self._open_results()

    def _open_results(self) -> None:
        ResultsDialog(self._output_dir, self.config['prompt_key'], self).exec()


# ---------------------------------------------------------------------------
# Proto: image-only drop target
# ---------------------------------------------------------------------------

class DropImageWidget(QGroupBox):
    """QGroupBox that accepts drag-and-drop of a single image file."""

    image_dropped = pyqtSignal(str)

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            url  = event.mimeData().urls()[0]
            path = url.toLocalFile()
            if url.isLocalFile() and path.lower().endswith(IMAGE_EXTS):
                event.acceptProposedAction()
                self.setStyleSheet(
                    "QGroupBox { border: 2px solid #007AFF; border-radius: 4px; }"
                )
                return
        event.ignore()

    def dragLeaveEvent(self, _event) -> None:
        self.setStyleSheet("")

    def dropEvent(self, event: QDropEvent) -> None:
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith(IMAGE_EXTS):
                self.image_dropped.emit(path)
                event.acceptProposedAction()


# ---------------------------------------------------------------------------
# Proto: interactive mosaic cell widget
# ---------------------------------------------------------------------------

class MosaicCellWidget(QWidget):
    """Displays a mosaic image with a 3×3 grid overlay and hover highlighting.

    Emits ``cell_clicked(int)`` with the zero-based row-major cell index
    when the user clicks on a cell.
    """

    cell_clicked = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._hovered_cell: int = -1
        self.setMouseTracking(True)
        self.setMinimumSize(300, 300)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()

    def _rendered_rect(self) -> QRect:
        if self._pixmap is None or self._pixmap.isNull():
            return QRect()
        pw, ph = self._pixmap.width(), self._pixmap.height()
        ww, wh = self.width(), self.height()
        scale  = min(ww / pw, wh / ph)
        rw, rh = int(pw * scale), int(ph * scale)
        return QRect((ww - rw) // 2, (wh - rh) // 2, rw, rh)

    def _cell_at(self, pos) -> int:
        r = self._rendered_rect()
        if not r.contains(pos):
            return -1
        col = (pos.x() - r.x()) * 3 // r.width()
        row = (pos.y() - r.y()) * 3 // r.height()
        col = max(0, min(2, col))
        row = max(0, min(2, row))
        return row * 3 + col

    def paintEvent(self, _event) -> None:
        if self._pixmap is None or self._pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = self._rendered_rect()
        painter.drawPixmap(r, self._pixmap)

        # Draw 3×3 white grid
        pen = QPen(QColor(255, 255, 255, 180))
        pen.setWidth(1)
        painter.setPen(pen)
        cw = r.width()  // 3
        ch = r.height() // 3
        for i in range(1, 3):
            painter.drawLine(r.x() + i * cw, r.y(), r.x() + i * cw, r.bottom())
            painter.drawLine(r.x(), r.y() + i * ch, r.right(), r.y() + i * ch)

        # Highlight hovered cell
        if self._hovered_cell >= 0:
            col  = self._hovered_cell % 3
            row  = self._hovered_cell // 3
            cell_rect = QRect(r.x() + col * cw, r.y() + row * ch, cw, ch)
            painter.fillRect(cell_rect, QColor(0, 122, 255, 60))
            pen2 = QPen(QColor(0, 122, 255))
            pen2.setWidth(2)
            painter.setPen(pen2)
            painter.drawRect(cell_rect)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(
                cell_rect,
                Qt.AlignmentFlag.AlignCenter,
                f"#{self._hovered_cell + 1}",
            )
        painter.end()

    def mouseMoveEvent(self, event) -> None:
        cell = self._cell_at(event.pos())
        if cell != self._hovered_cell:
            self._hovered_cell = cell
            self.setCursor(
                QCursor(Qt.CursorShape.PointingHandCursor)
                if cell >= 0
                else QCursor(Qt.CursorShape.ArrowCursor)
            )
            self.update()

    def leaveEvent(self, _event) -> None:
        self._hovered_cell = -1
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            cell = self._cell_at(event.pos())
            if cell >= 0:
                self.cell_clicked.emit(cell)


# ---------------------------------------------------------------------------
# Proto: upscale confirmation dialog
# ---------------------------------------------------------------------------

class UpscaleConfirmDialog(QDialog):
    """Dialog shown when the user clicks a mosaic cell.

    Displays the cropped cell preview alongside the mosaic prompt, lets the
    user choose an output size, then confirms or cancels the upscale.

    Signals
    -------
    upscale_confirmed(crop_path, image_size): emitted on confirmation.
    """

    upscale_confirmed = pyqtSignal(str, str)

    def __init__(
        self,
        crop_path: str,
        mosaic_prompt: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Upscale cell")
        self.setMinimumWidth(600)
        layout = QHBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Left: cropped cell preview
        preview_lbl = QLabel()
        pix = QPixmap(crop_path)
        if not pix.isNull():
            pix = pix.scaled(
                280, 280,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        preview_lbl.setPixmap(pix)
        preview_lbl.setFixedSize(280, 280)
        preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(preview_lbl)

        # Right: prompt + size + buttons
        right_v = QVBoxLayout()

        prompt_lbl = QLabel("Mosaic prompt:")
        prompt_lbl.setStyleSheet("font-weight: bold; font-size: 11px;")
        right_v.addWidget(prompt_lbl)

        prompt_text = QTextEdit()
        prompt_text.setReadOnly(True)
        prompt_text.setPlainText(mosaic_prompt)
        prompt_text.setFixedHeight(160)
        right_v.addWidget(prompt_text)

        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Size:"))
        self._size_combo = QComboBox()
        self._size_combo.addItems(["1K", "2K", "4K"])
        self._size_combo.setCurrentText("4K")
        size_row.addWidget(self._size_combo)
        size_row.addStretch()
        right_v.addLayout(size_row)

        right_v.addStretch()

        btn_row = QHBoxLayout()
        upscale_btn = QPushButton("⬆  Upscale")
        upscale_btn.setFixedHeight(34)
        cancel_btn  = QPushButton("Cancel")
        upscale_btn.clicked.connect(lambda: self._confirm(crop_path))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(upscale_btn)
        btn_row.addWidget(cancel_btn)
        right_v.addLayout(btn_row)

        layout.addLayout(right_v)

    def _confirm(self, crop_path: str) -> None:
        self.upscale_confirmed.emit(crop_path, self._size_combo.currentText())
        self.accept()


# ---------------------------------------------------------------------------
# Drop-target input area
# ---------------------------------------------------------------------------

class DropFolderWidget(QGroupBox):
    """QGroupBox that accepts drag-and-drop of folders and image files.

    Signals
    -------
    folder_dropped(path): emitted when a directory is dropped.
    image_dropped(path):  emitted when a supported image file is dropped.
    """

    folder_dropped = pyqtSignal(str)
    image_dropped  = pyqtSignal(str)

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            url  = event.mimeData().urls()[0]
            path = url.toLocalFile()
            if url.isLocalFile() and (
                os.path.isdir(path) or path.lower().endswith(IMAGE_EXTS)
            ):
                event.acceptProposedAction()
                self.setStyleSheet(
                    "QGroupBox { border: 2px solid #007AFF; border-radius: 4px; }"
                )
                return
        event.ignore()

    def dragLeaveEvent(self, _event) -> None:
        self.setStyleSheet("")

    def dropEvent(self, event: QDropEvent) -> None:
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isdir(path):
                self.folder_dropped.emit(path)
                event.acceptProposedAction()
            elif path.lower().endswith(IMAGE_EXTS):
                self.image_dropped.emit(path)
                event.acceptProposedAction()


# ---------------------------------------------------------------------------
# Proto: result dialog (mosaic viewer + cell click → upscale)
# ---------------------------------------------------------------------------

class ProtoResultDialog(QDialog):
    """Modal dialog showing the full mosaic with interactive cell selection.

    Clicking a cell opens ``UpscaleConfirmDialog``; confirming re-emits
    ``upscale_requested`` so the caller can launch an upscale job.
    """

    upscale_requested = pyqtSignal(str, str)   # (crop_path, image_size)

    def __init__(
        self,
        output_dir: str,
        mosaic_prompt: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._output_dir    = output_dir
        self._mosaic_prompt = mosaic_prompt
        self._mosaic_path: str | None = None
        self.setWindowTitle("Proto — mosaic viewer")
        self.setMinimumSize(700, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Folder link header
        header = QHBoxLayout()
        open_btn = QPushButton(output_dir)
        open_btn.setFlat(True)
        open_btn.setStyleSheet(
            "QPushButton { color: grey; font-size: 11px; text-align: left;"
            "  text-decoration: underline; border: none; padding: 0; }"
            "QPushButton:hover { color: #333; }"
        )
        open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_btn.clicked.connect(lambda: subprocess.run(["open", output_dir]))
        header.addWidget(open_btn, stretch=1)
        layout.addLayout(header)

        # Mosaic cell widget inside a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._mosaic_widget = MosaicCellWidget()
        self._mosaic_widget.cell_clicked.connect(self._on_cell_clicked)
        scroll.setWidget(self._mosaic_widget)
        layout.addWidget(scroll, stretch=1)

        hint = QLabel("Click a cell to upscale it  •  hover to highlight")
        hint.setStyleSheet("color: grey; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self._load_mosaic()

    def _load_mosaic(self) -> None:
        if not os.path.isdir(self._output_dir):
            return
        files = sorted([
            os.path.join(self._output_dir, f)
            for f in os.listdir(self._output_dir)
            if f.lower().endswith(IMAGE_EXTS) and "_cell" not in f
        ])
        if files:
            self._mosaic_path = files[0]
            pix = QPixmap(self._mosaic_path)
            if not pix.isNull():
                self._mosaic_widget.set_pixmap(pix)

    def _on_cell_clicked(self, cell_idx: int) -> None:
        if self._mosaic_path is None:
            return
        stem = Path(self._mosaic_path).stem
        ext  = Path(self._mosaic_path).suffix
        dst  = os.path.join(
            self._output_dir, f"{stem}_cell{cell_idx + 1}{ext}"
        )
        if not _crop_mosaic_cell(self._mosaic_path, cell_idx, dst):
            return
        dlg = UpscaleConfirmDialog(dst, self._mosaic_prompt, self)
        dlg.upscale_confirmed.connect(self.upscale_requested)
        dlg.exec()


# ---------------------------------------------------------------------------
# Proto: job card
# ---------------------------------------------------------------------------

class ProtoJobCard(QFrame):
    """Compact card for a proto run shown in ProtoWindow's job list.

    Layout::

        ┌──────────────────────────────────────────┐
        │ Proto · <filename>           [thumbnail] │
        │ [progress bar]                           │
        │ <status>                                 │
        └──────────────────────────────────────────┘

    The card becomes clickable once the run completes.
    """

    open_result_requested = pyqtSignal(str, str)   # (output_dir, mosaic_prompt)

    def __init__(self, config: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config     = config
        self._output_dir: str | None = None
        self._is_done    = False
        self._worker: ProtoWorker | None = None
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 8, 10, 8)

        # Title + thumbnail row
        top_row = QHBoxLayout()
        fname   = os.path.basename(config['image_path'])
        self.title_lbl = QLabel(f"<b>Proto</b>  ·  {fname}")
        top_row.addWidget(self.title_lbl, stretch=1)
        self._thumb_lbl = QLabel()
        self._thumb_lbl.setFixedSize(80, 80)
        self._thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb_lbl.setStyleSheet("background: #f0f0f0; border-radius: 4px;")
        top_row.addWidget(self._thumb_lbl)
        layout.addLayout(top_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%v / %m")
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Status
        self.status_lbl = QLabel("Starting…")
        self.status_lbl.setStyleSheet("color: grey; font-size: 11px;")
        layout.addWidget(self.status_lbl)

    def set_output_dir(self, output_dir: str) -> None:
        self._output_dir = output_dir

    def update_progress(self, current: int, total: int, filename: str) -> None:
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_lbl.setText(f"Processing: {os.path.basename(filename)}")

    def mark_done(self, output_dir: str) -> None:
        self._output_dir = output_dir
        self._is_done    = True
        self.progress_bar.setValue(self.progress_bar.maximum() or 1)
        self.status_lbl.setText("✓  Done — click to view mosaic")
        self.status_lbl.setStyleSheet("color: green; font-size: 11px;")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Click to view mosaic")
        self._load_thumbnail(output_dir)

    def mark_error(self, message: str) -> None:
        self.status_lbl.setText(f"✗  {message}")
        self.status_lbl.setStyleSheet("color: red; font-size: 11px;")

    def _load_thumbnail(self, output_dir: str) -> None:
        if not os.path.isdir(output_dir):
            return
        files = sorted([
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.lower().endswith(IMAGE_EXTS) and "_cell" not in f
        ])
        if files:
            pix = QPixmap(files[0])
            if not pix.isNull():
                pix = pix.scaled(
                    78, 78,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._thumb_lbl.setPixmap(pix)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._is_done and self._output_dir:
            self.open_result_requested.emit(
                self._output_dir, self._config['prompt']
            )


# ---------------------------------------------------------------------------
# Proto window
# ---------------------------------------------------------------------------

class ProtoWindow(QMainWindow):
    """Standalone window for rapid 3×3 mosaic prototyping.

    Workflow
    --------
    1. Drop an image (or browse).
    2. Type a concept and click "✦ Generate" (or write the mosaic prompt directly).
    3. Click "▶ Run Proto" → ProtoWorker generates a 3×3 mosaic.
    4. Click the resulting ProtoJobCard → ProtoResultDialog opens.
    5. Click any mosaic cell → UpscaleConfirmDialog → upscale job runs.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Svelda — Prototype Mode")
        self.setMinimumSize(920, 680)

        self._image_path: str | None = None
        self._gen_worker: MosaicPromptGeneratorWorker | None = None

        self._build_ui()
        self._restore_proto_history()

    # ── UI construction ─────────────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_row = QHBoxLayout(central)
        main_row.setSpacing(12)
        main_row.setContentsMargins(16, 16, 16, 16)

        # ── Left panel ──────────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(310)
        left_v = QVBoxLayout(left)
        left_v.setSpacing(10)
        left_v.setContentsMargins(0, 0, 0, 0)

        # Drop target
        self._drop_widget = DropImageWidget(
            "Input image  —  drag & drop or browse"
        )
        self._drop_widget.image_dropped.connect(self._set_image)
        drop_v = QVBoxLayout(self._drop_widget)

        self._path_lbl = QLabel("No image selected")
        self._path_lbl.setWordWrap(True)
        self._path_lbl.setStyleSheet("color: grey; font-size: 11px;")
        drop_v.addWidget(self._path_lbl)

        self._img_preview = QLabel()
        self._img_preview.setFixedSize(200, 200)
        self._img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_preview.setStyleSheet("background: #f0f0f0; border-radius: 4px;")
        drop_v.addWidget(self._img_preview, alignment=Qt.AlignmentFlag.AlignHCenter)

        browse_btn = QPushButton("Browse image…")
        browse_btn.clicked.connect(self._browse_image)
        drop_v.addWidget(browse_btn)
        left_v.addWidget(self._drop_widget)

        # Mosaic concept group
        concept_group = QGroupBox("Mosaic Concept")
        concept_v = QVBoxLayout(concept_group)

        gen_row = QHBoxLayout()
        self._concept_edit = QLineEdit()
        self._concept_edit.setPlaceholderText("e.g. cat food cans on kitchen counter")
        gen_row.addWidget(self._concept_edit, stretch=1)
        self._gen_btn = QPushButton("✦ Generate")
        self._gen_btn.setFixedWidth(90)
        self._gen_btn.clicked.connect(self._generate_mosaic_prompt)
        gen_row.addWidget(self._gen_btn)
        concept_v.addLayout(gen_row)

        self._gen_status_lbl = QLabel("")
        self._gen_status_lbl.setStyleSheet("color: grey; font-size: 11px;")
        self._gen_status_lbl.hide()
        concept_v.addWidget(self._gen_status_lbl)

        self._prompt_text = QTextEdit()
        self._prompt_text.setPlaceholderText(
            "Mosaic prompt will appear here — or type your own…"
        )
        self._prompt_text.setFixedHeight(140)
        concept_v.addWidget(self._prompt_text)
        left_v.addWidget(concept_group)

        # Size + run
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Size:"))
        self._size_combo = QComboBox()
        self._size_combo.addItems(["1K", "2K", "4K"])
        self._size_combo.setCurrentText("2K")
        self._size_combo.setFixedWidth(64)
        size_row.addWidget(self._size_combo)
        size_row.addStretch()
        left_v.addLayout(size_row)

        run_btn = QPushButton("▶  Run Proto")
        run_btn.setFixedHeight(38)
        f = run_btn.font()
        f.setPointSize(12)
        run_btn.setFont(f)
        run_btn.clicked.connect(self._run_proto)
        left_v.addWidget(run_btn)

        left_v.addStretch()
        main_row.addWidget(left)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setFrameShadow(QFrame.Shadow.Sunken)
        main_row.addWidget(div)

        # ── Right panel: jobs ────────────────────────────────────────────
        right   = QWidget()
        right_v = QVBoxLayout(right)
        right_v.setSpacing(8)
        right_v.setContentsMargins(0, 0, 0, 0)

        jobs_header = QHBoxLayout()
        jobs_title  = QLabel("<b>Proto Jobs</b>  —  click card to view mosaic")
        jobs_header.addWidget(jobs_title, stretch=1)
        clear_btn = QPushButton("Clear history")
        clear_btn.setFlat(True)
        clear_btn.setStyleSheet(
            "QPushButton { color: grey; font-size: 11px;"
            "  text-decoration: underline; border: none; }"
        )
        clear_btn.clicked.connect(self._clear_proto_history)
        jobs_header.addWidget(clear_btn)

        jobs_group = QGroupBox()
        jobs_v = QVBoxLayout(jobs_group)
        jobs_v.setContentsMargins(6, 6, 6, 6)
        jobs_v.setSpacing(4)
        jobs_v.addLayout(jobs_header)

        self._jobs_scroll    = QScrollArea()
        self._jobs_scroll.setWidgetResizable(True)
        self._jobs_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._jobs_container = QWidget()
        self.jobs_layout     = QVBoxLayout(self._jobs_container)
        self.jobs_layout.setSpacing(8)
        self.jobs_layout.setContentsMargins(0, 0, 0, 0)
        self.jobs_layout.addStretch()
        self._jobs_scroll.setWidget(self._jobs_container)
        jobs_v.addWidget(self._jobs_scroll)
        right_v.addWidget(jobs_group, stretch=1)

        main_row.addWidget(right, stretch=1)

    # ── Image selection ─────────────────────────────────────────────────

    def _browse_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select image", "",
            "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self._set_image(path)

    def _set_image(self, path: str) -> None:
        self._image_path = path
        self._path_lbl.setText(os.path.basename(path))
        self._path_lbl.setStyleSheet("color: black; font-size: 11px;")
        pix = QPixmap(path)
        if not pix.isNull():
            pix = pix.scaled(
                198, 198,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._img_preview.setPixmap(pix)

    # ── Prompt generation ────────────────────────────────────────────────

    def _generate_mosaic_prompt(self) -> None:
        concept = self._concept_edit.text().strip()
        if not concept:
            return
        self._gen_btn.setEnabled(False)
        self._gen_status_lbl.setText("Generating…")
        self._gen_status_lbl.show()
        self._gen_worker = MosaicPromptGeneratorWorker(concept)
        self._gen_worker.result.connect(self._on_prompt_generated)
        self._gen_worker.error.connect(self._on_prompt_error)
        self._gen_worker.start()

    def _on_prompt_generated(self, text: str) -> None:
        self._prompt_text.setPlainText(text)
        self._gen_status_lbl.hide()
        self._gen_btn.setEnabled(True)

    def _on_prompt_error(self, msg: str) -> None:
        self._gen_status_lbl.setText(f"Error: {msg}")
        self._gen_btn.setEnabled(True)

    # ── Run ─────────────────────────────────────────────────────────────

    def _run_proto(self) -> None:
        if not self._image_path:
            return
        prompt = self._prompt_text.toPlainText().strip()
        if not prompt:
            return
        ts       = datetime.now().strftime("%H%M%S")
        run_code = f"proto_{ts}"
        config   = {
            'image_path': self._image_path,
            'prompt':     prompt,
            'image_size': self._size_combo.currentText(),
            'run_code':   run_code,
        }
        self._launch_proto_job(config)
        self._append_proto_history(config)

    def _launch_proto_job(self, config: dict) -> None:
        card = ProtoJobCard(config)
        card.open_result_requested.connect(self._open_result_dialog)
        self.jobs_layout.insertWidget(self.jobs_layout.count() - 1, card)
        self._jobs_scroll.verticalScrollBar().setValue(
            self._jobs_scroll.verticalScrollBar().maximum()
        )

        worker = ProtoWorker(
            config['image_path'],
            config['prompt'],
            config['image_size'],
            config['run_code'],
        )
        card._worker = worker
        worker.output_known.connect(card.set_output_dir)
        worker.progress.connect(card.update_progress)
        worker.finished.connect(card.mark_done)
        worker.error.connect(card.mark_error)
        worker.start()

    # ── Result dialog ────────────────────────────────────────────────────

    def _open_result_dialog(self, output_dir: str, mosaic_prompt: str) -> None:
        dlg = ProtoResultDialog(output_dir, mosaic_prompt, self)
        dlg.upscale_requested.connect(self._launch_upscale_job)
        dlg.exec()

    # ── Upscale job ──────────────────────────────────────────────────────

    def _launch_upscale_job(self, crop_path: str, image_size: str) -> None:
        config = {
            'path':       [crop_path],
            'is_folder':  False,
            'prompt_key': 'UPSCALE',
            'image_size': image_size,
            'replace':    True,
        }
        card = JobCard(config)
        self.jobs_layout.insertWidget(self.jobs_layout.count() - 1, card)
        self._jobs_scroll.verticalScrollBar().setValue(
            self._jobs_scroll.verticalScrollBar().maximum()
        )

        worker = Worker(
            path=[crop_path],
            is_folder=False,
            prompt_key='UPSCALE',
            image_size=image_size,
            replace=True,
        )
        card._worker = worker
        worker.output_known.connect(card.set_output_dir)
        worker.progress.connect(card.update_progress)
        worker.finished.connect(card.mark_done)
        worker.error.connect(card.mark_error)
        worker.start()

    # ── History ──────────────────────────────────────────────────────────

    def _append_proto_history(self, config: dict) -> None:
        items = _load_proto_history()
        items.append(config)
        _save_proto_history(items)

    def _restore_proto_history(self) -> None:
        for config in _load_proto_history():
            card = ProtoJobCard(config)
            card.open_result_requested.connect(self._open_result_dialog)
            output_dir = os.path.join(
                os.path.dirname(config['image_path']), config['run_code']
            )
            if os.path.isdir(output_dir):
                card.mark_done(output_dir)
            self.jobs_layout.insertWidget(self.jobs_layout.count() - 1, card)

    def _clear_proto_history(self) -> None:
        _save_proto_history([])
        while self.jobs_layout.count() > 1:
            item = self.jobs_layout.itemAt(0)
            if item is None:
                break
            card   = item.widget()
            worker = getattr(card, '_worker', None)
            if worker is None or not worker.isRunning():
                card.deleteLater()
                self.jobs_layout.removeItem(item)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class SveldaApp(QMainWindow):
    """Top-level application window containing Run and Prompts tabs."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Svelda")
        self.setMinimumSize(960, 700)

        # Selection state: folder path string, or list of file paths
        self._selection_path: str | list[str] | None = None
        self._selection_is_folder = True

        # Prompts tab state
        self._editing_new_prompt = False
        self._pre_generate_state: dict | None = None
        self._generate_worker: PromptGeneratorWorker | None = None

        # Proto window (lazily created)
        self._proto_window: ProtoWindow | None = None

        self._build_ui()
        self._restore_job_history()

    # ── Top-level layout (tabs) ─────────────────────────────────────────

    def _build_ui(self) -> None:
        """Construct the tab widget and populate each tab."""
        tabs = QTabWidget()
        self.setCentralWidget(tabs)
        tabs.addTab(self._build_run_tab(),     "Run")
        tabs.addTab(self._build_prompts_tab(), "Prompts")

    # ── Run tab ────────────────────────────────────────────────────────

    def _build_run_tab(self) -> QWidget:
        """Build and return the Run tab widget."""
        tab      = QWidget()
        main_row = QHBoxLayout(tab)
        main_row.setSpacing(12)
        main_row.setContentsMargins(16, 16, 16, 16)

        # ── Left panel: input + prompt selector + options + run buttons ──
        left = QWidget()
        left.setFixedWidth(272)
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 0, 0)

        input_group = DropFolderWidget("Input  —  drag & drop a folder or image here")
        input_group.folder_dropped.connect(self._set_folder)
        input_group.image_dropped.connect(self._set_image_from_drop)
        input_v = QVBoxLayout(input_group)
        self.path_label = QLabel("No folder selected")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: grey; font-size: 11px;")
        self.path_label.setMaximumHeight(40)
        input_v.addWidget(self.path_label)
        folder_btn = QPushButton("📁  Browse folder…")
        folder_btn.clicked.connect(self._browse_folder)
        input_v.addWidget(folder_btn)
        left_layout.addWidget(input_group)

        left_layout.addWidget(self._build_prompt_radio_group())

        opts_row = QHBoxLayout()
        opts_row.addWidget(QLabel("Size:"))
        self.size_combo = QComboBox()
        self.size_combo.addItems(["1K", "2K", "4K"])
        self.size_combo.setFixedWidth(64)
        opts_row.addWidget(self.size_combo)
        opts_row.addSpacing(8)
        self.replace_check = QCheckBox("Replace existing")
        opts_row.addWidget(self.replace_check)
        opts_row.addStretch()
        left_layout.addLayout(opts_row)

        self.run_btn = QPushButton("▶  Run")
        self.run_btn.setFixedHeight(38)
        f = self.run_btn.font()
        f.setPointSize(12)
        self.run_btn.setFont(f)
        self.run_btn.clicked.connect(self._run)
        left_layout.addWidget(self.run_btn)

        self.test_btn = QPushButton("▶  Test on 1 image")
        self.test_btn.setStyleSheet("QPushButton { color: #555; font-size: 12px; }")
        self.test_btn.setToolTip("Process only the first image to preview the result")
        self.test_btn.clicked.connect(self._run_test)
        left_layout.addWidget(self.test_btn)

        proto_btn = QPushButton("⊞  Prototype Mode")
        proto_btn.setStyleSheet("QPushButton { color: #555; font-size: 11px; }")
        proto_btn.setToolTip("Open prototyping mode — generate 9-variant mosaics")
        proto_btn.clicked.connect(self._open_proto_window)
        left_layout.addWidget(proto_btn)

        store_btn = QPushButton("🛒  Store")
        store_btn.setStyleSheet("QPushButton { color: #555; font-size: 11px; }")
        store_btn.setToolTip("Open Svelda store in browser")
        store_btn.clicked.connect(self._open_store)
        left_layout.addWidget(store_btn)

        admin_btn = QPushButton("⚙️  Shopify Admin")
        admin_btn.setStyleSheet("QPushButton { color: #555; font-size: 11px; }")
        admin_btn.setToolTip("Open Shopify Admin in browser")
        admin_btn.clicked.connect(self._open_admin)
        left_layout.addWidget(admin_btn)

        preview_btn = QPushButton("🚀  Local Preview")
        preview_btn.setStyleSheet("QPushButton { color: #555; font-size: 11px; }")
        preview_btn.setToolTip("Open local Shopify preview (http://127.0.0.1:9292)")
        preview_btn.clicked.connect(self._open_local_preview)
        left_layout.addWidget(preview_btn)

        folder_btn = QPushButton("📁  Theme Folder")
        folder_btn.setStyleSheet("QPushButton { color: #555; font-size: 11px; }")
        folder_btn.setToolTip("Open theme folder in Finder")
        folder_btn.clicked.connect(self._open_theme_folder)
        left_layout.addWidget(folder_btn)

        left_layout.addStretch()
        main_row.addWidget(left)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setFrameShadow(QFrame.Shadow.Sunken)
        main_row.addWidget(div)

        # ── Right panel: preview strip + jobs list ──
        right        = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)

        preview_group = QGroupBox("Preview  —  click to select single image  •  hover for preview")
        preview_v     = QVBoxLayout(preview_group)
        preview_v.setContentsMargins(6, 6, 6, 6)
        self.thumb_strip = SelectableThumbnailStrip()
        self.thumb_strip.selection_changed.connect(self._on_thumb_selection)
        preview_v.addWidget(self.thumb_strip)
        right_layout.addWidget(preview_group)

        # Jobs header: title label + "Clear history" link
        jobs_header = QHBoxLayout()
        jobs_title  = QLabel("<b>Jobs</b>  —  click a card to view results")
        jobs_header.addWidget(jobs_title, stretch=1)
        clear_btn = QPushButton("Clear history")
        clear_btn.setFlat(True)
        clear_btn.setStyleSheet(
            "QPushButton { color: grey; font-size: 11px; text-decoration: underline; border: none; }"
        )
        clear_btn.clicked.connect(self._clear_history)
        jobs_header.addWidget(clear_btn)

        jobs_group = QGroupBox()
        jobs_v     = QVBoxLayout(jobs_group)
        jobs_v.setContentsMargins(6, 6, 6, 6)
        jobs_v.setSpacing(4)
        jobs_v.addLayout(jobs_header)

        self.jobs_scroll    = QScrollArea()
        self.jobs_scroll.setWidgetResizable(True)
        self.jobs_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.jobs_container = QWidget()
        self.jobs_layout    = QVBoxLayout(self.jobs_container)
        self.jobs_layout.setSpacing(8)
        self.jobs_layout.setContentsMargins(0, 0, 0, 0)
        self.jobs_layout.addStretch()
        self.jobs_scroll.setWidget(self.jobs_container)
        jobs_v.addWidget(self.jobs_scroll)
        right_layout.addWidget(jobs_group, stretch=1)

        main_row.addWidget(right, stretch=1)
        return tab

    def _open_proto_window(self) -> None:
        """Open (or raise) the standalone Prototype Mode window."""
        if self._proto_window is None or not self._proto_window.isVisible():
            self._proto_window = ProtoWindow()
        self._proto_window.show()
        self._proto_window.raise_()
        self._proto_window.activateWindow()

    def _build_prompt_radio_group(self) -> QGroupBox:
        """Build the scrollable prompt-selection radio group for the Run tab."""
        prompt_group        = QGroupBox("Prompt")
        prompt_group_layout = QVBoxLayout(prompt_group)
        prompt_scroll       = QScrollArea()
        prompt_scroll.setWidgetResizable(True)
        prompt_scroll.setFrameShape(QFrame.Shape.NoFrame)
        prompt_scroll.setFixedHeight(210)
        self._prompt_inner = QWidget()
        self._prompt_v     = QVBoxLayout(self._prompt_inner)
        self._prompt_v.setSpacing(2)
        self._prompt_v.setContentsMargins(0, 0, 0, 0)
        prompt_scroll.setWidget(self._prompt_inner)
        prompt_group_layout.addWidget(prompt_scroll)
        self.prompt_buttons = QButtonGroup(self)
        self._rebuild_prompt_radio_buttons()
        return prompt_group

    def _rebuild_prompt_radio_buttons(self, select_key: str = "NEUTRAL_WHITE_FRAMING") -> None:
        """Repopulate the prompt radio buttons from the current PROMPT_LABELS registry."""
        for btn in list(self.prompt_buttons.buttons()):
            self.prompt_buttons.removeButton(btn)
        while self._prompt_v.count():
            child = self._prompt_v.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        for key, label in PROMPT_LABELS.items():
            rb = QRadioButton(label)
            rb.setProperty("prompt_key", key)
            rb.setToolTip(_prompt_tooltip(key))
            self.prompt_buttons.addButton(rb)
            self._prompt_v.addWidget(rb)
            if key == select_key:
                rb.setChecked(True)
        # Ensure at least one button is always checked
        if not self.prompt_buttons.checkedButton():
            btns = self.prompt_buttons.buttons()
            if btns:
                btns[0].setChecked(True)

    # ── Prompts tab ────────────────────────────────────────────────────

    def _build_prompts_tab(self) -> QWidget:
        """Build and return the Prompts tab widget."""
        tab    = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Left column: prompt list + New button ──
        left   = QWidget()
        left.setFixedWidth(230)
        left_v = QVBoxLayout(left)
        left_v.setContentsMargins(0, 0, 0, 0)
        left_v.setSpacing(8)

        new_btn = QPushButton("+ New prompt")
        new_btn.clicked.connect(self._new_custom_prompt)
        left_v.addWidget(new_btn)

        self.prompt_list_widget = QListWidget()
        self.prompt_list_widget.currentItemChanged.connect(
            lambda cur, _: self._on_prompt_list_select(cur)
        )
        left_v.addWidget(self.prompt_list_widget, stretch=1)
        layout.addWidget(left)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(div)

        # ── Right column: editor form + AI generator ──
        right   = QWidget()
        right_v = QVBoxLayout(right)
        right_v.setContentsMargins(0, 0, 0, 0)
        right_v.setSpacing(8)

        form = QGridLayout()
        form.setSpacing(8)
        form.setColumnMinimumWidth(0, 72)
        form.setColumnStretch(1, 1)

        form.addWidget(QLabel("Nickname:"), 0, 0)
        self.edit_nickname = QLineEdit()
        self.edit_nickname.setPlaceholderText("Display name in Run tab")
        self.edit_nickname.textChanged.connect(self._auto_update_key)
        form.addWidget(self.edit_nickname, 0, 1)

        form.addWidget(QLabel("Key:"), 1, 0)
        self.edit_key = QLineEdit()
        self.edit_key.setPlaceholderText("AUTO_GENERATED")
        form.addWidget(self.edit_key, 1, 1)

        form.addWidget(QLabel("Prompt:"), 2, 0, Qt.AlignmentFlag.AlignTop)
        self.edit_text = QTextEdit()
        self.edit_text.setPlaceholderText("Enter prompt text…")
        form.addWidget(self.edit_text, 2, 1)
        form.setRowStretch(2, 1)

        right_v.addLayout(form, stretch=1)

        self.edit_builtin_note = QLabel("Built-in prompt — text is read-only. You can rename it.")
        self.edit_builtin_note.setStyleSheet("color: grey; font-size: 11px;")
        self.edit_builtin_note.hide()
        right_v.addWidget(self.edit_builtin_note)

        # Save / Delete buttons (shown during normal editing)
        self.prompt_btn_row    = QWidget()
        btn_row                = QHBoxLayout(self.prompt_btn_row)
        btn_row.setContentsMargins(0, 0, 0, 0)
        self.prompt_save_btn   = QPushButton("Save")
        self.prompt_save_btn.clicked.connect(self._save_prompt_edit)
        self.prompt_delete_btn = QPushButton("Delete")
        self.prompt_delete_btn.setStyleSheet("QPushButton { color: red; }")
        self.prompt_delete_btn.clicked.connect(self._delete_custom_prompt)
        btn_row.addWidget(self.prompt_save_btn)
        btn_row.addWidget(self.prompt_delete_btn)
        btn_row.addStretch()
        right_v.addWidget(self.prompt_btn_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        right_v.addWidget(sep)

        # AI generator section
        gen_group = QGroupBox("Generate with AI")
        gen_v     = QVBoxLayout(gen_group)
        gen_v.setSpacing(6)

        gen_input_row = QHBoxLayout()
        self.gen_input = QLineEdit()
        self.gen_input.setPlaceholderText(
            'Describe what you want, e.g. "moody black background with rim lighting"'
        )
        self.gen_input.returnPressed.connect(self._generate_prompt)
        gen_input_row.addWidget(self.gen_input, stretch=1)
        self.gen_btn = QPushButton("✦  Generate")
        self.gen_btn.setFixedWidth(108)
        self.gen_btn.clicked.connect(self._generate_prompt)
        gen_input_row.addWidget(self.gen_btn)
        gen_v.addLayout(gen_input_row)

        self.gen_status_lbl = QLabel("")
        self.gen_status_lbl.setStyleSheet("color: grey; font-size: 11px;")
        self.gen_status_lbl.hide()
        gen_v.addWidget(self.gen_status_lbl)
        right_v.addWidget(gen_group)

        # Accept / Decline row (shown while reviewing an AI-generated prompt)
        self.accept_row_widget = QWidget()
        self.accept_row_widget.hide()
        accept_row  = QHBoxLayout(self.accept_row_widget)
        accept_row.setContentsMargins(0, 0, 0, 0)
        accept_btn  = QPushButton("✓  Accept")
        accept_btn.setStyleSheet("QPushButton { color: green; font-weight: bold; }")
        accept_btn.clicked.connect(self._accept_generated)
        decline_btn = QPushButton("✗  Decline")
        decline_btn.setStyleSheet("QPushButton { color: #cc3300; }")
        decline_btn.clicked.connect(self._decline_generated)
        accept_note = QLabel("Generated by AI — review before saving")
        accept_note.setStyleSheet("color: grey; font-size: 11px; font-style: italic;")
        accept_row.addWidget(accept_btn)
        accept_row.addWidget(decline_btn)
        accept_row.addSpacing(10)
        accept_row.addWidget(accept_note)
        accept_row.addStretch()
        right_v.addWidget(self.accept_row_widget)

        layout.addWidget(right, stretch=1)

        self._populate_prompt_list()
        return tab

    def _populate_prompt_list(self) -> None:
        """Repopulate the left-side list of all prompts (built-in + custom)."""
        self.prompt_list_widget.clear()
        for key in _BUILTIN_KEYS_ORDERED:
            label = PROMPT_LABELS.get(key, key)
            item  = QListWidgetItem(f"{label}  ·  built-in")
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setForeground(QColor("#999"))
            self.prompt_list_widget.addItem(item)
        data = _load_custom_data()
        for key in data.get("custom_prompts", {}):
            label = PROMPT_LABELS.get(key, key)
            item  = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.prompt_list_widget.addItem(item)

    def _on_prompt_list_select(self, current: QListWidgetItem | None) -> None:
        """Populate the editor form when a prompt is selected in the list."""
        if self.accept_row_widget.isVisible():
            self._decline_generated()
        if current is None:
            return
        self._editing_new_prompt = False
        key        = current.data(Qt.ItemDataRole.UserRole)
        is_builtin = key in _BUILTIN_KEYS

        self.edit_nickname.blockSignals(True)
        self.edit_nickname.setText(PROMPT_LABELS.get(key, key))
        self.edit_nickname.blockSignals(False)

        self.edit_key.setText(key)
        self.edit_key.setReadOnly(True)

        if is_builtin:
            self.edit_text.setPlainText(_get_builtin_text(key))
            self.edit_text.setReadOnly(True)
            self.edit_builtin_note.show()
            self.prompt_delete_btn.hide()
        else:
            data = _load_custom_data()
            text = data.get("custom_prompts", {}).get(key, {}).get("text", "")
            self.edit_text.setPlainText(text)
            self.edit_text.setReadOnly(False)
            self.edit_builtin_note.hide()
            self.prompt_delete_btn.show()

    def _new_custom_prompt(self) -> None:
        """Clear the editor and prepare it for a new custom prompt."""
        if self.accept_row_widget.isVisible():
            self._decline_generated()
        self._editing_new_prompt = True
        self.prompt_list_widget.clearSelection()
        self.edit_key.setReadOnly(False)
        self.edit_text.setReadOnly(False)
        self.edit_builtin_note.hide()
        self.prompt_delete_btn.hide()

        self.edit_nickname.blockSignals(True)
        self.edit_nickname.setText("New Prompt")
        self.edit_nickname.blockSignals(False)
        self.edit_key.setText("NEW_PROMPT")
        self.edit_text.setPlainText("")
        self.edit_nickname.setFocus()
        self.edit_nickname.selectAll()

    def _auto_update_key(self, text: str) -> None:
        """Auto-derive the KEY field from the nickname while creating a new prompt."""
        if self._editing_new_prompt and not self.edit_key.isReadOnly():
            key = re.sub(r'[^A-Za-z0-9 ]', '', text).upper().replace(' ', '_') or "CUSTOM"
            self.edit_key.setText(key)

    def _save_prompt_edit(self) -> None:
        """Persist the current editor content as a new or updated prompt."""
        nickname = self.edit_nickname.text().strip()
        key      = re.sub(r'\s+', '_', self.edit_key.text().strip().upper())
        if not key or not nickname:
            return

        is_builtin = key in _BUILTIN_KEYS
        data       = _load_custom_data()

        if is_builtin:
            # Built-in prompts: only the display label can be changed
            data.setdefault("label_overrides", {})[key] = nickname
            PROMPT_LABELS[key] = nickname
        else:
            text = self.edit_text.toPlainText().strip()
            data.setdefault("custom_prompts", {})[key] = {"label": nickname, "text": text}
            ALL_PROMPTS[key]         = ([text], [key])
            PROMPT_LABELS[key]       = nickname
            CUSTOM_PROMPT_TEXTS[key] = text

        _save_custom_data(data)
        self._editing_new_prompt = False
        self.edit_key.setReadOnly(True)
        self.prompt_delete_btn.show()

        current_run_key = self._selected_prompt_key() or key
        self._rebuild_prompt_radio_buttons(select_key=current_run_key)
        self._populate_prompt_list()

        # Re-select the saved item without re-triggering the selection handler
        for i in range(self.prompt_list_widget.count()):
            if self.prompt_list_widget.item(i).data(Qt.ItemDataRole.UserRole) == key:
                self.prompt_list_widget.blockSignals(True)
                self.prompt_list_widget.setCurrentRow(i)
                self.prompt_list_widget.blockSignals(False)
                break

    def _delete_custom_prompt(self) -> None:
        """Delete the currently selected custom prompt from disk and memory."""
        item = self.prompt_list_widget.currentItem()
        if item is None:
            return
        key = item.data(Qt.ItemDataRole.UserRole)
        if key in _BUILTIN_KEYS:
            return  # built-in prompts cannot be deleted

        data = _load_custom_data()
        data.get("custom_prompts", {}).pop(key, None)
        _save_custom_data(data)

        ALL_PROMPTS.pop(key, None)
        PROMPT_LABELS.pop(key, None)
        CUSTOM_PROMPT_TEXTS.pop(key, None)

        self._rebuild_prompt_radio_buttons(select_key="NEUTRAL_WHITE_FRAMING")
        self._populate_prompt_list()
        self._clear_editor()

    def _clear_editor(self) -> None:
        """Reset all editor fields to their empty/default state."""
        self._clear_pending_style()
        self.accept_row_widget.hide()
        self.prompt_btn_row.show()
        self.edit_nickname.blockSignals(True)
        self.edit_nickname.clear()
        self.edit_nickname.blockSignals(False)
        self.edit_key.clear()
        self.edit_text.clear()
        self.edit_builtin_note.hide()
        self.prompt_delete_btn.hide()

    # ── AI prompt generator ───────────────────────────────────────────

    def _generate_prompt(self) -> None:
        """Start a PromptGeneratorWorker for the current gen_input text."""
        user_input = self.gen_input.text().strip()
        if not user_input:
            return
        self.gen_btn.setEnabled(False)
        self.gen_btn.setText("Generating…")
        self.gen_status_lbl.hide()

        self._generate_worker = PromptGeneratorWorker(user_input)
        self._generate_worker.result.connect(self._on_generate_result)
        self._generate_worker.error.connect(self._on_generate_error)
        self._generate_worker.start()

    def _on_generate_result(self, data: dict) -> None:
        """Populate editor fields with the AI-generated prompt (pending style)."""
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("✦  Generate")

        # Save current form state so the user can Decline and revert
        self._pre_generate_state = {
            'nickname':      self.edit_nickname.text(),
            'key':           self.edit_key.text(),
            'text':          self.edit_text.toPlainText(),
            'key_readonly':  self.edit_key.isReadOnly(),
            'text_readonly': self.edit_text.isReadOnly(),
            'editing_new':   self._editing_new_prompt,
        }

        self._editing_new_prompt = True

        self.edit_nickname.blockSignals(True)
        self.edit_nickname.setText(data.get("nickname", ""))
        self.edit_nickname.blockSignals(False)

        key = re.sub(r'[^A-Z0-9_]', '', data.get("key", "GENERATED").upper())
        self.edit_key.setReadOnly(False)
        self.edit_key.setText(key)
        self.edit_key.setReadOnly(True)

        self.edit_text.setReadOnly(False)
        self.edit_text.setPlainText(data.get("prompt", ""))

        # Grey italic style signals "pending review" to the user
        _pending = "color: #888; font-style: italic; background: #f8f8f6;"
        self.edit_nickname.setStyleSheet(_pending)
        self.edit_key.setStyleSheet(_pending)
        self.edit_text.setStyleSheet(_pending)

        self.prompt_list_widget.clearSelection()
        self.prompt_btn_row.hide()
        self.accept_row_widget.show()

    def _on_generate_error(self, message: str) -> None:
        """Show the generation error in the status label."""
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("✦  Generate")
        self.gen_status_lbl.setText(f"Error: {message}")
        self.gen_status_lbl.setStyleSheet("color: red; font-size: 11px;")
        self.gen_status_lbl.show()

    def _accept_generated(self) -> None:
        """Accept the AI-generated prompt and save it."""
        self._clear_pending_style()
        self.accept_row_widget.hide()
        self.prompt_btn_row.show()
        self._save_prompt_edit()
        self._pre_generate_state = None

    def _decline_generated(self) -> None:
        """Discard the AI-generated prompt and restore the previous form state."""
        self._clear_pending_style()
        self.accept_row_widget.hide()
        self.prompt_btn_row.show()

        if self._pre_generate_state:
            s = self._pre_generate_state
            self.edit_nickname.blockSignals(True)
            self.edit_nickname.setText(s['nickname'])
            self.edit_nickname.blockSignals(False)
            self.edit_key.setText(s['key'])
            self.edit_key.setReadOnly(s['key_readonly'])
            self.edit_text.setPlainText(s['text'])
            self.edit_text.setReadOnly(s['text_readonly'])
            self._editing_new_prompt = s['editing_new']
            self._pre_generate_state = None
        else:
            self._clear_editor()

    def _clear_pending_style(self) -> None:
        """Remove the grey-italic style applied during AI prompt review."""
        for w in (self.edit_nickname, self.edit_key, self.edit_text):
            w.setStyleSheet("")

    # ── Run tab — input ────────────────────────────────────────────────

    def _browse_folder(self) -> None:
        """Open a native folder picker and update the selection."""
        folder = QFileDialog.getExistingDirectory(self, "Select image folder")
        if folder:
            self._set_folder(folder)

    def _set_folder(self, folder: str) -> None:
        """Set the selection to a folder and reload the thumbnail strip."""
        self._selection_path      = folder
        self._selection_is_folder = True
        self.path_label.setText(folder)
        self.path_label.setStyleSheet("color: black; font-size: 11px;")
        files = [
            os.path.join(folder, f) for f in sorted(os.listdir(folder))
            if f.lower().endswith(IMAGE_EXTS)
        ]
        self.thumb_strip.set_folder(folder, files)

    def _set_image_from_drop(self, image_path: str) -> None:
        """Handle a dropped image by opening its parent folder and selecting it."""
        folder = os.path.dirname(image_path)
        self._set_folder(folder)
        self.thumb_strip.select_file(image_path)

    def _on_thumb_selection(self, path_or_list, is_folder: bool) -> None:
        """Sync internal selection state when the thumbnail strip changes."""
        self._selection_path      = path_or_list
        self._selection_is_folder = is_folder
        if is_folder:
            self.path_label.setText(path_or_list)
        else:
            n = len(path_or_list)
            self.path_label.setText(
                os.path.basename(path_or_list[0]) if n == 1
                else f"{n} images selected"
            )
        self.path_label.setStyleSheet("color: black; font-size: 11px;")

    def _selected_prompt_key(self) -> str | None:
        """Return the prompt key of the currently checked radio button, or None."""
        btn = self.prompt_buttons.checkedButton()
        return btn.property("prompt_key") if btn else None

    # ── Run / Test ────────────────────────────────────────────────────

    def _run(self) -> None:
        """Launch a full processing job for the current selection."""
        if not self._selection_path:
            return
        if self._selection_is_folder and not os.path.isdir(self._selection_path):
            return
        prompt_key = self._selected_prompt_key()
        if not prompt_key:
            return
        config = {
            'path':       self._selection_path,
            'is_folder':  self._selection_is_folder,
            'prompt_key': prompt_key,
            'image_size': self.size_combo.currentText(),
            'replace':    self.replace_check.isChecked(),
        }
        self._launch_job(config)

    def _run_test(self) -> None:
        """Launch a test job processing only the first image in the selection."""
        prompt_key = self._selected_prompt_key()
        if not prompt_key or not self._selection_path:
            return

        if self._selection_is_folder and os.path.isdir(self._selection_path):
            files = [
                os.path.join(self._selection_path, f)
                for f in sorted(os.listdir(self._selection_path))
                if f.lower().endswith(IMAGE_EXTS)
            ]
            if not files:
                return
            first = files[0]
        elif not self._selection_is_folder:
            first = self._selection_path[0]
        else:
            return

        config = {
            'path':       [first],
            'is_folder':  False,
            'prompt_key': prompt_key,
            'image_size': self.size_combo.currentText(),
            'replace':    self.replace_check.isChecked(),
        }
        self._launch_job(config)

    def _launch_job(self, config: dict) -> None:
        """Create a JobCard, start a Worker thread, and wire up all signals."""
        card = JobCard(config)
        card.reprocess_requested.connect(self._load_into_form)
        self.jobs_layout.insertWidget(self.jobs_layout.count() - 1, card)
        QApplication.processEvents()
        self.jobs_scroll.verticalScrollBar().setValue(
            self.jobs_scroll.verticalScrollBar().maximum()
        )
        worker = Worker(
            path=config['path'], is_folder=config['is_folder'],
            prompt_key=config['prompt_key'], image_size=config['image_size'],
            replace=config['replace'],
        )
        worker.output_known.connect(card.set_output_dir)
        worker.progress.connect(card.update_progress)
        worker.finished.connect(card.mark_done)
        worker.finished.connect(lambda out: self._notify(config, out))
        worker.finished.connect(lambda out: self._append_job_history(config, out, "done"))
        worker.error.connect(card.mark_error)
        worker.error.connect(lambda _: self._append_job_history(config, None, "error"))
        worker.start()
        card._worker = worker  # keep reference alive for the card's lifetime

    def _notify(self, config: dict, output_dir: str) -> None:
        """Send a macOS notification when a job finishes."""
        label = PROMPT_LABELS.get(config['prompt_key'], config['prompt_key'])
        subprocess.run([
            "osascript", "-e",
            f'display notification "Done: {label}" with title "Svelda" '
            f'subtitle "{os.path.basename(output_dir)}"'
        ])

    # ── Job history ────────────────────────────────────────────────────

    def _append_job_history(
        self,
        config: dict,
        output_dir: str | None,
        status: str,
    ) -> None:
        """Append a completed job entry to the on-disk history file."""
        history = _load_jobs_history()
        history.append({
            "config":     dict(config),  # shallow copy; all values are JSON-serialisable
            "output_dir": output_dir,
            "status":     status,
            "timestamp":  datetime.now().isoformat(timespec='seconds'),
        })
        _save_jobs_history(history)

    def _restore_job_history(self) -> None:
        """Recreate JobCards from the persisted history on startup."""
        for item in _load_jobs_history():
            try:
                config     = item["config"]
                output_dir = item.get("output_dir")
                status     = item.get("status", "done")

                # Normalise: folder jobs store path as a string, not a list
                if config.get("is_folder") and isinstance(config.get("path"), list):
                    config = dict(config, path=config["path"][0])

                card = JobCard(config)
                card.reprocess_requested.connect(self._load_into_form)
                self.jobs_layout.insertWidget(self.jobs_layout.count() - 1, card)

                if status == "done" and output_dir and os.path.isdir(output_dir):
                    card.set_output_dir(output_dir)
                    card.mark_done(output_dir)
                elif status == "error":
                    card.mark_error("(from previous session)")
                else:
                    card.mark_error("(session ended before completion)")
            except Exception:
                continue  # silently skip corrupt entries

    def _clear_history(self) -> None:
        """Clear the history file and remove all non-running job cards."""
        _save_jobs_history([])
        for i in reversed(range(self.jobs_layout.count() - 1)):  # skip trailing stretch
            item = self.jobs_layout.itemAt(i)
            if item and item.widget():
                card   = item.widget()
                worker = getattr(card, '_worker', None)
                if worker is None or not worker.isRunning():
                    card.deleteLater()
                    self.jobs_layout.removeItem(item)

    # ── Reprocess ─────────────────────────────────────────────────────

    def _load_into_form(self, config: dict) -> None:
        """Load a previous job's config back into the Run tab form fields."""
        if config['is_folder']:
            self._set_folder(config['path'])
        else:
            self._selection_path      = config['path']
            self._selection_is_folder = False
            n = len(config['path'])
            self.path_label.setText(f"{n} image{'s' if n != 1 else ''} selected")
            self.path_label.setStyleSheet("color: black; font-size: 11px;")
            self.thumb_strip.set_files(config['path'])

        for btn in self.prompt_buttons.buttons():
            if btn.property("prompt_key") == config['prompt_key']:
                btn.setChecked(True)
                break

        idx = self.size_combo.findText(config['image_size'])
        if idx >= 0:
            self.size_combo.setCurrentIndex(idx)
        self.replace_check.setChecked(config['replace'])

    def _open_store(self) -> None:
        """Open the Svelda public store in the default browser."""
        QDesktopServices.openUrl(QUrl("https://svelda.com"))

    def _open_admin(self) -> None:
        """Open the Svelda Shopify admin in the default browser."""
        QDesktopServices.openUrl(QUrl("https://svelda.myshopify.com/admin"))

    def _open_local_preview(self) -> None:
        """Open the local Shopify development server in the default browser."""
        QDesktopServices.openUrl(QUrl("http://127.0.0.1:9292"))

    def _open_theme_folder(self) -> None:
        """Open the Shopify theme folder in Finder."""
        theme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Website", "theme"))
        if os.path.exists(theme_path):
            subprocess.run(["open", theme_path])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("macos")
    window = SveldaApp()
    window.show()
    sys.exit(app.exec())
