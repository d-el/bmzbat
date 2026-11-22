#!/usr/bin/python3
# Version: 0.1
# Storozhenko Roman

import time
import canopen
import struct
import textwrap
import argparse

NODE_ID = 0x41
ID_NMT = 0x080
TPDO_current = 0x180
TPDO_cells_voltage_03 = 0x1C0
TPDO_cells_voltage_47 = 0x200
TPDO_cells_voltage_811 = 0x240
TPDO_cells_voltage_1215 = 0x280
TPDO_temperature = 0x2C0

class batvals():
    id = None
    values = list()
    vmax = 0
    imax = 0
    vmin = 0
    imin = 0
    vd = 0
    voltage = 0
    current = 0
    temperatures = list()
    temperature = 0

    vtpdo = {}

    def __init__(self, id):
        self.id = id

    def handle_voltage(self, can_id, data):
        self.vtpdo[can_id] = data
        if TPDO_cells_voltage_03 in self.vtpdo and TPDO_cells_voltage_47 in self.vtpdo and TPDO_cells_voltage_811 in self.vtpdo and TPDO_cells_voltage_1215 in self.vtpdo:
            self.values = struct.unpack('<4H', self.vtpdo[TPDO_cells_voltage_03]) + struct.unpack('<4H', self.vtpdo[TPDO_cells_voltage_47]) + struct.unpack('<4H', self.vtpdo[TPDO_cells_voltage_811]) + struct.unpack('<4H', self.vtpdo[TPDO_cells_voltage_1215])
            self.vmax = max(self.values)
            self.imax = self.values.index(self.vmax) + 1
            self.vmin = min(self.values)
            self.imin = self.values.index(self.vmin) + 1
            self.vd = self.vmax - self.vmin
            self.voltage = sum(self.values)
            del self.vtpdo[TPDO_cells_voltage_03]
            del self.vtpdo[TPDO_cells_voltage_47]
            del self.vtpdo[TPDO_cells_voltage_811]
            del self.vtpdo[TPDO_cells_voltage_1215]

    def handle_temperature(self, can_id, data):
        self.temperatures = struct.unpack('<6b2x', data)
        self.temperature = max(self.temperatures)

bats = {}

def handle_tpdo_current(can_id, data, timestamp):
    id = can_id - TPDO_current
    value, value2 = struct.unpack_from("<hh", data, 0)
    bats[id].current = value / 100.0

def handle_tpdo_voltage_03(can_id, data, timestamp):
    node_id = can_id - TPDO_cells_voltage_03
    bats[node_id].handle_voltage(can_id - node_id, data)

def handle_tpdo_voltage_47(can_id, data, timestamp):
    node_id = can_id - TPDO_cells_voltage_47
    bats[node_id].handle_voltage(can_id - node_id, data)

def handle_tpdo_voltage_811(can_id, data, timestamp):
    node_id = can_id - TPDO_cells_voltage_811
    bats[node_id].handle_voltage(can_id - node_id, data)

def handle_tpdo_voltage_1215(can_id, data, timestamp):
    node_id = can_id - TPDO_cells_voltage_1215
    bats[node_id].handle_voltage(can_id - node_id, data)

def handle_tpdo_temperature(can_id, data, timestamp):
    node_id = can_id - TPDO_temperature
    bats[node_id].handle_temperature(can_id - node_id, data)

def handle_nmt(can_id, data, timestamp):
    id = can_id - ID_NMT
    if id not in bats:
        bats[id] = batvals(id)
        network.subscribe(TPDO_current + id, handle_tpdo_current)
        network.subscribe(TPDO_cells_voltage_03 + id, handle_tpdo_voltage_03)
        network.subscribe(TPDO_cells_voltage_47 + id, handle_tpdo_voltage_47)
        network.subscribe(TPDO_cells_voltage_811 + id, handle_tpdo_voltage_811)
        network.subscribe(TPDO_cells_voltage_1215 + id, handle_tpdo_voltage_1215)
        network.subscribe(TPDO_temperature + id, handle_tpdo_temperature)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='BMZ battery manager',
                        formatter_class=argparse.RawDescriptionHelpFormatter,
                        epilog=textwrap.dedent('''\
    Example:
        ./bat.py -i can0
        '''))
    ap.add_argument('-i', '--interface', required=False, default="can0", help='Interface')
    args = ap.parse_args()

    network = canopen.Network()
    network.connect(interface="socketcan", channel=args.interface)

    # Put Node 0x41 into OPERATIONAL state so it starts sending TPDOs
    node = network.add_node(NODE_ID, canopen.ObjectDictionary())
    node.nmt.state = "OPERATIONAL"

    # NMT subscribe
    for i in range(NODE_ID, NODE_ID + 16):
        network.subscribe(ID_NMT + i, handle_nmt)

    # View loop
    try:
        while True:
            time.sleep(1)
            for i in bats:
                b = bats[i]
                print(f"[{i-NODE_ID :02}]: {b.current :6.2f}A  {b.voltage / 1000.0 :6.3f}V T  {b.temperature}°C  Delta {b.vd :3}mV  Max[{b.imax :02}]{b.vmax}mV  Min[{b.imin :02}]{b.vmin}mV  {b.values}")
            print("-----------")

    except KeyboardInterrupt:
        network.disconnect()
