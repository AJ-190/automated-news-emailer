import os
import requests
import feedparser
import pandas as pd
import yagmail
from openai import OpenAI
from htmldocx import transform  # (assuming you installed this)

def job():
    # Accessing the url
    print('Running the news digest...')
    RSS_URL = "https://www.france24.com/en/france/rss"
    headers = {"User-Agent": "Mozilla/5.0"}

    # getting response
    try:
        response = requests.get(RSS_URL, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f'Error while fetching calling requests, {e}')
        return  # Exit if there's an error

    # filtering and searching for entries
    data = []  # store the fetched entries
    try:
        feed = feedparser.parse(response.content)
        print(f"Total entries: {len(feed.entries)}")
        for i, entry in enumerate(feed.entries[:15]):
            title = entry.get('title')
            link = entry.get('link')
            summary = entry.get('summary', '')
            image_url = None
            if 'media_thumbnail' in entry and entry['media_thumbnail']:
                image_url = entry['media_thumbnail'][0]['url']

            data.append({
                "title": title,
                "link": link,
                "summary": summary,
                "image_url": image_url
            })
            print(f"✅ Processed entry {i+1}: {title}")

    except Exception as e:
        print(f"Error while retrieving the data entries {e}")
        return  # Exit if there's an error

    df = pd.DataFrame(data)
    df.to_csv('news.csv', index=False, encoding='utf-8')

    # Chatbot set up
    try:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),   # 🔑 from env
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.algion.dev/v1")
        )

        def summarization(text):
            try:
                responses = client.chat.completions.create(
                    model='gpt-4.1',
                    messages=[
                        {"role": 'system', "content": 'You are a helpful assistant for searching for news articles'},
                        {"role": 'user', "content": f"Rewrite the news summary in a very professional and appealing way: \n\n {text}"}
                    ]
                )
                return responses.choices[0].message.content.strip()
            except Exception as e:
                print(f"Error summarizing: {e}")
                return text

    except Exception as e:
        print(f"Error while communicating with the chatbot: {e}")
        return  # Exit if there's an error

    # applying the function
    df["professional"] = df["summary"].apply(summarization)

    print("News digest generated and summarized successfully!")

    try:
        sender_mail = os.getenv("SENDER_EMAIL")    # 🔑 from env
        password = os.getenv("EMAIL_PASSWORD")     # 🔑 from env
        recipients = os.getenv["RECIPIENTS"]
        

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
                .title {
                  font-size: 24px;
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
                .news-image {
                  max-width: 100%;
                  height: auto;
                  border-radius: 8px;
                  margin-bottom: 10px;
                }
              </style>
            </head>
            <body>
              <h2>🌍 Daily France24 Digest</h2>
        """

        # Loop through rows and add them as styled cards
        for _, row in df.iterrows():
            html_content += '<div class="news-card">'
            if row['image_url']:
                html_content += f'<img src="{row["image_url"]}" class="news-image" alt="News Image">'
            html_content += f"""
              <div class="title">{row['title']}</div>
              <div class="summary">{row['professional']}</div>
              <a class="link" href="{row['link']}">Read Full Article</a>
            </div>
            """

        html_content += """
            </body>
        </html>
        """
    except Exception as e:
        print(f"Error while preparing email HTML: {e}")
        return

    inline_html = transform(html_content)

    for user in recipients:
        print(f'Sending to {user}')
        try:
            yag = yagmail.SMTP(user=sender_mail, password=password)
            yag.send(
                to=user,
                subject='Daily France24 Digest',
                contents=[inline_html],
                headers={"From": "Addys Automated News"}
            )
            print(f'Email sent to {user}')
        except Exception as e:
            print(f'Error while sending email to {user}: {e}')