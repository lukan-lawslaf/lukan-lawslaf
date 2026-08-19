# Publishing your profile README

Everything here is local — nothing has been pushed to GitHub, and no repo has
been created. Work through this in order. **Step 3 must happen before step 4**,
or every workflow fails with `Permission to lukan-lawslaf/lukan-lawslaf.git denied`.

---

## 1. Fill in the placeholders

`README.md` has four. Find-and-replace each:

| Placeholder | Replace with | If you don't have one |
|---|---|---|
| `YOUR_LINKEDIN_SLUG` | tail of your LinkedIn URL, e.g. `nakul-falswal` | delete the whole `<a>…</a>` block |
| `YOUR_X_HANDLE` | your handle, no `@` | delete the block |
| `YOUR_DISCORD_INVITE` | a full invite URL, e.g. `https://discord.gg/abc123` | delete the block |
| `YOUR_EMAIL` | the address you want people to use | delete the block |

They're all inside the **say hi** section at the bottom. Check you got them all:

```bash
grep -n "YOUR_" README.md
```

That should print nothing when you're done.

---

## 2. Create the repository

The name **must exactly match your username** — that's what makes GitHub treat
its README as your profile — and it must be **public**.

```bash
gh repo create lukan-lawslaf/lukan-lawslaf --public --description "My GitHub profile"
```

---

## 3. Give Actions permission to push

All four workflows commit generated images back into the repo, so the default
read-only token isn't enough.

```bash
gh api --method PUT /repos/lukan-lawslaf/lukan-lawslaf/actions/permissions/workflow -F default_workflow_permissions=write -F can_approve_pull_request_reviews=false
```

<details>
<summary>Prefer clicking? Here's the UI path</summary>

Repo → **Settings** → **Actions** → **General** → *Workflow permissions* →
**Read and write permissions** → **Save**.
</details>

---

## 4. Push

```bash
git init -b main && git add . && git commit -m "feat: profile README" && git remote add origin https://github.com/lukan-lawslaf/lukan-lawslaf.git && git push -u origin main
```

---

## 5. Run the workflows once

`Stats cards` and `Snake animation` trigger on push, so they've already started.
The other two are schedule-only and need one manual kick:

```bash
gh workflow run "3D contribution graph" --repo lukan-lawslaf/lukan-lawslaf && gh workflow run "Space shooter" --repo lukan-lawslaf/lukan-lawslaf
```

Watch them:

```bash
gh run list --repo lukan-lawslaf/lukan-lawslaf --limit 8
```

Then `git pull` to bring the generated files down locally.

| Workflow | Output | README section |
|---|---|---|
| `stats-cards.yml` | `profile/stats.svg`, `profile/top-langs.svg`, `profile/streak*.svg` | *receipts* |
| `snake.yml` | pushes SVGs to the `output` branch | *my contribution graph, but as a game* |
| `profile-3d.yml` | `profile-3d-contrib/*.svg` | isometric-city collapsible |
| `space-shooter.yml` | `game.gif` | Galaga collapsible |

**Until they finish, four images will show as broken** — they're paths that don't
exist yet. Everything in `assets/` (banner, hero, rules) is already committed, so
the top of the page looks right immediately.

### Optional: count private contributions

The streak card is drawn from the contributions API using the repo's built-in
token, which only sees **public** activity. To include private commits, create a
PAT with the `read:user` scope and add it as a secret named `PROFILE_TOKEN` — the
workflow picks it up automatically:

```bash
gh secret set PROFILE_TOKEN --repo lukan-lawslaf/lukan-lawslaf
```

---

## 6. Two things to fix on your profile itself

These live in GitHub account settings, not this repo, and the CLI token here
lacks the `user` scope to change them.

**Your bio is currently just "Hello!"** — it's the line that follows your name
everywhere on GitHub. Something like:

> CS @ BML Munjal University · I build AI products, then try to break them · Currently on VibeSec

