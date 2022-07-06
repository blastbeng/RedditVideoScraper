import praw
import os
import sqlite3
from pathlib import Path
from os.path import join, dirname
from dotenv import load_dotenv
from urllib.request import urlretrieve

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
TMP_DIR = os.environ.get("TMP_DIR")
DB_DIR = os.environ.get("DB_DIR")

reddit = praw.Reddit(
    client_id=API_KEY,
    client_secret=API_SECRET,
    user_agent="Udoo_docker_instance",
)

def get_videos():
    for submission in reddit.subreddit("funnyvideos").hot(limit=10):
        if submission.is_video:
            try:
                print(submission.title)
                url = submission.url
                name = submission.title[:30].rstrip() + ".mp4"
                #vids.append((url, name))
                urlretrieve(url, name)
            except:
                pass

def check_db_exists(): 
  fle = Path(DB_DIR)
  fle.touch(exist_ok=True)
  f = open(fle)
  f.close()

def create_empty_tables():
  check_db_exists()
  try:
    sqliteConnection = sqlite3.connect(DB_DIR)
    cursor = sqliteConnection.cursor()

    sqlite_create_tournaments_query = """ CREATE TABLE IF NOT EXISTS Videos(
            id INTEGER PRIMARY KEY,
            title VARCHAR(255) NOT NULL
        ); """

    cursor.execute(sqlite_create_tournaments_query)

  except sqlite3.Error as error:
    print("Failed to create tables", error)
  finally:
    if sqliteConnection:
        sqliteConnection.close()


create_empty_tables()