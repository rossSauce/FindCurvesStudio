import pickle
import pyeq3

import tkinter as tk
from tkinter import ttk as ttk
from tkinter import messagebox as tk_mbox
import tkinter.scrolledtext as tk_stxt
from tkinter import filedialog as filedialog

import IndividualReports
import Tooltips
import AdditionalInfo


class ResultsFrame(tk.Frame):
    
    # 'equation' is either a fitted pyeq3 equation object, or the
    # file name of a pickled fitted equation
    def __init__(self, parent, equation):
        tk.Frame.__init__(self, parent)

        self.graphReportsListForPDF = []
        self.textReportsListForPDF = []
        self.sourceCodeReportsListForPDF = []

        # first, load the fitted equation if a file name was passed in
        if isinstance(equation, str):
            with open(equation, 'rb') as equationFile:
                self.equation = pickle.load(equationFile)
        else:
            self.equation = equation
        
        topLevelNotebook = ttk.Notebook(self)
        topLevelNotebook.pack()

        # the "graph reports" notebook tab
        nbGraphReports = ttk.Notebook(topLevelNotebook)
        nbGraphReports.pack()
        topLevelNotebook.add(nbGraphReports, text='Graph Reports')

        if self.equation.GetDimensionality() == 2:
            report = IndividualReports.ModelScatterConfidenceGraph(nbGraphReports, self.equation, scatterplotOnlyFlag=False)
            reportTitle = "Model With 95% Confidence"
            nbGraphReports.add(report[0], text=reportTitle)
            self.graphReportsListForPDF.append([report[1], reportTitle])

            report = IndividualReports.ModelScatterConfidenceGraph(nbGraphReports, self.equation, scatterplotOnlyFlag=True)
            reportTitle = "Scatter Plot"
            nbGraphReports.add(report[0], text=reportTitle)
            self.graphReportsListForPDF.append([report[1], reportTitle])
        else:
            report = IndividualReports.SurfacePlot(nbGraphReports, self.equation)
            reportTitle = "Surface Plot"
            nbGraphReports.add(report[0], text=reportTitle)
            self.graphReportsListForPDF.append([report[1], reportTitle])
            
            report = IndividualReports.ContourPlot(nbGraphReports, self.equation)
            reportTitle = "Contour Plot"
            nbGraphReports.add(report[0], text=reportTitle)
            self.graphReportsListForPDF.append([report[1], reportTitle])

            report = IndividualReports.ScatterPlot(nbGraphReports, self.equation)
            reportTitle = "Scatter Plot"
            nbGraphReports.add(report[0], text=reportTitle)
            self.graphReportsListForPDF.append([report[1], reportTitle])

        report = IndividualReports.AbsoluteErrorGraph(nbGraphReports, self.equation)
        reportTitle = "Absolute Error"
        nbGraphReports.add(report[0], text=reportTitle)
        self.graphReportsListForPDF.append([report[1], reportTitle])

        report = IndividualReports.AbsoluteErrorHistogram(nbGraphReports, self.equation)
        reportTitle = "Absolute Error Histogram"
        nbGraphReports.add(report[0], text=reportTitle)
        self.graphReportsListForPDF.append([report[1], reportTitle])

        if self.equation.dataCache.DependentDataContainsZeroFlag != 1:
            report = IndividualReports.PercentErrorGraph(nbGraphReports, self.equation)
            reportTitle = "Percent Error"
            nbGraphReports.add(report[0], text=reportTitle)
            self.graphReportsListForPDF.append([report[1], reportTitle])

            report = IndividualReports.PercentErrorHistogram(nbGraphReports, self.equation)
            reportTitle = "Percent Error Histogram"
            nbGraphReports.add(report[0], text=reportTitle)
            self.graphReportsListForPDF.append([report[1], reportTitle])


        # the "text reports" notebook tab
        nbTextReports = ttk.Notebook(topLevelNotebook)
        nbTextReports.pack()
        topLevelNotebook.add(nbTextReports, text='Text Reports')
                
        report = IndividualReports.CoefficientAndFitStatistics(nbTextReports, self.equation)
        reportTitle = "Coefficient And Fit Statistics"
        nbTextReports.add(report, text=reportTitle)
        self.textReportsListForPDF.append([report.get("1.0", tk.END), reportTitle])
        
        report = IndividualReports.CoefficientListing(nbTextReports, self.equation)
        reportTitle = "Coefficient Listing"
        nbTextReports.add(report, text=reportTitle)
        self.textReportsListForPDF.append([report.get("1.0", tk.END), reportTitle])

        report = IndividualReports.DataArrayStatisticsReport(nbTextReports, 'Absolute Error Statistics', self.equation.modelAbsoluteError)
        reportTitle = "Absolute Error Statistics"
        nbTextReports.add(report, text=reportTitle)
        self.textReportsListForPDF.append([report.get("1.0", tk.END), reportTitle])
        
        if self.equation.dataCache.DependentDataContainsZeroFlag != 1:
            report = IndividualReports.DataArrayStatisticsReport(nbTextReports, 'Percent Error Statistics', self.equation.modelPercentError)
            reportTitle = "Percent Error Statistics"
            nbTextReports.add(report, text=reportTitle)
            self.textReportsListForPDF.append([report.get("1.0", tk.END), reportTitle])

        # the "source code" notebook tab
        nbSourceCodeReports = ttk.Notebook(topLevelNotebook)
        nbSourceCodeReports.pack()
        topLevelNotebook.add(nbSourceCodeReports, text='Source Code')
                    
        report = IndividualReports.SourceCodeReport(nbSourceCodeReports, self.equation, 'CPP')
        reportTitle = "C++"
        nbSourceCodeReports.add(report, text=reportTitle)
        self.sourceCodeReportsListForPDF.append([report.get("1.0", tk.END), reportTitle + " Source Code"])
    
        report = IndividualReports.SourceCodeReport(nbSourceCodeReports, self.equation,'CSHARP')
        reportTitle = "CSHARP"
        nbSourceCodeReports.add(report, text=reportTitle)
        self.sourceCodeReportsListForPDF.append([report.get("1.0", tk.END), reportTitle + " Source Code"])
    
        report = IndividualReports.SourceCodeReport(nbSourceCodeReports, self.equation,'VBA')
        reportTitle = "VBA"
        nbSourceCodeReports.add(report, text=reportTitle)
        self.sourceCodeReportsListForPDF.append([report.get("1.0", tk.END), reportTitle + " Source Code"])
    
        report = IndividualReports.SourceCodeReport(nbSourceCodeReports, self.equation,'PYTHON')
        reportTitle = "PYTHON"
        nbSourceCodeReports.add(report, text=reportTitle)
        self.sourceCodeReportsListForPDF.append([report.get("1.0", tk.END), reportTitle + " Source Code"])
    
        report = IndividualReports.SourceCodeReport(nbSourceCodeReports, self.equation,'JAVA')
        reportTitle = "JAVA"
        nbSourceCodeReports.add(report, text=reportTitle)
        self.sourceCodeReportsListForPDF.append([report.get("1.0", tk.END), reportTitle + " Source Code"])
    
        report = IndividualReports.SourceCodeReport(nbSourceCodeReports, self.equation,'JAVASCRIPT')
        reportTitle = "JAVASCRIPT"
        nbSourceCodeReports.add(report, text=reportTitle)
        self.sourceCodeReportsListForPDF.append([report.get("1.0", tk.END), reportTitle + " Source Code"])
    
        report = IndividualReports.SourceCodeReport(nbSourceCodeReports, self.equation,'JULIA')
        reportTitle = "JULIA"
        nbSourceCodeReports.add(report, text=reportTitle)
        self.sourceCodeReportsListForPDF.append([report.get("1.0", tk.END), reportTitle + " Source Code"])
    
        report = IndividualReports.SourceCodeReport(nbSourceCodeReports, self.equation,'SCILAB')
        reportTitle = "SCILAB"
        nbSourceCodeReports.add(report, text=reportTitle)
        self.sourceCodeReportsListForPDF.append([report.get("1.0", tk.END), reportTitle + " Source Code"])
    
        report = IndividualReports.SourceCodeReport(nbSourceCodeReports, self.equation,'MATLAB')
        reportTitle = "MATLAB"
        nbSourceCodeReports.add(report, text=reportTitle)
        self.sourceCodeReportsListForPDF.append([report.get("1.0", tk.END), reportTitle + " Source Code"])
    
        report = IndividualReports.SourceCodeReport(nbSourceCodeReports, self.equation,'FORTRAN90')
        reportTitle = "FORTRAN90"
        nbSourceCodeReports.add(report, text=reportTitle)
        self.sourceCodeReportsListForPDF.append([report.get("1.0", tk.END), reportTitle + " Source Code"])

        # the "additional information" notebook tab
        nbAdditionalInfo = ttk.Notebook(topLevelNotebook)
        nbAdditionalInfo.pack()
        topLevelNotebook.add(nbAdditionalInfo, text='Additional Information')
                
        scrolledText = tk_stxt.ScrolledText(nbAdditionalInfo, width=IndividualReports.textboxWidth, height=IndividualReports.textboxHeight, wrap=tk.WORD)
        nbAdditionalInfo.add(scrolledText, text="Fitting History")
        scrolledText.insert(tk.END, AdditionalInfo.history)

        scrolledText = tk_stxt.ScrolledText(nbAdditionalInfo, width=IndividualReports.textboxWidth, height=IndividualReports.textboxHeight, wrap=tk.WORD)
        nbAdditionalInfo.add(scrolledText, text="Maintainer And Author")
        scrolledText.insert(tk.END, AdditionalInfo.author)

        scrolledText = tk_stxt.ScrolledText(nbAdditionalInfo, width=IndividualReports.textboxWidth, height=IndividualReports.textboxHeight, wrap=tk.WORD)
        nbAdditionalInfo.add(scrolledText, text="Web Links")
        scrolledText.insert(tk.END, AdditionalInfo.links)

        # the "list of all standard equations" notebook tab
        dim = self.equation.GetDimensionality()
        allEquations = IndividualReports.AllEquationReport(topLevelNotebook, dim)
        allEquations.pack()
        topLevelNotebook.add(allEquations, text="List Of All Standard " + str(dim) + "D Equations")

        # the "Save To PDF" tab
        fsaveFrame = tk.Frame(self)
            
        # this label is only for visual spacing
        l = tk.Label(fsaveFrame, text="\n\n\n")
        l.pack()

        buttonSavePDF = tk.Button(fsaveFrame, text="Save To PDF", command=self.createPDF, height=0, width=0)
        buttonSavePDF.pack()
        topLevelNotebook.add(fsaveFrame, text="Save To PDF File")
        Tooltips.Add(buttonSavePDF, "Save the graphs, reports and source code to a PDF file.")

        sourceCodeTip = ("The fitted equation, with its coefficient values, as a function in this programming "
                         "language - ready to use in your own programs.")
        Tooltips.AddToTabTitles(topLevelNotebook, {
            'Graph Reports': "Graphs of the fitted equation and of its errors.",
            'Text Reports': "The coefficients, and statistics describing how well the equation fits.",
            'Source Code': "The fitted equation as code in ten programming languages.",
            'Additional Information': "About FindCurves Studio and its authors, and useful web links.",
            "List Of All Standard " + str(dim) + "D Equations": "Every standard equation available, by family.",
            'Save To PDF File': "Save these results to a PDF file."})
        Tooltips.AddToTabTitles(nbGraphReports, {
            'Model With 95% Confidence': "The fitted curve with your data.  It should follow the data, "
                                         "including between and at the ends of the points.  The dashed lines "
                                         "show the 95% confidence intervals of the fitted curve.",
            'Scatter Plot': "Your data points, without the fitted equation.",
            'Surface Plot': "The fitted surface with your data points.",
            'Contour Plot': "Contours of the fitted surface, seen from above, with your data points.",
            'Absolute Error': "The error at each data point: the predicted value minus the actual value.  "
                              "A good fit shows the errors scattered randomly around zero.  A pattern, such as "
                              "a curve or a funnel shape, means the equation misses something about the data.",
            'Absolute Error Histogram': "How many data points have each size of error.  For a good fit with "
                                        "random measurement errors this is usually roughly bell shaped, "
                                        "centered on zero.",
            'Percent Error': "The error at each data point as a percentage of the actual value.  Useful when the "
                             "data spans a wide range of values.",
            'Percent Error Histogram': "How many data points have each size of percent error."})
        Tooltips.AddToTabTitles(nbTextReports, {
            'Coefficient And Fit Statistics': "How well the equation fits (R-squared, RMSE and more), and for "
                                              "each coefficient its standard error, t-statistic, p-value and "
                                              "95% confidence interval.  A standard error that is large compared "
                                              "with its coefficient means the data cannot pin that coefficient "
                                              "down - a simpler equation may be better.",
            'Coefficient Listing': "The fitted coefficient values, with full precision.",
            'Absolute Error Statistics': "Statistics of the errors: the predicted values minus the actual values.",
            'Percent Error Statistics': "Statistics of the errors as percentages of the actual values."})
        Tooltips.AddToTabTitles(nbSourceCodeReports, {title: sourceCodeTip for title in
            ['C++', 'CSHARP', 'VBA', 'PYTHON', 'JAVA', 'JAVASCRIPT', 'JULIA', 'SCILAB', 'MATLAB', 'FORTRAN90']})


    def createPDF(self):
        try:
            import reportlab
        except ImportError:
            tk_mbox.showerror("Error", "\nCould not import reportlab.\n\nPlease install using the command\n\n'pip install reportlab'", parent=self)
            return

        fName = filedialog.asksaveasfilename(
                                parent = self,
                                defaultextension = ".pdf",
                                filetypes =(("PDF Files", "*.pdf"),("All Files","*.*")),
                                title = "PDF file name"
                                )
        if fName:
            import pdfCode
            pdfCode.CreatePDF(fName,
                              self.equation,
                              self.graphReportsListForPDF,
                              self.textReportsListForPDF,
                              self.sourceCodeReportsListForPDF
                              )
            tk_mbox.showinfo("Success", "\nSuccessfully created PDF file.", parent=self)



if __name__ == "__main__":
    root = tk.Tk()
    interface = ResultsFrame(root, 'pickledEquationFile')
    interface.pack()
    root.title("FindCurves Studio - Fitting Results")
    
    # manually center the application window on the user display
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2) # integer division
    y = (root.winfo_screenheight() // 2) - (height // 2) # integer division
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))        
        
    root.mainloop()
