def satranc_dizilimi_bul(n):
    gecerli_dizilimler = []

    def olustur(suanki_dizilim):
        if len(suanki_dizilim) == n:
            gecerli_dizilimler.append(suanki_dizilim)
            return

        olustur(suanki_dizilim + 'b')

        if suanki_dizilim[-1] != 's':
            olustur(suanki_dizilim + 's')

    olustur('b')
    return gecerli_dizilimler

def main():
    print("==========================================")
    print("   SATRANÇ DİZİLİM HESAPLAYICI (v1.0)   ")
    print("==========================================")
    print("Çıkmak için 'q' tuşuna basıp enterlayın.\n")

    while True:
        kullanici_girisi = input("Piyon sayısını giriniz (N): ")

        if kullanici_girisi.lower() == 'q':
            print("Programdan çıkılıyor...")
            break

        try:
            n = int(kullanici_girisi)

            if n <= 0:
                print("-> Hata: Lütfen 0'dan büyük bir sayı giriniz!\n")
                continue

            print(f"\nHesaplanıyor (N={n})...")
            sonuclar = satranc_dizilimi_bul(n)

            print(f"-> Toplam Olasılık Sayısı: {len(sonuclar)}")
            print(f"-> Dizilimler: {', '.join(sonuclar)}")
            print("-" * 40)

        except ValueError:
            print("-> Hata: Lütfen geçerli bir TAMSAYI giriniz!\n")


if __name__ == "__main__":
    main()