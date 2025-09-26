import json
import boto3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import smtplib
from email.mime.text import MIMEText

# SQS-client-details
sqs = boto3.client('sqs')
RESULT_QUEUE_URL = 'https://sqs.us-east-2.amazonaws.com/705707996353/ResultQueue'

# --- Gmail function -----
def send_email(products):
    sender_email = "shamshkhan601@gmail.com"
    app_password = "nurn dojh wqiz mupr"
    receiver_email = "shamshkhan601@gmail.com"

    subject = "Purchase Summary"
    body = f"Purchase completed! You bought: {', '.join(products)}"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)
    print("Email sent with purchase summary")

def lambda_handler(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        username = body.get('username')
        password = body.get('password')
        product = body.get('product', '').lower()

        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = "/opt/headless-chromium"
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(service=Service("/opt/chromedriver"), options=chrome_options)
        driver.implicitly_wait(10)
        products_bought = []

        try:
            driver.get("https://www.saucedemo.com/")
            driver.find_element(By.ID, "user-name").send_keys(username)
            driver.find_element(By.ID, "password").send_keys(password)
            driver.find_element(By.ID, "login-button").click()

            wait = WebDriverWait(driver, 15)
            wait.until(lambda d: "inventory" in d.current_url.lower())

            product_id_map = {
                "backpack": "add-to-cart-sauce-labs-backpack",
                "bike-light": "add-to-cart-sauce-labs-bike-light",
                "bolt-t-shirt": "add-to-cart-sauce-labs-bolt-t-shirt",
                "fleece-jacket": "add-to-cart-sauce-labs-fleece-jacket",
                "onesie": "add-to-cart-sauce-labs-onesie",
            }

            if product in product_id_map:
                driver.find_element(By.ID, product_id_map[product]).click()

            driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()
            cart_items = driver.find_elements(By.CLASS_NAME, "inventory_item_name")
            products_bought = [item.text for item in cart_items]

            driver.find_element(By.ID, "checkout").click()
            driver.find_element(By.ID, "first-name").send_keys("Shamsh")
            driver.find_element(By.ID, "last-name").send_keys("Khan")
            driver.find_element(By.ID, "postal-code").send_keys("380001")
            driver.find_element(By.ID, "continue").click()
            driver.find_element(By.ID, "finish").click()

            # Send email
            send_email(products_bought)

            result = {
                "status": "success",
                "products": products_bought
            }

        except TimeoutException:
            result = {
                "status": "failed",
                "error": "Page load timeout or element not found"
            }
        except Exception as e:
            result = {
                "status": "failed",
                "error": str(e)
            }
        finally:
            driver.quit()

        # Send result back to SQS
        try:
            sqs.send_message(
                QueueUrl=RESULT_QUEUE_URL,
                MessageBody=json.dumps(result)
            )
        except Exception as e:
            print(f"Failed to send SQS message: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps('Lambda executed successfully!')
    }
