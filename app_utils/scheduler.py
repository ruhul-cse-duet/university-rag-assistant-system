import os
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


def start_scheduler():
    """
    Wrapper used by entrypoint.sh.
    Reads env vars:
      AUTO_UPDATE_UNIV   - short name (e.g., duet)
      AUTO_UPDATE_URL    - root URL to crawl
      AUTO_UPDATE_INTERVAL_MINUTES - how often to refresh (default 60)
    If any required value is missing, the scheduler is skipped.
    """
    univ = os.getenv("AUTO_UPDATE_UNIV")
    url = os.getenv("AUTO_UPDATE_URL")
    interval = int(os.getenv("AUTO_UPDATE_INTERVAL_MINUTES", "60"))

    if not univ or not url:
        print("Scheduler disabled: set AUTO_UPDATE_UNIV and AUTO_UPDATE_URL to enable.")
        return

    print(f"Scheduler starting: {univ} from {url} every {interval} minute(s).")
    try:
        auto_update(univ, url, interval_minutes=interval)
    except Exception as e:
        print(f"Scheduler error: {e}")
