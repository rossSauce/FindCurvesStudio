import time, threading

import pyeq3


# Note that this thread never touches tkinter widgets directly, as tkinter
# is not thread-safe. All communication with the GUI is through the queue,
# which the GUI thread polls using tkinter's after() method.
class FittingThread(threading.Thread):
    def __init__(self, notify_window, equation):
        threading.Thread.__init__(self, daemon=True)
        self.queue = notify_window.queue
        self.equation = equation
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()


    def run(self):
        try:
            self.queue.put('Fitting data...')
            time.sleep(0.5) # allow users a moment to see the update
            self.equation.Solve()

            self.queue.put('Calculating model errors...')
            time.sleep(0.5) # allow users a moment to see the update
            self.equation.CalculateModelErrors(self.equation.solvedCoefficients, self.equation.dataCache.allDataCacheDictionary)

            self.queue.put('Calculating coefficient and fit statistics...')
            time.sleep(0.5) # allow users a moment to see the update
            self.equation.CalculateCoefficientAndFitStatistics()

            self.queue.put('Fitting complete, creating graphs and reports...')
            time.sleep(0.5) # allow users a moment to see the update
        except Exception as e:
            # report the error to the GUI thread rather than dying silently
            self.queue.put(e)
            return

        # the fitted equation is now the queue's data, rather than
        # a status update string.  The GUI handler checks the data type
        self.queue.put(self.equation)
