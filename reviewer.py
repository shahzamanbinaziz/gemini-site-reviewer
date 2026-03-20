import os
import requests
import time
from google import genai
from datetime import datetime
import whois
from bs4 import BeautifulSoup

# 1. Configuration
TARGET_URL = os.environ.get("TARGET_URL", "https://google.com")
if not TARGET_URL.startswith("http"):
    TARGET_URL = f"https://{TARGET_URL}"

# Setup Client
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL_ID = "gemini-2.0-flash"

def get_audit_data(url):
    results = {"ads_txt": "Unknown", "title": "N/A", "links": []}
    try:
        # Check Ads.txt
        ads_url = f"{url.rstrip('/')}/ads.txt"
        r = requests.get(ads_url, timeout=5)
        results["ads_txt"] = "✅ Found/Valid" if r.status_code == 200 else "❌ Missing"
        
        # Check Title/SEO
        page = requests.get(url, timeout=10)
        soup = BeautifulSoup(page.text, 'html.parser')
        results["title"] = soup.title.string if soup.title else "Missing Title"
    except:
        pass
    return results

# 2. Gather Data
data = get_audit_data(TARGET_URL)

# 3. Request Review with STRICT Formatting
# We use 'system_instruction' to force Gemini to stay in 'Table Mode'
prompt = f"""
AUDIT REPORT FOR: {TARGET_URL}
Ads.txt Status: {data['ads_txt']}
Page Title: {data['title']}

INSTRUCTIONS:
1. Create a 3-column HTML TABLE: Check Name, Status, and Tutor's Grade (A-F).
2. Below the table, provide a 'Tutor's Secret' section with 2 bullet points on how to improve this specific site.
3. Use only standard HTML tags (<table>, <tr>, <td>, <h3>, <ul>).
4. DO NOT include ```html tags or any markdown.
"""

# Call Gemini with Retry
response_text = "Analysis Error"
for _ in range(3):
    try:
        # We add system_instruction here to make the AI more reliable
        response = client.models.generate_content(
            model=MODEL_ID, 
            contents=prompt,
            config={'system_instruction': "You are a web auditor. Output ONLY valid HTML body content. No backticks."}
        )
        response_text = response.text
        break
    except:
        time.sleep(5)

# 4. Save to File
# Clean out any accidental markdown if Gemini ignores instructions
clean_html = response_text.replace('```html', '').replace('```', '')

final_output = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: sans-serif; padding: 50px; background: #f9f9f9; }}
        .card {{ background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid #eee; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 15px; border-bottom: 1px solid #eee; text-align: left; }}
        th {{ color: #1a73e8; text-transform: uppercase; font-size: 0.8em; letter-spacing: 1px; }}
        h1 {{ color: #222; margin-bottom: 5px; }}
        .url-badge {{ background: #1a73e8; color: white; padding: 4px 12px; border-radius: 5px; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Site Audit Report</h1>
        <span class="url-badge">{TARGET_URL}</span>
        <hr style="margin: 30px 0; border: 0; border-top: 1px solid #eee;">
        {clean_html}
        <p style="margin-top:40px; color:#aaa; font-size:0.8em;">Generated on {datetime.now().strftime('%Y-%m-%d')}</p>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(final_output)
