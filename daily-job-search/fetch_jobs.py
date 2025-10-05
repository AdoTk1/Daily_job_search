#!/usr/bin/env python3
"""Daily Remote Data Analyst job fetcher.
- Uses Remotive API (reliable) + best-effort scraping for Wellfound & TopStartups.
- Builds a deduplicated HTML table and emails it using SendGrid.
Configure SENDGRID_API_KEY in GitHub Secrets and set FROM_EMAIL (default uses TO_EMAIL).
"""
import os
import time
import requests
from bs4 import BeautifulSoup
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from urllib.parse import urljoin

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
TO_EMAIL = os.getenv("TO_EMAIL", "Tanko8668@gmail.com")
FROM_EMAIL = os.getenv("FROM_EMAIL", TO_EMAIL)

USER_AGENT = "Mozilla/5.0 (compatible; JobFetcher/1.0; +https://github.com/)"
HEADERS = {"User-Agent": USER_AGENT}

def fetch_remotive():
    endpoint = "https://remotive.com/api/remote-jobs"
    params = {"search": "data analyst"}
    try:
        resp = requests.get(endpoint, params=params, timeout=15, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json().get("jobs", [])
        jobs = []
        for j in data:
            title = j.get("title","")
            if "data analyst" in title.lower() or "data" in title.lower() and "analyst" in title.lower():
                jobs.append({
                    "company": j.get("company_name") or "-",
                    "title": title,
                    "location": j.get("candidate_required_location") or "Remote",
                    "link": j.get("url"),
                    "keywords": "analysis; reporting; dashboards; metrics; data",
                    "skills": "Python; SQL; Excel; BI tools; statistics"
                })
        return jobs
    except Exception as e:
        print("Remotive error:", e)
        return []

def fetch_topstartups():
    url = "https://topstartups.io/jobs/?role=Data+Analyst"
    try:
        resp = requests.get(url, timeout=15, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        # Heuristic parsing: look for links to job pages
        for a in soup.select("a[href]"):
            txt = a.get_text(" ", strip=True)
            href = a.get("href")
            if not href or not txt:
                continue
            if "analyst" in txt.lower() and len(txt) < 200:
                full = href if href.startswith("http") else urljoin("https://topstartups.io", href)
                jobs.append({
                    "company": "-",
                    "title": txt,
                    "location": "Remote",
                    "link": full,
                    "keywords": "data; metrics; dashboards; insights; reporting",
                    "skills": "SQL; Python; visualization; data pipelines; statistics"
                })
        return jobs
    except Exception as e:
        print("TopStartups error:", e)
        return []

def fetch_wellfound():
    base = "https://wellfound.com"
    url = base + "/role/r/data-analyst"
    try:
        resp = requests.get(url, timeout=15, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        # Wellfound page structure may be dynamic (JS). This is best-effort scraping.
        for a in soup.select("a[href]"):
            txt = a.get_text(" ", strip=True)
            href = a.get("href")
            if not href or not txt:
                continue
            if "data analyst" in txt.lower() or ("data" in txt.lower() and "analyst" in txt.lower()):
                full = href if href.startswith("http") else urljoin(base, href)
                jobs.append({
                    "company": "-",
                    "title": txt,
                    "location": "Remote",
                    "link": full,
                    "keywords": "data; metrics; reporting; dashboards; insights",
                    "skills": "SQL; Python; Looker/Tableau; Excel; stats"
                })
        return jobs
    except Exception as e:
        print("Wellfound error (page may be JS-driven):", e)
        return []

def dedupe_jobs(jobs):
    seen = set()
    out = []
    for j in jobs:
        key = (j.get("link") or "").strip() or (j.get("company","") + "|" + j.get("title",""))
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out

def build_html_table(jobs):
    rows = ""
    for j in jobs:
        rows += (
            f"<tr>"
            f"<td>{j.get('company')}</td>"
            f"<td>{j.get('title')}</td>"
            f"<td>{j.get('location')}</td>"
            f"<td><a href='{j.get('link')}'>Apply</a></td>"
            f"<td>{j.get('keywords')}</td>"
            f"<td>{j.get('skills')}</td>"
            f"</tr>"
        )
    html = (
        "<h2>Daily Remote Data Analyst Jobs — Consolidated</h2>"
        "<p>Source: Remotive API + TopStartups + Wellfound (best-effort scraping)</p>"
        "<table border='1' cellpadding='6' style='border-collapse:collapse;'>"
        "<thead><tr><th>Company</th><th>Title</th><th>Location</th><th>Link</th><th>Keywords</th><th>Skills</th></tr></thead>"
        "<tbody>"
        + rows +
        "</tbody></table>"
    )
    return html

def send_email(html_body):
    if not SENDGRID_API_KEY:
        raise RuntimeError("SENDGRID_API_KEY not set in environment")
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=TO_EMAIL,
        subject="Daily Remote Data Analyst Jobs",
        html_content=html_body
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    resp = sg.send(message)
    print("Email sent, status:", resp.status_code)

def main():
    all_jobs = []
    all_jobs.extend(fetch_remotive())
    # Small delay to be polite
    time.sleep(1)
    all_jobs.extend(fetch_topstartups())
    time.sleep(1)
    all_jobs.extend(fetch_wellfound())
    jobs = dedupe_jobs(all_jobs)
    if not jobs:
        print("No jobs found — sending short status email.")
        send_email("<p>No remote Data Analyst jobs found today.</p>")
        return
    html = build_html_table(jobs)
    send_email(html)

if __name__ == "__main__":
    main()