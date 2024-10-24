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
logging.basicConfig(filename=os.path.join(log_dir, f'{timestamp}_crawler.log'), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def generate_random_string():
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(10))


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


def login(username, password, driver):
    start_time = time.time()
    driver.find_element(By.ID, 'username').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'submit').click()
    success = driver.find_element(By.TAG_NAME, 'h1').text
    duration = time.time() - start_time
    if (success == 'Hi, ' + username + '!'):
        print(f"Login successful for user '{username}': (Duration {duration:.5f} s)")
    else:
        print(f"Login failed for user '{username}': (Duration {duration:.5f} s)")


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


from selenium.webdriver.support.ui import Select


def send_private_message(username, target_username, message, driver):
    try:
        start_time = time.time()

        # Click on the "Explore" link to navigate to the Explore page
        print("Navigating to the Explore page by clicking on the 'Explore' link...")
        explore_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Explore"))
        )
        explore_link.click()

        print("Listing all user links on the Explore page:")
        user_links = driver.find_elements(By.CLASS_NAME, "user_popup")
        # Loop through the user links and find the one that matches the target username
        for link in user_links:
            text = link.text.strip()
            if text == target_username:  # Check for exact match with the target username
                print(f"Found target user link: '{text}' - href: {link.get_attribute('href')}")
                link.click()  # Click the matching link
                break
        else:
            print(f"Could not find a link matching the target username: '{target_username}'")
            return  # Exit the function if the target user is not found

        # Wait for the User Profile page to load
        print("Waiting for the User Profile page to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Send private message"))
        )

        # Click the "Send private message" link
        print("Clicking 'Send private message' link...")
        send_message_link = driver.find_element(By.LINK_TEXT, "Send private message")
        send_message_link.click()

        # Wait for the private message form to load
        print("Waiting for the private message form to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'textarea'))
        )

        # Fill in the message text area
        print("Filling in the message text area...")
        message_textarea = driver.find_element(By.TAG_NAME, 'textarea')
        if message_textarea:
            print("Message text area found.")
        else:
            print("Message text area not found.")
            return

        message_textarea.send_keys(message)

        # Click the Submit button to send the message
        # Click the Submit button to send the message
        print("Clicking the Submit button...")
        submit_button = driver.find_element(By.ID, 'submit')
        if submit_button:
            submit_button.click()
            print("Submit button clicked.")
        else:
            print("Submit button not found.")
            return

        # Verify the success message or sent messages page
        print("Waiting for the success message...")
        success_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-info'))
        ).text

        duration = time.time() - start_time
        if success_message == 'Your message has been sent.':
            print(
                f"Private message sent from '{username}' to '{target_username}': (Duration {duration:.5f} s)")
        else:
            print(
                f"Private message failed for '{username}' to '{target_username}': (Duration {duration:.5f} s)")
    except Exception as e:
        print(f"An error occurred while sending private message to '{target_username}': {e}")


def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1200,900"),
    driver = webdriver.Chrome(options=chrome_options)
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
