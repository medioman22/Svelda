import sys
import os
import json
import re
import subprocess
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
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QCursor, QDragEnterEvent, QDropEvent, QColor

IMAGE_EXTS   = ('.png', '.jpg', '.jpeg')
THUMB_SIZE   = 88
RESULT_THUMB = 160
PREVIEW_MAX  = 400
CARD_THUMB   = 52

# ---------------------------------------------------------------------------
# Prompt registry
# ---------------------------------------------------------------------------
def _prepare(key, prompt_list):
    if len(prompt_list) > 1:
        return (["\n\n".join(prompt_list)], [key])
    return (prompt_list, [key])

ALL_PROMPTS: dict = {}
for _src in [NEUTRAL_WHITE_PROMPT, CATS_PROMPTS_STUDIO, CATS_PROMPTS_HOME, UPSCALE_PROMPT]:
    for _key, _plist in _src.items():
        ALL_PROMPTS[_key] = _prepare(_key, _plist)

# Ordered list of built-in keys (for stable display order)
_BUILTIN_KEYS_ORDERED: list = []
_BUILTIN_KEYS: set = set()
for _src in [NEUTRAL_WHITE_PROMPT, CATS_PROMPTS_STUDIO, CATS_PROMPTS_HOME, UPSCALE_PROMPT]:
    for _k in _src:
        if _k not in _BUILTIN_KEYS:
            _BUILTIN_KEYS_ORDERED.append(_k)
            _BUILTIN_KEYS.add(_k)

PROMPT_LABELS = {
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
CUSTOM_PROMPTS_FILE  = Path(__file__).parent / "custom_prompts.json"
CUSTOM_PROMPT_TEXTS: dict = {}   # key -> raw text (for tooltip lookups)


def _load_custom_data() -> dict:
    if CUSTOM_PROMPTS_FILE.exists():
        try:
            return json.loads(CUSTOM_PROMPTS_FILE.read_text())
        except Exception:
            pass
    return {"label_overrides": {}, "custom_prompts": {}}


def _save_custom_data(data: dict):
    CUSTOM_PROMPTS_FILE.write_text(json.dumps(data, indent=2))


def _apply_custom_data():
    """Merge persisted custom data into ALL_PROMPTS / PROMPT_LABELS."""
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
    for src in [NEUTRAL_WHITE_PROMPT, CATS_PROMPTS_STUDIO, CATS_PROMPTS_HOME, UPSCALE_PROMPT]:
        if key in src:
            return "\n\n".join(src[key])
    return ""


def _prompt_tooltip(key: str) -> str:
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
    result = pyqtSignal(dict)
    error  = pyqtSignal(str)

    def __init__(self, user_input: str):
        super().__init__()
        self.user_input = user_input

    def run(self):
        try:
            contents = _META_PROMPT.format(user_input=self.user_input)
            response = _gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
            )
            text = response.text.strip()
            # Strip markdown code fences if Gemini wraps the JSON anyway
            if text.startswith("```"):
                lines = text.splitlines()
                text  = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
            data = json.loads(text)
            self.result.emit(data)
        except Exception as e:
            self.error.emit(str(e))


# ---------------------------------------------------------------------------
# Hover image preview popup (singleton)
# ---------------------------------------------------------------------------
class ImagePreviewPopup(QWidget):
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
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

    def show_for(self, path: str):
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

    def _reposition(self):
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
    _DELAY_MS = 350

    def _init_hover(self):
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._show_preview)

    def enterEvent(self, event):
        if getattr(self, "path", None):
            self._hover_timer.start(self._DELAY_MS)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_timer.stop()
        ImagePreviewPopup.get().hide()
        super().leaveEvent(event)

    def _show_preview(self):
        if getattr(self, "path", None):
            ImagePreviewPopup.get().show_for(self.path)


