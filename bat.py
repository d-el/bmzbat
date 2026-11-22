#!/usr/bin/python3
# Version: 0.1
# Storozhenko Roman

import time
import canopen
import struct
import textwrap
import argparse

ap = argparse.ArgumentParser(description='BMZ battery viever',
                    formatter_class=argparse.RawDescriptionHelpFormatter,
                    epilog=textwrap.dedent('''\
Example:
    ./bat.py -i can0 -n 0x41
    '''))
ap.add_argument('-i', '--interface', required=True, help='Interface')
ap.add_argument('-n', '--nodeid', required=True, default='', help='node id')
args = ap.parse_args()

NODE_ID = int(args.nodeid, 16)

TPDO_current = 0x180 + NODE_ID
TPDO_cells_voltage_03 = 0x1C0 + NODE_ID
TPDO_cells_voltage_47 = 0x200 + NODE_ID
TPDO_cells_voltage_811 = 0x240 + NODE_ID
TPDO_cells_voltage_1215 = 0x280 + NODE_ID
TPDO_temperature = 0x2C0 + NODE_ID

network = canopen.Network()
network.connect(interface="socketcan", channel=args.interface)

# Put Node 0x41 into OPERATIONAL state so it starts sending TPDOs
node = network.add_node(NODE_ID, canopen.ObjectDictionary())
node.nmt.state = "OPERATIONAL"

tpdoData = {}

def handle_tpdo(can_id, data, timestamp):
    #print(f"COB-ID 0x{can_id:03X} | Data: {data.hex(' ')}")
    tpdoData[can_id] = data


for cob_id in (TPDO_current, TPDO_cells_voltage_03, TPDO_cells_voltage_47, TPDO_cells_voltage_811, TPDO_cells_voltage_1215, TPDO_temperature):
    network.subscribe(cob_id, handle_tpdo)

vbat = 0

try:
    while True:
        time.sleep(0.1)
        if TPDO_cells_voltage_03 in tpdoData and TPDO_cells_voltage_47 in tpdoData and TPDO_cells_voltage_811 in tpdoData and TPDO_cells_voltage_1215 in tpdoData:
            values = struct.unpack('<4H', tpdoData[TPDO_cells_voltage_03]) + struct.unpack('<4H', tpdoData[TPDO_cells_voltage_47]) + struct.unpack('<4H', tpdoData[TPDO_cells_voltage_811]) + struct.unpack('<4H', tpdoData[TPDO_cells_voltage_1215])
            vmax = max(values)
            imax = values.index(vmax) + 1
            vmin = min(values)
            imin = values.index(vmin) + 1
            vd = vmax - vmin
            vbat = sum(values)
            print(f"vBat {vbat/1000 :.02f}V, Delta {vd}mV, Max[{imax}] {vmax}mV, Min[{imin}] {vmin}mV, {values}")
            del tpdoData[TPDO_cells_voltage_03]
            del tpdoData[TPDO_cells_voltage_47]
            del tpdoData[TPDO_cells_voltage_811]
            del tpdoData[TPDO_cells_voltage_1215]

        if TPDO_current in tpdoData:
            value, value2 = struct.unpack_from("<hh", tpdoData[TPDO_current], 0)
            current  = value / 100.0
            print(f"Current {current :.2f}A, Power {current*vbat/1000 :.0f}W ", value2)
            del tpdoData[TPDO_current]
            
        if TPDO_temperature in tpdoData:
            values = struct.unpack('<6b2x', tpdoData[TPDO_temperature])
            print(f"Temperature {values}")
            del tpdoData[TPDO_temperature]

except KeyboardInterrupt:
    network.disconnect()
