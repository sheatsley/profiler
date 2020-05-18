# Performance Profiler

<p align="center">
    <img src="https://github.com/sheatsley/profiler/blob/master/demo.gif?raw=true" alt="Performance Profiler in action"
</p>

Performance Profiler is a real-time CPU and GPU performance monitor for
Unix-like operating systems. Visually inspired by
[top](https://en.wikipedia.org/wiki/Top_(software), Performance Profiler shows
CPU, GPU, and RAM utilizations with a bar-like style. At its core, this script
is basically fancy parsers for
[/proc/stat](http://man7.org/linux/man-pages/man5/proc.5.html),
[free](http://man7.org/linux/man-pages/man1/free.1.html), and
[nvidia-smi](https://developer.download.nvidia.com/compute/DCGM/docs/nvidia-smi-367.38.pdf).
It relies on
[curses](https://en.wikipedia.org/wiki/Curses_(programming_library) for
manipulating the terminal.

Performance Profiler shows popular system performance metrics alongside output
by any arbitrary Python script. I wanted a simple and script-agnostic method
for monitoring system behavior as I ran my experiments, particularly those that
relied on GPUs. 

Using the module is straightforward: after instantiating `PerformanceProfiler`,
`start()` creates a thread daemon to collect performance data, monitors data
available on `stdout` by the script, and handles calls to `curses` for writing
to the terminal; `stop()` will, obviously, stop collecting performance metrics
and calls to `curses`; `deinit()` unloads `curses` and restores original
terminal functionality.

## Installation

To use Performance Profiler, simply `git clone` this repo, `import` the module,
and call the three functions above appropriately. A simple demo is shown at the
bottom of the script.
