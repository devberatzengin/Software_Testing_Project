import os
import time

import pandas as pd
import arxiv
import sys

FILE_NAME = "../pipeline/human_data_arxiv.csv"
TOTAL_LIMIT = 3500
SAVE_INTERVAL = 20

def fetch_arxiv_data():
    if os.path.exists(FILE_NAME):
        try:
            existing_df = pd.read_csv(FILE_NAME)
            existing_titles = set(existing_df['title'].unique())
            current_counts = existing_df['subject'].value_counts().to_dict()
            print(f"{FILE_NAME} bulundu. Kaldığı yerden devam ediyor...")
            print(f"Mevcut durum: {current_counts}")

        except Exception as e:
            print(f"Hata! Dosya okunamadı: {e}, Yedeklenip yeni dosya oluşturuluyor.")
            os.rename(FILE_NAME, f"{FILE_NAME}_backup_{int(time.time())}.csv")
            existing_titles = set()
            current_counts = {}
            pd.DataFrame(columns=['text','label','source','subject','license','title']).to_csv(FILE_NAME, index=False)
    else:
        print(f"Yeni dosya oluşturuluyor: {FILE_NAME}")
        existing_titles = set()
        current_counts= {}
        pd.DataFrame(columns=['text', 'label', 'source', 'subject', 'license', 'title']).to_csv(FILE_NAME, index=False)

    queries = {
        "Evrim": 'cat:q-bio.PE',
        "Biyoloji": 'cat:q-bio.BM',
        "Müzik": 'all:music',
        "Matematik": 'cat:math.CO',
        "Fizik": 'cat:physics.gen_ph',
        "AI": 'cat:cs.AI',
        "İstatistik": 'cat:stat.ML',
        "Kuantum": 'cat:quant-ph'
    }

    per_category = TOTAL_LIMIT //len(queries)
    client = arxiv.Client()
    total_collected_session = 0

    try:
        for topic, query in queries.items():
            count_so_far =  current_counts.get(topic, 0)
            if count_so_far >= per_category:
                print(f"✅ '{topic}' tamamlanmış ({count_so_far}/{per_category}). Atlanıyor.")
                continue

            needed = per_category - count_so_far
            print(f"\n-> {topic} ketegorisi için {needed} adet daha veri aranıyor... Mevcut: {count_so_far}")
            search = arxiv.Search(
                query=query,
                max_results=needed + 100,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )

            batch_data = []
            topic_new_count = 0

            for result in client.results(search):
                if result.title in existing_titles:
                    continue

                summary = result.summary.replace('\n',' ').strip()
                if len(summary)<100:
                    continue

                if topic == 'Müzik' and 'music' not in summary.lower() and 'audio' not in summary.lower():
                    continue

                row = {
                    "text": summary,
                    "label": 0,
                    "source": "arxiv",
                    "subject": topic,
                    "license": "CC-BY/arXiv",
                    "title": result.title
                }
                batch_data.append(row)
                existing_titles.add(result.title)
                topic_new_count += 1
                total_collected_session += 1

                if len(batch_data) >= SAVE_INTERVAL:
                    save_batch(batch_data)
                    batch_data = []
                    print(f"{SAVE_INTERVAL} adet veri kaydedildi. Toplam konu: {count_so_far+topic_new_count}/{per_category}")

                if count_so_far + topic_new_count >= per_category:
                    break

            if batch_data:
                save_batch(batch_data)
                print(f"Kalan {len(batch_data)} veri kaydedildi.")

            print(f"'{topic}' tamamlandı.")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\nİşlem kullanıcı tarafından durduruldu!")
        print("Toplanan veriler kaydedildi!")
        sys.exit()

    except Exception as e:
        print(f"\n\nBeklenmedik bir hata oluştu: {e}")

    finally:
        print(f"\nOturum sonlandı. Bu oturumda toplam {total_collected_session} veri eklendi.")

def save_batch(data):
    if not data:
        return

    df = pd.DataFrame(data)
    df.to_csv(FILE_NAME, mode='a', header=False, index=False)

if __name__ == "__main__":
    fetch_arxiv_data()





















