import sys
import time

import pathos
from pathos.connection import Pipe

ROBOT_IP = '127.0.0.1'
PYTHON3_PATH = '~/.pyenv/shims/python3.7'
PIP3_PATH = '~/.pyenv/shims/pip3'


def install_requirements():
    upload_file('requirements.txt', False)
    s = pathos.core.execute(PIP3_PATH + ' install -r requirements.txt', host=ROBOT_IP)
    print(s.response())


def upload_file(filename, script=True):
    dest = ROBOT_IP + ':~/' + filename
    mid_path = 'script/' if script else ''
    print('copying from ./' + mid_path + filename + ' to: '+ dest)
    pathos.core.copy('./' + mid_path + filename, destination=dest)


def run_python_file(filename, print_response=True):
    s = pathos.core.execute(PYTHON3_PATH + ' ' + filename, host=ROBOT_IP)
    if print_response:
        print(s.response())
    return s.pid()


# this does not work.
def kill_remote_process(pid, include_children=True):
    children = pathos.core.getchild(pid, ROBOT_IP)
    print(children)
    for child in children:
        kill_remote_process(child)
    res = pathos.core.kill(pid, ROBOT_IP)
    print(res)


# this does not work.
def run_classic_server_file():
    pid = run_python_file('./rpyc_classic.py --port=16666')
    print('server running with pid ' + pid)


def run_server_file(filename):
    pipe = Pipe(ROBOT_IP)
    pipe(command=PYTHON3_PATH + filename)
    pipe.launch()
    while True:
        time.sleep(0.1)
        print(str(pipe._stdout.readline(),'utf-8'), end='')


def home_made_kill_all_processes_with_filename(filename):
    pathos.core.execute('pkill -f ' + filename, ROBOT_IP)


# # 0.1 test upload file
# upload_file('./script/print_hostname.py')
#
# # 0.2 test run file
# run_server_file('~/print_hostname.py')
#
# # 1. install requirements
# install_requirements()
#
# # 2. upload production server script
# upload_file('prod_server.py')
#
# # 3. run production server
run_server_file('~/prod_server.py')

# 3.1 run classic server for quick dev. Does not work.
# run_classic_server_file()

# # 4. kill server
# home_made_kill_all_processes_with_filename('prod_server.py')
