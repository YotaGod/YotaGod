import os
import json
import re
import urllib.request
import urllib.error

# ── Config ─────────────────────────────────────────────────────────────────────
USERNAME    = "YotaGod"
README_PATH = "README.md"
MARKER_START = "<!-- PINNED_REPOS_START -->"
MARKER_END   = "<!-- PINNED_REPOS_END -->"

# Badge colors per language
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
    """Return a shields.io badge for a given language."""
    if not lang:
        return "—"
    color, logo, text_color = LANG_META.get(lang, ("555555", lang.lower(), "white"))
    label = lang.replace(" ", "%20")
    return (
        f"![{lang}](https://img.shields.io/badge/-{label}-{color}"
        f"?logo={logo}&logoColor={text_color}&style=flat)"
    )


def graphql(query: str, token: str) -> dict:
    """Execute a GitHub GraphQL query."""
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
        raise EnvironmentError("GITHUB_TOKEN environment variable is not set.")

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

    print("⏳ Fetching pinned repos from GitHub GraphQL API...")
    result = graphql(query, token)

    if "errors" in result:
        raise RuntimeError(f"GraphQL error: {result['errors']}")

    repos = result["data"]["user"]["pinnedItems"]["nodes"]

    if not repos:
        print("⚠️  No pinned repos found. README will not be updated.")
        return

    print(f"✅ Found {len(repos)} pinned repo(s):")
    for r in repos:
        print(f"   • {r['name']}")

    # Build markdown table
    rows = [
        "| 🚀 Project | 📝 Description | 🛠 Stack |",
        "|:---|:---|:---:|",
    ]
    for repo in repos:
        name  = repo["name"]
        desc  = (repo.get("description") or "—").replace("|", "\\|")
        url   = repo["url"]
        lang  = (repo.get("primaryLanguage") or {}).get("name", "")
        badge = make_badge(lang)
        rows.append(f"| [**{name}**]({url}) | {desc} | {badge} |")

    table = "\n".join(rows)
    new_section = f"{MARKER_START}\n\n{table}\n\n{MARKER_END}"

    # Read current README
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify markers exist
    if MARKER_START not in content or MARKER_END not in content:
        raise ValueError(
            f"Markers not found in {README_PATH}.\n"
            f"Make sure both {MARKER_START!r} and {MARKER_END!r} exist."
        )

    # Replace section between markers
    pattern = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        re.DOTALL,
    )
    new_content = pattern.sub(new_section, content)

    if new_content == content:
        print("ℹ️  No changes detected. README is already up to date.")
        return

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("🎉 README.md updated successfully!")


if __name__ == "__main__":
    main()
