import queue
import pyeq3

import matplotlib # ensure this dependency imports for later use in fitting results

import tkinter as tk
import tkinter.ttk
from tkinter import ttk
from tkinter import messagebox as tk_mbox
import tkinter.scrolledtext as tk_stxt

import DataForControls as dfc
import FittingThread
import FittingResultsViewer
import FunctionFinder
import FunctionFinderResults
import ImportDataDialog
import EquationCatalog
import EquationSelector
import CollapsibleSection


class InterfaceFrame(tk.Frame):
    
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.queue = queue.Queue()
        # the fitting thread communicates with the GUI only through self.queue,
        # since tkinter widgets must not be accessed from other threads

        self.fittingTargetSelect_2D = tk.IntVar(value=0)
        self.fittingTargetSelect_3D = tk.IntVar(value=0)
        self.maxCoefficients = {2: tk.IntVar(value=FunctionFinder.defaultMaxCoefficients[2]),
                                3: tk.IntVar(value=FunctionFinder.defaultMaxCoefficients[3])}
        self.exactCoefficientCount = {2: tk.BooleanVar(value=False), 3: tk.BooleanVar(value=False)}
        self.functionFinderOptions = {2: FunctionFinder.FunctionFinderOptions(), 3: FunctionFinder.FunctionFinderOptions()}
        self.equationSelector = {}
        self.buttonFunctionFinder = {}
        self.sections = {}

        # 2D and 3D fitting are on separate tabs, each with collapsible
        # sections, so that the window fits on small screens
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        for dim, title, exampleText in [(2, "  2D Curve Fitting  ", dfc.exampleText_2D),
                                        (3, "  3D Surface Fitting  ", dfc.exampleText_3D)]:
            tab = tk.Frame(self.notebook, padx=10, pady=8)
            self.notebook.add(tab, text=title)
            self.BuildTab(tab, dim, exampleText)
        self.notebook.bind('<<NotebookTabChanged>>', lambda e: self.OnTabChanged())
        self.OnTabChanged()


    def OnTabChanged(self):
        # A notebook is normally as tall as its tallest tab.  Hidden tabs
        # request no space, so the window can fit the selected tab - for
        # example when its sections are collapsed.
        selected = self.notebook.select()
        for tabName in self.notebook.tabs():
            tab = self.notebook.nametowidget(tabName)
            if tabName == selected:
                tab.grid_propagate(True)
            else:
                tab.grid_propagate(False)
                tab.configure(width=1, height=1)
        self.after_idle(self.FitWindowToContents)


    def BuildTab(self, tab, dim, exampleText):
        sections = {}
        self.sections[dim] = sections

        # data - the editor fills any extra space when the window is resized
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        section = CollapsibleSection.CollapsibleSection(tab, "%dD Data" % dim, expanded=True, expandBody=True)
        section.grid(row=0, column=0, sticky='nsew')
        tk.Button(section.headerExtras, text="Import Data...", command=lambda: self.OnImportData(dim)).pack(side=tk.RIGHT)
        text = tk_stxt.ScrolledText(section.body, width=60, height=9, wrap=tk.NONE)
        text.insert(tk.END, exampleText) # inital text data
        text.pack(fill=tk.BOTH, expand=True)
        text.bind('<<Modified>>', lambda e: self.UpdateDataSummary(dim))
        sections['data'] = section
        if dim == 2:
            self.text_2D = text
        else:
            self.text_3D = text
        self.UpdateDataSummary(dim)

        # fitting target, used by both single equation fits and the function finder
        row = tk.Frame(tab)
        row.grid(row=1, column=0, sticky='ew', pady=(8, 6))
        tk.Label(row, text="Fitting target:", font="-weight bold").pack(side=tk.LEFT)
        combo = ttk.Combobox(row, state='readonly', width=52, values=dfc.fittingTargetList)
        combo.current(0)
        variable = self.fittingTargetSelect_2D if dim == 2 else self.fittingTargetSelect_3D
        combo.bind('<<ComboboxSelected>>', lambda e: variable.set(combo.current()))
        combo.pack(side=tk.LEFT, padx=(6, 0))

        # fitting one equation
        section = CollapsibleSection.CollapsibleSection(tab, "Fit One Equation", expanded=True)
        section.grid(row=2, column=0, sticky='ew', pady=(4, 0))
        selector = EquationSelector.EquationSelector(section.body, dim, 'Polynomial',
                                                     '1st Order (Linear)' if dim == 2 else 'Linear')
        selector.pack(anchor=tk.W, fill=tk.X)
        self.equationSelector[dim] = selector
        button = tk.Button(section.body, text="Fit %dD Data" % dim, width=16, command=lambda: self.OnFit(dim))
        button.pack(anchor=tk.W, pady=(6, 4))
        if dim == 2:
            self.buttonFit_2D = button
        else:
            self.buttonFit_3D = button
        sections['equation'] = section
        for widget in (selector.moduleCombo, selector.equationCombo, selector.formCombo):
            widget.bind('<<ComboboxSelected>>', lambda e: self.UpdateEquationSummary(dim), add='+')
        self.UpdateEquationSummary(dim)

        # the function finder, which fits the data to many equations
        section = CollapsibleSection.CollapsibleSection(tab, "Function Finder", expanded=True)
        section.grid(row=3, column=0, sticky='ew', pady=(6, 0))
        f = tk.Frame(section.body)
        f.pack(anchor=tk.W, pady=(0, 4))
        tk.Label(f, text="Coefficients:").pack(side=tk.LEFT)
        tk.Spinbox(f, from_=1, to=15, width=3, textvariable=self.maxCoefficients[dim], state='readonly').pack(side=tk.LEFT)
        tk.Radiobutton(f, text="maximum", variable=self.exactCoefficientCount[dim], value=False).pack(side=tk.LEFT)
        tk.Radiobutton(f, text="exact", variable=self.exactCoefficientCount[dim], value=True).pack(side=tk.LEFT)
        tk.Button(f, text="Options...", command=lambda: self.OnFunctionFinderOptions(dim)).pack(side=tk.LEFT, padx=(10, 0))
        b = tk.Button(f, text="Run Function Finder", command=lambda: self.OnFunctionFinder(dim))
        b.pack(side=tk.LEFT, padx=(6, 0))
        self.buttonFunctionFinder[dim] = b
        section.SetSummary("finds the best fitting equations")
        sections['finder'] = section

        # resize the window to fit when sections open or close, or when the
        # equation settings change size
        def OnDataToggled(event):
            # extra space goes to the data editor, or below the sections when it is hidden
            expanded = sections['data'].expanded
            tab.rowconfigure(0, weight=1 if expanded else 0)
            tab.rowconfigure(4, weight=0 if expanded else 1)
        sections['data'].bind('<<SectionToggled>>', OnDataToggled)
        for section in sections.values():
            section.bind('<<SectionToggled>>', lambda e: self.after_idle(self.FitWindowToContents), add='+')
        selector.bind('<<SettingsChanged>>', lambda e: self.after_idle(self.FitWindowToContents))


    def FitWindowToContents(self):
        # Set the window height to what the contents need, within the screen.
        # The data editor shrinks if the screen is too small.
        root = self.winfo_toplevel()
        if not root.winfo_ismapped():
            return
        root.update_idletasks()
        maxHeight = root.winfo_screenheight() - 100 # leave room for the taskbar
        height = min(root.winfo_reqheight(), maxHeight)
        width = max(root.winfo_width(), min(root.winfo_reqwidth(), root.winfo_screenwidth() - 40))
        if height != root.winfo_height() or width != root.winfo_width():
            root.geometry('%dx%d' % (width, height))


    def UpdateDataSummary(self, dim):
        # the number of data points, shown in the Data header when collapsed
        text = self.text_2D if dim == 2 else self.text_3D
        text.edit_modified(False)
        try:
            count = FunctionFinder.CountDataPoints(dim, text.get('1.0', tk.END))
            summary = '%d data points' % count
        except Exception:
            summary = 'no usable data'
        self.sections[dim]['data'].SetSummary(summary)


    def UpdateEquationSummary(self, dim):
        selector = self.equationSelector[dim]
        summary = selector.equationCombo.get()
        if selector.formCombo.current() > 0:
            summary += ' (' + selector.formCombo.get() + ')'
        self.sections[dim]['equation'].SetSummary(summary)


    def SelectedFittingTarget(self, dim):
        variable = self.fittingTargetSelect_2D if dim == 2 else self.fittingTargetSelect_3D
        fittingTargetSelection = dfc.fittingTargetList[variable.get()]
        # the GUI's fitting target string contains what we need - extract it
        return fittingTargetSelection, fittingTargetSelection.split('(')[1].split(')')[0]


    def OnFit(self, dim):
        textData = (self.text_2D if dim == 2 else self.text_3D).get("1.0", tk.END)
        fittingTargetSelection, fittingTarget = self.SelectedFittingTarget(dim)

        try:
            spec = self.equationSelector[dim].GetSpec()
            self.equation = EquationCatalog.CreateEquation(spec, fittingTarget)
        except ValueError as e:
            tk_mbox.showerror("Error", str(e))
            return
        except Exception as e:
            tk_mbox.showerror("Error", "This equation could not be created:\n\n" + repr(e))
            return

        # convert text to numeric data checking for log of negative numbers, etc.
        try:
            pyeq3.dataConvertorService().ConvertAndSortColumnarASCII(textData, self.equation, False)
        except:
            tk_mbox.showerror("Error", getattr(self.equation, 'reasonWhyDataRejected', '') or "The data could not be used with this equation.")
            return

        # check for number of coefficients > number of data points to be fitted
        dataCount = len(self.equation.dataCache.allDataCacheDictionary['DependentData'])
        if EquationCatalog.IsSpline(self.equation):
            params = spec['params']
            if dim == 2:
                required = params['xOrder'] + 1
            else:
                required = (params['xOrder'] + 1) * (params['yOrder'] + 1)
            if dataCount < required:
                tk_mbox.showerror("Error", "A spline of this order requires at least %d data points, you have supplied %d." % (required, dataCount))
                return
        else:
            coeffCount = len(self.equation.GetCoefficientDesignators())
            if coeffCount > dataCount:
                tk_mbox.showerror("Error", "This equation requires a minimum of " + str(coeffCount) + " data points, you have supplied " + repr(dataCount) + ".")
                return

        # Now the status dialog is used. Disable fitting buttons until thread completes
        self.SetFittingButtonsState(tk.DISABLED)

        # create simple top-level text dialog to display status as fitting progresses
        # when the fitting thread completes, it will close the status box
        self.statusBox = tk.Toplevel()
        self.statusBox.title("Fitting Status")
        self.statusBox.text = tk.Text(self.statusBox)
        self.statusBox.text.pack()

        # in tkinter the status box must be manually centered
        self.statusBox.update_idletasks()
        width = self.statusBox.winfo_width()
        height = self.statusBox.winfo_height()
        x = (self.statusBox.winfo_screenwidth() // 2) - (width // 2) # integer division
        y = (self.statusBox.winfo_screenheight() // 2) - (height // 2) # integer division
        self.statusBox.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        # thread will automatically start to run
        # the queue polling handler will re-enable buttons
        self.fittingWorkerThread = FittingThread.FittingThread(self, self.equation)
        self.after(100, self.StatusUpdateHandler)


    # Periodically check the queue for data from the fitting thread.
    # Text is displayed in the status box. Otherwise the queue data is
    # either the fitted equation or an exception raised during fitting.
    def StatusUpdateHandler(self):
        while True:
            try:
                data = self.queue.get_nowait()
            except queue.Empty:
                self.after(100, self.StatusUpdateHandler) # check again later
                return

            if isinstance(data, str): # text is used for status box display to user
                self.statusBox.text.insert(tk.END, data + '\n')
                continue

            # the fitting thread is finished - re-enable fitting buttons
            # and destroy the now-unused status box
            self.SetFittingButtonsState(tk.NORMAL)
            self.statusBox.destroy()

            if isinstance(data, BaseException):
                tk_mbox.showerror("Error", "Fitting failed:\n\n" + repr(data))
            else: # the queue data is now the fitted equation, view fitting results
                self.ShowResults(data)
            return


    def OnImportData(self, dim):
        textWidget = self.text_2D if dim == 2 else self.text_3D

        def ImportText(text, replaceFlag):
            if replaceFlag:
                textWidget.delete('1.0', tk.END)
            else:
                textWidget.insert(tk.END, '\n')
            textWidget.insert(tk.END, text)
            textWidget.see('1.0' if replaceFlag else tk.END)

        ImportDataDialog.ImportDataDialog(self, dim, ImportText)


    def SetFittingButtonsState(self, state):
        self.buttonFit_2D.config(state=state)
        self.buttonFit_3D.config(state=state)
        for button in self.buttonFunctionFinder.values():
            button.config(state=state)


    def OnFunctionFinder(self, dim):
        textData = (self.text_2D if dim == 2 else self.text_3D).get("1.0", tk.END)
        fittingTargetSelection, fittingTarget = self.SelectedFittingTarget(dim)
        maxCoefficients = self.maxCoefficients[dim].get()
        exactCount = self.exactCoefficientCount[dim].get()

        # check that the text contains usable data before starting
        try:
            dataCount = FunctionFinder.CountDataPoints(dim, textData)
        except Exception:
            dataCount = 0
        if dataCount < 2:
            tk_mbox.showerror("Error", "Could not find at least two %dD data points in the text." % dim)
            return

        self.SetFittingButtonsState(tk.DISABLED)
        try:
            self.functionFinderRun = FunctionFinder.FunctionFinderRun(dim, fittingTarget, textData, maxCoefficients, exactCount,
                                                                      self.functionFinderOptions[dim])
        except Exception as e:
            self.SetFittingButtonsState(tk.NORMAL)
            tk_mbox.showerror("Error", "Could not start the function finder:\n\n" + repr(e))
            return

        # status dialog with progress bar and cancel button
        self.ffStatus = tk.Toplevel(self)
        self.ffStatus.title("Function Finder %dD" % dim)
        self.ffStatus.resizable(False, False)
        self.ffStatus.protocol("WM_DELETE_WINDOW", self.OnFunctionFinderCancel)
        tk.Label(self.ffStatus, text="Fitting %d equations with %s %d coefficients to %d data points,\nusing %s" % (
                     self.functionFinderRun.total, 'exactly' if exactCount else 'up to', maxCoefficients,
                     dataCount, fittingTargetSelection),
                 justify=tk.LEFT).pack(padx=12, pady=(12, 4), anchor=tk.W)
        self.ffStatus.progress = ttk.Progressbar(self.ffStatus, length=460, mode='determinate',
                                                 maximum=max(self.functionFinderRun.total, 1))
        self.ffStatus.progress.pack(padx=12, pady=4)
        self.ffStatus.countLabel = tk.Label(self.ffStatus, text="Starting...", anchor=tk.W, width=70)
        self.ffStatus.countLabel.pack(padx=12, anchor=tk.W)
        self.ffStatus.bestLabel = tk.Label(self.ffStatus, text="", anchor=tk.W, width=70)
        self.ffStatus.bestLabel.pack(padx=12, anchor=tk.W)
        tk.Button(self.ffStatus, text="Cancel (show results so far)",
                  command=self.OnFunctionFinderCancel).pack(pady=(8, 12))

        self.ffStatus.update_idletasks()
        width = self.ffStatus.winfo_width()
        height = self.ffStatus.winfo_height()
        x = (self.ffStatus.winfo_screenwidth() // 2) - (width // 2) # integer division
        y = (self.ffStatus.winfo_screenheight() // 2) - (height // 2) # integer division
        self.ffStatus.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        self.after(200, self.FunctionFinderPoll)


    def FunctionFinderPoll(self):
        run = self.functionFinderRun
        done = run.Poll()

        if not done:
            self.ffStatus.progress['value'] = run.completed
            self.ffStatus.countLabel.config(text="%d of %d complete    %d fitted, %d skipped, %d failed" % (
                run.completed, run.total, len(run.fitted), len(run.skipped), len(run.failed)))
            best = run.BestSoFarDescription()
            if best:
                self.ffStatus.bestLabel.config(text="Best so far: " + best)
            self.after(200, self.FunctionFinderPoll)
            return

        self.FunctionFinderFinished()


    def OnFunctionFinderOptions(self, dim):
        def CurrentSettings():
            return self.SelectedFittingTarget(dim)[1], self.maxCoefficients[dim].get(), self.exactCoefficientCount[dim].get()
        FunctionFinderOptionsDialog(self, dim, self.functionFinderOptions[dim], CurrentSettings)


    def OnFunctionFinderCancel(self):
        self.functionFinderRun.Cancel() # FunctionFinderPoll will then finish up


    def FunctionFinderFinished(self):
        self.ffStatus.bestLabel.config(text="Calculating statistics for the best results...")
        self.ffStatus.update_idletasks()
        self.functionFinderRun.SortedResults() # calculates fit statistics
        self.ffStatus.destroy()
        self.SetFittingButtonsState(tk.NORMAL)
        window = FunctionFinderResults.FunctionFinderResultsWindow(self, self.functionFinderRun, self.ShowResults)
        window.update_idletasks()
        x = max(0, (window.winfo_screenwidth() - window.winfo_width()) // 2)
        y = max(0, (window.winfo_screenheight() - window.winfo_height()) // 3)
        window.geometry('+{}+{}'.format(x, y))


    def ShowResults(self, equation):
        resultsWindow = tk.Toplevel(self)
        resultsWindow.title("tkinterFit - Fitting Results Viewer")
        results = FittingResultsViewer.ResultsFrame(resultsWindow, equation)
        results.pack()

        # manually center the results window on the user display
        resultsWindow.update_idletasks()
        width = resultsWindow.winfo_width()
        height = resultsWindow.winfo_height()
        x = (resultsWindow.winfo_screenwidth() // 2) - (width // 2) # integer division
        y = (resultsWindow.winfo_screenheight() // 2) - (height // 2) # integer division
        resultsWindow.geometry('{}x{}+{}+{}'.format(width, height, x, y))



class FunctionFinderOptionsDialog(tk.Toplevel):
    # Chooses which equations the function finder tries, as on zunzunsite3,
    # and shows how many equations will be fitted.

    def __init__(self, parent, dim, options, currentSettingsFunction):
        tk.Toplevel.__init__(self, parent)
        self.title("Function Finder %dD Options" % dim)
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self.dim = dim
        self.options = options
        self.currentSettingsFunction = currentSettingsFunction

        tk.Label(self, text="Equations to try:", font="-weight bold").pack(anchor=tk.W, padx=12, pady=(12, 2))
        tk.Label(self, text="Standard forms of every equation: Default, With Offset, and Plus %s (always included)"
                 % ('Line' if dim == 2 else 'Plane'), fg='gray25').pack(anchor=tk.W, padx=24)

        self.polynomialOrders = tk.BooleanVar(value=options.polynomialOrders)
        tk.Checkbutton(self, text="Polynomials of every order (up to %d)" % EquationCatalog.maxPolynomialOrder[dim],
                       variable=self.polynomialOrders, command=self.OnChanged).pack(anchor=tk.W, padx=20)

        frame = tk.LabelFrame(self, text=" Extended forms of every equation (each also with offset) ")
        frame.pack(fill=tk.X, padx=12, pady=6)
        self.groups = {}
        for index, group in enumerate([g for g in EquationCatalog.formGroups if g != 'STANDARD']):
            variable = tk.BooleanVar(value=group in options.formGroups)
            self.groups[group] = variable
            tk.Checkbutton(frame, text=EquationCatalog.formGroupLabels[group], variable=variable,
                           command=self.OnChanged).grid(row=index // 2, column=index % 2, sticky=tk.W, padx=6)

        frame = tk.LabelFrame(self, text=" Combinations of functions ")
        frame.pack(fill=tk.X, padx=12, pady=(0, 6))
        self.polyfunctional = tk.BooleanVar(value=options.polyfunctional)
        tk.Checkbutton(frame, text="Polyfunctional: up to %d terms (sum of squared absolute error fitting target only)"
                       % FunctionFinder.maxPolyfunctionalTerms[dim],
                       variable=self.polyfunctional, command=self.OnChanged).pack(anchor=tk.W, padx=6)
        self.rational = tk.BooleanVar(value=options.rational)
        if dim == 2:
            tk.Checkbutton(frame, text="Rational: up to %d numerator and %d denominator terms (slow nonlinear fits)"
                           % (FunctionFinder.maxRationalTermsEach, FunctionFinder.maxRationalTermsEach),
                           variable=self.rational, command=self.OnChanged).pack(anchor=tk.W, padx=6)

        self.countLabel = tk.Label(self, text="", justify=tk.LEFT, fg='#804000')
        self.countLabel.pack(anchor=tk.W, padx=12, pady=6)
        tk.Button(self, text="Close", width=10, command=self.destroy).pack(pady=(0, 12))
        self.OnChanged()


    def OnChanged(self):
        self.options.polynomialOrders = self.polynomialOrders.get()
        self.options.formGroups = ['STANDARD'] + [g for g, v in self.groups.items() if v.get()]
        self.options.polyfunctional = self.polyfunctional.get()
        self.options.rational = self.rational.get() and self.dim == 2

        fittingTarget, maxCoefficients, exactCount = self.currentSettingsFunction()
        specs = FunctionFinder.ListEquationSpecs(self.dim, fittingTarget, maxCoefficients, exactCount, self.options)
        linear = sum(1 for spec in specs if spec[2])
        text = "With the current fitting target and %s %d coefficients, %d equations will be tried:\n" \
               "%d fast linear fits and %d slower nonlinear fits." % (
                   'exactly' if exactCount else 'up to', maxCoefficients, len(specs), linear, len(specs) - linear)
        if self.options.polyfunctional and fittingTarget != 'SSQABS':
            text += "\nPolyfunctionals are skipped: they need the sum of squared absolute error fitting target."
        self.countLabel.config(text=text)



def SizeWindowToScreen(root):
    # Center the window, limiting its size to the screen.  The window is
    # resizable, and the data editor uses any extra space.
    root.update_idletasks()
    screenWidth = root.winfo_screenwidth()
    screenHeight = root.winfo_screenheight()
    width = min(root.winfo_reqwidth(), screenWidth - 40)
    height = min(root.winfo_reqheight(), screenHeight - 100) # leave room for the taskbar
    x = max(0, (screenWidth - width) // 2)
    y = max(0, (screenHeight - height) // 3)
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    root.minsize(min(width, 480), 200)



if __name__ == "__main__":
    root = tk.Tk()
    interface = InterfaceFrame(root)
    interface.pack(fill=tk.BOTH, expand=True)
    root.title("tkinterFit - Curve And Surface Fitting Interface")
    SizeWindowToScreen(root)
    root.mainloop()
