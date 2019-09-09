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
    from sys import stdout
    from time import time
    from threading import current_thread, Thread

    # profile commands & constants
    self.CPU_STAT = [
        ["cat /proc/stat"],
        ["grep", "cpu[0-9]"],
        ["awk", "{print $2, $3, $4, $5, $6, $7, $8, $9}"],
    ]
    self.GPU_COL = ["GPU0", "VRAM", "TEMP", "DRAM"]
    self.GPU_STAT = [
        ["nvidia-smi"],
        ["grep", "Default"],
        ["awk", "{print $3, $9, $11, $13}"],
    ]
    self.MEM_STAT = [["free -m"], ["grep Mem"], ["awk", "{print $2, $3}"]]
    self.NUM_CORE = "nproc"
    self.STAT_COL = []

    # profiler window dimensions, refresh rate, & bar length
    self.height = 3
    self.length = None
    self.refresh = 0.5
    self.ticks = 30

    def __init__(self, enc="utf-8"):
        """
        Allocate datastructures and sys info
        """

        # grab logical core count for profiler window
        self.enc = enc
        self.NUM_CORE = int(check_output(self.NUM_CORE, encoding=self.enc))

        # setup stdout wrapper
        self.stdout = StdOutWrapper()
        stdout = self.stdout

        # setup profiler data buffers
        self.cols = math.ceil((self.NUM_CORE + len(self.MEM_STAT)) / self.height)
        self.prof_buffer = [[""] * self.height] * self.cols

        # setup label buffers to be 1:1 to data buffers
        j = 0
        for i in range(self.NUM_CORE // self.height):
            self.STAT_COL.append(["CPU" + c for c in range(j, i + j)])
            j = i
        self.STAT_COL.append(self.GPU_COL)

        # initialize curses and record terminal size
        self.term_win = curses.initscr()
        self.length = curses.COL

        # initialize profiler windows
        profiler_box = curses.newwin(self.height + 2, self.length)
        profiler_box.box()
        self.prof_win = profiler_box.derwin(self.height, self.length - 2, 1, 1)

        # initialize stdout windows
        stdout_box = curses.newwin(curses.LINES - self.height, self.length, height, 0)
        stdout_box.box()
        self.out_win = stdout_box.derwin(
            curses.LINES - self.height - 2, self.length - 2, 1, 1
        )
        self.out_win.scrollok(True)

        # render windows (well, boxes at this point)
        profiler_box.refresh()
        stdout_box.refresh()
        return

    def deinit():
        """
        Unloads curses library and restores terminal settings
        """
        pass
        return

    def stdout():
        """
        Parses anything ready for us on STDOUT
        """

        # call wrapper and add to curses window
        self.out_win.addstr(self.stdout.read())
        self.out_win.refresh()
        self.stdout.clear()
        return

    def mem_utilization():
        """
        Compute memory utilization from free -m
        """

        # run RAM command iteratively
        out = ""
        for command in self.MEM_STAT:
            out = check_output(command, input=out)
        return int(out[0]) / int(out[1])

    def cpu_utilization(prior_metrics):
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
            out = check_output(command, input=out)

        # compute performance difference from old and new
        metrics = array(
            [metric.split(" ") for metric in out.decode(self.enc)], dtype=int
        )
        user, nice, system, idle, iowait, irq, softirq, steal = subtract(
            metrics, prior_metrics
        ).T
        total = user + nice + system + idle + iowait + irq + softirq + steal
        nbusy = idle + iowait
        usage = total - nbusy

        # on the first run, we can sometimes divide by zero
        try:
            cpu_util = list(nan_to_num(usage / total))
        except:
            pass
        return cpu_util, metrics

    def gpu_utilization():
        """
        Compute GPU utilziation from nvidia-smi
        """

        # run GPU command iteratively
        out = ""
        for command in self.GPU_STAT:
            out = check_output(command, input=out)
        temp, mem_used, mem_total, gpu_util = out.decode(self.enc).split(" ")
        mem_util = int(mem_used.strip("MiB")) / int(mem_total.strip("MiB"))
        return temp, mem_util, gpu_util

    def compute_bars(metrics, tweak=1.03):
        """
        Return bars for the utilization of a given metrics
        """

        # compute bars for each metric
        elements_placed = 0
        for metric in metrics:
            for m in metric:

                # do not compute bars for string-typed metrics (ie temperature)
                if not isinstance(m, str):
                    self.prof_buffer[elements_placed % self.cols][
                        elements_placed // self.cols
                    ] = (
                        "["
                        + "|" * int(self.ticks * m)
                        + " " * int(self.ticks * (tweak - m))
                        + "]"
                    )
                else:
                    self.prod_buffer[elements_placed % self.cols][
                        elements_placed // self.cols
                    ] = m
                elements_placed += 1
        return

    def render_bars(cpu, gpu_mem):
        """
        Writes bars and refreshes curses profile window
        """

        # write bars to curses profile window
        for i in range(self.height):
            self.prof_win.addstr(
                [
                    " ".join(label, metric)
                    for label, metric in zip(self.STAT_COL[i], self.prof_buffer[i])
                ]
            )

        # refresh curses profile window
        self.prof_win.refresh()
        return

    def profile():
        """
        Main profiler function that obtains system metrics
        """

        # do some prep for the first update
        cpu_util, prior_cpu_util = self.cpu_utilization([[1] * 8] * self.NUM_CORE)
        update = time()

        # check if we've sent the stop signal
        while self.run_thread:

            # parse anything queued from STDOUT
            self.stdout()
            if time() - update >= self.refresh:

                # obtain metrics
                mem_util = self.mem_utilization()
                cpu_util, prior_cpu_util = self.cpu_utilization(prior_cpu_util)
                gpu_temp, gpu_mem, gpu_util = self.gpu_utilization()

                # compute bars and render
                bars = self.compute_bars(
                    [cpu_util, [gpu_util, gpu_mem, gpu_temp, mem_util]]
                )

                # render bars (and auxiliary measurements)
                self.render_bars(win, bars[0], [bars[3], gpu_temp, bars[1], bars[2]])
                update = time()
        return

    def start():
        """
        Starts profiler thread
        """

        # start in daemon mode in case things get wonky
        self.profile_thread = Thread(target=profile, args=(), daemon=True)
        self.run_thread = True
        self.profile_thread.start()
        return

    def stop():
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
        self.queue = deque()
        return

    # add STDOUT elements to queue
    def write(self, out):
        self.queue.append(out)
        return

    # "pop" STDOUT elements from queue (pair with clear())
    def read(self):
        return list(self.queue)

    # clear all elements from queue
    def clear(self):
        self.queue.clear()
        return


if __name__ == "__main__":
    """
    Profiler demo
    """

    from random import choice, randint
    from time import time

    # initialize curses
    stdscr = curses.initscr()

    # print some random words
    word_file = "/usr/share/dict/words"
    words = open(word_file).read().splitlines()
    while True:
        print(" ".join(choice(words) for i in range(randint(1, 30))))
        time.sleep(1)
    raise SystemExit(0)
