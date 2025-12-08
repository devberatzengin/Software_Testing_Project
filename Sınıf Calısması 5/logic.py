from collections import deque


class OyunMotoru:
    def __init__(self, satir=8, sutun=8):
        self.satir = satir
        self.sutun = sutun
        self.grid_nesneleri = {}  # (r, c) -> "duvar", "ana", "yan"
        self.yan_taslar = []  # Koordinat listesi
        self.ana_tas_konumu = None

    def nesne_ekle(self, r, c, tip):
        # Sınırlar içinde mi?
        if not (0 <= r < self.satir and 0 <= c < self.sutun):
            return False

        # Önce o kareyi temizle
        self.nesne_sil(r, c)

        # Yeni tipi ekle
        if tip == "ana":
            # Eski ana taşı sil (sadece 1 tane olabilir)
            if self.ana_tas_konumu:
                if self.ana_tas_konumu in self.grid_nesneleri:
                    del self.grid_nesneleri[self.ana_tas_konumu]
            self.ana_tas_konumu = (r, c)

        elif tip == "yan":
            self.yan_taslar.append((r, c))

        self.grid_nesneleri[(r, c)] = tip
        return True

    def nesne_sil(self, r, c):
        if (r, c) in self.grid_nesneleri:
            tip = self.grid_nesneleri[(r, c)]
            if tip == "ana":
                self.ana_tas_konumu = None
            elif tip == "yan":
                if (r, c) in self.yan_taslar:
                    self.yan_taslar.remove((r, c))
            del self.grid_nesneleri[(r, c)]

    def bfs_mesafe_hesapla(self):
        """Tüm karelerin ana taşa olan uzaklığını hesaplar (Duvarları aşamaz)"""
        if not self.ana_tas_konumu:
            return {}

        mesafeler = {}
        kuyruk = deque([(self.ana_tas_konumu, 0)])
        ziyaret_edilen = {self.ana_tas_konumu}
        mesafeler[self.ana_tas_konumu] = 0

        while kuyruk:
            (r, c), dist = kuyruk.popleft()

            # 4 Yön (Yukarı, Aşağı, Sol, Sağ)
            komsular = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]

            for nr, nc in komsular:
                if 0 <= nr < self.satir and 0 <= nc < self.sutun:
                    # Duvar değilse ve ziyaret edilmediyse
                    if (nr, nc) not in ziyaret_edilen:
                        if self.grid_nesneleri.get((nr, nc)) != "duvar":
                            ziyaret_edilen.add((nr, nc))
                            mesafeler[(nr, nc)] = dist + 1
                            kuyruk.append(((nr, nc), dist + 1))
        return mesafeler

    def bir_adim_yurut(self):
        """Tüm yan taşları ana taşa 1 adım yaklaştırır. Hareket olduysa True döner."""
        mesafeler = self.bfs_mesafe_hesapla()
        yeni_yan_taslar = []
        hareket_oldu = False

        # Mevcut yan taşlar üzerinden geç
        for (r, c) in self.yan_taslar:
            # Grid'den eski konumu sil
            if (r, c) in self.grid_nesneleri and self.grid_nesneleri[(r, c)] == "yan":
                del self.grid_nesneleri[(r, c)]

            # Ana taşa ulaştı mı?
            if (r, c) == self.ana_tas_konumu:
                hareket_oldu = True
                continue  # Listeye ekleme, yok oldu.

            # En iyi komşuyu bul
            en_iyi_konum = (r, c)
            min_mesafe = mesafeler.get((r, c), 9999)

            komsular = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
            for nr, nc in komsular:
                if (nr, nc) in mesafeler and mesafeler[(nr, nc)] < min_mesafe:
                    min_mesafe = mesafeler[(nr, nc)]
                    en_iyi_konum = (nr, nc)

            # Yeni konuma koy
            if en_iyi_konum != self.ana_tas_konumu:
                self.grid_nesneleri[en_iyi_konum] = "yan"
                yeni_yan_taslar.append(en_iyi_konum)
            else:
                # Ana taşa girdi
                pass

            if en_iyi_konum != (r, c):
                hareket_oldu = True

        self.yan_taslar = yeni_yan_taslar

        # Ana taşı yanlışlıkla silinmekten koru
        if self.ana_tas_konumu:
            self.grid_nesneleri[self.ana_tas_konumu] = "ana"

        return hareket_oldu