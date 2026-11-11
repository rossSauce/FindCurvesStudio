# The FindCurves Studio look: a dark color scheme with the brand's teal and
# amber, and the application icon.
#
#   Theme.Apply(root)   call once, right after creating the Tk root window and
#                       before creating any other widgets
#
# Colors used directly by other modules are named here, such as Theme.muted
# for hint text, so the scheme can be changed in one place.

import os, sys
import tkinter as tk
from tkinter import ttk


# ---- the palette ----
window = '#22272e'      # window and panel background
raised = '#2d333c'      # buttons, tabs, headings
field = '#181c21'       # where text is typed: data editor, entries, lists
border = '#444c56'
text = '#e3e7ed'
muted = '#9aa4b1'       # hints and secondary text
disabled = '#6b7480'
accent = '#3fd1b8'      # teal, as the icon's curve
accentDark = '#1f6f66'  # selections
highlight = '#f7b242'   # amber, as the icon's data points; notes and warnings
link = '#6cb6ff'
tooltipBackground = '#363d47'


def IconFolder():
    # in the PyInstaller-built program, data files are in sys._MEIPASS
    return os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), 'icons')


def IconImage(size, master=None):
    # the icon as a PhotoImage, at 16, 24, 32, 48, 64 or 256 pixels
    return tk.PhotoImage(master=master, file=os.path.join(IconFolder(), 'FindCurves-%d.png' % size))


def Apply(root):
    _SetWindowIcon(root)
    _StyleTkWidgets(root)
    _StyleTtkWidgets(root)
    root.configure(background=window)
    if sys.platform == 'win32':
        # dark title bars on every window, as each window appears
        for windowClass in ('Tk', 'Toplevel'):
            root.bind_class(windowClass, '<Map>', lambda event: _DarkTitleBar(event.widget), add='+')


def _DarkTitleBar(widget):
    # Windows 10 (2004 and later) and 11 draw a dark title bar on request
    if getattr(widget, '_darkTitleBar', False):
        return
    widget._darkTitleBar = True
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(widget.winfo_id())
        on = ctypes.c_int(1)
        for attribute in (20, 19): # DWMWA_USE_IMMERSIVE_DARK_MODE, and its number before Windows 10 2004
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(on), ctypes.sizeof(on)) == 0:
                break
        # redraw the frame: SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0020 | 0x0002 | 0x0001 | 0x0004 | 0x0010)
    except Exception:
        pass


def MonospaceFont():
    # for data and reports, where columns of numbers should line up
    import tkinter.font as tkfont
    families = set(tkfont.families())
    for family, size in [('Consolas', 10), ('Menlo', 12), ('DejaVu Sans Mono', 10)]:
        if family in families:
            return (family, size)
    return 'TkFixedFont'


def _SetWindowIcon(root):
    if sys.platform == 'win32':
        # show this program's icon in the taskbar, rather than Python's, when
        # running from the source code
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('FindCurves.Studio')
        except Exception:
            pass
        try: # the .ico has hand drawn small sizes for the title bar
            root.iconbitmap(default=os.path.join(IconFolder(), 'FindCurves.ico'))
            return
        except tk.TclError:
            pass
    try: # every window, including dialogs, uses these
        root.iconImages = [IconImage(size, root) for size in (16, 32, 48, 256)]
        root.iconphoto(True, *root.iconImages)
    except tk.TclError:
        pass


