# UtilityBox

A desktop app that bundles three utilities in one launcher: **Converter** (PNG to PDF), **Timer** (countdown and stopwatch), and **Extender** (append files to PDFs or DOCX). Each utility opens in its own window.

## Utilities

### Converter
Convert PNG images to PDF.

- Drag & drop or browse to add PNGs
- Thumbnail previews and drag-and-drop reordering for page order
- Combine all images into one multi-page PDF or export each as a separate PDF
- Choose output directory; per-file status (success / error / skipped)

### Timer
Countdown and stopwatch with multiple timers.

- Countdown (HH:MM:SS) or stopwatch mode
- Add several timers; each runs independently
- Optional beep when a countdown finishes

### Extender
Append PDFs and images to an existing document.

- Base document: one PDF or DOCX (DOCX is converted to PDF first; requires `docx2pdf`)
- Attachments: PDFs and/or images, in order; drag & drop to reorder
- Output: a single PDF. Optionally renames the original base file to `*_original.*`

## Installation

1. Clone the repo and go into the project folder:

   ```bash
   git clone https://github.com/yourusername/converter.git
   cd converter
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   Requirements: Pillow, tkinterdnd2, pypdf; `docx2pdf` is included for Extender DOCX support (macOS may need additional setup for DOCX conversion).

## Usage

Run the launcher, then click a tile to open Converter, Timer, or Extender:

```bash
python src/main.py
```

## Building a standalone app (macOS example)

Using PyInstaller:

1. Install PyInstaller if needed:

   ```bash
   pip install pyinstaller
   ```

2. From the project root:

   ```bash
   pyinstaller --windowed --onefile --name "UtilityBox" src/main.py
   ```

   Optional: `--icon "path/to/icon.icns"` for a custom icon.

3. The `.app` is in `dist/`.

## License

MIT — see [LICENSE.txt](LICENSE.txt).
