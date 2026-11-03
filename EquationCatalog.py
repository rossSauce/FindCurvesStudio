# A catalog of every equation in the pyeq3 library, used by the main window,
# the function finder and the reports:
#
#   - the extended forms of each equation (Offset, Plus Line/Plane,
#     Reciprocal, Inverse, Linear and Exponential Growth/Decay)
#   - the special equation types that need settings: polynomials of a
#     selected order, customizable polynomials, polyfunctionals, rationals,
#     splines and user-defined functions
#   - readable display names for the special types, whose pyeq3 names do
#     not describe their settings
#
# An equation is described by a "spec" dictionary, which can be passed
# between processes:
#   {'dim': 2, 'module': 'Exponential', 'class': 'Exponential',
#    'form': 'Offset', 'params': {...settings for special types...}}

import collections, html, inspect, re, types

import pyeq3
import pyeq3.ExtendedVersionHandlers.ExtendedVersionHandler_PlusLine
import pyeq3.DataCache.DataCacheFunctions


def _FixPlusLineHandler():
    # pyeq3 12.6.1 bug: the "Plus Line" extended form uses the X data values
    # in its predictions, but does not request them from the data cache, so
    # fitting fails with NotImplementedError.  This adds the missing method,
    # in the same way as the "Plus Plane" handler.
    handler = pyeq3.ExtendedVersionHandlers.ExtendedVersionHandler_PlusLine.ExtendedVersionHandler_PlusLine
    if 'GetAdditionalDataCacheFunctions' in handler.__dict__:
        return # fixed in this pyeq3 version

    def GetAdditionalDataCacheFunctions(self, inModel, inDataCacheFunctions):
        if any(i[0] == 'X' for i in inDataCacheFunctions):
            return inDataCacheFunctions
        return inDataCacheFunctions + [[pyeq3.DataCache.DataCacheFunctions.X(NameOrValueFlag=1), []]]

    handler.GetAdditionalDataCacheFunctions = GetAdditionalDataCacheFunctions

_FixPlusLineHandler()


# ---- extended forms ----

# groups of extended forms, as in the zunzunsite3 function finder
formGroups = collections.OrderedDict([
    ('STANDARD', ['Default', 'Offset', 'PlusLine', 'PlusPlane']),
    ('RECIPROCAL', ['Reciprocal', 'ReciprocalWithOffset']),
    ('INVERSE', ['Inverse', 'InverseWithOffset']),
    ('LINEAR_GROWTH', ['LinearGrowth', 'LinearGrowthAndOffset']),
    ('LINEAR_DECAY', ['LinearDecay', 'LinearDecayAndOffset']),
    ('EXPONENTIAL_GROWTH', ['ExponentialGrowth', 'ExponentialGrowthAndOffset']),
    ('EXPONENTIAL_DECAY', ['ExponentialDecay', 'ExponentialDecayAndOffset']),
])

formGroupLabels = {'STANDARD': 'Standard', 'RECIPROCAL': 'Reciprocal', 'INVERSE': 'Inverse',
                   'LINEAR_GROWTH': 'Linear Growth', 'LINEAR_DECAY': 'Linear Decay',
                   'EXPONENTIAL_GROWTH': 'Exponential Growth', 'EXPONENTIAL_DECAY': 'Exponential Decay'}

formLabels = collections.OrderedDict([
    ('Default', 'Standard'), ('Offset', 'With Offset'),
    ('PlusLine', 'Plus Line'), ('PlusPlane', 'Plus Plane'),
    ('Reciprocal', 'Reciprocal'), ('ReciprocalWithOffset', 'Reciprocal With Offset'),
    ('Inverse', 'Inverse'), ('InverseWithOffset', 'Inverse With Offset'),
    ('LinearGrowth', 'Linear Growth'), ('LinearGrowthAndOffset', 'Linear Growth And Offset'),
    ('LinearDecay', 'Linear Decay'), ('LinearDecayAndOffset', 'Linear Decay And Offset'),
    ('ExponentialGrowth', 'Exponential Growth'), ('ExponentialGrowthAndOffset', 'Exponential Growth And Offset'),
    ('ExponentialDecay', 'Exponential Decay'), ('ExponentialDecayAndOffset', 'Exponential Decay And Offset'),
])


def FormAllowed(equationClass, form, dim):
    # the same rules as the zunzunsite3 function finder
    if form == 'Default':
        return True
    if form == 'PlusLine' and dim != 2 or form == 'PlusPlane' and dim != 3:
        return False
    rules = [('Offset', 'autoGenerateOffsetForm'), ('PlusLine', 'autoGeneratePlusLineForm'),
             ('PlusPlane', 'autoGeneratePlusPlaneForm'), ('Reciprocal', 'autoGenerateReciprocalForm'),
             ('Inverse', 'autoGenerateInverseForms'), ('Growth', 'autoGenerateGrowthAndDecayForms'),
             ('Decay', 'autoGenerateGrowthAndDecayForms')]
    for text, flag in rules:
        if text in form and not getattr(equationClass, flag, False):
            return False
    return True


