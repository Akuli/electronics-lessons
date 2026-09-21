# Initial version vibe coded

import argparse
import os
import glob
import html
import re
import sys


def read_title(filename):
    with open(filename, "r") as file:
        return file.readline().replace("title:", "", 1).strip()


def parse_inline(text):
    """Parses inline formatting like **bold** text to HTML standard."""
    regex = r'''
        (?P<br> <br\s*/?> )
        | (?P<link> \[ [^\[\]]+ \] \( [^()]+ \) )
        | (?P<bold> \*\* .*? \*\* )
        | (?P<code> ` .+? ` )
    '''

    result = ""
    last_end = 0

    for m in re.finditer(regex, text, flags=re.VERBOSE):
        result += html.escape(text[last_end:m.start(0)])
        last_end = m.end(0)

        match_text = m.group(0)
        match m.lastgroup:
            case 'br':
                result += match_text
            case 'link':
                i = match_text.index('](')
                result += f"<a href='{match_text[i+2:-1]}'>{parse_inline(match_text[1:i])}</a>"
            case 'bold':
                result += '<strong>' + parse_inline(match_text.strip("*")) + '</strong>'
            case 'code':
                result += '<code>' + html.escape(match_text.strip('`')) + '</code>'
            case _ as regex_group_name:
                raise NotImplementedError(regex_group_name)

    result += html.escape(text[last_end:])
    return result


def read_indented_block(lines, i):
    block = []
    while i < len(lines) and (lines[i].startswith("    ") or not lines[i].strip()):
        block.append(lines[i][4:])
        i += 1
    while block and not block[-1].strip():
        block.pop()
    return block, i


