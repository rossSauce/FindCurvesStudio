# The "Getting Started" guide window: how to start and proceed with
# fitting, how to judge a fit, and common difficulties in curve fitting,
# with a link to the animated explanations on the findcurves website.

import sys
import tkinter as tk
import tkinter.font as tkfont
import tkinter.scrolledtext as tk_stxt
import webbrowser

import Tooltips
import Theme


curveFittingProblemsURL = 'https://www.findcurves.com/CommonProblems/'


def OpenCurveFittingProblemsPage():
    webbrowser.open(curveFittingProblemsURL)


def AddHelpMenu(root, buttonArea=None):
    # The application's Help menu.  On Windows the menu bar is drawn by
    # Windows in light colors, so the menu is a button in buttonArea instead.
    if sys.platform == 'win32' and buttonArea is not None:
        button = tk.Menubutton(buttonArea, text='Help \u25be', relief=tk.FLAT, padx=8, pady=2,
                               background=Theme.raised, activebackground=Theme.border, cursor='hand2')
        button.pack()
        helpMenu = tk.Menu(button, tearoff=False)
        button.configure(menu=helpMenu)
        Tooltips.Add(button, "Getting started, curve fitting difficulties, and turning tooltips on or off.")
    else:
        menubar = tk.Menu(root)
        helpMenu = tk.Menu(menubar, name='help', tearoff=False) # named 'help' for the macOS Help menu
        menubar.add_cascade(label='Help', menu=helpMenu)
        root.config(menu=menubar)
    helpMenu.add_command(label='Getting Started...', command=lambda: GuideWindow(root))
    helpMenu.add_command(label='Curve Fitting Difficulties (Web Page)', command=OpenCurveFittingProblemsPage)
    helpMenu.add_separator()
    showTooltips = tk.BooleanVar(root, value=Tooltips.enabled)
    def OnShowTooltips():
        Tooltips.enabled = showTooltips.get()
    helpMenu.add_checkbutton(label='Show Tooltips', variable=showTooltips, command=OnShowTooltips)
    root.showTooltipsVariable = showTooltips # keep the variable alive


# (style, text) pieces of the guide; styles are defined in GuideWindow
guide = [
    ('title', 'Getting Started With FindCurves Studio\n'),
    ('body', 'FindCurves Studio finds an equation that describes your data.  Hover the mouse pointer over '
             'any control to see what it does.\n'),

    ('heading', '1.  Choose 2D or 3D'),
    ('body', 'Use the "2D Curve Fitting" tab when one value (Y) depends on one other value (X).  '
             'Use "3D Surface Fitting" when one value (Z) depends on two others (X and Y).\n'),

    ('heading', '2.  Enter your data'),
    ('body', 'Type or paste your data into the data area, one point per line: X and Y, or X, Y '
             'and Z, separated by spaces or tabs.  You can copy columns straight from a '
             'spreadsheet.  Lines without numbers, such as titles and column names, are ignored.  '
             'The example data shows the format - replace it with your own.\n\n'
             'Or press "Import Data..." to read columns from a CSV, text or Excel file, or to '
             'digitize the points of a graph from an image.  Use Import Data for CSV files with '
             'commas, which the data area does not read.\n'),

    ('heading', '3.  Choose the fitting target'),
    ('body', 'The fitting target decides what "best fit" means.  The first one, the lowest sum of '
             'squared absolute error, is ordinary least squares and suits most data.  Use relative '
             'error when your data spans several orders of magnitude, so the small values count as '
             'much as the large ones.  Use orthogonal distance (ODR) when the X values have '
             'measurement errors too.\n'),

    ('heading', '4.  Find an equation'),
    ('body', 'If you do not know which equation to use, run the Function Finder.  It fits your data '
             'to hundreds of equations and ranks them.  Start with the default number of '
             'coefficients; fewer coefficients give simpler equations.  Look at the first few '
             'results, not just the best one - when several fit almost equally well, prefer the '
             'simplest, or one that makes sense for what you measured.  Double-click a result to see '
             'its graphs and reports.\n\n'
             'If you already know the equation, choose it under "Fit One Equation" and press Fit.  '
             'You can also type in your own equation: choose the "User Defined Function" family.\n'),

    ('heading', '5.  Judge the fit'),
    ('body', 'A high R-squared alone does not make a good fit.  In the results window, check that:\n'),
    ('bullet', '•  the model graph follows the data, including between and at the ends of the data '
               'points\n'),
    ('bullet', '•  the error graphs show the errors scattered randomly around zero - a pattern, such '
               'as a curve or a funnel shape, means the equation misses something about the data\n'),
    ('bullet', '•  the coefficients\' standard errors are small compared with the coefficients - '
               'large ones mean the data cannot pin those coefficients down, and a simpler equation '
               'may be better\n'),

    ('heading', '6.  Use the result'),
    ('body', 'The Source Code tab has the fitted equation as code in ten programming languages, ready '
             'to use in your own programs and spreadsheets.  "Save To PDF" saves the complete '
             'results, and the Function Finder can save all of its results to one PDF.\n'),

    ('heading', 'Common difficulties in curve fitting'),
    ('bullet', '•  Too many coefficients: the curve passes close to every point but wiggles between '
               'them, and predicts new data badly.  Use the fewest coefficients that fit well.\n'),
    ('bullet', '•  Extrapolation: an equation can fit well within your data and behave wildly '
               'outside it.  Be careful using a fit beyond the range of your data.\n'),
    ('bullet', '•  Starting values: nonlinear equations are fitted from starting values for their '
               'coefficients.  FindCurves Studio estimates these automatically, but a complicated equation '
               'can still settle on a poor fit.  Try a simpler equation, or compare with the Function '
               'Finder.\n'),
    ('bullet', '•  Outliers: one bad data point can pull the whole fit away from the rest.  Look '
               'for points with unusually large errors in the error graphs.\n'),
    ('bullet', '•  Equations that cannot use the data: some equations need positive values, for '
               'example to take a logarithm.  The Function Finder skips them and says how many were '
               'skipped.\n'),
    ('body', '\nThe findcurves website has animated explanations of these and other difficulties:\n'),
    ('link', curveFittingProblemsURL),
    ('body', '\n'),
]


