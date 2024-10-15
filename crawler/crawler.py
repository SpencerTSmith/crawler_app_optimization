from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pyvirtualdisplay import Display

def register(username, password):
    return

def login(username, password):
    return

def sign_in(username, password):
    return

def forgot_password(email):
    return

def post(message):
    return

def main():
    # display = Display(visible=0, size=(800,600))
    # display.start()
    driver = webdriver.Chrome()
    driver.get("http://127.0.0.1:5000")
    username = driver.find_element()

if __name__ == "__main__":
    main()