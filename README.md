# AI vs Insan Tespit Sistemi (Yazilim Sinama Projesi)

Bu proje, bir yazilim testi dersi icin gelistirilmis, metinlerin Yapay Zeka (AI) tarafindan mi yoksa Insan tarafindan mi yazildigini tespit etmeyi amaclayan makine ogrenmesi tabanli bir web uygulamasidir.

Kullanici arayuzu Flask ile gelistirilmis olup, tahmin servisi scikit-learn tabanli makine ogrenmesi modelleri ile entegre calismaktadir.

---

## Proje Ozeti

Bu depo, universitedeki Yazilim Sinama dersi kapsaminda gelistirilen ve yapay zeka tarafindan uretilen metinleri insan tarafindan yazilanlardan ayirmayi hedefleyen bir projedir.

Proje, uc farkli makine ogrenmesi (ML) modelini ayni anda kullanir ve cogunluk oylamasi (ensemble) yontemi ile nihai bir karar uretir.

---

## Temel Ozellikler

* Coklu Model Mimarisi: Uc farkli makine ogrenmesi modeli (Logistic Regression, Naive Bayes, Random Forest) ayni anda calistirilabilir.
* Secmeli Analiz: Kullanici, analiz icin istedigi modelleri checkbox uzerinden secebilir.
* Cogunluk Oylamasi (Ensemble): Nihai karar, secili modellerin tahminlerinin cogunluguna gore belirlenir.
* Gorsellestirme: Model tahminlerinin guven skorlarini ve ortalama olasilik dagilimini Chart.js ile gorsellestirir.
* Basit ve Etkilesimli Arayuz: Flask ve Bootstrap kullanilarak hizli bir web arayuzu sunulur.

---

## Kullanilan Teknolojiler

| Alan                     | Teknoloji                      |
| ------------------------ | ------------------------------ |
| Web Catisi               | Flask                          |
| Makine Ogrenmesi         | scikit-learn (sklearn), joblib |
| Veri Analizi             | pandas, numpy, seaborn         |
| Vektorlestirme           | TfidfVectorizer (TF-IDF)       |
| Arayuz / Frontend        | HTML, Bootstrap 5, Chart.js    |
| Veri Toplama (Opsiyonel) | arxiv, google-generativeai     |

---

## Proje Yapisi

```
Software_Testing_Project/
├── README.md
└── HumanOrAI/
    └── data/
        ├── app.py
        ├── requirements.txt
        ├── services/
        │   └── model_service.py
        ├── templates/
        │   └── index.html
        ├── models/
        │   ├── tfidf_vectorizer.joblib
        │   ├── logistic_regression_model.joblib
        │   ├── naive_bayes_model.joblib
        │   └── random_forest_model.joblib
        └── pipeline/
            └── train_mdels.py
```

---

## Kurulum ve Calistirma

### Gerekli Kutuphaneler

Gerekli Python kutuphanelerini asagidaki komut ile yukleyin:

```bash
pip install -r HumanOrAI/data/requirements.txt
pip install flask
```

### Uygulamayi Baslatma

Flask uygulamasini calistirmak icin:

```bash
python HumanOrAI/data/app.py
```

Uygulama varsayilan olarak asagidaki adreste calisir:

```
http://127.0.0.1:5000/
```

---

## Model Egitimi (Opsiyonel)

Eger modelleri yeniden egitmek veya veri seti uzerinde degisiklik yapmak isterseniz, asagidaki script calistirilabilir.

Not: `3-cleaned_preprocessed_data.csv` dosyasi, `train_mdels.py` ile ayni dizinde bulunmalidir.

```bash
python HumanOrAI/data/pipeline/train_mdels.py
```

Bu script su adimlari gerceklestirir:

1. Veri setini yukler
2. Veriyi %80 egitim, %20 test olacak sekilde ayirir
3. TF-IDF vektorleyiciyi egitir ve kaydeder
4. Naive Bayes, Logistic Regression ve Random Forest modellerini egitir
5. Egitilen modelleri `.joblib` formatinda kaydeder

---

## Model Servisi

### ModelService (model_service.py)

* ModelService sinifi Singleton mantigi ile calisir
* Uygulama basladiginda modeller yalnizca bir kez yuklenir
* `initialize()` metodu, TF-IDF vektorleyiciyi ve tum egitilmis modelleri bellege alir
* `predict(text, active_models)` metodu:

  * Girilen metni vektorlesitirir
  * Secilen her model icin `predict_proba` kullanarak olasilik hesaplar
  * Her model icin AI veya HUMAN etiketi uretir
  * Cogunluk oylamasina gore nihai karari belirler
  * Ortalama AI ve HUMAN olasiliklarini gorsellestirme icin dondurur

---

## Notlar

* Proje egitsel amacla gelistirilmistir
* Gercek dunya senaryolari icin daha buyuk ve dengeli veri setleri ile egitim onerilir
* Ensemble yapi, tekil modellere gore daha dengeli sonuclar uretir

---
