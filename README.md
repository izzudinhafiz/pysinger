# PySinger <!-- omit in toc -->

- [Introduction](#introduction)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Using tap and target names](#using-tap-and-target-names)
  - [Different executable name](#different-executable-name)
  - [Defining Tap or Target manually](#defining-tap-or-target-manually)

## Introduction
A [Singer.io](http://singer.io) wrapper Python library (that's fully type-annotated :D) that makes using Singer taps and targets easy.

This wrapper creates temporary virtual environment for each tap and target, download the required dependency and executes them. After execution, all environments are torn down and cleaned up.

## Requirements
- Linux only (Windows in the future? :|)
- Requires Python 3.7+.
- PySinger has no dependencies, it uses only Python built-in libraries.


## Installation
`pip install pysinger`

## Usage
### Using tap and target names
Use the tap/target names you would use to `pip install` them.

E.g. the tap would be `"tap-exchangeratehost"` if you'd used `pip install tap-exchangeratehost` to install it or target `"singer-target-postgres"` for `pip install singer-target-postgres`.

```python
from pysinger import Singer

tap_config = {
    "base": "JPY",
    "start_date": "2022-01-01"
}

target_config = {
    "delimiter": "\t",
    "quotechar": "'",
    "destination_path": ""
}

singer = Singer(
    "tap-exchangeratehost",
    "target-csv",
    tap_config=tap_config,          # Optional
    target_config=target_config     # Optional
)

end_state = singer.run()

# Optionally you can save the state for future use
singer.save_state("/path/to/state.json")
```

### Different executable name
By default PySinger executes tap/target by their name, but sometimes the executables are named differently.

For example `singer-target-postgres` uses a `target-postgres` as its executable. To run these:
```python
...
singer = Singer(
    "tap-exchangeratehost",
    "singer-target-postgres",
    tap_config=tap_config,
    target_config=target_config
    target_kwargs={"target_exec": "target-postgres"}
)

# Similarly there's one for taps called 'tap_exec'
...
```
To know what the executable name is, see the individual tap/target repo and check their invocation name.

Summary:
- `tap/target name` is from `pip install tap_or_target`
- `tap/target_exec` is from `virtualenv/tap_or_target/bin/tap_or_target_exec`

### Defining Tap or Target manually
You can also pass Tap or Target instances that were created manually
```python
from pysinger import Tap, Target, Singer

tap = Tap("tap-exchangerates", config_path="/path/to/config.json")

target = Target(
    "pipelinewise-target-postgres",
    target_exec="target-postgres",
    config={"disable_collection": True}
    )

singer = Singer(tap=tap, target=target)
singer.run()
```

