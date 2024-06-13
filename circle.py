import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation
from matplotlib.lines import Line2D
import serial
import crc

from threading import Thread, Event
from queue import Queue

RANGE = 3000
THRESHOLD = 150
PORT = "COM3"


NUM_POINTS = 12

start_bytes = b'\x54\x2c'
point = np.dtype([
    ("distance",    "<u2"),
    ("intensity",   "u1"),
    ])
packet = np.dtype([
    ("speed",       "<u2"),
    ("start_angle", "<u2"),
    ("data",        point,  (NUM_POINTS,)),
    ("end_angle",   "<u2"),
    ("timestamp",   "<u2"),
    ("crc",         "u1"),
])

crc_calculator = crc.Calculator(crc.Configuration(8, 0x4d))

def background_thread_func(stop:Event, queue:Queue):
    full_circle = []

    with serial.Serial(PORT, 230400, timeout=1) as port:
        while not stop.is_set():

            read = port.read_until(start_bytes)
            if read[-2:] != start_bytes:
                raise Exception("Couldn't find start bytes")

            buffer = port.read(packet.itemsize)
            data = np.frombuffer(buffer, packet)[0]

            if crc_calculator.checksum(start_bytes + buffer) != 0:
                #raise Exception("Bad CRC")
                print("Bad CRC")
                continue
            
            start_angle = data["start_angle"] * 0.01 * np.pi/180
            end_angle = data["end_angle"] * 0.01 * np.pi/180
            angles = np.linspace(start_angle, end_angle, NUM_POINTS)
            points = np.column_stack([data["data"]["distance"], angles])

            #Filter out noise
            points = points[data["data"]["intensity"] >= THRESHOLD]
            if len(points) == 0:
                continue

            reset_index = np.argmax(points[:, 1] < points[0, 1])
            if reset_index == 0:
                full_circle.extend(points)
            else:
                full_circle.extend(points[:reset_index, :])
                queue.put(np.array(full_circle))
                full_circle = list(points[reset_index:, :])


stop = Event()
queue = Queue()

background_thread = Thread(target=background_thread_func, args=(stop, queue))

fig = plt.figure()
line = plt.plot([-RANGE, RANGE], [-RANGE, RANGE], ".")[0]

def update(frame:int, queue: Queue, line:Line2D):
    points = None
    while not queue.empty():
        points = queue.get()
    if points is None:
        return
    x = points[:, 0] * np.cos(-points[:, 1])
    y = points[:, 0] * np.sin(-points[:, 1])
    line.set_xdata(x)
    line.set_ydata(y)
    
animation = matplotlib.animation.FuncAnimation(fig, update, fargs=(queue, line), interval=10)

background_thread.start()
plt.show()
stop.set()
            


