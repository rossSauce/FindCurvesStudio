# Creates a single PDF file containing the results for every equation
# fitted by the function finder, ranked from best to worst fit.

import io, re, time, html

import numpy
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

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


def ModelGraphPNG(equation, widthInches=6.0, heightInches=2.6):
    # returns a BytesIO containing a PNG graph of the data and fitted model
    fig = Figure(figsize=(widthInches, heightInches), dpi=110)
    FigureCanvasAgg(fig)
    axes = fig.add_subplot(111)
    data = equation.dataCache.allDataCacheDictionary
    x_data = data['IndependentData'][0]
    z_or_y_data = data['DependentData']

    if equation.GetDimensionality() == 2:
        axes.plot(x_data, z_or_y_data, 'D', markersize=4)
        ylim = axes.get_ylim()
        xModel = numpy.linspace(min(x_data), max(x_data), 200)
        try:
            yModel = equation.CalculateModelPredictionsFromNewData(xModel)
            axes.plot(xModel, yModel)
        except Exception:
            pass
        # keep the data in view if the model has extreme values
        margin = (ylim[1] - ylim[0]) * 0.25
        axes.set_ylim(ylim[0] - margin, ylim[1] + margin)
        axes.set_xlabel('X Data')
        axes.set_ylabel('Y Data')
    else:
        y_data = data['IndependentData'][1]
        axes.plot(x_data, y_data, 'o', markersize=4)
        X, Y = numpy.meshgrid(numpy.linspace(min(x_data), max(x_data), 20),
                              numpy.linspace(min(y_data), max(y_data), 20))
        try:
            Z = equation.CalculateModelPredictionsFromNewData(numpy.array([X.flatten(), Y.flatten()]))
            Z = numpy.reshape(Z, X.shape)
            if numpy.all(numpy.isfinite(Z)) and numpy.ptp(Z) > 0.0:
                CS = axes.contour(X, Y, Z, 12, colors='k', linewidths=0.75)
                axes.clabel(CS, inline=True, fontsize=7)
        except Exception:
            pass
        # small margins so that data points on the edges are fully visible
        xMargin = (max(x_data) - min(x_data)) * 0.04
        yMargin = (max(y_data) - min(y_data)) * 0.06
        axes.set_xlim(min(x_data) - xMargin, max(x_data) + xMargin)
        axes.set_ylim(min(y_data) - yMargin, max(y_data) + yMargin)
        axes.set_xlabel('X Data')
        axes.set_ylabel('Y Data')
        axes.set_title('Model contours with data points', fontsize=9)

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


def _EquationDetails(rank, equation, styles, includeGraph):
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

    if includeGraph:
        try:
            image = reportlab.platypus.Image(ModelGraphPNG(equation), width=5.0*inch, height=5.0*inch*2.6/6.0)
            image.hAlign = 'CENTER'
            elements.append(reportlab.platypus.Spacer(1, 4))
            elements.append(image)
        except Exception:
            pass

    elements.append(reportlab.platypus.Spacer(1, 14))
    return [reportlab.platypus.KeepTogether(elements)]


def CreatePDF(fileName, run, includeGraphs=True, progressCallback=None, cancelEvent=None):
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
    elements.append(reportlab.platypus.Paragraph('tkinterFit Function Finder Results', styles['Title']))
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
               ['Equations fitted', str(len(run.fitted))],
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

    # ranked summary of every fitted equation
    elements.append(reportlab.platypus.PageBreak())
    elements.append(reportlab.platypus.Paragraph('Ranked Results', styles['Heading2']))
    rows = [['Rank', 'Equation', 'Family', 'Coefs', 'Fitting Target (%s)' % run.fittingTarget, 'R-squared', 'RMSE']]
    for rank, equation in enumerate(results, 1):
        rows.append([str(rank), equation.GetDisplayName(), EquationFamily(equation),
                     str(len(equation.solvedCoefficients)), FormatNumber(equation.fittingTargetValue),
                     FormatNumber(equation.r2, '%.8f'), FormatNumber(equation.rmse, '%.5E')])
    elements.append(_Table(rows, styles, colWidths=[0.45*inch, 2.4*inch, 1.1*inch, 0.45*inch, 1.05*inch, 0.8*inch, 0.85*inch]))

    # full details of every fitted equation
    elements.append(reportlab.platypus.PageBreak())
    elements.append(reportlab.platypus.Paragraph('Equation Details', styles['Heading2']))
    for rank, equation in enumerate(results, 1):
        Progress(rank - 1, 'Preparing equation %d of %d' % (rank, len(results)))
        elements.extend(_EquationDetails(rank, equation, styles, includeGraphs))

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
                                               title='tkinterFit Function Finder Results')
    doc.build(elements, canvasmaker=NumberedCanvas)
