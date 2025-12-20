import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

class SeleniumBrowserTests(unittest.TestCase):

    def setUp(self):
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless") # Arka planda çalıştırmak istersen aktif et
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.maximize_window()
        self.driver.get("http://127.0.0.1:5000")
        self.wait = WebDriverWait(self.driver, 10) # 10 saniyeye kadar bekleme tanımladık

    def test_case_1_successful_prediction(self):
        """Case 1: Metin analizi sonrası sonuç paneli görüntülenmeli."""
        driver = self.driver
        
        # 1. Metin alanına veri gir
        text_area = self.wait.until(EC.presence_of_element_located((By.NAME, "text_input")))
        text_area.send_keys("Yapay zeka teknolojileri hızla gelişiyor.")
        
        # 2. Formu gönder (XPATH yerine CSS Selector kullanarak 'submit' tipindeki butonu buluyoruz)
        # Bu yöntem butondaki metne değil, butonun fonksiyonuna bakar. Daha garantidir.
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()
        
        # 3. Sonuç kutusunun (verdict-box) gelmesini bekle
        result_box = self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "verdict-box")))
        
        # 4. Doğrulama
        self.assertIn("SONUÇ", result_box.text)
        print(" - Başarılı: Analiz sonucu ekranda görüldü.")

    def test_case_2_reset_functionality(self):
        """Case 2: Sıfırla butonu sayfayı başlangıç haline döndürmeli."""
        driver = self.driver
        
        # 1. Önce bir metin yazalım
        text_area = driver.find_element(By.NAME, "text_input")
        text_area.send_keys("Temizlenecek metin")
        
        # 2. "Sıfırla" linkine tıkla (HTML'de class="btn-outline-secondary")
        reset_link = driver.find_element(By.LINK_TEXT, "Sıfırla")
        reset_link.click()
        
        # 3. Textarea'nın boşaldığını doğrula
        time.sleep(1) # Sayfa yenilemesi için kısa bekleme
        text_area_after = driver.find_element(By.NAME, "text_input")
        self.assertEqual(text_area_after.get_attribute("value"), "")
        print(" - Başarılı: Sayfa sıfırlandı.")

    def test_case_3_checkbox_logic(self):
        """Case 3: Model seçim kutuları (Checkbox) aktif/pasif yapılabilmeli."""
        driver = self.driver
        
        # 1. Logistic Regression checkbox'ını bul (ID: m1)
        lr_checkbox = driver.find_element(By.ID, "m1")
        
        # 2. Eğer seçiliyse tıkla ve seçimini kaldır
        if lr_checkbox.is_selected():
            lr_checkbox.click()
        
        self.assertFalse(lr_checkbox.is_selected())
        
        # 3. Tekrar tıkla ve seçili yap
        lr_checkbox.click()
        self.assertTrue(lr_checkbox.is_selected())
        print(" - Başarılı: Checkbox yönetimi doğrulandı.")

    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()