import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


class SimpleBadmintonTests(unittest.TestCase):
    """Basic UI tests for Badminton Tournament Manager application."""

    def setUp(self):
        """Set up WebDriver before each test."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)  # seconds
        self.base_url = "http://127.0.0.1:5000"

    def tearDown(self):
        """Close WebDriver after each test."""
        self.driver.quit()

    def test_1_homepage_loads(self):
        """Test that the homepage loads correctly."""
        self.driver.get(self.base_url + "/")
        self.assertIn("Badminton", self.driver.title)

    def test_2_login_page_loads(self):
        """Test that the login page loads correctly."""
        self.driver.get(self.base_url + "/login")
        header = self.driver.find_element(By.TAG_NAME, "h1").text.lower()
        self.assertIn("login", header)

    def test_3_signup_page_loads(self):
        """Test that the signup page loads correctly."""
        self.driver.get(self.base_url + "/signup")
        header = self.driver.find_element(By.TAG_NAME, "h1").text.lower()
        self.assertIn("sign up", header)

    def test_4_login_with_invalid_credentials(self):
        """Test login validation with invalid credentials."""
        

    def test_5_how_it_works_page(self):
        """Test that the 'How It Works' page loads correctly."""
        


if __name__ == "__main__":
    unittest.main()
