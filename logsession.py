#!/usr/bin/env python3
import subprocess
import sys
import os
import select
from datetime import datetime

def logsession_unix(logfile, shell=None):
    if shell is None:
        shell = os.environ.get("SHELL", "/bin/bash")

    print(f"Logging started. Output will be saved to: {logfile}")

    import pty
    import termios
    import tty
    import fcntl

    with open(logfile, "a", buffering=1) as log:
        log.write(f"--- Session started {datetime.now()} ---\n")
        log.flush()

        master_fd, slave_fd = pty.openpty()

        # Copy terminal size to pty
        if sys.stdin.isatty():
            size = fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, b'\x00' * 8)
            fcntl.ioctl(master_fd, termios.TIOCSWINSZ, size)

        # Launch as interactive login shell to load profile
        proc = subprocess.Popen(
            [shell, "-i", "-l"],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            preexec_fn=os.setsid,
            env=os.environ.copy()
        )

        os.close(slave_fd)

        old_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())

        try:
            while proc.poll() is None:
                try:
                    rlist, _, _ = select.select([sys.stdin, master_fd], [], [], 0.1)
                except (ValueError, OSError):
                    break

                for fd in rlist:
                    if fd == sys.stdin:
                        try:
                            data = os.read(sys.stdin.fileno(), 1024)
                            if data:
                                os.write(master_fd, data)
                                if b'\r' in data or b'\n' in data:
                                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    log.write(f"\n@@@ {timestamp}\n")
                                    log.flush()
                        except OSError:
                            break

                    elif fd == master_fd:
                        try:
                            data = os.read(master_fd, 1024)
                            if data:
                                text = data.decode("utf-8", errors="replace")
                                sys.stdout.write(text)
                                sys.stdout.flush()
                                log.write(text)
                                log.flush()
                            else:
                                break
                        except OSError:
                            break

        except (IOError, OSError):
            pass

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            os.close(master_fd)
            log.write(f"\n--- Session ended {datetime.now()} ---\n")

    print(f"\nLogging stopped. Output saved to: {logfile}")


def logsession_windows(logfile, shell=None):
    try:
        from winpty import PtyProcess
    except ImportError:
        print("Error: pywinpty is required for Windows support.")
        print("Install it with: pip install pywinpty")
        sys.exit(1)

    import threading
    import time
    import msvcrt
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32

    if shell is None:
        shell = "powershell.exe"

    print(f"Logging started. Output will be saved to: {logfile}")

    # Enable virtual terminal processing
    STD_OUTPUT_HANDLE = -11
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

    stdout_handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    stdout_mode = wintypes.DWORD()
    kernel32.GetConsoleMode(stdout_handle, ctypes.byref(stdout_mode))
    kernel32.SetConsoleMode(stdout_handle, stdout_mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)

    with open(logfile, "a", buffering=1, encoding="utf-8") as log:
        log.write(f"--- Session started {datetime.now()} ---\n")
        log.flush()

        try:
            size = os.get_terminal_size()
            cols, rows = size.columns, size.lines
        except OSError:
            cols, rows = 120, 30

        # Use PtyProcess.spawn() - this is the correct API
        proc = PtyProcess.spawn(shell, dimensions=(rows, cols))

        running = True

        def read_output():
            nonlocal running
            while running:
                try:
                    if proc.isalive():
                        data = proc.read(1024)
                        if data:
                            sys.stdout.write(data)
                            sys.stdout.flush()
                            log.write(data)
                            log.flush()
                    else:
                        running = False
                        break
                except EOFError:
                    running = False
                    break
                except Exception as e:
                    time.sleep(0.01)

        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()

        # Give the shell time to start and show prompt
        time.sleep(0.5)

        try:
            while running and proc.isalive():
                if msvcrt.kbhit():
                    char = msvcrt.getwch()

                    if char == '\x00' or char == '\xe0':
                        ext = msvcrt.getwch()
                        key_map = {
                            'H': '\x1b[A',  # Up
                            'P': '\x1b[B',  # Down
                            'M': '\x1b[C',  # Right
                            'K': '\x1b[D',  # Left
                            'G': '\x1b[H',  # Home
                            'O': '\x1b[F',  # End
                            'S': '\x1b[3~', # Delete
                        }
                        if ext in key_map:
                            proc.write(key_map[ext])
                    elif char == '\r':
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log.write(f"\n@@@ {timestamp}\n")
                        log.flush()
                        proc.write('\r\n')
                    elif char == '\x03':
                        proc.write('\x03')
                    elif char == '\x04':
                        break
                    elif char == '\x08':  # Backspace
                        proc.write('\x08')
                    elif char == '\t':  # Tab
                        proc.write('\t')
                    else:
                        proc.write(char)

                time.sleep(0.001)

        except (IOError, OSError, KeyboardInterrupt):
            pass

        finally:
            running = False
            time.sleep(0.1)
            kernel32.SetConsoleMode(stdout_handle, stdout_mode.value)
            try:
                proc.terminate(force=True)
            except Exception:
                pass
            log.write(f"\n--- Session ended {datetime.now()} ---\n")

    print(f"\nLogging stopped. Output saved to: {logfile}")


def logsession(logfile="session.log", shell=None):
    # Handle duplicate filenames
    base, ext = os.path.splitext(logfile)
    counter = 1
    while os.path.exists(logfile):
        logfile = f"{base}-{counter}{ext}"
        counter += 1

    if sys.platform == "win32":
        logsession_windows(logfile, shell)
    else:
        logsession_unix(logfile, shell)


if __name__ == "__main__":
    logfile = sys.argv[1] if len(sys.argv) > 1 else "session.log"
    logsession(logfile)
