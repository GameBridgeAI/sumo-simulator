from threading import Thread
import datetime
import rpyc
import time


class Sensor(object):
    def __init__(self, value_ready_callback):
        self.callback = rpyc.async_(value_ready_callback)
        self.cmd_queue = []
        self.active = True
        self.thread = Thread(target=self.work)
        self.thread.start()

    def stop(self):
        self.active = False
        self.thread.join()

    def read_sensor(self, cmd):
        time.sleep(10)
        self.callback(datetime.datetime.now())

    def work(self):
        while self.active:
            time.sleep(5)
            if len(self.cmd_queue) > 0:
                print(self.cmd_queue)
                cmd_to_run = self.cmd_queue.pop(0)
                print(f'run cmd {cmd_to_run["name"]}')
                self.read_sensor(cmd_to_run)


class MyService(rpyc.Service):
    def __init__(self):
        self.sensor = None

    def on_connect(self, conn):
        pass

    def on_disconnect(self, conn):
        self.clear_sensor_if_exist()

    def clear_sensor_if_exist(self):
        if self.sensor is not None:
            self.sensor.stop()
            self.sensor = None

    def exposed_init(self, sensor_value_ready_callback):
        self.clear_sensor_if_exist()
        self.sensor = Sensor(sensor_value_ready_callback)

    def exposed_push_sensor_cmd(self, **kwargs):
        self.sensor.cmd_queue.append(kwargs)


if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer

    t = ThreadedServer(MyService, port=18861)
    t.start()
