import pickle, inspect, re
import pyeq3
import numpy

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Figure objects are used directly rather than through pyplot, which is the
# recommended way to embed matplotlib in a tkinter application
from matplotlib.figure import Figure

import tkinter as tk
from tkinter import ttk as ttk
from tkinter import messagebox as tk_mbox
import tkinter.scrolledtext as tk_stxt
import XYscrolledtext as xy_stxt
import ReportGraphs


textboxWidth = 60 # units are characters
textboxHeight = 12 # units are characters

graphWidth = 800 # units are pixels
graphHeight = 600 # units are pixels

# this is used in several reports
def DataArrayStatisticsReport(parent, titleString, tempdata):
    scrolledText = tk_stxt.ScrolledText(parent, width=textboxWidth, height=textboxHeight, wrap=tk.NONE)
    scrolledText.insert(tk.END, ReportGraphs.DataArrayStatisticsText(titleString, tempdata))
    return scrolledText


def CoefficientAndFitStatisticsText(equation):
    # returns the coefficient and fit statistics report as a string
    lines = []
    if equation.upperCoefficientBounds or equation.lowerCoefficientBounds:
        lines.append('This model has coefficient bounds. Parameter statistics may')
        lines.append('not be valid for parameter values at or near the bounds.')
        lines.append('')

    lines.append('Degress of freedom error ' + str(equation.df_e))
    lines.append('Degress of freedom regression ' + str(equation.df_r))

    for label, value in [('Root Mean Squared Error (RMSE)', equation.rmse),
                         ('R-squared', equation.r2),
                         ('R-squared adjusted', equation.r2adj),
                         ('Model F-statistic', equation.Fstat),
                         ('Model F-statistic p-value', equation.Fpv),
                         ('Model log-likelihood', equation.ll),
                         ('Model AIC', equation.aic),
                         ('Model BIC', equation.bic)]:
        if value is None:
            lines.append(label + ': n/a')
        else:
            lines.append(label + ': ' + str(value))

    lines.append('')
    lines.append("Individual Parameter Statistics:")
    designators = equation.GetCoefficientDesignators()
    for i in range(len(equation.solvedCoefficients)):
        if equation.tstat_beta is None:
            tstat = 'n/a'
        else:
            tstat = '%-.5E' %  (equation.tstat_beta[i])

        if equation.pstat_beta is None:
            pstat = 'n/a'
        else:
            pstat = '%-.5E' %  ( equation.pstat_beta[i])

        if equation.sd_beta is not None:
            lines.append("Coefficient %s = %-.16E, std error: %-.5E" % (designators[i], equation.solvedCoefficients[i], equation.sd_beta[i]))
        else:
            lines.append("Coefficient %s = %-.16E, std error: n/a" % (designators[i], equation.solvedCoefficients[i]))

        if equation.ci is None:
            ci = 'n/a'
        else:
            ci = '[%-.5E, %-.5E]' % (equation.ci[i][0], equation.ci[i][1])
        lines.append("          t-stat: %s, p-stat: %s, 95 percent confidence intervals: %s" % (tstat, pstat, ci))

    lines.append('')
    lines.append("Coefficient Covariance Matrix:")
    if equation.cov_beta is None:
        lines.append('n/a')
    else:
        for i in equation.cov_beta:
            lines.append(str(i))

    return '\n'.join(lines) + '\n'


def CoefficientAndFitStatistics(parent, equation):
    scrolledText = tk_stxt.ScrolledText(parent, width=80, height=25, wrap=tk.NONE)
    scrolledText.insert(tk.END, CoefficientAndFitStatisticsText(equation))
    return scrolledText


def CoefficientListing(parent, equation):
    scrolledText = tk_stxt.ScrolledText(parent, width=textboxWidth, height=textboxHeight, wrap=tk.NONE)
    cd = equation.GetCoefficientDesignators()
    for i in range(len(equation.solvedCoefficients)):
        scrolledText.insert(tk.END, "%s = %-.16E\n" % (cd[i], equation.solvedCoefficients[i]))

    return scrolledText


def SourceCodeReport(parent, equation, lanuageNameString):
    scrolledText = tk_stxt.ScrolledText(parent, width=textboxWidth, height=textboxHeight, wrap=tk.NONE)    
    code = eval('pyeq3.outputSourceCodeService().GetOutputSourceCode' + lanuageNameString + '(equation)')
    scrolledText.insert(tk.END, code)
    
    return scrolledText


# The graphs are drawn by ReportGraphs, which is shared with the function finder PDF
def _GraphCanvas(parent, projection=None):
    f = Figure(figsize=(graphWidth/100.0, graphHeight/100.0), dpi=100)
    canvas = FigureCanvasTkAgg(f, master=parent)
    axes = f.add_subplot(111, projection=projection)
    return f, canvas, axes


def AbsoluteErrorGraph(parent, equation):
    f, canvas, axes = _GraphCanvas(parent)
    ReportGraphs.DrawErrorGraph(axes, equation, percentFlag=False)
    canvas.draw()
    return [canvas.get_tk_widget(), f]


