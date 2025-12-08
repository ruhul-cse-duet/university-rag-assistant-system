import schedule
import time
from .scraper import scrape_website
from .vectorstore import save_to_vector_db


def auto_update(university: str, url: str, interval_minutes=60):

    def job():
        print(f"Refreshing data for {university}...")
        text = scrape_website(url)
        save_to_vector_db(university, text)
        print("Updated!")

    schedule.every(interval_minutes).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
