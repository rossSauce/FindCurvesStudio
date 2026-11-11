# Data import support for the Import Data dialog (ImportDataDialog.py):
#
#   - reading CSV/text files and Microsoft Excel workbooks into tables
#   - extracting numeric X, Y (and Z) columns from a table
#   - loading graph images, including vector formats, for digitizing
#   - converting digitized image pixel positions to data values
#   - automatically tracing a curve of one color in a graph image
#
# This module does not use tkinter, so it can be tested on its own.

import csv, io, math, os, sys

import numpy


spreadsheetFileTypes = [('Data files', '*.csv *.txt *.tsv *.dat *.xlsx *.xlsm *.xls'),
                        ('CSV and text files', '*.csv *.txt *.tsv *.dat'),
                        ('Microsoft Excel files', '*.xlsx *.xlsm *.xls'),
                        ('All files', '*.*')]

rasterImageExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff', '.webp']
# Pillow can only render EMF and WMF files on Windows
windowsMetafileExtensions = ['.emf', '.wmf']
vectorImageExtensions = ['.svg', '.pdf'] + (windowsMetafileExtensions if sys.platform == 'win32' else [])
vectorImageFormatNames = ', '.join(e[1:].upper() for e in vectorImageExtensions)
imageFileTypes = [('Graph images', ' '.join('*' + e for e in rasterImageExtensions + vectorImageExtensions)),
                  ('Raster images', ' '.join('*' + e for e in rasterImageExtensions)),
                  ('Vector images (%s)' % vectorImageFormatNames, ' '.join('*' + e for e in vectorImageExtensions)),
                  ('All files', '*.*')]


# ---- spreadsheets ----

def ReadTables(fileName):
    # Returns an ordered dictionary of {sheet name: list of rows}, where each
    # row is a list of cell values.  CSV and text files have one sheet.
    extension = os.path.splitext(fileName)[1].lower()
    if extension in ['.xlsx', '.xlsm']:
        return _ReadXLSX(fileName)
    if extension == '.xls':
        return _ReadXLS(fileName)
    return {os.path.basename(fileName): _ReadDelimitedText(fileName)}


def _ReadDelimitedText(fileName):
    with open(fileName, 'rb') as f:
        raw = f.read()
    for encoding in ['utf-8-sig', 'cp1252', 'latin-1']:
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    sample = '\n'.join(text.splitlines()[:50])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t| ')
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = None # whitespace separated

    rows = []
    if delimiter in [None, ' ']:
        for line in text.splitlines():
            rows.append(line.split())
    else:
        for row in csv.reader(io.StringIO(text), delimiter=delimiter):
            rows.append([cell.strip() for cell in row])
    return rows


def _ReadXLSX(fileName):
    import openpyxl
    # data_only=True gives the last calculated values of formulas
    workbook = openpyxl.load_workbook(fileName, read_only=True, data_only=True)
    try:
        tables = {}
        for sheet in workbook.worksheets:
            tables[sheet.title] = [list(row) for row in sheet.iter_rows(values_only=True)]
        return tables
    finally:
        workbook.close()


def _ReadXLS(fileName):
    import xlrd
    workbook = xlrd.open_workbook(fileName, on_demand=True)
    try:
        tables = {}
        for sheet in workbook.sheets():
            tables[sheet.name] = [sheet.row_values(i) for i in range(sheet.nrows)]
        return tables
    finally:
        workbook.release_resources()


def ToFloat(cell):
    # returns the cell as a finite float, or None if it is not a number
    if cell is None or isinstance(cell, bool):
        return None
    if isinstance(cell, (int, float)):
        value = float(cell)
    else:
        text = str(cell).strip().replace('−', '-') # unicode minus sign
        if not text:
            return None
        try:
            value = float(text)
        except ValueError:
            return None
    if not math.isfinite(value):
        return None
    return value


def ColumnCount(rows):
    return max((len(r) for r in rows), default=0)


