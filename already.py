import re
import time
import logging
import json
import pymysql.cursors
import undetected_chromedriver.v2 as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from decouple import config
from bs4 import BeautifulSoup
from decimal import Decimal
from datetime import datetime

ENV = config("ENV", default="prod")
DB_HOST = config("DB_HOST")
DB_PORT = int(config("DB_PORT", default=3306))
DB_USER = config("DB_USER")
DB_PASSWORD = config("DB_PASSWORD")
DB_NAME = config("DB_NAME")
LIMIT = int(config("LIMIT", default=1))
DELAY_SECOND = int(config("DELAY_SECOND", default=2))
MODE = int(config("MODE", default=1))
NUM_OF_RETRY = int(config("NUM_OF_RETRY", default=3))
IS_SCRAPE_IFRAME = bool(config("IS_SCRAPE_IFRAME", default=False))
YTTABLE = config("YTTABLE")
SITETABLE = config("SITETABLE")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

_connection = None


def get_connection():
    global _connection
    if not _connection:
        _connection = pymysql.connect(host=DB_HOST,
                                      port=DB_PORT,
                                      user=DB_USER,
                                      password=DB_PASSWORD,
                                      database=DB_NAME,
                                      cursorclass=pymysql.cursors.DictCursor)
    return _connection


def format_url(url):
    return url.replace("http://", "https://")


def remove_extra_chars(datestr):
    return re.sub(r'(\d)(st|nd|rd|th)', r'\1', datestr)


d = {
    'K': 3,
    'M': 6,
    'B': 9
}


def text_to_num(text):
    if text[-1] in d:
        num, magnitude = text[:-1], text[-1]
        return float(Decimal(num) * 10 ** d[magnitude])
    else:
        text = text.replace(",", "")
        return float(text)


def process_channel(sitemap: dict) -> None:
    try:
        channel = scrape_channel(sitemap)
        if channel is not None:
            logger.info(f"Channel info: {channel}")
            insert_channels(channel)
            logger.info(f"Successful insert channel for sitemap {sitemap['url']}")
    except Exception as ex:
        logger.error(f"Failed to scrape channel for sitemap {sitemap['url']}, err={ex}")


def process_video(sitemap: dict) -> None:
    try:
        videos = scrape_video(sitemap)
        if videos is not None and len(videos) > 0:
            logger.info(f"Videos info: {videos}")
            insert_videos(sitemap["id"], videos)
            logger.info(f"Successful insert videos for sitemap {sitemap['url']}")
    except Exception as ex:
        logger.error(f"Failed to scrape videos for sitemap {sitemap['url']}, err={ex}")


def get_percent_change(value: float, change: float, default_result: float = 10000.) -> float:
    if value - change <= 0.:
        return default_result
    else:
        return (value / (value - change) - 1) * 100.


