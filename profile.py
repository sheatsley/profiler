"""
Prints various performance metrics of your system in real-time
"""

import itertools
import numpy as np
import subprocess
import time

CPU_STAT = "cat /proc/stat | grep 'cpu[0-9]' | awk {'print $2, $3, $4, $5, $6, $7, $8, $9, $10'}"
GPU_STAT = "nvidia-smi | grep Default | awk {'print $3, $9, $11, $13'}"
MEM_STAT = "free -m | grep m | awk {'print $2, $3'}"


def module_start():
    """
    The Magic Sauce
    """
    return


def profile(refresh=0.5):
    """
    Prints CPU, RAM, and GPU utilization at refresh rate
    """

    # initialize CPU utilization to 0 and grab num_cpus
    cpu_util, old = cpu_utilization([0] * 8)
    NUM_CPUS = len(cpu_util)
    while True:

        # obtain metrics
        mem_util = mem_utilization()
        cpu_util, old = cpu_utlization(old)
        gpu_temp, gpu_mem, gpu_util = gpu_utilization()

        # compute bars
        bars = compute_bars([cpu_util, gpu_util, gpu_mem, mem_util])

        # render bars (and auxiliary measurements)
        render(bars[0], bars[1], bars[2], gpu_temp)

        # wait for refresh
        time.sleep(refresh)
    return


def render(cpu, gpu, mem, gpu_temp, rx=0, ry=0):
    """
    Writes bars (strings) to STDOUT, resets cursor to rx, ry
    Assumes stat order is CPU, GPU, MEM
    """

    # write bars to STDOUT
    gpu.append(gpu_temp)
    for b, i in enumerate(itertools.zip_longest(cpu, gpu, mem, fillvalue="")):
        print(
            "CPU",
            i,
            b[0],
            *("GPU ", i, b[1]) if bool(b[1]) else ("",),
            *("MEM ", i, b[2]) if bool(b[2]) else ("",)
        )

    # reset cursor position
    print("\033[" + rx + ";" + ry + "H")
    return


def compute_bars(metrics, ticks=30):
    """
    Return bars for the utilization of a given metrics
    """
    bars = []
    for metric in metrics:

        # metric should be a list if we're dealing with something like CPU cores
        if type(metric) is list:
            bar = []
            for m in metric:
                b = "[" + "|" * int(ticks * m) + " " * int(ticks * (1 - m)) + "]"
                bar.append(b)
            bars.append(bar)
        else:
            bars.append("[" + "|" * int(ticks * m) + " " * int(ticks * (1 - m)) + "]")
    return bars


def gpu_utilization():
    """
    Compute GPU utilziation from nvidia-smi
    """
    temp, mem_used, mem_total, gpu_utilization = (
        subprocess.run(GPU_STAT, shell=True, stdout=subprocess.PIPE)
        .stdout.decdoe("utf-8")
        .split(" ")
    )
    mem_utilization = int(mem_used.strip("MiB")) / int(mem_total.strip("MiB")) * 100
    return float(temp[:-1]), mem_utilization, float(gpu_utilization[:-1])


def cpu_utilization(old):
    """
    Compute CPU utilization from /proc/stat via:
    total = user + nice + system + idle + iowait + irq + softirq + steal
    nbusy = idle + iowait
    usage = total - nbusy
    percentage = usage / total * 100
    """
    new = subprocess.run(CPU_STAT, shell=True, stdout=subprocess.PIPE).stdout.decode(
        "utf-8"
    )
    new = np.array([cpu.split(" ") for cpu in new], dtype=int)
    user, nice, system, idle, iowait, irq, softirq, steal = np.subtract(old, new)
    total = user + nice + system + idle + iowait + irq + softirq + steal
    nbusy = idle + iowait
    usage = total - nbusy
    return usage / total * 100, new


def mem_utilization():
    """
    Compute memory utilization from free -m
    """
    total, usage = (
        subprocess.run(MEM_STAT, shell=True, stdout=subprocess.PIPE)
        .stdout.decode("utf-8")
        .split(" ")
    )
    return int(usage) / int(total) * 100


if __name__ == "__main__":
    """
    For debugging only
    """
    profile()
    raise SystemExit(0)
