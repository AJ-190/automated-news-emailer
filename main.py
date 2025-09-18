import requests
import feedparser
import pandas as pd
import yagmail
from openai import OpenAI
import schedule
import time


def job():
    print("🚀 Running the news digest job...")

    # --- Step 1: Get news from RSS ---
    RSS_URL = "https://www.france24.com/en/rss"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(RSS_URL, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching RSS feed: {e}")
        return
    
    feed = feedparser.parse(response.content)

    items = []
    for i, entry in enumerate(feed.entries[:10]):  
        title = entry.get("title")
        link = entry.get("link")
        summary = entry.get("summary", "")

        items.append({"Headline": title, "Link": link, "Summary": summary})
        print(f"✅ Processed entry {i+1}: {title}")

    df = pd.DataFrame(items) 
    df.to_csv("france24_news.csv", index=False, encoding="utf-8")
    print(f"💾 Saved {len(df)} items to france24_news.csv")

    # --- Step 2: Summarize using Algion API ---
    client = OpenAI(
        api_key="123123",  
        base_url="https://api.algion.dev/v1"
    )

    def summarize(text):
        try:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Rewrite this news summary in a professional and appealing way, and make the heading bold:\n\n{text}"}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Summarization error: {e}")
            return text  

    df["professional"] = df["Summary"].apply(summarize)

    # --- Step 3: Send email with yagmail ---
    try:
        sender_email = "adysamuel68@gmail.com"
        password = "vfxj qepe yygj wkmi"  # Gmail App Password
        recipients = [
            "adysamuel67@gmail.com",
            "adysamuel69@gmail.com",
            "therealmindset70@gmail.com"
        ]

        content = "\n\n".join(
            f"{row['Headline']} ({row['Link']})\n{row['professional']}"
            for _, row in df.iterrows()
        )

        yag = yagmail.SMTP(user=sender_email, password=password)
        yag.send(
            to=recipients,
            subject="Daily France24 Digest",
            contents=content,
            headers={"from": "Addys Automated News"}
        )

        print("📧 Email sent successfully!")

    except Exception as e:
        print(f"❌ Error sending email: {e}")


# --- Step 4: Schedule the job ---
schedule.every().day.at("7:30").do(job)

print("✅ Scheduler started. Waiting for 14:24 PM daily...")


if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)

