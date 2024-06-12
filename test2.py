import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation
from matplotlib.lines import Line2D
import serial
import crc

RANGE = 12000

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


full_circle = []

with serial.Serial("COM5", 230400, timeout=1) as port:
    while True:

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

        reset_index = np.argmax(points[:, 1] < points[0, 1])

        print(points)
        print(points[:, 1] < points[0, 1])
        if reset_index == 0:
            full_circle.extend(points)
        else:
            full_circle.extend(points[:reset_index, :])
            print(np.array(full_circle))
            quit()
            full_circle = list(points[reset_index:, :])