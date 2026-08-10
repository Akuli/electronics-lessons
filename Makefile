all: index.html 01/index.html

# TODO: how to properly depend on the images?
%.html: %.txt txt2html.py $(wildcard *.jpg */*.jpg)
	python3 txt2html.py $< $@

clean:
	rm -vf index.html [0-9][0-9]/index.html
