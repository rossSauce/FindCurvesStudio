# Orthogonal distance regression, and the coefficient covariance matrix
# used for fit statistics, for pyeq3:
#   - fitting with the "ODR" (orthogonal distance) fitting target, which
#     allows for errors in the independent data as well as the dependent
#     data, by the Levenberg-Marquardt method of ODRPACK
#   - the covariance matrix behind the coefficient standard errors,
#     confidence intervals, t-statistics and p-values of every fitted
#     equation, whatever its fitting target
#
# pyeq3 does these with scipy.odr, which is deprecated and will be removed
# in SciPy 1.19 - without it, every fit would fail when calculating its
# statistics.  This module provides the small part of the scipy.odr
# interface that pyeq3 calls: Model, Data, ODR(...).set_job(...) and
# .run().  It is always used, so results do not depend on the SciPy version.
#
# Importing this module installs it into pyeq3.

import types

import numpy
import scipy
import scipy.linalg
import scipy.optimize


class Model:
    def __init__(self, fcn, **unused):
        self.fcn = fcn # fcn(beta, x)


class Data:
    def __init__(self, x, y=None, we=None, wd=None, fix=None, meta=None):
        self.x = numpy.array(x, dtype=float)
        self.y = numpy.array(y, dtype=float)
        self.we = we # weights for the dependent data (y) errors
        self.wd = wd # weights for the independent data (x) adjustments


RealData = Data


class Output:
    pass


class ODR:
    def __init__(self, data, model, beta0=None, maxit=None, **unused):
        self.data = data
        self.model = model
        self.beta0 = numpy.array(beta0, dtype=float)
        self.maxit = 50 if maxit is None else maxit # ODRPACK's default
        self.fitType = 0 # 0 = explicit orthogonal distance, 2 = ordinary least squares

    def set_job(self, fit_type=None, **unused):
        # derivatives are always calculated by finite differences
        if fit_type is not None:
            if fit_type not in (0, 2):
                raise NotImplementedError('only explicit ODR and ordinary least squares are available')
            self.fitType = fit_type

    def run(self):
        x, y = self.data.x, self.data.y
        n, p = len(y), len(self.beta0)
        sqrtWe = _Weights(self.data.we, n, 'we')

        def Predict(beta, xValues):
            # pyeq3 can change the coefficients in place (bounds and fixed
            # coefficients), so always pass a copy
            return numpy.asarray(self.model.fcn(numpy.array(beta, dtype=float), xValues), dtype=float)

        beta = self.beta0.copy()
        delta = numpy.zeros_like(x)
        if self.fitType == 2:
            if self.maxit > 0:
                fit = scipy.optimize.least_squares(lambda b: sqrtWe * (y - Predict(b, x)), beta,
                                                   max_nfev=self.maxit * (p + 1), x_scale='jac')
                beta = fit.x
        elif self.maxit > 0:
            beta, delta = _SolveOrthogonalDistance(Predict, x, y, sqrtWe, self.data.wd, beta, self.maxit)

        out = Output()
        out.beta = beta
        out.delta = delta
        out.eps = y - Predict(beta, x + delta)
        weightedEps = sqrtWe * out.eps
        out.sum_square_eps = float(numpy.dot(weightedEps, weightedEps))
        sqrtWd = _Weights(self.data.wd, x.size, 'wd').reshape(x.shape)
        out.sum_square_delta = float(numpy.sum((sqrtWd * delta) ** 2)) if self.fitType == 0 else 0.0
        out.sum_square = out.sum_square_eps + out.sum_square_delta
        out.res_var = out.sum_square / (n - p) if n > p else numpy.nan

        # covariance as for ordinary least squares at the solution: the
        # "unscaled" covariance, as in scipy.odr, so sd_beta also uses res_var
        jacobian = _Jacobian(lambda b: sqrtWe * Predict(b, x + delta), beta)
        out.cov_beta = numpy.full((p, p), numpy.nan)
        # pyeq3 predicts 1.0E300 where an equation cannot be calculated, for
        # example at a singularity; the statistics are then not available
        if numpy.all(numpy.isfinite(jacobian)) and numpy.max(numpy.abs(jacobian), initial=0.0) < 1.0e250:
            try:
                out.cov_beta = _Covariance(jacobian)
            except (numpy.linalg.LinAlgError, ValueError):
                pass
        out.sd_beta = numpy.sqrt(numpy.abs(numpy.diag(out.cov_beta)) * out.res_var)
        out.info = 1
        out.stopreason = ['FindCurves Studio orthogonal distance regression']
        return out


def _Weights(weights, size, name):
    # square roots of the weights, as an array of the given size
    if weights is None:
        return numpy.ones(size)
    weights = numpy.asarray(weights, dtype=float)
    if weights.size == 1:
        return numpy.full(size, numpy.sqrt(weights.item()))
    if weights.size != size:
        raise NotImplementedError('%s weights must be a single value or one per data value' % name)
    return numpy.sqrt(weights.ravel())


