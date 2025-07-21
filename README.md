# 🔁 Reddit to Telegram Bot

This Python bot automatically fetches posts from a list of subreddits and sends them to a specified Telegram channel or group.

---

## 📦 Features

- Pulls media content from Reddit subreddits using the Reddit API (`praw`)
- Filters posts by minimum upvotes and allowed media types
- Avoids duplicate posts using SQLite
- Sends photos, GIFs, and videos directly to Telegram via bot API
- Reads subreddit list from a file (`subreddits.txt`)
- Logs errors to a local file
- Easily customizable time intervals between posts and subreddit rotations

---

## 🧰 Requirements

- Python 3.7+
- Telegram Bot Token (from @BotFather)
- Reddit API credentials (from https://www.reddit.com/prefs/apps)

---

## 📚 Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/reddit-telegram-bot.git
   cd reddit-telegram-bot

2. **Install The Requirements:**
    pip install -r requirements.txt

3. **Add your credentials:**
    Open the script and replace the placeholders:
        client_id="YOUR_REDDIT_CLIENT_ID"
        client_secret="YOUR_REDDIT_SECRET"
        username="YOUR_REDDIT_USERNAME"
        password="YOUR_REDDIT_PASSWORD"
        TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
        CHAT_ID = YOUR_CHANNEL_OR_GROUP_ID

4. **Add your SubReddits:**
    Create a file named subreddits.txt in the root of the project. Add one subreddit name per line:
        memes
        cosplay
        etc...

5. **Configuration:**
    Edit these variables in the script:
        INTERVAL_BETWEEN_POSTS = 0.5  # Minutes between posts
        INTERVAL_BETWEEN_SUBREDDITS = 20  # Minutes between switching subreddits
        POST_LIMIT = 1000  # How many posts to check from subreddit
        MIN_UPVOTES = 20  # Minimum upvotes required


6. **Run:**
    Run the bot with:
        python Telegram_Bot.py