**Your timezone is set to UTC−12** — the middle of the Pacific, which makes your
"local time" read 12+ hours off. Fix both at
[github.com/settings/profile](https://github.com/settings/profile) → *Local time*
→ `(UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi`.

---

## 7. Optional polish, in priority order

1. **Pin the six featured repos.** The README highlights VibeSec, TRIP-AI,
   Novelcast, Lodestone, orbital and Echo — pin those same six so the top of your
   profile agrees with itself. Right now `Dino` and `LRS-NET` are pinned with no
   descriptions.

2. **Fix these two typos** — they show in search results and on pinned cards:
   - Novelcast — "Turn **you** Novel into living audiobook with various **charaters** voices"
   - Echo — "generate images and even **vedios**"

3. **Add descriptions to the 14 blank repos:** `LRS`, `LRS-NET`, `LRS-NET-APP`,
   `Dino`, `Novatra`, `NivritAI`, `MyPoke_website`, `Lovora-Website`,
   `Light-Pollution`, `Hermes-Agent-Server`, `Hacker-Teach`, `campusiq`,
   `CampusIQ2`, `blablabla`. One line each.

4. **Rename the trailing-dash repos.** `Lodestone-` and
   `Echo-All-in-one-Discord-bot-` both end in a stray `-`. GitHub adds redirects
   on rename, but update the two links in `README.md` if you do it.

---

## Regenerating the custom art

Three of the images are drawn by scripts in `tools/`, not fetched from a badge
service. You only need to re-run them if you change something.

```bash
python tools/make_assets.py
```

Rebuilds `assets/header.png`, `assets/header-light.png` and `assets/rule.png`.
Edit `NAME`, `ROLE`, `ORG` or the `THEMES` colours at the top of the file to
re-theme the banner. Needs Pillow (`pip install pillow`).

```bash
python tools/make_hero.py
```

Rebuilds `assets/hero.gif` and `assets/hero-light.gif` from `.assets/hero-src.gif`.
Turn `SIZE` / `STEP` down for a smaller file. The source Octocat GIF is from
[Anmol-Baranwal/Cool-GIFs-For-GitHub](https://github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub)
(originally a [myoctocat.com](https://myoctocat.com/build-your-octocat/) build);
it's processed and re-hosted here because the original is 896×896 / 95 frames /
6.1 MB, which is far too heavy to hotlink into a README.

```bash
python tools/make_social.py
```

Rebuilds `assets/social/*`. The animated social icons from
[Cool-GIFs-For-GitHub](https://github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub) are
1080×1080 canvases with a small logo in a lot of transparent padding — embedded
raw at `height="48"` you get a tiny glyph and a strangely spaced row, because the
padding still takes up layout width. This crops each one to the union of its
frames' alpha bounds and scales it down (1.2 MB hotlinked → ~435 KB local).

```bash
GITHUB_TOKEN=$(gh auth token) USERNAME_OVERRIDE=lukan-lawslaf python tools/make_cards.py
```

Rebuilds `profile/streak.svg` and `profile/streak-light.svg`. The workflow does
this for you nightly — this is just for previewing changes locally.

### Swapping pieces out

- **A different 3D style** — `profile-3d.yml` generates ten variants. The README
  uses `profile-night-rainbow.svg`; also there: `profile-green-animate.svg`,
  `profile-season-animate.svg`, `profile-night-view.svg`, `profile-gitblock.svg`.
- **Different accent colour** — everything keys off `00E5A0`. It appears in
  `tools/make_assets.py` (`MINT`), `tools/make_cards.py` (`DARK`/`LIGHT`),
  `stats-cards.yml`, `snake.yml`, and the view counter in `README.md`.
- **Trophy themes** — swap `theme=darkhub` for `onedark`, `dracula`, `gruvbox`,
  `radical`, `nord` or `algolia`.

---

## Why the design avoids the usual widgets

Three of the four services every profile-README tutorial recommends are broken
right now. Each was checked, not assumed:

| Service | State | What's used instead |
|---|---|---|
| `github-readme-stats.vercel.app` | **503 DEPLOYMENT_PAUSED**, project formally deprecated | `stats-organization/github-readme-stats-action`, rendering the same cards inside your repo |
| `github-profile-trophy.vercel.app` | **402 Payment required** | the `github-trophies.vercel.app` mirror |
| `streak-stats.demolab.com` | returns a 2.3 KB **error card** for this username | `tools/make_cards.py`, drawn from the contributions API to match the banner |
| `capsule-render.vercel.app` | up, but it's the gradient banner on ten thousand other profiles | `assets/header.png`, generated for this profile |

Only three things are still fetched live: the trophy shelf (tucked inside a
collapsible, so a bad day for it isn't visible), the view counter (which has to
be live to count), and the eight animated tech logos — those come from GitHub's
own `user-images.githubusercontent.com` CDN. Everything that carries the design —
banner, hero, divider, social icons, stats, languages, streak, snake, 3D graph,
shooter — lives in your repo.
