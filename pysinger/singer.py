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
        if self.end_state:
            with open(path, "w") as f:
                f.write(json.dumps(self.end_state))
        else:
            raise ValueError(
                "State has not been generated, maybe run() hasn't been called"
            )

    def run(self) -> Optional[Dict[str, Any]]:
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
