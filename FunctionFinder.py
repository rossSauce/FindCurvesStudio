# Function finder: fit the user's data to every selected pyeq3 equation and
# rank the results by the chosen fitting target.  This follows the approach
# of the zunzunsite3 function finder:
#
#   1. The data is converted once.  The equations to try are listed from
#      the selected options: standard forms (Default, Offset, Plus Line or
#      Plus Plane), polynomials of every order, optional extended forms
#      (Reciprocal, Inverse, Growth and Decay), and optional polyfunctional
#      and rational combinations
#   2. Every equation is screened and fitted in parallel worker processes.
#      Each worker receives the data once, and returns only the fitting
#      target value and the solved coefficients.  Fast linear fits are sent
#      in batches, slow nonlinear fits one at a time
#   3. Fit statistics are calculated in this process, only for the best
#      results (as on zunzunsite3, which kept the best 1000)
#
# Note that on Windows the pool worker processes re-import the main script,
# so the main script must use an "if __name__ == '__main__':" guard and call
# multiprocessing.freeze_support() (see FindCurves.py)

import itertools, multiprocessing, os, time, warnings
import numpy
import pyeq3

import EquationCatalog


# default maximum number of coefficients, as on zunzunsite3
defaultMaxCoefficients = {2: 5, 3: 6}

# only the best results are kept with full statistics, as on zunzunsite3
maxResultsKept = 1000

# zunzunsite3 limits for the combination equation types
maxPolyfunctionalTerms = {2: 4, 3: 2}
maxRationalTermsEach = 2


class FunctionFinderOptions:
    def __init__(self):
        self.formGroups = ['STANDARD'] # see EquationCatalog.formGroups
        self.polynomialOrders = True    # polynomials of every order
        self.polyfunctional = False     # combinations of functions (SSQABS only)
        self.rational = False           # 2D rational combinations


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


def ListEquationSpecs(dim, fittingTarget, maxCoefficients, exactCount, options):
    # returns a list of [spec, coefficient count, linear flag] for every
    # equation selected by the options and the coefficient limit
    def Wanted(count):
        return count == maxCoefficients if exactCount else count <= maxCoefficients

    forms = [f for group in options.formGroups for f in EquationCatalog.formGroups[group]]
    specs = []
    for moduleName, equations in EquationCatalog.ListEquations(dim).items():
        for className in equations.values():
            equationClass = EquationCatalog.GetClass(dim, moduleName, className)
            if EquationCatalog.SpecialKind(equationClass) is not None:
                continue
            for form in forms:
                if not EquationCatalog.FormAllowed(equationClass, form, dim):
                    continue
                try:
                    equation = equationClass(fittingTarget, form)
                except Exception:
                    continue # this form cannot be used with this equation
                count = len(equation.GetCoefficientDesignators())
                if Wanted(count):
                    linear = fittingTarget == 'SSQABS' and equation.CanLinearSolverBeUsedForSSQABS()
                    specs.append([{'dim': dim, 'module': moduleName, 'class': className, 'form': form}, count, linear])

    linear = fittingTarget == 'SSQABS'
    if options.polynomialOrders:
        maxOrder = EquationCatalog.maxPolynomialOrder[dim]
        if dim == 2:
            orders = [{'xOrder': x} for x in range(maxOrder + 1)]
        else:
            orders = [{'xOrder': x, 'yOrder': y} for x in range(maxOrder + 1) for y in range(maxOrder + 1)]
        for params in orders:
            count = (params['xOrder'] + 1) * (params.get('yOrder', 0) + 1)
            if Wanted(count):
                specs.append([{'dim': dim, 'module': 'Polynomial', 'class': 'UserSelectablePolynomial', 'form': 'Default',
                               'params': params}, count, linear])

    # polyfunctionals use the linear solver, so like zunzunsite3 these are
    # only used for the sum of squared absolute error fitting target
    if options.polyfunctional and fittingTarget == 'SSQABS':
        lists = EquationCatalog.FunctionLists(dim, 'polyfunctional')
        if dim == 2:
            terms = list(range(len(lists[0])))
        else:
            terms = [[i, j] for i in range(len(lists[0])) for j in range(len(lists[1]))]
        for count in range(1, maxPolyfunctionalTerms[dim] + 1):
            if not Wanted(count):
                continue
            for flags in itertools.combinations(terms, count):
                specs.append([{'dim': dim, 'module': 'Polyfunctional', 'class': 'UserSelectablePolyfunctional', 'form': 'Default',
                               'params': {'flags': list(flags)}}, count, True])

    if options.rational and dim == 2:
        size = len(EquationCatalog.FunctionLists(dim, 'rational')[0])
        termCombinations = [list(c) for n in range(1, maxRationalTermsEach + 1) for c in itertools.combinations(range(size), n)]
        for numerator in termCombinations:
            for denominator in termCombinations:
                count = len(numerator) + len(denominator)
                if Wanted(count):
                    specs.append([{'dim': dim, 'module': 'Rational', 'class': 'UserSelectableRational', 'form': 'Default',
                                   'params': {'numerator': numerator, 'denominator': denominator}}, count, False])
    return specs