def AvailableForms(dim, moduleName, className):
    # the extended forms that can be used with this equation
    equationClass = GetClass(dim, moduleName, className)
    if SpecialKind(equationClass) == 'spline':
        return ['Default']
    return [form for form in formLabels if FormAllowed(equationClass, form, dim)]


# ---- equation classes ----

def GetModelsModule(dim):
    return pyeq3.Models_2D if dim == 2 else pyeq3.Models_3D


def GetClass(dim, moduleName, className):
    return getattr(getattr(GetModelsModule(dim), moduleName), className)


def SpecialKind(equationClass):
    # the kind of settings an equation needs, or None for standard equations
    if getattr(equationClass, 'splineFlag', False):
        return 'spline'
    if equationClass.__module__.endswith('UserDefinedFunction'):
        return 'userFunction'
    if equationClass.userSelectablePolynomialFlag:
        return 'polynomialOrder'
    if equationClass.userCustomizablePolynomialFlag:
        return 'customPolynomial'
    if getattr(equationClass, 'userSelectablePolyfunctionalFlag', False) or equationClass.__module__.endswith('Polyfunctional'):
        return 'polyfunctional'
    if equationClass.userSelectableRationalFlag:
        return 'rational'
    return None


def ListEquations(dim):
    # returns {module name: {display name: class name}} for every equation,
    # sorted by module, with display names of the standard (Default) form
    catalog = collections.OrderedDict()
    for moduleName, module in inspect.getmembers(GetModelsModule(dim), inspect.ismodule):
        equations = {}
        for className, equationClass in inspect.getmembers(module, inspect.isclass):
            if not issubclass(equationClass, pyeq3.IModel.IModel) or equationClass.__module__ != module.__name__:
                continue
            kind = SpecialKind(equationClass)
            if kind is None:
                try:
                    name = equationClass('SSQABS', 'Default').GetDisplayName()
                except Exception:
                    continue
            else:
                name = equationClass._baseName
            equations[name] = className
        if equations:
            catalog[moduleName] = collections.OrderedDict(sorted(equations.items()))
    return catalog


# ---- function lists for the special types ----

_functionListCache = {}

def FunctionLists(dim, kind):
    # the lists of terms that can be selected for a special equation type,
    # shared between equations as creating them is relatively slow
    key = (dim, kind)
    if key not in _functionListCache:
        models = GetModelsModule(dim)
        if kind == 'polyfunctional':
            e = models.Polyfunctional.UserSelectablePolyfunctional('SSQABS')
            lists = [e.polyfunctionalEquationList] if dim == 2 else [e.polyfunctionalEquationList_X, e.polyfunctionalEquationList_Y]
        elif kind == 'rational':
            lists = [models.Rational.UserSelectableRational('SSQABS').rationalEquationList]
        elif kind == 'customPolynomial':
            lists = [models.Polynomial.UserCustomizablePolynomial('SSQABS').polynomialEquationList]
        else:
            lists = []
        _functionListCache[key] = lists
    return _functionListCache[key]


def TermText(term):
    # plain text for a term, e.g. 'x<sup>0.5</sup>' -> 'x^0.5'
    return HTMLToText(term.HTML)


