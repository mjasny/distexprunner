import experiment
import time
import config


class exp1(experiment.Base):
    SERVERS = [
        experiment.Server('node1', '127.0.0.1', custom_field=42)
    ]
    def experiment(self, target):
        long_cmd = target('node1').run_cmd('sleep 4', stdout=experiment.Printer(), stderr=experiment.Printer())

        target('node1').run_cmd('ls', stdout=experiment.Logfile('ls.log', append=True))
        # print(target('node1').data.custom_field)

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
        target('node1').run_cmd('sleep 5', stdout=experiment.Printer(), stderr=experiment.Printer())
        target('node2').run_cmd('sleep 10', stdout=experiment.Printer(), stderr=experiment.Printer()).wait()