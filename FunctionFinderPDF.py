# Creates a single PDF file containing the results for every equation
# fitted by the function finder, ranked from best to worst fit.

import io, re, time, html

import numpy
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

import ReportGraphs
import Scripture

import pyeq3
import reportlab
import reportlab.platypus
import reportlab.lib.styles
import reportlab.lib.enums
import reportlab.lib.colors
import reportlab.lib.pagesizes
from reportlab.lib.units import inch

from pdfCode import NumberedCanvas


class PDFCancelled(Exception):
    pass


def EquationFamily(equation):
    # the pyeq3 module name, for example 'Polynomial' or 'Exponential'
    return equation.__class__.__module__.split('.')[-1]


def FormatNumber(value, formatString='%.6E'):
    if value is None:
        return 'n/a'
    try:
        if not numpy.isfinite(value):
            return 'n/a'
        return formatString % value
    except Exception:
        return 'n/a'


def EquationHTMLForPDF(equationHTML):
    # reportlab paragraphs understand <sup>, <sub> and <br/> - escape
    # everything else so that characters such as < and & display correctly
    text = html.escape(equationHTML, quote=False)
    text = re.sub(r'&lt;(/?)(sup|sub)&gt;', r'<\1\2>', text, flags=re.IGNORECASE)
    text = re.sub(r'&lt;br\s*/?&gt;', '<br/>', text, flags=re.IGNORECASE)
    return text


graphWidthInches = 7.0
graphRowHeightInches = 2.9


def GraphRowsPNG(equation, includeModelGraphs=True, includeErrorGraphs=False):
    # Returns a list of [BytesIO containing a PNG, height in inches], one per
    # row of up to two graphs.  These are the same graphs shown in the
    # individual fitting results viewer, drawn by the shared ReportGraphs
    # module.  Each row is a separate image so rows can flow across pages.
    rows = []
    if includeModelGraphs:
        if equation.GetDimensionality() == 2:
            rows.append([('model',)])
        else:
            rows.append([('surface',), ('contour',)])
    if includeErrorGraphs:
        rows.append([('error', False), ('histogram', False)])
        if ReportGraphs.PercentErrorAvailable(equation):
            rows.append([('error', True), ('histogram', True)])
    images = []
    for row in rows:
        images.append([_GraphRowPNG(equation, row), graphRowHeightInches])
    return images


def _GraphRowPNG(equation, row):
    with matplotlib.rc_context({'font.size': 7, 'axes.titlesize': 8}):
        fig = Figure(figsize=(graphWidthInches, graphRowHeightInches), dpi=110)
        FigureCanvasAgg(fig)
        grid = fig.add_gridspec(1, 2)
        for columnIndex, panel in enumerate(row):
            # a single graph in a row uses the full width
            location = grid[0, :] if len(row) == 1 else grid[0, columnIndex]
            kind = panel[0]
            try:
                if kind == 'model':
                    axes = fig.add_subplot(location)
                    ReportGraphs.DrawModelScatterConfidence(axes, equation, False, markersize=4)
                elif kind == 'surface':
                    axes = fig.add_subplot(location, projection='3d')
                    ReportGraphs.DrawSurfacePlot(axes, equation, title='Surface Plot', markersize=8)
                elif kind == 'contour':
                    axes = fig.add_subplot(location)
                    ReportGraphs.DrawContourPlot(axes, equation, labelFontSize=6, markersize=4)
                elif kind == 'error':
                    axes = fig.add_subplot(location)
                    ReportGraphs.DrawErrorGraph(axes, equation, panel[1], markersize=4)
                elif kind == 'histogram':
                    axes = fig.add_subplot(location)
                    ReportGraphs.DrawErrorHistogram(axes, equation, panel[1])
            except Exception:
                pass # leave this graph empty rather than losing the whole report
        fig.tight_layout()
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png')
    buffer.seek(0)
    return buffer


