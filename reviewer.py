import os
import requests
from google import genai # New SDK
from datetime import datetime
import whois

# 1. Configuration & API Setup
TARGET_URL = "https://google.com" 

# Setup the new Gemini Client
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL_ID = "gemini-1.5-flash"

def check_ads_txt(url):
    try:
        clean_url = url if url.startswith("http") else f"https://{url}"
        r = requests.get(f"{clean_url}/ads.txt", timeout=10)
        return "✅ Found" if r.status_code == 200 else "❌ Missing"
    except Exception:
        return "⚠️ Error checking"

def get_domain_age(url):
    try:
        domain_name = url.replace("https://", "").replace("http://", "").split("/")[0]
        w = whois.whois(domain_name)
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        return creation_date.strftime('%Y-%m-%d')
    except:
        return "Unknown"

# 2. Collect Data
ads_status = check_ads_txt(TARGET_URL)
domain_age = get_domain_age(TARGET_URL)

data_summary = f"""
Site Analyzed: {TARGET_URL}
Ads.txt Status: {ads_status}
Domain Creation Date: {domain_age}
"""

# 3. Gemini "Tutor" Prompt
prompt = f"""
Analyze this website data: {data_summary}
1. Create a scorecard table (Check, Status, Grade).
2. Provide a 'Tutor's Guide' explaining how to fix issues (especially if ads.txt is missing).
Format as clean HTML.
"""

# New way to call the model
response = client.models.generate_content(
    model=MODEL_ID,
    contents=prompt
)

# 4. Save the Report
# Extract the text from the new response object
raw_report = response.text.replace('\n', '<br>')

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: auto; padding: 20px; background: #f4f7f6; }}
        .card {{ background: white; padding: 20px; border-radius: 10px; shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Site Audit: {TARGET_URL}</h1>
        <div>{raw_report}</div>
        <p><small>Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
