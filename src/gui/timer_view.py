import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk


def _format_hhmmss(total_seconds: int) -> str:
    total_seconds = max(0, int(total_seconds))
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def _safe_int(text: str, default: int = 0) -> int:
    try:
        return int(text.strip())
    except Exception:
        return default


@dataclass
class _TimerState:
    key: str
    mode: str  # "countdown" | "stopwatch"
    name: str
    duration_seconds: int
    running: bool = False
    finished: bool = False
    start_ts: float | None = None
    elapsed_before: float = 0.0
    finished_notified: bool = False


class TimerView:
    def __init__(self, parent, root, window=None, header_icon=None):
        self.root = root
        self.window = window
        self.frame = ttk.Frame(parent, padding=(18, 16))

        self._header_icon = header_icon

        self._next_timer_num = 1
        self._timers: list[_TimerState] = []
        self._row_widgets: dict[str, dict[str, object]] = {}

        self.mode = tk.StringVar(value="countdown")
        self.name = tk.StringVar(value="")

        self.hh = tk.StringVar(value="0")
        self.mm = tk.StringVar(value="0")
        self.ss = tk.StringVar(value="0")

        self.beep_on_finish = tk.BooleanVar(value=True)

        self._tick_job: str | None = None
        self._closed = False

        self._build_ui()
        self._sync_duration_enabled()
        self._start_tick_loop()

    def cleanup(self):
        self._closed = True
        if self._tick_job is not None:
            try:
                self.root.after_cancel(self._tick_job)
            except Exception:
                pass
            self._tick_job = None

    def _build_ui(self):
        title_row = ttk.Frame(self.frame)
        title_row.pack(anchor="w")

        if self._header_icon is not None:
            ttk.Label(title_row, image=self._header_icon).pack(side="left", padx=(0, 8))

        ttk.Label(title_row, text="Timer", font=("Helvetica", 16, "bold")).pack(side="left")

        subtitle = ttk.Label(self.frame, text="Run multiple countdowns and stopwatches at the same time")
        subtitle.pack(anchor="w", pady=(2, 14))

        add_box = ttk.Frame(self.frame)
        add_box.pack(fill="x", pady=(0, 12))

        row1 = ttk.Frame(add_box)
        row1.pack(fill="x")

        ttk.Label(row1, text="Type").pack(side="left")
        type_menu = ttk.OptionMenu(row1, self.mode, self.mode.get(), "countdown", "stopwatch", command=lambda *_: self._sync_duration_enabled())
        type_menu.pack(side="left", padx=(8, 16))

        ttk.Label(row1, text="Name").pack(side="left")
        ttk.Entry(row1, textvariable=self.name).pack(side="left", fill="x", expand=True, padx=8)

        ttk.Checkbutton(row1, text="Beep", variable=self.beep_on_finish).pack(side="left", padx=(8, 0))

        row2 = ttk.Frame(add_box)
        row2.pack(fill="x", pady=(10, 0))

        ttk.Label(row2, text="Duration").pack(side="left")

        self.hh_entry = ttk.Entry(row2, textvariable=self.hh, width=5)
        self.mm_entry = ttk.Entry(row2, textvariable=self.mm, width=5)
        self.ss_entry = ttk.Entry(row2, textvariable=self.ss, width=5)

        self.hh_entry.pack(side="left", padx=(8, 4))
        ttk.Label(row2, text="HH").pack(side="left", padx=(0, 10))

        self.mm_entry.pack(side="left", padx=(0, 4))
        ttk.Label(row2, text="MM").pack(side="left", padx=(0, 10))

        self.ss_entry.pack(side="left", padx=(0, 4))
        ttk.Label(row2, text="SS").pack(side="left", padx=(0, 16))

        quick = ttk.Frame(row2)
        quick.pack(side="left")

        ttk.Button(quick, text="+1m", command=lambda: self._quick_add(seconds=60)).pack(side="left")
        ttk.Button(quick, text="+5m", command=lambda: self._quick_add(seconds=5 * 60)).pack(side="left", padx=6)
        ttk.Button(quick, text="+10m", command=lambda: self._quick_add(seconds=10 * 60)).pack(side="left")
        ttk.Button(quick, text="+30m", command=lambda: self._quick_add(seconds=30 * 60)).pack(side="left", padx=6)
        ttk.Button(quick, text="+1h", command=lambda: self._quick_add(seconds=3600)).pack(side="left")

        ttk.Button(row2, text="Add", command=self._add_timer, style="Primary.TButton").pack(side="right")

        list_outer = tk.Frame(self.frame, bg="#FFFFFF")
        list_outer.pack(fill="both", expand=True, pady=(0, 12))

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

    def _sync_duration_enabled(self):
        is_countdown = self.mode.get().strip().lower() == "countdown"
        state = "normal" if is_countdown else "disabled"

        for w in (self.hh_entry, self.mm_entry, self.ss_entry):
            try:
                w.configure(state=state)
            except Exception:
                pass

    def _quick_add(self, seconds: int):
        if self.mode.get().strip().lower() != "countdown":
            return

        current = self._get_duration_seconds()
        new_total = current + seconds

        h = new_total // 3600
        m = (new_total % 3600) // 60
        s = new_total % 60

        self.hh.set(str(h))
        self.mm.set(str(m))
        self.ss.set(str(s))

    def _get_duration_seconds(self) -> int:
        h = max(0, _safe_int(self.hh.get(), 0))
        m = max(0, _safe_int(self.mm.get(), 0))
        s = max(0, _safe_int(self.ss.get(), 0))
        return h * 3600 + m * 60 + s

    def _add_timer(self):
        mode = self.mode.get().strip().lower()
        if mode not in {"countdown", "stopwatch"}:
            mode = "countdown"

        name = self.name.get().strip()
        if not name:
            name = f"Timer {self._next_timer_num}"
            self._next_timer_num += 1

        duration = 0
        if mode == "countdown":
            duration = self._get_duration_seconds()
            if duration <= 0:
                self.status_label.config(text="Please enter a duration for a countdown.", style="Error.TLabel")
                return

        timer_key = f"{int(time.time() * 1000)}_{len(self._timers)}"
        st = _TimerState(
            key=timer_key,
            mode=mode,
            name=name,
            duration_seconds=duration,
        )
        self._timers.append(st)

        self.name.set("")
        self.status_label.config(text="", style="TLabel")

        self._render_or_update_row(st)

    def _render_or_update_row(self, st: _TimerState):
        widgets = self._row_widgets.get(st.key)
        if widgets is None:
            row = tk.Frame(self.scrollable_frame, bg="#FFFFFF", highlightbackground="#EFEFEF", highlightthickness=1)
            row.pack(fill="x", pady=6)

            left = tk.Frame(row, bg="#FFFFFF")
            left.pack(side="left", fill="x", expand=True, padx=10, pady=10)

            name_lbl = tk.Label(left, text=st.name, bg="#FFFFFF", fg="#1F1F1F", font=("Helvetica", 12, "bold"))
            name_lbl.pack(anchor="w")

            mode_lbl = tk.Label(
                left,
                text=("Countdown" if st.mode == "countdown" else "Stopwatch"),
                bg="#FFFFFF",
                fg="#6B6B6B",
                font=("Helvetica", 10),
            )
            mode_lbl.pack(anchor="w", pady=(2, 0))

            time_lbl = tk.Label(row, text="", bg="#FFFFFF", fg="#1F1F1F", font=("Helvetica", 18, "bold"))
            time_lbl.pack(side="left", padx=10)

            controls = ttk.Frame(row)
            controls.pack(side="right", padx=10)

            btn_start = ttk.Button(controls, text="Start", command=lambda k=st.key: self._toggle_start(k))
            btn_start.grid(row=0, column=0, padx=(0, 6))

            btn_reset = ttk.Button(controls, text="Reset", command=lambda k=st.key: self._reset_timer(k))
            btn_reset.grid(row=0, column=1, padx=(0, 6))

            btn_delete = ttk.Button(controls, text="Delete", command=lambda k=st.key: self._delete_timer(k))
            btn_delete.grid(row=0, column=2)

            widgets = {
                "row": row,
                "left": left,
                "name": name_lbl,
                "mode": mode_lbl,
                "time": time_lbl,
                "start": btn_start,
                "reset": btn_reset,
                "delete": btn_delete,
            }
            self._row_widgets[st.key] = widgets

        self._update_row_visuals(st)

    def _update_row_visuals(self, st: _TimerState):
        widgets = self._row_widgets.get(st.key)
        if widgets is None:
            return

        if self._closed or not self.frame.winfo_exists():
            return

        row: tk.Frame = widgets["row"]  # type: ignore[assignment]
        left: tk.Frame = widgets["left"]  # type: ignore[assignment]
        name_lbl: tk.Label = widgets["name"]  # type: ignore[assignment]
        mode_lbl: tk.Label = widgets["mode"]  # type: ignore[assignment]
        time_lbl: tk.Label = widgets["time"]  # type: ignore[assignment]
        start_btn: ttk.Button = widgets["start"]  # type: ignore[assignment]

        try:
            if st.mode == "countdown":
                remaining = self._get_countdown_remaining(st)
                time_lbl.config(text=_format_hhmmss(remaining))
            else:
                elapsed = int(self._get_elapsed(st))
                time_lbl.config(text=_format_hhmmss(elapsed))
        except Exception:
            return

        if st.finished and st.mode == "countdown":
            bg = "#6fcdac"
            fg = "#0B2B22"
        else:
            bg = "#FFFFFF"
            fg = "#1F1F1F"

        try:
            row.configure(bg=bg)
            left.configure(bg=bg)
            name_lbl.configure(bg=bg, fg=fg)
            mode_lbl.configure(bg=bg)
            time_lbl.configure(bg=bg, fg=fg)
        except Exception:
            pass

        if st.running:
            start_btn.config(text="Pause")
        else:
            start_btn.config(text="Start")

        if st.finished and st.mode == "countdown":
            start_btn.config(state="disabled")
        else:
            start_btn.config(state="normal")

    def _get_elapsed(self, st: _TimerState) -> float:
        if st.running and st.start_ts is not None:
            return st.elapsed_before + (time.time() - st.start_ts)
        return st.elapsed_before

    def _get_countdown_remaining(self, st: _TimerState) -> int:
        elapsed = self._get_elapsed(st)
        return max(0, int(round(st.duration_seconds - elapsed)))

    def _toggle_start(self, key: str):
        st = self._find_timer(key)
        if st is None:
            return

        if st.finished and st.mode == "countdown":
            return

        if st.running:
            st.elapsed_before = self._get_elapsed(st)
            st.running = False
            st.start_ts = None
        else:
            st.running = True
            st.start_ts = time.time()

        self._update_row_visuals(st)

    def _reset_timer(self, key: str):
        st = self._find_timer(key)
        if st is None:
            return

        st.running = False
        st.finished = False
        st.finished_notified = False
        st.start_ts = None
        st.elapsed_before = 0.0

        self._update_row_visuals(st)

    def _delete_timer(self, key: str):
        st = self._find_timer(key)
        if st is None:
            return

        self._timers = [t for t in self._timers if t.key != key]

        widgets = self._row_widgets.pop(key, None)
        if widgets is not None:
            try:
                widgets["row"].destroy()  # type: ignore[union-attr]
            except Exception:
                pass

    def _find_timer(self, key: str) -> _TimerState | None:
        for t in self._timers:
            if t.key == key:
                return t
        return None

    def _start_tick_loop(self):
        if self._tick_job is not None:
            try:
                self.root.after_cancel(self._tick_job)
            except Exception:
                pass
            self._tick_job = None

        self._tick()

    def _tick(self):
        if self._closed:
            return

        try:
            if not self.frame.winfo_exists():
                return
        except Exception:
            return

        for st in list(self._timers):
            if st.mode == "countdown" and not st.finished:
                if st.running:
                    remaining = self._get_countdown_remaining(st)
                    if remaining <= 0:
                        st.running = False
                        st.start_ts = None
                        st.finished = True

                if st.finished and not st.finished_notified:
                    st.finished_notified = True
                    self._notify_finished(st)

            self._update_row_visuals(st)

        self._tick_job = self.root.after(250, self._tick)

    def _notify_finished(self, st: _TimerState):
        if self.window is not None:
            try:
                self.window.deiconify()
            except Exception:
                pass
            try:
                self.window.lift()
            except Exception:
                pass
            try:
                self.window.focus_force()
            except Exception:
                pass

        if self.beep_on_finish.get():
            self._play_beep_sequence(count=4, delay_ms=450)

    def _play_beep_sequence(self, count: int, delay_ms: int):
        if self._closed:
            return

        def do_one(i: int):
            if self._closed:
                return
            try:
                self.root.bell()
            except Exception:
                pass
            if i + 1 < count:
                try:
                    self.root.after(delay_ms, lambda: do_one(i + 1))
                except Exception:
                    pass

        do_one(0)