def _Styles():
    styles = reportlab.lib.styles.getSampleStyleSheet()
    ParagraphStyle = reportlab.lib.styles.ParagraphStyle
    styles.add(ParagraphStyle(name='CenteredBodyText', parent=styles['BodyText'], alignment=reportlab.lib.enums.TA_CENTER))
    styles.add(ParagraphStyle(name='Cell', parent=styles['BodyText'], fontSize=7, leading=8.5))
    styles.add(ParagraphStyle(name='HeaderCell', parent=styles['BodyText'], fontSize=7, leading=8.5, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='EquationHeading', parent=styles['Heading3'], spaceBefore=6, spaceAfter=2))
    styles.add(ParagraphStyle(name='Formula', parent=styles['BodyText'], fontSize=9, leading=13, leftIndent=12, spaceAfter=4))
    styles.add(ParagraphStyle(name='SmallCode', parent=styles['Code'], fontSize=5.8, leading=6.6, leftIndent=0, spaceBefore=2))
    styles.add(ParagraphStyle(name='SourceCodeHeading', parent=styles['Heading4'], fontSize=9, spaceBefore=4, spaceAfter=4))
    return styles


def _Table(rows, styles, colWidths=None, header=True):
    # wrap every cell in a paragraph so long text wraps within its column
    cellRows = []
    for rowIndex, row in enumerate(rows):
        style = styles['HeaderCell'] if (header and rowIndex == 0) else styles['Cell']
        cellRows.append([reportlab.platypus.Paragraph(html.escape(str(cell), quote=False), style) for cell in row])
    table = reportlab.platypus.Table(cellRows, colWidths=colWidths, repeatRows=1 if header else 0, hAlign='LEFT')
    tableStyle = [('GRID', (0, 0), (-1, -1), 0.25, reportlab.lib.colors.grey),
                  ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                  ('TOPPADDING', (0, 0), (-1, -1), 1.5),
                  ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5)]
    if header:
        tableStyle.append(('BACKGROUND', (0, 0), (-1, 0), reportlab.lib.colors.HexColor('#E4E8EE')))
    table.setStyle(reportlab.platypus.TableStyle(tableStyle))
    return table


