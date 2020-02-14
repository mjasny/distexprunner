import experiment
import time
import config


class exp1(experiment.Base):
    SERVERS = [
        experiment.Server('node1', '127.0.0.1', custom_field=42)
    ]
    def experiment(self, target):
        long_cmd = target('node1').run_cmd('sleep 4', stdout=experiment.Printer(), stderr=experiment.Printer())

        target('node1').run_cmd('ls', stdout=[experiment.Printer(), experiment.Logfile('ls.log', append=True)])
        # self.SERVERS[0].data.custom_field = 69
        # print(target('node1').data().custom_field)

        printer = experiment.Printer(fmt='stdin="{line}"\n', rstrip=True)
        cmd = target('node1').run_cmd('bash -c "read p && echo $p"', stdout=printer)
        # cmd.kill()
        cmd.stdin('foobar\n')

        long_cmd.wait()     # We need to wait, else all running commands are killed


class exp2(experiment.Base):
    SERVERS = exp1.SERVERS + [
        experiment.Server('node2', '127.0.0.1', config.SERVER_PORT+1)
    ]
    def experiment(self, target):
        procs = []
        for i, s in enumerate(self.SERVERS):
            try:
                p = target(s.id).run_cmd(f'sleep {5*(i+1)}', stdout=experiment.Printer(), stderr=experiment.Printer())
            except experiment.errors.NoConnectionError:
                continue
            procs.append(p)

        rcs = [proc.wait() for proc in procs]
        assert(all(rc == 0 for rc in rcs))



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


class exp4(experiment.Base):
    SERVERS = [
        experiment.Server('node1', '127.0.0.1')
    ]
    def experiment(self, target):
        env = {
            'OMP_NUM_THREADS': 8
        }
        target('node1').run_cmd('env', stdout=experiment.Printer(), stderr=experiment.Printer(), env=env).wait()