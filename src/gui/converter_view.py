import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from PIL import Image
from tkinterdnd2 import DND_FILES

from src.core.converter import process_images_to_pdf


class ConverterView:
    def __init__(self, parent, root):
        self.root = root
        self.frame = ttk.Frame(parent, padding=(18, 16))

        self.files_to_convert = []
        self.dragged_item_path = None
        self.dragged_item_frame = None
        self.drag_offset_y = 0
        self.placeholder_frame_id = None

        self.output_dir = tk.StringVar(value=os.getcwd())
        self.output_name = tk.StringVar(value="combined_images.pdf")

        self._build_ui()
        self._update_button_state()

    def _build_ui(self):
        title = ttk.Label(self.frame, text="Converter", font=("Helvetica", 16, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(self.frame, text="Convert images into a single PDF")
        subtitle.pack(anchor="w", pady=(2, 14))

        self.drop_frame = ttk.Frame(self.frame)
        self.drop_frame.pack(fill="both", expand=False)

        self.drop_zone = tk.Frame(self.drop_frame, bg="#F6F6F6", highlightbackground="#E0E0E0", highlightthickness=1)
        self.drop_zone.pack(fill="x", expand=False)
        self.drop_zone.configure(height=220)
        self.drop_zone.pack_propagate(False)

        self.drop_label = ttk.Label(self.drop_zone, text="Drag & drop images here, or use Browse")
        self.drop_label.place(relx=0.5, rely=0.5, anchor="center")

        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind("<<Drop>>", self._handle_drop)

        output_row = ttk.Frame(self.frame)
        output_row.pack(fill="x", pady=(12, 10))

        ttk.Label(output_row, text="Output folder").pack(side="left")
        ttk.Entry(output_row, textvariable=self.output_dir, state="readonly").pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(output_row, text="Browse", command=self._browse_output_dir).pack(side="left")

        name_row = ttk.Frame(self.frame)
        name_row.pack(fill="x", pady=(0, 12))

        ttk.Label(name_row, text="Output name").pack(side="left")
        ttk.Entry(name_row, textvariable=self.output_name).pack(side="left", fill="x", expand=True, padx=8)

        btn_row = ttk.Frame(self.frame)
        btn_row.pack(fill="x", pady=(0, 12))

        self.browse_btn = ttk.Button(btn_row, text="Browse", command=self._browse_files)
        self.browse_btn.pack(side="left")

        self.convert_btn = ttk.Button(btn_row, text="Convert", command=self._start_conversion, style="Primary.TButton")
        self.convert_btn.pack(side="left", padx=10)

        self.clear_btn = ttk.Button(btn_row, text="Clear", command=self._clear_files, style="Danger.TButton")
        self.clear_btn.pack(side="left")

        list_outer = tk.Frame(self.frame, bg="#FFFFFF")
        list_outer.pack(fill="both", expand=True, pady=(0, 12))
        list_outer.configure(height=170)
        list_outer.pack_propagate(False)

        self.canvas = tk.Canvas(list_outer, bg="#FFFFFF", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(list_outer, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.status_label = ttk.Label(self.frame, text="")
        self.status_label.pack(anchor="w", pady=(12, 0))

    def _browse_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory", initialdir=self.output_dir.get())
        if directory:
            self.output_dir.set(directory)

    def _browse_files(self):
        files = filedialog.askopenfilenames(title="Select images", filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.gif")])
        if files:
            self._add_files([Path(f) for f in files])

    def _handle_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        paths = [Path(f) for f in files if Path(f).suffix]
        image_paths = [p for p in paths if self._is_image(p)]
        if image_paths:
            self._add_files(image_paths)

    def _is_image(self, p: Path) -> bool:
        try:
            Image.open(p).close()
            return True
        except Exception:
            return False

    def _add_files(self, new_files):
        existing = {f["path"] for f in self.files_to_convert if not f.get("removed", False)}

        if not existing and new_files:
            self.output_dir.set(str(new_files[0].parent))

        for p in new_files:
            if str(p) in existing:
                continue
            self.files_to_convert.append({"path": str(p), "removed": False})

        self._refresh_list()
        self._update_button_state()
        self.status_label.config(text="", style="TLabel")

    def _refresh_list(self):
        for child in self.scrollable_frame.winfo_children():
            child.destroy()

        for file_info in self.files_to_convert:
            if file_info.get("removed", False):
                continue

            row = tk.Frame(self.scrollable_frame, bg="#FFFFFF", highlightbackground="#EFEFEF", highlightthickness=1)
            row.pack(fill="x", pady=4)

            row.bind("<Button-1>", lambda e, p=file_info["path"]: self._on_drag_start(e, p))
            row.bind("<B1-Motion>", self._on_drag_motion)
            row.bind("<ButtonRelease-1>", self._on_drop)

            lbl = ttk.Label(row, text=file_info["path"])
            lbl.pack(side="left", padx=8, pady=8, fill="x", expand=True)

            btn = ttk.Button(row, text="Remove", command=lambda p=file_info["path"]: self._remove_file(p))
            btn.pack(side="right", padx=8, pady=6)

    def _remove_file(self, file_path: str):
        for f in self.files_to_convert:
            if f["path"] == file_path and not f.get("removed", False):
                f["removed"] = True
        self._refresh_list()
        self._update_button_state()

    def _clear_files(self):
        self.files_to_convert = []
        self._refresh_list()
        self._update_button_state()
        self.status_label.config(text="", style="TLabel")

    def _update_button_state(self):
        active = [f for f in self.files_to_convert if not f.get("removed", False)]
        state = "normal" if active else "disabled"
        self.convert_btn.config(state=state)
        self.clear_btn.config(state=state)

    def _start_conversion(self):
        active_paths = [f["path"] for f in self.files_to_convert if not f.get("removed", False)]
        if not active_paths:
            return

        thread = threading.Thread(target=self._process, args=(active_paths,))
        thread.start()

    def _process(self, active_paths):
        output_dir = Path(self.output_dir.get())
        output_name = self.output_name.get().strip() or "combined_images.pdf"

        if not output_name.lower().endswith(".pdf"):
            output_name = f"{output_name}.pdf"
            self.root.after(0, lambda: self.output_name.set(output_name))

        def ask_overwrite_callback(_png_path, _pdf_path):
            return "overwrite"

        def get_new_name_callback(original_path):
            return original_path

        def update_status_callback(_file_path, _status_text, _color):
            return

        def update_overall_progress_callback(_message, _current, _total):
            return

        converted, skipped = process_images_to_pdf(
            png_paths=active_paths,
            output_dir=output_dir,
            output_mode="single",
            ask_overwrite_callback=ask_overwrite_callback,
            get_new_name_callback=get_new_name_callback,
            update_status_callback=update_status_callback,
            update_overall_progress_callback=update_overall_progress_callback,
            single_pdf_filename=output_name,
            auto_rename_if_exists=True,
        )

        def update_status():
            if converted > 0 and skipped == 0:
                self.status_label.config(text=f"Converted: {converted}", style="Success.TLabel")
            elif converted > 0:
                self.status_label.config(text=f"Converted: {converted}  Skipped: {skipped}", style="Success.TLabel")
            else:
                self.status_label.config(text=f"Skipped: {skipped}", style="Error.TLabel")

        self.root.after(0, update_status)

    def _on_drag_start(self, event, file_path):
        self.dragged_item_path = file_path
        self.dragged_item_frame = event.widget
        self.drag_offset_y = event.y_root - self.dragged_item_frame.winfo_rooty()

        if self.placeholder_frame_id is not None:
            try:
                self.canvas.delete(self.placeholder_frame_id)
            except Exception:
                pass
            self.placeholder_frame_id = None

        try:
            y = self.canvas.canvasy(event.y)
            self.placeholder_frame_id = self.canvas.create_rectangle(0, y, self.canvas.winfo_width(), y + 44, outline="#C0C0C0")
        except Exception:
            self.placeholder_frame_id = None

    def _on_drag_motion(self, event):
        if self.placeholder_frame_id is None:
            return
        y = self.canvas.canvasy(event.y_root - self.canvas.winfo_rooty() - self.drag_offset_y)
        self.canvas.coords(self.placeholder_frame_id, 0, y, self.canvas.winfo_width(), y + 44)

    def _on_drop(self, event):
        if not self.dragged_item_path:
            return

        drop_y = self.canvas.canvasy(event.y_root - self.canvas.winfo_rooty() - self.drag_offset_y)

        active_items = [f for f in self.files_to_convert if not f.get("removed", False)]
        if not active_items:
            return

        new_index = 0
        current_y = 0
        for i, f in enumerate(active_items):
            current_y += 52
            if drop_y > current_y:
                new_index = i + 1

        original_index = next((i for i, f in enumerate(self.files_to_convert) if f["path"] == self.dragged_item_path), None)
        if original_index is None:
            return

        item = self.files_to_convert.pop(original_index)

        active_positions = [i for i, f in enumerate(self.files_to_convert) if not f.get("removed", False)]
        if new_index >= len(active_positions):
            self.files_to_convert.append(item)
        else:
            insert_at = active_positions[new_index]
            self.files_to_convert.insert(insert_at, item)

        if self.placeholder_frame_id is not None:
            try:
                self.canvas.delete(self.placeholder_frame_id)
            except Exception:
                pass
            self.placeholder_frame_id = None

        self.dragged_item_path = None
        self.dragged_item_frame = None

        self._refresh_list()
