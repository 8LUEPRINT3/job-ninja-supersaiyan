#!/usr/bin/env python3
"""
JobNinja SuperSaiyan — Job Scraper
Runs via GitHub Actions every 6 hours.
Fetches from multiple free APIs and saves to jobs.json
"""
import json, urllib.request, urllib.error, time, os
from datetime import datetime, timezone

TAGS = [
    'support', 'security', 'devops', 'cloud', 'network',
    'data', 'python', 'javascript', 'backend', 'fullstack',
    'product', 'project', 'finance', 'design', 'marketing',
    'hr', 'writing', 'ai', 'ml', 'mobile',
]

def fetch(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'JobNinjaSS/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f'  FAIL {url[:80]}: {e}')
        return None

def scrape_jobicy():
    """Jobicy — free remote jobs API, no key needed"""
    jobs = []
    seen = set()

    # Base fetch (latest 50)
    d = fetch('https://jobicy.com/api/v2/remote-jobs?count=50')
    if d and d.get('jobs'):
        for j in d['jobs']:
            if j['id'] not in seen:
                seen.add(j['id'])
                jobs.append(normalize_jobicy(j))

    # Per-tag fetches
    for tag in TAGS:
        time.sleep(0.5)  # be polite
        d = fetch(f'https://jobicy.com/api/v2/remote-jobs?count=20&tag={tag}')
        if d and d.get('jobs'):
            for j in d['jobs']:
                if j['id'] not in seen:
                    seen.add(j['id'])
                    jobs.append(normalize_jobicy(j))

    print(f'  Jobicy: {len(jobs)} jobs')
    return jobs

def normalize_jobicy(j):
    return {
        'id': f'jcy-{j["id"]}',
        'source': 'Jobicy',
        'title': j.get('jobTitle', ''),
        'company': j.get('companyName', ''),
        'logo': j.get('companyLogo', ''),
        'location': j.get('jobGeo', 'Worldwide'),
        'type': ', '.join(j.get('jobType', [])),
        'level': j.get('jobLevel', ''),
        'industry': ', '.join(j.get('jobIndustry', [])),
        'salary_min': j.get('salaryMin'),
        'salary_max': j.get('salaryMax'),
        'salary_currency': j.get('salaryCurrency', 'USD'),
        'excerpt': (j.get('jobExcerpt') or '').replace('<[^>]*>', '')[:300],
        'url': j.get('url', ''),
        'remote': True,
        'date': j.get('pubDate', ''),
        'tags': [j.get('jobLevel',''), *j.get('jobIndustry',[])],
    }

def scrape_remotive():
    """Remotive — remote jobs, no key needed"""
    jobs = []
    seen = set()

    categories = [
        'software-development', 'devops', 'data',
        'product', 'design', 'marketing', 'finance',
        'all-others',
    ]

    # Base
    d = fetch('https://remotive.com/api/remote-jobs?limit=100')
    if d and d.get('jobs'):
        for j in d['jobs']:
            if j['id'] not in seen:
                seen.add(j['id'])
                jobs.append(normalize_remotive(j))

    # Per category
    for cat in categories:
        time.sleep(0.3)
        d = fetch(f'https://remotive.com/api/remote-jobs?category={cat}&limit=50')
        if d and d.get('jobs'):
            for j in d['jobs']:
                if j['id'] not in seen:
                    seen.add(j['id'])
                    jobs.append(normalize_remotive(j))

    print(f'  Remotive: {len(jobs)} jobs')
    return jobs

def normalize_remotive(j):
    return {
        'id': f'rem-{j["id"]}',
        'source': 'Remotive',
        'title': j.get('title', ''),
        'company': j.get('company_name', ''),
        'logo': j.get('company_logo', ''),
        'location': j.get('candidate_required_location') or 'Worldwide',
        'type': j.get('job_type', ''),
        'level': '',
        'industry': j.get('category', ''),
        'salary_min': None,
        'salary_max': None,
        'salary_currency': 'USD',
        'excerpt': (j.get('description') or '')[:300],
        'url': j.get('url', ''),
        'remote': True,
        'date': j.get('publication_date', ''),
        'tags': j.get('tags', []),
    }

def scrape_arbeitnow():
    """Arbeitnow — free job board API with remote filter"""
    jobs = []
    seen = set()

    for page in range(1, 4):  # 3 pages = ~75 jobs
        time.sleep(0.3)
        d = fetch(f'https://www.arbeitnow.com/api/job-board-api?page={page}')
        if not d or not d.get('data'):
            break
        for j in d['data']:
            if j['slug'] not in seen:
                seen.add(j['slug'])
                jobs.append(normalize_arbeitnow(j))

    print(f'  Arbeitnow: {len(jobs)} jobs')
    return jobs

def normalize_arbeitnow(j):
    return {
        'id': f'abn-{j["slug"]}',
        'source': 'Arbeitnow',
        'title': j.get('title', ''),
        'company': j.get('company_name', ''),
        'logo': j.get('company_logo', ''),
        'location': j.get('location', 'Remote'),
        'type': j.get('job_types', [''])[0] if j.get('job_types') else '',
        'level': '',
        'industry': ', '.join(j.get('tags', [])[:3]),
        'salary_min': None,
        'salary_max': None,
        'salary_currency': 'USD',
        'excerpt': (j.get('description') or '')[:300],
        'url': j.get('url', ''),
        'remote': j.get('remote', False),
        'date': j.get('created_at', ''),
        'tags': j.get('tags', []),
    }

if __name__ == '__main__':
    print('🥷 JobNinja SuperSaiyan Scraper starting...')
    all_jobs = []

    print('Fetching Jobicy...')
    all_jobs += scrape_jobicy()

    print('Fetching Remotive...')
    all_jobs += scrape_remotive()

    print('Fetching Arbeitnow...')
    all_jobs += scrape_arbeitnow()

    # Deduplicate by title+company
    seen_key = set()
    deduped = []
    for j in all_jobs:
        key = (j['title'].lower().strip(), j['company'].lower().strip())
        if key not in seen_key:
            seen_key.add(key)
            deduped.append(j)

    # Sort by date descending
    deduped.sort(key=lambda j: str(j.get('date','')), reverse=True)

    output = {
        'updated': datetime.now(timezone.utc).isoformat(),
        'count': len(deduped),
        'jobs': deduped,
    }

    with open('jobs.json', 'w') as f:
        json.dump(output, f, separators=(',', ':'))

    print(f'✅ Done — {len(deduped)} unique jobs saved to jobs.json')