def _EquationDetails(rank, equation, styles, includeModelGraphs, includeErrorGraphs):
    elements = []
    elements.append(reportlab.platypus.Paragraph(
        'Rank %d: %s' % (rank, html.escape(equation.GetDisplayName())), styles['EquationHeading']))
    elements.append(reportlab.platypus.Paragraph(
        '%dD %s &nbsp;&nbsp;&nbsp; Fitting target (%s): %s' % (
            equation.GetDimensionality(), html.escape(EquationFamily(equation)),
            equation.fittingTarget, FormatNumber(equation.fittingTargetValue, '%.10E')),
        styles['BodyText']))
    elements.append(reportlab.platypus.Paragraph(EquationHTMLForPDF(equation.GetDisplayHTML()), styles['Formula']))

    rows = [['Coefficient', 'Value', 'Std Error', 't-stat', 'p-value', '95% Confidence Interval']]
    designators = equation.GetCoefficientDesignators()
    for i in range(len(equation.solvedCoefficients)):
        sd = None if equation.sd_beta is None else equation.sd_beta[i]
        t = None if equation.tstat_beta is None else equation.tstat_beta[i]
        p = None if equation.pstat_beta is None else equation.pstat_beta[i]
        if equation.ci is None:
            ci = 'n/a'
        else:
            ci = '[%s, %s]' % (FormatNumber(equation.ci[i][0], '%.5E'), FormatNumber(equation.ci[i][1], '%.5E'))
        rows.append([designators[i], FormatNumber(equation.solvedCoefficients[i], '%.16E'),
                     FormatNumber(sd, '%.5E'), FormatNumber(t, '%.5E'), FormatNumber(p, '%.5E'), ci])
    elements.append(_Table(rows, styles, colWidths=[0.75*inch, 1.6*inch, 0.85*inch, 0.85*inch, 0.85*inch, 2.1*inch]))
    elements.append(reportlab.platypus.Spacer(1, 4))

    stats = [['RMSE', FormatNumber(equation.rmse), 'R-squared', FormatNumber(equation.r2)],
             ['R-squared adjusted', FormatNumber(equation.r2adj), 'Model F-statistic', FormatNumber(equation.Fstat)],
             ['F-statistic p-value', FormatNumber(equation.Fpv), 'Log-likelihood', FormatNumber(equation.ll)],
             ['AIC', FormatNumber(equation.aic), 'BIC', FormatNumber(equation.bic)],
             ['Degrees of freedom error', str(equation.df_e), 'Degrees of freedom regression', str(equation.df_r)]]
    elements.append(_Table(stats, styles, colWidths=[1.5*inch, 2.0*inch, 1.6*inch, 2.0*inch], header=False))

    # coefficient covariance matrix
    if equation.cov_beta is not None:
        elements.append(reportlab.platypus.Spacer(1, 4))
        rows = [['Covariance'] + list(designators)]
        for i, row in enumerate(numpy.atleast_2d(equation.cov_beta)):
            rows.append([designators[i]] + [FormatNumber(v, '%.5E') for v in row])
        columnWidth = min(0.95*inch, 6.3*inch / len(designators))
        elements.append(_Table(rows, styles, colWidths=[0.75*inch] + [columnWidth] * len(designators)))

    # absolute and percent error statistics, as in the individual results viewer
    errorColumns = [['Absolute Error', ReportGraphs.DataArrayStatistics(equation.modelAbsoluteError)]]
    if ReportGraphs.PercentErrorAvailable(equation):
        errorColumns.append(['Percent Error', ReportGraphs.DataArrayStatistics(equation.modelPercentError)])
    elements.append(reportlab.platypus.Spacer(1, 4))
    rows = [['Error Statistics'] + [c[0] for c in errorColumns]]
    for index, name in enumerate(['max', 'min', 'mean', 'standard error of mean', 'median',
                                  'variance', 'std. deviation', 'skew', 'kurtosis']):
        row = [name]
        for columnName, statistics in errorColumns:
            if not statistics:
                row.append('all values equal' if index == 0 else '')
            else:
                row.append(FormatNumber(statistics[index][1], '%.10E'))
        rows.append(row)
    elements.append(_Table(rows, styles, colWidths=[1.6*inch] + [2.0*inch] * len(errorColumns)))

    images = []
    if includeModelGraphs or includeErrorGraphs:
        try:
            for buffer, heightInches in GraphRowsPNG(equation, includeModelGraphs, includeErrorGraphs):
                image = reportlab.platypus.Image(buffer, width=graphWidthInches*inch, height=heightInches*inch)
                image.hAlign = 'CENTER'
                images.append(image)
        except Exception:
            pass

    # keep the tables together with the first row of graphs; any further
    # rows of graphs follow on, possibly on the next page
    if images:
        elements.append(reportlab.platypus.Spacer(1, 4))
        elements.append(images[0])
    flowables = [reportlab.platypus.KeepTogether(elements)] + images[1:]
    flowables.extend(_SourceCodeListings(rank, equation, styles))
    flowables.append(reportlab.platypus.Spacer(1, 14))
    return flowables


# the same source code languages as the individual fitting results viewer
sourceCodeLanguages = [('CPP', 'C++'), ('CSHARP', 'C#'), ('VBA', 'VBA'), ('PYTHON', 'Python'),
                       ('JAVA', 'Java'), ('JAVASCRIPT', 'JavaScript'), ('JULIA', 'Julia'),
                       ('SCILAB', 'Scilab'), ('MATLAB', 'MATLAB'), ('FORTRAN90', 'Fortran 90')]

# listings longer than this are printed full width so they can split across pages
maxSideBySideCodeLines = 100
codeColumnCharacters = 72 # 5.8 point Courier in a 3.65 inch column


