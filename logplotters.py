import os
import time
from typing import List, Dict

import numpy as np


class BasePlotter:
    start_time = time.time_ns()

    def __init__(self, ax_, x_last_=90):
        self.ax = ax_
        self.x_last = x_last_
        self.measurements = {}
        self.ts = np.array([])

    def process_line(self, kval):
        for k, v in kval.items():
            if k == "ts":
                self.ts = np.append(self.ts, (v - self.start_time) / 1e9)
            else:
                if k in self.measurements:
                    self.measurements[k] = np.append(self.measurements[k], v)
                else:
                    self.measurements[k] = np.array([v])

        if len(self.ts) == 0:
            return

        x_last = self.ts[-1]
        x_first = max(self.ts[0], x_last - self.x_last)
        idx = np.where((self.ts >= x_first) & (self.ts <= x_last))
        self.ts = self.ts[idx]
        for k, v in self.measurements.items():
            self.measurements[k] = v[idx]

    def update_plot(self, x: np.array, args: List[Dict[str, np.array or str]],
                    ax=None, clear=True):
        if x.shape[0] < 1:
            return

        x_last = x[-1]
        x_first = max(x[0], x_last - self.x_last)
        if ax is None:
            ax = self.ax
        if clear:
            ax.clear()
        for y in args:
            idxs = np.where(x >= x_first)
            y["x"] = x[idxs]
            label = y["label"] if "label" in y else ""
            fmt = y["fmt"] if "fmt" in y else "-"
            ax.plot(x[idxs], y["y"][idxs], fmt, label=label)
        ax.legend()
        ax.set_xlim([x_first, x_last])


class JittPlotter(BasePlotter):
    def __init__(self, ax_):
        super().__init__(ax_)

    def process(self, line):
        # type, qts, sts, jitter, peak_jitter, envelope
        self.process_line({"ts": line[1],
                           "jitter": line[3],
                           "peak_jitter": line[4],
                           "envelope": line[5]})

    def replot(self):
        if self.measurements == {}:
            return

        self.update_plot(self.ts, [
            {"y": self.measurements["jitter"], "label": "Jitter, ms"},
            {"y": self.measurements["peak_jitter"] / 1e6, "label": "Peak Jitter, ms"},
            {"y": self.measurements["envelope"] / 1e6, "label": "Envelope, ms"}])


class LatencyPlotter(BasePlotter):
    def __init__(self, ax_):
        super().__init__(ax_)

    def process(self, line):
        # type, ts, niq_latency, target_latency
        self.process_line({"ts": line[1],
                           "niq_latency": line[2],
                           "target_latency": line[3]})

    def replot(self):
        if self.measurements == {}:
            return

        self.update_plot(self.ts, [
            {"y": self.measurements["niq_latency"] / 44100. * 1e3, "label": "NIQ lateny, ms"},
            {"y": self.measurements["target_latency"] / 44100. * 1e3, "label": "Target latency, ms"}])


class FreqEstimatorPlotter(BasePlotter):
    def __init__(self, ax_):
        self.accum_ax = ax_.twinx()
        super().__init__(ax_)

    def process(self, line):
        # type, ts, filtered, target, p, i
        self.process_line({"ts": line[1],
                           "filtered": line[2],
                           "target": line[3],
                           "p": line[4],
                           "i": line[5]})

    def replot(self):
        if self.measurements == {}:
            return

        self.update_plot(self.ts, [{"y": self.measurements["filtered"] / 44100 * 1e3,
                                    "label": "Filtered, ms"},
                            {"y": self.measurements["target"] / 44100 * 1e3,
                             "label": "Target, ms"}],
                  ax=self.ax,
                  clear=True)
        self.update_plot(self.ts, [{"y": self.measurements["p"], "label": "P", "fmt": "k-"},
                            {"y": self.measurements["i"], "label": "I", "fmt": "r-"}],
                  ax=self.accum_ax)


class DepacketizerPlotter(BasePlotter):
    def __init__(self, ax_):
        super().__init__(ax_)

    def process(self, line):
        # type, ts, missing, late, recovered
        self.process_line({"ts": line[1],
                           "missing": line[2],
                           "late": line[3],
                           "recovered": line[4]})

    def replot(self):
        if self.measurements == {}:
            return

        self.update_plot(self.ts, [
            {"y": self.measurements["missing"] / 44100. * 1e3, "label": "Missing samples, ms"},
            {"y": self.measurements["late"] / 44100. * 1e3, "label": "Late samples, ms"},
            {"y": self.measurements["recovered"] / 44100. * 1e3, "label": "Recovered samples, ms"}])
