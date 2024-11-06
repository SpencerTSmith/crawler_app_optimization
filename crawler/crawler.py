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
from sys import argv
from enum import StrEnum
import multiprocessing as mp

# Set up logging
log_dir = 'crawler_logs'
timestamp = datetime.now().strftime('%Y%m%d_%H%M')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, f'{timestamp}_crawler.log'), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class Args(StrEnum):
    HEADLESS = "--headless"
    REGISTER = "--register"
    POST = "--post"
    MESSAGE = "--message"

def generate_random_string():
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choices(letters_and_digits, k=10))

def edit_bio(username, bio, driver):
    start_time = time.time()
    try:
        profile_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='nav-link' and text()='Profile']"))
        )
        profile_link.click()
    except Exception as e:
        logging.info(e)
        logging.error(f"Failed to find or click the Profile link: {e}")
        return
    try:
        driver.find_element(By.LINK_TEXT, 'Edit your profile').click()
        driver.find_element(By.ID, 'about_me').clear()
        driver.find_element(By.ID, 'about_me').send_keys(bio)
        driver.find_element(By.ID, 'submit').click()
        success = driver.find_element(By.CLASS_NAME, 'alert-info').text
        duration = time.time() - start_time
        if success == 'Your changes have been saved.':
            logging.info(f"Bio updated for user '{username}': (Duration {duration:.5f} s)")
            return True
        else:
            logging.error(f"Bio update failed for user '{username}': (Duration {duration:.5f} s)")
            return False
    except Exception as e:
        logging.error(f"An error occurred while editing the bio: {e}")
        return False

def register(username, password, driver):
    start_time = time.time()
    driver.find_element(By.LINK_TEXT, 'Click to Register!').click()
    driver.find_element(By.ID, 'username').send_keys(username)
    driver.find_element(By.ID, 'email').send_keys(username + '@gmail.com')
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'password2').send_keys(password)
    driver.find_element(By.ID, 'submit').click()
    try:
        success = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'alert-info'))
        ).text
        duration = time.time() - start_time
        if (success == 'Congratulations, you are now a registered user!'):
            logging.info(f"Registration successful for user '{username}': (Duration {duration:.5f} s)")
            return True
        else:
            logging.error(f"Registration failed for user '{username}': (Duration {duration:.5f} s)")
            return False
    except Exception as e:
        logging.error(f"An error occurred while editing the bio: {e}")
        return False

def register_bench():
    with mp.Pool() as workers:
        start_time = time.time()
        workers.map(register_worker, range(mp.cpu_count()))
        workers.close()

    end_time = time.time()
    total_duration = end_time - start_time

    # each process should be registering 5 users
    n_registered = mp.cpu_count() * 5

    logging.info(f"{n_registered} registrations complete in {total_duration}")

def register_worker(_):
    # each process gets a driver
    driver_opts = Options()
    driver_opts.add_argument("--window-size=1920,1080")
    driver_opts.add_argument('--no-sandbox')
    driver_opts.add_argument('--disable-dev-shm-usage')
    driver_opts.add_argument("--headless=new")

    driver = webdriver.Chrome(options=driver_opts)
    driver.get("http://127.0.0.1:5000")

    # register 5 users
    for _ in range(5):
        username = generate_random_string()
        password = generate_random_string()
        register(username, password, driver)

    logging.info(f"Process {mp.current_process().name} has finished registering users")
    driver.quit()

def post_bench():
    # temp driver to register a new user for benchmarking
    driver_opts = Options()
    driver_opts.add_argument("--window-size=1920,1080")
    driver_opts.add_argument('--no-sandbox')
    driver_opts.add_argument('--disable-dev-shm-usage')
    driver_opts.add_argument("--headless=new")

    driver = webdriver.Chrome(options=driver_opts)
    driver.get("http://127.0.0.1:5000")

    username = generate_random_string()
    password = generate_random_string()
    register(username, password, driver)

    driver.quit()

    with mp.Pool() as workers:
        args = (username, password)
        all_args = mp.cpu_count() * [args]

        start_time = time.time()

        workers.starmap(func=post_worker, iterable=all_args)
        workers.close()

        end_time = time.time()

    total_duration = end_time - start_time

    n_posts = mp.cpu_count() * 5
    logging.info(f"{n_posts} posts complete in {total_duration}")

def post_worker(username, password):
    # each process gets a driver
    driver_opts = Options()
    driver_opts.add_argument("--window-size=1920,1080")
    driver_opts.add_argument('--no-sandbox')
    driver_opts.add_argument('--disable-dev-shm-usage')
    driver_opts.add_argument("--headless=new")

    driver = webdriver.Chrome(options=driver_opts)
    driver.get("http://127.0.0.1:5000")

    # login and get to post screen
    login(username, password, driver)

    for _ in range(5):
        post(username, password, driver)

    logging.info(f"Process {mp.current_process().name} has finished posting")
    driver.quit()

