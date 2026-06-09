import os
import json
import re
import urllib.request

# ── Config ─────────────────────────────────────────────────────────────────────
USERNAME     = "YotaGod"
README_PATH  = "README.md"
MARKER_START = "<!-- PINNED_REPOS_START -->"
MARKER_END   = "<!-- PINNED_REPOS_END -->"

LANG_META = {
    "TypeScript":       ("3178C6", "typescript",   "white"),
    "JavaScript":       ("F7DF1E", "javascript",   "black"),
    "PHP":              ("777BB4", "php",           "white"),
    "Python":           ("3776AB", "python",        "white"),
    "HTML":             ("E34F26", "html5",         "white"),
    "CSS":              ("1572B6", "css3",          "white"),
    "Jupyter Notebook": ("F37626", "jupyter",       "white"),
    "Shell":            ("4EAA25", "gnubash",       "white"),
    "Go":               ("00ADD8", "go",            "white"),
    "Rust":             ("000000", "rust",          "white"),
    "Java":             ("007396", "openjdk",       "white"),
    "C++":              ("00599C", "cplusplus",     "white"),
    "C#":               ("239120", "csharp",        "white"),
    "Vue":              ("4FC08D", "vuedotjs",      "white"),
    "Svelte":           ("FF3E00", "svelte",        "white"),
    "Dart":             ("0175C2", "dart",          "white"),
    "Kotlin":           ("7F52FF", "kotlin",        "white"),
    "Swift":            ("F05138", "swift",         "white"),
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def make_badge(lang: str) -> str:
    if not lang:
        return "—"
    color, logo, text_color = LANG_META.get(lang, ("555555", lang.lower().replace(" ", ""), "white"))
    label = lang.replace(" ", "%20")
    return (
        f"![{lang}](https://img.shields.io/badge/-{label}-{color}"
        f"?logo={logo}&logoColor={text_color}&style=flat)"
    )

def graphql(query: str, token: str) -> dict:
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
            "User-Agent":    f"{USERNAME}-profile-bot",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_TOKEN is not set.")

    query = f"""
    {{
      user(login: "{USERNAME}") {{
        pinnedItems(first: 6, types: REPOSITORY) {{
          nodes {{
            ... on Repository {{
              name
              description
              url
              primaryLanguage {{ name }}
            }}
          }}
        }}
      }}
    }}
    """

    print("⏳ Fetching pinned repos...")
    result = graphql(query, token)

    if "errors" in result:
        raise RuntimeError(f"GraphQL error: {result['errors']}")

    repos = result["data"]["user"]["pinnedItems"]["nodes"]
    print(f"✅ Found {len(repos)} pinned repo(s):")
    for r in repos:
        print(f"   • {r['name']} — {r.get('description', '(no description)')}")

    if not repos:
        print("⚠️  No pinned repos. Skipping update.")
        return

    # Build markdown table
    rows = [
        "| 🚀 Project | 📝 Description | 🛠 Stack |",
        "|:---|:---|:---:|",
    ]
    for repo in repos:
        name  = repo["name"]
        raw_desc = (repo.get("description") or "—").replace("|", "\\|")
        desc  = raw_desc[:80] + "…" if len(raw_desc) > 80 else raw_desc
        url   = repo["url"]
        lang  = (repo.get("primaryLanguage") or {}).get("name", "")
        rows.append(f"| [**{name}**]({url}) | {desc} | {make_badge(lang)} |")

    table = "\n".join(rows)

    # Read README — normalize to LF so regex works regardless of OS
    with open(README_PATH, "r", encoding="utf-8") as f:
        raw = f.read()

    content = raw.replace("\r\n", "\n").replace("\r", "\n")  # normalize CRLF → LF

    # Verify markers
    if MARKER_START not in content:
        raise ValueError(f"Marker not found: {MARKER_START!r}")
    if MARKER_END not in content:
        raise ValueError(f"Marker not found: {MARKER_END!r}")

    print(f"\n📄 Current section between markers:")
    start_idx = content.index(MARKER_START) + len(MARKER_START)
    end_idx   = content.index(MARKER_END)
    print(content[start_idx:end_idx].strip())

    # Replace section
    new_section = f"{MARKER_START}\n\n{table}\n\n{MARKER_END}"
    pattern     = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        re.DOTALL,
    )
    new_content = pattern.sub(new_section, content)

    print(f"\n📝 New section to write:")
    print(new_section)

    if new_content == content:
        print("\nℹ️  Content identical — no update needed.")
    else:
        with open(README_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_content)
        print("\n🎉 README.md written successfully!")

if __name__ == "__main__":
    main()
