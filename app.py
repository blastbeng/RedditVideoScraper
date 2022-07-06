import praw
import os
import time
import random
import requests
import sqlite3
from pathlib import Path
from os.path import join, dirname
from dotenv import load_dotenv
from urllib.request import urlretrieve
from datetime import datetime
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip
from RedDownloader import RedDownloader
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager as CM

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
TMP_DIR = os.environ.get("TMP_DIR")
DB_DIR = os.getcwd()+"/"+os.environ.get("DB_DIR")
SUBREDDITS = os.environ.get("SUBREDDITS").split(",")


        
print('=====================================================================================================')
print('Heyy, you have to login manully on tiktok, so the bot will wait you 1 minute for loging in manually!')
print('=====================================================================================================')
time.sleep(8)
print('Running bot now, get ready and login manually...')
time.sleep(4)
options = webdriver.ChromeOptions()
bot = webdriver.Chrome(options=options,  executable_path=CM().install())
bot.set_window_size(1680, 900)
bot.get('https://www.tiktok.com/login')
ActionChains(bot).key_down(Keys.CONTROL).send_keys(
    '-').key_up(Keys.CONTROL).perform()
ActionChains(bot).key_down(Keys.CONTROL).send_keys(
    '-').key_up(Keys.CONTROL).perform()
print('Waiting 50s for manual login...')
time.sleep(50)
bot.get('https://www.tiktok.com/upload/?lang=it')
time.sleep(3)

def get_videos():

    os.chdir(TMP_DIR)

    reddit = praw.Reddit(
        client_id=API_KEY,
        client_secret=API_SECRET,
        user_agent="Udoo_docker_instance",
    )

    for subreddit in SUBREDDITS:
        for submission in reddit.subreddit(subreddit).hot(limit=10):
            if submission.is_video:
                try:
                    url = "https://reddit.com" + submission.permalink
                    name = submission.title[:30].rstrip() + ".mp4"
                    tmp_name = submission.title[:30].rstrip() + "_tmp"
                    if not get_video(submission.id, name):
                        print("Posting '" + submission.title + "'")
                        save_video(submission.id, name)
                        
                        tmp_name = os.path.join(TMP_DIR, tmp_name)
                        name = os.path.join(TMP_DIR, name)
                        file = RedDownloader.Download(url = url, output = tmp_name, quality = 1080)

                        tmp_name = tmp_name + ".mp4"

                        clip = VideoFileClip(tmp_name)

                        if clip.duration > 60:
                            ffmpeg_extract_subclip(tmp_name, 0, 5, targetname=name)
                        else:
                            os.rename(tmp_name, name)

                        upload(name)
                            
                        os.remove(tmp_name)
                        os.remove(name)
                    else:
                        print("Not posting '" + submission.title + "'")
                except Exception as e: 
                    print(e)
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

    sqlite_create_videos_query = """ CREATE TABLE IF NOT EXISTS Videos(
            id INTEGER PRIMARY KEY,
            id_reddit  VARCHAR(255) NOT NULL,
            title VARCHAR(255) NOT NULL,
            date_add VARCHAR(255) NOT NULL
        ); """

    cursor.execute(sqlite_create_videos_query)

    sqliteConnection.commit()
    cursor.close()

  except sqlite3.Error as error:
    print("Failed to create tables", error)
  finally:
    if sqliteConnection:
        sqliteConnection.close()

def save_video(id_reddit: str, title: str):  
  try:
    sqliteConnection = sqlite3.connect(DB_DIR)
    cursor = sqliteConnection.cursor()

    sqlite_insert_video_query = """INSERT INTO Videos
                          (id_reddit, title, date_add) 
                           VALUES 
                          (?, ?, ?)"""

    data_videos_tuple = (id_reddit, title, datetime.now())

    cursor.execute(sqlite_insert_video_query, data_videos_tuple)

    sqliteConnection.commit()
    cursor.close()

  except sqlite3.Error as error:
    print("Failed to insert data into sqlite", error)
  finally:
    if sqliteConnection:
        sqliteConnection.close()

def get_video(id_reddit: str, title: str):
  try:
    sqliteConnection = sqlite3.connect(DB_DIR)
    cursor = sqliteConnection.cursor()

    sqlite_select_video_query = """SELECT * FROM Videos WHERE id_reddit = ? and title = ?"""
    cursor.execute(sqlite_select_video_query, (id_reddit, title,))
    records = cursor.fetchall()
    cursor.close()

    if records is not None and records.__len__() > 0:
        return True
    else:
        return False

  except sqlite3.Error as error:
    print("Failed to select data from sqlite", error)
  finally:
    if sqliteConnection:
        sqliteConnection.close()


def check_exists_by_xpath(driver, xpath):
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False

    return True


def upload(video_path):
    while True:
        file_uploader = bot.find_element_by_xpath(
            '//*[@id="main"]/div[2]/div/div[2]/div[2]/div/div/input')

        file_uploader.send_keys(video_path)

        caption = bot.find_element_by_xpath(
            '//*[@id="main"]/div[2]/div/div[2]/div[3]/div[1]/div[1]/div[2]/div/div[1]/div/div/div/div/div/div/span')

        bot.implicitly_wait(10)
        ActionChains(bot).move_to_element(caption).click(
            caption).perform()
        # ActionChains(bot).key_down(Keys.CONTROL).send_keys(
        #     'v').key_up(Keys.CONTROL).perform()

        with open(r"caption.txt", "r") as f:
            tags = [line.strip() for line in f]

        for tag in tags:
            ActionChains(bot).send_keys(tag).perform()
            time.sleep(2)
            ActionChains(bot).send_keys(Keys.RETURN).perform()
            time.sleep(1)

        time.sleep(5)
        bot.execute_script("window.scrollTo(150, 300);")
        time.sleep(5)

        post = WebDriverWait(bot, 100).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="main"]/div[2]/div/div[2]/div[3]/div[5]/button[2]')))

        post.click()
        time.sleep(30)

        if check_exists_by_xpath(bot, '//*[@id="portal-container"]/div/div/div[1]/div[2]'):
            reupload = WebDriverWait(bot, 100).until(EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="portal-container"]/div/div/div[1]/div[2]')))

            reupload.click()
        else:
            print('Unknown error cooldown')
            while True:
                time.sleep(600)
                post.click()
                time.sleep(15)
                if check_exists_by_xpath(bot, '//*[@id="portal-container"]/div/div/div[1]/div[2]'):
                    break

        if check_exists_by_xpath(bot, '//*[@id="portal-container"]/div/div/div[1]/div[2]'):
            reupload = WebDriverWait(bot, 100).until(EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="portal-container"]/div/div/div[1]/div[2]')))
            reupload.click()

        time.sleep(1)

        
create_empty_tables()
#tiktok_login()
get_videos()