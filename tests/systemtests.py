import unittest
import os
import sys
import time
import urllib.request
import urllib.error
from multiprocessing import Process

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_flask():
    """Run the Flask app (from app.py) in a separate process."""
    from app import app
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False
    )

    with app.app_context():
        from models import db
        db.create_all()

    # ⚠️ Must close reloader，avoid the child process fork
    app.run(host='127.0.0.1', port=5000, use_reloader=False)

def is_server_running(url, max_retries=10, retry_delay=0.5):
    for _ in range(max_retries):
        try:
            urllib.request.urlopen(url)
            return True
        except urllib.error.URLError:
            time.sleep(retry_delay)
    return False

# --------------------------------------------------------------------
# 3️⃣ Selenium-based system tests
# --------------------------------------------------------------------
class SimpleBadmintonTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import multiprocessing
        multiprocessing.set_start_method('spawn', force=True)

    def setUp(self):
        # 启动 Flask
        self.server_process = Process(target=run_flask, daemon=True)
        self.server_process.start()

        # 等待服务就绪
        self.base_url = "http://127.0.0.1:5000"
        if not is_server_running(self.base_url):
            self.fail("Flask server did not start properly")

        # 启动无头 Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Chrome 120+ 建议写法
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)

    def tearDown(self):
        if hasattr(self, "driver"):
            self.driver.quit()

        if hasattr(self, "server_process"):
            self.server_process.terminate()
            self.server_process.join(timeout=2)
            if self.server_process.is_alive():
                self.server_process.kill()

    # --------------------------------------------------------------
    # 以下测试用例原样保留
    # --------------------------------------------------------------
    def test_1_homepage_loads(self):
        self.driver.get(self.base_url + "/")
        self.assertIn("Badminton", self.driver.title)

    def test_2_login_page_loads(self):
        self.driver.get(self.base_url + "/login")
        header = self.driver.find_element(By.TAG_NAME, "h2").text.lower()
        self.assertIn("welcome back", header)

    def test_3_signup_page_loads(self):
        self.driver.get(self.base_url + "/signup")
        header = self.driver.find_element(By.TAG_NAME, "h2").text.lower()
        self.assertIn("create an account", header)

    def test_4_login_with_invalid_credentials(self):
        self.driver.get(self.base_url + "/login")
        self.driver.find_element(By.ID, "username").send_keys("invalid_user")
        self.driver.find_element(By.ID, "password").send_keys("wrong_password")
        self.driver.find_element(By.ID, "submit_button").click()

        WebDriverWait(self.driver, 5).until(EC.url_contains("/login"))
        self.assertIn("Invalid username or password", self.driver.page_source)
        self.assertIn("/login", self.driver.current_url)

    def test_5_how_it_works_page(self):
        self.driver.get(self.base_url + "/how-it-works")
        self.assertIn("How It Works", self.driver.title)
        self.assertIn("Getting Started with Badminton MASTER", self.driver.page_source)
        step_heading = self.driver.find_element(By.XPATH, "//div[contains(@class, 'flex')]/h3")
        self.assertIn("Create Your Account", step_heading.text)

if __name__ == "__main__":
    unittest.main()
