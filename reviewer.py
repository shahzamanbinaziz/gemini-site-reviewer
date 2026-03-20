import os
import requests
import time
from google import genai
from datetime import datetime
import whois
from bs4 import BeautifulSoup

# 1. Configuration
TARGET_URL = os.environ.get("TARGET_URL", "https://propakistani.pk")
if not TARGET_URL.startswith("http"):
    TARGET_URL = f"https://{TARGET_URL}"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL_ID = "gemini-2.0-flash"

def get_audit_data(url):
    results = {"ads_txt": "Unknown", "title": "N/A"}
    try:
        # Check Ads.txt
        ads_url = f"{url.rstrip('/')}/ads.txt"
        r = requests.get(ads_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        results["ads_txt"] = "✅ Found" if r.status_code == 200 else "❌ Missing"
        
        # Check Title
        page = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(page.text, 'html.parser')
        results["title"] = soup.title.string.strip() if soup.title else "Missing Title"
    except Exception as e:
        results["ads_txt"] = f"Error: {str(e)[:30]}"
    return results

# 2. Gather Data
data = get_audit_data(TARGET_URL)

# 3. Request Review (Simplified to prevent 503/Analysis Errors)
prompt = f"""
You are a Web Auditor. Write a report for {TARGET_URL}.
Data: Ads.txt is {data['ads_txt']}, Title is {data['title']}.

Output exactly this structure in HTML:
1. A table with 3 columns: Feature, Status, and Grade.
2. A 'Tutor Advice' section with 3 bullet points.

Rules: No markdown, no backticks, just raw HTML tags.
"""

response_text = "<h3>Analysis Currently Unavailable</h3><p>The AI is busy. Please try running the workflow again in a few minutes.</p>"

for attempt in range(3):
    try:
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        if response.text:
            response_text = response.text
            break
    except Exception as e:
        print(f"Gemini Attempt {attempt+1} failed: {e}")
        time.sleep(10)

# 4. Final HTML Generation
# We clean the text just in case the AI added backticks
clean_body = response_text.replace('```html', '').replace('```', '')

final_output = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 40px; background: #f0f2f5; }}
        .report-card {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 800px; margin: auto; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; border: 1px solid #eee; text-align: left; }}
        th {{ background: #1a73e8; color: white; }}
        h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
        .footer {{ margin-top: 30px; font-size: 0.8em; color: #777; border-top: 1px solid #eee; padding-top: 10px; }}
    </style>
</head>
<body>
    <div class="report-card">
        <h1>Audit: {TARGET_URL}</h1>
        <div>{clean_body}</div>
        <div class="footer">
            Analyzed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(final_output)
