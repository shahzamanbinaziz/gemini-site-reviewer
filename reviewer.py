import os
import requests
import time
from google import genai
from datetime import datetime
import whois
from bs4 import BeautifulSoup # You'll need: pip install beautifulsoup4

# 1. Configuration
TARGET_URL = os.environ.get("TARGET_URL", "https://google.com") # Pulls from GitHub Action
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL_ID = "gemini-2.0-flash"

def get_site_data(url):
    results = {"url": url, "ads_txt": "Missing", "links": [], "status": 200, "html": ""}
    try:
        response = requests.get(url, timeout=15)
        results["status"] = response.status_code
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check Ads.txt
        ads_req = requests.get(f"{url.rstrip('/')}/ads.txt", timeout=5)
        results["ads_txt"] = "✅ Valid" if ads_req.status_code == 200 else "❌ Missing"
        
        # Check for Broken Links (First 10 links for speed)
        all_links = [a.get('href') for a in soup.find_all('a', href=True)][:10]
        for link in all_links:
            if link.startswith('http'):
                try:
                    res = requests.head(link, timeout=3)
                    if res.status_code >= 400:
                        results["links"].append(f"{link} ({res.status_code})")
                except:
                    results["links"].append(f"{link} (Timeout)")
                    
        results["title"] = soup.title.string if soup.title else "No Title"
        results["meta"] = len(soup.find_all('meta'))
    except Exception as e:
        results["error"] = str(e)
    return results

# 2. Execution
data = get_site_data(TARGET_URL)
domain_info = "Unknown"
try:
    w = whois.whois(TARGET_URL.replace("https://","").split('/')[0])
    domain_info = str(w.creation_date)
except: pass

# 3. The "Tutor" Prompt
prompt = f"""
Act as a Web Compliance Tutor. Analyze:
URL: {data['url']}
Ads.txt: {data['ads_txt']}
Broken Links Found: {data['links']}
Domain Age: {domain_info}
Page Title: {data.get('title')}

Provide:
1. A Scorecard (0-100).
2. A 'Fix-It' guide for Ads.txt, Broken Links, and UX Navigation.
3. Suggest 2 ways to improve 'Content Originality'.
Return ONLY clean HTML (no markdown code blocks).
"""

# ... (Insert the same Retry Logic from previous message here) ...
# ... (Save to index.html as before) ...
