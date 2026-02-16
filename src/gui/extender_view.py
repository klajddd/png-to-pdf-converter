import os
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from PIL import Image
from tkinterdnd2 import DND_FILES

from src.core.extender import extend_document


class ExtenderView:
    def __init__(self, parent, root):
        self.root = root
        self.frame = ttk.Frame(parent, padding=(18, 16))

        self.base_type = tk.StringVar(value="pdf")
        self.base_path = tk.StringVar(value="")

        self.output_dir = tk.StringVar(value=os.getcwd())
        self.output_name = tk.StringVar(value="")

        self.files_to_append = []
        self.dragged_item_path = None
        self.drag_offset_y = 0
        self.placeholder_frame_id = None

        self._build_ui()
        self._update_buttons()

    def _build_ui(self):
        title = ttk.Label(self.frame, text="Extender", font=("Helvetica", 16, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(self.frame, text="Append images to an existing document")
        subtitle.pack(anchor="w", pady=(2, 14))

        drop_container = tk.Frame(self.frame, bg="#FFFFFF")
        drop_container.pack(fill="x")

        drop_container.columnconfigure(0, weight=1)
        drop_container.columnconfigure(1, weight=1)

        base_drop = tk.Frame(drop_container, bg="#F6F6F6", highlightbackground="#E0E0E0", highlightthickness=1)
        base_drop.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        base_drop.configure(height=220)
        base_drop.grid_propagate(False)

        attach_drop = tk.Frame(drop_container, bg="#F6F6F6", highlightbackground="#E0E0E0", highlightthickness=1)
        attach_drop.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        attach_drop.configure(height=220)
        attach_drop.grid_propagate(False)

        self.base_drop_label = ttk.Label(base_drop, text="Drag & drop PDF/DOCX here")
        self.base_drop_label.place(relx=0.5, rely=0.5, anchor="center")

        self.attach_drop_label = ttk.Label(attach_drop, text="Drag & drop images here")
        self.attach_drop_label.place(relx=0.5, rely=0.5, anchor="center")

        base_drop.drop_target_register(DND_FILES)
        base_drop.dnd_bind("<<Drop>>", self._handle_base_drop)

        attach_drop.drop_target_register(DND_FILES)
        attach_drop.dnd_bind("<<Drop>>", self._handle_attachments_drop)

        controls_row = ttk.Frame(self.frame)
        controls_row.pack(fill="x", pady=(12, 10))

        ttk.Label(controls_row, text="Base type").pack(side="left")
        ttk.OptionMenu(controls_row, self.base_type, self.base_type.get(), "pdf", "docx").pack(side="left", padx=8)
        ttk.Entry(controls_row, textvariable=self.base_path, state="readonly").pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(controls_row, text="Browse", command=self._browse_base).pack(side="left")

        attach_controls = ttk.Frame(self.frame)
        attach_controls.pack(fill="x", pady=(0, 12))

        ttk.Button(attach_controls, text="Browse images", command=self._browse_attachments).pack(side="left")

        out_row = ttk.Frame(self.frame)
        out_row.pack(fill="x", pady=(0, 10))

        ttk.Label(out_row, text="Output folder").pack(side="left")
        ttk.Entry(out_row, textvariable=self.output_dir, state="readonly").pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(out_row, text="Browse", command=self._browse_output_dir).pack(side="left")

        name_row = ttk.Frame(self.frame)
        name_row.pack(fill="x", pady=(0, 12))

        ttk.Label(name_row, text="Output name").pack(side="left")
        ttk.Entry(name_row, textvariable=self.output_name).pack(side="left", fill="x", expand=True, padx=8)

        btn_row = ttk.Frame(self.frame)
        btn_row.pack(fill="x", pady=(0, 12))

        self.extend_btn = ttk.Button(btn_row, text="Extend", command=self._start_extend)
        self.extend_btn.pack(side="left")

        self.clear_btn = ttk.Button(btn_row, text="Clear", command=self._clear)
        self.clear_btn.pack(side="left", padx=10)

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

    def _browse_base(self):
        filetypes = [("PDF or DOCX", "*.pdf *.docx"), ("PDF", "*.pdf"), ("DOCX", "*.docx")]
        f = filedialog.askopenfilename(title="Select base document", filetypes=filetypes)
        if f:
            self._set_base(Path(f))

    def _set_base(self, p: Path):
        self.base_path.set(str(p))
        ext = p.suffix.lower()
        if ext == ".docx":
            self.base_type.set("docx")
        else:
            self.base_type.set("pdf")

        self.output_dir.set(str(p.parent))
        if ext == ".pdf":
            self.output_name.set(p.name)
        else:
            self.output_name.set(f"{p.stem}.pdf")
        self._update_buttons()

    def _browse_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory", initialdir=self.output_dir.get())
        if directory:
            self.output_dir.set(directory)

    def _browse_attachments(self):
        files = filedialog.askopenfilenames(title="Select images", filetypes=[("Images", "*.*")])
        if files:
            self._add_attachments([Path(f) for f in files])

    def _handle_base_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        if not files:
            return
        p = Path(files[0])
        if p.suffix.lower() in {".pdf", ".docx"}:
            self._set_base(p)

    def _handle_attachments_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        paths = [Path(f) for f in files]
        self._add_attachments(paths)

    def _is_image(self, p: Path) -> bool:
        try:
            img = Image.open(p)
            img.close()
            return True
        except Exception:
            return False

    def _add_attachments(self, paths):
        new_images = [p for p in paths if p.is_file() and self._is_image(p)]
        existing = {f["path"] for f in self.files_to_append if not f.get("removed", False)}

        for p in new_images:
            if str(p) in existing:
                continue
            self.files_to_append.append({"path": str(p), "removed": False})

        self._refresh_list()
        self._update_buttons()
        self.status_label.config(text="")

    def _refresh_list(self):
        for child in self.scrollable_frame.winfo_children():
            child.destroy()

        for file_info in self.files_to_append:
            if file_info.get("removed", False):
                continue

            row = tk.Frame(self.scrollable_frame, bg="#FFFFFF", highlightbackground="#EFEFEF", highlightthickness=1)
            row.pack(fill="x", pady=4)

            row.bind("<Button-1>", lambda e, p=file_info["path"]: self._on_drag_start(e, p))
            row.bind("<B1-Motion>", self._on_drag_motion)
            row.bind("<ButtonRelease-1>", self._on_drop)

            lbl = ttk.Label(row, text=file_info["path"])
            lbl.pack(side="left", padx=8, pady=8, fill="x", expand=True)

            btn = ttk.Button(row, text="Remove", command=lambda p=file_info["path"]: self._remove_attachment(p))
            btn.pack(side="right", padx=8, pady=6)

    def _remove_attachment(self, file_path: str):
        for f in self.files_to_append:
            if f["path"] == file_path and not f.get("removed", False):
                f["removed"] = True
        self._refresh_list()
        self._update_buttons()

    def _clear(self):
        self.base_path.set("")
        self.files_to_append = []
        self.output_name.set("")
        self.output_dir.set(os.getcwd())
        self.status_label.config(text="")
        self._refresh_list()
        self._update_buttons()

    def _update_buttons(self):
        has_base = bool(self.base_path.get())
        active = [f for f in self.files_to_append if not f.get("removed", False)]
        can_extend = has_base and bool(active) and bool(self.output_name.get().strip())

        self.extend_btn.config(state=("normal" if can_extend else "disabled"))
        self.clear_btn.config(state=("normal" if (has_base or active) else "disabled"))

    def _start_extend(self):
        base = Path(self.base_path.get())
        attachments = [Path(f["path"]) for f in self.files_to_append if not f.get("removed", False)]
        out_dir = Path(self.output_dir.get())
        out_name = self.output_name.get().strip()
        base_type = self.base_type.get().strip().lower()

        if not out_name.lower().endswith(".pdf"):
            out_name = f"{out_name}.pdf"
            self.output_name.set(out_name)

        def worker():
            try:
                with tempfile.TemporaryDirectory() as td:
                    out_path, renamed_base, pages = extend_document(
                        base_path=base,
                        base_type=base_type,
                        attachment_image_paths=attachments,
                        output_dir=out_dir,
                        output_filename=out_name,
                        temp_dir=Path(td),
                    )

                def update_status():
                    if renamed_base:
                        self.base_path.set(str(renamed_base))
                    self.status_label.config(text=f"Created: {out_path.name}  Added pages: {pages}")

                self.root.after(0, update_status)
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"Error: {e}"))

        threading.Thread(target=worker).start()

    def _on_drag_start(self, event, file_path):
        self.dragged_item_path = file_path
        self.drag_offset_y = event.y_root - event.widget.winfo_rooty()

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

        active_items = [f for f in self.files_to_append if not f.get("removed", False)]
        if not active_items:
            return

        new_index = 0
        current_y = 0
        for i, f in enumerate(active_items):
            current_y += 52
            if drop_y > current_y:
                new_index = i + 1

        original_index = next((i for i, f in enumerate(self.files_to_append) if f["path"] == self.dragged_item_path), None)
        if original_index is None:
            return

        item = self.files_to_append.pop(original_index)

        active_positions = [i for i, f in enumerate(self.files_to_append) if not f.get("removed", False)]
        if new_index >= len(active_positions):
            self.files_to_append.append(item)
        else:
            insert_at = active_positions[new_index]
            self.files_to_append.insert(insert_at, item)

        if self.placeholder_frame_id is not None:
            try:
                self.canvas.delete(self.placeholder_frame_id)
            except Exception:
                pass
            self.placeholder_frame_id = None

        self.dragged_item_path = None
        self._refresh_list()
