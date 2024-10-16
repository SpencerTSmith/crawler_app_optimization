from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display
from datetime import datetime
import logging
import os
import random
import string
import time

log_dir = 'crawler_logs'
timestamp = datetime.now().strftime('%Y%m%d_%H%M')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, f'{timestamp}_crawler.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_random_string():
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(10))

def edit_bio(username, bio, driver):
    start_time = time.time()
    driver.find_element(By.CLASS_NAME, 'navbar-toggler-icon').click()
    try:
        logout_link = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.LINK_TEXT, 'Profile')))
        logout_link.click()
    except Exception as e:
        print(e)
    driver.find_element(By.LINK_TEXT, 'Edit your profile').click()
    driver.find_element(By.ID, 'about_me').clear()
    driver.find_element(By.ID, 'about_me').send_keys(bio)
    driver.find_element(By.ID, 'submit').click()
    success = driver.find_element(By.CLASS_NAME, 'alert-info').text
    duration = time.time() - start_time
    if (success == 'Your changes have been saved.'):
        logging.info(f"Bio updated for user '{username}': (Duration {duration:.5f} s)")
    else:
        logging.error(f"Bio update failed for user '{username}': (Duration {duration:.5f} s)")

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
    driver.find_element(By.CLASS_NAME, 'navbar-toggler-icon').click()
    try:
        logout_link = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.LINK_TEXT, 'Logout')))
        logout_link.click()
    except Exception as e:
        print(e)
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
    driver = webdriver.Chrome()
    driver.get("http://127.0.0.1:5000")
    username = generate_random_string()
    email = username + '@gmail.com'
    password = generate_random_string()
    message = generate_random_string()
    register(username=username, password=password, driver=driver)
    login(username=username, password=password, driver=driver)
    post(username=username, message=message, driver=driver)
    edit_bio(username=username, bio='Hello, my name is ' + username, driver=driver)
    logout(username=username, driver=driver)
    forgot_password(email=email, driver=driver)
    driver.quit()

if __name__ == "__main__":
    main()