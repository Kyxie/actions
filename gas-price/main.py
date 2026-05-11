import os
import re
import json
import smtplib
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

try:
    from curl_cffi import requests as curl_req
    CURL_AVAILABLE = True
except ImportError:
    CURL_AVAILABLE = False
    print("curl_cffi not available — gaswizard.ca fallback disabled")

# ── Constants ─────────────────────────────────────────────────────────────────

CITYNEWS_URL = "https://toronto.citynews.ca/toronto-gta-gas-prices/"
GASWIZARD_URL = "https://gaswizard.ca/"

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

# ── Models ────────────────────────────────────────────────────────────────────

@dataclass
class User:
    name: str
    city: str
    email: str
    subscribe: bool = True

@dataclass
class DayPrice:
    label: str          # "Today", "Tomorrow", "Monday", …
    date: str           # "May 12, 2026"
    regular: str        # "152.9"
    regular_change: str = ""   # "+3¢", "-1¢", "n/c"
    premium: str = ""
    premium_change: str = ""

@dataclass
class GasReport:
    city: str
    days: list[DayPrice]
    source_url: str

# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_date(dt: datetime) -> str:
    return dt.strftime("%b %d, %Y").replace(" 0", " ")

def _today_tomorrow() -> tuple[str, str]:
    now = datetime.now()
    return _fmt_date(now), _fmt_date(now + timedelta(days=1))

# ── citynews.ca scraper ───────────────────────────────────────────────────────

def _parse_citynews(html: str) -> list[DayPrice]:
    soup = BeautifulSoup(html, "html.parser")

    # Grab the most relevant content block
    content = (
        soup.find("article")
        or soup.find(class_=re.compile(r"entry|post|article|content", re.I))
        or soup
    )
    text = content.get_text(" ", strip=True)

    today_str, tomorrow_str = _today_tomorrow()

    # ------------------------------------------------------------------
    # Extract a price (3 digits + optional decimal) near a fuel keyword.
    # Splits text into sentences and searches each sentence for a pair
    # (fuel keyword + price in the 100–250 range).
    # ------------------------------------------------------------------
    def find_price(fuel_re: str) -> str:
        for sentence in re.split(r"[.!\n]", text):
            if re.search(fuel_re, sentence, re.I):
                m = re.search(r"\b(\d{3}(?:\.\d)?)\b", sentence)
                if m and 100.0 <= float(m.group(1)) <= 250.0:
                    return m.group(1)
        return ""

    regular = find_price(r"\bregular\b")
    premium = find_price(r"\bpremium\b")

    # Fallback: pick the first plausible price in the whole text
    if not regular:
        m = re.search(r"\b(\d{3}(?:\.\d)?)\s*(?:cents?|¢)", text, re.I)
        if m and 100.0 <= float(m.group(1)) <= 250.0:
            regular = m.group(1)

    if not regular:
        return []

    # Determine if prices are for today or tomorrow
    lower = text.lower()
    is_tomorrow = bool(re.search(r"\btomorrow\b", lower[:600]))
    label = "Tomorrow" if is_tomorrow else "Today"
    date_str = tomorrow_str if is_tomorrow else today_str

    # Extract change direction  (+3¢ / -2¢)
    regular_change = ""
    up = re.search(r"(?:rise|increase|jump|up)\D{0,30}?(\d+(?:\.\d)?)\s*(?:cent|¢)", text, re.I)
    dn = re.search(r"(?:fall|drop|decrease|down)\D{0,30}?(\d+(?:\.\d)?)\s*(?:cent|¢)", text, re.I)
    if up:
        regular_change = f"+{up.group(1)}¢"
    elif dn:
        regular_change = f"-{dn.group(1)}¢"

    return [DayPrice(
        label=label,
        date=date_str,
        regular=regular,
        regular_change=regular_change,
        premium=premium,
    )]


