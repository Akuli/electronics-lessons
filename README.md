# Electronics Lessons

This is the source code for [akuli.github.io/electronics-lessons](https://akuli.github.io/electronics-lessons/),
a website that shows chat logs of me teaching electronics to my friend.
The website uses a custom file format for the website content,
and a simple Python script that converts it to HTML.

If you are on linux, you almost certainly don't need to install any dependencies to build or develop this project.

Building:

```
$ ./build.sh
```

Then open `index.html` in your web browser. There's no need to run a HTTP server on localhost.

To deploy, simply push to the main branch.

You can run `./prod-diff.sh` to compare build results to what's actually on GitHub Pages.
This is useful if you have refactored the Python script,
and you want to know whether it still produces the same HTML output as before.


## File Structure

The most important files are:
- `index.txt` and `index.html`: root landing page, list of lessons
- `01`, `02` etc: lessons, one subfolder per lesson
- `txt2html.py`: Python script to convert from custom text file format to HTML
- `build.sh`: defines how to run `txt2html.py` to build each page
- `.github/workflows/deploy.yml`: GitHub Actions configuration to build and deploy by pushing to main branch

All `.html` files are generated from the corresponding `.txt` files.
They should not be committed to git, and they will be overwritten by the next build.

Each `.html` file is self-contained.
For example, all CSS is baked in, not distributed as a separate `.css` file.
This makes the `.html` files slightly bigger, but also easier to reason about.