def scrape_channel(sitemap: dict) -> set:
    channel = {
        "sitemap_id": sitemap["id"],
        "channel_id": sitemap["url"].rsplit('/', 1)[-1],
        "channel_name": None,
        "username": None,
        "avatar": None,
        "uploads": None,
        "subscribers": None,
        "views": None,
        "country": None,
        "channel_type": None,
        "user_created": None,
        "social_blade_rank": None,
        "subscriber_rank": None,
        "view_rank": None,
        "country_rank": None,
        "genre_rank": None,
        "fb_link": None,
        "ig_link": None,
        "tw_link": None,
        "twitch_link": None,
        "tiktok_link": None,
        "total_subscribers_weekly": None,
        "total_views_weekly": None,
        "monthly_gained_views": None,
        "6mv": None,
        "1yv": None,
        "2yv": None,
        "maxv": None,
        "monthly_gained_subscribers": None,
        "6ms": None,
        "1ys": None,
        "2ys": None,
        "maxs": None,
        "recent_video": None,
        "latest_date": None,
    }
    url = format_url(sitemap["url"])
    try_count = 0
    driver = None
    while True:
        if try_count > NUM_OF_RETRY:
            raise Exception(f"Exceed number of retry (maximum retry for {NUM_OF_RETRY} times)")
        try_count += 1
        logger.info(f"[{url}] Num retry {try_count}")
        try:
            options = uc.ChromeOptions()
            options.arguments.extend(
                ["--no-sandbox", "--disable-setuid-sandbox"])
            options.add_argument('--disable-gpu')  # for headless
            options.add_argument('--disable-dev-shm-usage')  # uses /tmp for memory sharing
            # disable popups on startup
            options.add_argument('--no-first-run')
            options.add_argument('--no-service-autorun')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--password-store=basic')

            logger.info("Creating Driver...")
            if ENV == "prod":
                driver = uc.Chrome(
                    driver_executable_path='/usr/bin/chromedriver',
                    options=options,
                    headless=True,
                )
            else:
                driver = uc.Chrome(
                    options=options,
                    headless=False,
                )
            logger.info("Created Driver...")

            driver.get(url)

            # wait until document is ready
            WebDriverWait(driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState;") == "complete")
            logger.info(f"Checkpoint #1")
            page_source = driver.page_source
            # parse to bs4
            soup = BeautifulSoup(page_source, features="html.parser")
            logger.info(f"Checkpoint #2")
            # check if block page is show or not
            block_ip = soup.find_all("div", class_="cf-error-details cf-error-1020")
            if len(block_ip) > 0:
                raise Exception("Cloudflare block IP")

            userTopInfoBlockTop = soup.find("div", {"id": "YouTubeUserTopInfoBlockTop"})
            logger.info(f"Checkpoint #3")
            if not userTopInfoBlockTop:
                return None
            userTopInfoBlockTop = userTopInfoBlockTop.find("div", recursive=False)
            ranking = soup.find_all("span", attrs={"data-hint": re.compile("^This spot is shared with")})
            channel_name = userTopInfoBlockTop.find("h1", recursive=False)
            if channel_name:
                channel["channel_name"] = channel_name.string
            username = userTopInfoBlockTop.find("h4", recursive=False)
            if username:
                channel["username"] = username.find("a", recursive=False).string
            avatar = soup.find("img", {"id": "YouTubeUserTopInfoAvatar"})
            if avatar:
                channel["avatar"] = avatar["src"]
            uploads = text_to_num(soup.find("span", {"id": "youtube-stats-header-uploads"}).string)
            uploads = uploads if uploads >= 0 else None
            channel["uploads"] = int(uploads) if uploads is not None else None
            subscribers = text_to_num(soup.find("span", {"id": "youtube-stats-header-subs"}).string)
            subscribers = subscribers if subscribers >= 0 else None
            channel["subscribers"] = int(subscribers) if subscribers is not None else None
            views = text_to_num(soup.find("span", {"id": "youtube-stats-header-views"}).string)
            views = views if views >= 0 else None
            channel["views"] = int(views) if views is not None else None
            channel["country"] = soup.find("span", {"id": "youtube-stats-header-country"}).string or None
            channel["channel_type"] = soup.find("a", {"id": "youtube-user-page-channeltype"}).string or None
            user_created = soup.find_all("div", class_="YouTubeUserTopInfo")[-1].find_all("span")[-1].string or None
            if user_created is not None:
                channel["user_created"] = datetime.strptime(remove_extra_chars(user_created), '%b %d, %Y')
            social_blade_rank = re.sub('\D', '', ranking[0].string)
            channel["social_blade_rank"] = int(social_blade_rank) if social_blade_rank != "" else None
            subscriber_rank = re.sub('\D', '', ranking[1].string)
            channel["subscriber_rank"] = int(subscriber_rank) if subscriber_rank != "" else None
            view_rank = re.sub('\D', '', ranking[2].string)
            channel["view_rank"] = int(view_rank) if view_rank != "" else None
            country_rank = re.sub('\D', '', ranking[3].string)
            channel["country_rank"] = int(country_rank) if country_rank != "" else None
            genre_rank = re.sub('\D', '', ranking[4].string)
            channel["genre_rank"] = int(genre_rank) if genre_rank != "" else None

            userTopSocial = soup.find("div", {"id": "YouTubeUserTopSocial"})
            if userTopSocial:
                socialLinks = userTopSocial.find_all("a")
                if socialLinks:
                    for socialLink in socialLinks:
                        if re.search("facebook.com", socialLink["href"]):
                            channel["fb_link"] = socialLink["href"]
                        elif re.search("instagram.com", socialLink["href"]):
                            channel["ig_link"] = socialLink["href"]
                        elif re.search("twitter.com", socialLink["href"]):
                            channel["tw_link"] = socialLink["href"]
                        elif re.search("tiktok.com", socialLink["href"]):
                            channel["tiktok_link"] = socialLink["href"]
                        elif re.search("twitch.tv", socialLink["href"]):
                            channel["twitch_link"] = socialLink["href"]
                        elif re.search("youtube.com/channel", socialLink["href"]):
                            channel["channel_id"] = socialLink["href"].rsplit('/', 1)[-1]
            try:
                logger.info(f"Checkpoint #4")
                num_chart_available = driver.execute_script("return Highcharts.charts.length") or 0
                if num_chart_available > 0:
                    logger.info(f"Checkpoint #4.1")
                    for i in range(0, num_chart_available):
                        chart_title = driver.execute_script(f"return Highcharts.charts[{i}].userOptions.title") or ""
                        if chart_title:
                            chart_title = chart_title["text"]
                        if "Monthly Gained Subscribers" in chart_title:
                            monthly_gained_subscribers = driver.execute_script(
                                f"return Highcharts.charts[{i}].series[0].userOptions.data")
                            if monthly_gained_subscribers:
                                channel["monthly_gained_subscribers"] = json.dumps(monthly_gained_subscribers,
                                                                                   separators=(',', ':'))
                                channel["latest_date"] = monthly_gained_subscribers[-1][0]

                                monthly_gained_subscribers_values = [mgs_item[1] for mgs_item in
                                                                     monthly_gained_subscribers][::-1]

                                if subscribers:
                                    mgs_series_length = len(monthly_gained_subscribers_values)
                                    try:
                                        if mgs_series_length >= 6:
                                            channel["6ms"] = get_percent_change(subscribers,
                                                                                sum(monthly_gained_subscribers_values[
                                                                                    -6:]))
                                        if mgs_series_length >= 12:
                                            channel["1ys"] = get_percent_change(subscribers,
                                                                                sum(monthly_gained_subscribers_values[
                                                                                    -12:]))
                                        if mgs_series_length >= 24:
                                            channel["2ys"] = get_percent_change(subscribers,
                                                                                sum(monthly_gained_subscribers_values[
                                                                                    -24:]))
                                        channel["maxs"] = get_percent_change(subscribers,
                                                                             sum(monthly_gained_subscribers_values))
                                    except ZeroDivisionError:
                                        logger.warning(
                                            f"[{url}] Division by zero encountered in subscribers growth calculation!")
                        elif "Monthly Gained Video Views" in chart_title:
                            monthly_gained_views = driver.execute_script(
                                f"return Highcharts.charts[{i}].series[0].userOptions.data")
                            if monthly_gained_views:
                                channel["monthly_gained_views"] = json.dumps(monthly_gained_views,
                                                                             separators=(',', ':'))
                                channel["latest_date"] = monthly_gained_views[-1][0]

                                monthly_gained_views_values = [mgv_item[1] for mgv_item in monthly_gained_views][::-1]

                                if views:
                                    mgv_series_length = len(monthly_gained_views_values)
                                    try:
                                        if mgv_series_length >= 6:
                                            channel["6mv"] = get_percent_change(views,
                                                                                sum(monthly_gained_views_values[-6:]))
                                        if mgv_series_length >= 12:
                                            channel["1yv"] = get_percent_change(views,
                                                                                sum(monthly_gained_views_values[-12:]))
                                        if mgv_series_length >= 24:
                                            channel["2yv"] = get_percent_change(views,
                                                                                sum(monthly_gained_views_values[-24:]))
                                        channel["maxv"] = get_percent_change(views, sum(monthly_gained_views_values))
                                    except ZeroDivisionError:
                                        logger.warning(
                                            f"[{url}] Division by zero encountered in views growth calculation!")
                        elif "TOTAL SUBSCRIBERS (WEEKLY)" in chart_title:
                            total_subscribers_weekly = driver.execute_script(
                                f"return Highcharts.charts[{i}].series[0].userOptions.data")
                            if total_subscribers_weekly:
                                channel["total_subscribers_weekly"] = json.dumps(total_subscribers_weekly,
                                                                                 separators=(',', ':'))
                                channel["latest_date"] = total_subscribers_weekly[-1][0]
                        elif "TOTAL VIDEO VIEWS (WEEKLY)" in chart_title:
                            total_views_weekly = driver.execute_script(
                                f"return Highcharts.charts[{i}].series[0].userOptions.data")
                            if total_views_weekly:
                                channel["total_views_weekly"] = json.dumps(total_views_weekly, separators=(',', ':'))
                                channel["latest_date"] = total_views_weekly[-1][0]
            except Exception as ex:
                logger.error(f"[{url}] Failed to get charts, err={ex}")
            logger.info(f"Checkpoint #5")
            if IS_SCRAPE_IFRAME:
                # hover over element for loading iframe youtube embedded
                a = ActionChains(driver)
                try:
                    logger.info(f"[{url}] Trigger youtube iframe")
                    recent_video = driver.find_element(By.XPATH, '//div[@class="youtube-video-embed-recent"]')
                    if recent_video:
                        a.move_to_element(recent_video).perform()
                        a.move_to_element(recent_video).click().perform()
                        iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                            (By.XPATH, '//div[@class="youtube-video-embed-recent"]//iframe')))
                        if iframe:
                            channel["recent_video"] = iframe.get_attribute("src")
                except:
                    logger.info(f"[{url}] Not found user recent video")
        except Exception as ex:
            update_status(sitemap["id"], -1)
            logger.info(f"[{url}] Failed to crawl, err={ex}")
            time.sleep(DELAY_SECOND)
        else:
            update_status(sitemap["id"], 1)
            logger.info(f"[{url}] Done crawl")
            return channel
        finally:
            if driver is not None:
                driver.quit()


