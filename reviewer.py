import os
import requests
import time
from google import genai
from datetime import datetime
import whois
from bs4 import BeautifulSoup

# 1. Setup & Configuration
# This looks for a URL input from GitHub Actions, or defaults to google.com
TARGET_URL = os.environ.get("TARGET_URL", "https://google.com")
if not TARGET_URL.startswith("http"):
    TARGET_URL = f"https://{TARGET_URL}"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL_ID = "gemini-2.0-flash" # Stable version for 2026

def get_site_audit_data(url):
    results = {"url": url, "ads_txt": "Unknown", "links": [], "title": "N/A", "meta_count": 0}
    try:
        # Main Page Request
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        results["title"] = soup.title.string if soup.title else "No Title Found"
        results["meta_count"] = len(soup.find_all('meta'))
        
        # Ads.txt Check
        ads_url = f"{url.rstrip('/')}/ads.txt"
        ads_check = requests.get(ads_url, timeout=5)
        results["ads_txt"] = "✅ Found" if ads_check.status_code == 200 else "❌ Missing"
        
        # Simple Broken Link Check (Top 5 links)
        links = [a.get('href') for a in soup.find_all('a', href=True) if a.get('href').startswith('http')][:5]
        for l in links:
            try:
                res = requests.head(l, timeout=3)
                if res.status_code >= 400:
                    results["links"].append(f"{l} (Status: {res.status_code})")
            except:
                results["links"].append(f"{l} (Timeout)")
    except Exception as e:
        results["error"] = str(e)
    return results

# 2. Collect Data
audit_data = get_site_audit_data(TARGET_URL)
domain_age = "Unknown"
try:
    domain_name = TARGET_URL.replace("https://","").replace("http://","").split('/')[0]
    w = whois.whois(domain_name)
    domain_age = str(w.creation_date)
except:
    pass

# 3. Request Gemini Analysis (With Retry)
prompt = f"""
Act as a Website Tutor & Compliance Expert.
Analyze this data for {TARGET_URL}:
- Ads.txt: {audit_data['ads_txt']}
- Broken Links: {audit_data['links']}
- Domain Age: {domain_age}
- SEO Title: {audit_data['title']}
- Meta Tags: {audit_data['meta_count']}

Tasks:
1. Provide a Scorecard (Table with Check, Status, Grade).
2. 'How to Fix' guide as a Tutor for each issue.
3. Advice on Content Quality and UX Navigation.

FORMAT: Return ONLY clean HTML. Do not use Markdown code blocks.
"""

response_text = ""
for attempt in range(3):
    try:
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        response_text = response.text
        break
    except Exception as e:
        print(f"Attempt {attempt+1} failed: {e}. Retrying...")
        time.sleep(10)

# 4. Final HTML Generation (Safe from backslash errors)
# We process formatting OUTSIDE the f-string to prevent crashes
html_body = response_text.replace('```html', '').replace('```', '').replace('\n', '<br>')

final_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 40px; background: #f4f7f9; color: #333; }}
        .container {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a73e8; border-bottom: 2px solid #e8f0fe; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; }}
        th {{ background: #f8f9fa; }}
        .tutor-note {{ font-style: italic; color: #555; background: #fffde7; padding: 10px; border-left: 4px solid #fbc02d; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Review for: {TARGET_URL}</h1>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <hr>
        <div>{html_body}</div>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(final_html)
