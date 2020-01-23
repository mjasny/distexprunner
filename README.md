# distexprunner

A suite to write and run distributed experiments across multiple network nodes.


## Installation

The best way to integrate distexprunner in a project is to add it as a submodule:

```
mkdir distexperiments/ && cd distexperiments/
git submodule add https://github.com/mjasny/distexprunner
cp -r distexprunner/experiments .
```

At this stage you can already try the functionality by running locally the following commands in different shells. (e.g using `tmux`)

Start two server instances. They second instance requires a different port because both run on the same machine:

`python server.py`
`python server.py --port 20002`

Now a client is ready to connect to the servers and execute experiments.

`python client.py experiments/`

The folder parameter (`experiments/`) is the default path to recursively search for experiments.

*Note: For readability all commands only list the required executeable instead of the full path. In a current setup it would be e.g. `python3 distexprunner/server.py --port`*

## Writing experiments

```python
import experiment

config.CLIENT_IP = '127.0.0.1'

class exp2(experiment.Base):
    SERVERS = [
        experiment.Server('node1', '127.0.0.1', foobar=42)
    ]
    def experiment(self, target):
        procs = []
        for s in self.SERVERS:
            printer = experiment.Printer(fmt=f'{s.id}: '+'{line}')
            p = target(s.id).run_cmd('sleep 10', stdout=printer, stderr=printer)
            procs.append(p)

        rcs = [proc.wait() for proc in procs]
        assert(all(rc == 0 for rc in rcs))
```

Experiments should be placed into a separate folder (e.g. `experiments/`) and need to contain classes which need to inherit from `experiment.Base`. Other classes are ignored when scanning for experiments and can be used as helpers.
It is necessary to specify the IP address from which the experiments are started, because currently automatic resolution is not implemented. Tests need to have unique names and take the class-name by default as their name.
Each experiment class needs to provide a `SERVERS` list on which the experiments are run. In the preparation step it is verified that all servers are running. Servers need to have an unique identifier and an IP address. Optional values are the `port` which defaults to `CLIENT_PORT` in `config` or an arbitrary long list of keys for server specific data. These values can be accessed by using the attribute name via `Servers[x].data.foobar` or `target(x).data().foobar`.
When the experiment is executed its `experiment()` function is executed with the target parameter. It can be used to access data to a specific server or to spawn processes via `target(x).run_cmd()`. The supplied command is run without `shell=True` that means when you want to use logical expression you might need wrap it around with `bash -c "ping -c 1 {s.id} || echo 'Server unreachable'"`. Optional arguments are `stdout` and `stderr` which may take handlers for outputted lines from the process. `experiment.Printer()` and `experiment.Logfile()` are preimplemented. If a custom handler is needed a class instace needs to be supplied with a `__call__(self, line)` function.
Each run command returns an instance with the following callable methods:
- `.wait()` blocking call until the process finished execution. Returns the returncode of the process. Returns directly if the process already finished.
- `.kill()` terminates the running process forcefully.
-  `.stdin('\n')` can be called to send input over stdin to the process.

If the `experiment()` function returns before processes are terminated they are killed. So it is advised to use `.wait()` calls on running processes.


All experiments which are found in the experiment folder on the client-side are sorted numerically `['a_1', 'a_2', 'a_10', ...]` and executed in order.


### Experiment Factory

A factory pattern can be used to do parameterized grid executions. The factory is called for the kartesian product (`itertools.product`) of all parameters (e.g. `a` and `b`).

```python
def exp3_factory(a, b):
    class exp3(experiment.Base):
        SERVERS = [
            experiment.Server('node', '127.0.0.1')
        ]
        def experiment(self, target):
            cmd = f'./foobar -a {a} -b {b}'
            print(cmd)

    return exp3


a = ['x', 'y']
b = range(5, 10)
experiment.factory.Grid(exp3_factory, a, b)
```

This generates the following set of experiments:

```
experiments = [
    exp3_a_5, exp3_a_6, exp3_a_7, exp3_a_8, exp3_a_9, 
    exp3_b_5, exp3_b_6, exp3_b_7, exp3_b_8, exp3_b_9,
    exp3_c_5, exp3_c_6, exp3_c_7, exp3_c_8, exp3_c_9
]
```


## Usage

An example setup can be found in [experiments/example.py](experiments/example.py).
Please not that a common practice is to include a compile experiment named `AA_Compile` with the optional server feature which is run always before other experiments to make use of the newest program version. It can then also be used in a double filter setup, e.g. `python client.py --filter=AA_Compile --filter=<name>`.


## Client

```
usage: client.py [-h] [--filter FILTER] [folder]

Distributed Experiment Runner Client Instance

positional arguments:
  folder           experiment folder

optional arguments:
  -h, --help       show this help message and exit
  --filter FILTER  filter experiments by name
```

- `folder` defaults to `experiments/`
- `--filter` can be supplied multiple times and matches are run in order. Uses Unix-filename matching internally (e.g. `--filter=exper*`)


## Server

```
usage: server.py [-h] [--port [PORT]]

Distributed Experiment Runner Server Instance

optional arguments:
  -h, --help     show this help message and exit
  --port [PORT]  port for client connection
```

- `port` defaults to value specified in `config.py`
