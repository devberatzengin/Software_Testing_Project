import os
import time
import random
import json
import pandas as pd
import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv

# --- AYARLAR ---
load_dotenv()

AI_DATA_FILE = "ai_data_gemini.csv"
API_KEY = os.getenv("API_KEY")
SAVE_INTERVAL = 50
TARGET_COUNT = 3000
BATCH_SIZE = 5

# --- GÜNCELLENMİŞ VE TEMİZLENMİŞ MODEL LİSTESİ ---
# Senin 'list_models' çıktına göre SADECE çalışan ve hızlı modelleri ekledim.
# 404 veren eskiler çıkarıldı.
MODEL_LIST = [
    'models/gemini-2.5-flash',
    'models/gemini-2.0-flash',
    'models/gemini-2.0-flash-lite-preview-02-05',
    'models/gemini-2.0-flash-001',
    'models/gemini-2.0-flash-exp',  # Yeni eklendi (Genelde kotası rahattır)
    'models/gemini-2.0-flash-lite-001',  # Yeni eklendi
    'models/gemini-2.0-flash-lite'  # Yeni eklendi
]

# Konu Listesi
TOPICS = [
    "Evolutionary Biology (Evrim)",
    "Molecular Biology (Biyoloji)",
    "Music Theory and Audio Analysis (Müzik)",
    "Combinatorics and Mathematics (Matematik)",
    "General Physics (Fizik)",
    "Artificial Intelligence and Machine Learning (AI)",
    "Statistical Methods (İstatistik)",
    "Quantum Physics (Kuantum)"
]

if not API_KEY:
    raise ValueError("HATA: GEMINI_API_KEY bulunamadı!")

# Başlangıç yapılandırması
genai.configure(api_key=API_KEY)
current_model_index = 0


def get_current_model():
    """Şu anki sıradaki modeli döndürür."""
    model_name = MODEL_LIST[current_model_index]
    return genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})


def switch_model():
    """Bir sonraki modele geçer."""
    global current_model_index
    current_model_index = (current_model_index + 1) % len(MODEL_LIST)
    new_model_name = MODEL_LIST[current_model_index]
    print(f"\n🔄 Model Değiştiriliyor -> {new_model_name}\n")
    return get_current_model()


def init_files():
    existing_titles = set()
    if os.path.exists(AI_DATA_FILE):
        try:
            ai_df = pd.read_csv(AI_DATA_FILE)
            if 'title' in ai_df.columns:
                existing_titles = set(ai_df['title'].unique())
            print(f"📄 '{AI_DATA_FILE}' bulundu. {len(ai_df)} veri hazır. Devam ediliyor...")
        except:
            print("⚠️ Dosya hatası, yenisi oluşturuluyor.")
            pd.DataFrame(columns=['text', 'label', 'source', 'subject', 'license', 'title']).to_csv(AI_DATA_FILE,
                                                                                                    index=False)
    else:
        print(f"🆕 Yeni dosya oluşturuluyor: {AI_DATA_FILE}")
        pd.DataFrame(columns=['text', 'label', 'source', 'subject', 'license', 'title']).to_csv(AI_DATA_FILE,
                                                                                                index=False)
    return existing_titles


def generate_ai_data():
    existing_titles = init_files()
    current_count = len(existing_titles)

    if current_count >= TARGET_COUNT:
        print("✅ Zaten hedeflenen sayıya ulaşılmış!")
        return

    batch_data = []
    model = get_current_model()

    print(f"\n--- 🚀 MULTI-MODEL Veri Üretimi (Optimize Edildi) ---\n")
    print(f"📋 Aktif Model Sayısı: {len(MODEL_LIST)}")

    try:
        while current_count < TARGET_COUNT:
            topic_raw = random.choice(TOPICS)
            topic_eng = topic_raw.split('(')[0].strip()
            subject_label = topic_raw.split('(')[-1].strip(')')

            prompt = (
                f"You are an academic AI. Generate {BATCH_SIZE} unique, fake academic research paper abstracts "
                f"related to '{topic_eng}'. "
                f"Each abstract must be highly technical, 100-150 words long, and sound like a real publication. "
                f"Return ONLY a raw JSON list of objects. "
                f"JSON Schema: [{{\"title\": \"string\", \"abstract\": \"string\"}}, ...]"
            )

            success = False
            loop_protection = 0

            while not success:
                try:
                    response = model.generate_content(prompt)

                    if response.text:
                        try:
                            json_data = json.loads(response.text)
                        except json.JSONDecodeError:
                            clean_text = response.text.replace("```json", "").replace("```", "").strip()
                            try:
                                json_data = json.loads(clean_text)
                            except:
                                success = True
                                continue

                        items_added = 0
                        for item in json_data:
                            title = item.get("title")
                            abstract = item.get("abstract")

                            if not title or not abstract or title in existing_titles:
                                continue

                            new_row = {
                                "text": abstract,
                                "label": 1,
                                "source": MODEL_LIST[current_model_index],
                                "subject": subject_label,
                                "license": "Generated",
                                "title": title
                            }

                            batch_data.append(new_row)
                            existing_titles.add(title)
                            current_count += 1
                            items_added += 1

                        if items_added > 0:
                            print(
                                f"✅ +{items_added} Veri | Toplam: {current_count}/{TARGET_COUNT} | Model: {MODEL_LIST[current_model_index]}")
                            success = True
                            # Başarılı olursa döngü korumasını sıfırla
                            loop_protection = 0
                        else:
                            success = True

                            # Her başarılı işlemden sonra kısa bir bekleme (Kotayı rahatlatır)
                        time.sleep(3)

                except exceptions.ResourceExhausted:
                    print(f"⚠️ Kota Doldu ({MODEL_LIST[current_model_index]}) -> Değiştiriliyor...")
                    model = switch_model()
                    time.sleep(2)

                    loop_protection += 1
                    # Tüm modelleri denedik ve hepsi hata verdiyse uzun mola ver
                    if loop_protection >= len(MODEL_LIST):
                        wait_time = 120  # 2 Dakika tam soğuma
                        print(f"💤 TÜM MODELLER YORULDU! {wait_time} saniye tam soğuma molası...")
                        time.sleep(wait_time)
                        loop_protection = 0  # Sayacı sıfırla ve tekrar dene

                except Exception as e:
                    print(f"❌ Beklenmedik Hata ({MODEL_LIST[current_model_index]}): {e}")
                    # 404 gibi kalıcı hatalarda o modeli listeden silmeyi deneyebiliriz ama şimdilik geçelim
                    model = switch_model()
                    time.sleep(2)

            # Kaydetme
            if len(batch_data) >= SAVE_INTERVAL:
                save_batch(batch_data)
                batch_data = []
                print(f"💾 Veriler diske yazıldı.")

    except KeyboardInterrupt:
        print("\n⛔ İşlem durduruldu.")
    finally:
        if batch_data: save_batch(batch_data)
        print(f"\nOturum sonu. Toplam Veri: {current_count}")


def save_batch(data):
    if not data: return
    pd.DataFrame(data).to_csv(AI_DATA_FILE, mode='a', header=False, index=False)


if __name__ == "__main__":
    generate_ai_data()