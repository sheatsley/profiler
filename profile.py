"""
Prints various performance metrics of your system in real-time
"""

import curses
import itertools
import numpy as np
import shutil
import subprocess
import sys
import time
import threading

CPU_STAT = (
    "cat /proc/stat | grep 'cpu[0-9]' | awk {'print $2, $3, $4, $5, $6, $7, $8, $9'}"
)
GPU_STAT = "nvidia-smi | grep Default | awk {'print $3, $9, $11, $13'}"
MEM_STAT = "free -m | grep m | awk {'print $2, $3'}"
GPU_COL = [" RAM", " TMP", " GPU", "VRAM"]


class StdOutWrapper:
    text = ""

    def write(self, txt):
        self.text += txt
        self.text = "\n".join(self.text.split("\n")[-30:])

    def get_text(self):
        return "\n".join(self.text.split("\n"))


mystdout = StdOutWrapper()
sys.stdout = mystdout


def module_start(ticks=30, refresh=0.5, rx=0, ry=0):
    """
    Handler for the profiler (using curses). 
    Params:
    - ticks: length of bars
    - refresh: how often we should redraw the screen (time.sleep)
    - ry: space between the top of the terminal and profiler
    """

    # grab CPU count
    num_cpus = int(
        subprocess.run(["nproc"], stdout=subprocess.PIPE).stdout.decode("utf-8")
    )

    # compute profiler placement on right side of terminal (_CPU_XX_[ticks]_VRAM_[ticks]_)
    height = max(num_cpus, len(GPU_COL)) + 2
    length = ticks * 2 + 19

    # create curses window
    if True:
        win = curses.newwin(height, length, ry, rx)
        win.box()
        p = threading.Thread(target=profile, args=(win, ticks, refresh, rx, ry), daemon=True)
        p.start()

    if True:
        mw = curses.newwin(curses.LINES - height, curses.COLS, ry + height+20, rx)
        mw.scrollok(True)
        #mw.box()
        m = threading.Thread(target=main_update, args=(mw,), daemon=True)
        m.start()

    return


def main_update(mw):
    while True:
        mw.addstr(mystdout.get_text())
        mw.refresh()
    return


def profile(win, ticks, refresh=0.5, rx="0", ry="0"):
    """
    Prints CPU, RAM, and GPU utilization at refresh rate
    """

    # initialize CPU utilization to 0 and grab num_cpus
    num_cpus = int(
        subprocess.run(["nproc"], stdout=subprocess.PIPE).stdout.decode("utf-8")
    )
    cpu_util, old = cpu_utilization([[1] * CPU_STAT.count("$")] * num_cpus)
    while True:

        # obtain metrics
        mem_util = mem_utilization()
        cpu_util, old = cpu_utilization(old)
        gpu_temp, gpu_mem, gpu_util = gpu_utilization()

        # compute bars
        bars = compute_bars([cpu_util, gpu_util, gpu_mem, mem_util], ticks=ticks)

        # render bars (and auxiliary measurements)
        render(
            stdscr, win, bars[0], [bars[3], gpu_temp, bars[1], bars[2]], rx=rx, ry=ry
        )

        # wait for refresh
        time.sleep(refresh)
    return


def render(stdscr, win, cpu, gpu_mem, rx="0", ry="0"):
    """
    Writes bars (strings) to STDOUT, resets cursor to rx, ry
    """

    # write bars to STDOUT (grab current cursor position)
    for i, b in enumerate(itertools.zip_longest(cpu, gpu_mem, fillvalue="")):
        win.addstr(
            i + 1,
            1,
            " ".join(
                [
                    "CPU",
                    str(i).rjust(2),
                    b[0],
                    " ".join((GPU_COL[i], b[1])) if bool(b[1]) else "",
                ]
            ),
        )

    # refresh the window and restore cursor position
    win.refresh()
    # curses.endwin()
    return


def compute_bars(metrics, ticks=30, buf=1.03):
    """
    Return bars for the utilization of a given metrics
    """
    bars = []
    for metric in metrics:

        # metric should be a list if we're dealing with something like CPU cores
        if type(metric) is list:
            bar = []
            for m in metric:
                b = "[" + "|" * int(ticks * m) + " " * int(ticks * (buf - m)) + "]"
                bar.append(b)
            bars.append(bar)
        else:
            bars.append(
                "["
                + "|" * int(ticks * metric)
                + " " * int(ticks * (buf - metric))
                + "]"
            )
    return bars


def gpu_utilization():
    """
    Compute GPU utilziation from nvidia-smi
    """
    temp, mem_used, mem_total, gpu_utilization = (
        subprocess.run(GPU_STAT, shell=True, stdout=subprocess.PIPE)
        .stdout.decode("utf-8")
        .split(" ")
    )
    mem_utilization = int(mem_used.strip("MiB")) / int(mem_total.strip("MiB"))
    return temp[:-1], mem_utilization, float(gpu_utilization[:-2])


def cpu_utilization(old):
    """
    Compute CPU utilization from /proc/stat via:
    total = user + nice + system + idle + iowait + irq + softirq + steal
    nbusy = idle + iowait
    usage = total - nbusy
    percentage = usage / total
    """
    new = (
        subprocess.run(CPU_STAT, shell=True, stdout=subprocess.PIPE)
        .stdout.decode("utf-8")
        .splitlines()
    )
    new = np.array([cpu.split(" ") for cpu in new], dtype=int)
    user, nice, system, idle, iowait, irq, softirq, steal = np.subtract(new, old).T
    total = user + nice + system + idle + iowait + irq + softirq + steal
    nbusy = idle + iowait
    usage = total - nbusy
    return list(np.nan_to_num(usage / total)), new


def mem_utilization():
    """
    Compute memory utilization from free -m
    """
    total, usage = (
        subprocess.run(MEM_STAT, shell=True, stdout=subprocess.PIPE)
        .stdout.decode("utf-8")
        .split(" ")
    )
    return int(usage) / int(total)


if __name__ == "__main__":
    """
    For debugging only
    """
    import random

    # initialize curses
    stdscr = curses.initscr()
    module_start()
    while True:
        print(random.randint(1, 100))
        time.sleep(0.25)
    raise SystemExit(0)
