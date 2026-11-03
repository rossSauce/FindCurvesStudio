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
    interface.pack()
    root.title("tkinterFit - Curve And Surface Fitting Interface")

    # manually center the application window on the user display
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2) # integer division
    y = (root.winfo_screenheight() // 2) - (height // 2) # integer division
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    root.mainloop()
