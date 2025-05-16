import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from multiprocessing import Process
import time
import urllib.request
import urllib.error
import os
import sys

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app


def run_flask():
    """Run Flask app for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        from models import db
        db.create_all()

    app.run(host='127.0.0.1', port=5000, use_reloader=False)


def is_server_running(url, max_retries=10, retry_delay=0.5):
    """Check if server is running with retries."""
    for i in range(max_retries):
        try:
            urllib.request.urlopen(url)
            return True
        except urllib.error.URLError:
            if i < max_retries - 1:
                time.sleep(retry_delay)
            continue
    return False


class SimpleBadmintonTests(unittest.TestCase):
    """Basic UI tests for Badminton Tournament Manager application."""

    @classmethod
    def setUpClass(cls):
        """Class setup that runs once before all tests."""
        # For Windows compatibility
        import multiprocessing
        multiprocessing.set_start_method('spawn', force=True)

    def setUp(self):
        """Set up WebDriver before each test."""
        # Start the flask server on a different thread
        self.server_process = Process(target=run_flask)
        self.server_process.daemon = True  # Ensures process is terminated when main process exits
        self.server_process.start()

        # Wait for server to be available
        self.base_url = "http://127.0.0.1:5000"
        if not is_server_running(self.base_url, max_retries=10, retry_delay=0.5):
            self.fail("Flask server did not start properly")

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # Initialize the WebDriver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)  # seconds

    def tearDown(self):
        """Close WebDriver and server after each test."""
        if hasattr(self, 'driver'):
            self.driver.quit()

        if hasattr(self, 'server_process'):
            self.server_process.terminate()
            self.server_process.join(timeout=2)  # Give it time to terminate gracefully

            # Force kill if still alive
            if self.server_process.is_alive():
                self.server_process.kill()

    def test_1_homepage_loads(self):
        """Test that the homepage loads correctly."""
        self.driver.get(self.base_url + "/")
        self.assertIn("Badminton", self.driver.title)

    def test_2_login_page_loads(self):
        """Test that the login page loads correctly."""
        self.driver.get(self.base_url + "/login")
        header = self.driver.find_element(By.TAG_NAME, "h2").text.lower()
        self.assertIn("welcome back", header)

    def test_3_signup_page_loads(self):
        """Test that the signup page loads correctly."""
        self.driver.get(self.base_url + "/signup")
        header = self.driver.find_element(By.TAG_NAME, "h2").text.lower()
        self.assertIn("create an account", header)

    def test_4_login_with_invalid_credentials(self):
        """Test login validation with invalid credentials."""
        self.driver.get(self.base_url + "/login")

        # Find username and password
        username_field = self.driver.find_element(By.ID, "username")
        password_field = self.driver.find_element(By.ID, "password")

        # Enter invalid data
        username_field.send_keys("invalid_user")
        password_field.send_keys("wrong_password")

        # Submit the form
        submit_button = self.driver.find_element(By.ID, "submit_button")
        submit_button.click()

        # Wait for the page to load after submission and check if we're still on the login page
        WebDriverWait(self.driver, 5).until(
            EC.url_contains("/login")
        )

        # Check for any error indication - this could be:
        # 1. An error message displayed on the page
        self.assertIn("Invalid username or password", self.driver.page_source)
        # 2. The URL still being the login page
        self.assertIn("/login", self.driver.current_url)

    def test_5_how_it_works_page(self):
        """Test that the 'How It Works' page loads correctly."""
        self.driver.get(self.base_url + "/how-it-works")

        # Verify the title contains "How It Works"
        self.assertIn("How It Works", self.driver.title)

        # Verify the contents
        page_content = self.driver.page_source
        self.assertIn("Getting Started with Badminton MASTER", page_content)

        # Verify step-by-step guide section
        step_heading = self.driver.find_element(By.XPATH, "//div[contains(@class, 'flex')]/h3")
        self.assertIn("Create Your Account", step_heading.text)


if __name__ == "__main__":
    unittest.main()