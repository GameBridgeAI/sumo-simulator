import time
import sys
import rpyc

print(sys.version_info)

print(rpyc.version)

conn = rpyc.connect('localhost', port=18861)  # host name or IP address of the EV3
bgsrv = rpyc.BgServingThread(conn)


def callback(ret):
    print(ret)


conn.root.init(callback)
conn.root.push_sensor_cmd(name="aaa")
conn.root.push_sensor_cmd(name="bbb")
conn.root.push_sensor_cmd(name="ccc")
conn.root.push_sensor_cmd(name="dddd")
conn.root.push_sensor_cmd(name="eee")
conn.root.push_sensor_cmd(name="fff")

time.sleep(120)

# conn.root.push_cmd("bbb")
# conn.root.push_cmd("ccc")
# conn.root.push_cmd("ddd")

# with open('server_script.py', 'r') as file:
#     script_text = file.read()
#     conn.execute(script_text)

bgsrv.stop()
conn.close()
