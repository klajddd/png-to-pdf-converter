import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

class ShellApp:
    def __init__(self, root):
        self.root = root
        self.root.title("UtilityBox")
        self.root.minsize(720, 520)

        self._launcher_bg = "#E3E1EB"

        self._tile_bg = "#FFFFFF"
        self._tile_hover_bg = "#D6D2DD"
        self._tile_pressed_bg = "#CFCAD8"

        self._open_windows: dict[str, tk.Toplevel] = {}

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Launcher.TFrame", background=self._launcher_bg)
        style.configure("LauncherHeader.TFrame", background=self._launcher_bg)
        style.configure("LauncherGrid.TFrame", background=self._launcher_bg)
        style.configure(
            "LauncherSearch.TEntry",
            padding=(10, 8),
            fieldbackground="#FFFFFF",
        )

        style.configure(
            "Primary.TButton",
            padding=(12, 10),
            background="#386757",
            foreground="#FFFFFF",
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#2F584B"), ("disabled", "#A9BDB6")],
            foreground=[("active", "#FFFFFF"), ("disabled", "#FFFFFF")],
        )

        style.configure(
            "Danger.TButton",
            padding=(12, 10),
            background="#E45757",
            foreground="#FFFFFF",
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#CC4C4C"), ("disabled", "#F0B1B1")],
            foreground=[("active", "#FFFFFF"), ("disabled", "#FFFFFF")],
        )

        style.configure("Success.TLabel", foreground="#2F7D46", background="#FFFFFF")
        style.configure("Error.TLabel", foreground="#B23B3B", background="#FFFFFF")

        self.root.configure(bg=self._launcher_bg)

        self._utilities = [
            {
                "key": "converter",
                "name": "Converter",
                "size": (900, 680),
                "minsize": (860, 620),
            },
            {
                "key": "extender",
                "name": "Extender",
                "size": (980, 720),
                "minsize": (900, 650),
            },
        ]

        self.search_text = tk.StringVar(value="")

        self._build_layout()

    def _build_layout(self):
        self.container = ttk.Frame(self.root, style="Launcher.TFrame")
        self.container.pack(fill="both", expand=True)

        self.container.rowconfigure(1, weight=1)
        self.container.columnconfigure(0, weight=1)

        header = ttk.Frame(self.container, style="LauncherHeader.TFrame", padding=(18, 16))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title = ttk.Label(header, text="UtilityBox", font=("Helvetica", 18, "bold"), background=self._launcher_bg)
        title.grid(row=0, column=0, sticky="w")

        self.search_entry = ttk.Entry(header, textvariable=self.search_text, style="LauncherSearch.TEntry")
        self.search_entry.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        self.search_entry.insert(0, "Search utilities…")
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)

        grid_outer = ttk.Frame(self.container, style="LauncherGrid.TFrame", padding=(18, 16))
        grid_outer.grid(row=1, column=0, sticky="nsew")
        grid_outer.rowconfigure(0, weight=1)
        grid_outer.columnconfigure(0, weight=1)

        self.grid_canvas = tk.Canvas(grid_outer, bg=self._launcher_bg, highlightthickness=0)
        self.grid_canvas.grid(row=0, column=0, sticky="nsew")

        self.grid_frame = ttk.Frame(self.grid_canvas, style="LauncherGrid.TFrame")
        self.grid_window_id = self.grid_canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        self.grid_canvas.bind("<Configure>", self._on_canvas_configure)
        self.grid_frame.bind("<Configure>", self._on_grid_configure)

        self._tiles = []
        for util in self._utilities:
            tile = self._create_tile(self.grid_frame, util)
            self._tiles.append((tile, util))

        self._relayout_tiles()

    def _on_search_focus_in(self, _event):
        if self.search_entry.get() == "Search utilities…":
            self.search_entry.delete(0, "end")

    def _on_search_focus_out(self, _event):
        if not self.search_entry.get().strip():
            self.search_entry.delete(0, "end")
            self.search_entry.insert(0, "Search utilities…")

    def _on_canvas_configure(self, event):
        try:
            self.grid_canvas.itemconfigure(self.grid_window_id, width=event.width)
        except Exception:
            pass
        self._relayout_tiles()

    def _on_grid_configure(self, _event):
        try:
            self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
        except Exception:
            pass

    def _relayout_tiles(self):
        width = self.grid_canvas.winfo_width() or 1
        tile_w = 160
        columns = max(3, min(5, max(1, width // tile_w)))

        for i in range(columns):
            self.grid_frame.columnconfigure(i, weight=1)

        for idx, (tile, _util) in enumerate(self._tiles):
            r = idx // columns
            c = idx % columns
            tile.grid(row=r, column=c, padx=10, pady=10, sticky="n")

    def _create_tile(self, parent, util):
        outer = tk.Frame(parent, bg=self._tile_bg, highlightbackground="#E6E6E6", highlightthickness=1)
        outer.configure(width=150, height=140)
        outer.grid_propagate(False)

        icon = tk.Canvas(outer, width=64, height=64, bg=self._tile_bg, highlightthickness=0)
        icon.grid(row=0, column=0, pady=(18, 8))
        icon.create_rectangle(8, 8, 56, 56, outline="#B8B8B8", width=2)
        icon.create_text(32, 32, text=util["name"][0], fill="#6B6B6B", font=("Helvetica", 18, "bold"))

        lbl = tk.Label(outer, text=util["name"], bg=self._tile_bg, fg="#1F1F1F", font=("Helvetica", 12))
        lbl.grid(row=1, column=0)

        def set_bg(bg):
            outer.configure(bg=bg)
            icon.configure(bg=bg)
            lbl.configure(bg=bg)

        def on_enter(_e):
            set_bg(self._tile_hover_bg)

        def on_leave(_e):
            set_bg(self._tile_bg)

        def on_press(_e):
            set_bg(self._tile_pressed_bg)

        def on_release(_e):
            set_bg(self._tile_hover_bg)
            self.root.after(70, lambda: set_bg(self._tile_bg))
            self.open_utility(util["key"])

        for w in (outer, icon, lbl):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_press)
            w.bind("<ButtonRelease-1>", on_release)

        return outer

    def open_utility(self, key: str):
        existing = self._open_windows.get(key)
        if existing is not None and existing.winfo_exists():
            try:
                existing.deiconify()
            except Exception:
                pass
            try:
                existing.lift()
            except Exception:
                pass
            try:
                existing.focus_force()
            except Exception:
                pass
            return

        util = next((u for u in self._utilities if u["key"] == key), None)
        if util is None:
            return

        win = tk.Toplevel(self.root)
        self._open_windows[key] = win

        w, h = util["size"]
        min_w, min_h = util["minsize"]

        win.title(f"{util['name']} — UtilityBox")
        win.minsize(min_w, min_h)
        win.geometry(f"{w}x{h}")

        container = ttk.Frame(win)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        try:
            if key == "converter":
                from src.gui.converter_view import ConverterView

                view = ConverterView(container, root=self.root)
            else:
                from src.gui.extender_view import ExtenderView

                view = ExtenderView(container, root=self.root)
        except Exception as e:
            win.destroy()
            messagebox.showerror(
                "UtilityBox",
                f"Could not open '{util['name']}'.\n\n{e}",
                parent=self.root,
            )
            try:
                if self._open_windows.get(key) is win:
                    del self._open_windows[key]
            except Exception:
                pass
            return

        view.frame.grid(row=0, column=0, sticky="nsew")

        def on_close():
            try:
                if self._open_windows.get(key) is win:
                    del self._open_windows[key]
            except Exception:
                pass
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)
