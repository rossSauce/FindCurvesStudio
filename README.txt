Welcome to tkInterFit, an example of creating a
cross-platform curve and surface fitting application 
using tkinter and the pyeq3 fitting library.
see http://zunzun.com/CommonProblems/


If you prefer wxPython, the wxPython version of this code
is at: https://bitbucket.org/zunzuncode/wxPythonFit


Windows users: just run the installer
-------------------------------------
tkinterFit-<version>-Setup.exe installs tkinterFit with its own bundled
copy of Python and every library it needs - nothing else is required.



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