# ---- worker process functions ----

_workerDataCache = None
_workerBadCacheFlags = {}

def _InitWorker(dataCache):
    global _workerDataCache
    _workerDataCache = dataCache
    # poor fits generate many numeric warnings, which are expected here
    warnings.simplefilter('ignore')
    numpy.seterr(all='ignore')


def _ScreenEquation(equation):
    # returns a reason the data cannot be used with this equation, or ''
    if equation.ShouldDataBeRejected(equation):
        return getattr(equation, 'reasonWhyDataRejected', '') or 'Data rejected by this equation'
    # see if the cache generation yielded any overly large numbers or exceptions
    try:
        equation.dataCache.FindOrCreateAllDataCache(equation)
        for cacheName in [i[0] for i in equation.GetDataCacheFunctions()]:
            if cacheName not in _workerBadCacheFlags:
                values = equation.dataCache.allDataCacheDictionary[cacheName]
                _workerBadCacheFlags[cacheName] = not numpy.all(numpy.isfinite(values)) or numpy.max(numpy.abs(values)) >= 1.0E300
            if _workerBadCacheFlags[cacheName]:
                return 'Data values are invalid for this equation'
    except Exception:
        return 'Data values are invalid for this equation'
    return ''


def _FitInWorker(task):
    index, spec, fittingTarget = task
    try:
        equation = EquationCatalog.CreateEquation(spec, fittingTarget)
        equation.dataCache = _workerDataCache
        reason = _ScreenEquation(equation)
        if reason:
            return (index, 'skipped', reason)
        equation.Solve()
        coefficients = numpy.array(equation.solvedCoefficients, dtype=float)
        if not numpy.all(numpy.isfinite(coefficients)):
            return (index, 'failed', 'Solver did not converge')
        target = equation.CalculateAllDataFittingTarget(equation.solvedCoefficients)
        if not numpy.isfinite(target) or target > 1.0E290:
            return (index, 'failed', 'Fitting target could not be calculated')
        return (index, 'fitted', (float(target), coefficients))
    except Exception as e:
        return (index, 'failed', str(e) or repr(e))


def _FitBatchInWorker(tasks):
    return [_FitInWorker(task) for task in tasks]


# ---- function finder run, used by the GUI ----

