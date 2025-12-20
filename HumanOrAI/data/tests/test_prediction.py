from unittest.mock import patch
from tests.test_base import BaseTestCase

class TestPrediction(BaseTestCase):

    @patch('services.model_service.ModelService.predict')
    def test_successful_prediction(self, mock_predict):
        """Form dolu gönderildiğinde tahmin sonucu ekranda görünüyor mu?"""
        
        # HTML'in beklediği karmaşık yapıyı mock olarak tanımlıyoruz
        mock_predict.return_value = {
            "predictions": {"Logistic Regression": "Positive"},
            "stats": {
                "avg_ai": 0.45,
                "avg_human": 0.55
            }
        }
        
        payload = {
            'text_input': 'Harika bir deneyimdi',
            'models': ['Logistic Regression']
        }
        
        response = self.client.post('/', data=payload)
        
        self.assertEqual(response.status_code, 200)
        # HTML içinde stats değerlerinin basılıp basılmadığını kontrol edelim
        self.assertIn(b"0.45", response.data)
        mock_predict.assert_called_once()

    def test_post_with_empty_text(self):
        """Metin kutusu boşken tahmin yapılmamalı."""
        response = self.client.post('/', data={'text_input': '', 'models': ['Naive Bayes']})
        self.assertEqual(response.status_code, 200)
        # Eğer sonucun boş kalmasını bekliyorsanız buna dair bir kontrol eklenebilir