# ---------------------------------------------------------------------------
# Worker thread (image processing)
# ---------------------------------------------------------------------------
class Worker(QThread):
    progress     = pyqtSignal(int, int, str)
    output_known = pyqtSignal(str)
    finished     = pyqtSignal(str)
    error        = pyqtSignal(str)

    def __init__(self, path, is_folder, prompt_key, image_size, replace):
        super().__init__()
        self.path       = path
        self.is_folder  = is_folder
        self.prompt_key = prompt_key
        self.image_size = image_size
        self.replace    = replace

    def run(self):
        try:
            prompts, codes = ALL_PROMPTS[self.prompt_key]

            if self.is_folder:
                output_dir = os.path.join(self.path, f"processed_{codes[0]}")
            else:
                output_dir = os.path.join(os.path.dirname(self.path[0]), codes[0])
            self.output_known.emit(output_dir)

            def on_progress(current, total, filename):
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
    clicked_signal = pyqtSignal()

    def __init__(self, path="", label_text="", parent=None):
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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked_signal.emit()

    def set_selected(self, on: bool):
        if on:
            self.setStyleSheet(
                "border: 2px solid #007AFF; border-radius: 4px; background: #ddeeff;"
            )
        else:
            self._unselect()

    def _unselect(self):
        self.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")