def insert_channels(channel) -> None:
    connection = get_connection()
    with connection.cursor() as cursor:
        placeholder = ", ".join(["%s"] * len(channel))
        sql = """INSERT INTO `channel` ({columns}) 
        VALUES ({values})
        ON DUPLICATE KEY UPDATE
            channel_id = VALUES(channel_id),
            channel_name = VALUES(channel_name),
            username = VALUES(username),
            avatar = VALUES(avatar),
            uploads = VALUES(uploads),
            subscribers = VALUES(subscribers),
            views = VALUES(views),
            country = VALUES(country),
            channel_type = VALUES(channel_type),
            user_created = VALUES(user_created),
            social_blade_rank = VALUES(social_blade_rank),
            subscriber_rank = VALUES(subscriber_rank),
            view_rank = VALUES(view_rank),
            country_rank = VALUES(country_rank),
            genre_rank = VALUES(genre_rank),
            fb_link = VALUES(fb_link),
            ig_link = VALUES(ig_link),
            tw_link = VALUES(tw_link),
            twitch_link = VALUES(twitch_link),
            tiktok_link = VALUES(tiktok_link),
            total_subscribers_weekly = VALUES(total_subscribers_weekly),
            total_views_weekly = VALUES(total_views_weekly),
            monthly_gained_views = VALUES(monthly_gained_views),
            6mv = VALUES(6mv),
            1yv = VALUES(1yv),
            2yv = VALUES(2yv),
            maxv = VALUES(maxv),
            monthly_gained_subscribers = VALUES(monthly_gained_subscribers),
            6ms = VALUES(6ms),
            1ys = VALUES(1ys),
            2ys = VALUES(2ys),
            maxs = VALUES(maxs),
            recent_video = VALUES(recent_video),
            latest_date = VALUES(latest_date);
        """.format(columns=",".join(channel.keys()), values=placeholder)
        cursor.execute(sql, list(channel.values()))
        # print(cursor._last_executed)
    connection.commit()


