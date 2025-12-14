import pandas as pd
import numpy as np
import os
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

DATA_PATH = "3-cleaned_preprocessed_data.csv"
MODEL_DIR = "../models"

if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)


def load_data():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"HATA: '{DATA_PATH}' bulunamadı! Lütfen önce EDA notebook'unu çalıştır.")

    print("⏳ Veri yükleniyor...")
    df = pd.read_csv(DATA_PATH)

    df.dropna(subset=['cleaned_text'], inplace=True)
    return df


def train_and_evaluate():
    df = load_data()
    X = df['cleaned_text']
    y = df['label']

    print(f"Toplam Veri Sayısı: {len(df)}")
    print(f"Dağılım -> İnsan: {len(df[y == 0])} | AI: {len(df[y == 1])}")

    print("\n✂️  Veri seti bölünüyor (Train: %80, Test: %20)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print("🧮 TF-IDF Vektörleştirme işlemi yapılıyor...")
    # max_features=5000: En çok kullanılan 5.000 kelimeyi öğren (Gereksiz kelimeleri atar, hızlandırır)
    vectorizer = TfidfVectorizer(max_features=5000)

    X_train_vec = vectorizer.fit_transform(X_train)
    # Test setini dönüştür (Transform)
    X_test_vec = vectorizer.transform(X_test)

    joblib.dump(vectorizer, f"{MODEL_DIR}/tfidf_vectorizer.joblib")
    print(f"💾 Vectorizer kaydedildi: {MODEL_DIR}/tfidf_vectorizer.joblib")

    models = {
        "Naive Bayes": MultinomialNB(),
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42)
    }

    results = {}

    print("\n🚀 MODELLER EĞİTİLİYOR...\n")

    for name, model in models.items():
        print(f"⚙️  {name} Eğitiliyor...")
        model.fit(X_train_vec, y_train)

        y_pred = model.predict(X_test_vec)
        acc = accuracy_score(y_test, y_pred)
        results[name] = acc

        print(f"✅  {name} Başarısı: %{acc * 100:.2f}")

        # Dosya adı örn: naive_bayes_model.joblib
        filename = f"{MODEL_DIR}/{name.lower().replace(' ', '_')}_model.joblib"
        joblib.dump(model, filename)

        print(classification_report(y_test, y_pred, target_names=['Human', 'AI']))
        print("-" * 50)

    print("\n🏆 --- FİNAL SONUÇLAR ---")
    best_model_name = max(results, key=results.get)
    print(f"En Başarılı Model: {best_model_name} (%{results[best_model_name] * 100:.2f})")

    plt.figure(figsize=(8, 5))
    sns.barplot(x=list(results.keys()), y=list(results.values()), palette='viridis')
    plt.title("Model Başarı Karşılaştırması (Accuracy)")
    plt.ylim(0.8, 1.0)
    plt.ylabel("Accuracy Score")
    plt.savefig(f"{MODEL_DIR}/model_comparison.png")
    print(f"📊 Karşılaştırma grafiği kaydedildi: {MODEL_DIR}/model_comparison.png")


if __name__ == "__main__":
    train_and_evaluate()