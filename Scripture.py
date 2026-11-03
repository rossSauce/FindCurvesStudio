# The inspirational message page included in PDF reports, as in the
# ZunZun4 site's PDF reports.  Verses.txt holds pairs of lines: a reference
# (which may be blank) followed by its message.

import os, sys, time, html

import reportlab.platypus


EXPLANATION = ('In the pursuit of knowledge, discovery, and innovation, we often find ourselves facing '
               'challenges and uncertainties. These inspirational messages are here to remind us that our '
               'journey, as scientists and engineers, is a remarkable one. They encourage us to embrace '
               'wisdom, compassion, and the pursuit of truth as we work to unravel the mysteries of the '
               'universe and shape a brighter future for all. Let them serve as a source of inspiration and '
               'guidance on our path to making a lasting impact through our contributions.')


def _VersesFile():
    # in the PyInstaller-built executable data files are in sys._MEIPASS
    folder = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(folder, 'Verses.txt')


def ReadVerses():
    # returns a list of [reference, message]
    try:
        with open(_VersesFile(), encoding='utf-8') as f:
            lines = [line.strip() for line in f.read().splitlines()]
    except OSError:
        return []
    return [[lines[i], lines[i + 1]] for i in range(0, len(lines) - 1, 2) if lines[i + 1]]


def GetVerseInfo():
    # as on ZunZun4, the message shown changes with the time of day
    verses = ReadVerses()
    if not verses:
        return None
    return verses[int(time.time()) % len(verses)]


def PageElements(centeredStyle, smallStyle):
    # flowables for the message page, ending with a page break;
    # empty if the messages are not available
    verse = GetVerseInfo()
    if verse is None:
        return []
    reference, message = verse
    elements = [reportlab.platypus.Spacer(1, 144)]
    if reference:
        elements.append(reportlab.platypus.Paragraph(html.escape(reference), centeredStyle))
        elements.append(reportlab.platypus.Spacer(1, 18))
    elements.append(reportlab.platypus.Paragraph(html.escape(message), centeredStyle))
    elements.append(reportlab.platypus.Spacer(1, 24))
    elements.append(reportlab.platypus.Paragraph(EXPLANATION, smallStyle))
    elements.append(reportlab.platypus.PageBreak())
    return elements
