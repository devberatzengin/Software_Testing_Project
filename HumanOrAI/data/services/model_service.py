import os
import joblib
import numpy as np
import warnings

# Versiyon uyarılarını gizle
warnings.filterwarnings("ignore")

class ModelService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelService, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(base_dir, '..', 'models')
        
        self.models = {}
        self.vectorizer = None

        try:
            vec_path = os.path.join(models_dir, 'tfidf_vectorizer.joblib')
            self.vectorizer = joblib.load(vec_path)
            
            # Modelleri yükle
            model_files = {
                "Logistic Regression": "logistic_regression_model.joblib",
                "Naive Bayes": "naive_bayes_model.joblib",
                "Random Forest": "random_forest_model.joblib"
            }

            for name, filename in model_files.items():
                try:
                    path = os.path.join(models_dir, filename)
                    if os.path.exists(path):
                        loaded_model = joblib.load(path)
                        self.models[name] = loaded_model
                except Exception as e:
                    print(f"[UYARI] {name} yüklenemedi: {e}")

        except Exception as e:
            print(f"[KRİTİK] Başlatma hatası: {e}")

    # GÜNCELLEME: active_models parametresi eklendi
    def predict(self, text, active_models=None):
        if not text or not self.vectorizer:
            return None

        # Eğer kullanıcı hiç seçim yapmadıysa hepsini çalıştır
        if not active_models:
            active_models = self.models.keys()

        try:
            vectorized_text = self.vectorizer.transform([text])
        except:
            return None
        
        results = []
        ai_vote_count = 0
        total_valid_models = 0

        for name in active_models:
            if name not in self.models:
                continue
                
            model = self.models[name]
            try:
                # Scikit-learn versiyon hatası için YAMA
                # LogisticRegression eski sürümlerde olmayan özellikleri isteyebilir
                # Bunu try-except bloğu ile yönetiyoruz.
                probs = model.predict_proba(vectorized_text)[0]
                
                human_score = probs[0] * 100
                ai_score = probs[1] * 100
                
                label = "AI" if ai_score > 50 else "HUMAN"
                confidence = ai_score if label == "AI" else human_score
                
                if label == "AI": ai_vote_count += 1
                total_valid_models += 1

                results.append({
                    "model_name": name,
                    "label": label,
                    "confidence": round(confidence, 1),
                    "ai_prob": round(ai_score, 1),
                    "human_prob": round(human_score, 1),
                    "status": "success"
                })
            except Exception as e:
                # Model çalışmazsa arayüze hata bilgisi gönder
                results.append({
                    "model_name": name,
                    "status": "error",
                    "error_msg": "Versiyon Hatası"
                })

        if total_valid_models == 0:
            return {"error": "Hiçbir model başarıyla çalıştırılamadı."}

        # Sonuç Hesaplama
        final_verdict = "AI" if ai_vote_count >= (total_valid_models / 2) else "HUMAN"
        
        # Grafik için ortalama skorlar
        avg_ai = sum([r['ai_prob'] for r in results if r['status']=='success']) / total_valid_models
        avg_human = sum([r['human_prob'] for r in results if r['status']=='success']) / total_valid_models


        final_verdict = "AI" if avg_ai > 50 else "HUMAN"

        return {
            "individual_results": results,
            "final_verdict": final_verdict,
            "stats": {
                "avg_ai": round(avg_ai, 1),
                "avg_human": round(avg_human, 1)
            }
        }