all: 01/index.html

%/index.html: %/index.txt $(wildcard %/*.jpg)
	python3 txt2html.py $< $@