def _Covariance(jacobian):
    # inverse(J'J), calculated as ODRPACK does: the columns are scaled to unit
    # length and factored with a pivoted QR decomposition, and coefficients
    # that the data cannot determine at all (rank deficiency) are left out,
    # with zero variance.  Nearly undetermined coefficients keep their large
    # variances, so their standard errors show that they are undetermined.
    p = jacobian.shape[1]
    cov = numpy.zeros((p, p))
    norms = numpy.linalg.norm(jacobian, axis=0)
    used = numpy.flatnonzero(norms > 0.0)
    if used.size == 0:
        return cov
    q, r, pivots = scipy.linalg.qr(jacobian[:, used] / norms[used], mode='economic', pivoting=True)
    diagonal = numpy.abs(numpy.diag(r))
    rank = int(numpy.sum(diagonal > 1.0e-12 * diagonal[0]))
    rInverse = scipy.linalg.solve_triangular(r[:rank, :rank], numpy.eye(rank))
    keep = used[pivots[:rank]]
    cov[numpy.ix_(keep, keep)] = (rInverse @ rInverse.T) / numpy.outer(norms[keep], norms[keep])
    return cov


def _Jacobian(function, beta):
    # central differences, d function / d beta
    columns = []
    for i in range(len(beta)):
        step = numpy.finfo(float).eps ** (1.0 / 3.0) * max(abs(beta[i]), 1.0)
        up, down = beta.copy(), beta.copy()
        up[i] += step
        down[i] -= step
        columns.append((function(up) - function(down)) / (2.0 * step))
    return numpy.column_stack(columns) if columns else numpy.zeros((0, 0))


