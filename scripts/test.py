import time
import sys
import rpyc

print(sys.version_info)

print(rpyc.version)

conn = rpyc.connect('localhost', port=18861)  # host name or IP address of the EV3
bgsrv = rpyc.BgServingThread(conn)


conn.get_distance_sensor().add_to_cmd_queue(["get_distance_ahead"])
print(conn.get_distance_sensor().reading_results)
conn.get_wheel_controller().add_to_cmd_queue(["move_forward_cm", 40, 5])

# def callback(ret):
#     print(ret)
#
# conn.root.init(callback)
# conn.root.push_sensor_cmd(name="aaa")
# conn.root.push_sensor_cmd(name="bbb")
# conn.root.push_sensor_cmd(name="ccc")
# conn.root.push_sensor_cmd(name="dddd")
# conn.root.push_sensor_cmd(name="eee")
# conn.root.push_sensor_cmd(name="fff")
#
# time.sleep(120)


bgsrv.stop()
conn.close()