def scrape_video(sitemap: dict) -> set:
    videos = []
    url = format_url(sitemap["url"])
    try_count = 0
    driver = None
    while True:
        if try_count > NUM_OF_RETRY:
            raise Exception(f"Exceed number of retry (maximum retry for {NUM_OF_RETRY} times)")
        try_count += 1
        logger.info(f"[{url}] Num retry {try_count}")
        try:
            options = uc.ChromeOptions()
            options.arguments.extend(
                ["--no-sandbox", "--disable-setuid-sandbox"])
            options.add_argument('--disable-gpu')  # for headless
            options.add_argument('--disable-dev-shm-usage')  # uses /tmp for memory sharing
            # disable popups on startup
            options.add_argument('--no-first-run')
            options.add_argument('--no-service-autorun')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--password-store=basic')
            # options.add_argument('--incognito')

            logger.info("Creating Driver...")
            if ENV == "prod":
                driver = uc.Chrome(
                    driver_executable_path='/usr/bin/chromedriver',
                    options=options,
                    headless=True,
                )
            else:
                driver = uc.Chrome(
                    options=options,
                    headless=False,
                )
            logger.info("Created Driver...")

            driver.get(f"{url}/videos")

            # wait until document is ready
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "YouTube-Video-Wrap")))
            page_source = driver.page_source
            # parse to bs4
            soup = BeautifulSoup(page_source, features="html.parser")

            # check if block page is show or not
            block_ip = soup.find_all("div", class_="cf-error-details cf-error-1020")
            if len(block_ip) > 0:
                raise Exception("Cloudflare block IP")

            videoTable = soup.find("div", {"id": "YouTube-Video-Wrap"})
            if not videoTable:
                return None
            rows = soup.find_all("div", {"class": "RowRecentTable"})
            for row in rows:
                video = {
                    "sitemap_id": sitemap["id"],
                    "title": None,
                    "views": None,
                    "ratings": None,
                    "comments": None,
                    "date": None,
                }
                for idx, item in enumerate(row):
                    val = item.text
                    if idx == 1:
                        video["date"] = val
                    elif idx == 3:
                        video["title"] = val
                    elif idx == 5:
                        val = text_to_num(item.text)
                        val = val if val >= 0 else None
                        if val is not None:
                            video["views"] = int(val)
                    elif idx == 7:
                        if val:
                            video["ratings"] = val
                    elif idx == 9:
                        val = text_to_num(item.text)
                        val = val if val >= 0 else None
                        if val is not None:
                            video["comments"] = int(val)
                videos.append(video)
        except Exception as ex:
            update_status(sitemap["id"], -1)
            logger.info(f"[{url}] Failed to crawl, err={ex}")
            time.sleep(DELAY_SECOND)
        else:
            update_status(sitemap["id"], 1)
            logger.info(f"[{url}] Done crawl")
            return videos
        finally:
            if driver is not None:
                driver.quit()


