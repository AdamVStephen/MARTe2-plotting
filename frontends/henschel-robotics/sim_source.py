
#!/usr/bin/env python3
# 
#
# Ref https://henschel-robotics.ch/get-started/python-and-live-plot-example/
import math
import itertools
import pdb
import socket
import struct
import time
import threading
import signal
import matplotlib.pyplot as plt

def tcp_send_command_thread(stop_event):
    # Configure Socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Connect to motor
        s.connect(('192.168.1.102', 1000))

        # Compose String to send to the drive
        st = '"<control pos=\"15000\" frequency=\"20\" torque=\"200\" mode=\"135\" offset=\"0\" phase=\"0\" />"'
        s.sendall(st.encode('ascii')) # send XML command  
        
        # The main thread can continue executing other tasks
        while not stop_event.is_set():
            time.sleep(1)
    
def receive_udp_data(udp_port, stop_event, ring_buffer):
    index = 0
    # Configure Socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', udp_port))

        while not stop_event.is_set():
            data, addr = s.recvfrom(132) # buffer size is 132 bytes
            int_list = list(struct.unpack("<33i", data)) # interprete 33 int32 numbers
            
            # Update the ring buffer
            ring_buffer[index] = [int_list[0]*1e-3, int_list[1]/10.0, int_list[2]]
            index = (index + 1) % len(ring_buffer)

def keyboard_interrupt_handler(signal, frame):
    print("Keyboard interrupt received. Stopping the program.")
    # Set the stop event to signal the thread to exit
    stop_event.set()

    # Exit the program
    exit(0)

def build_data_packet(f, t0, t1 = 32):
    ms_timestamps = list(range(t0, t0 + t1))
    timestamps = [float(t) for t in ms_timestamps]
    datavals = [f(t) for t in timestamps]
    data = list(itertools.chain(*zip(timestamps, datavals)))
    pack_format="<%df" % len(data)
    #pdb.set_trace()
    packed_data = struct.pack(pack_format, *data)
    return (packed_data, t1)

     


def send_udp_data(frequency=100):
    # Create an array of 32 int32 values from 1 to 32

    data = list(range(1, 34))  # Python list of 32 integers
    # Pack the integers into a binary structure
    # Format: 32 signed int32 ('i')
    #packed_data = struct.pack('!33i', *data)  # ! = network byte order (big-endian), 32i = 32 int32s
    packed_data = struct.pack('<33i', *data)  # ! = network byte order (big-endian), 32i = 32 int32s

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Define the destination address (localhost:1000)
    server_address = ('127.0.0.1', 1025)

    time_ms = 0
    
    sine100 = lambda x : math.sin(2*math.pi*frequency*x)
    try:
        while True:
            # Send the packed data to the UDP socket
            (packed_data, t1) = build_data_packet(sine100, time_ms)
            bytes_to_send = len(packed_data)
            sock.sendto(packed_data, server_address)
            print("%d bytes Data sent to UDP socket on port 1001." % bytes_to_send)
            time_ms = t1 + 1
            time.sleep(0.01)
    finally:
        # Close the socket
        sock.close()
 
if __name__ == '__main__':
    stop_event = threading.Event()  # create an event object

    # Initialize the ring buffer
    ring_buffer = [[0, 0, 0] for i in range(10000)]

    # create a thread that receives on UDP port 1001    
    #udp_send_thread = threading.Thread(target=send_udp_data, args=(1001, stop_event, ring_buffer))
    udp_send_thread = threading.Thread(target=send_udp_data)
    udp_send_thread.start()

    # Install the keyboard interrupt handler
    signal.signal(signal.SIGINT, keyboard_interrupt_handler)

    # The main thread can continue executing other tasks
    while True:
        continue
