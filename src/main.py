import tkinterdnd2 as TkinterDnD
from src.gui.app_gui import PNGtoPDFConverter

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = PNGtoPDFConverter(root)
    root.mainloop()