def HTMLToText(text):
    text = re.sub(r'<sup>(.*?)</sup>', r'^\1', text, flags=re.IGNORECASE)
    text = re.sub(r'<sub>(.*?)</sub>', r'_\1', text, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '; ', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    return html.unescape(text).replace('\xa0', ' ').strip()


# limits on settings, as in zunzunsite3
maxPolynomialOrder = {2: 8, 3: 4}
maxSplineOrder = 5


# ---- creating equations ----

def CreateEquation(spec, fittingTarget):
    # Creates an equation from a spec.  Raises ValueError with a message
    # for the user if the settings are not valid.
    dim = spec['dim']
    equationClass = GetClass(dim, spec['module'], spec['class'])
    form = spec.get('form', 'Default')
    params = spec.get('params', {})
    kind = SpecialKind(equationClass)

    if kind == 'spline':
        smoothing = params.get('smoothing')
        if dim == 2:
            equation = equationClass(smoothing, params.get('xOrder', 3))
        else:
            equation = equationClass(smoothing, params.get('xOrder', 3), params.get('yOrder', 3))
    elif kind == 'userFunction':
        functionString = params.get('function', '').strip()
        if not functionString:
            raise ValueError('Please enter a function for the user defined function.')
        try:
            equation = equationClass(fittingTarget, form, functionString)
        except Exception as e:
            raise ValueError('The user defined function could not be used:\n\n' + str(e))
    elif kind == 'polynomialOrder':
        if dim == 2:
            equation = equationClass(fittingTarget, form, params.get('xOrder', 2))
        else:
            equation = equationClass(fittingTarget, form, params.get('xOrder', 2), params.get('yOrder', 2))
    elif kind == 'customPolynomial':
        flags = list(params.get('flags', []))
        if not flags:
            raise ValueError('Please select at least one term for the customizable polynomial.')
        equation = equationClass(fittingTarget, form, flags, FunctionLists(dim, kind)[0])
    elif kind == 'polyfunctional':
        flags = [list(f) if isinstance(f, (list, tuple)) else f for f in params.get('flags', [])]
        if not flags:
            raise ValueError('Please select at least one term for the polyfunctional.')
        equation = equationClass(fittingTarget, form, flags, *FunctionLists(dim, kind))
    elif kind == 'rational':
        numerator = list(params.get('numerator', []))
        denominator = list(params.get('denominator', []))
        if not numerator or not denominator:
            raise ValueError('Please select at least one numerator term and one denominator term for the rational equation.')
        equation = equationClass(fittingTarget, form, numerator, denominator, FunctionLists(dim, kind)[0])
    else:
        equation = equationClass(fittingTarget, form)

    if kind is not None:
        _SetDisplayName(equation, kind, params)
    equation.equationSpec = spec
    return equation


def _SetDisplayName(equation, kind, params):
    # replace pyeq3's generic name with one describing the settings
    base = equation.__class__._baseName
    if kind == 'spline':
        smoothing = params.get('smoothing')
        name = 'Spline, order %s' % params.get('xOrder', 3)
        if equation.GetDimensionality() == 3:
            name = 'Spline, X order %s, Y order %s' % (params.get('xOrder', 3), params.get('yOrder', 3))
        name += ', smoothing %s' % ('automatic' if smoothing is None else '%g' % smoothing)
    elif kind == 'userFunction':
        name = 'User Defined Function: ' + params.get('function', '').strip()
        functionHTML = html.escape(params.get('function', '').strip())
        left = 'y' if equation.GetDimensionality() == 2 else 'z'
        equation.GetDisplayHTML = types.MethodType(lambda self: left + ' = ' + functionHTML, equation)
    elif kind == 'polynomialOrder':
        if equation.GetDimensionality() == 2:
            name = 'Polynomial, order %d' % params.get('xOrder', 2)
        else:
            name = 'Polynomial, X order %d, Y order %d' % (params.get('xOrder', 2), params.get('yOrder', 2))
    else:
        formula = HTMLToText(equation.GetDisplayHTML())
        formula = formula.split('=', 1)[1].strip() if '=' in formula else formula
        name = {'customPolynomial': 'Custom Polynomial', 'polyfunctional': 'Polyfunctional',
                'rational': 'Rational'}[kind] + ': ' + formula
    form = equation.extendedVersionHandler.__class__.__name__.split('_')[-1] if hasattr(equation, 'extendedVersionHandler') else 'Default'
    if form not in ('Default', '') and kind not in ('spline',):
        name += ' (' + formLabels.get(form, form) + ')'
    equation.GetDisplayName = types.MethodType(lambda self: name, equation)


def IsSpline(equation):
    return getattr(equation, 'splineFlag', False)


def CoefficientNamesAndValues(equation):
    # [name, value] pairs, or [] for splines which have no named coefficients
    if IsSpline(equation):
        return []
    return list(zip(equation.GetCoefficientDesignators(), equation.solvedCoefficients))


def SplineDescription(equation):
    # text describing a fitted spline's knots and coefficients
    lines = ['Splines do not have named coefficients. The fitted spline is:', '']
    coefficients = equation.solvedCoefficients
    if equation.GetDimensionality() == 2:
        knots, values, order = coefficients
        lines.append('Spline order: %s' % order)
    else:
        knotsX, knotsY, values = coefficients[:3]
        knots = ['X knots:'] + list(knotsX) + ['Y knots:'] + list(knotsY)
        lines.append('Spline orders: X %s, Y %s' % (equation.xOrder, equation.yOrder))
    lines.append('Knots:')
    lines.extend('    %s' % (k if isinstance(k, str) else '%-.16E' % k) for k in knots)
    lines.append('Coefficients:')
    lines.extend('    %-.16E' % v for v in values)
    return '\n'.join(lines) + '\n'
