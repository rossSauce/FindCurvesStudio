# Function finder: fit the user's data to every standard pyeq3 equation
# and rank the results by the chosen fitting target.  This follows the
# approach of the zunzunsite3 function finder:
#
#   1. The data is converted once, and each equation is screened in this
#      process (coefficient count, data rejection, bad data cache values)
#   2. Equations that can use the linear solver are fitted in this
#      process, as linear fits are very fast
#   3. Nonlinear equations are fitted in parallel worker processes.  Each
#      worker receives the data cache once, and returns only the fitting
#      target value and the solved coefficients
#   4. Fit statistics are calculated in this process from those coefficients
#
# Note that on Windows the pool worker processes re-import the main script,
# so the main script must use an "if __name__ == '__main__':" guard and call
# multiprocessing.freeze_support() (see tkinterFit.py)

import inspect, multiprocessing, os, time, warnings
import numpy
import pyeq3


# these require additional user input - available in zunzunsite3 but not this project
excludedModuleNames = {
    2: ['Polyfunctional', 'Rational', 'Spline', 'UserDefinedFunction'],
    3: ['Polyfunctional', 'Spline', 'UserDefinedFunction'],
}

# default maximum number of coefficients, as on zunzunsite3
defaultMaxCoefficients = {2: 5, 3: 6}


def GetModelsModule(dim):
    if dim == 2:
        return pyeq3.Models_2D
    return pyeq3.Models_3D


def CreateEquation(dim, moduleName, className, extendedVersionName, fittingTarget):
    equationClass = getattr(getattr(GetModelsModule(dim), moduleName), className)
    return equationClass(fittingTarget, extendedVersionName)


def ConvertData(dim, textData):
    # returns a pyeq3 data cache containing the converted text data
    if dim == 2:
        equation = pyeq3.Models_2D.Polynomial.Linear('SSQABS')
    else:
        equation = pyeq3.Models_3D.Polynomial.Linear('SSQABS')
    pyeq3.dataConvertorService().ConvertAndSortColumnarASCII(textData, equation, False)
    return equation.dataCache


def CountDataPoints(dim, textData):
    return len(ConvertData(dim, textData).allDataCacheDictionary['DependentData'])


def SolveEquation(equation):
    # returns [fittingTargetValue, solvedCoefficients], or raises an exception
    equation.Solve()
    target = equation.CalculateAllDataFittingTarget(equation.solvedCoefficients)
    if not numpy.isfinite(target) or target > 1.0E290:
        raise ValueError('Fitting target could not be calculated')
    return [float(target), numpy.array(equation.solvedCoefficients, dtype=float)]


# ---- worker process functions ----

_workerDataCache = None

def _InitWorker(dataCache):
    global _workerDataCache
    _workerDataCache = dataCache
    # poor fits generate many numeric warnings, which are expected here
    warnings.simplefilter('ignore')
    numpy.seterr(all='ignore')


def _FitInWorker(task):
    dim, moduleName, className, extendedVersionName, fittingTarget = task
    key = (moduleName, className, extendedVersionName)
    try:
        equation = CreateEquation(dim, moduleName, className, extendedVersionName, fittingTarget)
        equation.dataCache = _workerDataCache
        return ('fitted', key, SolveEquation(equation))
    except Exception as e:
        return ('failed', key, str(e) or repr(e))


# ---- function finder run, used by the GUI ----

