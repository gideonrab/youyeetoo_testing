import numpy as np
import serial
import crc

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

# Example from website. Used to sanity check CRC calculations
# test = bytes.fromhex("54 2C 68 08 AB 7E E0 00 E4 DC 00 E2 D9 00 E5 D5 00 E3 D3 00 E4 D0 00 E9 CD 00 E4 CA 00 E2 C7 00 E9 C5 00 E5 C2 00 E5 C0 00 E5 BE 82 3A 1A 50")

with serial.Serial("COM5", 230400, timeout=1) as port:
    # while((read_bytes := port.read_until(start_bytes))[-2:] != start_bytes):
    #     print(read_bytes.hex())
    read = port.read_until(start_bytes)
    if read[-2:] != start_bytes:
        raise Exception("Couldn't find start bytes")

    buffer = port.read(packet.itemsize)
    data = np.frombuffer(buffer, packet)[0]

    if crc_calculator.checksum(start_bytes + buffer) != 0:
        raise Exception("Bad CRC")
    
    start_angle = data["start_angle"] * 0.01# * np.pi/180
    end_angle = data["end_angle"] * 0.01# * np.pi/180
    angles = np.linspace(start_angle, end_angle, NUM_POINTS)

    print(f"{360 / data['speed']} Hz")
    print(f"{(data['end_angle'] - data['start_angle']) * 0.01 / (NUM_POINTS - 1)} deg/point")

    point_cloud = np.column_stack([data["data"]["distance"], angles])
    print(point_cloud)


