import tkinter as tk
from ui import OyunPenceresi

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Taş Toplama Projesi - Modüler Yapı")

    root.geometry("600x450")

    app = OyunPenceresi(root)

    root.mainloop()