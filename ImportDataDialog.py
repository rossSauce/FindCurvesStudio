# The Import Data dialog: imports data into the 2D or 3D data text editor
# from CSV/text files and Microsoft Excel workbooks, or (2D only) by
# digitizing data points from an image of a graph.

import os, sys

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as tk_mbox
from tkinter import filedialog

import DataImport
import Tooltips
import Theme


class ImportDataDialog(tk.Toplevel):

    def __init__(self, parent, dim, importCallback):
        # importCallback(text, replaceFlag) puts the imported text in the editor
        tk.Toplevel.__init__(self, parent)
        self.dim = dim
        self.importCallback = importCallback
        self.title("Import %dD Data" % dim)
        self.transient(parent.winfo_toplevel())

        # the buttons are packed first so they always stay visible
        buttonFrame = tk.Frame(self)
        buttonFrame.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=(4, 8))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))
        self.spreadsheetTab = SpreadsheetTab(self.notebook, dim)
        self.notebook.add(self.spreadsheetTab, text="CSV / Excel File")
        self.imageTab = None
        if dim == 2:
            self.imageTab = GraphImageTab(self.notebook)
            self.notebook.add(self.imageTab, text="Digitize Graph Image")
        Tooltips.AddToTabs(self.notebook, [
            "Read columns of numbers from a CSV, text or Excel file.",
            "Read data points from a picture of a graph, such as a scan or a figure from a paper."])

        self.replaceFlag = tk.BooleanVar(value=True)
        Tooltips.Add(tk.Radiobutton(buttonFrame, text="Replace the existing data", variable=self.replaceFlag, value=True),
                     "The imported points replace everything in the data area.").pack(side=tk.LEFT)
        Tooltips.Add(tk.Radiobutton(buttonFrame, text="Add to the existing data", variable=self.replaceFlag, value=False),
                     "The imported points are added after the data already in the data area.").pack(side=tk.LEFT)
        tk.Button(buttonFrame, text="Cancel", width=10, command=self.destroy).pack(side=tk.RIGHT)
        Tooltips.Add(tk.Button(buttonFrame, text="Import", width=10, command=self.OnImport),
                     "Put the selected data points in the main window's data area.").pack(side=tk.RIGHT, padx=6)

        self.geometry('1000x720' if dim == 2 else '820x560')
        self.minsize(720, 480)


    def OnImport(self):
        tab = self.notebook.nametowidget(self.notebook.select())
        error, points, description = tab.GetPoints()
        if error:
            tk_mbox.showerror("Import Data", error, parent=self)
            return
        self.importCallback(DataImport.FormatDataText(points, self.dim, description), self.replaceFlag.get())
        self.destroy()



