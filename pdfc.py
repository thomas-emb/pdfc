import re, argparse, pathlib

parser = argparse.ArgumentParser(description='Process PDF formatting')
parser.add_argument('-i', '--input', required=True, type=pathlib.Path)
parser.add_argument('-o', '--output', required=True, type=pathlib.Path)
parser.add_argument('-mm', '--mm', action='store_true', help='convert mm to pt')
parser.add_argument('-c', '--clean', action='store_true', help='remove all comments')
pars = parser.parse_args()

with open(pars.input, 'r') as inp:
    pdfc =  inp.read()


comment = r"""
    \s*         # Any spaces
    (?:%.*)?    # Optionally a `%` followed by any text
    $           # End of line
"""


# Remove all commentaries
if pars.clean:
    commentary = re.compile(comment, re.MULTILINE | re.VERBOSE)
    [header, pdfc] = pdfc.split(maxsplit=1)
    [pdfc, eof_marker] = pdfc.rsplit(maxsplit=1)
    pdfc = '\n'.join([header, commentary.sub('', pdfc), eof_marker])


# Replace all ###mm with the appropriate point sizes
if pars.mm:
    mm = re.compile(r"""
        (\d+(?:\.\d*)?| # A number with integer part and optional decimal part, or
        (?:\.\d+))      # A number with a decimal part only
        mm              # Followed by `mm`
    """, re.VERBOSE)
    noComment = re.compile(r"""
        (^[^%]+)        # A line start followed by any non `%` (may be multiple lines)
        (?=%)?          # Optionally followed by a comment
    """, re.MULTILINE | re.VERBOSE)

    def seekMm(match):
        def toMm(match):
            return repr(float(match.group(1)) * 72 / 25.4)
        return mm.sub(toMm, match.group(1))
    pdfc = noComment.sub(seekMm, pdfc)


# Identify all streams and determine their lengths
length = re.compile(r"""
    (^(?:<<)?\s*        # A line may start with `<<` and any trailing spaces
    /Length)            # Followed by `/Length`, capture this (group 1) to reproduce identically after substitution
    (\s+\d*|\s*)        # Any spaces or spaces followed by a non-negative integer, capture (group 2) to replace
    ([\s\S]*?>>         # Any other text (least greedy) up until `>>`, capture (group 3) to reproduce identically after substitution
    \s*^stream$         # Any spaces followed by `stream` and end of line
    \n([\s\S]*?)(?:\n)? # Consume the newline character and as many (non greedy) lines, capture (group 4), excuding the next newline character
    ^endstream          # `endstream` on a new line
    """ + comment + ")" # Capture (group 3) all after group 2 to reproduce identically after substitution
, re.MULTILINE | re.VERBOSE)

def fillLength(match):
    return match.group(1)+' '+str(len(match.group(4)))+match.group(3)
pdfc = length.sub(fillLength, pdfc)


# Index all indirect objects to put in the cross reference
obj = re.compile(r"""
    ^\s*                # Any leading spaces on the line
    [1-9]\d*\s+         # The object number (positive) with trailing space(s)
    (?:0|[1-9]\d*)\s+   # The generation number (non-negative) with trailing space(s)
    obj                 # `obj` with any trailing spaces
    """ + comment
, re.MULTILINE | re.VERBOSE)

references = [pos.start() for pos in obj.finditer(pdfc)]


# Compile the cross refrerence set
reference_count = len(references) + 1
references = '0 ' + str(reference_count) + '\n0000000000 65535 f \n' + '\n'.join(['%010d 00000 n ' % offset for offset in references]) + '\n'


# Replace the cross reference
xref = re.compile(r"""
    (?<=^xref$\n)       # `xref` on a separate line
    (|                  # Optionally (note this does not support multiple cross-references):
    ^\d+\s+\d+$\n       # - Two numbers on a line (start and count)
    (?:^\s*\d{10}\s+\d{5}\s+[nf]\s*$\n)*) # - Any number of lines containing a 10 digit number, a 5 digit number, and an `n|f` object reference
    (?=^trailer)        # `trailer`
""", re.MULTILINE | re.VERBOSE)

pdfc = xref.sub(references, pdfc)


# Replace size in trailer
trailer = re.compile(r"""
    (^trailer                           # `trailer`
    """ + comment + r"""\n^             # Followed by any comment
    <<$\n)                              # `<<`
    ((?:(?:^\s*\/(?!Size))[^\n]*$\n)*)  # Followed by any number of keys not equal to `Size`
    (^\s*\/Size)(\s*\d*)$\n             # Followed by the `Size` key with optional number
    ((?:(?:^\s*\/(?!Size))[^\n]*$\n)*)  # Followed by any number of keys not equal to `Size`
    (?=>>)                              # `>>`
""", re.MULTILINE | re.VERBOSE)

def setLengthInTrailer(match):
    return match.group(1) + match.group(2) + match.group(3) + ' ' + str(reference_count) + '\n' + match.group(5)
pdfc = trailer.sub(setLengthInTrailer, pdfc)


# Find and replace cross-reference start in the trailer
xref_position = re.compile("^xref$", re.MULTILINE).search(pdfc).start()
pdfc = re.compile(r"""(?<=^startxref$\n^)(\d*)(?:$\n)?""", re.MULTILINE).sub(str(xref_position)+'\n', pdfc)


# Write file to disk
with open(pars.output, 'w', newline='\n') as out:
    out.write(pdfc)
