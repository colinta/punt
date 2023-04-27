"""Punter.  Watches current path (or another path) for changes and executes
command(s) when a change is detected.  Uses watchdog to track file changes.

Usage:
    punt [-w <path> ...] [-l] [-t 5] <commands>...
    punt (-h | --help)
    punt --version

Options:
    -t <time>      Minimum time to delay between consecutive runs [default: 1]
    -w <path> ...  Which path(s) to watch
    -l             Only tracks local files (disables recusive)
"""
import time
import sys
import os
import os.path
import traceback
from subprocess import call

from docopt import docopt
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import pkg_resources  # part of setuptools
version = pkg_resources.require("punt")[0].version


def run():
    arguments = docopt(__doc__, version='punt ' + version)

    if not arguments['-w']:
        watch_paths = [os.getcwd()]
    else:
        watch_paths = []
        for watch in arguments['-w']:
            watch = os.path.abspath(watch)
            if not os.path.isfile(watch):
                sys.stderr.write("Error: {watch} does not exist".format(watch=watch))
            watch_paths.append(watch)

    recursive = not arguments['-l']
    try:
        timeout = float(arguments['-t'])
    except ValueError:
        sys.stderr.write("Error: 'timeout' must be a number\n")
        return
    commands = arguments['<commands>']

    class Regenerate(FileSystemEventHandler):
        last_run = None

        def on_any_event(self, event, alert=True):
            if self.last_run and time.time() - self.last_run < timeout:
                return
            self.last_run = time.time()

            try:
                sys.stderr.write("\033[2J\033[H\033[3J")
                sys.stderr.write('Watching %s for changes\n' % ', '.join(watch_paths))
                for command in commands:
                    desc = command.splitlines()[0]
                    if "\n" in command:
                        desc += "..."
                    sys.stderr.write("Running {0}\n".format(desc))
                    call(command, shell=True)
                sys.stderr.write("...done.\n")
            except OSError as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
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
        sys.stderr.write('!!! Stopping\n')
        observer.stop()
    observer.join()

if __name__ == "__main__":
    run()