def forgot_password(email, driver):
    start_time = time.time()
    driver.find_element(By.LINK_TEXT, 'Click to Reset It').click()
    driver.find_element(By.ID, 'email').send_keys(email)
    driver.find_element(By.ID, 'submit').click()
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-info'))
        )
        success = driver.find_element(By.CLASS_NAME, 'alert-info').text
        duration = time.time() - start_time
        if success == 'Check your email for the instructions to reset your password':
            logging.info(f"Forgot password request sent for email '{email}': (Duration {duration:.5f} s)")
            return True
        else:
            logging.error(f"Forgot password request failed for email '{email}': (Duration {duration:.5f} s)")
            return False
    except Exception as e:
        logging.error(f"An error occurred while waiting for the forgot password confirmation: {e}")
        return False

def login(username, password, driver):
    start_time = time.time()
    driver.find_element(By.ID, 'username').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'submit').click()
    try:
        success = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.TAG_NAME, 'h1'))
        ).text
        duration = time.time() - start_time
        if success == 'Hi, ' + username + '!':
            logging.info(f"Login successful for user '{username}': (Duration {duration:.5f} s)")
            return True
        else:
            logging.error(f"Login failed for user '{username}': (Duration {duration:.5f} s)")
            return False
    except Exception as e:
        logging.info(f"An error occurred during login for '{username}': {e}")
        return False

def logout(username, driver):
    start_time = time.time()
    try:
        profile_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='nav-link' and text()='Logout']"))
        )
        profile_link.click()
    except Exception as e:
        logging.info(e)
        logging.error(f"Failed to find or click the Profile link: {e}")
        return
    try:
        success = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'alert-info'))
        ).text
        duration = time.time() - start_time
        if success == 'Please log in to access this page.':
            logging.info(f"Logout successful for '{username}': (Duration {duration:.5f} s)")
            return True
        else:
            logging.error(f"Logout failed for '{username}': (Duration {duration:.5f} s)")
            return False
    except Exception as e:
        logging.error(f"Failed to get logout confirmation message: {e}")
        return False

def post(username, message, driver):
    start_time = time.time()
    driver.find_element(By.ID, 'post').send_keys(message)
    driver.find_element(By.ID, 'submit').click()
    try:
        post = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "alert"))
        ).text
        duration = time.time() - start_time
        if "Your post is now live!" in post:
            logging.info(f"'{username}' submitted a post successfully: (Duration {duration:.5f} s)")
            return True
        else:
            logging.error(f"'{username}' post failed: (Duration {duration:.5f} s)")
            return False
    except Exception as e:
        logging.error(f"Failed to confirm post submission: {e}")
        return False

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
            logging.info(f"Could not find a link matching the target username: '{target_username}'")
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
            logging.info(f"Private message sent from '{username}' to '{target_username}'")
        else:
            logging.error(f"Private message failed for '{username}' to '{target_username}'")
    except Exception as e:
        logging.error(f"An error occurred while sending private message to '{target_username}': {e}")

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
        driver.get("http://localhost:5000")
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
                logging.error(f"Generated an exception: {exc}")

def process_message_task(username, password, target_username, message, driver, webdriver_pool):
    """Log in, send a private message, and release the WebDriver back to the pool."""
    try:
        if login(username, password, driver):
            send_private_message(username, target_username, message, driver)
    finally:
        webdriver_pool.release(driver)

def message_bench():
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
    logging.info(f"Total time taken for all messages: {total_duration:.5f} s")

    webdriver_pool.close_all()

def main():
    # display = Display(visible=0, size=(800,600))
    # display.start()

    if Args.REGISTER in argv:
        register_bench()
        return

    if Args.POST in argv:
        post_bench()
        return

    if Args.MESSAGE in argv:
        message_bench()
        return

    driver_opts = Options()
    if Args.HEADLESS in argv:
        driver_opts.add_argument("--window-size=1920,1080")
        driver_opts.add_argument('--no-sandbox')
        driver_opts.add_argument('--disable-dev-shm-usage')
        driver_opts.add_argument("--headless=new")

    driver = webdriver.Chrome(options=driver_opts)
    driver.get("http://127.0.0.1:5000")
    username = generate_random_string()
    email = username + '@gmail.com'
    password = generate_random_string()
    message = generate_random_string()


    start_time = time.time()
    register(username=username, password=password, driver=driver)

    login(username=username, password=password, driver=driver)
    post(username=username, message=message, driver=driver)
    edit_bio(username=username, bio='Hello, my name is ' + username, driver=driver)
    logout(username=username, driver=driver)
    forgot_password(email=email, driver=driver)

    stop_time = time.time()
    duration = stop_time - start_time
    logging.info(f"'{username}' successful run of all crawler tests: (Duration {duration:.5f} s)")

    driver.quit()

if __name__ == "__main__":
    main()
