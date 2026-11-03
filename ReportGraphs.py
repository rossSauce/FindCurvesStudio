# Graph drawing and statistics shared by the individual fitting results
# viewer (IndividualReports.py) and the function finder PDF report
# (FunctionFinderPDF.py), so that both show the same information.
#
# The Draw functions draw into an existing matplotlib axes, and do not use
# tkinter, so they can be used for both on-screen and PDF graphs.

import numpy
import scipy.stats
from matplotlib import cm # to colormap 3D surfaces from blue to red


# 3D contour plot lines
numberOfContourLines = 16


def PercentErrorAvailable(equation):
    # percent error cannot be calculated if any dependent data is zero
    return equation.dataCache.DependentDataContainsZeroFlag != 1 and \
           len(getattr(equation, 'modelPercentError', [])) > 0


def DataArrayStatistics(data):
    # returns a list of [name, value] pairs, where value is None if it
    # could not be calculated, or [] if all data has the same value
    minData = min(data)
    maxData = max(data)
    if maxData == minData:
        return []
    statistics = [['max', maxData], ['min', minData]]
    for name, function in [['mean', numpy.mean],
                           ['standard error of mean', scipy.stats.sem],
                           ['median', numpy.median],
                           ['variance', numpy.var],
                           ['std. deviation', numpy.std],
                           ['skew', scipy.stats.skew],
                           ['kurtosis', scipy.stats.kurtosis]]:
        try:
            statistics.append([name, float(function(data))])
        except Exception:
            statistics.append([name, None])
    return statistics


def DataArrayStatisticsText(titleString, data):
    lines = [titleString, '']
    statistics = DataArrayStatistics(data)
    if not statistics:
        lines.append('All data has the same value,')
        lines.append("value = %-.16E" % (min(data)))
        lines.append('statistics cannot be calculated.')
    else:
        for name, value in statistics:
            if value is None:
                lines.append(name + ' gave error in calculation')
            else:
                lines.append("%s = %-.16E" % (name, value))
    return '\n'.join(lines) + '\n'


def _ModelGrid3D(equation, x_data, y_data):
    xModel = numpy.linspace(min(x_data), max(x_data), 20)
    yModel = numpy.linspace(min(y_data), max(y_data), 20)
    X, Y = numpy.meshgrid(xModel, yModel)
    Z = equation.CalculateModelPredictionsFromNewData(numpy.array([X, Y]))
    return X, Y, Z


def DrawModelScatterConfidence(axes, equation, scatterplotOnlyFlag, markersize=None):
    y_data = equation.dataCache.allDataCacheDictionary['DependentData']
    x_data = equation.dataCache.allDataCacheDictionary['IndependentData'][0]

    # first the raw data as a scatter plot
    axes.plot(x_data, y_data,  'D', markersize=markersize)

    if not scatterplotOnlyFlag:
        # create data for the fitted equation plot
        xModel = numpy.linspace(min(x_data), max(x_data))
        yModel = equation.CalculateModelPredictionsFromNewData(xModel)

        # now the model as a line plot
        axes.plot(xModel, yModel)

        # now calculate confidence intervals
        # http://support.sas.com/documentation/cdl/en/statug/63347/HTML/default/viewer.htm#statug_nlin_sect026.htm
        # http://www.staff.ncl.ac.uk/tom.holderness/software/pythonlinearfit
        try:
            mean_x = numpy.mean(x_data)
            n = equation.nobs

            t_value = scipy.stats.t.ppf(0.975, equation.df_e) # (1.0 - (a/2)) is used for two-sided t-test critical value, here a = 0.05

            confs = t_value * numpy.sqrt((equation.sumOfSquaredErrors/equation.df_e)*(1.0/n + (numpy.power((xModel-mean_x),2.0)/
                                                                                               ((numpy.sum(numpy.power(x_data,2.0)))-n*(numpy.power(mean_x,2.0))))))

            # get lower and upper confidence limits based on predicted y and confidence intervals
            upper = yModel + abs(confs)
            lower = yModel - abs(confs)

            # mask off any numbers outside the existing plot limits
            booleanMask = yModel > axes.get_ylim()[0]
            booleanMask &= (yModel < axes.get_ylim()[1])

            # color scheme improves visibility on black background lines or points
            axes.plot(xModel[booleanMask], lower[booleanMask], linestyle='solid', color='white')
            axes.plot(xModel[booleanMask], upper[booleanMask], linestyle='solid', color='white')
            axes.plot(xModel[booleanMask], lower[booleanMask], linestyle='dashed', color='blue')
            axes.plot(xModel[booleanMask], upper[booleanMask], linestyle='dashed', color='blue')
        except Exception:
            pass # confidence intervals are not available for this fit

    if not scatterplotOnlyFlag:
        axes.set_title('Model With 95% Confidence Intervals') # add a title
    else:
        axes.set_title('Scatter Plot') # add a title
    axes.set_xlabel('X Data') # X axis data label
    axes.set_ylabel('Y Data') # Y axis data label