class SpreadsheetTab(tk.Frame):

    maxPreviewRows = 500
    maxPreviewColumns = 40

    def __init__(self, parent, dim):
        tk.Frame.__init__(self, parent)
        self.dim = dim
        self.tables = {}
        self.rows = []
        self.fileName = ''
        self.axisNames = ['X', 'Y', 'Z'][:dim]

        top = tk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=8)
        Tooltips.Add(tk.Button(top, text="Open File...", command=self.OnOpen),
                     "Choose a CSV, text or Excel file.  Its contents are shown below, so you can choose "
                     "the columns to import.").pack(side=tk.LEFT)
        self.fileLabel = tk.Label(top, text="CSV, text (.csv .txt .tsv .dat) or Excel (.xlsx .xlsm .xls) files", anchor=tk.W, fg=Theme.muted)
        self.fileLabel.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)

        options = tk.Frame(self)
        options.pack(fill=tk.X, padx=8)
        sheetTip = "For Excel files with several worksheets, the worksheet to read."
        Tooltips.Add(tk.Label(options, text="Sheet:"), sheetTip).pack(side=tk.LEFT)
        self.sheetCombo = ttk.Combobox(options, state='disabled', width=24)
        Tooltips.Add(self.sheetCombo, sheetTip)
        self.sheetCombo.pack(side=tk.LEFT, padx=(2, 12))
        self.sheetCombo.bind('<<ComboboxSelected>>', lambda e: self.OnSheetChanged())
        self.headerFlag = tk.BooleanVar(value=False)
        Tooltips.Add(tk.Checkbutton(options, text="First row contains column names", variable=self.headerFlag,
                                    command=self.OnHeaderChanged),
                     "Use the first row as names for the columns, rather than as data.").pack(side=tk.LEFT)

        columns = tk.Frame(self)
        columns.pack(fill=tk.X, padx=8, pady=6)
        self.columnCombos = []
        for name in self.axisNames:
            columnTip = "The column holding the %s values.  Rows without a number in every chosen column are skipped." % name
            Tooltips.Add(tk.Label(columns, text="%s column:" % name), columnTip).pack(side=tk.LEFT)
            combo = ttk.Combobox(columns, state='disabled', width=22)
            Tooltips.Add(combo, columnTip)
            combo.pack(side=tk.LEFT, padx=(2, 12))
            combo.bind('<<ComboboxSelected>>', lambda e: self.UpdateSummary())
            self.columnCombos.append(combo)

        previewFrame = tk.Frame(self)
        previewFrame.pack(fill=tk.BOTH, expand=True, padx=8)
        self.preview = ttk.Treeview(previewFrame, show='headings', height=12)
        vbar = ttk.Scrollbar(previewFrame, orient=tk.VERTICAL, command=self.preview.yview)
        hbar = ttk.Scrollbar(previewFrame, orient=tk.HORIZONTAL, command=self.preview.xview)
        self.preview.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.preview.grid(row=0, column=0, sticky='nsew')
        vbar.grid(row=0, column=1, sticky='ns')
        hbar.grid(row=1, column=0, sticky='ew')
        previewFrame.rowconfigure(0, weight=1)
        previewFrame.columnconfigure(0, weight=1)

        self.summaryLabel = tk.Label(self, text="", anchor=tk.W, justify=tk.LEFT)
        self.summaryLabel.pack(fill=tk.X, padx=8, pady=6)


    def OnOpen(self):
        fileName = filedialog.askopenfilename(parent=self, title="Open Data File", filetypes=DataImport.spreadsheetFileTypes)
        if not fileName:
            return
        try:
            tables = DataImport.ReadTables(fileName)
        except Exception as e:
            tk_mbox.showerror("Import Data", "Could not read the file:\n\n%s\n\n%s" % (fileName, e), parent=self)
            return
        if not any(tables.values()):
            tk_mbox.showerror("Import Data", "The file does not contain any data.", parent=self)
            return

        self.fileName = fileName
        self.tables = tables
        self.fileLabel.config(text=fileName, fg=Theme.text)
        names = list(tables.keys())
        self.sheetCombo['values'] = names
        # start with the first sheet that has any numbers
        first = next((n for n in names if DataImport.NumericColumns(tables[n], False)), names[0])
        self.sheetCombo.set(first)
        self.sheetCombo.config(state='readonly' if len(names) > 1 else 'disabled')
        self.OnSheetChanged()


    def OnSheetChanged(self):
        self.rows = self.tables.get(self.sheetCombo.get(), [])
        self.headerFlag.set(DataImport.LooksLikeHeader(self.rows))
        self.OnHeaderChanged(selectDefaultColumns=True)


    def OnHeaderChanged(self, selectDefaultColumns=False):
        header = self.headerFlag.get()
        names = DataImport.ColumnNames(self.rows, header)
        numeric = DataImport.NumericColumns(self.rows, header)
        for i, combo in enumerate(self.columnCombos):
            current = combo.current()
            combo['values'] = names
            combo.config(state='readonly' if names else 'disabled')
            if selectDefaultColumns or current < 0 or current >= len(names):
                # default to the first numeric columns, in order
                if i < len(numeric):
                    combo.current(numeric[i])
                elif names:
                    combo.current(min(i, len(names) - 1))
            else:
                combo.current(current)
        self.UpdatePreview(names)
        self.UpdateSummary()


    def UpdatePreview(self, names):
        self.preview.delete(*self.preview.get_children())
        columns = ['row'] + ['c%d' % i for i in range(min(len(names), self.maxPreviewColumns))]
        self.preview['columns'] = columns
        self.preview.heading('row', text='Row')
        self.preview.column('row', width=50, anchor=tk.E, stretch=False)
        for i, name in enumerate(names[:self.maxPreviewColumns]):
            self.preview.heading('c%d' % i, text=name)
            self.preview.column('c%d' % i, width=110, anchor=tk.W, stretch=False)
        for index, row in enumerate(self.rows[:self.maxPreviewRows]):
            values = [index + 1] + ['' if c is None else str(c) for c in row[:self.maxPreviewColumns]]
            self.preview.insert('', tk.END, values=values)


    def SelectedColumns(self):
        return [combo.current() for combo in self.columnCombos]


    def UpdateSummary(self):
        if not self.rows:
            self.summaryLabel.config(text="")
            return
        columns = self.SelectedColumns()
        if min(columns) < 0:
            self.summaryLabel.config(text="Select a column for each of " + ', '.join(self.axisNames) + ".")
            return
        points, skipped = DataImport.ExtractPoints(self.rows, columns, self.headerFlag.get())
        text = "%d data points will be imported." % len(points)
        if skipped:
            text += "  %d rows without numbers in all selected columns will be skipped." % skipped
        if len(set(columns)) < len(columns):
            text += "  Note: the same column is selected more than once."
        if len(self.rows) > self.maxPreviewRows:
            text += "  (The preview shows the first %d of %d rows.)" % (self.maxPreviewRows, len(self.rows))
        self.summaryLabel.config(text=text)


    def GetPoints(self):
        # returns (error string, points, description)
        if not self.rows:
            return ("Please open a CSV, text or Excel file first.", None, None)
        columns = self.SelectedColumns()
        if min(columns) < 0:
            return ("Please select a column for each of " + ', '.join(self.axisNames) + ".", None, None)
        points, skipped = DataImport.ExtractPoints(self.rows, columns, self.headerFlag.get())
        if not points:
            return ("The selected columns do not contain any rows of numbers.", None, None)
        return ('', points, 'Data imported from a CSV, text or Excel file')



