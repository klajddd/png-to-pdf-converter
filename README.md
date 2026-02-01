# PNG to PDF Converter

A simple desktop application to convert single or multiple PNG images into PDF documents, with options for combining into a single PDF, reordering, and output location management.

## Features

- Graphical User Interface (GUI)
- Drag & Drop and File Browsing for PNG selection
- Thumbnail previews of selected images
- Reorder images via drag-and-drop for custom PDF page order
- Option to combine all PNGs into a single multi-page PDF or create separate PDFs per image
- Customizable output directory
- Clear all files button
- Individual file status indicators (success/error/skipped)
- Integrated conversion completion message (no popups)

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/png-to-pdf-converter.git
    cd png-to-pdf-converter
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows: .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To run the application:

```bash
python src/main.py
```

## Building a Standalone Application (macOS example)

To create a double-clickable macOS `.app` bundle, use PyInstaller:

1.  **Install PyInstaller (if not already installed):**

    ```bash
    pip install pyinstaller
    ```

2.  **Navigate to the project root and run PyInstaller:**

    ```bash
    pyinstaller --windowed --onefile --name "PNG to PDF Converter" src/main.py
    ```

    (Optional: add `--icon "path/to/your/icon.icns"` for a custom icon.)

3.  The `.app` bundle will be found in the `dist/` directory.

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.