class FunctionFinderRun:
    # The GUI calls Poll() periodically, which does a little linear fitting
    # and collects any finished nonlinear results without blocking.

    def __init__(self, dim, fittingTarget, textData, maxCoefficients, exactCoefficientCount=False, processes=None):
        self.dim = dim
        self.fittingTarget = fittingTarget
        self.textData = textData
        self.maxCoefficients = maxCoefficients
        self.exactCoefficientCount = exactCoefficientCount
        self.cancelled = False

        self.fitted = []  # fitted equation objects, with statistics
        self.skipped = [] # [moduleName, displayName, reason]
        self.failed = []  # [moduleName, displayName, reason]
        self.lastName = ''

        # convert the data once, and share the data cache with every equation
        self.dataCache = ConvertData(dim, textData)
        self.dataPointCount = len(self.dataCache.allDataCacheDictionary['DependentData'])

        self.names = {}
        self.linearList = []    # equations fitted in this process
        self.nonlinearList = [] # equations fitted by worker processes
        self._ScanEquations()

        self.total = len(self.names)
        self.completed = len(self.skipped)

        self.pool = None
        self.iterator = None
        self.nonlinearRemaining = len(self.nonlinearList)
        if self.nonlinearList:
            # fit the equations with the most coefficients first, as these
            # usually take the longest - this gives better use of all CPU cores
            self.nonlinearList.sort(key=lambda item: -item[1])
            tasks = [item[0] for item in self.nonlinearList]
            if processes is None:
                # leave one CPU core free so the computer stays responsive
                processes = max(1, (os.cpu_count() or 2) - 1)
            processes = min(processes, len(tasks))
            self.pool = multiprocessing.Pool(processes, initializer=_InitWorker, initargs=(self.dataCache,))
            self.iterator = self.pool.imap_unordered(_FitInWorker, tasks, chunksize=1)


    def _ScanEquations(self):
        badCacheFlags = {} # data cache name -> True if the cache contains bad values
        for moduleName, module in inspect.getmembers(GetModelsModule(self.dim), inspect.ismodule):
            if moduleName in excludedModuleNames[self.dim]:
                continue
            for className, equationClass in inspect.getmembers(module, inspect.isclass):
                # if the equation requires special user input, exclude here
                if equationClass.userSelectablePolynomialFlag or \
                   equationClass.userCustomizablePolynomialFlag or \
                   equationClass.userSelectableRationalFlag:
                    continue
                for extendedVersionName in ['Default', 'Offset']:
                    # if the equation *already* has an offset, do not add an offset version here
                    if extendedVersionName == 'Offset' and equationClass.autoGenerateOffsetForm == False:
                        continue
                    try:
                        equation = equationClass(self.fittingTarget, extendedVersionName)
                    except Exception:
                        continue

                    # smoothness control: maximum or exact number of coefficients
                    coefficientCount = len(equation.GetCoefficientDesignators())
                    if self.exactCoefficientCount:
                        if coefficientCount != self.maxCoefficients:
                            continue
                    elif coefficientCount > self.maxCoefficients:
                        continue

                    key = (moduleName, className, extendedVersionName)
                    displayName = equation.GetDisplayName()
                    self.names[key] = (moduleName, displayName)

                    # require at least one degree of freedom for error, otherwise equations
                    # that can exactly interpolate the data would rank as perfect fits
                    if coefficientCount >= self.dataPointCount:
                        self.skipped.append([moduleName, displayName, 'Requires more than %d data points' % coefficientCount])
                        continue

                    # check for functions requiring non-zero or non-negative data such as 1/x, etc.
                    equation.dataCache = self.dataCache
                    if equation.ShouldDataBeRejected(equation):
                        self.skipped.append([moduleName, displayName, equation.reasonWhyDataRejected or 'Data rejected by this equation'])
                        continue

                    # see if the cache generation yielded any overly large numbers or exceptions
                    try:
                        equation.dataCache.FindOrCreateAllDataCache(equation)
                        bad = False
                        for cacheName in [i[0] for i in equation.GetDataCacheFunctions()]:
                            if cacheName not in badCacheFlags:
                                values = equation.dataCache.allDataCacheDictionary[cacheName]
                                badCacheFlags[cacheName] = not numpy.all(numpy.isfinite(values)) or numpy.max(numpy.abs(values)) >= 1.0E300
                            bad = bad or badCacheFlags[cacheName]
                    except Exception:
                        bad = True
                    if bad:
                        self.skipped.append([moduleName, displayName, 'Data values are invalid for this equation'])
                        continue

                    task = (self.dim, moduleName, className, extendedVersionName, self.fittingTarget)
                    if self.fittingTarget == 'SSQABS' and equation.CanLinearSolverBeUsedForSSQABS():
                        self.linearList.append(task)
                    else:
                        self.nonlinearList.append((task, coefficientCount))


    def _AddResult(self, key, status, data):
        moduleName, displayName = self.names[key]
        self.completed += 1
        self.lastName = moduleName + ': ' + displayName
        if status != 'fitted':
            self.failed.append([moduleName, displayName, data])
            return

        # recreate the fitted equation in this process and calculate statistics
        try:
            equation = CreateEquation(self.dim, key[0], key[1], key[2], self.fittingTarget)
            equation.dataCache = self.dataCache
            equation.solvedCoefficients = data[1]
            equation.fittingTargetValue = data[0]
            equation.dataCache.FindOrCreateAllDataCache(equation)
            equation.CalculateModelErrors(equation.solvedCoefficients, equation.dataCache.allDataCacheDictionary)
            with warnings.catch_warnings(), numpy.errstate(all='ignore'):
                warnings.simplefilter('ignore')
                try:
                    equation.CalculateCoefficientAndFitStatistics()
                except Exception:
                    # the overall fit is still usable, but parameter statistics are not
                    equation.cov_beta = None
                    equation.sd_beta = None
                    equation.tstat_beta = None
                    equation.pstat_beta = None
                    equation.ci = None
            self.fitted.append(equation)
        except Exception as e:
            self.failed.append([moduleName, displayName, str(e) or repr(e)])


    def IsDone(self):
        return self.cancelled or self.completed >= self.total


    def Poll(self, timeBudget=0.15):
        # do some work without blocking the GUI for long,
        # returns True when all equations are done
        if self.IsDone():
            self._StopPool()
            return True

        startTime = time.time()

        # collect any finished nonlinear results
        while self.nonlinearRemaining > 0:
            try:
                status, key, data = self.iterator.next(timeout=0)
            except multiprocessing.TimeoutError:
                break
            self.nonlinearRemaining -= 1
            self._AddResult(key, status, data)

        # linear fits are very fast - run these in this process
        with warnings.catch_warnings(), numpy.errstate(all='ignore'):
            warnings.simplefilter('ignore')
            while self.linearList and time.time() - startTime < timeBudget:
                task = self.linearList.pop()
                key = task[1:4]
                try:
                    equation = CreateEquation(*task)
                    equation.dataCache = self.dataCache
                    self._AddResult(key, 'fitted', SolveEquation(equation))
                except Exception as e:
                    self._AddResult(key, 'failed', str(e) or repr(e))

        if self.IsDone():
            self._StopPool()
            return True
        return False


    def _StopPool(self):
        if self.pool is not None:
            self.pool.terminate()
            self.pool = None


    def Cancel(self):
        self.cancelled = True
        self._StopPool()


    def BestSoFar(self):
        if not self.fitted:
            return None
        return min(self.fitted, key=lambda e: e.fittingTargetValue)


    def SortedResults(self):
        # best fit (lowest fitting target value) first
        return sorted(self.fitted, key=lambda e: e.fittingTargetValue)