def _StyleTkWidgets(root):
    # defaults for the classic tk widgets, through the option database
    options = {
        '*Background': window, '*Foreground': text,
        '*activeBackground': raised, '*activeForeground': text,
        '*disabledForeground': disabled,
        '*highlightBackground': window, '*highlightColor': accent,
        '*selectBackground': accentDark, '*selectForeground': text,
        '*troughColor': field, '*insertBackground': text,
        '*Button.background': raised, '*Button.relief': 'flat', '*Button.borderWidth': 1,
        '*Button.highlightThickness': 1, '*Button.highlightBackground': border,
        '*Button.padX': 8, '*Button.padY': 2,
        '*Checkbutton.selectColor': field, '*Radiobutton.selectColor': field,
        '*Checkbutton.activeBackground': window, '*Radiobutton.activeBackground': window,
        '*Entry.background': field, '*Entry.relief': 'flat', '*Entry.highlightThickness': 1,
        '*Entry.highlightBackground': border,
        '*Spinbox.background': field, '*Spinbox.buttonBackground': raised, '*Spinbox.relief': 'flat',
        '*Spinbox.readonlyBackground': field, '*Spinbox.highlightThickness': 1, '*Spinbox.highlightBackground': border,
        '*Text.background': field, '*Text.relief': 'flat', '*Text.highlightThickness': 1,
        '*Text.highlightBackground': border,
        '*Listbox.background': field, '*Listbox.relief': 'flat', '*Listbox.highlightThickness': 1,
        '*Listbox.highlightBackground': border,
        '*Scale.highlightThickness': 0, '*Scale.sliderRelief': 'flat',
        '*LabelFrame.foreground': muted,
        '*Menu.background': raised, '*Menu.activeBackground': accentDark, '*Menu.relief': 'flat',
        '*Menu.selectColor': text, # check marks
        '*Canvas.background': field, '*Canvas.highlightThickness': 0,
    }
    for pattern, value in options.items():
        root.option_add(pattern, value)
    root.option_add('*Text.font', MonospaceFont())


def _StyleTtkWidgets(root):
    style = ttk.Style(root)
    style.theme_use('clam') # colors can be set for every part of 'clam'
    style.configure('.', background=window, foreground=text, fieldbackground=field, bordercolor=border,
                    lightcolor=raised, darkcolor=window, troughcolor=field, arrowcolor=text,
                    selectbackground=accentDark, selectforeground=text, insertcolor=text, focuscolor=accent)
    style.map('.', foreground=[('disabled', disabled)], background=[('active', raised)])

    style.configure('TNotebook', background=window, bordercolor=border, tabmargins=(2, 4, 2, 0))
    style.configure('TNotebook.Tab', background=window, foreground=muted, padding=(12, 4), bordercolor=border,
                    lightcolor=window)
    style.map('TNotebook.Tab', background=[('selected', raised), ('active', raised)],
              foreground=[('selected', text), ('active', text)],
              lightcolor=[('selected', accent)]) # a teal line along the selected tab

    style.configure('TCombobox', fieldbackground=field, background=raised, foreground=text, arrowcolor=text,
                    bordercolor=border, lightcolor=field, darkcolor=field)
    style.map('TCombobox', fieldbackground=[('readonly', field), ('disabled', window)],
              foreground=[('disabled', disabled)], background=[('active', raised)],
              selectbackground=[('readonly', field)], selectforeground=[('readonly', text)],
              bordercolor=[('focus', accent)])
    root.option_add('*TCombobox*Listbox.background', field)
    root.option_add('*TCombobox*Listbox.foreground', text)
    root.option_add('*TCombobox*Listbox.selectBackground', accentDark)
    root.option_add('*TCombobox*Listbox.selectForeground', text)

    style.configure('Treeview', background=field, fieldbackground=field, foreground=text, bordercolor=border,
                    lightcolor=field, darkcolor=field)
    style.map('Treeview', background=[('selected', accentDark)], foreground=[('selected', text)])
    style.configure('Treeview.Heading', background=raised, foreground=text, bordercolor=border,
                    lightcolor=raised, darkcolor=raised, relief='flat')
    style.map('Treeview.Heading', background=[('active', border)])

    style.configure('TScrollbar', background=raised, troughcolor=field, bordercolor=field, arrowcolor=muted,
                    lightcolor=raised, darkcolor=raised)
    style.map('TScrollbar', background=[('active', border)])
    style.configure('TProgressbar', background=accent, troughcolor=field, bordercolor=border,
                    lightcolor=accent, darkcolor=accent)
    style.configure('TPanedwindow', background=window)
    style.configure('Sash', sashthickness=6, gripcount=0, background=window)
