import os
import requests
from google import genai
from datetime import datetime
import whois

# 1. UPDATED Configuration
TARGET_URL = "https://example.com" 

# Use the new Gemini 2.5 Flash (Free Tier stable model)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL_ID = "gemini-2.5-flash" 

def check_ads_txt(url):
    try:
        clean_url = url if url.startswith("http") else f"https://{url}"
        r = requests.get(f"{clean_url}/ads.txt", timeout=10)
        return "✅ Found" if r.status_code == 200 else "❌ Missing"
    except:
        return "⚠️ Error checking"

def get_domain_age(url):
    try:
        domain_name = url.replace("https://", "").replace("http://", "").split("/")[0]
        w = whois.whois(domain_name)
        creation_date = w.creation_date
        if isinstance(creation_date, list): creation_date = creation_date[0]
        return creation_date.strftime('%Y-%m-%d')
    except:
        return "Unknown"

# 2. Data Gathering
ads_status = check_ads_txt(TARGET_URL)
age = get_domain_age(TARGET_URL)

# 3. Request for Gemini 2.5
prompt = f"""
I am auditing {TARGET_URL}. 
Data: Ads.txt is {ads_status}, Domain age is {age}.
Please provide a 0-100 compliance score and a short 'Tutor' guide on how to improve.
Format as simple HTML.
"""

response = client.models.generate_content(
    model=MODEL_ID,
    contents=prompt
)

# 4. Save to index.html (with backslash fix)
clean_text = response.text.replace('\n', '<br>')
html_content = f"<html><body style='font-family:sans-serif; padding:20px;'>{clean_text}</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
