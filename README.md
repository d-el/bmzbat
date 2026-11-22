## Reverse engineering BMZ 2500Wh BMS

CAN Bus driver:
<img src="Pictures/candriver.png" style="zoom:25%;" />

Run: `./bat.py -i can0 -n 0x41`

Output:

`vBat 49.91V, Delta 51mV, Max[15] 3132mV, Min[3] 3081mV, (3098, 3127, 3081, 3128, 3107, 3119, 3116, 3124, 3126, 3123, 3129, 3125, 3125, 3125, 3132, 3124)`
`Current -9.96A, Power -497W  -3984`
`Temperature (23, 23, 24, 24, 23, 22)`
`Current -9.97A, Power -498W  -3984`
