import tkinter as tk
from tkinter import ttk

from src.gui.converter_view import ConverterView
from src.gui.extender_view import ExtenderView


class ShellApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Converter")
        self.root.minsize(900, 600)

        self._nav_button_style = "Nav.TButton"
        self._nav_button_active_style = "NavActive.TButton"

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Nav.TFrame", background="#F6F6F6")
        style.configure("Content.TFrame", background="#FFFFFF")
        style.configure(self._nav_button_style, padding=(12, 10), anchor="w")

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
        style.configure(
            self._nav_button_active_style,
            padding=(12, 10),
            anchor="w",
            background="#3B3B3B",
            foreground="#FFFFFF",
        )
        style.map(
            self._nav_button_active_style,
            background=[("active", "#2E2E2E"), ("disabled", "#3B3B3B")],
            foreground=[("active", "#FFFFFF"), ("disabled", "#FFFFFF")],
        )

        self.root.configure(bg="#FFFFFF")

        self._build_layout()
        self.show_view("converter")

    def _build_layout(self):
        self.container = ttk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        self.container.columnconfigure(0, weight=1)
        self.container.columnconfigure(1, weight=3)
        self.container.rowconfigure(0, weight=1)

        self.nav_frame = ttk.Frame(self.container, style="Nav.TFrame")
        self.nav_frame.grid(row=0, column=0, sticky="nsew")

        self.content_frame = ttk.Frame(self.container, style="Content.TFrame")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.rowconfigure(0, weight=1)
        self.content_frame.columnconfigure(0, weight=1)

        self.btn_converter = ttk.Button(
            self.nav_frame,
            text="Converter",
            style=self._nav_button_style,
            command=lambda: self.show_view("converter"),
        )
        self.btn_converter.pack(fill="x", padx=12, pady=(16, 8))

        self.btn_extender = ttk.Button(
            self.nav_frame,
            text="Extender",
            style=self._nav_button_style,
            command=lambda: self.show_view("extender"),
        )
        self.btn_extender.pack(fill="x", padx=12, pady=8)

        self._views = {
            "converter": ConverterView(self.content_frame, root=self.root),
            "extender": ExtenderView(self.content_frame, root=self.root),
        }

        for view in self._views.values():
            view.frame.grid(row=0, column=0, sticky="nsew")

    def show_view(self, view_key: str):
        for key, view in self._views.items():
            if key == view_key:
                view.frame.tkraise()

        self.root.title("Converter" if view_key == "converter" else "Extender")

        self.btn_converter.configure(
            style=self._nav_button_active_style if view_key == "converter" else self._nav_button_style
        )
        self.btn_extender.configure(
            style=self._nav_button_active_style if view_key == "extender" else self._nav_button_style
        )
