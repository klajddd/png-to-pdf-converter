import tkinterdnd2 as TkinterDnD
from src.gui.shell import ShellApp

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ShellApp(root)
    root.mainloop()