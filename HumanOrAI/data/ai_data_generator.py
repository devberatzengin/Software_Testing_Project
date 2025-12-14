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
SAVE_INTERVAL = 100  # Artık çok hızlıyız, 100'de bir kaydetmek yeterli
TARGET_COUNT = 31
00
BATCH_SIZE = 10  # Tek seferde 10 veri iste (Paid Tier bunu rahat kaldırır)

MODEL_LIST = [
    'models/gemini-2.5-pro',
    'models/gemini-2.5-flash'

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

genai.configure(api_key=API_KEY)
current_model_index = 0


def get_current_model():
    model_name = MODEL_LIST[current_model_index]
    # JSON modu aktif
    return genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})


def switch_model():
    """Hata durumunda diğer modele geçer."""
    global current_model_index
    current_model_index = (current_model_index + 1) % len(MODEL_LIST)
    new_model_name = MODEL_LIST[current_model_index]
    print(f"\n⚡ Model Değişiyor -> {new_model_name}\n")
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

    print(f"\n--- 💎 PREMIUM Veri Üretimi Başlıyor (Batch: {BATCH_SIZE}) ---\n")

    try:
        while current_count < TARGET_COUNT:
            topic_raw = random.choice(TOPICS)
            topic_eng = topic_raw.split('(')[0].strip()
            subject_label = topic_raw.split('(')[-1].strip(')')

            prompt = (
                f"You are an expert academic researcher. Generate {BATCH_SIZE} unique, highly sophisticated research paper abstracts "
                f"in the field of '{topic_eng}'. "
                f"Each abstract must be 120-180 words, use dense technical terminology, and mimic top-tier journal standards. "
                f"Return ONLY a raw JSON list. "
                f"JSON Schema: [{{\"title\": \"string\", \"abstract\": \"string\"}}, ...]"
            )

            success = False
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
                        else:
                            success = True

                            # Bekleme süresini 0.5 saniyeye indirdik! (Paid Tier gücü)
                        time.sleep(0.5)

                except exceptions.ResourceExhausted:
                    # Ücretli planda bile nadiren kota dolabilir, o zaman diğer modele geç
                    print(f"⚠️ Kota Sınırı ({MODEL_LIST[current_model_index]}) -> Diğer modele geçiliyor...")
                    model = switch_model()
                    time.sleep(1)

                except Exception as e:
                    print(f"❌ Hata: {e} -> Geçiliyor...")
                    model = switch_model()
                    time.sleep(1)

            # Kaydetme
            if len(batch_data) >= SAVE_INTERVAL:
                save_batch(batch_data)
                batch_data = []
                print(f"💾 {SAVE_INTERVAL}+ Veri diske yazıldı.")

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