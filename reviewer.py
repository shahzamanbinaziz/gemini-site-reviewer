import os
import requests
import google.generativeai as genai
from datetime import datetime
import whois

# 1. Configuration & API Setup
# TIP: You can change this URL to test different sites
TARGET_URL = "https://google.com" 

# Setup Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

def check_ads_txt(url):
    try:
        # Ensure URL has protocol
        clean_url = url if url.startswith("http") else f"https://{url}"
        r = requests.get(f"{clean_url}/ads.txt", timeout=10)
        return "✅ Found" if r.status_code == 200 else "❌ Missing"
    except Exception as e:
        return f"⚠️ Error: {str(e)[:30]}"

def get_domain_age(url):
    try:
        domain_name = url.replace("https://", "").replace("http://", "").split("/")[0]
        w = whois.whois(domain_name)
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        return creation_date.strftime('%Y-%m-%d')
    except:
        return "Unknown (Private/Restricted)"

# 2. Collect Raw Data
ads_status = check_ads_txt(TARGET_URL)
domain_age = get_domain_age(TARGET_URL)

data_summary = f"""
Site Analyzed: {TARGET_URL}
Ads.txt Status: {ads_status}
Domain Creation Date: {domain_age}
Check: Broken Links (Simulated Scan)
Check: UX & Navigation (Structural Analysis)
"""

# 3. Gemini "Tutor" Prompt
prompt = f"""
You are a Website Compliance & SEO Tutor. 
Analyze this data for {TARGET_URL}:
{data_summary}

Tasks:
1. Create a 3-column Markdown table for a 'Scorecard' with: Check Name, Status (Pass/Fail/Warning), and Grade (A-F).
2. Provide a 'Tutor's Guide' section. For each issue found, explain WHY it matters and give STEP-BY-STEP instructions on how to fix it.
3. Be professional, encouraging, and clear.
"""

response = model.generate_content(prompt)

# 4. Generate the HTML Report
# We fix the backslash issue by processing text before putting it in the f-string
raw_report = response.text.replace('\n', '<br>')

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Site Audit: {TARGET_URL}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 40px; background-color: #f9f9f9; }}
        .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #eee; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .meta {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        .tutor-section {{ background: #e8f4fd; border-left: 5px solid #3498db; padding: 15px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Website Audit Report</h1>
        <p class="meta">Target URL: <strong>{TARGET_URL}</strong><br>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        
        <div class="report-content">
            {raw_report}
        </div>
        
        <hr>
        <p style="text-align: center; font-size: 0.8em; color: #999;">Powered by Gemini AI & GitHub Actions</p>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Report generated successfully as index.html")
