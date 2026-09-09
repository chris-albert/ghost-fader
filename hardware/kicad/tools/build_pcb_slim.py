#!/usr/bin/env python3
"""Build ghost-fader-slim.kicad_pcb: the same schematic on the narrowest board two side-by-side jacks allow.

Run with KiCad's bundled Python (it needs the pcbnew module):
  kicad-cli sch export netlist --format kicadsexpr -o /tmp/gf.net ghost-fader.kicad_sch
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 tools/build_pcb_slim.py /tmp/gf.net

Board: 207 x 38 mm, 2 layers, for a 3D-printed box. Width is set by two NRJ6HF jacks side by side (16.8 mm each,
18 mm pitch) and, across the board, the Teensy (36.6 mm long, USB out of the rear edge). Inputs on the right end,
outputs on the left, signal flows right to left; Teensy USB out of the rear long edge (y = 0), centred on the
length. No mounting holes: the board hangs on the four jack nuts, so give the printed box a ledge under the
board edges. Parts stay 1 mm off the edges; copper 0.3 mm.

Coordinates below are mm, origin top-left, y down. Everything is arranged in columns along the length:
output jacks -> RF caps -> drivers + sense caps -> build-outs and 100n -> summer -> coupling caps ->
PGA2310s (digital rows facing each other) -> Teensy -> DIP switch, pull-ups, +/-15 V bulk -> DC-DC and rail
filters -> receivers -> bulk caps -> RF caps -> input jacks.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse
import pcbnew
from pcbnew import VECTOR2I, EDA_ANGLE, DEGREES_T

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
NETFILE = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PROJ, 'ghost-fader-slim.kicad_pcb')
FPDIR = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'

W, H = 207.0, 38.0          # board outline

def mm(v): return pcbnew.FromMM(v)
def pt(x, y): return VECTOR2I(mm(x), mm(y))

# ---------------------------------------------------------------- placement: ref -> (x, y, rotation)
# Anchor is the footprint origin (pad 1 / T pad / body centre, as each library footprint defines it).
# Jacks: T pad 15.5 mm in from the end, nose out through the end wall; the body face sits 1.45 mm past the board edge.
def jack_in(c): return (W - 15.5, c - 5.79, 0)     # nose points +x (right end)
def jack_out(c): return (15.5, c + 5.79, 180)      # nose points -x (left end)
JY_L, JY_R = 10.0, 28.0                            # jack centres across the board, 18 mm apart
PLACE = {
    # right end: inputs. Left end: outputs.
    'J1': jack_in(JY_L), 'J2': jack_in(JY_R), 'J3': jack_out(JY_L), 'J4': jack_out(JY_R),
    # RF caps at the jack pins, one vertical column per end
    'C9': (26.5, 2.5, 270), 'C10': (26.5, 11, 270), 'C15': (26.5, 19.5, 270), 'C16': (26.5, 28, 270),
    'C1': (181, 2.5, 270), 'C2': (181, 11, 270), 'C7': (181, 19.5, 270), 'C8': (181, 28, 270),
    # output drivers (pins 1-4 facing the jacks) with their sense caps stacked in one column
    'C17': (31.5, 4.1, 0), 'U6': (33, 10, 0), 'C18': (31.5, 16, 0),
    'C19': (31.5, 21.9, 0), 'U7': (33, 27.9, 0), 'C20': (31.5, 33.9, 0),
    # build-outs, driver and op-amp 100n, summing resistors R2/R3/R6
    'R10': (38.5, 2.5, 0), 'R11': (38.5, 6, 0), 'R12': (38.5, 9.5, 0), 'R13': (38.5, 13, 0),
    'C33': (38.5, 16.5, 0), 'C34': (46, 16.5, 0), 'C35': (38.5, 20, 0), 'C36': (46, 20, 0),
    'C31': (38.5, 23.5, 0), 'C32': (46, 23.5, 0),
    'R2': (38.5, 27.5, 0), 'R3': (38.5, 31, 0), 'R6': (38.5, 34.5, 0),
    # summer with its feedback resistors above, R9 and R7 below
    'R4': (52, 2.5, 0), 'R5': (52, 6, 0), 'R8': (52, 9.5, 0), 'U5': (54, 14, 0), 'R9': (52, 26.5, 0), 'R7': (52, 30, 0),
    # coupling caps into the PGAs and the PGA +/-15 V 100n
    'C4': (65, 4.5, 0), 'C3': (72, 4.5, 0), 'C5': (65, 11, 0), 'C6': (72, 11, 0),
    'C25': (65, 16.5, 0), 'C26': (72.5, 16.5, 0), 'C28': (65, 20, 0), 'C29': (72.5, 20, 0),
    # PGA2310s stacked across the board, digital rows (pins 1-8) facing each other at y 12.5 and 24.5, 5 V 100n between
    'U3': (80.5, 12.5, 90), 'U4': (99.5, 24.5, 270), 'C27': (81.5, 18.5, 0), 'C30': (90.5, 18.5, 0),
    # Teensy across the board, USB end at the rear edge
    'U9': (111.5, 19, 0),
    # DIP switch, pull-ups / pull-down / LED resistor, +/-15 V bulk
    'SW1': (124.5, 3.5, 0),
    'R15': (124, 16, 270), 'R16': (127.5, 16, 270), 'R1': (131, 16, 270), 'R14': (134.5, 16, 270),
    'C40': (123.5, 32.5, 0), 'C41': (131, 32.5, 0),
    # power: USB 5 V -> FB1 -> C11 -> PS1; L1/L2 on the converter outputs; 100u bulk; LED at the rear edge
    'FB1': (139, 3, 0), 'LED1': (154, 3.2, 0), 'PS1': (139, 11.5, 0),
    'C11': (139, 21.5, 0), 'C12': (146.5, 21.5, 0), 'L1': (153.5, 19, 270), 'L2': (157.5, 19, 270),
    'C14': (139, 29, 0), 'C13': (146.5, 29, 0),
    # input receivers (inputs facing the jacks) with 100n above and below, +/-15 V bulk beside them
    'C22': (164, 3.5, 0), 'U1': (166, 10, 180), 'C21': (164, 16, 0),
    'C24': (164, 21, 0), 'U2': (166, 28, 180), 'C23': (164, 34.5, 0),
    'C42': (172.5, 4.5, 0), 'C43': (172.5, 33.5, 0),
}

# Reference labels, world coordinates (x, y, angle). Parts not listed use a rule for their footprint type.
# On a board this tight most labels sit on the part body (resistors, discs, ICs): readable on the bare board.
LABELS = {
    'U9': (111.5, 19, 90), 'SW1': (129.5, 7.3, 0), 'PS1': (146, 9, 0), 'U5': (57.8, 17.8, 90),
    'U3': (89.4, 8.7, 0), 'U4': (90.6, 28.3, 0), 'LED1': (150.9, 3.2, 90),
    'U1': (166, 10, 0), 'U2': (166, 28, 0), 'U6': (33, 10, 0), 'U7': (33, 27.9, 0),
    'C17': (29.0, 4.1, 90), 'C18': (29.0, 16, 90), 'C19': (29.0, 21.9, 90), 'C20': (29.0, 33.9, 90),
}
REF_ABOVE = {'C43', 'C11', 'C12', 'C40', 'C41'}   # 6.3 mm radial caps whose label goes above the can

def label_for(ref, name, x, y, rot):
    if ref in LABELS: return LABELS[ref]
    if name.startswith('CP_Radial_D6.3'): return (x + 1.25, y + (-3.9 if ref in REF_ABOVE else 3.9), 0)
    if name.startswith('CP_Radial_D5'): return (x + 1.25, y + 3.25, 0)
    if name.startswith('R_Axial') or name.startswith('L_Axial'):
        return (x, y + 5.08, 90) if rot == 270 else (x + 5.08, y, 0)      # on the body
    if name.startswith('C_Disc'):
        if rot == 270 and x < 28: return (x - 2.2, y + 2.5, 90)           # output RF caps: label toward the jack
        return (x, y + 2.5, 90) if rot == 270 else (x + 2.5, y, 0)        # on the body
    return None   # library default

# ---------------------------------------------------------------- netlist
net = parse(open(NETFILE).read())[0]
def kids(n, tag): return [e for e in n if isinstance(e, list) and e[0] == tag]
def one(n, tag): return kids(n, tag)[0]
def s(v): return str(v).strip('"')
comps = {}
for c in kids(one(net, 'components'), 'comp'):
    comps[s(one(c, 'ref')[1])] = (s(one(c, 'footprint')[1]), s(one(c, 'value')[1]))
nets = {}
for n in kids(one(net, 'nets'), 'net'):
    nets[s(one(n, 'name')[1])] = [(s(one(nd, 'ref')[1]), s(one(nd, 'pin')[1])) for nd in kids(n, 'node')]
missing = set(comps) - set(PLACE)
assert not missing, f'no placement for {sorted(missing)}'

# ---------------------------------------------------------------- board + rules
board = pcbnew.NewBoard(OUT) if hasattr(pcbnew, 'NewBoard') else pcbnew.BOARD()
ds = board.GetDesignSettings()
ds.m_MinClearance = mm(0.2)
ds.m_TrackMinWidth = mm(0.2)
ds.m_ViasMinSize = mm(0.6)
ds.m_MinThroughDrill = mm(0.3)
ds.m_CopperEdgeClearance = mm(0.3)
ds.m_HoleClearance = mm(0.25)
ds.m_HoleToHoleMin = mm(0.25)
ds.m_MinResolvedSpokes = 1
ds.m_SolderMaskExpansion = mm(0.05)

nc = ds.m_NetSettings
default = nc.GetDefaultNetclass()
default.SetClearance(mm(0.25)); default.SetTrackWidth(mm(0.3)); default.SetViaDiameter(mm(0.8)); default.SetViaDrill(mm(0.4))
power = pcbnew.NETCLASS('Power')
power.SetClearance(mm(0.25)); power.SetTrackWidth(mm(0.6)); power.SetViaDiameter(mm(0.9)); power.SetViaDrill(mm(0.5))
nc.SetNetclass('Power', power)
POWER_NETS = ['+5V', 'USB_5V', '+15V', '-15V', 'GND', 'Net-(PS1-+Vout)', 'Net-(PS1--Vout)']
for pn in POWER_NETS:
    nc.SetNetclassPatternAssignment(pn, 'Power')

netinfo = {}
for name in nets:
    ni = pcbnew.NETINFO_ITEM(board, name)
    board.Add(ni)
    netinfo[name] = ni
pad_net = {}
for name, nodes in nets.items():
    for ref, pin in nodes:
        pad_net[(ref, pin)] = name

# ---------------------------------------------------------------- footprints
for ref in sorted(comps, key=lambda r: (r.rstrip('0123456789'), int(r.lstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ') or 0))):
    fpname, value = comps[ref]
    lib, name = fpname.split(':')
    path = os.path.join(PROJ, 'GhostFader.pretty') if lib == 'GhostFader' else f'{FPDIR}/{lib}.pretty'
    fp = pcbnew.FootprintLoad(path, name)
    assert fp, f'footprint {fpname} not found'
    fp.SetReference(ref); fp.SetValue(value)
    fp.SetFPIDAsString(fpname)
    fp.Reference().SetVisible(True)
    x, y, rot = PLACE[ref]
    fp.SetPosition(pt(x, y))
    fp.SetOrientation(EDA_ANGLE(rot, DEGREES_T))
    fp.Reference().SetTextSize(VECTOR2I(mm(0.8), mm(0.8))); fp.Reference().SetTextThickness(mm(0.15))
    lbl = label_for(ref, name, x, y, rot)
    if lbl:
        fp.Reference().SetPosition(pt(lbl[0], lbl[1]))
        fp.Reference().SetTextAngle(EDA_ANGLE(lbl[2], DEGREES_T))   # absolute angle
    for pad in fp.Pads():
        n = pad_net.get((ref, pad.GetNumber()))
        if n: pad.SetNet(netinfo[n])
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            pad.SetLocalClearance(mm(0.3))   # keep the ground pour off the jack locating holes
    board.Add(fp)

# ---------------------------------------------------------------- outline: plain rectangle
outline = [(0, 0), (W, 0), (W, H), (0, H)]
for i in range(len(outline)):
    a, b = outline[i], outline[(i + 1) % len(outline)]
    seg = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(pt(*a)); seg.SetEnd(pt(*b))
    seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(mm(0.1))
    board.Add(seg)

# ---------------------------------------------------------------- ground pours on both layers
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer); z.SetNet(netinfo['GND'])
    z.SetLocalClearance(mm(0.3)); z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.4)); z.SetThermalReliefSpokeWidth(mm(0.5))
    z.SetZoneName('GND_' + ('F' if layer == pcbnew.F_Cu else 'B'))
    z.SetAssignedPriority(0)
    poly = z.Outline()
    poly.NewOutline()
    for x, y in outline: poly.Append(mm(x), mm(y))
    board.Add(z)

# ---------------------------------------------------------------- silkscreen labels
def text(txt, x, y, size=1.5, layer=pcbnew.F_SilkS, rot=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt); t.SetPosition(pt(x, y)); t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(0.2))
    t.SetTextAngle(EDA_ANGLE(rot, DEGREES_T))
    if layer == pcbnew.B_SilkS: t.SetMirrored(True)
    board.Add(t)
text('GHOST FADER rev B  slim', 111.5, 22, 1.5, pcbnew.B_SilkS, 90)
text('USB', 111.5, 2.5, 1.0, pcbnew.B_SilkS)
text('IN L', W - 12.3, JY_L + 2.5, 1.2, pcbnew.B_SilkS); text('IN R', W - 12.3, JY_R + 2.5, 1.2, pcbnew.B_SilkS)
text('OUT L', 12.3, JY_L - 2.5, 1.2, pcbnew.B_SilkS); text('OUT R', 12.3, JY_R - 2.5, 1.2, pcbnew.B_SilkS)

board.BuildListOfNets()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(OUT, board)
print('wrote', OUT, len(comps), 'footprints,', len(nets), 'nets')
