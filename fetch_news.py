#!/usr/bin/env python3
"""Coleta feeds RSS/Atom de cibersegurança e gera noticias.json (somente biblioteca padrão)."""
import json, re, sys, html, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

FEEDS = [
    ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
    ("BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
    ("SecurityWeek", "https://feeds.feedburner.com/securityweek"),
    ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
    ("CISA", "https://www.cisa.gov/cybersecurity-advisories/all.xml"),
    ("The Register", "https://www.theregister.com/security/headlines.atom"),
    ("Dark Reading", "https://www.darkreading.com/rss.xml"),
    ("Infosecurity Magazine", "https://www.infosecurity-magazine.com/rss/news/"),
    ("CERT.br", "https://www.cert.br/rss/certbr-rss.xml"),
]
DAYS, MAX_ITEMS = 7, 150

REGIONS = [
    ("América Latina", r"brazil|brasil|latin america|mexic|argentin|chile|colombia|peru\b|lgpd|cert\.br"),
    ("Ásia", r"china|chinese|north korea|lazarus|japan|india\b|taiwan|singapore|vietnam|thailand|korea|asia"),
    ("Europa", r"europe|russia|ukrain|\buk\b|britain|germany|france|italy|spain|netherlands|nato|apt29|eu\b"),
    ("América do Norte", r"\bu\.?s\.?\b|fbi|cisa|canada|american|white house|pentagon|nist"),
]
TYPES = [
    ("Ransomware", r"ransomware|extortion"),
    ("Vulnerabilidade", r"cve-|vulnerab|zero-day|0-day|patch|rce\b|flaw"),
    ("Vazamento de dados", r"breach|leak|exposed data|stolen data"),
    ("Phishing / Golpes", r"phishing|scam|fraud|smish|clickfix"),
    ("Malware / Botnet", r"malware|botnet|trojan|backdoor|infostealer|spyware"),
    ("Cripto", r"crypto|bitcoin|blockchain|defi"),
    ("Espionagem", r"\bapt\d*|espionage|state-sponsored|nation-state"),
    ("Operação policial", r"arrest|seiz|takedown|indict|sentenced|extradit"),
]

def clean(t):
    t = re.sub(r"<[^>]+>", " ", html.unescape(t or ""))
    return re.sub(r"\s+", " ", t).strip()

def parse_date(s):
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except Exception:
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

def tag(e):
    return e.tag.split("}")[-1]

def child(e, name):
    for c in e:
        if tag(c) == name:
            return c
    return None

def first(e, *names):
    for n in names:
        c = child(e, n)
        if c is not None:
            return c
    return None

def classify(text):
    low = text.lower()
    region = next((n for n, rx in REGIONS if re.search(rx, low)), "Global")
    typ = next((n for n, rx in TYPES if re.search(rx, low)), "Geral")
    if re.search(r"zero-day|0-day|actively exploited|critical|massive|largest|record", low):
        sev = "Crítica"
    elif re.search(r"ransomware|breach|exploit|rce\b|backdoor|espionage|apt\d*", low):
        sev = "Alta"
    elif re.search(r"awareness|guide|report|survey|webinar|研究", low):
        sev = "Baixa"
    else:
        sev = "Média"
    return region, typ, sev

def parse_feed(data, source):
    root = ET.fromstring(data)
    out = []
    for it in root.iter():
        if tag(it) not in ("item", "entry"):
            continue
        title = clean((child(it, "title").text if child(it, "title") is not None else ""))
        link_el = child(it, "link")
        link = ""
        if link_el is not None:
            link = (link_el.get("href") or link_el.text or "").strip()
        desc_el = first(it, "description", "summary", "content")
        desc = clean(desc_el.text if desc_el is not None else "")
        date_el = first(it, "pubDate", "published", "updated", "date")
        d = parse_date(date_el.text if date_el is not None else None)
        if not (title and link.startswith("http") and d):
            continue
        region, typ, sev = classify(title + " " + desc)
        out.append({
            "d": d.astimezone(timezone.utc).isoformat(timespec="minutes"),
            "r": region, "t": typ, "s": sev,
            "h": title, "x": (desc[:220] + "…") if len(desc) > 220 else desc,
            "f": source, "u": link,
        })
    return out

def main():
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)
    items, seen = [], set()
    for source, url in FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "cyber-monitor/1.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                got = parse_feed(r.read(), source)
            print(f"OK   {source}: {len(got)} itens")
        except Exception as e:
            print(f"FALHA {source}: {e}", file=sys.stderr)
            continue
        for n in got:
            if n["u"] in seen or datetime.fromisoformat(n["d"]) < cutoff:
                continue
            seen.add(n["u"]); items.append(n)
    items.sort(key=lambda n: n["d"], reverse=True)
    out = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "items": items[:MAX_ITEMS]}
    if not items:
        print("Nenhum item coletado; mantendo arquivo anterior.", file=sys.stderr)
        return
    with open("noticias.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"Gravado noticias.json com {len(out['items'])} itens")

if __name__ == "__main__":
    main()