def _WrapCode(code, width):
    lines = []
    for line in code.replace('\t', '    ').replace('\r\n', '\n').split('\n'):
        while len(line) > width:
            lines.append(line[:width])
            line = '    ' + line[width:] # indent continuation lines
        lines.append(line)
    while lines and not lines[-1].strip():
        lines.pop()
    return '\n'.join(lines)


def _SourceCodeListings(rank, equation, styles):
    service = pyeq3.outputSourceCodeService()
    listings = []
    for languageCode, languageName in sourceCodeLanguages:
        try:
            code = getattr(service, 'GetOutputSourceCode' + languageCode)(equation)
        except Exception as e:
            code = 'Source code could not be generated: ' + repr(e)
        listings.append([languageName, _WrapCode(code, codeColumnCharacters)])

    flowables = [reportlab.platypus.CondPageBreak(1.5*inch),
                 reportlab.platypus.Paragraph('Rank %d: %s - Source Code' % (rank, html.escape(equation.GetDisplayName())),
                                              styles['SourceCodeHeading'])]

    # pairs of listings side by side, or full width if too long for one page
    def Cell(listing):
        return [reportlab.platypus.Paragraph(listing[0], styles['HeaderCell']),
                reportlab.platypus.Preformatted(listing[1], styles['SmallCode'])]

    short = [l for l in listings if l[1].count('\n') < maxSideBySideCodeLines]
    long = [l for l in listings if l[1].count('\n') >= maxSideBySideCodeLines]
    for i in range(0, len(short), 2):
        pair = short[i:i + 2]
        row = [Cell(l) for l in pair] + ([''] if len(pair) == 1 else [])
        table = reportlab.platypus.Table([row], colWidths=[3.65*inch, 3.65*inch], hAlign='LEFT')
        table.setStyle(reportlab.platypus.TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                                      ('LEFTPADDING', (0, 0), (-1, -1), 2),
                                                      ('RIGHTPADDING', (0, 0), (-1, -1), 6)]))
        flowables.append(table)
        flowables.append(reportlab.platypus.Spacer(1, 6))
    for listing in long:
        flowables.append(reportlab.platypus.Paragraph(listing[0], styles['HeaderCell']))
        flowables.append(reportlab.platypus.Preformatted(_WrapCode(listing[1], 160), styles['SmallCode']))
        flowables.append(reportlab.platypus.Spacer(1, 6))
    return flowables