class FunctionFinderRun:
    # The GUI calls Poll() periodically, which collects any finished results
    # without blocking.

    def __init__(self, dim, fittingTarget, textData, maxCoefficients, exactCoefficientCount=False,
                 options=None, processes=None):
        self.dim = dim
        self.fittingTarget = fittingTarget
        self.textData = textData
        self.maxCoefficients = maxCoefficients
        self.exactCoefficientCount = exactCoefficientCount
        self.options = options or FunctionFinderOptions()
        self.cancelled = False

        self.fitted = []  # [fitting target value, spec index, coefficients]
        self.skipped = [] # [module name, display name, reason]
        self.failed = []  # [module name, display name, reason]
        self.bestTarget = None
        self.bestIndex = None
        self._sortedResults = None

        # convert the data once, and share the data cache with every equation
        self.dataCache = ConvertData(dim, textData)
        self.dataPointCount = len(self.dataCache.allDataCacheDictionary['DependentData'])

        specs = ListEquationSpecs(dim, fittingTarget, maxCoefficients, exactCoefficientCount, self.options)
        self.specs = []
        linearTasks, nonlinearTasks = [], []
        for spec, count, linear in specs:
            index = len(self.specs)
            self.specs.append(spec)
            # require at least one degree of freedom for error, otherwise equations
            # that can exactly interpolate the data would rank as perfect fits
            if count >= self.dataPointCount:
                self.skipped.append(self._Describe(index) + ['Requires more than %d data points' % count])
            elif linear:
                linearTasks.append((index, spec, fittingTarget))
            else:
                nonlinearTasks.append(((index, spec, fittingTarget), count))

        self.total = len(self.specs)
        self.completed = len(self.skipped)
        self.linearCount = len(linearTasks)
        self.nonlinearCount = len(nonlinearTasks)

        self.pool = None
        self.iterators = []
        self.pending = [0, 0]
        if linearTasks or nonlinearTasks:
            if processes is None:
                # leave one CPU core free so the computer stays responsive
                processes = max(1, (os.cpu_count() or 2) - 1)
            self.pool = multiprocessing.Pool(processes, initializer=_InitWorker, initargs=(self.dataCache,))
            # linear fits are very fast: send them in batches, and first, so
            # that many results are available quickly
            batches = [linearTasks[i:i + 50] for i in range(0, len(linearTasks), 50)]
            self.iterators.append(self.pool.imap_unordered(_FitBatchInWorker, batches, chunksize=1))
            # fit the nonlinear equations with the most coefficients first, as these
            # usually take the longest - this gives better use of all CPU cores
            nonlinearTasks.sort(key=lambda item: -item[1])
            self.iterators.append(self.pool.imap_unordered(_FitInWorker, [t[0] for t in nonlinearTasks], chunksize=1))
            self.pending = [len(batches), len(nonlinearTasks)]


    def _Describe(self, index):
        # [module name, display name] for a spec, for skipped and failed lists
        spec = self.specs[index]
        try:
            equation = EquationCatalog.CreateEquation(spec, self.fittingTarget)
            return [spec['module'], equation.GetDisplayName()]
        except Exception:
            return [spec['module'], spec['class']]


    def _AddResult(self, index, status, data):
        self.completed += 1
        if status == 'fitted':
            target, coefficients = data
            self.fitted.append([target, index, coefficients])
            if self.bestTarget is None or target < self.bestTarget:
                self.bestTarget, self.bestIndex = target, index
        elif status == 'skipped':
            self.skipped.append(self._Describe(index) + [data])
        else:
            self.failed.append(self._Describe(index) + [data])


    def IsDone(self):
        return self.cancelled or self.completed >= self.total


    def Poll(self):
        # collect any finished results, returns True when all equations are done
        while not self.IsDone():
            gotResult = False
            for which, iterator in enumerate(self.iterators):
                if self.pending[which] <= 0:
                    continue
                try:
                    result = iterator.next(timeout=0)
                except multiprocessing.TimeoutError:
                    continue
                self.pending[which] -= 1
                gotResult = True
                for index, status, data in (result if which == 0 else [result]):
                    self._AddResult(index, status, data)
            if not gotResult:
                return False
        self._StopPool()
        return True


    def _StopPool(self):
        if self.pool is not None:
            self.pool.terminate()
            self.pool = None


    def Cancel(self):
        self.cancelled = True
        self._StopPool()


    def BestSoFarDescription(self):
        if self.bestIndex is None:
            return ''
        return '%s (%s = %.6E)' % (self._Describe(self.bestIndex)[1], self.fittingTarget, self.bestTarget)


    def SortedResults(self):
        # Fitted equation objects with statistics, best fit (lowest fitting
        # target value) first.  Only the best maxResultsKept are returned.
        if self._sortedResults is None:
            best = sorted(self.fitted, key=lambda r: r[0])[:maxResultsKept]
            self._sortedResults = []
            with warnings.catch_warnings(), numpy.errstate(all='ignore'):
                warnings.simplefilter('ignore')
                for target, index, coefficients in best:
                    equation = self._BuildEquation(index, target, coefficients)
                    if equation is not None:
                        self._sortedResults.append(equation)
        return self._sortedResults


    def _BuildEquation(self, index, target, coefficients):
        # recreate a fitted equation in this process and calculate statistics
        try:
            equation = EquationCatalog.CreateEquation(self.specs[index], self.fittingTarget)
            equation.dataCache = self.dataCache
            equation.solvedCoefficients = coefficients
            equation.fittingTargetValue = target
            equation.dataCache.FindOrCreateAllDataCache(equation)
            equation.CalculateModelErrors(equation.solvedCoefficients, equation.dataCache.allDataCacheDictionary)
            try:
                equation.CalculateCoefficientAndFitStatistics()
            except Exception:
                # the overall fit is still usable, but parameter statistics are not
                equation.cov_beta = None
                equation.sd_beta = None
                equation.tstat_beta = None
                equation.pstat_beta = None
                equation.ci = None
            return equation
        except Exception as e:
            self.failed.append(self._Describe(index) + [str(e) or repr(e)])
            return None
