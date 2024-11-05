from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import logging
import os
import random
import string
import time

# Set up logging
log_dir = 'crawler_logs'
timestamp = datetime.now().strftime('%Y%m%d_%H%M')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, f'{timestamp}_crawler.log'), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def generate_random_string():
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(10))


def edit_bio(username, bio, driver):
    try:
        profile_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='nav-link' and text()='Profile']"))
        )
        profile_link.click()
        driver.find_element(By.LINK_TEXT, 'Edit your profile').click()
        driver.find_element(By.ID, 'about_me').clear()
        driver.find_element(By.ID, 'about_me').send_keys(bio)
        driver.find_element(By.ID, 'submit').click()
        success = driver.find_element(By.CLASS_NAME, 'alert-info').text
        if success == 'Your changes have been saved.':
            logging.info(f"Bio updated for user '{username}'")
        else:
            logging.error(f"Bio update failed for user '{username}'")
    except Exception as e:
        logging.error(f"An error occurred while editing the bio: {e}")


def register(username, password, driver):
    driver.find_element(By.LINK_TEXT, 'Click to Register!').click()
    driver.find_element(By.ID, 'username').send_keys(username)
    driver.find_element(By.ID, 'email').send_keys(username + '@gmail.com')
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'password2').send_keys(password)
    driver.find_element(By.ID, 'submit').click()
    success = driver.find_element(By.CLASS_NAME, 'alert-info').text
    if success == 'Congratulations, you are now a registered user!':
        logging.info(f"Registration successful for user '{username}'")
    else:
        logging.error(f"Registration failed for user '{username}'")


def login(username, password, driver):
    try:
        driver.find_element(By.ID, 'username').send_keys(username)
        driver.find_element(By.ID, 'password').send_keys(password)
        driver.find_element(By.ID, 'submit').click()
        success = driver.find_element(By.TAG_NAME, 'h1').text
        if success == f'Hi, {username}!':
            print(f"Login successful for user '{username}'")
            return True
        else:
            print(f"Login failed for user '{username}'")
            return False
    except Exception as e:
        print(f"An error occurred during login for '{username}': {e}")
        return False


def logout(username, driver):
    try:
        profile_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='nav-link' and text()='Logout']"))
        )
        profile_link.click()
        success = driver.find_element(By.CLASS_NAME, 'alert-info').text
        if success == 'Please log in to access this page.':
            logging.info(f"Logout successful for '{username}'")
        else:
            logging.error(f"Logout failed for '{username}'")
    except Exception as e:
        logging.error(f"Failed to logout for user '{username}': {e}")


def post(username, message, driver):
    driver.find_element(By.ID, 'post').send_keys(message)
    driver.find_element(By.ID, 'submit').click()
    posts = driver.find_elements(By.TAG_NAME, 'span')
    for post in posts:
        if post.text == message:
            logging.info(f"'{username}' submitted a post successfully")
            return
    logging.info(f"'{username}' post failed")


def send_private_message(username, target_username, message, driver):
    try:
        explore_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Explore"))
        )
        explore_link.click()
        user_links = driver.find_elements(By.CLASS_NAME, "user_popup")
        for link in user_links:
            if link.text.strip() == target_username:
                link.click()
                break
        else:
            print(f"Could not find a link matching the target username: '{target_username}'")
            return

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Send private message"))
        ).click()

        message_textarea = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'textarea'))
        )
        message_textarea.send_keys(message)
        submit_button = driver.find_element(By.ID, 'submit')
        submit_button.click()

        success_message = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-info'))
        ).text
        if success_message == 'Your message has been sent.':
            print(f"Private message sent from '{username}' to '{target_username}'")
        else:
            print(f"Private message failed for '{username}' to '{target_username}'")
    except Exception as e:
        print(f"An error occurred while sending private message to '{target_username}': {e}")


class WebDriverPool:
    """A pool of WebDriver instances to optimize reuse and reduce setup time."""
    def __init__(self, size):
        self.pool = Queue(maxsize=size)
        for _ in range(size):
            self.pool.put(self.create_webdriver())

    def create_webdriver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1200,900")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("http://127.0.0.1:3000")
        return driver

    def acquire(self):
        """Acquire a WebDriver instance from the pool."""
        return self.pool.get()

    def release(self, driver):
        """Release a WebDriver instance back to the pool."""
        self.pool.put(driver)

    def close_all(self):
        """Close all WebDriver instances in the pool."""
        while not self.pool.empty():
            driver = self.pool.get()
            driver.quit()


def send_messages_multithreaded(tasks, webdriver_pool, max_workers=4):
    """Send messages concurrently with WebDriver instance reuse."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for username, password, target_username, message in tasks:
            driver = webdriver_pool.acquire()
            futures.append(
                executor.submit(process_message_task, username, password, target_username, message, driver, webdriver_pool)
            )

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f"Generated an exception: {exc}")


def process_message_task(username, password, target_username, message, driver, webdriver_pool):
    """Log in, send a private message, and release the WebDriver back to the pool."""
    try:
        if login(username, password, driver):
            send_private_message(username, target_username, message, driver)
    finally:
        webdriver_pool.release(driver)


def main():
    # Specify task list
    tasks = [
        ('a', 'a', 'f', "Hello, this is a test message!"),
        ("m", 'm', 'f', "Another message for you!"),
        ("c", 'c', 'f', "Another message for you!"),
        ("e", 'e', 'f', "Another message for you!"),
        ("f", 'f', 'z', "Another message for you!"),
        ("z", 'z', 'f', "Another message for you!"),
        ("x", 'x', 'f', "Another message for you!"),
        ("v", 'v', 'f', "Another message for you!"),
        (">", '>', 'f', "Another message for you!"),
        ("?", '?', 'f', "Another message for you!"),
    ]
    webdriver_pool = WebDriverPool(size=len(tasks))
    start_time = time.time()
    send_messages_multithreaded(tasks, webdriver_pool, max_workers=len(tasks))
    total_duration = time.time() - start_time
    print(f"Total time taken for all messages: {total_duration:.5f} s")

    webdriver_pool.close_all()


if __name__ == "__main__":
    main()
