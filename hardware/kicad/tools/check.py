#!/usr/bin/env python3
"""Compare the KiCad-exported netlist with the intended Ghost Fader connectivity.
IC / jack / module pins are exact ("U1.3"); 2-terminal passives are listed by ref ("C1"), meaning one of its pins."""
import sys, xml.etree.ElementTree as ET
from collections import defaultdict

# (name, exact pins, passives) -- hand-written from the design, independent of gen.py geometry.
DEC_P15 = ['C21', 'C23', 'C25', 'C28', 'C31', 'C33', 'C35', 'C40', 'C42']
DEC_M15 = ['C22', 'C24', 'C26', 'C29', 'C32', 'C34', 'C36', 'C41', 'C43']
DEC_P5 = ['C27', 'C30', 'C14']
EXPECTED = [
    ('GND', ['J1.S', 'J1.TN', 'J2.S', 'J2.TN', 'J3.S', 'J4.S', 'U1.1', 'U2.1', 'U3.5', 'U3.10', 'U3.15', 'U4.5', 'U4.10', 'U4.15',
             'U6.3', 'U7.3', 'U9.13', 'SW1.1', 'SW1.2', 'SW1.3', 'SW1.4', 'LED1.1', 'PS1.2', 'PS1.5'],
     ['C1', 'C2', 'C7', 'C8', 'C9', 'C10', 'C15', 'C16', 'R4', 'R8', 'R15', 'C11', 'C12', 'C13'] + DEC_P15 + DEC_M15 + DEC_P5),
    ('+12V', ['U1.7', 'U2.7', 'U3.12', 'U4.12', 'U5.8', 'U6.6', 'U7.6'], ['L1', 'C12'] + DEC_P15),
    ('-12V', ['U1.4', 'U2.4', 'U3.13', 'U4.13', 'U5.4', 'U6.5', 'U7.5'], ['L2', 'C13'] + DEC_M15),
    ('+5V', ['PS1.1', 'U3.1', 'U3.4', 'U4.1', 'U4.4'], ['FB1', 'C11'] + DEC_P5),
    ('+3V3', ['U9.12'], ['R1', 'R14']),
    ('USB_5V', ['U9.14'], ['FB1']),
    ('L tip', ['J1.T', 'U1.3'], ['C1']), ('L ring', ['J1.R', 'U1.2'], ['C2']),
    ('R tip', ['J2.T', 'U2.3'], ['C7']), ('R ring', ['J2.R', 'U2.2'], ['C8']),
    ('SENSE_L', ['J1.RN', 'U9.1'], ['R1']), ('SENSE_R', ['J2.RN', 'U9.2'], ['R14']),
    ('L_SE', ['U1.5', 'U1.6'], ['C3', 'C5']), ('R_SE', ['U2.5', 'U2.6'], ['C4', 'C6']),
    ('U3 inL', ['U3.16'], ['C3']), ('U3 inR', ['U3.9'], ['C4']), ('U4 inL', ['U4.16'], ['C5']), ('U4 inR', ['U4.9'], ['C6']),
    ('SCLK', ['U9.9', 'U3.6', 'U4.6'], []), ('SDI', ['U9.11', 'U3.3'], []), ('U3_SDO', ['U3.7', 'U4.3'], []),
    ('/CS', ['U9.8', 'U3.2', 'U4.2'], []), ('/MUTE', ['U9.7', 'U3.8', 'U4.8'], ['R15']),
    ('U3 outL', ['U3.14'], ['R2']), ('U4 outR', ['U4.11'], ['R3']), ('L_SUM', ['U5.3'], ['R2', 'R3']),
    ('U3 outR', ['U3.11'], ['R6']), ('U4 outL', ['U4.14'], ['R7']), ('R_SUM', ['U5.5'], ['R6', 'R7']),
    ('L fb', ['U5.2'], ['R4', 'R5']), ('L_OUT_SE', ['U5.1', 'U6.4'], ['R5']),
    ('R fb', ['U5.6'], ['R8', 'R9']), ('R_OUT_SE', ['U5.7', 'U7.4'], ['R9']),
    ('U6 out+', ['U6.8'], ['C17', 'R10']), ('U6 sns+', ['U6.7'], ['C17']), ('U6 out-', ['U6.1'], ['C18', 'R11']), ('U6 sns-', ['U6.2'], ['C18']),
    ('J3 tip', ['J3.T'], ['R10', 'C9']), ('J3 ring', ['J3.R'], ['R11', 'C10']),
    ('U7 out+', ['U7.8'], ['C19', 'R12']), ('U7 sns+', ['U7.7'], ['C19']), ('U7 out-', ['U7.1'], ['C20', 'R13']), ('U7 sns-', ['U7.2'], ['C20']),
    ('J4 tip', ['J4.T'], ['R12', 'C15']), ('J4 ring', ['J4.R'], ['R13', 'C16']),
    ('DIP0', ['U9.3', 'SW1.8'], []), ('DIP1', ['U9.4', 'SW1.7'], []), ('DIP2', ['U9.5', 'SW1.6'], []), ('DIP3', ['U9.6', 'SW1.5'], []),
    ('LED drive', ['U9.10'], ['R16']), ('LED anode', ['LED1.2'], ['R16']),
    ('PS1 +out', ['PS1.6'], ['L1']), ('PS1 -out', ['PS1.4'], ['L2']),
]
NC = ['U1.8', 'U2.8', 'U4.7', 'J3.RN', 'J3.TN', 'J4.RN', 'J4.TN']

t = ET.parse(sys.argv[1]).getroot()
nets = {}
for n in t.iter('net'):
    nodes = {f"{nd.get('ref')}.{nd.get('pin')}" for nd in n.findall('node') if not nd.get('ref').startswith('#')}
    if nodes and not n.get('name').startswith('unconnected-'): nets[n.get('name')] = nodes
pin2net = {p: name for name, ps in nets.items() for p in ps}
allpins = set(pin2net)
ok = True
def fail(msg):
    global ok; ok = False; print('FAIL', msg)
passive_count = defaultdict(int)
covered = set()
for name, exact, passives in EXPECTED:
    anchor = exact[0]
    if anchor not in pin2net: fail(f'{name}: {anchor} not in any net'); continue
    kn = pin2net[anchor]; members = nets[kn]
    def is_passive(p): r = p.split('.')[0]; return (r[0] in 'RCL' and not r.startswith('LED')) or r.startswith('FB')
    got_exact = {p for p in members if not is_passive(p)}
    got_pass = sorted(p.split('.')[0] for p in members if is_passive(p))
    if got_exact != set(exact): fail(f'{name} ({kn}): exact pins {sorted(got_exact)} != expected {sorted(exact)}')
    if got_pass != sorted(passives): fail(f'{name} ({kn}): passives {got_pass} != expected {sorted(passives)}')
    for p in got_pass: passive_count[p] += 1
    covered |= members
for p, c in passive_count.items():
    if c != 2: fail(f'passive {p} appears in {c} nets, expected 2')
for p in NC:
    if p in pin2net: fail(f'{p} should be unconnected but is on {pin2net[p]}')
extra = allpins - covered
if extra: fail(f'pins on nets not covered by the spec: {sorted(extra)}')
print('nets in netlist:', len(nets), '| spec nets:', len(EXPECTED), '| pins checked:', len(covered))
print('NETLIST OK' if ok else 'NETLIST MISMATCH')
sys.exit(0 if ok else 1)
