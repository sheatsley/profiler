"""
Prints various performance metrics of your system in real-time
"""

import numpy as np
import subprocess

CPU_STAT = [
    "cat",
    "/proc/stat",
    "|",
    "grep",
    "'cpu[0-9]'",
    "|",
    "awk" "{'print",
    "$2",
    "$3",
    "$4",
    "$5",
    "$6",
    "$7",
    "$8",
    "$9",
    "$10}",
]


def profile():
    """
    Prints CPU, RAM, and GPU utilization
    """
    return


def cpu_percentage(old, new):
    """
    Compute CPU usage as a percentage from /proc/stat via:
    total = user + nice + system + idle + iowait + irq + softirq + steal
    nbusy = idle + iowait
    usage = total - nbusy
    percentage = usage / total * 100
    """
    user, nice, system, idle, iowait, irq, softirq, steal = np.subtract(old, new)
    total = user + nice + system + idle + iowait + irq + softirq + steal
    nbusy = idle + iowait
    usage = total - nbusy
    return usage / total * 100


if __name__ == "__main__":

    # grab initial CPU stats

    return
