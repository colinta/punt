"""Punter.  Watches current path (or another path) for changes and executes
command(s) when a change is detected.  Uses watchdog to track file changes.

Usage:
    punt [options] <commands>...
    punt (-h | --help)
    punt --version

Options:
    -w <path>, --watch <path>       Which path to watch [default: current directory]
    -l, --local                     Only tracks local files (disables recusive)
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


def run():
    arguments = docopt(__doc__, version='punt v1.4')

    if arguments['--watch'] == 'current directory':
        watch_path = os.getcwd()
    else:
        watch_path = os.path.abspath(arguments['--watch'])

    if not os.path.isdir(watch_path):
        sys.stderr.write("Error: {watch_path} does not exist".format(watch_path=watch_path))

    recursive = not arguments['--local']
    commands = arguments['<commands>']

    class Regenerate(FileSystemEventHandler):
        last_run = None

        def on_any_event(self, event, alert=True):
            if self.last_run and time.time() - self.last_run < .1:
                return

            try:
                print "Running..."
                for command in commands:
                    call(command, shell=True)
            except OSError as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
                sys.stderr.write("Error (%s): %s\n" % (type(e).__name__, e.message))
            self.last_run = time.time()

    observer = Observer()
    handler = Regenerate()

    sys.stderr.write('Watching "%s" for changes\n' % watch_path)
    observer.schedule(handler, path=watch_path, recursive=recursive)
    observer.start()

    try:
        sys.stderr.write('Listening...\n')
        handler.on_any_event(None, False)  # run the first time, no alert
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.stderr.write('!!! Stopping\n')
        observer.stop()
    observer.join()