class GuideWindow(tk.Toplevel):

    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.title('FindCurves Studio - Getting Started')
        # the system's normal interface font, which reads better than the
        # text widget's fixed width font
        base = tkfont.nametofont('TkDefaultFont')
        family, size = base.actual('family'), base.actual('size')
        def Size(larger): # sizes below zero are in pixels
            return size + larger if size > 0 else size - larger
        text = tk_stxt.ScrolledText(self, width=78, height=30, wrap=tk.WORD, padx=12, pady=10,
                                    cursor='arrow', relief=tk.FLAT, font=(family, Size(1)))
        text.pack(fill=tk.BOTH, expand=True)
        text.tag_configure('title', font=(family, Size(5), 'bold'), foreground=Theme.accent, spacing1=4, spacing3=6)
        text.tag_configure('heading', font=(family, Size(2), 'bold'), spacing1=10, spacing3=2)
        text.tag_configure('body', spacing3=2)
        text.tag_configure('bullet', lmargin1=12, lmargin2=26, spacing3=3)
        text.tag_configure('link', foreground=Theme.link, underline=True)
        text.tag_bind('link', '<Button-1>', lambda e: OpenCurveFittingProblemsPage())
        text.tag_bind('link', '<Enter>', lambda e: text.config(cursor='hand2'))
        text.tag_bind('link', '<Leave>', lambda e: text.config(cursor='arrow'))
        for style, piece in guide:
            text.insert(tk.END, piece + ('\n' if style == 'heading' else ''), style)
        text.config(state=tk.DISABLED)

        buttons = tk.Frame(self)
        buttons.pack(fill=tk.X, padx=10, pady=8)
        tk.Button(buttons, text='Open Curve Fitting Difficulties Web Page',
                  command=OpenCurveFittingProblemsPage).pack(side=tk.LEFT)
        tk.Button(buttons, text='Close', width=10, command=self.destroy).pack(side=tk.RIGHT)

        # centered, within the screen
        self.update_idletasks()
        width = min(self.winfo_reqwidth(), self.winfo_screenwidth() - 40)
        height = min(self.winfo_reqheight(), self.winfo_screenheight() - 100)
        self.geometry('%dx%d+%d+%d' % (width, height, max(0, (self.winfo_screenwidth() - width) // 2),
                                       max(0, (self.winfo_screenheight() - height) // 3)))
