import json
import logging
from typing import Any, Optional, Dict, Union
from .target import Target, TargetRuntimeError
from .tap import Tap, TapRuntimeError
import subprocess


class Singer:
    def __init__(
        self,
        tap: Union[str, Tap],
        target: Union[str, Target],
        tap_config: Optional[Dict[str, Any]] = None,
        tap_state: Optional[Dict[str, Any]] = None,
        target_config: Optional[Dict[str, Any]] = None,
        tap_kwargs: Dict[str, Any] = {},
        target_kwargs: Dict[str, Any] = {},
    ) -> None:
        if isinstance(tap, Tap):
            self.tap = tap
        else:
            self.tap = Tap(tap, config=tap_config, state=tap_state, **tap_kwargs)

        if isinstance(target, Target):
            self.target = target
        else:
            self.target = Target(target, config=target_config, **target_kwargs)
        self._initialize()
        self.end_state: Optional[Dict[str, Any]] = None

    def _initialize(self):
        self.tap.initialize()
        self.target.initialize()

    def save_state(self, path: str):
        """Saves the state from when the last call to run or run_unsafe was executed

        Args:
            path (str): Absolute path to save the file to

        Raises:
            ValueError: There isnt a state to be save. Run run() or run_unsafe() first
        """
        if self.end_state:
            with open(path, "w") as f:
                f.write(json.dumps(self.end_state))
        else:
            raise ValueError(
                "State has not been generated, maybe run() hasn't been called"
            )

    def run(self) -> Optional[Dict[str, Any]]:
        """This runs the tap into the target. Guarantees that the process will stop

        Raises:
            RuntimeError: Either tap or target has failed to execute

        Returns:
            Optional[Dict[str, Any]]: Last state returned by the ingestion
        """
        logging.info(f"Running {self.tap.tap_name} | {self.target.target_name}")
        cmd = f"{self.tap.run_cmd} | {self.target.run_cmd};"
        proc = subprocess.run(cmd, capture_output=True, shell=True)
        stdout = proc.stdout.decode("utf-8").splitlines()
        stderr = proc.stderr.decode("utf-8").splitlines()

        if proc.returncode > 0:
            for line in stderr:
                logging.error(line)
            raise RuntimeError(
                f"Failed to execute {self.tap.tap_name} | {self.target.target_name}"
            )
        logging.info(f"Finished {self.tap.tap_name} | {self.target.target_name}")

        try:
            state = json.loads(stdout[-1])
        except Exception:
            state = None

        return state or {}

    def run_unsafe(self) -> Optional[Dict[str, Any]]:
        """This runs the tap into the target. Does not guarantees that the process will
        not hang in an infinite wait. Use this if you need more info on failure

        Raises:
            TapRuntimeError: Tap failed to execute for any reason
            TargetRuntimeError: Target failed to execute for any reason

        Returns:
            Optional[Dict[str, Any]]: Last state returned by the ingestion
        """
        logging.info(f"Running {self.tap.tap_name} | {self.target.target_name}")
        tap_proc = subprocess.Popen(self.tap.run_cmd.split(), stdout=subprocess.PIPE)

        target_proc = subprocess.Popen(
            self.target.run_cmd.split(),
            stdin=tap_proc.stdout,
            stdout=subprocess.PIPE,
        )
        last_line = None
        if target_proc.stdout:
            for line in target_proc.stdout:
                logging.info(line.decode("utf-8"))
                last_line = line.decode("utf-8")

        tap_proc.poll()
        target_proc.poll()
        logging.info(f"Finished {self.tap.tap_name} | {self.target.target_name}")

        if tap_proc.returncode and tap_proc.returncode > 0:
            raise TapRuntimeError()

        if target_proc.returncode and target_proc.returncode > 0:
            raise TargetRuntimeError()

        if last_line:
            state = json.loads(last_line)
            self.end_state = state
            return state

        return {}
