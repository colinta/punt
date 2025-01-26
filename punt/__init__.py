"""Punter.  Watches current path (or another path) for changes and executes
command(s) when a change is detected.  Uses watchdog to track file changes.

Usage:
    punt [-i | --info] [-w <path> ...] [-l] [-t 5] [--] <commands>...
    punt (-h | --help)
    punt --version

Options:
    -t <time>      Minimum time to delay between consecutive runs [default: 1]
    -w <path>      Which path(s) to watch. Glob patterns are supported, multiple -w flags are supported.
    -i --info      Show command info
    -l             Only tracks local files (disables recusive)
"""
import datetime
import time
import sys
import os
import os.path
import traceback
import glob
from subprocess import call, run

from docopt import docopt
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import importlib.metadata

version = importlib.metadata.version("punt")
puntrc = os.path.expanduser("~/.puntrc")
shell = run("echo $SHELL", shell=True, capture_output=True)
shell = shell.stdout.decode("utf-8").strip()


class Command:
    def __init__(self, command, puntrc):
        self.command = command
        self.puntrc = puntrc

    def desc(self):
        desc = self.command.splitlines()[0]
        if "\n" in self.command:
            desc += "..."
        return desc

    def run(self, shell):
        command = self.command
        if os.path.isfile(self.puntrc):
            command = f"source {puntrc} ; {command}"
        return call(command, shell=True, executable=shell)


def write_status(status, command):
    if status == 0:
        sys.stderr.write("\x1B[32;2m`" + command.desc() + "` -> 0\x1B[0m\n")
    else:
        sys.stderr.write(
            "\x1B[31;2m`" + command.desc() + "` -> " + str(status) + "\x1B[0m\n"
        )


def main():
    arguments = docopt(__doc__, version="punt " + version)
    info = arguments["--info"]
    watch_paths = []

    if not arguments["-w"]:
        watch_paths.append(os.getcwd())
    else:
        for watch in arguments["-w"]:
            watch = os.path.abspath(watch)
            if not os.path.isfile(watch):
                paths = glob.glob(watch, recursive=True)
                if not paths:
                    sys.stderr.write(
                        "Error: {watch} does not exist\n".format(watch=watch)
                    )
                    return
                for path in paths:
                    watch_paths.append(path)
            else:
                watch_paths.append(watch)

    recursive = not arguments["-l"]
    try:
        timeout = float(arguments["-t"])
    except ValueError:
        sys.stderr.write("Error: 'timeout' must be a number\n")
        return

    commands = list(
        map(
            lambda c: Command(c, puntrc),
            arguments["<commands>"],
        )
    )

    class Regenerate(FileSystemEventHandler):
        last_run = None

        def on_any_event(self, event, alert=True):
            if self.last_run and time.time() - self.last_run < timeout:
                return
            self.last_run = time.time()

            try:
                sys.stderr.write("\033[2J\033[H\033[3J")
                sys.stderr.flush()

                last_status = None
                statuses = {}
                for command in commands:
                    desc = command.desc()

                    if info:
                        sys.stderr.write("\x1B[34;2mRunning {0}\x1B[0m\n".format(desc))

                    last_status = command.run(shell)
                    statuses[command] = last_status

                if info:
                    for command in commands:
                        status = statuses[command]
                        write_status(status, command=command)
                    clock = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                    sys.stderr.write(f"\x1B[33;2mat {clock}\x1B[0m\n")

            except OSError as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(
                    exc_type, exc_value, exc_traceback, file=sys.stderr
                )
                sys.stderr.write("Error (%s): %s\n" % (type(e).__name__, e.message))

    observer = Observer()
    handler = Regenerate()

    for watch in watch_paths:
        observer.schedule(handler, path=watch, recursive=recursive)
    observer.start()

    try:
        handler.on_any_event(None, False)  # run the first time, no alert
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if info:
            sys.stderr.write("!!! Stopping\n")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
