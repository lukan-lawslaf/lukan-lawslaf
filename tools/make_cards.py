"""
Renders profile/streak.svg (+ light variant) for README.md — from scratch.

Why this exists: the streak widget every profile tutorial recommends,
`streak-stats.demolab.com`, is currently returning a 2.3 KB error card for this
user, and it is instantly recognisable as template furniture besides. So we pull
the contribution calendar ourselves and draw a card that matches
assets/header.png.

Deliberately static — no CSS keyframes. An animated entrance looks nice in a
browser but holds `opacity: 0` in anything that does not run animations
(reduced-motion settings, the GitHub mobile app, feed readers, OpenGraph
screenshotters), which turns the card blank. Not worth the risk for a fade-in
nobody watches twice.

Outputs:
  profile/streak.svg        dark
  profile/streak-light.svg  light   (paired with <picture> in the README)

Run locally:
  GITHUB_TOKEN=$(gh auth token) USERNAME_OVERRIDE=lukan-lawslaf python tools/make_cards.py

In CI, .github/workflows/stats-cards.yml passes a token in GITHUB_TOKEN.
"""
import datetime as dt
import json
import os
import sys
import urllib.request

API = "https://api.github.com/graphql"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    createdAt
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

DARK = dict(bg="#0D1117", line="#1E2530", ink="#E9EEF5", dim="#6E7A8A",
            mint="#00E5A0", violet="#7C5CFF", empty="#171E27")
LIGHT = dict(bg="#FFFFFF", line="#DFE3EA", ink="#0D1117", dim="#7A8594",
             mint="#00A070", violet="#5E3EE2", empty="#E4E8EE")

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

WEEKS = 26  # width of the sparkline


# --------------------------------------------------------------------------- #
# data
# --------------------------------------------------------------------------- #
def gql(token, variables):
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-card-builder",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        body = json.load(r)
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]["user"]


