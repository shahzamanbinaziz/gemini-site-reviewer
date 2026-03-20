import os
import requests
import google.generativeai as genai
from datetime import datetime
import whois # You'll need: pip install python-whois

# 1. Configuration
TARGET_URL = "https://example.com" # You can make this dynamic later
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

def check_ads_txt(url):
    try:
        r = requests.get(f"{url}/ads.txt", timeout=10)
        return "Found" if r.status_code == 200 else "Missing"
    except:
        return "Error checking"

def get_domain_age(url):
    try:
        domain = whois.whois(url)
        creation_date = domain.creation_date
        if isinstance(creation_date, list): creation_date = creation_date[0]
        return str(creation_date)
    except:
        return "Unknown"

# 2. Collect Data
data_summary = f"""
Site: {TARGET_URL}
Ads.txt Status: {check_ads_txt(TARGET_URL)}
Domain Creation: {get_domain_age(TARGET_URL)}
Broken Links: [Simulated: 2 links found: /about-old, /broken-page]
"""

# 3. Gemini "Tutor" Prompt
prompt = f"""
You are a Website Compliance Tutor. Analyze this data:
{data_summary}

Provide a scorecard (0-100) and a "How to Fix" guide for:
1. Ads.txt Compliance
2. Broken Links
3. Domain Trust
Make it encouraging and technical but easy to follow.
"""

response = model.generate_content(prompt)

# 4. Save as HTML for GitHub Pages
with open("index.html", "w") as f:
    f.write(f"<html><body><h1>Review for {TARGET_URL}</h1>")
    f.write(f"<div>{response.text.replace('\n', '<p>')}</div>")
    f.write(f"<p>Last Updated: {datetime.now()}</p></body></html>")
