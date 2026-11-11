# Tooltips: short explanations that appear when the mouse pointer rests on
# a control.  tkinter has no tooltips of its own.
#
#   Tooltips.Add(widget, "What this control does")
#   Tooltips.AddToTabs(notebook, ["first tab's tooltip", "second tab's", ...])
#   Tooltips.AddToHeadings(treeview, {'column id': "column tooltip", ...})
#
# Tooltips.enabled turns all tooltips on or off, for example from a menu.

import sys
import tkinter as tk

import Theme


enabled = True
delayMilliseconds = 600
wrapLength = 360 # pixels


class Tooltip:
    # textFunction(event) returns the text to show at the mouse position, or
    # None for no tooltip there - so one widget can have several tooltips,
    # such as one for each notebook tab.

    def __init__(self, widget, textFunction):
        self.widget = widget
        self.textFunction = textFunction
        self.window = None
        self.pending = None
        self.text = None
        self.lastEvent = None
        widget.bind('<Enter>', self.OnMotion, add='+')
        widget.bind('<Motion>', self.OnMotion, add='+')
        widget.bind('<Leave>', self.Hide, add='+')
        widget.bind('<ButtonPress>', self.Hide, add='+')
        widget.bind('<KeyPress>', self.Hide, add='+')
        widget.bind('<Destroy>', self.Hide, add='+')

    def OnMotion(self, event):
        self.lastEvent = event
        text = self.textFunction(event) if enabled else None
        if text == self.text and (self.window or self.pending):
            return # the same tooltip is showing, or about to show
        self.Hide()
        self.text = text
        if text:
            self.pending = self.widget.after(delayMilliseconds, self.Show)

    def Show(self):
        self.pending = None
        if not self.text or not self.widget.winfo_exists():
            return
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        if sys.platform == 'darwin':
            try: # a borderless help window on macOS
                self.window.tk.call('::tk::unsupported::MacWindowStyle', 'style', self.window._w, 'help', 'none')
            except tk.TclError:
                pass
        try:
            self.window.wm_attributes('-topmost', True)
        except tk.TclError:
            pass
        tk.Label(self.window, text=self.text, justify=tk.LEFT, wraplength=wrapLength,
                 background=Theme.tooltipBackground, foreground=Theme.text, borderwidth=0,
                 highlightthickness=1, highlightbackground=Theme.border, highlightcolor=Theme.border,
                 padx=8, pady=5).pack()
        # below and to the right of the pointer, kept on the screen
        self.window.update_idletasks()
        x = self.widget.winfo_pointerx() + 12
        y = self.widget.winfo_pointery() + 20
        width, height = self.window.winfo_reqwidth(), self.window.winfo_reqheight()
        x = max(0, min(x, self.widget.winfo_screenwidth() - width - 4))
        if y + height > self.widget.winfo_screenheight() - 40:
            y = self.widget.winfo_pointery() - height - 8 # above the pointer instead
        self.window.wm_geometry('+%d+%d' % (x, y))

    def Hide(self, event=None):
        if self.pending:
            self.widget.after_cancel(self.pending)
            self.pending = None
        if self.window:
            self.window.destroy()
            self.window = None
        if event is not None and event.type != tk.EventType.Motion:
            self.text = None


def Add(widget, text):
    # a tooltip for a whole widget; returns the widget, so it can be used as
    #   Tooltips.Add(tk.Button(...), "...").pack()
    Tooltip(widget, lambda event: text)
    return widget


def AddToTabs(notebook, texts):
    # a tooltip for each tab of a ttk.Notebook, in tab order
    def TextAt(event):
        try:
            index = notebook.index('@%d,%d' % (event.x, event.y))
        except tk.TclError:
            return None
        return texts[index] if isinstance(index, int) and index < len(texts) else None
    Tooltip(notebook, TextAt)


def AddToTabTitles(notebook, textsByTitle):
    # a tooltip for each tab of a ttk.Notebook, by the tab's title
    def TextAt(event):
        try:
            index = notebook.index('@%d,%d' % (event.x, event.y))
            return textsByTitle.get(notebook.tab(index, 'text').strip())
        except tk.TclError:
            return None
    Tooltip(notebook, TextAt)


def AddToHeadings(treeview, textsByColumn):
    # a tooltip for each column heading of a ttk.Treeview
    def TextAt(event):
        if treeview.identify_region(event.x, event.y) != 'heading':
            return None
        column = treeview.identify_column(event.x) # '#1', '#2', ...
        try:
            identifier = treeview['columns'][int(column[1:]) - 1]
        except (ValueError, IndexError):
            return None
        return textsByColumn.get(identifier)
    Tooltip(treeview, TextAt)
