# Daily Remote Data Analyst Job Search

## What this repo does
- Runs daily (10:00 AM West Africa Time / UTC+1) as a GitHub Action.
- Fetches remote Data Analyst jobs from Remotive (API) plus best-effort scraping from TopStartups and Wellfound.
- Deduplicates results, builds an HTML table, and emails it to `Tanko8668@gmail.com` using SendGrid.

## Setup
1. Create a SendGrid account and obtain an API key.
2. Verify the sender email (recommended same as recipient).
3. Create a GitHub repository and push these files.
4. In GitHub: Settings → Secrets and variables → Actions → New repository secret:
   - `SENDGRID_API_KEY` = your SendGrid API key
5. (Optional) Modify schedule in `.github/workflows/daily-job-search.yml`.

## Notes
- Wellfound pages are often rendered with JavaScript; scraping may not return results without a headless browser. The Remotive API is the most reliable source in this script.
- You can expand sources, add caching, or store results in the repo as CSVs if you want history.