def fetch_days(token, login):
    """Every contribution day since the account was created, oldest first.

    contributionsCollection accepts at most a one-year window, so page by
    calendar year and stitch the results together.
    """
    today = dt.date.today()
    probe = gql(token, {"login": login,
                        "from": f"{today.year}-01-01T00:00:00Z",
                        "to": f"{today.isoformat()}T23:59:59Z"})
    start_year = dt.datetime.fromisoformat(probe["createdAt"].replace("Z", "+00:00")).year

    days = {}
    for year in range(start_year, today.year + 1):
        to = min(dt.date(year, 12, 31), today)
        data = gql(token, {"login": login,
                           "from": f"{year}-01-01T00:00:00Z",
                           "to": f"{to.isoformat()}T23:59:59Z"})
        for week in data["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in week["contributionDays"]:
                days[d["date"]] = d["contributionCount"]

    return [(dt.date.fromisoformat(k), v) for k, v in sorted(days.items())]


def streaks(days):
    """(total, current, current_span, longest, longest_span).

    A zero on the final day does not break the current streak — the day is not
    over yet. Any earlier zero does.
    """
    total = sum(c for _, c in days)

    best = cur = 0
    best_span = cur_span = None
    for d, c in days:
        if c > 0:
            cur += 1
            cur_span = (d if cur == 1 else cur_span[0], d)
            if cur > best:
                best, best_span = cur, cur_span
        else:
            cur, cur_span = 0, None

    if cur == 0 and len(days) > 1 and days[-1][1] == 0:
        run, span = 0, None
        for d, c in days[:-1][::-1]:
            if c == 0:
                break
            run += 1
            span = (d, span[1] if span else d)
        cur, cur_span = run, span

    return total, cur, cur_span, best, best_span


def fmt_span(span):
    if not span:
        return "not today"
    f = "%b %#d" if os.name == "nt" else "%b %-d"
    a, b = span
    if a == b:
        return f"{a.strftime(f)}, {a.year}"
    if a.year == b.year:
        return f"{a.strftime(f)} – {b.strftime(f)}, {b.year}"
    return f"{a.strftime(f)}, {a.year} – {b.strftime(f)}, {b.year}"


# --------------------------------------------------------------------------- #
# drawing
# --------------------------------------------------------------------------- #
def streak_card(t, total, cur, cur_span, best, best_span, days):
    W, H = 840, 228
    busy_day, busy_n = max(days, key=lambda kv: kv[1])
    first = next((d for d, c in days if c > 0), days[0][0])

    panels = [
        ("TOTAL CONTRIBUTIONS", f"{total:,}", f"since {first.strftime('%b %Y')}", t["ink"]),
        ("CURRENT STREAK", f"{cur}", fmt_span(cur_span), t["ink"]),
        ("LONGEST STREAK", f"{best}", fmt_span(best_span), t["mint"]),
        ("BUSIEST DAY", f"{busy_n:,}", fmt_span((busy_day, busy_day)), t["ink"]),
    ]
    centres = (105, 315, 525, 735)

    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="{total:,} contributions since {first.strftime("%B %Y")}; '
        f'current streak {cur} days; longest streak {best} days; busiest day {busy_n}">',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="{t["bg"]}" stroke="{t["line"]}"/>',
        # corner ticks, echoing the banner
        f'<path d="M14 14h26M14 14v26" stroke="{t["mint"]}" stroke-width="3" fill="none" stroke-linecap="square"/>',
        f'<path d="M{W - 14} {H - 14}h-26M{W - 14} {H - 14}v-26" stroke="{t["violet"]}" stroke-width="3" '
        f'fill="none" stroke-linecap="square"/>',
        f'<defs><filter id="gl" x="-70%" y="-70%" width="240%" height="240%">'
        f'<feGaussianBlur stdDeviation="10"/></filter>'
        f'<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{t["mint"]}" stop-opacity=".95"/>'
        f'<stop offset="1" stop-color="{t["mint"]}" stop-opacity=".38"/></linearGradient></defs>',
    ]

    for x in (210, 420, 630):
        o.append(f'<line x1="{x}" y1="38" x2="{x}" y2="146" stroke="{t["line"]}"/>')

    for (label, value, sub, colour), cx in zip(panels, centres):
        if colour == t["mint"]:  # soft bloom under the highlighted figure
            o.append(f'<text x="{cx}" y="108" text-anchor="middle" filter="url(#gl)" font-family="{SANS}" '
                     f'font-size="40" font-weight="800" fill="{colour}" opacity=".5">{value}</text>')
        o.append(f'<text x="{cx}" y="60" text-anchor="middle" font-family="{MONO}" font-size="9.5" '
                 f'letter-spacing="1.5" fill="{t["dim"]}">{label}</text>')
        o.append(f'<text x="{cx}" y="108" text-anchor="middle" font-family="{SANS}" font-size="40" '
                 f'font-weight="800" fill="{colour}">{value}</text>')
        o.append(f'<text x="{cx}" y="132" text-anchor="middle" font-family="{MONO}" font-size="9.5" '
                 f'fill="{t["dim"]}">{sub}</text>')

    # --- weekly sparkline ---------------------------------------------------
    # Weekly rather than daily buckets: at this contribution volume a 70-day
    # daily strip is almost all zeroes and reads as a broken image.
    tail = days[-WEEKS * 7:]
    weeks = [sum(c for _, c in tail[i:i + 7]) for i in range(0, len(tail), 7)][-WEEKS:]
    peak = max(weeks) or 1
    bw, gap = 21, 5
    x0, base, span = 132, 204, 32

    o.append(f'<line x1="24" y1="162" x2="{W - 24}" y2="162" stroke="{t["line"]}"/>')
    o.append(f'<text x="24" y="{base - 9}" font-family="{MONO}" font-size="9" letter-spacing="1.4" '
             f'fill="{t["dim"]}">LAST {len(weeks)}</text>')
    o.append(f'<text x="24" y="{base + 2}" font-family="{MONO}" font-size="9" letter-spacing="1.4" '
             f'fill="{t["dim"]}">WEEKS</text>')
    for i, c in enumerate(weeks):
        # sqrt scale: one 63-commit week would otherwise flatten every other
        # bar into an indistinguishable 3 px stub
        h = 3 if not c else round(6 + (span - 6) * (c / peak) ** 0.5)
        o.append(f'<rect x="{x0 + i * (bw + gap)}" y="{base - h}" width="{bw}" height="{h}" rx="3" '
                 f'fill="{"url(#bar)" if c else t["empty"]}"/>')
    o.append(f'<text x="{W - 24}" y="{base - 40}" text-anchor="end" font-family="{MONO}" font-size="9" '
             f'letter-spacing="1.4" fill="{t["dim"]}">PEAK {peak}/WK</text>')
    o.append("</svg>")
    return "\n".join(o)


def main():
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    login = os.environ.get("USERNAME_OVERRIDE") or os.environ.get("USERNAME") or "lukan-lawslaf"
    if not token:
        sys.exit("GITHUB_TOKEN is required (locally: GITHUB_TOKEN=$(gh auth token))")

    days = fetch_days(token, login)
    if not days:
        sys.exit(f"no contribution data returned for {login}")
    total, cur, cur_span, best, best_span = streaks(days)
    print(f"{login}: {len(days)} days  total={total} current={cur} longest={best}")

    os.makedirs("profile", exist_ok=True)
    for suffix, theme in (("", DARK), ("-light", LIGHT)):
        path = f"profile/streak{suffix}.svg"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(streak_card(theme, total, cur, cur_span, best, best_span, days))
        print(f"  wrote {path}  {os.path.getsize(path):,} bytes")


if __name__ == "__main__":
    main()
