from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display
import time
import random
import string

def generate_random_string():
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(10))

def register(username, password, driver):
    driver.find_element(By.LINK_TEXT, 'Click to Register!').click()
    driver.find_element(By.ID, 'username').send_keys(username)
    driver.find_element(By.ID, 'email').send_keys(username + '@gmail.com')
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'password2').send_keys(password)
    driver.find_element(By.ID, 'submit').click()
    success = driver.find_element(By.CLASS_NAME, 'alert-info').text
    print(success)

def login(username, password, driver):
    driver.find_element(By.ID, 'username').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'submit').click()
    success = driver.find_element(By.TAG_NAME, 'h1').text
    print(success)

def logout(driver):
    driver.find_element(By.CLASS_NAME, 'navbar-toggler-icon').click()
    try:
        logout_link = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.LINK_TEXT, 'Logout')))
        logout_link.click()
    except Exception as e:
        print(e)
    success = driver.find_element(By.CLASS_NAME, 'alert-info').text
    print(success)

def forgot_password(email, driver):
    driver.find_element(By.LINK_TEXT, 'Click to Reset It').click()
    driver.find_element(By.ID, 'email').send_keys(email)
    driver.find_element(By.ID, 'submit').click()
    success = driver.find_element(By.CLASS_NAME, 'alert-info').text
    print(success)

def post(message, driver):
    driver.find_element(By.ID, 'post').send_keys(message)
    driver.find_element(By.ID, 'submit').click()
    posts = driver.find_elements(By.TAG_NAME, 'span')
    for post in posts:
        if post.text == message:
            print('Posted: ' + message)
            break

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
    post(message=message, driver=driver)
    logout(driver=driver)
    forgot_password(email=email, driver=driver)
    driver.quit()

if __name__ == "__main__":
    main()