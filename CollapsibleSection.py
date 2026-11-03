# A section with a clickable header that shows or hides its contents,
# used to keep the main window compact on small screens.

import tkinter as tk


class CollapsibleSection(tk.Frame):
    # Put the section's widgets in self.body.  Extra header widgets, such as
    # buttons, can be packed into self.headerExtras.

    def __init__(self, parent, title, expanded=True, expandBody=False):
        tk.Frame.__init__(self, parent)
        self.title = title
        self.expandBody = expandBody # if the body should fill extra space when resized

        header = tk.Frame(self)
        header.pack(fill=tk.X)
        self.toggleButton = tk.Label(header, font="-weight bold", cursor='hand2', anchor=tk.W)
        self.toggleButton.pack(side=tk.LEFT)
        self.toggleButton.bind('<Button-1>', lambda e: self.Toggle())
        self.summaryLabel = tk.Label(header, fg='gray35', anchor=tk.W, cursor='hand2')
        self.summaryLabel.pack(side=tk.LEFT, padx=(6, 0))
        self.summaryLabel.bind('<Button-1>', lambda e: self.Toggle())
        self.headerExtras = tk.Frame(header)
        self.headerExtras.pack(side=tk.RIGHT)
        tk.Frame(self, height=1, background='gray70').pack(fill=tk.X, pady=(1, 3))

        self.body = tk.Frame(self)
        self.expanded = not expanded
        self.Toggle()


    def Toggle(self):
        self.expanded = not self.expanded
        if self.expanded:
            self.body.pack(fill=tk.BOTH, expand=self.expandBody, padx=(14, 0))
        else:
            self.body.pack_forget()
        self.toggleButton.config(text=('▼  ' if self.expanded else '▶  ') + self.title)
        self.UpdateSummaryVisibility()
        # let the parent container recalculate its layout
        self.event_generate('<<SectionToggled>>')


    def SetSummary(self, text):
        # a short description shown in the header while the section is collapsed
        self._summary = text
        self.UpdateSummaryVisibility()


    def UpdateSummaryVisibility(self):
        text = getattr(self, '_summary', '')
        self.summaryLabel.config(text='' if self.expanded else text)
