import requests
import feedparser
import pandas as pd
import yagmail
from openai import OpenAI
import schedule
import time
from premailer import transform


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
    for i, entry in enumerate(feed.entries[:15]):
        title = entry.get("title")
        link = entry.get("link")
        summary = entry.get("summary", "")

        items.append({"Headline": title, "Link": link, "Summary": summary})
        print(f"✅ Processed entry {i+1}: {title}")

    df = pd.DataFrame(items)
    df.to_csv("france24_news.csv", index=False, encoding="utf-8")
    # print(f"💾 Saved {len(df)} items to france24_news.csv")

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
                    {"role": "user", "content": f"Rewrite this news summary in a professional and appealing way:\n\n{text}"}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Summarization error: {e}")
            return text

    df["professional"] = df["Summary"].apply(summarize)

    # --- Step 3: Send email with yagmail (HTML version) ---
    try:
        sender_email = "adysamuel68@gmail.com"
        password = "vfxj qepe yygj wkmi"  # Gmail App Password
        recipients = [
            "adysamuel67@gmail.com",
            "adysamuel69@gmail.com",
            "therealmindset70@gmail.com",
            "bensonofosuappiah9@gmail.com"
        ]

        # Build HTML email content
        html_content = """
        <html>
        <head>
          <style>
            body {
              font-family: Arial, sans-serif;
              background: #f4f4f9;
              padding: 20px;
              color: #333;
            }
            h2 {
              color: #2a9d8f;
            }
            .news-card {
              background: #fff;
              padding: 15px;
              margin-bottom: 15px;
              border-radius: 10px;
              box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
            }
            .headline {
              font-size: 18px;
              font-weight: bold;
              margin-bottom: 5px;
              color: #264653;
            }
            .summary {
              font-size: 14px;
              color: #555;
              margin-bottom: 8px;
            }
            .link {
              display: inline-block;
              margin-top: 8px;
              padding: 6px 12px;
              background: #2a9d8f;
              color: white;
              text-decoration: none;
              border-radius: 6px;
            }
            .link:hover {
              background: #21867a;
            }
          </style>
        </head>
        <body>
          <h2>🌍 Daily France24 Digest</h2>
        """

        # Loop through rows and add them as styled cards
        for _, row in df.iterrows():
            html_content += f"""
            <div class="news-card">
              <div class="headline">{row['Headline']}</div>
              <div class="summary">{row['professional']}</div>
              <a class="link" href="{row['Link']}">Read Full Article</a>
            </div>
            """

        # Close the HTML body
        html_content += """
        </body>
        </html>
        """

        # Inline CSS using premailer
        inlined_html = transform(html_content)

        # Send styled HTML email
        yag = yagmail.SMTP(user=sender_email, password=password)
        yag.send(
            to=recipients,
            subject="Daily France24 Digest 🌍",
            contents=[inlined_html],  # send as HTML
            headers={"from": "Addy's Automated News"}
        )

        print("📧 Styled HTML Email sent successfully!")

    except Exception as e:
        print(f"❌ Error sending email: {e}")


# --- Step 4: Schedule the job ---
# You can change the time below as needed (format: "HH:MM")
schedule.every().day.at("23:28").do(job)
print("✅ Scheduler started. Waiting for 11:28 PM daily...")

while True:
    schedule.run_pending()
    time.sleep(20)     