# Displays the ranked function finder results, with fit parameters
# for each equation, and saves all of them to a single PDF file.

import threading, queue

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as tk_mbox
from tkinter import filedialog
import tkinter.scrolledtext as tk_stxt

import pyeq3
import IndividualReports
from FunctionFinderPDF import EquationFamily, FormatNumber


class FunctionFinderResultsWindow(tk.Toplevel):

    # columns: (identifier, heading, width, numeric sort)
    columns = [('rank', 'Rank', 45, True),
               ('equation', 'Equation', 260, False),
               ('family', 'Family', 110, False),
               ('coefs', 'Coefs', 45, True),
               ('target', 'Fitting Target', 115, True),
               ('r2', 'R-squared', 95, True),
               ('rmse', 'RMSE', 95, True),
               ('aic', 'AIC', 90, True),
               ('coefficients', 'Coefficient Values', 420, False)]

    def __init__(self, parent, run, showFullResultsCallback):
        tk.Toplevel.__init__(self, parent)
        self.run = run
        self.results = run.SortedResults()
        self.showFullResultsCallback = showFullResultsCallback
        self.title("tkinterFit - %dD Function Finder Results" % run.dim)

        targetName = pyeq3.IModel.IModel.fittingTargetDictionary[run.fittingTarget]
        summary = '%dD function finder, fitting target: %s (%s), %d data points, %s %d coefficients.\n' % (
            run.dim, targetName, run.fittingTarget, run.dataPointCount,
            'exactly' if run.exactCoefficientCount else 'maximum', run.maxCoefficients)
        summary += '%d equations fitted, %d skipped as not applicable to this data, %d failed to fit.' % (
            len(run.fitted), len(run.skipped), len(run.failed))
        if run.cancelled:
            summary += '\nCancelled by user - only %d of %d equations were tested.' % (run.completed, run.total)
        tk.Label(self, text=summary, justify=tk.LEFT, anchor=tk.W).pack(fill=tk.X, padx=8, pady=(8, 4))

        panes = ttk.PanedWindow(self, orient=tk.VERTICAL)
        panes.pack(fill=tk.BOTH, expand=True, padx=8)

        # the ranked results table
        tableFrame = tk.Frame(panes)
        self.tree = ttk.Treeview(tableFrame, columns=[c[0] for c in self.columns], show='headings',
                                 height=14, selectmode='browse')
        for identifier, heading, width, numeric in self.columns:
            self.tree.heading(identifier, text=heading, command=lambda c=identifier: self.SortByColumn(c))
            anchor = tk.E if numeric else tk.W
            self.tree.column(identifier, width=width, anchor=anchor, stretch=(identifier == 'coefficients'))
        vbar = ttk.Scrollbar(tableFrame, orient=tk.VERTICAL, command=self.tree.yview)
        hbar = ttk.Scrollbar(tableFrame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vbar.grid(row=0, column=1, sticky='ns')
        hbar.grid(row=1, column=0, sticky='ew')
        tableFrame.rowconfigure(0, weight=1)
        tableFrame.columnconfigure(0, weight=1)
        panes.add(tableFrame, weight=3)

        self.sortValues = {} # tree item id -> {column: sort value}
        for rank, equation in enumerate(self.results, 1):
            designators = equation.GetCoefficientDesignators()
            coefficientText = ',  '.join('%s = %.6E' % (d, c) for d, c in zip(designators, equation.solvedCoefficients))
            values = [rank, equation.GetDisplayName(), EquationFamily(equation), len(designators),
                      FormatNumber(equation.fittingTargetValue), FormatNumber(equation.r2, '%.8f'),
                      FormatNumber(equation.rmse), FormatNumber(equation.aic, '%.6f'), coefficientText]
            itemId = str(rank - 1) # index into self.results
            self.tree.insert('', tk.END, iid=itemId, values=values)
            self.sortValues[itemId] = {'rank': rank, 'equation': values[1], 'family': values[2], 'coefs': values[3],
                                       'target': equation.fittingTargetValue, 'r2': equation.r2,
                                       'rmse': equation.rmse, 'aic': equation.aic, 'coefficients': coefficientText}
        self.sortColumn = 'rank'
        self.sortReverse = False
        self.tree.bind('<<TreeviewSelect>>', self.OnSelect)
        self.tree.bind('<Double-1>', lambda event: self.OnViewFullResults())

        # details for the selected equation
        self.details = tk_stxt.ScrolledText(panes, width=100, height=14, wrap=tk.NONE)
        self.details.tag_configure("sup", offset=5) # superscript is +5 pixels
        self.details.tag_configure("sub", offset=-5) # subscript is -5 pixels
        self.details.tag_configure("bold", font='-weight bold')
        panes.add(self.details, weight=2)

        # buttons
        buttonFrame = tk.Frame(self)
        buttonFrame.pack(fill=tk.X, padx=8, pady=8)
        self.buttonView = tk.Button(buttonFrame, text="View Graphs And Reports For Selected Equation",
                                    command=self.OnViewFullResults)
        self.buttonView.pack(side=tk.LEFT)
        self.buttonPDF = tk.Button(buttonFrame, text="Save All Results To PDF...", command=self.OnSavePDF)
        self.buttonPDF.pack(side=tk.RIGHT)
        self.includeGraphs = tk.BooleanVar(value=True)
        tk.Checkbutton(buttonFrame, text="Include a graph for each equation in the PDF",
                       variable=self.includeGraphs).pack(side=tk.RIGHT, padx=8)

        if self.results:
            self.tree.selection_set('0')
            self.tree.focus('0')
        else:
            self.buttonView.config(state=tk.DISABLED)
            self.details.insert(tk.END, 'No equations could be fitted to this data.')


    def SelectedEquation(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self.results[int(selection[0])]


    def SortByColumn(self, column):
        if self.sortColumn == column:
            self.sortReverse = not self.sortReverse
        else:
            self.sortColumn = column
            self.sortReverse = False

        def SortKey(itemId):
            value = self.sortValues[itemId][column]
            if value is None: # missing values always sort last
                return (1, 0)
            return (0, value)
        items = sorted(self.tree.get_children(''), key=SortKey, reverse=self.sortReverse)
        if self.sortReverse: # keep missing values last when reversed
            items = [i for i in items if self.sortValues[i][column] is not None] + \
                    [i for i in items if self.sortValues[i][column] is None]
        for index, itemId in enumerate(items):
            self.tree.move(itemId, '', index)


    def OnSelect(self, event=None):
        equation = self.SelectedEquation()
        if equation is None:
            return
        rank = self.results.index(equation) + 1
        self.details.delete('1.0', tk.END)
        self.details.insert(tk.END, 'Rank %d: %s (%dD %s)\n' % (
            rank, equation.GetDisplayName(), equation.GetDimensionality(), EquationFamily(equation)), 'bold')
        IndividualReports.InsertEquationHTML(self.details, equation.GetDisplayHTML())
        self.details.insert(tk.END, '\n\nFitting target (%s): %s\n\n' % (
            equation.fittingTarget, FormatNumber(equation.fittingTargetValue, '%.16E')))
        self.details.insert(tk.END, IndividualReports.CoefficientAndFitStatisticsText(equation))


    def OnViewFullResults(self):
        equation = self.SelectedEquation()
        if equation is not None:
            self.showFullResultsCallback(equation)


    def OnSavePDF(self):
        if not self.results:
            tk_mbox.showerror("Error", "There are no fitted equations to save.", parent=self)
            return
        try:
            import reportlab
        except ImportError:
            tk_mbox.showerror("Error", "\nCould not import reportlab.\n\nPlease install using the command\n\n'pip install reportlab'", parent=self)
            return

        fileName = filedialog.asksaveasfilename(parent=self, defaultextension=".pdf",
                                                filetypes=(("PDF Files", "*.pdf"), ("All Files", "*.*")),
                                                title="PDF file name")
        if fileName:
            PDFProgressDialog(self, self.run, fileName, self.includeGraphs.get())



class PDFProgressDialog(tk.Toplevel):
    # Creates the PDF in a background thread, showing progress.  The dialog
    # is modal so that the fitted equations are not used elsewhere meanwhile.

    def __init__(self, parent, run, fileName, includeGraphs):
        tk.Toplevel.__init__(self, parent)
        self.title("Creating PDF")
        self.transient(parent)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.OnCancel)
        self.fileName = fileName

        self.label = tk.Label(self, text="Preparing...", width=50, anchor=tk.W)
        self.label.pack(padx=12, pady=(12, 4))
        self.progress = ttk.Progressbar(self, length=360, mode='determinate')
        self.progress.pack(padx=12, pady=4)
        self.buttonCancel = tk.Button(self, text="Cancel", command=self.OnCancel)
        self.buttonCancel.pack(pady=(4, 12))
        self.grab_set()

        self.queue = queue.Queue()
        self.cancelEvent = threading.Event()
        self.thread = threading.Thread(target=self.Worker, args=(run, fileName, includeGraphs), daemon=True)
        self.thread.start()
        self.after(100, self.Poll)


    def Worker(self, run, fileName, includeGraphs):
        # runs in the background thread - communicate only through the queue
        import FunctionFinderPDF
        def Progress(done, total, message):
            self.queue.put(('progress', done, total, message))
        try:
            FunctionFinderPDF.CreatePDF(fileName, run, includeGraphs, Progress, self.cancelEvent)
            self.queue.put(('done',))
        except FunctionFinderPDF.PDFCancelled:
            self.queue.put(('cancelled',))
        except Exception as e:
            self.queue.put(('error', repr(e)))


    def Poll(self):
        while True:
            try:
                item = self.queue.get_nowait()
            except queue.Empty:
                self.after(100, self.Poll)
                return
            if item[0] == 'progress':
                done, total, message = item[1:]
                self.progress['maximum'] = max(total, 1)
                self.progress['value'] = done
                self.label.config(text=message)
                continue

            parent = self.master
            self.grab_release()
            self.destroy()
            if item[0] == 'done':
                tk_mbox.showinfo("Success", "\nSuccessfully created PDF file.", parent=parent)
            elif item[0] == 'error':
                tk_mbox.showerror("Error", "Could not create the PDF file:\n\n" + item[1], parent=parent)
            return


    def OnCancel(self):
        self.cancelEvent.set()
        self.buttonCancel.config(state=tk.DISABLED)
        self.label.config(text="Cancelling...")
