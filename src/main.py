import tkinter as tk

try:
    import tkinterdnd2 as TkinterDnD
except Exception:  # pragma: no cover
    TkinterDnD = None

from src.gui.shell import ShellApp

if __name__ == "__main__":
    root = TkinterDnD.Tk() if TkinterDnD is not None else tk.Tk()
    root.title("UtilityBox")
    app = ShellApp(root)
    root.mainloop()