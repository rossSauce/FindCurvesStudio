# Parsing of user defined functions, such as  a * X + b * exp(c * X),
# replacing pyeq3's own parser for its UserDefinedFunction equations.
#
# pyeq3's parser works on the raw text and has several problems that this
# fixes:
#   - "fabs" is rejected because it contains "abs"
#   - numbers inside names and exponents are broken by its integer to float
#     conversion: log10, log2, arctan2, deg2rad, rad2deg and 3.5e-2 all fail
#   - words in comment lines become extra coefficients
#   - coefficient names cannot contain digits, such as a1 and a2
#   - mistakes such as unknown function names are not reported - the fit
#     just fails, with no reason given
# The function text is parsed with Python's own parser and only plain math
# is accepted: numbers, X (and Y), coefficient names, + - * / ** and
# parentheses, and calls to the functions listed below.
#
# Importing this module installs the parser into pyeq3.

import ast, re

import numpy

import pyeq3


# function name: numpy function.  pyeq3's own functions, plus friendlier
# names that people often type
functions = {name: getattr(numpy, name) for name in [
    'exp', 'log', 'log10', 'log2',
    'sin', 'cos', 'tan', 'arcsin', 'arccos', 'arctan', 'hypot', 'arctan2', 'deg2rad', 'rad2deg',
    'arcsinh', 'arccosh', 'arctanh', 'sinh', 'cosh', 'tanh',
    'sinc', 'sqrt', 'square', 'fabs', 'sign']}
functions.update({'abs': numpy.absolute, 'ln': numpy.log, 'pow': numpy.power})

constants = {'pi': numpy.pi, 'e': numpy.e}

_twoArgumentFunctions = {'arctan2', 'hypot', 'pow'}
_reservedNames = {'x_in', 'y_in', 'temp'}
_operators = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd)
_coefficientName = re.compile(r'[A-Za-z][A-Za-z0-9_]*\Z')


def FunctionNamesText():
    return ', '.join(sorted(functions))


def Parse(text, dim):
    # Returns (expression tree, sorted coefficient names, display text), or
    # raises ValueError with a message for the user.
    variables = ['X', 'Y'] if dim == 3 else ['X']

    # comments start with #, and the function may be split over lines
    lines = [line.split('#', 1)[0].strip() for line in text.splitlines()]
    text = ' '.join(line for line in lines if line)
    if not text:
        raise ValueError('Please enter a function, such as a * X + b * exp(c * X).')
    text = text.replace('[', '(').replace(']', ')')
    if '^' in text:
        raise ValueError('Please use ** for powers, not ^ - for example X**2.')
    if '=' in text:
        raise ValueError('Please enter only the right hand side of the equation, without "y =".')

    try:
        tree = ast.parse(text, mode='eval')
    except SyntaxError as e:
        where = ''
        if e.offset:
            where = ' at "%s"' % text[max(e.offset - 1, 0):][:20]
        raise ValueError('The function could not be read%s. Please check it for missing or extra '
                         'parentheses, operators or commas.' % where)

    coefficients = set()
    usedVariables = set()

    def Describe(node):
        return '"%s"' % ast.get_source_segment(text, node)

    def Check(node):
        if isinstance(node, ast.BinOp) and isinstance(node.op, _operators):
            Check(node.left)
            Check(node.right)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, _operators):
            Check(node.operand)
        elif isinstance(node, ast.Constant):
            if type(node.value) not in (int, float):
                raise ValueError('%s is not a number.' % Describe(node))
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError('%s is not one of the available functions: %s.'
                                 % (Describe(node.func), FunctionNamesText()))
            name = node.func.id
            if name not in functions:
                hint = ''
                if name.lower() in functions:
                    hint = ' Function names are lower case: %s().' % name.lower()
                raise ValueError('"%s()" is not one of the available functions.%s\n\nAvailable functions: %s.'
                                 % (name, hint, FunctionNamesText()))
            if node.keywords:
                raise ValueError('Named arguments such as %s are not allowed.' % Describe(node.keywords[0]))
            count = 2 if name in _twoArgumentFunctions else 1
            if len(node.args) != count:
                example = '%s(X, b)' % name if count == 2 else '%s(X)' % name
                raise ValueError('%s() needs %s, such as %s.'
                                 % (name, 'two values' if count == 2 else 'one value', example))
            for argument in node.args:
                Check(argument)
        elif isinstance(node, ast.Name):
            name = node.id
            if name in functions:
                raise ValueError('The function "%s" must be followed by its value in parentheses, '
                                 'such as %s(X).' % (name, name))
            if name in variables:
                usedVariables.add(name)
            elif name in constants:
                pass
            elif name.lower() in variables:
                raise ValueError('Please use upper case %s for the data, not %s.' % (name.upper(), name))
            elif name in _reservedNames:
                raise ValueError('"%s" is used in the generated source code, please choose another '
                                 'coefficient name.' % name)
            elif _coefficientName.match(name):
                coefficients.add(name)
            else:
                raise ValueError('"%s" cannot be used as a coefficient name. Use letters, and '
                                 'optionally digits after them, such as a, b2 or slope.' % name)
        else:
            raise ValueError('%s is not allowed. Use numbers, %s, coefficient names, + - * / **, '
                             'parentheses, and these functions: %s.'
                             % (Describe(node), ' and '.join(variables), FunctionNamesText()))

    Check(tree.body)
    if usedVariables != set(variables):
        raise ValueError('The function must use %s for the data values.' % ' and '.join(variables))
    if not coefficients:
        raise ValueError('The function has no coefficients to fit. Use letters such as a, b and c '
                         'for the values to be fitted, for example a * X + b.')
    return tree, sorted(coefficients), ast.unparse(tree)


