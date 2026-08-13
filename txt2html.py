# Initial version vibe coded

import glob
import html
import re
import sys


def parse_inline(text):
    """Parses inline formatting like **bold** text to HTML standard."""
    text = html.escape(text)
    text = re.sub(r"\[([^\[\]]+)\]\(([^()]+)\)", (lambda m: f"<a href='{m.group(2)}'>{m.group(1)}</a>"), text)
    return re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)


def convert_block(lines):
    """Recursively process blocks (notes, questions, pictures, raw, chat lines)."""
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1

        if not line.strip():
            continue

        # Akuli Notes
        if line.startswith("akuli-note:"):
            note_lines = []
            while i < len(lines) and (
                lines[i].startswith("    ") or not lines[i].strip()
            ):
                note_lines.append(lines[i][4:] if len(lines[i]) >= 4 else "")
                i += 1

            print(f'<div class="akuli-note"><strong>Note from Akuli:</strong><br>')
            convert_block(note_lines)
            print("</div>")

        # Questions (Collapsible)
        elif line.startswith("question:"):
            q_title = line[9:].strip()
            q_lines = []
            while i < len(lines) and (
                lines[i].startswith("    ") or not lines[i].strip()
            ):
                q_lines.append(lines[i][4:] if len(lines[i]) >= 4 else "")
                i += 1

            print(f'<details><summary>{html.escape(q_title)}</summary><div class="question-content">')
            convert_block(q_lines)
            print('</div></details>')

        # Headings
        elif line.startswith("## "):
            print(f"<h2>{html.escape(line[3:]).strip()}</h2>")

        # Images/Pictures
        elif line.startswith("pic:"):
            img_file = ""
            img_from = ""
            while i < len(lines) and lines[i].startswith("    "):
                sub_line = lines[i].strip()
                if sub_line.startswith("file:"):
                    img_file = sub_line[5:].strip()
                elif sub_line.startswith("from:"):
                    img_from = sub_line[5:].strip()
                i += 1

            caption = (
                f"<figcaption>Photo by {img_from}</figcaption>"
                if img_from
                else ""
            )
            print(
                f'<figure class="image-box"><img src="{html.escape(img_file)}" alt="Lesson Image">{caption}</figure>'
            )

        # Raw HTML injection
        elif line.startswith("raw:"):
            while i < len(lines) and (
                lines[i].startswith("    ") or not lines[i].strip()
            ):
                print(lines[i][4:] if len(lines[i]) >= 4 else "")
                i += 1

        # IRC Chat Messages
        elif line.startswith("<"):
            match = re.match(r"^<([^>]+)>\s*(.*)$", line)
            assert match
            author, msg = match.groups()
            escaped_msg = html.escape(msg)
            print(
                f'<div class="chat-msg"><span class="author {author.lower()}">{html.escape(author)}</span> {escaped_msg}</div>'
            )

        # Lesson List
        elif line.strip() == "lesson-list":
            print("<ol>")
            for subfolder in sorted(glob.glob("[0-9][0-9]"), key=int):
                with open(f"{subfolder}/index.txt", "r") as file:
                    title = file.readline().replace("title:", "", 1).strip()
                print(f'<li><a href="{subfolder}" class="lesson-list-link">{html.escape(title)}</a></li>')
            print("</ol>")

            # Make the links work without a web server when developing locally.
            # I used to always have index.html at the end but I prefer short URLs.
            print('<script>if(document.location.protocol === "file:") document.querySelectorAll("a.lesson-list-link").forEach(a => a.href += "/index.html");</script>')

        # Paragraph text
        else:
            p_lines = [line]
            while i < len(lines) and lines[i].strip():
                p_lines.append(lines[i].strip())
                i += 1
            p_text = " ".join(p_lines)
            print(f"<p>{parse_inline(p_text)}</p>")


def main():
    if len(sys.argv) > 1:
        sys.exit("Usage: python txt2html.py < input.txt > output.html")

    lines = sys.stdin.read().split("\n")

    # Parse main title
    title = "Lesson"
    if lines and lines[0].startswith("title:"):
        title = lines[0][6:].strip()
        lines = lines[1:]

    css = """
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        max-width: 800px;
        margin: 40px auto;
        padding: 0 20px;
        line-height: 1.6;
        color: #222;
        background-color: #fdfdfd;
    }
    h1 {
        border-bottom: 2px solid #eaeaea;
        padding-bottom: 10px;
    }
    h2 {
        margin-top: 40px;
        color: #111;
        border-bottom: 1px solid #eee;
        padding-bottom: 5px;
    }
    .chat-msg {
        font-family: monospace;
        background: #f8f9fa;
        padding: 4px 8px;
        border-radius: 4px;
        margin: 2px 0;
    }
    .author {
        font-weight: bold;
        margin-right: 6px;
    }
    .author.akuli { color: #d63384; }
    .author.adder { color: #0d6efd; }
    .akuli-note {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 15px;
        margin: 20px 0;
        border-radius: 0 4px 4px 0;
    }
    details {
        background: #eef2f5;
        border: 1px solid #dcdfe3;
        border-radius: 6px;
        margin: 15px 0;
        padding: 10px;
    }
    summary {
        font-weight: bold;
        cursor: pointer;
        color: #2c3e50;
    }
    .question-content {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #dcdfe3;
    }
    figure.image-box {
        margin: 20px 0;
        text-align: center;
    }
    figure.image-box img {
        max-width: 100%;
        border-radius: 6px;
        border: 1px solid #ddd;
    }
    figcaption {
        font-size: 0.85em;
        color: #666;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 20px 0;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px 12px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
    }
    """

    print(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>{css}</style>
</head>
<body>
    <h1>{html.escape(title)}</h1>
    """)

    convert_block(lines)

    print("""
</body>
</html>""")


if __name__ == "__main__":
    main()
