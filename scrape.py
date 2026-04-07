#!/usr/bin/env python3
"""
JobNinja SuperSaiyan — Job Scraper
Runs via GitHub Actions every 6 hours.
Fetches from multiple free APIs and saves to jobs.json
"""
import json, urllib.request, urllib.error, time, os
from datetime import datetime, timezone

TAGS = [
    # Tech
    'support', 'security', 'devops', 'cloud', 'network',
    'data', 'python', 'javascript', 'backend', 'fullstack',
    'ai', 'ml', 'mobile', 'qa', 'ios', 'android',
    # Business
    'sales', 'finance', 'accounting', 'legal', 'operations',
    'product', 'project', 'business', 'consulting', 'strategy',
    # Creative
    'design', 'marketing', 'content', 'writing', 'social',
    'video', 'ux', 'brand', 'seo', 'copywriting',
    # People
    'hr', 'recruiting', 'customer', 'education', 'community',
    'coaching', 'training',
    # Other
    'healthcare', 'research', 'logistics', 'nonprofit', 'real estate',
]

def fetch(url, timeout=15):
    try:
        url = url.replace(' ', '+')
        req = urllib.request.Request(url, headers={'User-Agent': 'JobNinjaSS/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f'  FAIL {url[:80]}: {e}')
        return None

def fetch_url(url, timeout=15):
    """Follow redirects and return raw bytes."""
    import urllib.request
    url = url.replace(' ', '+')
    req = urllib.request.Request(url, headers={'User-Agent': 'JobNinjaSS/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

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
        'software-development', 'devops-sysadmin', 'data',
        'product', 'design', 'marketing', 'finance-legal',
        'customer-support', 'sales', 'human-resources',
        'project-management', 'business', 'writing',
        'qa', 'medical-health', 'teaching-education',
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

def scrape_remoteok():
    """RemoteOK — free public API, no key needed"""
    jobs = []
    d = fetch('https://remoteok.com/api', timeout=20)
    if not d:
        return jobs
    for j in d:
        if not isinstance(j, dict) or not j.get('position'):
            continue
        jobs.append({
            'id': f'rok-{j.get("id","")}',
            'source': 'RemoteOK',
            'title': j.get('position', ''),
            'company': j.get('company', ''),
            'logo': j.get('company_logo', ''),
            'location': j.get('location') or 'Worldwide',
            'type': 'Full-time',
            'level': '',
            'industry': ', '.join(j.get('tags', [])[:3]),
            'salary_min': None,
            'salary_max': None,
            'salary_currency': 'USD',
            'excerpt': (j.get('description') or '').replace('<br />', ' ').replace('<[^>]*>', '')[:300],
            'url': j.get('url', ''),
            'remote': True,
            'date': j.get('date', ''),
            'tags': j.get('tags', []),
        })
    print(f'  RemoteOK: {len(jobs)} jobs')
    return jobs


def scrape_workingnomads():
    """Working Nomads — free public API"""
    jobs = []
    # Fetch all categories
    categories = ['it', 'programming', 'design', 'marketing', 'sales',
                  'customer-support', 'writing', 'business', 'finance',
                  'product', 'data', 'devops', 'legal', 'hr', 'education']
    seen = set()

    # Base fetch
    d = fetch('https://www.workingnomads.com/api/exposed_jobs/?limit=100')
    if d:
        for j in d:
            if j.get('slug') not in seen:
                seen.add(j.get('slug'))
                jobs.append(normalize_workingnomads(j))

    for cat in categories:
        time.sleep(0.3)
        d = fetch(f'https://www.workingnomads.com/api/exposed_jobs/?category={cat}&limit=50')
        if d:
            for j in d:
                if j.get('slug') not in seen:
                    seen.add(j.get('slug'))
                    jobs.append(normalize_workingnomads(j))

    print(f'  WorkingNomads: {len(jobs)} jobs')
    return jobs


def normalize_workingnomads(j):
    uid = j.get('url', j.get('title',''))
    return {
        'id': f'wn-{abs(hash(uid))}',
        'source': 'WorkingNomads',
        'title': j.get('title', ''),
        'company': j.get('company_name', ''),
        'logo': '',
        'location': j.get('location') or 'Worldwide',
        'type': '',
        'level': '',
        'industry': j.get('category_name', ''),
        'salary_min': None,
        'salary_max': None,
        'salary_currency': 'USD',
        'excerpt': (j.get('description') or '')[:300],
        'url': j.get('url', ''),
        'remote': True,
        'date': j.get('pub_date', ''),
        'tags': j.get('tags', []),
    }


def scrape_himalayas():
    """Himalayas — free public API"""
    jobs = []
    seen = set()
    for page in range(1, 6):  # 5 pages
        time.sleep(0.3)
        d = fetch(f'https://himalayas.app/jobs/api?limit=50&offset={(page-1)*50}')
        if not d or not d.get('jobs'):
            break
        for j in d['jobs']:
            jid = j.get('slug', j.get('title',''))
            if jid not in seen:
                seen.add(jid)
                jobs.append({
                    'id': f'him-{jid}',
                    'source': 'Himalayas',
                    'title': j.get('title', ''),
                    'company': j.get('company', {}).get('name', '') if isinstance(j.get('company'), dict) else '',
                    'logo': j.get('company', {}).get('logo', '') if isinstance(j.get('company'), dict) else '',
                    'location': j.get('location') or 'Worldwide',
                    'type': j.get('jobType', ''),
                    'level': j.get('seniority', ''),
                    'industry': j.get('categories', [''])[0] if j.get('categories') else '',
                    'salary_min': j.get('minAnnualSalary'),
                    'salary_max': j.get('maxAnnualSalary'),
                    'salary_currency': 'USD',
                    'excerpt': (j.get('description') or '')[:300],
                    'url': f"https://himalayas.app/jobs/{jid}",
                    'remote': True,
                    'date': j.get('createdAt', ''),
                    'tags': j.get('categories', []),
                })
    print(f'  Himalayas: {len(jobs)} jobs')
    return jobs


def scrape_weworkremotely():
    """We Work Remotely — RSS feed"""
    import xml.etree.ElementTree as ET
    jobs = []
    feeds = [
        'https://weworkremotely.com/remote-jobs.rss',
        'https://weworkremotely.com/categories/remote-programming-jobs.rss',
        'https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss',
        'https://weworkremotely.com/categories/remote-design-jobs.rss',
        'https://weworkremotely.com/categories/remote-sales-jobs.rss',
        'https://weworkremotely.com/categories/remote-marketing-jobs.rss',
        'https://weworkremotely.com/categories/remote-customer-support-jobs.rss',
        'https://weworkremotely.com/categories/remote-finance-legal-jobs.rss',
        'https://weworkremotely.com/categories/remote-writing-jobs.rss',
    ]
    seen = set()
    for feed_url in feeds:
        time.sleep(0.3)
        try:
            xml = fetch_url(feed_url).decode('utf-8', errors='replace')
            root = ET.fromstring(xml)
            ns = {'content': 'http://purl.org/rss/1.0/modules/content/'}
            for item in root.iter('item'):
                title_el = item.find('title')
                link_el = item.find('link')
                pub_el = item.find('pubDate')
                desc_el = item.find('description')
                if title_el is None: continue
                raw = (title_el.text or '').split(':')
                company = raw[0].strip() if len(raw) > 1 else ''
                title = raw[-1].strip()
                url = (link_el.text or '') if link_el is not None else ''
                if url in seen: continue
                seen.add(url)
                jobs.append({
                    'id': f'wwr-{abs(hash(url))}',
                    'source': 'WeWorkRemotely',
                    'title': title,
                    'company': company,
                    'logo': '',
                    'location': 'Worldwide',
                    'type': 'Full-time',
                    'level': '',
                    'industry': feed_url.split('remote-')[1].replace('-jobs.rss','').replace('-',' ').title() if 'categories' in feed_url else '',
                    'salary_min': None,
                    'salary_max': None,
                    'salary_currency': 'USD',
                    'excerpt': (desc_el.text or '').replace('<[^>]*>', '')[:300] if desc_el is not None else '',
                    'url': url,
                    'remote': True,
                    'date': pub_el.text if pub_el is not None else '',
                    'tags': [],
                })
        except Exception as e:
            print(f'  WWR feed error: {e}')
    print(f'  WeWorkRemotely: {len(jobs)} jobs')
    return jobs


if __name__ == '__main__':
    print('🥷 JobNinja SuperSaiyan Scraper starting...')
    all_jobs = []

    print('Fetching Jobicy...')
    all_jobs += scrape_jobicy()

    print('Fetching Remotive...')
    all_jobs += scrape_remotive()

    print('Fetching Arbeitnow...')
    all_jobs += scrape_arbeitnow()

    print('Fetching RemoteOK...')
    all_jobs += scrape_remoteok()

    print('Fetching WorkingNomads...')
    all_jobs += scrape_workingnomads()

    print('Fetching Himalayas...')
    all_jobs += scrape_himalayas()

    print('Fetching WeWorkRemotely...')
    all_jobs += scrape_weworkremotely()

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
