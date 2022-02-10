import logging
import venv
import json
from typing import Dict, Any, Optional
from tempfile import TemporaryDirectory
from subprocess import CalledProcessError, run


class TargetCreateError(Exception):
    ...


class TargetRuntimeError(Exception):
    ...


class Target:
    def __init__(
        self,
        target: str,
        target_exec: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
    ) -> None:
        self.target_name = target
        self.target_exec = target_exec or target
        self.config = config
        self.wdir = TemporaryDirectory()
        self.venv_path = f"{self.wdir.name}/{self.target_name}"
        self.pip_path = f"{self.venv_path}/bin/pip"
        self.exec_path = f"{self.venv_path}/bin/"
        self.config_path = config_path or f"{self.wdir.name}/target_config.json"
        self.use_config_path = True if config_path else False
        self._initialized = False

    def initialize(self) -> None:
        if not self._initialized:
            self.create_venv()
            self.install_target()
            self.create_config_file()
            self._initialized = True

    def create_venv(self) -> None:
        logging.info(f"Creating virtualenv for {self.target_name} at {self.venv_path}")
        venv.create(self.venv_path, with_pip=True)

    def install_target(self, verbose: bool = False) -> None:
        logging.info(f"Installing {self.target_name} in {self.venv_path}")
        cmd = f"{self.pip_path} install {self.target_name}"
        proc = run(cmd.split(), capture_output=True)

        try:
            proc.check_returncode()
        except CalledProcessError:
            for line in proc.stderr.splitlines():
                logging.error(line.decode("utf-8"))
            raise TargetCreateError(f"Failed to create {self.target_name}")

        if verbose:
            for line in proc.stdout.splitlines():
                logging.info(line.decode("utf-8"))

    def create_config_file(self) -> None:
        if self.config:
            with open(self.config_path, "w") as f:
                f.write(json.dumps(self.config))

    @property
    def run_cmd(self) -> str:
        cmd = f"{self.exec_path}{self.target_exec} "
        if self.config or self.use_config_path:
            cmd += f"--config {self.config_path} "

        return cmd
