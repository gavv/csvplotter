#!/usr/bin/env python3

import os
import queue
import signal
import sys
import time

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle

from logreader import LogReader
from logplotters import JittPlotter, LatencyPlotter, FreqEstimatorPlotter

if __name__ == '__main__':
    reader = LogReader(sys.argv[1])

    def die(*args, **kw):
        reader.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, die)

    mplstyle.use('fast')

    fig = plt.figure()
    fig.canvas.mpl_connect('close_event', die)

    ax1 = fig.add_subplot(311)
    ax2 = fig.add_subplot(312)
    ax3 = fig.add_subplot(313)

    plotters = {'f': [FreqEstimatorPlotter(ax3), 0],
                't': [LatencyPlotter(ax2), 0],
                'm': [JittPlotter(ax1), 0]}

    time_start = time.time_ns()
    time_print = time_start
    unrecognized_processor_cntr = 0
    lines_s = 0

    interval = 0.1

    while True:
        first = True
        while True:
            try:
                if first:
                    line = reader.queue.get(block=True, timeout=interval)
                else:
                    line = reader.queue.get_nowait()
            except queue.Empty:
                break

            first = False
            lines_s += 1
            discriminator = line[0]
            if discriminator not in plotters:
                unrecognized_processor_cntr += 1
                continue

            cur_time = time.time_ns()
            plotters[discriminator][0].process(line)
            plotters[discriminator][1] += time.time_ns() - cur_time

        for plotter in plotters.values():
            cur_time = time.time_ns()
            plotter[0].replot()
            plotter[1] += time.time_ns() - cur_time

        plt.pause(interval)
        cur_time = time.time_ns()
        if cur_time - time_print > 1e9:
            for k in plotters.keys():
                print(f"Processor {k}: {plotters[k][1] / (cur_time - time_start) * 100.:.2f}%")
            print(f"Unrecognized processor: {unrecognized_processor_cntr}")
            print(f"Lines per second: {lines_s}")
            print(f"Queue size: {reader.queue.qsize()}")
            print(f"Overtime: {(cur_time - time_print - 1e9) / 1e9}s")
            time_print = time.time_ns()
            lines_s = 0

    plt.show()
