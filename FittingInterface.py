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


class InterfaceFrame(tk.Frame):
    
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        
        self.queue = queue.Queue()

        self.equationSelect_2D = tk.IntVar()
        self.equationSelect_3D = tk.IntVar()
        self.fittingTargetSelect_2D = tk.IntVar()
        self.fittingTargetSelect_3D = tk.IntVar()

        # ROW 0 - empty labels as visual buffers
        row, col = (0, 0) # left edge
        l = tk.Label(self, text="   ")
        l.grid(column=col, row=row)
        row, col = (0, 2) # center
        l = tk.Label(self, text="     ")
        l.grid(column=col, row=row)
        row, col = (0, 4) # right edge
        l = tk.Label(self, text="   ")
        l.grid(column=col, row=row)
        
        # ROW 1 - text data entry labels, with buttons to import data from files
        for dim, col in [(2, 1), (3, 3)]:
            f = tk.Frame(self)
            f.grid(column=col, row=1)
            tk.Label(f, text="--- %dD Data Text Editor ---" % dim, font="-weight bold").pack(side=tk.LEFT)
            tk.Button(f, text="Import Data...", command=lambda d=dim: self.OnImportData(d)).pack(side=tk.LEFT, padx=(10, 0))

        # ROW 2 - text data input, no line wrap
        row, col = (2, 1)
        self.text_2D = tk_stxt.ScrolledText(self, width=45, height=12, wrap=tk.NONE)
        self.text_2D.insert(tk.END, dfc.exampleText_2D) # inital text data
        self.text_2D.grid(column=col, row=row, sticky=(tk.N, tk.W, tk.E, tk.S))

        row, col = (2, 3)
        self.text_3D = tk_stxt.ScrolledText(self, width=45, height=12, wrap=tk.NONE)
        self.text_3D.insert(tk.END, dfc.exampleText_3D) # inital text data
        self.text_3D.grid(column=col, row=row, sticky=(tk.N, tk.W, tk.E, tk.S))

        # ROW 3 - empty label as visual buffer
        row, col = (3, 0)
        l = tk.Label(self, text=" ")
        l.grid(column=col, row=row)

        # ROW 4 - equation selection labels
        # no "self" needed as no later references exist
        row, col = (4, 1)
        l = tk.Label(self, text="--- Standard 2D Equations ---", font="-weight bold")
        l.grid(column=col, row=row)
        
        row, col = (4, 3)
        l = tk.Label(self, text="--- Standard 3D Equations ---", font="-weight bold")
        l.grid(column=col, row=row)

        # ROW 5 - equation selection
        row, col = (5, 1)
        f = tk.Frame(self)
        f.grid(column=col, row=row)
        self.cb_Modules2D = tk.ttk.Combobox(f, state='readonly')
        self.cb_Modules2D['values'] = sorted(list(dfc.eq_od2D.keys()))
        self.cb_Modules2D.bind("<<ComboboxSelected>>", self.moduleSelectChanged_2D)
        self.cb_Modules2D.set('Polynomial')
        self.cb_Modules2D.pack(anchor=tk.W)

        self.cb_Equations2D = tk.ttk.Combobox(f, state='readonly')
        self.cb_Equations2D['width'] = 50
        self.cb_Equations2D['values'] = sorted(list(dfc.eq_od2D['Polynomial'].keys()))
        self.cb_Equations2D.set('1st Order (Linear)')
        self.cb_Equations2D.pack(anchor=tk.W)

        row, col = (5, 3)
        f = tk.Frame(self)
        f.grid(column=col, row=row)        
        self.cb_Modules3D = tk.ttk.Combobox(f, state='readonly')
        self.cb_Modules3D['values'] = sorted(list(dfc.eq_od3D.keys()))
        self.cb_Modules3D.bind("<<ComboboxSelected>>", self.moduleSelectChanged_3D)
        self.cb_Modules3D.set('Polynomial')
        self.cb_Modules3D.pack(anchor=tk.W)

        self.cb_Equations3D = tk.ttk.Combobox(f, state='readonly')
        self.cb_Equations3D['width'] = 50
        self.cb_Equations3D['values'] = sorted(list(dfc.eq_od3D['Polynomial'].keys()))
        self.cb_Equations3D.set('Linear')
        self.cb_Equations3D.pack(anchor=tk.W)

        # ROW 6 - empty label as visual buffer
        row, col = (6, 0)
        l = tk.Label(self, text=" ")
        l.grid(column=col, row=row)

        # ROW 7 - fitting target selection labels
        # no "self" needed as no later references exist
        row, col = (7, 1)
        l = tk.Label(self, text="--- Fitting Target 2D ---", font="-weight bold")
        l.grid(column=col, row=row)
        
        row, col = (7, 3)
        l = tk.Label(self, text="--- Fitting Target 3D ---", font="-weight bold")
        l.grid(column=col, row=row)

        # ROW 8 - fitting target selection radio buttons
        row, col = (8, 1)
        f = tk.Frame(self)
        f.grid(column=col, row=row)        
        index=0
        for fittingTargetText in dfc.fittingTargetList:
            rb = tk.Radiobutton(f, text=fittingTargetText, variable=self.fittingTargetSelect_2D, value=index)
            rb.pack(anchor=tk.W)
            index += 1

        row, col = (8, 3)
        f = tk.Frame(self)
        f.grid(column=col, row=row)        
        index=0
        for fittingTargetText in dfc.fittingTargetList:
            rb = tk.Radiobutton(f, text=fittingTargetText, variable=self.fittingTargetSelect_3D, value=index)
            rb.pack(anchor=tk.W)
            index += 1
    
            # ROW 9 - empty label as visual buffer
            row, col = (9, 0)
            l = tk.Label(self, text=" ")
            l.grid(column=col, row=row)
    
        # ROW 10 - fitting buttons
        row, col = (10, 1)
        self.buttonFit_2D = tk.Button(self, text="Fit 2D Text Data", command=self.OnFit_2D)
        self.buttonFit_2D.grid(column=col, row=row)
    
        row, col = (10, 3)
        self.buttonFit_3D = tk.Button(self, text="Fit 3D Text Data", command=self.OnFit_3D)
        self.buttonFit_3D.grid(column=col, row=row)

        # ROW 11 - empty label as visual buffer
        row, col = (11, 0)
        l = tk.Label(self, text=" ")
        l.grid(column=col, row=row)

        # ROW 12 - function finder, which fits the data to all standard equations
        self.maxCoefficients = {2: tk.IntVar(value=FunctionFinder.defaultMaxCoefficients[2]),
                                3: tk.IntVar(value=FunctionFinder.defaultMaxCoefficients[3])}
        self.exactCoefficientCount = {2: tk.BooleanVar(value=False), 3: tk.BooleanVar(value=False)}
        self.buttonFunctionFinder = {}
        for dim, col in [(2, 1), (3, 3)]:
            f = tk.Frame(self)
            f.grid(column=col, row=12)
            tk.Label(f, text="Coefficients:").pack(side=tk.LEFT)
            tk.Spinbox(f, from_=1, to=15, width=3, textvariable=self.maxCoefficients[dim], state='readonly').pack(side=tk.LEFT)
            tk.Radiobutton(f, text="maximum", variable=self.exactCoefficientCount[dim], value=False).pack(side=tk.LEFT)
            tk.Radiobutton(f, text="exact", variable=self.exactCoefficientCount[dim], value=True).pack(side=tk.LEFT)
            b = tk.Button(f, text="Function Finder %dD" % dim, command=lambda d=dim: self.OnFunctionFinder(d))
            b.pack(side=tk.LEFT, padx=(8, 0))
            self.buttonFunctionFinder[dim] = b

        # ROW 13 - empty label as visual buffer
        row, col = (13, 0)
        l = tk.Label(self, text=" ")
        l.grid(column=col, row=row)

        # the fitting thread communicates with the GUI only through self.queue,
        # since tkinter widgets must not be accessed from other threads


    def moduleSelectChanged_2D(self, event):
        self.cb_Equations2D['values'] = sorted(list(dfc.eq_od2D[event.widget.get()].keys()))
        self.cb_Equations2D.current(0)


    def moduleSelectChanged_3D(self, event):
        self.cb_Equations3D['values'] = sorted(list(dfc.eq_od3D[event.widget.get()].keys()))
        self.cb_Equations3D.current(0)


    def OnFit_2D(self):
        textData = self.text_2D.get("1.0", tk.END)
        moduleSelection = self.cb_Modules2D.get()
        equationSelection = self.cb_Equations2D.get()
        fittingTargetSelection = dfc.fittingTargetList[self.fittingTargetSelect_2D.get()]
        
        # the GUI's fitting target string contains what we need - extract it
        fittingTarget = fittingTargetSelection.split('(')[1].split(')')[0]

        item = dfc.eq_od2D[moduleSelection][equationSelection]
        equationClass = getattr(getattr(pyeq3.Models_2D, moduleSelection), item[0])
        self.equation = equationClass(fittingTarget, item[1])

        # convert text to numeric data checking for log of negative numbers, etc.
        try:
            pyeq3.dataConvertorService().ConvertAndSortColumnarASCII(textData, self.equation, False)
        except:
            tk_mbox.showerror("Error", self.equation.reasonWhyDataRejected)
            return

        # check for number of coefficients > number of data points to be fitted
        coeffCount = len(self.equation.GetCoefficientDesignators())
        dataCount = len(self.equation.dataCache.allDataCacheDictionary['DependentData'])
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


    def OnFit_3D(self):
        textData = self.text_3D.get("1.0", tk.END)
        moduleSelection = self.cb_Modules3D.get()
        equationSelection = self.cb_Equations3D.get()
        fittingTargetSelection = dfc.fittingTargetList[self.fittingTargetSelect_3D.get()]
        
        # the GUI's fitting target string contains what we need - extract it
        fittingTarget = fittingTargetSelection.split('(')[1].split(')')[0]

        item = dfc.eq_od3D[moduleSelection][equationSelection]
        equationClass = getattr(getattr(pyeq3.Models_3D, moduleSelection), item[0])
        self.equation = equationClass(fittingTarget, item[1])

        # convert text to numeric data checking for log of negative numbers, etc.
        try:
            pyeq3.dataConvertorService().ConvertAndSortColumnarASCII(textData, self.equation, False)
        except:
            tk_mbox.showerror("Error", self.equation.reasonWhyDataRejected)
            return

        # check for number of coefficients > number of data points to be fitted
        coeffCount = len(self.equation.GetCoefficientDesignators())
        dataCount = len(self.equation.dataCache.allDataCacheDictionary['DependentData'])
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
        if dim == 2:
            textData = self.text_2D.get("1.0", tk.END)
            fittingTargetSelection = dfc.fittingTargetList[self.fittingTargetSelect_2D.get()]
        else:
            textData = self.text_3D.get("1.0", tk.END)
            fittingTargetSelection = dfc.fittingTargetList[self.fittingTargetSelect_3D.get()]
        maxCoefficients = self.maxCoefficients[dim].get()
        exactCount = self.exactCoefficientCount[dim].get()

        # the GUI's fitting target string contains what we need - extract it
        fittingTarget = fittingTargetSelection.split('(')[1].split(')')[0]

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
            self.functionFinderRun = FunctionFinder.FunctionFinderRun(dim, fittingTarget, textData, maxCoefficients, exactCount)
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
            best = run.BestSoFar()
            if best is not None:
                self.ffStatus.bestLabel.config(text="Best so far: %s (%s = %.6E)" % (
                    best.GetDisplayName(), run.fittingTarget, best.fittingTargetValue))
            self.after(200, self.FunctionFinderPoll)
            return

        self.FunctionFinderFinished()


    def OnFunctionFinderCancel(self):
        self.functionFinderRun.Cancel() # FunctionFinderPoll will then finish up


    def FunctionFinderFinished(self):
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



if __name__ == "__main__":
    root = tk.Tk()
    interface = InterfaceFrame(root)
    interface.pack()
    root.title("tkinterFit - Curve And Surface Fitting Interface")
    
    # manually center the application window on the user display
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2) # integer division
    y = (root.winfo_screenheight() // 2) - (height // 2) # integer division
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))        
    
    root.mainloop()
