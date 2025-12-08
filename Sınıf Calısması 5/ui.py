import tkinter as tk
from tkinter import messagebox
from logic import OyunMotoru

HUCRE_BOYUTU = 50
RENKLER = {
    "ana_tas": "#e67e22",
    "yan_tas": "#3498db",
    "duvar": "#2c3e50",
    "yol": "white"
}


class OyunPenceresi(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)

        # Mantık motorunu başlat
        self.motor = OyunMotoru(8, 8)

        self.secili_arac = "yan"
        self.oyun_aktif = False

        self.arayuz_olustur()
        self.izgara_ciz()

    def arayuz_olustur(self):
        # --- Sol: Canvas ---
        self.canvas = tk.Canvas(self, width=8 * HUCRE_BOYUTU, height=8 * HUCRE_BOYUTU, bg="white")
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.tiklama_olayi)

        # --- Sağ: Kontrol ---
        panel = tk.Frame(self, bg="#ecf0f1", width=200)
        panel.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(panel, text="ARAÇLAR", font=("Arial", 12, "bold"), bg="#ecf0f1").pack(pady=10)

        self.btn_ana = tk.Button(panel, text="★ Ana Taş", bg=RENKLER["ana_tas"], fg="white",
                                 command=lambda: self.arac_sec("ana"))
        self.btn_ana.pack(fill=tk.X, padx=10, pady=5)

        self.btn_yan = tk.Button(panel, text="● Yan Taş", bg=RENKLER["yan_tas"], fg="white",
                                 command=lambda: self.arac_sec("yan"))
        self.btn_yan.pack(fill=tk.X, padx=10, pady=5)

        self.btn_duvar = tk.Button(panel, text="■ Duvar", bg=RENKLER["duvar"], fg="white",
                                   command=lambda: self.arac_sec("duvar"))
        self.btn_duvar.pack(fill=tk.X, padx=10, pady=5)

        self.btn_sil = tk.Button(panel, text="Silgi", command=lambda: self.arac_sec("sil"))
        self.btn_sil.pack(fill=tk.X, padx=10, pady=5)

        tk.Frame(panel, height=2, bg="grey").pack(fill=tk.X, pady=20)

        self.btn_basla = tk.Button(panel, text="▶ BAŞLAT", bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
                                   command=self.oyunu_baslat)
        self.btn_basla.pack(fill=tk.X, padx=10, pady=5)

        self.lbl_info = tk.Label(panel, text="Seçili: Yan Taş", fg="red", bg="#ecf0f1")
        self.lbl_info.pack(pady=10)

    def arac_sec(self, tip):
        self.secili_arac = tip
        self.lbl_info.config(text=f"Seçili: {tip.upper()}")

    def izgara_ciz(self):
        self.canvas.delete("grid")
        for i in range(9):
            p = i * HUCRE_BOYUTU
            self.canvas.create_line(0, p, 8 * HUCRE_BOYUTU, p, tags="grid")
            self.canvas.create_line(p, 0, p, 8 * HUCRE_BOYUTU, tags="grid")

    def tiklama_olayi(self, event):
        if self.oyun_aktif: return

        c = event.x // HUCRE_BOYUTU
        r = event.y // HUCRE_BOYUTU

        if self.secili_arac == "sil":
            self.motor.nesne_sil(r, c)
        else:
            self.motor.nesne_ekle(r, c, self.secili_arac)

        self.sahneyi_guncelle()

    def sahneyi_guncelle(self):
        self.canvas.delete("nesne")
        mesafeler = self.motor.bfs_mesafe_hesapla()

        for (r, c), tip in self.motor.grid_nesneleri.items():
            x, y = c * HUCRE_BOYUTU, r * HUCRE_BOYUTU
            cx, cy = x + HUCRE_BOYUTU / 2, y + HUCRE_BOYUTU / 2

            if tip == "duvar":
                self.canvas.create_rectangle(x, y, x + HUCRE_BOYUTU, y + HUCRE_BOYUTU, fill=RENKLER["duvar"],
                                             tags="nesne")
            elif tip == "ana":
                self.canvas.create_oval(x + 5, y + 5, x + HUCRE_BOYUTU - 5, y + HUCRE_BOYUTU - 5,
                                        fill=RENKLER["ana_tas"], outline="white", width=2, tags="nesne")
            elif tip == "yan":
                self.canvas.create_oval(x + 10, y + 10, x + HUCRE_BOYUTU - 10, y + HUCRE_BOYUTU - 10,
                                        fill=RENKLER["yan_tas"], outline="white", tags="nesne")
                dist = mesafeler.get((r, c), "?")
                self.canvas.create_text(cx, cy, text=str(dist), fill="white", font=("Arial", 10, "bold"), tags="nesne")

    def oyunu_baslat(self):
        if not self.motor.ana_tas_konumu:
            messagebox.showwarning("Hata", "Ana Taş Yok!")
            return

        self.oyun_aktif = True
        self.btn_basla.config(state="disabled")
        self.animasyon_dongusu()

    def animasyon_dongusu(self):
        # Mantık motoruna "1 adım ilerlet" diyoruz
        hareket_var = self.motor.bir_adim_yurut()

        self.sahneyi_guncelle()

        if hareket_var and self.motor.yan_taslar:
            self.after(500, self.animasyon_dongusu)
        else:
            self.oyun_aktif = False
            self.btn_basla.config(state="normal")
            if not self.motor.yan_taslar:
                messagebox.showinfo("Bitti", "Tüm taşlar toplandı!")