def ColumnLetter(index):
    # 0 -> A, 25 -> Z, 26 -> AA, as in spreadsheets
    letters = ''
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def LooksLikeHeader(rows):
    # True if the first row has text where later rows have numbers
    if len(rows) < 2:
        return False
    first = rows[0]
    for row in rows[1:20]:
        for i, cell in enumerate(row):
            if ToFloat(cell) is not None and i < len(first) and first[i] not in (None, '') and ToFloat(first[i]) is None:
                return True
    return False


def ColumnNames(rows, headerFlag):
    names = []
    for i in range(ColumnCount(rows)):
        name = ColumnLetter(i)
        if headerFlag and rows and i < len(rows[0]) and rows[0][i] not in (None, ''):
            name += ': ' + str(rows[0][i])
        names.append(name)
    return names


def NumericColumns(rows, headerFlag):
    # indices of columns that contain at least one number
    start = 1 if headerFlag else 0
    result = []
    for i in range(ColumnCount(rows)):
        for row in rows[start:]:
            if i < len(row) and ToFloat(row[i]) is not None:
                result.append(i)
                break
    return result


def ExtractPoints(rows, columnIndices, headerFlag):
    # Returns (points, skippedRowCount).  Rows where any selected column is
    # not a number are skipped - for example blank rows or notes.
    points = []
    skipped = 0
    start = 1 if headerFlag else 0
    for row in rows[start:]:
        values = []
        for index in columnIndices:
            values.append(ToFloat(row[index]) if index < len(row) else None)
        if None in values:
            if any(cell not in (None, '') for cell in row):
                skipped += 1
            continue
        points.append(values)
    return points, skipped


def FormatDataText(points, dim, description=''):
    # text for the data editor - the fitting code ignores non-numeric lines
    names = ['X', 'Y', 'Z'][:dim]
    lines = []
    if description:
        lines.append(description)
    lines.append('')
    # 13 characters per column so that 3D data fits the 45 character editor
    lines.append(' '.join('%13s' % n for n in names))
    for point in points:
        lines.append(' '.join('%13.10G' % v for v in point))
    return '\n'.join(lines) + '\n'


# ---- graph images ----

def LoadGraphImage(fileName, vectorScale=2.0):
    # Returns an RGB PIL image.  Vector formats are rendered at a higher
    # resolution so that points can be placed accurately.
    from PIL import Image
    extension = os.path.splitext(fileName)[1].lower()
    if extension == '.svg':
        import resvg_py
        png = resvg_py.svg_to_bytes(svg_path=fileName, dpi=96.0, zoom=int(round(vectorScale)))
        image = Image.open(io.BytesIO(bytes(png)))
    elif extension == '.pdf':
        import pypdfium2
        pdf = pypdfium2.PdfDocument(fileName)
        try:
            # first page only; 72 points per inch, render at 144 dpi or more
            image = pdf[0].render(scale=vectorScale).to_pil()
        finally:
            pdf.close()
    elif extension in windowsMetafileExtensions:
        if sys.platform != 'win32':
            raise ValueError("EMF and WMF images can only be opened on Windows. "
                             "Please convert the image to SVG, PDF or PNG.")
        image = Image.open(fileName)
        try:
            image.load(dpi=int(96 * vectorScale)) # rendering requires Windows
        except TypeError:
            image.load()
    else:
        image = Image.open(fileName)
        image.load()

    # flatten any transparency onto a white background
    if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
        image = image.convert('RGBA')
        background = Image.new('RGBA', image.size, (255, 255, 255, 255))
        image = Image.alpha_composite(background, image)
    return image.convert('RGB')