def DrawSurfacePlot(axes3D, equation, title='Surface Plot (click-drag with mouse)', markersize=None):
    axes3D.grid(True)
    x_data = equation.dataCache.allDataCacheDictionary['IndependentData'][0]
    y_data = equation.dataCache.allDataCacheDictionary['IndependentData'][1]
    z_data = equation.dataCache.allDataCacheDictionary['DependentData']

    X, Y, Z = _ModelGrid3D(equation, x_data, y_data)
    axes3D.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm, linewidth=1, antialiased=True, alpha=0.75)
    if markersize is None:
        axes3D.scatter(x_data, y_data, z_data, depthshade=False, color='k')
    else:
        axes3D.scatter(x_data, y_data, z_data, depthshade=False, color='k', s=markersize)

    axes3D.set_title(title) # add a title for surface plot
    axes3D.set_xlabel('X Data') # X axis data label
    axes3D.set_ylabel('Y Data') # Y axis data label
    axes3D.set_zlabel('Z Data') # Z axis data label


def DrawContourPlot(axes, equation, labelFontSize=10, markersize=None):
    x_data = equation.dataCache.allDataCacheDictionary['IndependentData'][0]
    y_data = equation.dataCache.allDataCacheDictionary['IndependentData'][1]

    X, Y, Z = _ModelGrid3D(equation, x_data, y_data)
    axes.plot(x_data, y_data, 'o', markersize=markersize)

    axes.set_title('Contour Plot') # add a title for contour plot
    axes.set_xlabel('X Data') # X axis data label
    axes.set_ylabel('Y Data') # Y axis data label

    if numpy.all(numpy.isfinite(Z)) and numpy.ptp(Z) > 0.0:
        CS = axes.contour(X, Y, Z, numberOfContourLines, colors='k')
        axes.clabel(CS, inline=True, fontsize=labelFontSize) # labels for contours


def DrawScatterPlot3D(axes3D, equation):
    axes3D.grid(True)
    x_data = equation.dataCache.allDataCacheDictionary['IndependentData'][0]
    y_data = equation.dataCache.allDataCacheDictionary['IndependentData'][1]
    z_data = equation.dataCache.allDataCacheDictionary['DependentData']

    axes3D.scatter(x_data, y_data, z_data, depthshade=False, color='k')

    axes3D.set_title('Scatter Plot (click-drag with mouse)')
    axes3D.set_xlabel('X Data')
    axes3D.set_ylabel('Y Data')
    axes3D.set_zlabel('Z Data')


def DrawErrorGraph(axes, equation, percentFlag, markersize=None):
    dep_data = equation.dataCache.allDataCacheDictionary['DependentData']
    if percentFlag:
        error, name = equation.modelPercentError, 'Percent Error'
    else:
        error, name = equation.modelAbsoluteError, 'Absolute Error'
    axes.plot(dep_data, error, 'D', markersize=markersize)

    if equation.GetDimensionality() == 2: # used for labels only
        axes.set_title(name + ' vs. X Data')
        axes.set_xlabel('X Data')
    else:
        axes.set_title(name + ' vs. Z Data')
        axes.set_xlabel('Z Data')

    axes.set_ylabel(" " + name) # Y axis label is always the error


def DrawErrorHistogram(axes, equation, percentFlag):
    if percentFlag:
        error, name = equation.modelPercentError, 'Percent Error'
    else:
        error, name = equation.modelAbsoluteError, 'Absolute Error'
    bincount = len(error)//2 # integer division
    if bincount < 5:
        bincount = 5
    if bincount > 25:
        bincount = 25
    n, bins, patches = axes.hist(error, bincount, rwidth=0.8)

    # some axis space at the top of the graph
    ylim = axes.get_ylim()
    if ylim[1] == max(n):
        axes.set_ylim(0.0, ylim[1] + 1)

    axes.set_title(name + ' Histogram') # add a title
    axes.set_xlabel(name) # X axis data label
    axes.set_ylabel(" Frequency") # Y axis label is frequency