def PercentErrorGraph(parent, equation):
    f, canvas, axes = _GraphCanvas(parent)
    ReportGraphs.DrawErrorGraph(axes, equation, percentFlag=True)
    canvas.draw()
    return [canvas.get_tk_widget(), f]


def AbsoluteErrorHistogram(parent, equation):
    f, canvas, axes = _GraphCanvas(parent)
    ReportGraphs.DrawErrorHistogram(axes, equation, percentFlag=False)
    canvas.draw()
    return [canvas.get_tk_widget(), f]


def PercentErrorHistogram(parent, equation):
    f, canvas, axes = _GraphCanvas(parent)
    ReportGraphs.DrawErrorHistogram(axes, equation, percentFlag=True)
    canvas.draw()
    return [canvas.get_tk_widget(), f]


def ModelScatterConfidenceGraph(parent, equation, scatterplotOnlyFlag):
    f, canvas, axes = _GraphCanvas(parent)
    ReportGraphs.DrawModelScatterConfidence(axes, equation, scatterplotOnlyFlag)
    canvas.draw()
    return [canvas.get_tk_widget(), f]


def SurfacePlot(parent, equation):
    f, canvas, axes = _GraphCanvas(parent, projection='3d')
    ReportGraphs.DrawSurfacePlot(axes, equation)
    canvas.draw()
    return [canvas.get_tk_widget(), f]


def ContourPlot(parent, equation):
    f, canvas, axes = _GraphCanvas(parent)
    ReportGraphs.DrawContourPlot(axes, equation)
    canvas.draw()
    return [canvas.get_tk_widget(), f]


def ScatterPlot(parent, equation):
    f, canvas, axes = _GraphCanvas(parent, projection='3d')
    ReportGraphs.DrawScatterPlot3D(axes, equation)
    canvas.draw()
    return [canvas.get_tk_widget(), f]


def InsertEquationHTML(textWidget, html):
    # The text widget must have "sup" and "sub" tags configured.
    # html <br> tags become new line characters
    html = html.replace('<br>', '\n')

    # display pyeq3's html superscript and subscript tags
    # tkinter has no native HTML widget, and pyeq3's html is
    # simple and has no *nested* HTML tags - no recursion needed
    findIter = re.finditer(r'<su.>|</su.>', html)
    currentIndex = 0
    endingIndex = len(html)
    itemCount = 0
    for item in findIter:
        span = item.span()
        if not itemCount % 2: # text is *not* within HTML tags
            t = html[currentIndex:span[0]]
            textWidget.insert(tk.END, t)
            currentIndex = span[1] # beginning tag
        else: # text *is* within html tags
            if html[span[1]-2] == 'b': # subscript tag
                tag = 'sub'
            else: # html superscript tag
                tag = 'sup'
            t = html[currentIndex:span[1]-6]
            textWidget.insert(tk.END, t, tag)
            currentIndex = span[1] # ending tag
        itemCount += 1

    # any ending text, or if no tags were found
    if currentIndex < endingIndex:
        t = html[currentIndex:endingIndex]
        textWidget.insert(tk.END, t)


def AllEquationReport(parent, dim):
    xyscrolledText = xy_stxt.XYScrolledText(parent, width=textboxWidth, height=textboxHeight, wrap=tk.NONE)
    xyscrolledText.tag_configure("sup", offset=5) # superscript is +5 pixels
    xyscrolledText.tag_configure("sub", offset=-5) # subscript is -5 pixels
    xyscrolledText.tag_configure("bold", font='-weight bold')
    xyscrolledText.tag_configure("italic", font='-slant italic')
    
    if dim == 2:
        module = pyeq3.Models_2D
    else:
        module = pyeq3.Models_3D
     
    for submodule in inspect.getmembers(module):
        if inspect.ismodule(submodule[1]):
            for equationClass in inspect.getmembers(submodule[1]):
                if inspect.isclass(equationClass[1]):
                    for extendedVersionName in ['Default', 'Offset']:
                        
                        # if the equation *already* has an offset,
                        # do not add an offset version here
                        if (-1 != extendedVersionName.find('Offset')) and (equationClass[1].autoGenerateOffsetForm == False):
                            continue

                        equation = equationClass[1]('SSQABS', extendedVersionName)

                        equationName = equation.GetDisplayName()
                        moduleName = str(dim) + 'D ' + submodule[0]
                        
                        xyscrolledText.insert(tk.END, moduleName, 'bold')
                        xyscrolledText.insert(tk.END, '   ')
                        xyscrolledText.insert(tk.END, equationName, 'italic')
                        xyscrolledText.insert(tk.END, '   ')

                        InsertEquationHTML(xyscrolledText, equation.GetDisplayHTML())
                        xyscrolledText.insert(tk.END, '\n')
                        
    return xyscrolledText



if __name__ == "__main__":
    import FittingResultsViewer
    root = tk.Tk()
    interface = FittingResultsViewer.ResultsFrame(root, 'pickledEquationFile')
    interface.pack()
    root.title("Example tkinterFit -  Fitting Results Viewer")
    
    # manually center the application window on the user display
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2) # integer division
    y = (root.winfo_screenheight() // 2) - (height // 2) # integer division
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))        
        
    root.mainloop()
