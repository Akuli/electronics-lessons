#!/bin/bash
set -ex -o pipefail

python3 txt2html.py --no-nav < index.txt > index.html
python3 txt2html.py < cheat-sheet.txt > cheat-sheet.html

for index_txt in ??/index.txt; do
    (cd $(dirname $index_txt) && python3 ../txt2html.py < index.txt > index.html)
done
