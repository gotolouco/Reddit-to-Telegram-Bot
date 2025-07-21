import praw
from telegram import Bot, InputFile
import time
import sqlite3
from datetime import datetime
import random
import requests
import io

# ==== Configuration ====
# Reddit
reddit = praw.Reddit(
    client_id="YOUR_REDDIT_CLIENT_ID",
    client_secret="YOUR_REDDIT_SECRET",
    username="YOUR_REDDIT_USERNAME",
    password="YOUR_REDDIT_PASSWORD",
    user_agent="CUSTOM NAME"
)

# Telegram
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = YOUR_CHANNEL_OR_GROUP_ID
bot = Bot(token=TELEGRAM_TOKEN)

# Time intervals (in minutes)
INTERVAL_BETWEEN_POSTS = 10
INTERVAL_BETWEEN_SUBREDDITS = 120

# Post filtering configuration
POST_LIMIT = 1000
MIN_UPVOTES = 20

# Allowed media types
ALLOWED_EXTENSIONS = ('.jpg', '.png', '.jpeg', '.gif', '.mp4', '.mov', '.webm', '.gifv')

# Database file
DB_FILE = "posted_posts.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posted_posts
                 (post_id TEXT PRIMARY KEY,
                  subreddit TEXT,
                  date_added TEXT)''')
    conn.commit()
    conn.close()

def is_post_sent(post_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM posted_posts WHERE post_id=?", (post_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def mark_post_as_sent(post):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO posted_posts VALUES (?, ?, ?)",
              (post.id, post.subreddit.display_name, 
               datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def is_direct_media_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.head(url, allow_redirects=True, timeout=10, headers=headers)
        content_type = response.headers.get('Content-Type', '')
        return any(media in content_type for media in ['image/', 'video/', 'gif'])
    except Exception as e:
        print(f"Error checking media URL: {url} | Exception: {e}")
        return False

def get_valid_posts(subreddit_name):
    try:
        subreddit = reddit.subreddit(subreddit_name)
        print(f"\nFetching posts from r/{subreddit_name}...")

        valid_posts = []
        for post in subreddit.hot(limit=POST_LIMIT):
            if (post.stickied or not hasattr(post, 'url') or not post.url or
                is_post_sent(post.id) or post.score < MIN_UPVOTES or
                not post.url.lower().endswith(ALLOWED_EXTENSIONS)):
                continue

            valid_posts.append(post)

        print(f"Found {len(valid_posts)} valid posts in r/{subreddit_name}")
        return valid_posts

    except Exception as e:
        print(f"Error while fetching from r/{subreddit_name}: {str(e)}")
        return []

def send_post(post):
    try:
        if not hasattr(post, "url") or not post.url:
            print("Post has no URL. Skipping.")
            return False

        url = post.url
        lower_url = url.lower()

        # Fix .gifv links from Imgur
        if 'imgur.com' in lower_url and lower_url.endswith('.gifv'):
            url = url.replace('.gifv', '.mp4')
            lower_url = url

        if not is_direct_media_url(url):
            print(f"URL is not a direct media link: {url}")
            return False

        if any(lower_url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
            print("Downloading image...")
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            response.raise_for_status()
            bio = io.BytesIO(response.content)
            bio.name = url.split('/')[-1]
            bot.send_photo(chat_id=CHAT_ID, photo=bio, caption=post.title)

        elif lower_url.endswith('.gif'):
            print("Downloading GIF...")
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            response.raise_for_status()
            bio = io.BytesIO(response.content)
            bio.name = 'animation.gif'
            bot.send_document(chat_id=CHAT_ID, document=bio, caption=post.title)

        elif any(lower_url.endswith(ext) for ext in ['.mp4', '.mov', '.webm']):
            print("Sending video...")
            bot.send_video(chat_id=CHAT_ID, video=url, caption=post.title)

        else:
            print(f"Unsupported media type: {url}")
            return False

        mark_post_as_sent(post)
        return True

    except Exception as e:
        print(f"Failed to send post ({getattr(post, 'url', 'no URL')}): {str(e)}")
        with open("error_log.txt", "a") as log:
            log.write(f"{datetime.now()} - {getattr(post, 'url', 'no URL')} - {str(e)}\n")
        return False

def load_subreddits_from_file(file_path="subreddits.txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            subreddits = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            print(f"{len(subreddits)} subreddits loaded from file.")
            return subreddits
    except FileNotFoundError:
        print(f"File {file_path} not found. Please create it and list your subreddits.")
        return []

def main_loop():
    init_db()
    print("=== Bot Started ===")
    print(f"Post interval: {INTERVAL_BETWEEN_POSTS} minutes")
    print(f"Subreddit interval: {INTERVAL_BETWEEN_SUBREDDITS} minutes")

    subreddits = load_subreddits_from_file()
    if not subreddits:
        print("No subreddits loaded. Shutting down.")
        return

    current_subreddit_index = 0

    while True:
        subreddit_name = subreddits[current_subreddit_index]
        print(f"\n--- Processing r/{subreddit_name} ---")

        valid_posts = get_valid_posts(subreddit_name)
        random.shuffle(valid_posts)

        for post in valid_posts:
            if send_post(post):
                print(f"\nWaiting {INTERVAL_BETWEEN_POSTS} minutes before next post...")
                time.sleep(INTERVAL_BETWEEN_POSTS * 60)

        current_subreddit_index = (current_subreddit_index + 1) % len(subreddits)
        print(f"\nSwitching to next subreddit. Waiting {INTERVAL_BETWEEN_SUBREDDITS} minutes...")
        time.sleep(INTERVAL_BETWEEN_SUBREDDITS * 60)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nBot manually stopped by user.")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