# ---- source code ----

# pyeq3 generates source code in ten languages from one C++ expression,
# converting it to the other languages by text replacement that only knows
# these functions: abs pow log log10 exp sin cos tan asin atan cosh tanh.
# Other functions are written using them.
_cppFunctions = {
    'exp': 'exp(%s)', 'log': 'log(%s)', 'ln': 'log(%s)', 'log10': 'log10(%s)',
    'log2': '(log(%s) / log(2.0))',
    'sin': 'sin(%s)', 'cos': 'cos(%s)', 'tan': 'tan(%s)',
    'arcsin': 'asin(%s)', 'arctan': 'atan(%s)',
    'arccos': '(1.5707963267948966 - asin(%s))',
    'deg2rad': '((%s) * 0.017453292519943295)', 'rad2deg': '((%s) * 57.29577951308232)',
    'sinh': '((exp(%s) - exp(-(%s))) / 2.0)', 'cosh': 'cosh(%s)', 'tanh': 'tanh(%s)',
    'arcsinh': 'log((%s) + pow(pow(%s, 2.0) + 1.0, 0.5))',
    'arccosh': 'log((%s) + pow(pow(%s, 2.0) - 1.0, 0.5))',
    'arctanh': '(0.5 * log((1.0 + (%s)) / (1.0 - (%s))))',
    'sinc': '(sin(3.141592653589793 * (%s)) / (3.141592653589793 * (%s)))',
    'sqrt': 'pow(%s, 0.5)', 'square': 'pow(%s, 2.0)', 'fabs': 'abs(%s)', 'abs': 'abs(%s)',
    'pow': 'pow(%s, %s)', 'hypot': 'pow(pow(%s, 2.0) + pow(%s, 2.0), 0.5)',
}
_cppConstants = {'pi': '3.141592653589793', 'e': '2.718281828459045'}
_precedence = {ast.Add: 1, ast.Sub: 1, ast.Mult: 2, ast.Div: 2}


