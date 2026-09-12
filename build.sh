#!/bin/bash
set -ex -o pipefail

python3 txt2html.py < index.txt > index.html
for index_txt in ??/index.txt; do
    (cd $(dirname $index_txt) && python3 ../txt2html.py < index.txt > index.html)
done