class GraphImageTab(tk.Frame):
    # Digitizes data points from an image of a 2D graph.  The user places two
    # reference points on each axis and enters their values, then adds data
    # points by clicking, or traces a curve automatically by its color.

    markerColors = {'X': '#3d8bff', 'Y': '#2fbf4f'} # also the Place buttons' text
    pointColor = '#ff00ff'

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.image = None       # full resolution PIL image
        self.photo = None       # displayed (zoomed) tkinter image
        self.scale = 1.0
        self.fileName = ''
        self.points = []        # data points in image pixel coordinates
        self.calibration = {'X': DataImport.AxisCalibration(), 'Y': DataImport.AxisCalibration()}
        self.referencePoints = {} # 'X1' -> (column, row) image position
        self.traceColor = None
        self.traceArea = None   # (left, top, right, bottom) in image pixels
        self.mode = tk.StringVar(value='add')
        self.placing = None     # reference point being placed, e.g. 'X1'
        self.dragStart = None

        # the image canvas, with scroll bars
        canvasFrame = tk.Frame(self)
        canvasFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 4), pady=8)
        self.canvas = tk.Canvas(canvasFrame, background=Theme.field, highlightthickness=0, cursor='crosshair')
        vbar = ttk.Scrollbar(canvasFrame, orient=tk.VERTICAL, command=self.canvas.yview)
        hbar = ttk.Scrollbar(canvasFrame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        vbar.grid(row=0, column=1, sticky='ns')
        hbar.grid(row=1, column=0, sticky='ew')
        canvasFrame.rowconfigure(0, weight=1)
        canvasFrame.columnconfigure(0, weight=1)
        self.canvas.create_text(20, 20, anchor=tk.NW, tags='help', fill=Theme.muted,
                                text="Open an image of a 2D graph to begin.\n\n"
                                     "Supported formats: PNG, JPG, GIF, BMP, TIFF, WebP,\n"
                                     "and vector graphs in %s." % DataImport.vectorImageFormatNames)

        self.canvas.bind('<ButtonPress-1>', self.OnPress)
        self.canvas.bind('<B1-Motion>', self.OnDrag)
        self.canvas.bind('<ButtonRelease-1>', self.OnRelease)
        self.canvas.bind('<ButtonPress-3>', self.OnRightClick)
        if sys.platform == 'darwin':
            # macOS Tk 8.6 reports a right-click as button 2, and one-button
            # mice and trackpads right-click with Control-click
            self.canvas.bind('<ButtonPress-2>', self.OnRightClick)
            self.canvas.bind('<Control-ButtonPress-1>', self.OnRightClick)
        self.canvas.bind('<Motion>', self.OnMotion)

        # the controls
        controls = tk.Frame(self, width=300)
        controls.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 8), pady=8)

        row = tk.Frame(controls)
        row.pack(fill=tk.X)
        Tooltips.Add(tk.Button(row, text="Open Image...", command=self.OnOpen),
                     "Open a picture of a graph: PNG, JPG, GIF, BMP, TIFF or WebP, or a vector graph in %s."
                     % DataImport.vectorImageFormatNames).pack(side=tk.LEFT)
        zoomTip = "Enlarge the image to place points more accurately.  Fit shows the whole image."
        Tooltips.Add(tk.Label(row, text="  Zoom:"), zoomTip).pack(side=tk.LEFT)
        self.zoomCombo = ttk.Combobox(row, state='readonly', width=6,
                                      values=['Fit', '50%', '75%', '100%', '150%', '200%', '300%', '400%'])
        self.zoomCombo.set('Fit')
        self.zoomCombo.bind('<<ComboboxSelected>>', lambda e: self.Redraw(rescale=True))
        self.zoomCombo.pack(side=tk.LEFT)
        Tooltips.Add(self.zoomCombo, zoomTip)
        self.fileLabel = tk.Label(controls, text="", anchor=tk.W, fg=Theme.muted, wraplength=290, justify=tk.LEFT)
        self.fileLabel.pack(fill=tk.X, pady=(2, 6))

        # step 1 - axis calibration
        calibrationFrame = tk.LabelFrame(controls, text=" 1. Calibrate the axes ")
        calibrationFrame.pack(fill=tk.X)
        tk.Label(calibrationFrame, text="Place two points on each axis at known\nvalues (such as tick marks), then enter them.",
                 justify=tk.LEFT, fg=Theme.muted).grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=4)
        self.valueEntries = {}
        self.placeButtons = {}
        for index, name in enumerate(['X1', 'X2', 'Y1', 'Y2']):
            button = tk.Button(calibrationFrame, text="Place %s" % name, width=9,
                               fg=self.markerColors[name[0]], command=lambda n=name: self.StartPlacing(n))
            Tooltips.Add(button, "Then click the image at a known %s value, such as a labeled tick mark on the %s "
                                 "axis.  Use two points far apart for accuracy."
                                 % (name[0], 'horizontal' if name[0] == 'X' else 'vertical'))
            button.grid(row=index + 1, column=0, padx=4, pady=2, sticky=tk.W)
            self.placeButtons[name] = button
            tk.Label(calibrationFrame, text="%s value:" % name[0]).grid(row=index + 1, column=1, sticky=tk.E)
            entry = tk.Entry(calibrationFrame, width=12)
            entry.grid(row=index + 1, column=2, padx=4, pady=2)
            Tooltips.Add(entry, "The %s value at the point you placed, as labeled on the graph." % name[0])
            self.valueEntries[name] = entry
        self.logX = tk.BooleanVar(value=False)
        self.logY = tk.BooleanVar(value=False)
        Tooltips.Add(tk.Checkbutton(calibrationFrame, text="Log X axis", variable=self.logX),
                     "Check this if the X axis has a logarithmic scale, such as 1, 10, 100, 1000 equally "
                     "spaced.").grid(row=5, column=0, columnspan=2, sticky=tk.W)
        Tooltips.Add(tk.Checkbutton(calibrationFrame, text="Log Y axis", variable=self.logY),
                     "Check this if the Y axis has a logarithmic scale, such as 1, 10, 100, 1000 equally "
                     "spaced.").grid(row=5, column=2, sticky=tk.W)

        # step 2 - data points
        pointsFrame = tk.LabelFrame(controls, text=" 2. Add data points ")
        pointsFrame.pack(fill=tk.X, pady=(8, 0))
        for value, text, tip in [
                ('add', "Click to add points", "Click on the image to add a data point at each click."),
                ('delete', "Click or drag a box to delete points",
                 "Click a point, or drag a box around several, to delete them."),
                ('color', "Click a curve to pick its color",
                 "Click on the curve to trace, so that Trace Curve follows that color."),
                ('area', "Drag a box around the area to trace",
                 "Optional: drag a box around the plot area, so that tracing leaves out the legend, labels "
                 "and other curves of the same color.")]:
            Tooltips.Add(tk.Radiobutton(pointsFrame, text=text, variable=self.mode, value=value,
                                        command=self.OnModeChanged), tip).pack(anchor=tk.W)

        traceFrame = tk.Frame(pointsFrame)
        traceFrame.pack(fill=tk.X, padx=4, pady=(4, 0))
        tk.Label(traceFrame, text="Curve color:").grid(row=0, column=0, sticky=tk.W)
        self.colorSwatch = tk.Label(traceFrame, text=" none ", relief=tk.SUNKEN, width=8)
        self.colorSwatch.grid(row=0, column=1, sticky=tk.W, padx=4)
        toleranceTip = ("How different a color can be from the curve's color and still be traced.  Raise it "
                        "if the trace misses parts of the curve; lower it if it picks up other lines or text.")
        Tooltips.Add(tk.Label(traceFrame, text="Color tolerance:"), toleranceTip).grid(row=1, column=0, sticky=tk.W)
        self.tolerance = tk.IntVar(value=100)
        Tooltips.Add(tk.Scale(traceFrame, from_=10, to=250, orient=tk.HORIZONTAL, variable=self.tolerance,
                              showvalue=True, length=130), toleranceTip).grid(row=1, column=1, sticky=tk.W)
        spacingTip = "The distance between traced points along the curve, in image pixels.  Smaller gives more points."
        Tooltips.Add(tk.Label(traceFrame, text="Point spacing (pixels):"), spacingTip).grid(row=2, column=0, sticky=tk.W)
        self.spacing = tk.IntVar(value=5)
        Tooltips.Add(tk.Spinbox(traceFrame, from_=1, to=100, width=5, textvariable=self.spacing),
                     spacingTip).grid(row=2, column=1, sticky=tk.W, padx=4)

        buttons = tk.Frame(pointsFrame)
        buttons.pack(fill=tk.X, padx=4, pady=6)
        Tooltips.Add(tk.Button(buttons, text="Trace Curve", command=self.OnTrace),
                     "Add points along the curve of the picked color automatically.  Pick the color "
                     "first.").pack(side=tk.LEFT)
        Tooltips.Add(tk.Button(buttons, text="Clear Points", command=self.OnClearPoints),
                     "Delete all of the data points, keeping the axis calibration.").pack(side=tk.LEFT, padx=6)

        self.countLabel = tk.Label(controls, text="No data points", anchor=tk.W)
        self.countLabel.pack(fill=tk.X, pady=(8, 0))
        self.positionLabel = tk.Label(controls, text="", anchor=tk.W, fg=Theme.muted)
        self.positionLabel.pack(fill=tk.X)
        self.helpLabel = tk.Label(controls, text="", anchor=tk.W, justify=tk.LEFT, wraplength=290, fg=Theme.highlight)
        self.helpLabel.pack(fill=tk.X, pady=(6, 0))
        self.OnModeChanged()


    # ---- image loading and display ----

    def OnOpen(self):
        fileName = filedialog.askopenfilename(parent=self, title="Open Graph Image", filetypes=DataImport.imageFileTypes)
        if not fileName:
            return
        try:
            self.config(cursor='watch')
            self.update_idletasks()
            image = DataImport.LoadGraphImage(fileName)
        except Exception as e:
            tk_mbox.showerror("Import Data", "Could not open the image:\n\n%s\n\n%s" % (fileName, e), parent=self)
            return
        finally:
            self.config(cursor='')
        self.image = image
        self.fileName = fileName
        self.fileLabel.config(text="%s  (%d x %d pixels)" % (os.path.basename(fileName), image.width, image.height))
        self.points = []
        self.referencePoints = {}
        self.traceArea = None
        self.traceColor = None
        self.colorSwatch.config(text=" none ", background=self.cget('background'))
        self.Redraw(rescale=True)
        self.StartPlacing('X1')


    def ZoomScale(self):
        choice = self.zoomCombo.get()
        if choice != 'Fit':
            return float(choice.rstrip('%')) / 100.0
        self.canvas.update_idletasks()
        width = max(self.canvas.winfo_width(), 200)
        height = max(self.canvas.winfo_height(), 200)
        return min(width / self.image.width, height / self.image.height, 4.0)


    def Redraw(self, rescale=False):
        if self.image is None:
            return
        from PIL import Image, ImageTk
        if rescale or self.photo is None:
            self.scale = self.ZoomScale()
            size = (max(1, int(self.image.width * self.scale)), max(1, int(self.image.height * self.scale)))
            resample = Image.Resampling.NEAREST if self.scale >= 2.0 else Image.Resampling.LANCZOS
            self.photo = ImageTk.PhotoImage(self.image.resize(size, resample))
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo, tags='image')
        self.canvas.configure(scrollregion=(0, 0, self.photo.width(), self.photo.height()))

        s = self.scale
        if self.traceArea is not None:
            l, t, r, b = self.traceArea
            self.canvas.create_rectangle(l * s, t * s, r * s, b * s, outline='#ff8000', dash=(4, 3), width=2, tags='area')
        for name, (px, py) in self.referencePoints.items():
            x, y = px * s, py * s
            color = self.markerColors[name[0]]
            self.canvas.create_line(x - 9, y, x + 10, y, fill=color, width=2)
            self.canvas.create_line(x, y - 9, x, y + 10, fill=color, width=2)
            self.canvas.create_text(x + 6, y - 6, text=name, anchor=tk.SW, fill=color, font='-weight bold')
        for px, py in self.points:
            x, y = px * s, py * s
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, outline=self.pointColor, width=2, tags='point')
        self.countLabel.config(text="%d data points" % len(self.points) if self.points else "No data points")


    def ImagePosition(self, event):
        # image pixel position for a mouse event, or None if outside the image
        if self.image is None:
            return None
        px = self.canvas.canvasx(event.x) / self.scale
        py = self.canvas.canvasy(event.y) / self.scale
        if 0 <= px < self.image.width and 0 <= py < self.image.height:
            return (px, py)
        return None


    # ---- modes and mouse handling ----

    def StartPlacing(self, name):
        if self.image is None:
            tk_mbox.showinfo("Import Data", "Please open a graph image first.", parent=self)
            return
        self.placing = name
        axis = 'x-axis (horizontal)' if name[0] == 'X' else 'y-axis (vertical)'
        self.helpLabel.config(text="Click the image at a known value on the %s for reference point %s, "
                                   "then enter that value. Zoom in for accuracy." % (axis, name))


    def OnModeChanged(self):
        self.placing = None
        rightClick = "Right-click or Control-click" if sys.platform == 'darwin' else "Right-click"
        help = {'add': "Click to add a data point. %s a point to delete it." % rightClick,
                'delete': "Click a point, or drag a box around points, to delete them.",
                'color': "Click on the curve to use its color for tracing, then press Trace Curve.",
                'area': "Drag a box around the plot area to trace only inside it - for example to "
                        "leave out the legend. Then press Trace Curve."}
        self.helpLabel.config(text=help[self.mode.get()])


    def OnPress(self, event):
        position = self.ImagePosition(event)
        if position is None:
            return
        if self.placing:
            name = self.placing
            self.referencePoints[name] = position
            self.placing = None
            self.valueEntries[name].focus_set()
            self.valueEntries[name].select_range(0, tk.END)
            self.Redraw()
            # continue with the next reference point that has not been placed
            remaining = [n for n in ['X1', 'X2', 'Y1', 'Y2'] if n not in self.referencePoints]
            if remaining:
                self.StartPlacing(remaining[0])
            else:
                self.OnModeChanged()
            return

        mode = self.mode.get()
        if mode == 'add':
            self.points.append(position)
            self.Redraw()
        elif mode == 'color':
            # search a few screen pixels around the click, as lines are thin
            radius = max(2, int(round(6 / self.scale)))
            color = DataImport.PickCurveColor(self.image, position[0], position[1], radius)
            self.traceColor = color
            hexColor = '#%02x%02x%02x' % color
            textColor = 'white' if sum(color) < 384 else 'black'
            self.colorSwatch.config(text=hexColor, background=hexColor, foreground=textColor)
        elif mode in ['delete', 'area']:
            self.dragStart = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))


    def OnDrag(self, event):
        if self.dragStart is None:
            return
        self.canvas.delete('drag')
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        color = '#ff0000' if self.mode.get() == 'delete' else '#ff8000'
        self.canvas.create_rectangle(self.dragStart[0], self.dragStart[1], x, y, outline=color, dash=(4, 3), tags='drag')


    def OnRelease(self, event):
        if self.dragStart is None:
            return
        x0, y0 = self.dragStart
        x1, y1 = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.dragStart = None
        self.canvas.delete('drag')
        s = self.scale
        box = (min(x0, x1) / s, min(y0, y1) / s, max(x0, x1) / s, max(y0, y1) / s)
        small = abs(x1 - x0) < 4 and abs(y1 - y0) < 4

        if self.mode.get() == 'delete':
            if small:
                self.DeleteNearest(x1, y1)
            else:
                self.points = [p for p in self.points
                               if not (box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3])]
                self.Redraw()
        elif self.mode.get() == 'area':
            self.traceArea = None if small else box
            self.Redraw()


    def OnRightClick(self, event):
        self.DeleteNearest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))


    def DeleteNearest(self, canvasX, canvasY):
        # delete the point nearest the canvas position, within 8 screen pixels
        best, bestDistance = None, 8.0
        for index, (px, py) in enumerate(self.points):
            distance = ((px * self.scale - canvasX) ** 2 + (py * self.scale - canvasY) ** 2) ** 0.5
            if distance <= bestDistance:
                best, bestDistance = index, distance
        if best is not None:
            del self.points[best]
            self.Redraw()


    def OnMotion(self, event):
        position = self.ImagePosition(event)
        if position is None:
            self.positionLabel.config(text="")
            return
        text = "Pixel (%d, %d)" % position
        xCal, yCal = self.Calibrations()
        if not xCal.Check() and not yCal.Check():
            text += "   X = %.6G   Y = %.6G" % (xCal.ToValue(position[0]), yCal.ToValue(position[1]))
        self.positionLabel.config(text=text)


    # ---- tracing and results ----

    def OnTrace(self):
        if self.image is None:
            tk_mbox.showinfo("Import Data", "Please open a graph image first.", parent=self)
            return
        if self.traceColor is None:
            tk_mbox.showinfo("Import Data", "Please pick the curve color first: choose "
                             "\"Click a curve to pick its color\", then click on the curve.", parent=self)
            return
        try:
            spacing = int(self.spacing.get())
        except (tk.TclError, ValueError):
            spacing = 5
        traced = DataImport.TraceCurveByColor(self.image, self.traceColor, self.tolerance.get(), spacing, self.traceArea)
        if not traced:
            tk_mbox.showinfo("Import Data", "No pixels of that color were found. Try increasing the "
                             "color tolerance, or pick the color again.", parent=self)
            return
        self.points.extend(traced)
        self.Redraw()
        self.helpLabel.config(text="%d points traced. Delete any unwanted points, such as on the legend, "
                                   "by dragging a box around them in delete mode." % len(traced))


    def OnClearPoints(self):
        self.points = []
        self.Redraw()


    def Calibrations(self):
        for axis, logFlag in [('X', self.logX.get()), ('Y', self.logY.get())]:
            calibration = self.calibration[axis]
            calibration.logFlag = logFlag
            for index in range(2):
                name = axis + str(index + 1)
                position = self.referencePoints.get(name)
                calibration.pixels[index] = None if position is None else position[0 if axis == 'X' else 1]
                calibration.values[index] = DataImport.ToFloat(self.valueEntries[name].get())
        return self.calibration['X'], self.calibration['Y']


    def GetPoints(self):
        # returns (error string, points, description)
        if self.image is None:
            return ("Please open a graph image first.", None, None)
        xCal, yCal = self.Calibrations()
        for axis, calibration in [('X', xCal), ('Y', yCal)]:
            error = calibration.Check()
            if error:
                return ("%s axis calibration: %s." % (axis, error), None, None)
        if not self.points:
            return ("Please add some data points: click on the graph, or trace a curve by its color.", None, None)
        return ('', DataImport.PixelsToData(self.points, xCal, yCal), 'Data digitized from a graph image')