def insert_videos(sitemap_id: int, videos: list) -> None:
    connection = get_connection()
    with connection.cursor() as cursor:
        sql = """DELETE FROM `video` WHERE sitemap_id = %s"""
        cursor.execute(sql, sitemap_id)
        sql = """
        INSERT INTO `video` (sitemap_id, title, views, ratings, comments, date) 
        VALUES (%s, %s, %s, %s, %s, %s)                 
        """
        data = list(
            [(video["sitemap_id"], video["title"], video["views"], video["ratings"], video["comments"], video["date"])
             for video in videos])
        cursor.executemany(sql, data)
    connection.commit()


def update_status(sitemap_id: int, isprocessed: int) -> None:
    connection = get_connection()
    with connection.cursor() as cursor:
        sql = "UPDATE {} SET isprocessed = %s WHERE sitemap_id = %s".format(YTTABLE)
        cursor.execute(sql, (isprocessed, sitemap_id))
    connection.commit()


def get_sitemap(limit: int = 100) -> list:
    connection = get_connection()
    with connection.cursor() as cursor:
        sql = "SELECT s.id, s.url FROM {} y INNER JOIN {} s ON y.sitemap_id = s.id WHERE y.isprocessed = 0".format(
            YTTABLE, SITETABLE)
        cursor.execute(sql)
        result = cursor.fetchmany(limit)
        return result


if __name__ == "__main__":
    logger.info("Program starting...")
    if MODE != 1 and MODE != 2:
        raise Exception("Only support MODE 1 for channel and MODE 2 for video!")
    try:
        while True:
            logger.info(f"Fetch {LIMIT} list sitemaps")
            sitemaps = get_sitemap(limit=LIMIT)

            if len(sitemaps) == 0:
                logger.info("No records in db! Wait for 60 seconds...")
                time.sleep(60)
                continue

            logger.info("Starting fetch details info...")
            for sitemap in sitemaps:
                if MODE == 1:
                    process_channel(sitemap)
                elif MODE == 2:
                    process_video(sitemap)
                time.sleep(DELAY_SECOND)
    except Exception as ex:
        logger.error(f"There are some errors occurred: {ex}")
    finally:
        # close connection
        connection = get_connection()
        if connection is not None:
            connection.close()
        logger.info("Program exit!")
