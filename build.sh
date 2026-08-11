#!/bin/bash
set -ex -o pipefail

python3 txt2html.py < index.txt > index.html
for folder in ??/; do
    (cd $folder && python3 ../txt2html.py < index.txt > index.html)
done