class AxisCalibration:
    # Converts an image pixel coordinate to a data value along one axis,
    # from two reference pixels with known data values.  Log axes are
    # interpolated in log10 space.

    def __init__(self):
        self.pixels = [None, None]
        self.values = [None, None]
        self.logFlag = False

    def IsComplete(self):
        return None not in self.pixels and None not in self.values

    def Check(self):
        # returns an error string, or '' if the calibration is usable
        if None in self.pixels:
            return 'both reference points must be placed on the image'
        if None in self.values:
            return 'both reference values must be entered'
        if abs(self.pixels[0] - self.pixels[1]) < 1.0:
            return 'the two reference points must be further apart'
        if self.values[0] == self.values[1]:
            return 'the two reference values must be different'
        if self.logFlag and (self.values[0] <= 0.0 or self.values[1] <= 0.0):
            return 'reference values must be greater than zero for a log scale'
        return ''

    def ToValue(self, pixel):
        p1, p2 = self.pixels
        v1, v2 = self.values
        fraction = (pixel - p1) / (p2 - p1)
        if self.logFlag:
            l1, l2 = math.log10(v1), math.log10(v2)
            return 10.0 ** (l1 + fraction * (l2 - l1))
        return v1 + fraction * (v2 - v1)


def PixelsToData(pixelPoints, xCalibration, yCalibration):
    # pixelPoints are (column, row) image positions; returns sorted [x, y] values
    points = [[xCalibration.ToValue(px), yCalibration.ToValue(py)] for px, py in pixelPoints]
    points.sort()
    return points


def PickCurveColor(image, column, row, radius=5):
    # Graph lines are often only one or two pixels wide, so a click may
    # miss the line slightly.  Returns the most colorful pixel color near
    # the click, or the darkest one if there are no colored pixels nearby
    # (for black or gray curves).
    pixels = numpy.asarray(image, dtype=numpy.int32)[:, :, :3]
    height, width = pixels.shape[:2]
    top, bottom = max(0, int(row) - radius), min(height, int(row) + radius + 1)
    left, right = max(0, int(column) - radius), min(width, int(column) + radius + 1)
    region = pixels[top:bottom, left:right].reshape(-1, 3)
    saturation = region.max(axis=1) - region.min(axis=1)
    if saturation.max() >= 60:
        color = region[int(numpy.argmax(saturation))]
    else:
        color = region[int(numpy.argmin(region.sum(axis=1)))]
    return tuple(int(c) for c in color)


def TraceCurveByColor(image, targetColor, tolerance=60, spacing=5, area=None):
    # Finds pixels whose color is within 'tolerance' of 'targetColor' and
    # returns their (column, row) positions, sampling every 'spacing'
    # columns.  In each sampled column, each separate run of matching pixels
    # gives one point at its center, and long vertical runs (steep parts of
    # the curve) give a point every 'spacing' pixels.
    # 'area' is an optional (left, top, right, bottom) pixel rectangle.
    pixels = numpy.asarray(image, dtype=numpy.float32)
    height, width = pixels.shape[:2]
    left, top, right, bottom = 0, 0, width, height
    if area is not None:
        left = max(0, int(min(area[0], area[2])))
        right = min(width, int(max(area[0], area[2])) + 1)
        top = max(0, int(min(area[1], area[3])))
        bottom = min(height, int(max(area[1], area[3])) + 1)

    region = pixels[top:bottom, left:right, :3]
    distance = numpy.sqrt(numpy.sum((region - numpy.array(targetColor[:3], dtype=numpy.float32)) ** 2, axis=2))
    mask = distance <= tolerance

    spacing = max(1, int(spacing))
    points = []
    for column in range(0, mask.shape[1], spacing):
        rows = numpy.flatnonzero(mask[:, column])
        if rows.size == 0:
            continue
        # split into runs of adjacent pixels
        breaks = numpy.flatnonzero(numpy.diff(rows) > 1)
        starts = numpy.concatenate(([rows[0]], rows[breaks + 1]))
        ends = numpy.concatenate((rows[breaks], [rows[-1]]))
        for start, end in zip(starts, ends):
            length = end - start + 1
            if length <= spacing * 2:
                centers = [(start + end) / 2.0]
            else:
                count = int(length // spacing)
                centers = list(numpy.linspace(start, end, count))
            for center in centers:
                points.append((float(left + column), float(top + center)))
    return points
