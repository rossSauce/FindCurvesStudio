# tkInterFit

Welcome to tkInterFit, an example of creating a cross-platform curve and
surface fitting application using tkinter and the
[pyeq3](https://pypi.org/project/pyeq3/) fitting library.

- Fit 2D and 3D data to any of the several hundred pyeq3 equations, with
  extended forms, polynomials, polyfunctionals, rationals, splines and user
  defined functions
- Function finder: fit data to many equations and rank the results, with a
  single PDF report of every fit
- Import data from CSV and Excel files, or digitize it from a graph image
- Windows installer, macOS app and Linux package with Python and all
  libraries bundled

See also <http://zunzun.com/CommonProblems/>, and [CHANGELOG.md](CHANGELOG.md)
for release notes.


## Maintainer

tkInterFit is maintained by Ross Moffett. Please send questions, comments,
suggestions and bug reports to <findcurves@gmail.com>.

tkInterFit was originally written by James R. Phillips, who is no longer
maintaining it. His original version, and a wxPython version of this code,
are at:

- <https://bitbucket.org/zunzuncode/tkInterFit>
- <https://bitbucket.org/zunzuncode/wxPythonFit>


## Windows users: just run the installer

`tkinterFit-<version>-Setup.exe` installs tkinterFit with its own bundled
copy of Python and every library it needs - nothing else is required.


## Main Window

2D curve fitting and 3D surface fitting are on separate tabs. Each tab has
collapsible sections - click a section title to show or hide it:

- **Data:** the data text editor, and "Import Data..."
- **Fit One Equation:** choose an equation and fit the data to it
- **Function Finder:** fit the data to many equations and rank them

The fitting target applies to both kinds of fitting. A collapsed section
shows a short summary, such as the number of data points. The window fits
the screen and can be resized; the data editor uses any extra space.


## Equations

Every equation in the pyeq3 library is available in the 2D and 3D equation
lists. "Form" selects an extended form of the equation, where the equation
allows it: With Offset, Plus Line (2D) or Plus Plane (3D), Reciprocal,
Inverse, and Linear or Exponential Growth and Decay, each with or without an
offset.

Some equation types have settings, shown below the equation list:

- **User-Selectable Polynomial:** the polynomial order (X and Y for 3D)
- **User-Customizable Polynomial (2D):** the polynomial terms to use
- **Polyfunctional:** the function terms to use
- **Rational (2D):** the numerator and denominator terms
- **Spline:** the smoothing factor and spline order
- **User Defined Function:** type in a function, such as
  `a * X + b * exp(c * X)`, using X (and Y) for the data and letters for
  the coefficients


## Function Finder

The "Run Function Finder" button on the 2D and 3D tabs fits the text data
to many equations, using the selected fitting target, and rank the results
from best to worst fit. As on zunzunsite3, the "Coefficients" setting
limits the equations tried to a maximum (or an exact) number of
coefficients - defaults are 5 for 2D and 6 for 3D.

By default every standard equation is tried in its Default, With Offset and
Plus Line/Plane forms, along with polynomials of every order. "Options..."
adds, as on zunzunsite3: Reciprocal, Inverse, and Linear and Exponential
Growth and Decay forms; polyfunctional combinations of up to 4 (2D) or 2
(3D) terms; and 2D rational equations with up to 2 numerator and 2
denominator terms. The options window shows how many equations will be
tried. Splines and user defined functions are not used by the function
finder.

Equations are fitted in parallel on all but one CPU core: fast linear fits
first, then nonlinear fits, which can take several minutes or more with
many options selected. Cancel shows the results found so far. As on
zunzunsite3, the best 1000 results are kept with full fit statistics.

The results window lists every fitted equation with its coefficients and
fit statistics. Click a column heading to sort, select an equation to see
its full coefficient and fit statistics, or double-click it to open the
complete graphs and reports. "Save All Results To PDF" creates a single PDF
with the data and a ranked summary table, then for every fitted equation:
the formula; coefficients with standard errors, t-statistics, p-values and
confidence intervals; fit statistics; the covariance matrix; absolute and
percent error statistics; source code in ten languages; and optionally the
same model graphs (2D model with 95% confidence intervals, or 3D surface
and contour plots) and error graphs as the individual results viewer. It
ends with a list of equations that could not be fitted.


## Importing Data

The "Import Data..." button beside each data editor title imports data from
CSV or text files (.csv .txt .tsv .dat) and Microsoft Excel files (.xlsx
.xlsm .xls): choose the sheet and the X, Y (and Z) columns. Rows without
numbers in every selected column are skipped.

For 2D data, the "Digitize Graph Image" tab reads data points from an image
of a graph - PNG, JPG, GIF, BMP, TIFF, WebP, or vector SVG and PDF files,
and on Windows also EMF and WMF files:

1. Place two reference points on each axis at known values (such as tick
   marks) and enter their values. Check "Log X/Y axis" for log scales.
2. Click to add data points, or trace a curve automatically: pick the
   curve's color by clicking it, optionally drag a box around the plot area
   to leave out legends, then press "Trace Curve". Delete unwanted points
   by right-clicking them (or Control-clicking on macOS), or in delete
   mode.


## Running from source

**Step 1:** Install Python 3.14 (<https://www.python.org/downloads/>)

**Step 2:** Create a virtual environment and install the required libraries.
From a command prompt in this directory, run:

```
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

(On Linux/macOS use `python3 -m venv .venv` and `.venv/bin/python`)

This installs pyeq3, numpy, scipy, matplotlib and reportlab (reportlab is
used for creating PDF files of the fitting results).

**Step 3:** Run the tkInterFit example

```
.venv\Scripts\python tkinterFit.py
```

**Step 4:** Celebrate

You are now curve and surface fitting data using tkinter!


## Building the Windows executable and installer

Install Inno Setup 6 (`winget install JRSoftware.InnoSetup`), then run:

```
powershell -ExecutionPolicy Bypass -File build.ps1
```

This creates the virtual environment if needed, builds
`dist\tkinterFit\tkinterFit.exe` with PyInstaller (`tkinterFit.spec`), and
then builds `installer\Output\tkinterFit-<version>-Setup.exe` with Inno
Setup (`installer\tkinterFit.iss`). Update `MyAppVersion` in the .iss file
for each release. The macOS and Linux builds read their version number from
the same place.


## Building for macOS

On a Mac with Python 3.14 from python.org (or Homebrew python@3.14 with
python-tk@3.14), run:

```
bash build-macos.sh
```

This builds `dist/tkinterFit.app` and
`installer/Output/tkinterFit-<version>-macOS-<arch>.dmg`. The app is built
for the Mac it is built on (arm64 for Apple silicon, x86_64 for Intel).
Without a Developer ID the app is unsigned, and users must right-click it
and choose Open the first time. To sign and notarize, set
`CODESIGN_IDENTITY` and `NOTARY_PROFILE` - see the comments at the top of
`build-macos.sh`.


## Building for Linux

With Python 3.14, its venv module and tkinter installed (for example the
python3.14-venv and python3.14-tk packages on Debian/Ubuntu), run:

```
bash build-linux.sh
```

This builds `dist/tkinterFit/tkinterFit` and
`installer/Output/tkinterFit-<version>-linux-<arch>.tar.gz`. Users extract
it and run `./install.sh`, which installs for the current user and adds a
menu entry (or installs for all users when run with sudo). The program runs
on distributions with the same or newer glibc than the build machine, so
build on the oldest distribution you want to support.
