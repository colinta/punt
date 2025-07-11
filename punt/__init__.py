"""Punter.  Watches current path (or another path) for changes and executes
command(s) when a change is detected.  Uses watchdog to track file changes.

Usage:
    punt [-i | --info] [-k | --keep] [-w <path> ...] [-l] [-t 5] [--] <commands>...
    punt (-h | --help)
    punt (-k | --keep)
    punt --version

Options:
    -t <time>      Minimum time to delay between consecutive runs [default: 1]
    -w <path>      Which path(s) to watch. Glob patterns are supported, multiple -w flags are supported.
    -i --info      Show command info
    -k --keep      Do not clear terminal between runs [default: false]
    -l             Only tracks local files (disables recusive)
"""
import datetime
import time
import sys
import os
import os.path
import traceback
import glob
import termios
import tty
import select
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
    keep = arguments["--keep"]
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
        is_running = False

        def __init__(self):
            self.old_settings = termios.tcgetattr(sys.stdin)
            super().__init__()

        def on_any_event(self, event, alert=True):
            if self.last_run and time.time() - self.last_run < timeout:
                return
            self.last_run = time.time()

            try:
                self.is_running = True
                if not keep:
                    sys.stderr.write("\033[2J\033[H\033[3J")
                    sys.stderr.flush()

                # Display which file changed if info flag is active
                if info and alert:
                    if event is not None:
                        file_path = event.src_path
                        event_type = event.event_type
                        sys.stderr.write(f"\x1B[36;2mFile {event_type}: {file_path}\x1B[0m\n")
                    else:
                        sys.stderr.write("\x1B[36;2mManual trigger: Enter key pressed\x1B[0m\n")

                last_status = None
                statuses = {}
                for command in commands:
                    desc = command.desc()

                    if info:
                        sys.stderr.write("\x1B[34;2mRunning {0}\x1B[0m\n".format(desc))

                    # Restore normal terminal mode for command execution
                    if self.old_settings:
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

                    last_status = command.run(shell)
                    statuses[command] = last_status

                    # Re-enable raw mode for keyboard input
                    if self.old_settings:
                        os.set_blocking(sys.stdin.fileno(), False)

                self.is_running = False

                if info:
                    for command in commands:
                        status = statuses[command]
                        write_status(status, command=command)
                    clock = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                    sys.stderr.write(f"\x1B[33;2mat {clock}\x1B[0m\n")
                    sys.stderr.write("\x1B[33;2mPress 'enter' to reload\x1B[0m\n")

            except OSError as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(
                    exc_type, exc_value, exc_traceback, file=sys.stderr
                )
                sys.stderr.write("Error (%s): %s\n" % (type(e).__name__, e.message))

    observer = Observer()
    handler = Regenerate()  # Will be updated with settings later

    for watch in watch_paths:
        observer.schedule(handler, path=watch, recursive=recursive)
    observer.start()

    try:
        # Set stdin to non-blocking mode
        os.set_blocking(sys.stdin.fileno(), False)
        
        handler.on_any_event(None, False)  # run the first time, no alert

        while True:
            if handler.is_running:
                time.sleep(0.5)
                continue
            # Check for keyboard input
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                if key == '\r' or key == '\n':  # Enter key
                    handler.on_any_event(None, True)
                elif key == '\x03':  # Ctrl+C
                    raise KeyboardInterrupt
                elif key == '\x1b':  # ESC key
                    raise KeyboardInterrupt
            
            time.sleep(0.1)  # Shorter sleep for more responsive keyboard input
    except KeyboardInterrupt:
        if info:
            sys.stderr.write("\x1b[31;2mStopping\x1b[0m\n")
        observer.stop()
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, handler.old_settings)
    observer.join()


if __name__ == "__main__":
    main()
