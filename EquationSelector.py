# A tkinter widget for choosing any pyeq3 equation: the equation family and
# equation, its extended form (Offset, Plus Line, Reciprocal, ...), and the
# settings needed by special equation types - polynomial orders, the terms of
# customizable polynomials, polyfunctionals and rationals, spline orders and
# smoothing, and user-defined functions.

import tkinter as tk
from tkinter import ttk

import EquationCatalog


class EquationSelector(tk.Frame):

    def __init__(self, parent, dim, defaultModule='Polynomial', defaultEquation=None):
        tk.Frame.__init__(self, parent)
        self.dim = dim
        self.catalog = EquationCatalog.ListEquations(dim)
        self.forms = [] # form names matching the form combobox entries

        row = tk.Frame(self)
        row.pack(anchor=tk.W, fill=tk.X)
        self.moduleCombo = ttk.Combobox(row, state='readonly', width=24, values=list(self.catalog.keys()))
        self.moduleCombo.pack(side=tk.LEFT)
        self.moduleCombo.bind("<<ComboboxSelected>>", lambda e: self.OnModuleChanged())
        tk.Label(row, text="  Form:").pack(side=tk.LEFT)
        self.formCombo = ttk.Combobox(row, state='readonly', width=24)
        self.formCombo.pack(side=tk.LEFT)

        self.equationCombo = ttk.Combobox(self, state='readonly', width=58)
        self.equationCombo.pack(anchor=tk.W, pady=(2, 0))
        self.equationCombo.bind("<<ComboboxSelected>>", lambda e: self.OnEquationChanged())

        # settings for special equation types; empty for standard equations
        self.settingsFrame = tk.Frame(self)
        self.settingsFrame.pack(anchor=tk.W, fill=tk.X, pady=(4, 0))
        self.settings = {}

        self.moduleCombo.set(defaultModule)
        self.OnModuleChanged()
        if defaultEquation in self.catalog.get(defaultModule, {}):
            self.equationCombo.set(defaultEquation)
            self.OnEquationChanged()


    def SelectedClassName(self):
        return self.catalog[self.moduleCombo.get()][self.equationCombo.get()]


    def OnModuleChanged(self):
        self.equationCombo['values'] = list(self.catalog[self.moduleCombo.get()].keys())
        self.equationCombo.current(0)
        self.OnEquationChanged()


    def OnEquationChanged(self):
        moduleName = self.moduleCombo.get()
        className = self.SelectedClassName()
        self.forms = EquationCatalog.AvailableForms(self.dim, moduleName, className)
        self.formCombo['values'] = [EquationCatalog.formLabels[f] for f in self.forms]
        self.formCombo.current(0)
        self.formCombo.config(state='readonly' if len(self.forms) > 1 else 'disabled')

        kind = EquationCatalog.SpecialKind(EquationCatalog.GetClass(self.dim, moduleName, className))
        previousKind = self.settings.get('kind', 'none')
        self.BuildSettings(kind)
        if kind != previousKind:
            # the settings area changed size - the window may need resizing
            self.event_generate('<<SettingsChanged>>')


    # ---- settings for special equation types ----

    def BuildSettings(self, kind):
        for child in self.settingsFrame.winfo_children():
            child.destroy()
        self.settings = {'kind': kind}
        f = self.settingsFrame
        if kind == 'polynomialOrder':
            self.settings['xOrder'] = self._Spinbox(f, 'X order:' if self.dim == 3 else 'Polynomial order:', 0,
                                                    EquationCatalog.maxPolynomialOrder[self.dim], 2)
            if self.dim == 3:
                self.settings['yOrder'] = self._Spinbox(f, 'Y order:', 0, EquationCatalog.maxPolynomialOrder[3], 2)
        elif kind == 'spline':
            tk.Label(f, text="Smoothing:").pack(side=tk.LEFT)
            entry = tk.Entry(f, width=8)
            entry.insert(0, '1.0')
            entry.pack(side=tk.LEFT, padx=(2, 4))
            self.settings['smoothing'] = entry
            self.settings['xOrder'] = self._Spinbox(f, 'X order:' if self.dim == 3 else 'Order:', 1, EquationCatalog.maxSplineOrder, 3)
            if self.dim == 3:
                self.settings['yOrder'] = self._Spinbox(f, 'Y order:', 1, EquationCatalog.maxSplineOrder, 3)
        elif kind == 'userFunction':
            tk.Label(f, text="Function:").pack(anchor=tk.W)
            entry = tk.Entry(f, width=60)
            entry.insert(0, 'a * X + b * exp(c * X)' if self.dim == 2 else 'a + b * X + c * Y')
            entry.pack(anchor=tk.W)
            self.settings['function'] = entry
            variables = 'X' if self.dim == 2 else 'X and Y'
            tk.Label(f, fg='gray30', justify=tk.LEFT,
                     text="Use %s for the data, letters such as a, b, c for coefficients, and\n"
                          "functions such as exp(), log(), sin(), sqrt() and pow()." % variables).pack(anchor=tk.W)
        elif kind == 'customPolynomial':
            terms = EquationCatalog.FunctionLists(self.dim, kind)[0]
            labels = [EquationCatalog.TermText(t) for t in terms]
            default = [i for i, l in enumerate(labels) if l in ('x^0', 'x^1', 'x', 'x^2')]
            self.settings['flags'] = self._TermList(f, 'Polynomial terms (click to select several):', labels, default)
        elif kind == 'polyfunctional':
            lists = EquationCatalog.FunctionLists(self.dim, kind)
            if self.dim == 2:
                labels = [EquationCatalog.TermText(t) for t in lists[0]]
                self.settings['flagValues'] = list(range(len(labels)))
                default = [i for i, l in enumerate(labels) if l in ('Offset', 'x')]
            else:
                pairs = [[i, j] for i in range(len(lists[0])) for j in range(len(lists[1]))]
                labels = [self._PairLabel(lists[0][i], lists[1][j]) for i, j in pairs]
                self.settings['flagValues'] = pairs
                default = [k for k, l in enumerate(labels) if l in ('Offset', 'x', 'y')]
            self.settings['flags'] = self._TermList(f, 'Terms, each with a coefficient (click to select several):', labels, default)
        elif kind == 'rational':
            terms = EquationCatalog.FunctionLists(self.dim, kind)[0]
            labels = [EquationCatalog.TermText(t) for t in terms]
            tk.Label(f, text="Click to select several terms.", fg='gray30').pack(anchor=tk.W)
            self.settings['numerator'] = self._TermList(f, 'Numerator terms:', labels,
                                                        [i for i, l in enumerate(labels) if l in ('Offset', 'x')], side=tk.LEFT)
            self.settings['denominator'] = self._TermList(f, 'Denominator: 1.0 + terms:', labels,
                                                          [i for i, l in enumerate(labels) if l == 'x'], side=tk.LEFT)


    def _Spinbox(self, parent, label, low, high, default):
        tk.Label(parent, text=label).pack(side=tk.LEFT)
        variable = tk.IntVar(value=default)
        tk.Spinbox(parent, from_=low, to=high, width=3, textvariable=variable, state='readonly').pack(side=tk.LEFT, padx=(2, 8))
        return variable


    def _TermList(self, parent, label, labels, defaultSelection, side=None):
        frame = tk.Frame(parent)
        frame.pack(side=side or tk.TOP, anchor=tk.NW, padx=(0, 8))
        tk.Label(frame, text=label).pack(anchor=tk.W)
        listFrame = tk.Frame(frame)
        listFrame.pack(anchor=tk.W)
        listbox = tk.Listbox(listFrame, selectmode=tk.MULTIPLE, height=5, width=24 if side else 40, exportselection=False)
        scroll = ttk.Scrollbar(listFrame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scroll.set)
        listbox.pack(side=tk.LEFT)
        scroll.pack(side=tk.LEFT, fill=tk.Y)
        for text in labels:
            listbox.insert(tk.END, text)
        for index in defaultSelection:
            listbox.selection_set(index)
        if defaultSelection:
            listbox.see(defaultSelection[0])
        return listbox


    @staticmethod
    def _PairLabel(xTerm, yTerm):
        x, y = EquationCatalog.TermText(xTerm), EquationCatalog.TermText(yTerm)
        if x == 'Offset' and y == 'Offset':
            return 'Offset'
        if x == 'Offset':
            return y
        if y == 'Offset':
            return x
        return x + ' * ' + y


    # ---- result ----

    def GetSpec(self):
        # returns the equation spec, or raises ValueError with a message
        spec = {'dim': self.dim, 'module': self.moduleCombo.get(), 'class': self.SelectedClassName(),
                'form': self.forms[self.formCombo.current()] if self.forms else 'Default', 'params': {}}
        params = spec['params']
        kind = self.settings.get('kind')
        if kind in ('polynomialOrder', 'spline'):
            params['xOrder'] = self.settings['xOrder'].get()
            if 'yOrder' in self.settings:
                params['yOrder'] = self.settings['yOrder'].get()
        if kind == 'spline':
            text = self.settings['smoothing'].get().strip()
            try:
                params['smoothing'] = float(text) if text else None
            except ValueError:
                raise ValueError('The spline smoothing must be a number, or blank for automatic smoothing.')
            if params['smoothing'] is not None and params['smoothing'] < 0.0:
                raise ValueError('The spline smoothing cannot be negative.')
        elif kind == 'userFunction':
            params['function'] = self.settings['function'].get()
        elif kind == 'customPolynomial':
            params['flags'] = list(self.settings['flags'].curselection())
        elif kind == 'polyfunctional':
            values = self.settings['flagValues']
            params['flags'] = [values[i] for i in self.settings['flags'].curselection()]
        elif kind == 'rational':
            params['numerator'] = list(self.settings['numerator'].curselection())
            params['denominator'] = list(self.settings['denominator'].curselection())
        return spec
