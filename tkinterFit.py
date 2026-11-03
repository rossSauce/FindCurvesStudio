import multiprocessing


# The function finder fits equations in parallel worker processes.  On
# Windows each worker process re-imports this script, so the application
# must only be started when this script is run as the main program.
if __name__ == '__main__':
    # required for multiprocessing in a PyInstaller-built executable
    multiprocessing.freeze_support()

    import tkinter as tk
    import FittingInterface

    # Note that you can embed the application into
    # your own tkinter programs as shown here
    root = tk.Tk()
    interface = FittingInterface.InterfaceFrame(root)
    interface.pack(fill=tk.BOTH, expand=True)
    root.title("tkinterFit - Curve And Surface Fitting Interface")

    # center the window, limited to the size of the screen
    FittingInterface.SizeWindowToScreen(root)

    root.mainloop()
