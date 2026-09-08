#!/usr/bin/env python3
"""Build ghost-fader.kicad_pcb from the schematic netlist: footprints, nets, placement, outline, ground pours.

Run with KiCad's bundled Python (it needs the pcbnew module):
  kicad-cli sch export netlist --format kicadsexpr -o /tmp/gf.net ghost-fader.kicad_sch
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 tools/build_pcb.py /tmp/gf.net

Board: 108 x 80 mm, 2 layers, for a Hammond 1590BB (inside ~112 x 86 mm, lid-screw bosses on 103.5 x 78 mm
centres, cleared by 7.5 x 6.5 mm corner notches). Jacks on the rear edge (y = 0), Teensy USB on the front edge
(y = 80). Coordinates below are mm, origin top-left, y down. Signal flow: jacks -> receivers (y ~33) ->
coupling caps (y ~47) -> PGA2310s (y ~53-61) -> summers/drivers -> output jacks; DC-DC at the front centre,
input receivers top-left, so the converter is as far from the receivers as the board allows.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse
import pcbnew
from pcbnew import VECTOR2I, EDA_ANGLE, DEGREES_T

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
NETFILE = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PROJ, 'ghost-fader.kicad_pcb')
FPDIR = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'

W, H = 108.0, 80.0          # board outline
NX, NY = 7.5, 6.5           # corner notch (clears the 1590BB lid-screw bosses)

def mm(v): return pcbnew.FromMM(v)
def pt(x, y): return VECTOR2I(mm(x), mm(y))

# ---------------------------------------------------------------- placement: ref -> (x, y, rotation)
# Anchor is the footprint origin (pad 1 / T pad / body centre, as each library footprint defines it).
def jack(c): return (c - 5.79, 15.5, 90)      # nose points to the rear edge, T pad column at x = c - 5.79
PLACE = {
    # rear jacks, in L, in R, out L, out R
    'J1': jack(19), 'J2': jack(39), 'J3': jack(68), 'J4': jack(90),
    # RF caps at the jack pins
    'C1': (12.5, 26.5, 0), 'C2': (20.8, 26.5, 0), 'C7': (32.5, 26.5, 0), 'C8': (40.8, 26.5, 0),
    'C9': (61.5, 26.5, 0), 'C10': (69.8, 26.5, 0), 'C15': (82.5, 26.5, 0), 'C16': (90.8, 26.5, 0),
    # input receivers (inputs face the jacks) and their 100n
    'U1': (16, 33.5, 270), 'U2': (36, 33.5, 270),
    'C22': (10, 38.5, 90), 'C21': (22, 38.5, 90), 'C24': (30, 38.5, 90), 'C23': (42, 38.5, 90),
    # +/-15 V bulk, input end, in the gap between J2 and J3
    'C40': (50.5, 28, 0), 'C41': (50.5, 35.5, 0),
    # coupling caps into the PGAs and the PGA +/-15 V 100n
    'C3': (31, 47.5, 0), 'C25': (39.5, 51, 90), 'C26': (43.5, 51, 90), 'C4': (48, 47.5, 0),
    'C5': (55, 47.5, 0), 'C28': (63.5, 51, 90), 'C29': (67.5, 51, 90), 'C6': (72, 47.5, 0),
    # PGA2310s, analog pins on top (y 53.4), digital pins below (y 61)
    'U3': (34, 61, 90), 'U4': (58, 61, 90),
    # 5 V logic decoupling below the PGAs
    'C27': (32.4, 65, 0), 'C30': (69.5, 65, 0), 'C14': (60.5, 65.5, 0),
    # Teensy, USB end flush with the front edge; DIP switch to its right
    'U9': (19.5, 61.5, 180), 'SW1': (31.5, 78.5, 90),
    # left column: plug-sense pull-ups, mute pull-down
    'R1': (3.5, 55, 90), 'R14': (7, 55, 90), 'R15': (5.25, 68, 90),
    # power: USB 5 V -> FB1 -> C11 -> PS1; L1/L2 + C12/C13 on the +/-15 V outputs
    'FB1': (39.8, 65.5, 0), 'C11': (53.5, 65.5, 0), 'PS1': (44.5, 74.7, 0),
    'L1': (67.3, 78.5, 90), 'L2': (71.3, 78.5, 90), 'C12': (76.3, 74, 0), 'C13': (83.3, 74, 0),
    # summing resistors from the PGA outputs, op-amp, feedback/ground resistors, op-amp 100n
    'R2': (91, 65.8, 90), 'R3': (94.5, 65.8, 90), 'R6': (98, 65.8, 90), 'R7': (101.5, 65.8, 90),
    'U5': (80, 55, 0), 'R4': (89.1, 68.5, 0), 'R5': (89.1, 71.8, 0), 'R8': (89.1, 75.1, 0), 'R9': (89.1, 78.4, 0),
    'C31': (84, 48, 0), 'C32': (84, 51.5, 0),
    # output drivers under J3/J4 with sense caps either side, build-out resistors and 100n below
    'C17': (58, 33.5, 0), 'U6': (68, 33.5, 270), 'C18': (74, 33.5, 0),
    'C19': (80, 33.5, 0), 'U7': (90, 33.5, 270), 'C20': (96, 33.5, 0),
    'R10': (57, 39.5, 0), 'R11': (57, 43, 0), 'C33': (70, 39.5, 0), 'C34': (70, 43, 0),
    'R12': (79, 39.5, 0), 'R13': (79, 43, 0), 'C35': (92, 39.5, 0), 'C36': (92, 43, 0),
    # +/-15 V bulk, output end
    'C42': (103, 33.5, 0), 'C43': (103, 40.5, 0),
    # MIDI activity LED and its resistor, front-right corner
    'LED1': (102, 71, 0), 'R16': (105.5, 66, 90),
}

REF_ABOVE = {'C40', 'C42', 'C12', 'C13'}   # 6.3 mm radial caps whose label goes above the can (the rest go below)

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
ds.m_CopperEdgeClearance = mm(0.25)
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
    fp.Reference().SetTextSize(VECTOR2I(mm(0.9), mm(0.9))); fp.Reference().SetTextThickness(mm(0.15))
    # dense rows: put the reference inside the part outline instead of on the neighbour
    if name.startswith('R_Axial') or name.startswith('L_Axial'): fp.Reference().SetFPRelativePosition(pt(5.08, 0))
    elif name.startswith('CP_Radial_D6.3'): fp.Reference().SetFPRelativePosition(pt(1.25, -3.9 if ref in REF_ABOVE else 3.9))
    elif name.startswith('CP_Radial_D5'): fp.Reference().SetFPRelativePosition(pt(1.25, 3.25))
    elif name.startswith('C_Disc'): fp.Reference().SetFPRelativePosition(pt(2.5, 0))
    elif name.startswith('DIP-8'): fp.Reference().SetFPRelativePosition(pt(3.81, 3.81))
    elif name.startswith('SW_DIP'): fp.Reference().SetFPRelativePosition(pt(3.81, -1.4))
    x, y, rot = PLACE[ref]
    fp.SetPosition(pt(x, y))
    fp.SetOrientation(EDA_ANGLE(rot, DEGREES_T))
    for pad in fp.Pads():
        n = pad_net.get((ref, pad.GetNumber()))
        if n: pad.SetNet(netinfo[n])
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            pad.SetLocalClearance(mm(0.3))   # keep the ground pour off the jack locating holes
    board.Add(fp)

# ---------------------------------------------------------------- outline with corner notches
outline = [(NX, 0), (W - NX, 0), (W - NX, NY), (W, NY), (W, H - NY), (W - NX, H - NY), (W - NX, H), (NX, H),
           (NX, H - NY), (0, H - NY), (0, NY), (NX, NY)]
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
text('GHOST FADER rev B', 4, 25, 1.5, rot=90)
text('USB', 19.5, 42.3, 1.2)
text('IN L', 19, 5, 1.2, pcbnew.B_SilkS); text('IN R', 39, 5, 1.2, pcbnew.B_SilkS)
text('OUT L', 68, 5, 1.2, pcbnew.B_SilkS); text('OUT R', 90, 5, 1.2, pcbnew.B_SilkS)

board.BuildListOfNets()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(OUT, board)
print('wrote', OUT, len(comps), 'footprints,', len(nets), 'nets')