def fetch_citynews(city: str) -> GasReport | None:
    if "toronto" not in city.lower():
        return None
    try:
        r = requests.get(CITYNEWS_URL, headers=BROWSER_HEADERS, timeout=15)
        r.raise_for_status()
        days = _parse_citynews(r.text)
        if days:
            print("  Source: citynews.ca ✓")
            return GasReport(city="Toronto (GTA)", days=days, source_url=CITYNEWS_URL)
        print("  citynews.ca: no prices found in page")
    except Exception as e:
        print(f"  citynews.ca error: {e}")
    return None

# ── gaswizard.ca scraper (curl_cffi — bypasses bot protection) ────────────────

_GASWIZARD_REGU = re.compile(
    r"Regular<\/div><div class=\"fuelprice\">(\d{3}\.\d)\s*"
    r"\(<span class=\"price-direction (?:pd-nc|pd-up|pd-down)\">(\+?\-?\d*¢|n\/c)<\/span>\)"
)
_GASWIZARD_PREM = re.compile(
    r"Premium<\/div><div class=\"fuelprice\">(\d{3}\.\d)\s*"
    r"\(<span class=\"price-direction (?:pd-nc|pd-up|pd-down)\">(\+?\-?\d*¢|n\/c)<\/span>\)"
)
_GASWIZARD_DAY  = re.compile(r"Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday")
_GASWIZARD_DATE = re.compile(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{1,2},\s\d{4}")


def fetch_gaswizard(city: str) -> GasReport | None:
    if not CURL_AVAILABLE:
        return None

    slug = city.lower().replace(" ", "-")
    url = f"{GASWIZARD_URL}{slug}"

    try:
        r = curl_req.get(url, impersonate="chrome124", timeout=20)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        print(f"  gaswizard.ca error: {e}")
        return None

    start = re.search(r'class="single-city-prices"', html)
    if not start:
        print("  gaswizard.ca: price block not found")
        return None

    snippet = html[start.start(): start.start() + 6000]
    days_found  = _GASWIZARD_DAY.findall(snippet)
    dates_found = _GASWIZARD_DATE.findall(snippet)
    regus       = _GASWIZARD_REGU.findall(snippet)
    prems       = _GASWIZARD_PREM.findall(snippet)

    if not (days_found and dates_found and regus):
        print("  gaswizard.ca: incomplete data")
        return None

    today_str, _ = _today_tomorrow()

    day_prices = []
    for day, date, regu, prem in zip(days_found, dates_found, regus, prems):
        label = day
        if date == today_str:
            label = "Today"
        day_prices.append(DayPrice(
            label=label,
            date=date,
            regular=regu[0],
            regular_change=regu[1],
            premium=prem[0],
            premium_change=prem[1],
        ))

    try:
        day_prices.sort(key=lambda d: datetime.strptime(d.date, "%b %d, %Y"))
    except ValueError:
        pass

    print("  Source: gaswizard.ca ✓")
    return GasReport(city=city.title(), days=day_prices, source_url=url)


def fetch_gas_report(city: str) -> GasReport | None:
    report = fetch_citynews(city)
    if report:
        return report
    print("  Falling back to gaswizard.ca…")
    return fetch_gaswizard(city)

# ── Email ─────────────────────────────────────────────────────────────────────

def _change_color(change: str) -> str:
    if "+" in change:
        return "#e74c3c"
    if "-" in change:
        return "#27ae60"
    return "#888888"


def _build_html(user: User, report: GasReport) -> str:
    rows_html = ""
    for dp in report.days:
        regu_change = ""
        if dp.regular_change:
            c = _change_color(dp.regular_change)
            regu_change = f' <span style="color:{c};font-size:.88em">({dp.regular_change})</span>'

        prem_cell = f"{dp.premium}¢/L" if dp.premium else "—"
        if dp.premium_change:
            c = _change_color(dp.premium_change)
            prem_cell += f' <span style="color:{c};font-size:.88em">({dp.premium_change})</span>'

        rows_html += f"""
        <tr>
          <td style="padding:10px 14px;border-bottom:1px solid #eee;color:#555;font-size:.9em">{dp.label}<br>
            <span style="font-size:.8em;color:#aaa">{dp.date}</span></td>
          <td style="padding:10px 14px;border-bottom:1px solid #eee;font-weight:700">{dp.regular}¢/L{regu_change}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #eee">{prem_cell}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:20px;background:#f4f4f4;font-family:Arial,sans-serif">
  <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:10px;
              box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden">
    <div style="background:#2c3e50;padding:20px 24px">
      <h2 style="margin:0;color:#fff;font-size:1.2em">⛽ Gas Price Update</h2>
      <p style="margin:4px 0 0;color:#bdc3c7;font-size:.85em">
        {report.city} &nbsp;·&nbsp; {datetime.now().strftime("%b %d, %Y")}
      </p>
    </div>
    <div style="padding:20px 24px">
      <p style="margin:0 0 12px;color:#333">Hi {user.name},</p>
      <table style="width:100%;border-collapse:collapse">
        <thead>
          <tr style="background:#f8f8f8">
            <th style="padding:8px 14px;text-align:left;font-size:.8em;color:#777;font-weight:600">DATE</th>
            <th style="padding:8px 14px;text-align:left;font-size:.8em;color:#777;font-weight:600">REGULAR</th>
            <th style="padding:8px 14px;text-align:left;font-size:.8em;color:#777;font-weight:600">PREMIUM</th>
          </tr>
        </thead>
        <tbody>{rows_html}
        </tbody>
      </table>
      <p style="margin:16px 0 0;font-size:.72em;color:#bbb">
        Source: <a href="{report.source_url}" style="color:#bbb">{report.source_url}</a>
      </p>
    </div>
  </div>
</body>
</html>"""


def _build_text(user: User, report: GasReport) -> str:
    lines = [
        f"Hi {user.name}, gas prices in {report.city}:",
        "─" * 44,
    ]
    for dp in report.days:
        regu = f"{dp.regular}¢/L"
        if dp.regular_change:
            regu += f" ({dp.regular_change})"
        prem = f"{dp.premium}¢/L" if dp.premium else "—"
        if dp.premium_change:
            prem += f" ({dp.premium_change})"
        lines.append(f"{dp.label} ({dp.date})")
        lines.append(f"  Regular: {regu}   Premium: {prem}")
    lines += ["─" * 44, f"Source: {report.source_url}"]
    return "\n".join(lines)


def send_email(user: User, report: GasReport):
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PASS")
    if not sender or not password:
        print("  Skipping email: SENDER_EMAIL / SENDER_PASS not set.")
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = user.email
    msg["Subject"] = f"⛽ {report.city} Gas — {datetime.now().strftime('%b %d, %Y')}"
    msg.attach(MIMEText(_build_text(user, report), "plain"))
    msg.attach(MIMEText(_build_html(user, report), "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(sender, password)
            s.send_message(msg)
        print(f"  ✅ Email sent to {user.name} ({user.email})")
    except Exception as e:
        print(f"  ❌ Email failed: {e}")

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    try:
        users = [User(**u) for u in json.loads(os.environ.get("USERS", "[]"))]
    except Exception as e:
        print(f"❌ Invalid USERS config: {e}")
        return

    if not users:
        print("No users configured.")
        return

    send = os.environ.get("ENABLE_EMAIL", "true").lower() == "true"

    for user in users:
        if not user.subscribe:
            print(f"\n[{user.name}] Skipped (subscribe=false)")
            continue

        print(f"\n[{user.name}] Fetching {user.city}…")
        report = fetch_gas_report(user.city)
        if not report:
            print("  ❌ No data available.")
            continue

        print(_build_text(user, report))

        if send:
            send_email(user, report)


if __name__ == "__main__":
    main()
