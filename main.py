import requests
import feedparser
import pandas as pd
import yagmail
from openai import OpenAI
import os
import schedule
import time


def job():
    print("Running the news digest job...")

    # --- Fetch RSS ---
    RSS_URL = "https://www.france24.com/en/rss"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(RSS_URL, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching RSS feed: {e}")
        return

    feed = feedparser.parse(response.content)

    items = []
    for i, entry in enumerate(feed.entries[:15]):
        title = entry.get("title")
        link = entry.get("link")
        summary = entry.get("summary", "")
        items.append({"Headline": title, "Link": link, "Summary": summary})
        print(f"Processed entry {i}: {title}")

    df = pd.DataFrame(items)
    df.to_csv("france24_news.csv", index=False, encoding="utf-8")
    print("Saved", len(df), "items to france24_news.csv")

    # --- Summarization with Algion ---
    client = OpenAI(
        api_key=os.getenv("ALGION_KEY", "123123"),  # fallback to demo key
        base_url="https://api.algion.dev/v1"
    )

    def summarize(text):
        try:
            response = client.chat.completions.create(
                model='gpt-4.1',
                messages=[
                    {'role': 'system', 'content': 'You are a helpful assistant.'},
                    {'role': 'user', 'content': f"Rewrite this news summary in a professional and appealing way, with more details. Do not add headers/footers or mention AI:\n\n{text}"}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Summarization error: {e}")
            return "Could not generate summary."

    df['professional'] = df['Summary'].apply(summarize)

    # --- Send email ---
    try:
        sender_email = os.getenv("GMAIL_USER", "adysamuel68@gmail.com")
        password = os.getenv("GMAIL_PASS", "vfxj qepe yygj wkmi")
        emails = [
            "adysamuel67@gmail.com",
            "adysamuel69@gmail.com",
            "therealmindset70@gmail.com"
        ]

        yag = yagmail.SMTP(user=(sender_email, "Addys Automated News"), password=password)

        content = "\n\n".join(
            f"{row['Headline']} ({row['Link']})\n{row['professional']}"
            for _, row in df.iterrows()
        )

        for mail in emails:
            yag.send(to=mail, subject="Daily France24 Digest", contents=content)

        print("✅ Emails sent successfully!")

    except Exception as e:
        print(f"Email error: {e}")


# --- Schedule job at 7:30 daily ---
schedule.every().day.at("07:30").do(job)

print("⏳ Scheduler started. Waiting for 07:30 each day...")
while True:
    schedule.run_pending()
    time.sleep(60)