def _SolveOrthogonalDistance(Predict, x, y, sqrtWe, wd, beta0, maxit):
    # Explicit orthogonal distance regression, as in ODRPACK: find the
    # coefficients (beta) and adjustments to every independent data value
    # (delta) that minimize
    #     sum(we * (y - f(x + delta, beta))**2) + sum(wd * delta**2)
    #
    # This is the Levenberg-Marquardt method used by ODRPACK (Boggs, Byrd
    # and Schnabel, 1987).  The model is evaluated point by point, so each
    # data point's deltas only affect that point.  Each step is a linear
    # least squares problem: every point's deltas are projected out with a
    # small QR factorization, leaving a problem in the coefficients alone,
    # and then each point's deltas are found - quick even for many data
    # points.  Orthogonal factorizations are used rather than the normal
    # equations, which lose too much precision for ill-conditioned
    # equations such as high order polynomials.
    p, n = len(beta0), len(y)
    m = 1 if x.ndim == 1 else x.shape[0] # rows of independent data
    x2 = x.reshape(m, n)
    wdRows = (_Weights(wd, x.size, 'wd') ** 2).reshape(m, n)
    sstol = numpy.sqrt(numpy.finfo(float).eps) # ODRPACK's default tolerances
    partol = numpy.finfo(float).eps ** (2.0 / 3.0)

    def WeightedModel(beta, delta):
        return sqrtWe * Predict(beta, (x2 + delta).reshape(x.shape))

    def Cost(weightedPrediction, delta):
        e = sqrtWe * y - weightedPrediction
        return float(e @ e + numpy.sum(wdRows * delta * delta))

    def Minimize(beta, delta, fitDeltas, iterationLimit):
        # fitDeltas False: ordinary least squares, with the deltas held at zero
        prediction = WeightedModel(beta, delta)
        cost = Cost(prediction, delta)
        if not numpy.isfinite(cost):
            return beta, delta, cost
        # start cautiously, as ODRPACK does, so the first steps from a poor
        # starting point do not jump to a distant, poor solution
        damping = 1.0
        history = [cost]
        for iteration in range(iterationLimit):
            # derivatives of the weighted model for the coefficients (n x p) and
            # for each point's independent data values (n x m)
            Jb = _Jacobian(lambda b: WeightedModel(b, delta), beta)
            G = numpy.zeros((n, m))
            for r in range(m if fitDeltas else 0):
                step = numpy.finfo(float).eps ** (1.0 / 3.0) * numpy.maximum(numpy.abs(x2[r] + delta[r]), 1.0)
                up, down = delta.copy(), delta.copy()
                up[r] += step
                down[r] -= step
                G[:, r] = (WeightedModel(beta, up) - WeightedModel(beta, down)) / (2.0 * step)
            if not (numpy.all(numpy.isfinite(Jb)) and numpy.all(numpy.isfinite(G))):
                break
            e = sqrtWe * y - prediction
            sqrtWdT = numpy.sqrt(wdRows).T # n x m
            # Marquardt scaling of the damping, by the size of each derivative
            betaScale = numpy.linalg.norm(Jb, axis=0)
            deltaScale = numpy.sqrt(G * G + wdRows.T)
            eye = numpy.eye(m)

            improved = False
            while damping < 1.0e16:
                # Minimize, for each point i:  |c_i - K_i dBeta - M_i dDelta_i|^2
                # plus the damping of dBeta.  The rows of each point are its
                # y error, its weighted deltas, and the damping of its deltas.
                rootDamping = numpy.sqrt(damping)
                if not fitDeltas:
                    dBeta = numpy.linalg.lstsq(numpy.vstack([Jb, numpy.diag(rootDamping * betaScale)]),
                                               numpy.concatenate([e, numpy.zeros(p)]), rcond=None)[0]
                    dDelta = numpy.zeros((n, m))
                else:
                    M = numpy.concatenate([G[:, None, :], sqrtWdT[:, :, None] * eye,
                                           (rootDamping * deltaScale)[:, :, None] * eye], axis=1) # n x (1+2m) x m
                    c = numpy.concatenate([e[:, None], -sqrtWdT * delta.T, numpy.zeros((n, m))], axis=1)
                    K = numpy.zeros((n, 1 + 2 * m, p))
                    K[:, 0, :] = Jb
                    Q, R = numpy.linalg.qr(M, mode='complete')
                    Q1, Q2 = Q[:, :, :m], Q[:, :, m:]
                    # with the deltas projected out, the coefficients' problem
                    reducedK = numpy.einsum('irk,irp->ikp', Q2, K).reshape(-1, p)
                    reducedC = numpy.einsum('irk,ir->ik', Q2, c).ravel()
                    dBeta = numpy.linalg.lstsq(numpy.vstack([reducedK, numpy.diag(rootDamping * betaScale)]),
                                               numpy.concatenate([reducedC, numpy.zeros(p)]), rcond=None)[0]
                    # then each point's deltas
                    remaining = c - numpy.einsum('irp,p->ir', K, dBeta)
                    dDelta = numpy.einsum('ikm,im->ik', numpy.linalg.pinv(R[:, :m, :]),
                                          numpy.einsum('irk,ir->ik', Q1, remaining)) # n x m
                newBeta, newDelta = beta + dBeta, delta + dDelta.T
                newPrediction = WeightedModel(newBeta, newDelta)
                newCost = Cost(newPrediction, newDelta)
                if numpy.isfinite(newCost) and newCost < cost:
                    improved = True
                    break
                damping *= 10.0
            if not improved:
                break
            reduction = (cost - newCost) / max(cost, numpy.finfo(float).tiny)
            smallStep = numpy.linalg.norm(dBeta) <= partol * (numpy.linalg.norm(beta) + partol)
            # a small improvement only shows convergence when the step was close
            # to a full Gauss-Newton step - heavily damped steps are always small
            nearlyUndamped = damping <= 1.0e-2
            beta, delta, prediction, cost = newBeta, newDelta, newPrediction, newCost
            damping = max(damping / 10.0, 1.0e-12)
            if nearlyUndamped and (reduction <= sstol or smallStep):
                break
            # stalled: ill-conditioned fits can creep on for thousands of
            # iterations with no useful improvement
            history.append(cost)
            if len(history) > 20 and history[-21] - cost <= 1.0e-5 * history[-21]:
                break
        return beta, delta, cost

    # From a poor starting point the deltas can slide points along a steep
    # curve into a poor local minimum, so the coefficients are first fitted
    # by ordinary least squares.  The fit is also made directly from the
    # starting point, and the better result is kept.
    zero = numpy.zeros((m, n))
    beta0 = numpy.array(beta0, dtype=float)
    if len(numpy.unique(beta0)) < p:
        # equal starting values, such as pyeq3's start with every coefficient
        # 1.0, can keep similar terms such as a*exp(b*x) + c*exp(d*x) equal
        # throughout the fit, so make them slightly different
        beta0 = beta0 + 1.0e-3 * (numpy.abs(beta0) + 1.0e-3) * numpy.linspace(-1.0, 1.0, p)
    fromLeastSquares = Minimize(Minimize(beta0, zero, False, maxit)[0], zero, True, maxit)
    # directly from a poor starting point the fit can crawl for many
    # iterations; the least squares start covers that case
    direct = Minimize(beta0, zero, True, min(maxit, 500))
    beta, delta, cost = min([direct, fromLeastSquares], key=lambda result: result[2] if numpy.isfinite(result[2]) else numpy.inf)
    return beta, delta.reshape(x.shape)


# ---- installed into pyeq3 ----

odr = types.SimpleNamespace(Model=Model, Data=Data, RealData=RealData, ODR=ODR, Output=Output)
odr.odrpack = odr # pyeq3 also uses scipy.odr.odrpack.Data


class _ScipyWithThisModuleAsOdr(types.ModuleType):
    # scipy, but with this module's odr
    def __init__(self):
        types.ModuleType.__init__(self, 'scipy')
        self.odr = odr

    def __getattr__(self, name):
        return getattr(scipy, name)


def _Install():
    import pyeq3.IModel, pyeq3.Services.SolverService
    scipyWithThisModule = _ScipyWithThisModuleAsOdr()
    for module in [pyeq3.IModel, pyeq3.Services.SolverService]:
        module.scipy = scipyWithThisModule

_Install()
