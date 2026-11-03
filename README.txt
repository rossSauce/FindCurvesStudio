Welcome to tkInterFit, an example of creating a
cross-platform curve and surface fitting application
using tkinter and the pyeq3 fitting library.
see http://zunzun.com/CommonProblems/


Maintainer
----------
tkInterFit is maintained by Ross Moffett. Please send questions,
comments, suggestions and bug reports to findcurves@gmail.com

tkInterFit was originally written by James R. Phillips, who is no
longer maintaining it. His original version, and a wxPython version
of this code, are at:
https://bitbucket.org/zunzuncode/tkInterFit
https://bitbucket.org/zunzuncode/wxPythonFit


Windows users: just run the installer
-------------------------------------
tkinterFit-<version>-Setup.exe installs tkinterFit with its own bundled
copy of Python and every library it needs - nothing else is required.



Function Finder
---------------
The "Function Finder 2D" and "Function Finder 3D" buttons fit the text
data to every standard equation, using the selected fitting target, and
rank the results from best to worst fit. As on zunzunsite3, the
"Coefficients" setting limits the equations tried to a maximum (or an
exact) number of coefficients - defaults are 5 for 2D and 6 for 3D.

Linear equations are fitted immediately; nonlinear equations are fitted
in parallel on all but one CPU core and can take several minutes. Cancel
shows the results found so far.

The results window lists every fitted equation with its coefficients and
fit statistics. Click a column heading to sort, select an equation to see
its full coefficient and fit statistics, or double-click it to open the
complete graphs and reports. "Save All Results To PDF" creates a single
PDF with the data, a ranked summary table, the formula, coefficients,
standard errors, t-statistics, p-values, confidence intervals and fit
statistics of every fitted equation (optionally with a graph of each),
and a list of the equations that could not be fitted.



Running from source
-------------------

Step 1: Install Python 3.14 (https://www.python.org/downloads/)


Step 2: Create a virtual environment and install the required libraries

From a command prompt in this directory, run:

py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

(On Linux/macOS use python3 -m venv .venv and .venv/bin/python)

This installs pyeq3, numpy, scipy, matplotlib and reportlab (reportlab
is used for creating PDF files of the fitting results).



Step 3: Run the tkInterFit example

.venv\Scripts\python tkinterFit.py



Building the Windows executable and installer
---------------------------------------------

Install Inno Setup 6 (winget install JRSoftware.InnoSetup), then run:

powershell -ExecutionPolicy Bypass -File build.ps1

This creates the virtual environment if needed, builds
dist\tkinterFit\tkinterFit.exe with PyInstaller (tkinterFit.spec), and then
builds installer\Output\tkinterFit-<version>-Setup.exe with Inno Setup
(installer\tkinterFit.iss). Update MyAppVersion in the .iss file for each release.



Step 4: Celebrate

You are now curve and surface fitting data using tkinter!
