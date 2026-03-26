import logging
import os
import shutil
import subprocess
import tempfile
import threading
from functools import lru_cache
from io import BytesIO
from typing import IO

logger = logging.getLogger(__name__)


class ExifTool:
    # single instance
    _instance = None
    # thread safety
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ExifTool, cls).__new__(cls, *args, **kwargs)
                cls._instance._start_process()
        return cls._instance

    def _start_process(self):
        """Replace __init__"""

        # ExifTool (https://exiftool.org/)
        # persistence ExifTool process
        # args:
        #  -stay_open True: keep process running
        #  -@ -: read parameters from stdin
        # Capture stderr to stdout for easier error diagnostic
        try:
            self.process = subprocess.Popen(
                ["exiftool", "-stay_open", "True", "-@", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
            )
        except FileNotFoundError:
            logger.info("ExifTool not found. Some features will be disabled.")
            self.process = None

        self._counter = 0

    def execute(self, *args: str) -> str:
        """
        Execute a custom ExifTool command.
        Args:
            *args: Command line arguments for exiftool.
        Returns:
            The stdout response from ExifTool.
        """

        with self._lock:
            if self.process is None or self.process.poll() is not None:
                self._start_process()

            if self.process is None:
                raise RuntimeError("ExifTool process is not running.")

            try:
                self._counter += 1
                exec_id = self._counter
                sentinel = f"{{ready{exec_id}}}".encode("utf-8")

                # Prepare arguments, each on a new line as per -@ - format
                cmd_args = "\n".join(args) + f"\n-execute{exec_id}\n"
                self.process.stdin.write(cmd_args.encode("utf-8"))
                self.process.stdin.flush()

                # Read from stdout until we see the sentinel
                response = bytearray()
                while True:
                    chunk = self.process.stdout.read(4096)
                    if not chunk:
                        break
                    response.extend(chunk)
                    if sentinel in response:
                        break

                # Decode and strip the sentinel
                return (
                    response.decode("utf-8", errors="ignore")
                    .replace(f"{{ready{exec_id}}}", "")
                    .strip()
                )
            except Exception as e:
                logger.error(f"ExifTool execution failed: {e}")
                self.terminate()  # Reset process on error
                raise e

    def clean(self, data: IO, filename: str = None) -> BytesIO:
        with self._lock:
            if self.process is None or self.process.poll() is not None:
                self._start_process()

            if self.process is None:
                raise RuntimeError("ExifTool process is not running.")

            # prefer /dev/shm, makesure we are using tmpfs
            tmp_base = (
                "/dev/shm"
                if os.path.exists("/dev/shm") and os.access("/dev/shm", os.W_OK)
                else None
            )

            with tempfile.TemporaryDirectory(
                dir=tmp_base, prefix="blog-exiftool-"
            ) as tmp_dir:
                ext = os.path.splitext(filename)[-1] if filename else ""
                tmp_in_path = os.path.join(tmp_dir, f"input{ext}")
                tmp_out_path = os.path.join(tmp_dir, f"output{ext}")

                # Ensure data pointer is at the beginning
                if hasattr(data, "seekable") and data.seekable():
                    data.seek(0)

                with open(tmp_in_path, "wb") as f:
                    # noinspection PyTypeChecker
                    shutil.copyfileobj(data, f)

                try:
                    # file unique identifier
                    self._counter += 1
                    exec_id = self._counter
                    sentinel = f"{{ready{exec_id}}}".encode("utf-8")

                    # disable formater here, multiple lines is easy to read
                    # fmt: off
                    args = (
                        "-all=\n"
                        f"{tmp_in_path}\n"
                        "-o\n"
                        f"{tmp_out_path}\n"
                        f"-execute{exec_id}\n"
                    ).encode("utf-8")
                    # fmt: on

                    # send args
                    self.process.stdin.write(args)
                    self.process.stdin.flush()

                    # Read from stdout until we see the sentinel
                    response = bytearray()
                    while True:
                        chunk = self.process.stdout.read(4096)  # 4KiB
                        if not chunk:
                            break
                        response.extend(chunk)
                        if sentinel in response:
                            break

                    # Check if output file exists
                    if not os.path.exists(tmp_out_path):
                        # response might contain the error message
                        error_msg = (
                            response.decode("utf-8", errors="ignore")
                            .replace(f"{{ready{exec_id}}}", "")
                            .strip()
                        )
                        raise RuntimeError(
                            f"ExifTool failed: {error_msg or 'No output file created'}"
                        )

                    with open(tmp_out_path, "rb") as f:
                        return BytesIO(f.read())
                except Exception as e:
                    logger.error(f"ExifTool cleaning failed: {e}")
                    self.terminate()  # Reset process on error
                    raise e

    def terminate(self):
        if self.process:
            try:
                self.process.stdin.write(b"-stay_open\nFalse\n")
                self.process.stdin.flush()
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                if self.process:
                    self.process.kill()
                    self.process.wait()
            finally:
                self.process = None

    @staticmethod
    @lru_cache(1)
    def is_available() -> bool:
        try:
            subprocess.run(
                ["exiftool", "-ver"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            return True
        except Exception:
            return False