# ---------------------------------------------------------------------------
# Selectable thumbnail strip
# ---------------------------------------------------------------------------
class SelectableThumbnailStrip(QScrollArea):
    selection_changed = pyqtSignal(object, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setFixedHeight(THUMB_SIZE + 24)

        container = QWidget()
        self._row  = QHBoxLayout(container)
        self._row.setSpacing(6)
        self._row.setContentsMargins(4, 4, 4, 4)
        self._row.addStretch()
        self.setWidget(container)

        self._folder_path: str | None = None
        self._all_files:   list       = []
        self._buttons:     list       = []

    def set_folder(self, folder_path: str, files: list):
        self._folder_path = folder_path
        self._all_files   = files
        self._rebuild()

    def set_files(self, files: list):
        self._folder_path = None
        self._all_files   = files
        self._rebuild()

    def select_file(self, path: str):
        try:
            idx = self._all_files.index(path)
            self._on_click(idx + 1)
        except ValueError:
            pass

    def _rebuild(self):
        self._buttons.clear()
        while self._row.count() > 1:
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

    def _on_click(self, idx: int):
        self._highlight(idx)
        if idx == 0:
            if self._folder_path:
                self.selection_changed.emit(self._folder_path, True)
            else:
                self.selection_changed.emit(self._all_files, False)
        else:
            self.selection_changed.emit([self._all_files[idx - 1]], False)

    def _highlight(self, idx: int):
        for i, btn in enumerate(self._buttons):
            btn.set_selected(i == idx)


# ---------------------------------------------------------------------------
# Results dialog
# ---------------------------------------------------------------------------
class ResultImageCell(HoverPreviewMixin, QWidget):
    def __init__(self, path: str, parent=None):
        super().__init__(parent=parent)
        self.path = path
        self._init_hover()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Click to open  •  hover for preview")

        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)

        img_lbl = QLabel()
        img_lbl.setFixedSize(RESULT_THUMB, RESULT_THUMB)
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(path)
        if not pix.isNull():
            pix = pix.scaled(RESULT_THUMB, RESULT_THUMB,
                             Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
            img_lbl.setPixmap(pix)
        layout.addWidget(img_lbl)

        name_lbl = QLabel(os.path.basename(path))
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("font-size: 10px; color: grey;")
        name_lbl.setFixedWidth(RESULT_THUMB)
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            subprocess.run(["open", self.path])


class ResultsDialog(QDialog):
    def __init__(self, output_dir: str, prompt_key: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Results — {PROMPT_LABELS.get(prompt_key, prompt_key)}")
        self.setMinimumSize(600, 480)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

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
        layout.addWidget(open_folder_btn)

        scroll    = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid      = QGridLayout(container)
        grid.setSpacing(12)
        grid.setContentsMargins(8, 8, 8, 8)
        scroll.setWidget(container)

        files = []
        if os.path.isdir(output_dir):
            files = sorted([
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if f.lower().endswith(IMAGE_EXTS)
            ])

        cols = 3
        for i, path in enumerate(files):
            grid.addWidget(ResultImageCell(path), i // cols, i % cols)

        if not files:
            empty = QLabel("No output images yet.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(empty, 0, 0)

        layout.addWidget(scroll)

        hint = QLabel("Click image to open  •  hover for large preview  •  click folder path to open in Finder")
        hint.setStyleSheet("color: grey; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)


# ---------------------------------------------------------------------------
# Job card
# ---------------------------------------------------------------------------
class JobCard(QFrame):
    reprocess_requested = pyqtSignal(dict)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config       = config
        self._output_dir: str | None = None
        self._shown_files: set = set()
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 8, 10, 8)

        header = QHBoxLayout()
        label  = PROMPT_LABELS.get(config['prompt_key'], config['prompt_key'])
        src    = (os.path.basename(config['path']) if config['is_folder']
                  else f"{len(config['path'])} image{'s' if len(config['path']) != 1 else ''}")
        self.title_lbl = QLabel(f"<b>{label}</b>  ·  {src}")
        reprocess_btn  = QPushButton("↺")
        reprocess_btn.setFixedWidth(28)
        reprocess_btn.setToolTip("Load into form")
        reprocess_btn.clicked.connect(lambda: self.reprocess_requested.emit(self.config))
        header.addWidget(self.title_lbl, stretch=1)
        header.addWidget(reprocess_btn)
        layout.addLayout(header)

        body = QHBoxLayout()
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

    def set_output_dir(self, output_dir: str):
        self._output_dir = output_dir
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Click to preview results")

    def update_progress(self, current, total, filename):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_lbl.setText(f"Processing: {os.path.basename(filename)}")
        self._refresh_thumbs()

    def mark_done(self, output_dir):
        self._output_dir = output_dir
        self.progress_bar.setValue(self.progress_bar.maximum() or 1)
        self.status_lbl.setText("✓  Done — click to view results")
        self.status_lbl.setStyleSheet("color: green; font-size: 11px;")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Click to view results")
        self._refresh_thumbs()

    def mark_error(self, message):
        self.status_lbl.setText(f"✗  {message}")
        self.status_lbl.setStyleSheet("color: red; font-size: 11px;")

    def _refresh_thumbs(self):
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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._output_dir:
            self._open_results()

    def _open_results(self):
        ResultsDialog(self._output_dir, self.config['prompt_key'], self).exec()


# ---------------------------------------------------------------------------
# Drop-target input area
# ---------------------------------------------------------------------------
class DropFolderWidget(QGroupBox):
    folder_dropped = pyqtSignal(str)
    image_dropped  = pyqtSignal(str)

    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
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

    def dragLeaveEvent(self, _event):
        self.setStyleSheet("")

    def dropEvent(self, event: QDropEvent):
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
# Main window
# ---------------------------------------------------------------------------
class SveldaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Svelda")
        self.setMinimumSize(960, 700)
        self._selection_path      = None
        self._selection_is_folder = True
        self._editing_new_prompt  = False
        self._pre_generate_state  = None
        self._generate_worker     = None
        self._build_ui()

    # ── Top-level layout (tabs) ───────────────────────────────────────────

    def _build_ui(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)
        tabs.addTab(self._build_run_tab(),     "Run")
        tabs.addTab(self._build_prompts_tab(), "Prompts")

    # ── Run tab ──────────────────────────────────────────────────────────

    def _build_run_tab(self) -> QWidget:
        tab = QWidget()
        main_row = QHBoxLayout(tab)
        main_row.setSpacing(12)
        main_row.setContentsMargins(16, 16, 16, 16)

        # Left panel
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
        left_layout.addStretch()

        main_row.addWidget(left)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setFrameShadow(QFrame.Shadow.Sunken)
        main_row.addWidget(div)

        # Right panel
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)

        preview_group = QGroupBox("Preview  —  click to select single image  •  hover for preview")
        preview_v = QVBoxLayout(preview_group)
        preview_v.setContentsMargins(6, 6, 6, 6)
        self.thumb_strip = SelectableThumbnailStrip()
        self.thumb_strip.selection_changed.connect(self._on_thumb_selection)
        preview_v.addWidget(self.thumb_strip)
        right_layout.addWidget(preview_group)

        jobs_group = QGroupBox("Jobs  —  click a card to view results")
        jobs_v = QVBoxLayout(jobs_group)
        jobs_v.setContentsMargins(6, 6, 6, 6)
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

    def _build_prompt_radio_group(self) -> QGroupBox:
        prompt_group = QGroupBox("Prompt")
        prompt_group_layout = QVBoxLayout(prompt_group)
        prompt_scroll = QScrollArea()
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

    def _rebuild_prompt_radio_buttons(self, select_key="NEUTRAL_WHITE_FRAMING"):
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
        if not self.prompt_buttons.checkedButton():
            btns = self.prompt_buttons.buttons()
            if btns:
                btns[0].setChecked(True)

    # ── Prompts tab ──────────────────────────────────────────────────────

    def _build_prompts_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Left: list + New button
        left = QWidget()
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

        # Right: editor form + AI generator
        right = QWidget()
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

        # Save / Delete row (shown normally, hidden during pending-generation state)
        self.prompt_btn_row = QWidget()
        btn_row = QHBoxLayout(self.prompt_btn_row)
        btn_row.setContentsMargins(0, 0, 0, 0)
        self.prompt_save_btn = QPushButton("Save")
        self.prompt_save_btn.clicked.connect(self._save_prompt_edit)
        self.prompt_delete_btn = QPushButton("Delete")
        self.prompt_delete_btn.setStyleSheet("QPushButton { color: red; }")
        self.prompt_delete_btn.clicked.connect(self._delete_custom_prompt)
        btn_row.addWidget(self.prompt_save_btn)
        btn_row.addWidget(self.prompt_delete_btn)
        btn_row.addStretch()
        right_v.addWidget(self.prompt_btn_row)

        # ── Separator ─────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        right_v.addWidget(sep)

        # ── Generate with AI ──────────────────────────────────────────────
        gen_group = QGroupBox("Generate with AI")
        gen_v = QVBoxLayout(gen_group)
        gen_v.setSpacing(6)

        gen_input_row = QHBoxLayout()
        self.gen_input = QLineEdit()
        self.gen_input.setPlaceholderText('Describe what you want, e.g. "moody black background with rim lighting"')
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

        # Accept / Decline row (shown only after successful generation)
        self.accept_row_widget = QWidget()
        self.accept_row_widget.hide()
        accept_row = QHBoxLayout(self.accept_row_widget)
        accept_row.setContentsMargins(0, 0, 0, 0)
        accept_btn = QPushButton("✓  Accept")
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

    def _populate_prompt_list(self):
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

    def _on_prompt_list_select(self, current):
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

    def _new_custom_prompt(self):
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

    def _auto_update_key(self, text: str):
        if self._editing_new_prompt and not self.edit_key.isReadOnly():
            key = re.sub(r'[^A-Za-z0-9 ]', '', text).upper().replace(' ', '_') or "CUSTOM"
            self.edit_key.setText(key)

    def _save_prompt_edit(self):
        nickname = self.edit_nickname.text().strip()
        key      = re.sub(r'\s+', '_', self.edit_key.text().strip().upper())
        if not key or not nickname:
            return

        is_builtin = key in _BUILTIN_KEYS
        data       = _load_custom_data()

        if is_builtin:
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

        for i in range(self.prompt_list_widget.count()):
            if self.prompt_list_widget.item(i).data(Qt.ItemDataRole.UserRole) == key:
                self.prompt_list_widget.blockSignals(True)
                self.prompt_list_widget.setCurrentRow(i)
                self.prompt_list_widget.blockSignals(False)
                break

    def _delete_custom_prompt(self):
        item = self.prompt_list_widget.currentItem()
        if item is None:
            return
        key = item.data(Qt.ItemDataRole.UserRole)
        if key in _BUILTIN_KEYS:
            return

        data = _load_custom_data()
        data.get("custom_prompts", {}).pop(key, None)
        _save_custom_data(data)

        ALL_PROMPTS.pop(key, None)
        PROMPT_LABELS.pop(key, None)
        CUSTOM_PROMPT_TEXTS.pop(key, None)

        self._rebuild_prompt_radio_buttons(select_key="NEUTRAL_WHITE_FRAMING")
        self._populate_prompt_list()
        self._clear_editor()

    def _clear_editor(self):
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

    # ── AI prompt generator ───────────────────────────────────────────────

    def _generate_prompt(self):
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

    def _on_generate_result(self, data: dict):
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("✦  Generate")

        # Save form state so Decline can restore it
        self._pre_generate_state = {
            'nickname':      self.edit_nickname.text(),
            'key':           self.edit_key.text(),
            'text':          self.edit_text.toPlainText(),
            'key_readonly':  self.edit_key.isReadOnly(),
            'text_readonly': self.edit_text.isReadOnly(),
            'editing_new':   self._editing_new_prompt,
        }

        # Populate fields with generated content
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

        # Grey italic style signals the pending / unconfirmed state
        _pending = "color: #888; font-style: italic; background: #f8f8f6;"
        self.edit_nickname.setStyleSheet(_pending)
        self.edit_key.setStyleSheet(_pending)
        self.edit_text.setStyleSheet(_pending)

        self.prompt_list_widget.clearSelection()
        self.prompt_btn_row.hide()
        self.accept_row_widget.show()

    def _on_generate_error(self, message: str):
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("✦  Generate")
        self.gen_status_lbl.setText(f"Error: {message}")
        self.gen_status_lbl.setStyleSheet("color: red; font-size: 11px;")
        self.gen_status_lbl.show()

    def _accept_generated(self):
        self._clear_pending_style()
        self.accept_row_widget.hide()
        self.prompt_btn_row.show()
        self._save_prompt_edit()
        self._pre_generate_state = None

    def _decline_generated(self):
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

    def _clear_pending_style(self):
        for w in (self.edit_nickname, self.edit_key, self.edit_text):
            w.setStyleSheet("")

    # ── Run tab — input ───────────────────────────────────────────────────

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select image folder")
        if folder:
            self._set_folder(folder)

    def _set_folder(self, folder: str):
        self._selection_path      = folder
        self._selection_is_folder = True
        self.path_label.setText(folder)
        self.path_label.setStyleSheet("color: black; font-size: 11px;")
        files = [
            os.path.join(folder, f) for f in sorted(os.listdir(folder))
            if f.lower().endswith(IMAGE_EXTS)
        ]
        self.thumb_strip.set_folder(folder, files)

    def _set_image_from_drop(self, image_path: str):
        folder = os.path.dirname(image_path)
        self._set_folder(folder)
        self.thumb_strip.select_file(image_path)

    def _on_thumb_selection(self, path_or_list, is_folder: bool):
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

    def _selected_prompt_key(self):
        btn = self.prompt_buttons.checkedButton()
        return btn.property("prompt_key") if btn else None

    # ── Run ──────────────────────────────────────────────────────────────

    def _run(self):
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

    def _launch_job(self, config: dict):
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
        worker.error.connect(card.mark_error)
        worker.start()
        card._worker = worker

    def _notify(self, config, output_dir):
        label = PROMPT_LABELS.get(config['prompt_key'], config['prompt_key'])
        subprocess.run([
            "osascript", "-e",
            f'display notification "Done: {label}" with title "Svelda" '
            f'subtitle "{os.path.basename(output_dir)}"'
        ])

    # ── Reprocess ────────────────────────────────────────────────────────

    def _load_into_form(self, config: dict):
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("macos")
    window = SveldaApp()
    window.show()
    sys.exit(app.exec())
