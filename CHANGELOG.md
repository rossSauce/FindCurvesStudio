# Changelog

FindCurves Studio, formerly tkInterFit, is maintained by Ross Moffett
(<findcurves@gmail.com>).

## Unreleased

- Renamed FindCurves Studio, formerly tkInterFit.  The Windows installer
  upgrades an existing tkInterFit installation
- A new look: a dark color scheme, and an application icon - a curve fitted
  through data points - on the windows, program, installer, macOS app and
  Linux menu entry.  On Windows the title bars are dark too, and the Help
  menu is a button in the main window
- Tooltips explain every control, and the tabs and columns of the results
  windows - including what to look for in each graph.  They can be turned
  off in the new Help menu
- A Getting Started guide, from the Help menu and the top of the main
  window: how to start, choose a fitting target, find an equation, judge
  the fit and use the results, with common curve fitting difficulties and a
  link to the animated explanations on the findcurves website
- macOS app and Linux package builds, alongside the Windows installer
- Digitizing graph images: right-click and Control-click delete points on
  macOS; EMF and WMF images are offered only on Windows, where they can be
  read
- User defined functions:
  - fabs(), log10(), log2(), arctan2(), deg2rad() and rad2deg() now work,
    as do numbers such as 3.5e-2
  - abs(), ln() and pow() can be used
  - coefficient names can include digits, such as a1 and a2
  - words in # comments are no longer taken as coefficients
  - clear messages for mistakes such as unknown functions, unbalanced
    parentheses, a lower case x, or a function without coefficients
  - source code output in all ten languages, which was not available before
  - the function is shown in a tidy, consistent form in the results
- Ready for SciPy 1.19, which removes scipy.odr: FindCurves Studio now does
  its own orthogonal distance regression and coefficient statistics for pyeq3
  - standard errors are slightly more accurate
  - fits that cannot be calculated show their statistics as not available,
    rather than as zero
  - fixes a crash of the whole program with some equations and the
    orthogonal distance (ODR) fitting target

## 1.4.0 (November 2026)

- Every equation in the pyeq3 library is now available, including
  polynomials of a selected order, customizable polynomials,
  polyfunctionals, rationals, splines and user defined functions
- Extended forms of each equation can be selected: Plus Line/Plane,
  Reciprocal, Inverse, and Linear and Exponential Growth and Decay
- The function finder tries Plus Line/Plane forms and polynomials of every
  order by default, as on zunzunsite3, with options for the extended forms,
  polyfunctional and rational equations
- Works around a pyeq3 12.6.1 bug that made Plus Line forms fail
- More compact main window for small screens: 2D and 3D tabs with
  collapsible Data, Fit One Equation and Function Finder sections, a
  fitting target list, and a resizable window that fits the screen
- PDF reports include an inspirational message page after the title page,
  as in the ZunZun4 site's reports

## 1.3.0 (November 2026)

- Added an Import Data dialog for CSV, text and Excel files, and for
  digitizing 2D data from graph images (raster, SVG, PDF, EMF, WMF)
- The function finder PDF now matches the individual results: 3D surface
  and contour plots, 2D confidence intervals, covariance matrix, error
  statistics, optional error graphs, and source code in ten languages

## 1.2.0 (November 2026)

- Added the 2D and 3D Function Finder, based on the zunzunsite3 function
  finder, with a ranked results window and a single PDF of all results

## 1.1.0 (November 2026)

- Updated for Python 3.14 and current numpy, scipy, matplotlib and
  reportlab
- Added a Windows executable and installer

## Earlier versions

Earlier versions were written by James R. Phillips. Their change log can be
viewed at <https://bitbucket.org/zunzuncode/tkInterFit/commits/all>