def parse_table_row(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def convert_table(lines, i):
    table_lines, i = read_indented_block(lines, i)
    rows = [parse_table_row(line) for line in table_lines if line.strip()]
    assert len(rows) >= 3
    assert all(re.fullmatch(r"-{3,}", cell) for cell in rows[1])
    assert all(len(row) == len(rows[0]) for row in rows)

    print("<table>")
    print("<tr>")
    for cell in rows[0]:
        print(f"<th>{parse_inline(cell)}</th>")
    print("</tr>")
    for row in rows[2:]:
        print("<tr>")
        for cell in row:
            print(f"<td>{parse_inline(cell)}</td>")
        print("</tr>")
    print("</table>")
    return i


def convert_block(lines):
    """Recursively process blocks (notes, questions, pictures, videos, tables, raw, chat lines)."""
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1

        if not line.strip():
            continue

        # Akuli Notes
        if line.startswith("akuli-note:"):
            note_lines, i = read_indented_block(lines, i)
            print(f'<div class="akuli-note"><strong>Note from Akuli:</strong><br>')
            convert_block(note_lines)
            print("</div>")

        # Collapsible blocks
        elif line.startswith(("collapse:", "question:", "example:")):
            kind, q_title = line.split(":", maxsplit=1)
            q_lines, i = read_indented_block(lines, i)
            css_class = {"question": "question-block", "example": "example-block"}.get(kind)
            class_attr = f' class="{css_class}"' if css_class else ""
            title_prefix = "Example: " if kind == "example" else ""
            print(f'<details{class_attr}><summary>{title_prefix}{html.escape(q_title.strip())}</summary><div class="collapse-content">')
            convert_block(q_lines)
            print('</div></details>')

        # Headings
        elif line.startswith("## "):
            text = line[3:].strip()
            id = "-".join(re.findall(r"[A-Za-z0-9]+", text)).lower()
            print(f'<h2 id="{id}">{html.escape(text)}</h2>')

        # Images/Pictures
        elif line.startswith("pic:"):
            option_lines, i = read_indented_block(lines, i)
            options = dict(opt.strip().split(": ", maxsplit=1) for opt in option_lines)
            for opt in options:
                assert opt in {"file", "from", "caption-append", "max-width"}, opt

            caption = f"{options['from']} sent a picture." if "from" in options else ""
            if "caption-append" in options:
                caption += " "
                caption += parse_inline(options["caption-append"])
            if caption:
                caption = f"<figcaption>{caption}</figcaption>"
            print(
                f'<figure class="image-box"><img src="{html.escape(options["file"])}" style="max-width: {options.get("max-width", "100%")}" alt="Lesson Image">{caption}</figure>'
            )

        # Videos
        elif line.startswith("video:"):
            vid_file = ""
            vid_from = ""
            vid_caption_append = ""
            vid_max_width = "100%"
            while i < len(lines) and lines[i].startswith("    "):
                sub_line = lines[i].strip()
                if sub_line.startswith("file:"):
                    vid_file = sub_line[5:].strip()
                elif sub_line.startswith("from:"):
                    vid_from = sub_line[5:].strip()
                elif sub_line.startswith("caption-append:"):
                    vid_caption_append = sub_line[15:].strip()
                elif sub_line.startswith("max-width:"):
                    vid_max_width = sub_line[10:].strip()
                else:
                    raise ValueError(sub_line)
                i += 1

            caption = f"{vid_from} sent a video." if vid_from else ""
            if vid_caption_append:
                caption += " "
                caption += parse_inline(vid_caption_append)
            caption = caption.strip()
            if caption:
                caption = f"<figcaption>{caption}</figcaption>"
            print(
                f'<figure class="video-box"><video src="{html.escape(vid_file)}" style="max-width: {vid_max_width}" controls></video>{caption}</figure>'
            )

        # PDF datasheets
        elif line.startswith("datasheet:"):
            option_lines, i = read_indented_block(lines, i)
            options = dict(opt.strip().split(": ", maxsplit=1) for opt in option_lines)
            for opt in options:
                assert opt in {"file", "from", "caption-append"}, opt

            escaped_file = html.escape(options["file"])
            download_link = f'<a href="{escaped_file}" target="_blank" rel="noopener noreferrer">Click here to open the datasheet.</a>'

            caption_parts = []
            if "from" in options:
                caption_parts.append(f"{options['from']} shared a PDF datasheet.")
            if "caption-append" in options:
                caption_parts.append(parse_inline(options["caption-append"]))
            
            caption_parts.append(f"{download_link}")
            caption = f"<figcaption>{' '.join(caption_parts)}</figcaption>"

            print(
                f'<figure class="pdf-box">'
                f'<object data="{escaped_file}" type="application/pdf" width="100%" height="600px"></object>'
                f'{caption}'
                f'</figure>'
            )

        # Comment/ignore
        elif line.startswith("comment:"):
            _, i = read_indented_block(lines, i)

        # Tables
        elif line.startswith("table:"):
            i = convert_table(lines, i)

        # Raw HTML injection
        elif line.startswith("raw:"):
            raw_lines, i = read_indented_block(lines, i)
            for raw_line in raw_lines:
                print(raw_line)

        # Lists
        elif line.startswith("- "):
            print("<ul>")
            print(f"<li>{parse_inline(line[2:])}</li>")
            while i < len(lines) and lines[i].startswith("- "):
                print(f"<li>{parse_inline(lines[i][2:])}</li>")
                i += 1
            print("</ul>")

        # IRC Chat Messages
        elif line.startswith("<"):
            match = re.match(r"^<([^>]+)> (.*)$", line)
            assert match
            author, msg = match.groups()
            escaped_msg = html.escape(msg)
            print(
                f'<div class="chat-msg"><span class="author {author.lower()}">{html.escape(author)}</span> {escaped_msg}</div>'
            )

        # Lesson List
        elif line.strip() == "lesson-list":
            print("<ol>")
            for index_txt in sorted(glob.glob("[0-9][0-9]/index.txt")):
                subfolder = os.path.dirname(index_txt)
                print(f'<li><a href="{subfolder}" class="lesson-list-link">{html.escape(read_title(index_txt))}</a></li>')
            print("</ol>")

        # Paragraph text
        else:
            p_lines = [line]
            while i < len(lines) and lines[i].strip():
                p_lines.append(lines[i].strip())
                i += 1
            p_text = " ".join(p_lines)
            print(f"<p>{parse_inline(p_text)}</p>")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-nav", action="store_true", help="disable navigation buttons")
    args = parser.parse_args()

    lines = sys.stdin.read().split("\n")

    # Parse main title
    title = "Lesson"
    if lines and lines[0].startswith("title:"):
        title = lines[0].split(":", maxsplit=1)[1].strip()
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
    .site-nav {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px 16px;
        margin: -2px 0 28px;
        padding: 10px 14px;
        font-size: 0.95em;
        background: #f1f6fb;
        border: 1px solid #d6e2ee;
        border-radius: 6px;
    }
    .site-nav a {
        display: inline-block;
        padding: 4px 10px;
        color: #0d6efd;
        font-weight: normal;
        text-decoration: none;
        background: #fff;
        border: 1px solid #c7d7e6;
        border-radius: 4px;
    }
    .site-nav a:hover {
        background: #e8f1f9;
        text-decoration: underline;
    }
    h2 {
        margin-top: 40px;
        color: #111;
        border-bottom: 1px solid #eee;
        padding-bottom: 5px;
    }
    .chat-msg {
        font-family: monospace;
        white-space: pre-wrap;  /* for ASCII art drawings */
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
    details.example-block {
        background: #eef6ef;
        border-color: #c7dcc9;
    }
    details.example-block summary {
        color: #315b39;
    }
    details.question-block {
        background: #e5f0fa;
        border-color: #a9c8e3;
    }
    details.question-block summary {
        color: #18527d;
    }
    summary {
        font-weight: bold;
        cursor: pointer;
        color: #2c3e50;
    }
    .collapse-content {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #dcdfe3;
    }
    figure.image-box, figure.video-box {
        margin: 20px 0;
        text-align: center;
    }
    figure.image-box img, figure.video-box video {
        max-width: 100%;
        border-radius: 6px;
        border: 1px solid #ddd;
    }
    figcaption {
        font-size: 0.85em;
        color: #666;
        text-align: center;
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

    js = r"""
    // During local development, add /index.html to all links that point at directories
    // Example: <a href="01">...</a> --> <a href="01/index.html">...</a>
    if (document.location.protocol === "file:") {
        document.addEventListener("DOMContentLoaded", () => {
            for (const a of document.querySelectorAll("a")) {
                try {
                    const url = new URL(a.href, window.location.href);

                    // Regex checks if the pathname ends with a 2-digit segment
                    // e.g., matches "/01" or ".../12", but not "/123" or "/page01"
                    if (/(?:^|\/)[0-9][0-9]$/.test(url.pathname)) {
                        url.pathname += "/index.html";
                    } else if (url.pathname.endsWith("/electronics-lessons/")) {
                        // navigation back to front page with the top nav bar
                        url.pathname += "index.html";
                    } else {
                        continue;
                    }

                    const old = a.href;
                    a.href = url.toString();
                    console.log(`${old} --> ${a.href}`);
                } catch(e) {
                    // Ignore invalid URLs (e.g., mailto:, javascript:, or malformed strings)
                    continue;
                }
            }
        });
    }
    """

    print(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>{css}</style>
    <script>{js}</script>
</head>
<body>
    <h1>{html.escape(title)}</h1>
    """)

    if not args.no_nav:
        print('<nav class="site-nav" aria-label="Lesson navigation">')
        try:
            n = int(os.path.basename(os.getcwd()))
        except ValueError:
            print('<a href=".">Lesson List</a>')
        else:
            print('<a href="..">Lesson List</a>')
            try:
                print(f'<a href="../{n-1 :02}">Previous: {html.escape(read_title(f"../{n-1 :02}/index.txt"))}</a>')
            except FileNotFoundError:
                pass
            try:
                print(f'<a href="../{n+1 :02}">Next: {html.escape(read_title(f"../{n+1 :02}/index.txt"))}</a>')
            except FileNotFoundError:
                pass
        print('</nav>')

    convert_block(lines)

    print("""
</body>
</html>""")


if __name__ == "__main__":
    main()
