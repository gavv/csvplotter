import subprocess
from multiprocessing import Process, Queue

class LogReader:
    def __init__(self, filepath):
        self.queue = Queue()
        self._tail = subprocess.Popen(['tail', '-F', filepath], stdout=subprocess.PIPE,
                                      universal_newlines=True)
        self._proc = Process(target=self._read)
        self._proc.start()

    def kill(self):
        self._tail.kill()
        self._proc.terminate()

    def _read(self):
        while True:
            line = self._tail.stdout.readline()
            if line:
                try:
                    parts = line.split(',')
                    fields = (parts[0],) + tuple(float(num) for num in parts[1:])
                    self.queue.put(fields)
                except:
                    pass
