# PDF compiler
A simple "compiler" to do the tedious work in PDF "proto"-files:

- Fill the cross-reference table with the correct object offsets.
- Option to remove commentary, so your result looks more clean.
- Convert millimeter sizes to points.
- Fill stream lengths with the actual stream size.

What it does not do:

- Anything fancy

Why I made this:

- There are plenty of PDF libraries, but most (if not all) of them have a very convoluted interface or do not support pattern tiling.
- Note that `pdfc` doesn't support pattern tiling either, but it doesn't need to. Instead, it enables you to write PDF and takes away tedious calculations.

To test:

- `pdfc.py -i pdfc.test -o pdfc.pdf --mm -c`
- Verify `pdfc.pdf` contains valid numbers
- If desired, reduce the number of decimals in `pdfc.pdf` and run it again to update the offsets `pdfc.pf -i pdfc.pdf -o pdfc.pdf`

```usage: pdfc.py [-h] -i INPUT -o OUTPUT [-mm] [-c]

Process PDF formatting

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
  -o OUTPUT, --output OUTPUT
  -mm, --mm             convert mm to pt
  -c, --clean           remove all comments```
