"""
Prints various performance metrics of your system in real-time
"""


class PerformanceProfiler:
    """
    Reads performance metrics from popular NIX tools
    """

    import curses
    from math import ceil
    from numpy import array, nan_to_num, subtract
    from subprocess import check_output
    import sys
    from time import time
    from threading import current_thread, Thread

    # profile commands & constants
    CPU_STAT = [
        ["cat", "/proc/stat"],
        ["grep", "cpu[0-9]"],
        ["awk", "{print $2, $3, $4, $5, $6, $7, $8, $9}"],
    ]
    GPU_COL = ["GPU0 ", "VRAM ", "TEMP ", " DRAM "]
    GPU_STAT = [
        ["nvidia-smi"],
        ["grep", "Default"],
        ["awk", "{print $3, $9, $11, $13}"],
    ]
    MEM_STAT = [["free", "-m"], ["grep", "Mem"], ["awk", "{print $3, $4}"]]
    NUM_CORE = ["nproc"]
    STAT_COL = []

    def __init__(self, rows=3, refresh=0.5, ticks=20, enc="utf-8"):
        """
        Allocate datastructures and sys info
        """

        # setup stdout wrapper
        self.out = StdOutWrapper()
        PerformanceProfiler.sys.stdout = self.out
        PerformanceProfiler.sys.stderror = self.out

        # grab logical core count for profiler window
        self.enc = enc
        self.NUM_CORE = int(
            PerformanceProfiler.check_output(self.NUM_CORE, encoding=self.enc)
        )

        # profiler window dimensions & refresh rate
        self.rows = rows
        self.refresh = refresh
        self.ticks = ticks

        # setup 1:1 profiler data and label buffers
        self.cols = PerformanceProfiler.ceil(
            (self.NUM_CORE + len(self.GPU_COL)) / self.rows
        )
        self.prof_buffer = [["" for r in range(self.cols)] for c in range(self.rows)]
        stats = ["CPU" + str(c).ljust(2) for c in range(self.NUM_CORE)] + self.GPU_COL

        # ensure buffer sizes match - format label buffers to be 1:1 to profiler buffer
        stats += ["" for d in range(self.cols * self.rows - len(stats))]
        self.STAT_COL = [
            [stats[c + r * self.cols] for c in range(self.cols)]
            for r in range(self.rows)
        ]

        # initialize curses and record terminal size (hide cursor)
        self.term_win = PerformanceProfiler.curses.initscr()
        self.length = PerformanceProfiler.curses.COLS
        PerformanceProfiler.curses.curs_set(0)

        # initialize profiler windows
        profiler_box = PerformanceProfiler.curses.newwin(self.rows + 2, self.length)
        profiler_box.box()
        self.prof_win = profiler_box.derwin(self.rows, self.length - 2, 1, 1)

        # initialize stdout windows
        stdout_box = PerformanceProfiler.curses.newwin(
            PerformanceProfiler.curses.LINES - self.rows - 2,
            self.length,
            self.rows + 2,
            0,
        )
        stdout_box.box()
        self.out_win = stdout_box.derwin(
            PerformanceProfiler.curses.LINES - self.rows - 4, self.length - 2, 1, 1
        )
        self.out_win.scrollok(True)

        # render windows (well, boxes at this point)
        profiler_box.refresh()
        stdout_box.refresh()
        return

    def deinit(self):
        """
        Unloads curses library and restores terminal settings
        """
        PerformanceProfiler.stdout = PerformanceProfiler.sys.__stdout__
        return PerformanceProfiler.curses.endwin()

    def stdout(self):
        """
        Parses anything ready for us on STDOUT
        """

        # call wrapper and add to curses window
        self.out_win.addstr(self.stdout.read())
        self.out_win.refresh()
        return self.stdout.clear()

    def mem_utilization(self):
        """
        Compute memory utilization from free -m
        """

        # run RAM command iteratively
        out = ""
        for command in self.MEM_STAT:
            out = PerformanceProfiler.check_output(command, input=out)
        used, total = out.decode(self.enc).split()
        return int(used) / int(total)

    def cpu_utilization(self, prior_metrics):
        """
        Compute CPU utilization from /proc/stat via:
        total = user + nice + system + idle + iowait + irq + softirq + steal
        nbusy = idle + iowait
        usage = total - nbusy
        percentage = usage / total
        """

        # run CPU command iteratively
        out = ""
        for command in self.CPU_STAT:
            out = PerformanceProfiler.check_output(command, input=out)

        # compute performance delta
        metrics = self.array(
            [metric.split(" ") for metric in out.decode(self.enc).splitlines()],
            dtype=int,
        )
        user, nice, system, idle, iowait, irq, softirq, steal = PerformanceProfiler.subtract(
            metrics, prior_metrics
        ).T
        total = user + nice + system + idle + iowait + irq + softirq + steal
        nbusy = idle + iowait
        usage = total - nbusy

        # on the first run, we can sometimes divide by zero
        try:
            cpu_util = list(PerformanceProfiler.nan_to_num(usage / total))
        except:
            pass
        return cpu_util, metrics

    def gpu_utilization(self):
        """
        Compute GPU utilziation from nvidia-smi
        """

        # run GPU command iteratively
        out = ""
        for command in self.GPU_STAT:
            out = PerformanceProfiler.check_output(command, input=out)
        temp, mem_used, mem_total, gpu_util = out.decode(self.enc).split(" ")
        mem_util = int(mem_used.strip("MiB")) / int(mem_total.strip("MiB"))
        return temp, mem_util, gpu_util[:-1]  # (strip newline)

    def compute_bars(self, metrics):
        """
        Return bars for the utilization of a given metrics
        """

        # compute bars for each metric
        elements_placed = 0
        for metric in metrics:

            # do not compute bars for string-typed metrics (ie temperature)
            if not isinstance(metric, str):
                self.prof_buffer[elements_placed // self.cols][
                    elements_placed % self.cols
                ] = ("[" + ("|" * int(self.ticks * metric)).ljust(self.ticks) + "]")
            else:
                self.prof_buffer[elements_placed // self.cols][
                    elements_placed % self.cols
                ] = metric.ljust(self.ticks + 4 - len(metric))
            elements_placed += 1
        return

    def render_bars(self):
        """
        Writes bars and refreshes curses profile window
        """

        # write bars to curses profile window
        for i in range(self.rows):
            self.prof_win.addstr(
                i,
                0,
                " ".join(
                    [
                        " ".join((label, metric))
                        for label, metric in zip(self.STAT_COL[i], self.prof_buffer[i])
                    ]
                ),
            )

        # refresh curses profile window
        return self.prof_win.refresh()

    def profile(self):
        """
        Main profiler function that obtains system metrics
        """

        # do some prep for the first update
        cpu_util, prior_cpu_util = self.cpu_utilization([[1] * 8] * self.NUM_CORE)
        update = PerformanceProfiler.time()

        # check if we've sent the stop signal
        while self.run_thread:

            # parse anything queued from STDOUT
            out = self.out.read()
            if out:
                self.out_win.addstr(out)
                self.out_win.refresh()

            # refresh the performance montior if applicable
            if PerformanceProfiler.time() - update >= self.refresh:

                # obtain metrics
                mem_util = self.mem_utilization()
                cpu_util, prior_cpu_util = self.cpu_utilization(prior_cpu_util)
                gpu_temp, gpu_mem, gpu_util = self.gpu_utilization()

                # compute bars and render
                bars = self.compute_bars(
                    cpu_util + [gpu_util, gpu_mem, gpu_temp, mem_util]
                )

                # render bars (and auxiliary measurements)
                self.render_bars()
                update = PerformanceProfiler.time()
        return

    def start(self):
        """
        Starts profiler thread
        """

        # start in daemon mode in case things get wonky
        self.profile_thread = PerformanceProfiler.Thread(
            target=self.profile, daemon=True
        )
        self.run_thread = True
        return self.profile_thread.start()

    def stop(self):
        """
        Stops profiler thread
        """

        self.run_thread = False
        return


class StdOutWrapper:
    """
    STDOUT wrapper to make PP script-agnostic
    """

    from collections import deque

    # initilize queue for STDOUT
    def __init__(self):
        self.queue = StdOutWrapper.deque()
        return

    # add STDOUT elements to queue
    def write(self, out):
        self.queue.append(out)
        return

    # "pop" STDOUT elements from queue and clear
    def read(self):
        out = " ".join(list(self.queue))
        self.queue.clear()
        return out

    # forcibly empty the queue
    flush = read


if __name__ == "__main__":
    """
    Profiler demo
    """

    from random import choice, randint
    from time import sleep

    # instantiate profiler object and start
    profiler = PerformanceProfiler()
    profiler.start()

    # print some random words
    word_file = "/usr/share/dict/words"
    words = open(word_file).read().splitlines()
    while True:
        try:
            print(" ".join(choice(words) for i in range(randint(1, 30))))
            sleep(1)
        except:
            profiler.stop()
            profiler.deinit()
            raise SystemExit(-1)
    raise SystemExit(0)
