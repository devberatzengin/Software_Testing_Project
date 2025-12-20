from tests.test_base import BaseTestCase

class TestNavigation(BaseTestCase):

    def test_homepage_loads(self):
        """Ana sayfa başarılı şekilde yükleniyor mu?"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_default_models_present(self):
        """Sayfa ilk açıldığında varsayılan modeller HTML içinde var mı?"""
        response = self.client.get('/')
        self.assertIn(b"Logistic Regression", response.data)
        self.assertIn(b"Naive Bayes", response.data)
        self.assertIn(b"Random Forest", response.data)

    def test_reset_button_redirects(self):
        """Reset rotası kullanıcıyı ana sayfaya yönlendiriyor mu?"""
        response = self.client.get('/reset')
        # 302: Redirect kodu, location: yönlendirilen yer
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/'))