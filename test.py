from datetime import date
import schedule
from time import sleep

def test_job():
    print("Hello")


if __name__ == '__main__':
    schedule.every().thursday.at("22:").do(test_job)
    print("hi")
    while True:
        schedule.run_pending()
        sleep(1)