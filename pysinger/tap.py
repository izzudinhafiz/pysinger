import venv
import logging
import json
from typing import Dict, Any, Optional
from tempfile import TemporaryDirectory
from subprocess import CalledProcessError, run


class TapCreateError(Exception):
    ...


class TapRuntimeError(Exception):
    ...


class Tap:
    def __init__(
        self,
        tap: str,
        tap_exec: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        state: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
        state_path: Optional[str] = None,
    ) -> None:
        self.tap_name = tap
        self.tap_exec = tap_exec or tap
        self.config = config
        self.state = state
        self.wdir = TemporaryDirectory()
        self.venv_path = f"{self.wdir.name}/{self.tap_name}"
        self.pip_path = f"{self.venv_path}/bin/pip"
        self.exec_path = f"{self.venv_path}/bin/"
        self.config_path = config_path or f"{self.wdir.name}/tap_config.json"
        self.state_path = state_path or f"{self.wdir.name}/tap_state.json"
        self.use_config_path = True if config_path else False
        self.use_state_path = True if state_path else False
        self._initialized = False

    def initialize(self) -> None:
        if not self._initialized:
            self.create_venv()
            self.install_tap()
            self.create_config_state_files()
            self._initialized = True

    def create_venv(self) -> None:
        logging.info(f"Creating virtualenv for {self.tap_name} at {self.venv_path}")
        venv.create(self.venv_path, with_pip=True)

    def install_tap(self, verbose: bool = False) -> None:
        logging.info(f"Installing {self.tap_name} in {self.venv_path}")
        cmd = f"{self.pip_path} install {self.tap_name}"
        proc = run(cmd.split(), capture_output=True)

        try:
            proc.check_returncode()
        except CalledProcessError:
            for line in proc.stderr.splitlines():
                logging.error(line.decode("utf-8"))
            raise TapCreateError(f"Failed to create {self.tap_name}")

        if verbose:
            for line in proc.stdout.splitlines():
                logging.info(line.decode("utf-8"))

    def create_config_state_files(self) -> None:
        if self.config:
            with open(self.config_path, "w") as f:
                f.write(json.dumps(self.config))

        if self.state:
            with open(self.state_path, "w") as f:
                f.write(json.dumps(self.state))

    @property
    def run_cmd(self) -> str:
        cmd = f"{self.exec_path}{self.tap_exec} "
        if self.config or self.use_config_path:
            cmd += f"--config {self.config_path} "

        if self.state or self.use_state_path:
            cmd += f"--state {self.state_path} "
        return cmd
