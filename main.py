import tkinter as tk
from app_gui import STMSpectraViewer

if __name__ == "__main__":
    root = tk.Tk()
    app = STMSpectraViewer(root)
    root.mainloop()