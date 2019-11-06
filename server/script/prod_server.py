import ctypes
import inspect
import threading
from threading import Thread
import datetime
import rpyc
import time
from time import sleep
import ev3dev2
from ev3dev2.motor import LargeMotor, MoveSteering, MoveTank, OUTPUT_B, OUTPUT_C
from ev3dev2.sensor.lego import UltrasonicSensor, ColorSensor
from ev3dev2.sensor import INPUT_4, INPUT_1, INPUT_2
from ev3dev2.sound import Sound


# A thread class that can be terminated
# https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
class ThreadWithException(Thread):
    def get_id(self):
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def try_terminate(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Failed to terminate thread ' + thread_id)
        else:
            print('Thread ' + thread_id + " terminated")


class QueuedTaskRunner(object):
    def __init__(self):
        self.cmd_queue = []
        self.reading_results = []
        self.reading_results_limit = 200
        self.active = True
        self.loop_thread = Thread(target=self.work)
        self.task_thread = None
        self.loop_thread.start()

    def stop(self):
        self.active = False

        if self.task_thread:
            self.task_thread.try_termniate()
        self.loop_thread.join()

    def work(self):
        while self.active:
            time.sleep(0.1)
            # when no task is running
            if self.task_thread is None:
                # our queue is not empty
                if len(self.cmd_queue) > 0:
                    # print(self.cmd_queue)

                    cmd_to_run = self.cmd_queue.pop(0)

                    cmd_name = cmd_to_run[0]

                    # reflection, find a method named 'handle_cmd_name', return None if not found
                    target_func = getattr(self, "handle_" + cmd_name, None)

                    if target_func is not None:
                        print('run sensor cmd ' + cmd_name)
                        self.task_thread = ThreadWithException(target=target_func, args=cmd_to_run[1:])
                        self.task_thread.start()
                    else:
                        print('cannot find handler for cmd ' + cmd_name + ', skipping')

    def try_terminate_current_task(self):
        if self.task_thread is None:
            print('no active task is running. Nothing to terminate')
        else:
            self.task_thread.try_termniate()

    def add_to_cmd_queue(self, cmd):
        self.cmd_queue.append(cmd)

    def clear_cmd_queue(self, cmd):
        self.cmd_queue.clear()


class DistanceSensor(QueuedTaskRunner):  # should only create one instance of this
    def __init__(self):
        self.ultrasound = UltrasonicSensor(INPUT_2)
        super(DistanceSensor, self).__init__()

    def handle_get_distance_ahead(self):
        while len(self.reading_results) >= self.reading_results_limit:
            self.reading_results.pop(0)
        self.reading_results.append(self.ultrasound.distance_centimeters)


class WheelController(QueuedTaskRunner):  # should only create one instance of this
    def __init__(self):
        self.safe_clearance_ahead = 200
        self.steer_pair = MoveSteering(OUTPUT_B, OUTPUT_C, motor_class=LargeMotor)
        self.tank_pair = MoveTank(OUTPUT_B, OUTPUT_C, motor_class=LargeMotor)
        super(WheelController, self).__init__()

    def handle_keep_going_forward(self, speed, reading):
        while True:
            if len(reading) > 0 and reading[-1] > self.safe_clearance_ahead:
                degrees_to_run = 360
                self.steer_pair.on_for_degrees(steering=0, speed=speed, degrees=degrees_to_run)
                # no need for delay
            else:
                print("not safe to move forward")
                sleep(2)  # prevent logging crazily

    def handle_move_forward_cm(self, cm, speed):
        degrees_to_run = cm / 17.5 * 360
        self.steer_pair.on_for_degrees(steering=0, speed=speed, degrees=degrees_to_run)

    def handle_spin_left_degrees(self, deg, speed):
        degrees_to_turn = deg * 197.5 / 90
        self.steer_pair.on_for_degrees(steering=-100, speed=speed, degrees=degrees_to_turn)

    def handle_spin_right_degrees(self, deg, speed):
        degrees_to_turn = deg * 197.5 / 90
        self.steer_pair.on_for_degrees(steering=+100, speed=speed, degrees=degrees_to_turn)

    def handle_turn_right_degrees(self, deg, speed):
        degrees_to_turn = deg * 403 / 90
        self.tank_pair.on_for_degrees(speed, 0, degrees_to_turn)

    def handle_turn_left_degrees(self, deg, speed):
        degrees_to_turn = deg * 403 / 90
        self.tank_pair.on_for_degrees(0, speed, degrees_to_turn)

    def handle_turn_left_rotations(self, rot, speed):
        self.tank_pair.on_for_rotations(0, speed, rot)

    def handle_turn_right_rotations(self, rot, speed):
        self.tank_pair.on_for_rotations(speed, 0, rot)


class MyService(rpyc.Service):
    def __init__(self):
        self.distance_sensor = None
        self.wheel_controller = None

    def on_connect(self, conn):
        pass

    def on_disconnect(self, conn):
        self.clear_sensor_if_exist()

    def clear_sensor_if_exist(self):
        if self.distance_sensor is not None:
            self.distance_sensor.stop()
            self.distance_sensor = None
        if self.wheel_controller is not None:
            self.wheel_controller.stop()
            self.wheel_controller = None

    def exposed_init(self):
        self.clear_sensor_if_exist()
        self.distance_sensor = DistanceSensor()
        self.wheel_controller = WheelController()

    def exported_get_distance_sensor(self):
        return self.distance_sensor

    def exported_get_wheel_controller(self):
        return self.wheel_controller

if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer

    t = ThreadedServer(MyService, port=18861)
    t.start()