def CppExpression(tree):
    # C++ for a parsed function, for pyeq3's source code output.  Raises
    # NotImplementedError for functions that cannot be converted.
    def Cpp(node):
        if isinstance(node, ast.Expression):
            return Cpp(node.body)
        if isinstance(node, ast.Constant):
            return repr(float(node.value))
        if isinstance(node, ast.Name):
            return {'X': 'x_in', 'Y': 'y_in'}.get(node.id, _cppConstants.get(node.id, node.id))
        if isinstance(node, ast.UnaryOp):
            return '(-%s)' % Cpp(node.operand) if isinstance(node.op, ast.USub) else Cpp(node.operand)
        if isinstance(node, ast.Call):
            template = _cppFunctions.get(node.func.id)
            if template is None or template.count('%s') not in (len(node.args), 2 * len(node.args)):
                raise NotImplementedError
            args = [Cpp(a) for a in node.args]
            if len(args) == 1:
                args = args * template.count('%s')
            return template % tuple(args)
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Pow):
                return 'pow(%s, %s)' % (Cpp(node.left), Cpp(node.right))
            level = _precedence[type(node.op)]
            left, right = Cpp(node.left), Cpp(node.right)
            if _Level(node.left) < level:
                left = '(%s)' % left
            # a - (b + c) and a / (b * c) need their parentheses
            if _Level(node.right) < level or (_Level(node.right) == level and
                                              isinstance(node.op, (ast.Sub, ast.Div))):
                right = '(%s)' % right
            symbol = {ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/'}[type(node.op)]
            return '%s %s %s' % (left, symbol, right)
        raise NotImplementedError

    return Cpp(tree)


def _Level(node):
    if isinstance(node, ast.BinOp) and type(node.op) in _precedence:
        return _precedence[type(node.op)]
    return 3 # everything else is a single term


class _IntsToFloats(ast.NodeTransformer):
    # as in pyeq3, so that for example 1/2 and 2**-1 always use floats
    def visit_Constant(self, node):
        if type(node.value) is int:
            return ast.copy_location(ast.Constant(float(node.value)), node)
        return node


# ---- installed into pyeq3's UserDefinedFunction classes ----

def _ParseAndCompileUserFunctionString(self, inString, dim):
    tree, coefficients, displayText = Parse(inString, dim)
    self.userFunctionTree = tree
    floatTree = ast.fix_missing_locations(_IntsToFloats().visit(ast.parse(displayText, mode='eval')))
    self.userFunctionCodeObject = compile(floatTree, '<user defined function>', 'eval')
    self._coefficientDesignators = coefficients
    self.userFunctionDisplayText = displayText
    self.safe_dict = dict(functions)
    self.safe_dict.update(constants)


def _CalculateModelPredictions(self, inCoeffs, inDataCacheDictionary):
    names = dict(self.safe_dict)
    names['X'] = inDataCacheDictionary['X']
    if self.GetDimensionality() == 3:
        names['Y'] = inDataCacheDictionary['Y']
    names.update(zip(self._coefficientDesignators, inCoeffs))
    try:
        temp = eval(self.userFunctionCodeObject, {'__builtins__': {}}, names)
        return self.extendedVersionHandler.GetAdditionalModelPredictions(
            temp, inCoeffs, inDataCacheDictionary, self)
    except Exception:
        # as in pyeq3: a huge error makes the solvers avoid these coefficients
        return numpy.ones(len(inDataCacheDictionary['X'])) * 1.0e300


def _SpecificCodeCPP(self):
    # NotImplementedError is shown as "not available" in the reports
    return '\ttemp = %s;\n' % CppExpression(self.userFunctionTree)


def _Install():
    import pyeq3.Models_2D.UserDefinedFunction, pyeq3.Models_3D.UserDefinedFunction
    for equationClass in [pyeq3.Models_2D.UserDefinedFunction.UserDefinedFunction,
                          pyeq3.Models_3D.UserDefinedFunction.UserDefinedFunction]:
        equationClass.ParseAndCompileUserFunctionString = _ParseAndCompileUserFunctionString
        equationClass.CalculateModelPredictions = _CalculateModelPredictions
        equationClass.SpecificCodeCPP = _SpecificCodeCPP

_Install()