def CreatePDF(fileName, run, includeModelGraphs=True, includeErrorGraphs=False, progressCallback=None, cancelEvent=None):
    # 'run' is a completed FunctionFinder.FunctionFinderRun
    # progressCallback(completedCount, totalCount, message) is optional
    # cancelEvent is an optional threading.Event to stop PDF creation
    styles = _Styles()
    results = run.SortedResults()
    targetName = run.fittingTarget + ' - ' + pyeq3.IModel.IModel.fittingTargetDictionary[run.fittingTarget]

    def Progress(done, message):
        if cancelEvent is not None and cancelEvent.is_set():
            raise PDFCancelled()
        if progressCallback:
            progressCallback(done, len(results), message)

    elements = []
    elements.append(reportlab.platypus.Paragraph('FindCurves Studio Function Finder Results', styles['Title']))
    elements.append(reportlab.platypus.Spacer(1, 12))

    if run.cancelled:
        status = 'Cancelled by user - %d of %d equations were tested' % (run.completed, run.total)
    else:
        status = 'Complete'
    summary = [['Dimensionality', '%dD' % run.dim],
               ['Fitting target', targetName],
               ['Data points', str(run.dataPointCount)],
               ['Number of coefficients', ('exactly %d' if run.exactCoefficientCount else 'maximum of %d') % run.maxCoefficients],
               ['Equations tested', '%d of %d' % (run.completed, run.total)],
               ['Equations fitted', str(len(run.fitted)) + ('' if len(run.fitted) <= len(results) else
                                    ' (the best %d are included in this report)' % len(results))],
               ['Equations skipped (not applicable to this data)', str(len(run.skipped))],
               ['Equations that failed to fit', str(len(run.failed))],
               ['Status', status],
               ['Created', time.asctime(time.localtime())]]
    elements.append(_Table(summary, styles, colWidths=[2.6*inch, 4.4*inch], header=False))
    elements.append(reportlab.platypus.Spacer(1, 12))
    elements.append(reportlab.platypus.Paragraph(
        'Equations are ranked by their fitting target value, lowest (best) first. '
        'Equations requiring at least as many coefficients as there are data points '
        'are not fitted.', styles['BodyText']))

    # the data that was fitted
    if results:
        data = results[0].dataCache.allDataCacheDictionary
        if run.dim == 2:
            rows = [['X', 'Y']]
            columns = [data['IndependentData'][0], data['DependentData']]
        else:
            rows = [['X', 'Y', 'Z']]
            columns = [data['IndependentData'][0], data['IndependentData'][1], data['DependentData']]
        for values in zip(*columns):
            rows.append(['%.10G' % v for v in values])
        elements.append(reportlab.platypus.Spacer(1, 12))
        elements.append(reportlab.platypus.Paragraph('Data', styles['Heading2']))
        elements.append(_Table(rows, styles, colWidths=[1.3*inch] * len(rows[0])))

    # inspirational message page, then the ranked summary of every fitted equation
    elements.append(reportlab.platypus.PageBreak())
    elements.extend(Scripture.PageElements(styles['CenteredBodyText'], styles['BodyText']))
    elements.append(reportlab.platypus.Paragraph('Ranked Results', styles['Heading2']))
    rows = [['Rank', 'Equation', 'Family', 'Coefs', 'Fitting Target (%s)' % run.fittingTarget, 'R-squared', 'RMSE']]
    for rank, equation in enumerate(results, 1):
        rows.append([str(rank), equation.GetDisplayName(), EquationFamily(equation),
                     str(len(equation.solvedCoefficients)), FormatNumber(equation.fittingTargetValue),
                     FormatNumber(equation.r2, '%.8f'), FormatNumber(equation.rmse, '%.5E')])
    elements.append(_Table(rows, styles, colWidths=[0.45*inch, 2.4*inch, 1.1*inch, 0.45*inch, 1.05*inch, 0.8*inch, 0.85*inch]))

    # full details of every fitted equation
    elements.append(reportlab.platypus.PageBreak())
    for rank, equation in enumerate(results, 1):
        Progress(rank - 1, 'Preparing equation %d of %d' % (rank, len(results)))
        details = _EquationDetails(rank, equation, styles, includeModelGraphs, includeErrorGraphs)
        if rank == 1:
            # keep the section heading on the same page as the first equation
            details[0] = reportlab.platypus.KeepTogether(
                [reportlab.platypus.Paragraph('Equation Details', styles['Heading2']), details[0]])
        elements.extend(details)

    # equations that could not be fitted
    notFitted = [[m, n, 'Skipped', r] for m, n, r in run.skipped] + [[m, n, 'Failed', r] for m, n, r in run.failed]
    if notFitted:
        elements.append(reportlab.platypus.PageBreak())
        elements.append(reportlab.platypus.Paragraph('Equations Not Fitted', styles['Heading2']))
        rows = [['Family', 'Equation', 'Status', 'Reason']]
        for m, n, s, r in sorted(notFitted):
            rows.append([m, n, s, str(r)[:300]])
        elements.append(_Table(rows, styles, colWidths=[1.1*inch, 2.5*inch, 0.6*inch, 2.9*inch]))

    Progress(len(results), 'Writing PDF file...')
    doc = reportlab.platypus.SimpleDocTemplate(fileName, pagesize=reportlab.lib.pagesizes.letter,
                                               leftMargin=0.6*inch, rightMargin=0.6*inch,
                                               topMargin=0.6*inch, bottomMargin=0.9*inch,
                                               title='FindCurves Studio Function Finder Results')
    doc.build(elements, canvasmaker=NumberedCanvas)
