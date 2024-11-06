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

log_dir = 'crawler_logs'
timestamp = datetime.now().strftime('%Y%m%d_%H%M')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, f'{timestamp}_crawler.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Args(StrEnum):
    HEADLESS = "--headless"
    REGISTER = "--register"
    POST = "--post"

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
        print(e)
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
        else:
            logging.error(f"Bio update failed for user '{username}': (Duration {duration:.5f} s)")
    except Exception as e:
        logging.error(f"An error occurred while editing the bio: {e}")

def register(username, password, driver):
    start_time = time.time()
    driver.find_element(By.LINK_TEXT, 'Click to Register!').click()
    driver.find_element(By.ID, 'username').send_keys(username)
    driver.find_element(By.ID, 'email').send_keys(username + '@gmail.com')
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'password2').send_keys(password)
    driver.find_element(By.ID, 'submit').click()
    success = driver.find_element(By.CLASS_NAME, 'alert-info').text
    duration = time.time() - start_time
    if (success == 'Congratulations, you are now a registered user!'):
        logging.info(f"Registration successful for user '{username}': (Duration {duration:.5f} s)")
    else:
        logging.error(f"Registration failed for user '{username}': (Duration {duration:.5f} s)")

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

def login(username, password, driver):
    start_time = time.time()
    driver.find_element(By.ID, 'username').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'submit').click()
    success = driver.find_element(By.TAG_NAME, 'h1').text
    duration = time.time() - start_time
    if (success == 'Hi, ' + username + '!'):
        logging.info(f"Login successful for user '{username}': (Duration {duration:.5f} s)")
    else:
        logging.error(f"Login failed for user '{username}': (Duration {duration:.5f} s)")

def logout(username, driver):
    start_time = time.time()
    try:
        profile_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='nav-link' and text()='Logout']"))
        )
        profile_link.click()
    except Exception as e:
        print(e)
        logging.error(f"Failed to find or click the Profile link: {e}")
        return
    success = driver.find_element(By.CLASS_NAME, 'alert-info').text
    duration = time.time() - start_time
    if (success == 'Please log in to access this page.'):
        logging.info(f"Logout successful for '{username}': (Duration {duration:.5f} s)")
    else:
        logging.error(f"Logout failed for '{username}': (Duration {duration:.5f} s)")

def forgot_password(email, driver):
    start_time = time.time()
    driver.find_element(By.LINK_TEXT, 'Click to Reset It').click()
    driver.find_element(By.ID, 'email').send_keys(email)
    driver.find_element(By.ID, 'submit').click()
    success = driver.find_element(By.CLASS_NAME, 'alert-info').text
    duration = time.time() - start_time
    if (success == 'Check your email for the instructions to reset your password'):
        logging.info(f"Forgot password request sent for email '{email}': (Duration {duration:.5f} s)")
    else:
        logging.error(f"Forgot password request failed for email '{email}': (Duration {duration:.5f} s)")

def post(username, message, driver):
    start_time = time.time()
    driver.find_element(By.ID, 'post').send_keys(message)
    driver.find_element(By.ID, 'submit').click()
    posts = driver.find_elements(By.TAG_NAME, 'span')
    for post in posts:
        if post.text == message:
            duration = time.time() - start_time
            logging.info(f"'{username}' submitted a post successfully: (Duration {duration:.5f} s)")
            return
    duration = time.time() - start_time
    logging.info(f"'{username}' post failed: (Duration {duration:.5f} s)")


def main():
    # display = Display(visible=0, size=(800,600))
    # display.start()

    if Args.REGISTER in argv:
        register_bench()
        return

    if Args.POST in argv:
        post_bench()
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
