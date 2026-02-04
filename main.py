# main.py - X.com (Twitter) Job Poster (Stateful, ALL Today, IST Safe)

import time
import requests
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import io
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

from x_posters import post_to_x

load_dotenv()

# ========================================
# CONFIG
# ========================================
BLOG_FEED_URL = 'https://www.firstjobtech.in/feeds/posts/default?alt=json'
POSTED_JOBS_FILE = 'posted_jobs.txt'
IST = pytz.timezone("Asia/Kolkata")

# ========================================
# Helper: Track posted jobs
# ========================================
def load_posted_jobs():
    if not os.path.exists(POSTED_JOBS_FILE):
        return set()
    with open(POSTED_JOBS_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def save_posted_job(job_id):
    with open(POSTED_JOBS_FILE, 'a') as f:
        f.write(f"{job_id}\n")

# ========================================
# Helper: Check if Blogger post is TODAY (IST)
# ========================================
def is_today(date_str):
    try:
        # Example: 2026-02-03T23:55:53.238-08:00
        dt = datetime.fromisoformat(date_str)
        dt_ist = dt.astimezone(IST)
        return dt_ist.date() == datetime.now(IST).date()
    except Exception as e:
        print(f"Date parsing error: {date_str} -> {e}")
        return False

# ========================================
# Helper: Extract Company & Logo
# ========================================
def extract_job_metadata(entry):
    title_text = entry.get('title', {}).get('$t', '')
    content_html = entry.get('content', {}).get('$t', '')

    company_name = "Company"
    if " - " in title_text:
        parts = title_text.split(" - ")
        if len(parts) > 1:
            raw_company = parts[1]
            clean_company = re.sub(
                r'(Recruitment|Hiring|Off Campus|Job|Careers).*',
                '',
                raw_company,
                flags=re.IGNORECASE
            ).strip()
            if clean_company:
                company_name = clean_company

    logo_url = None
    img_match = re.search(r'<img[^>]+src="([^">]+)"', content_html)
    if img_match:
        logo_url = img_match.group(1)

    return company_name, logo_url

# ========================================
# Caption Formatter (280 char safe)
# ========================================
def format_caption(job):
    title = job['title']
    company = job['company_name']
    url = job['url']

    hashtags = f"#Hiring #Jobs #{company.replace(' ', '')} #Careers #OffCampus"

    caption = (
        f"🚀 New Job Alert: {title}\n\n"
        f"🏢 {company}\n"
        f"🔗 Apply: {url}\n\n"
        f"{hashtags}"
    )

    # X.com hard limit
    if len(caption) > 280:
        caption = caption[:277] + "..."

    return caption

# ========================================
# Fetch ALL TODAY jobs (IST)
# ========================================
def fetch_today_jobs():
    try:
        print(f"Fetching from: {BLOG_FEED_URL}")
        response = requests.get(BLOG_FEED_URL, timeout=15)

        if response.status_code != 200:
            print(f"Blogger API error: {response.status_code}")
            return []

        data = response.json()
        entries = data.get('feed', {}).get('entry', [])

        today_jobs = []

        for entry in entries:
            published = entry.get('published', {}).get('$t', '')
            if not is_today(published):
                continue

            raw_id = entry.get('id', {}).get('$t', '')
            job_id = raw_id.split('-')[-1]

            title = entry.get('title', {}).get('$t', 'Job Opening')
            link_url = next(
                (l.get('href') for l in entry.get('link', []) if l.get('rel') == 'alternate'),
                ""
            )

            company_name, logo_url = extract_job_metadata(entry)

            today_jobs.append({
                'id': job_id,
                'title': title,
                'company_name': company_name,
                'company_logo': logo_url,
                'url': link_url,
                'published': published
            })

            print(f"✓ Today job found: {title}")

        print(f"Total jobs TODAY (IST): {len(today_jobs)}")
        return today_jobs

    except Exception as e:
        print(f"Fetch error: {e}")
        return []

# ========================================
# MAIN
# ========================================
def main():
    print("AI X.com (Twitter) Job Poster")
    print("Stateful | All Today's Jobs | Text Only | IST Safe")
    print("=" * 60)

    if not os.getenv('TWITTER_API_KEY'):
        print("ERROR: Missing Twitter credentials in .env")
        return

    posted_jobs = load_posted_jobs()
    today_jobs = fetch_today_jobs()

    if not today_jobs:
        print("No jobs found for today.")
        return

    first_post = True
    success = 0

    for job in today_jobs:
        if job['id'] in posted_jobs:
            continue

        if not first_post:
            print("Waiting 5 minutes before next post...")
            time.sleep(300)

        caption = format_caption(job)

        if post_to_x(caption, image_path=None):
            save_posted_job(job['id'])
            success += 1
            first_post = False
            print("✅ Posted successfully (Text Only)")
        else:
            print("❌ Failed to post")

    print(f"\nBatch completed. Posted {success} jobs today.")

if __name__ == "__main__":
    main()
