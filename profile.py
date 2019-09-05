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
    "$2,",
    "$3,",
    "$4,",
    "$5,",
    "$6,",
    "$7,",
    "$8,",
    "$9,",
    "$10'}",
]
GPU_STAT = [
    "nvidia-smi",
    "|",
    "grep",
    "Default",
    "|",
    "awk",
    "{'print",
    "$3,",
    "$9,",
    "$11,",
    "$13'}",
]
MEM_STAT = ["free", "-m", "|", "grep", "m", "|", "awk", "{'print", "$2,", "$3'}"]


def profile():
    """
    Prints CPU, RAM, and GPU utilization
    """
    return


def bars(metric, ticks=30):
    """
    Return bars for the utilization of a given metric
    """
    
    # metric should be a list if we're dealing with something like CPU cores
    if type(metric) is list:
        bars = []
        for m in metric:


    return


def cpu_utilization(old, new):
    """
    Compute CPU utilization from /proc/stat via:
    total = user + nice + system + idle + iowait + irq + softirq + steal
    nbusy = idle + iowait
    usage = total - nbusy
    percentage = usage / total * 100
    """
    new = subprocess.run(CPU_STAT, stdout=subprocess.PIPE).stdout.readlines()
    new = np.array([cpu.split(" ") for cpu in new], dtype=int)
    user, nice, system, idle, iowait, irq, softirq, steal = np.subtract(old, new)
    total = user + nice + system + idle + iowait + irq + softirq + steal
    nbusy = idle + iowait
    usage = total - nbusy
    return str(usage / total * 100) + "%"


def gpu_utilization():
    """
    Compute GPU utilziation from nvidia-smi
    """
    temp, mem_used, mem_total, gpu_utilization = (
        subprocess.run(GPU_STAT, stdout=subprocess.PIPE)
        .stdout.decdoe("utf-8")
        .split(" ")
    )
    mem_utilization = (
        str(int(mem_used.strip("MiB")) / int(mem_total.strip("MiB")) * 100) + "%"
    )
    return temp, mem_utilization, gpu_utilization


def mem_utilization():
    """
    Compute memory utilization from free -m
    """
    total, usage = (
        subprocess.run(MEM_STAT, stdout=subprocess.PIPE)
        .stdout.decode("utf-8")
        .split(" ")
    )
    return str(int(usage) / int(total) * 100) + "%"


if __name__ == "__main__":

    # grab initial CPU stats

    return
