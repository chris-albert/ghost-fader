#!/usr/bin/env python3
"""Build ghost-fader-narrow.kicad_pcb: the same schematic on a long, narrow in-line board.

Run with KiCad's bundled Python (it needs the pcbnew module):
  kicad-cli sch export netlist --format kicadsexpr -o /tmp/gf.net ghost-fader.kicad_sch
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 tools/build_pcb_narrow.py /tmp/gf.net

Board: 156 x 74.5 mm, 2 layers, for a Hammond 1455K1601 extruded box (78 x 43 x 160 mm, made for a 75 mm wide
board that slides into the wall slots; the end plates carry the jacks). Inputs on the right end plate, outputs on
the left, so signal flows right to left like a pedal; Teensy USB out of the rear long edge (y = 0), centred.
No mounting holes: the board sits in the extrusion slots and hangs on the four jack nuts. Copper and parts stay
1.5 mm off the long edges because those edges sit inside the aluminium slots.

Coordinates below are mm, origin top-left, y down. Signal flow (right to left): input jacks -> RF caps ->
THAT 1246 receivers -> coupling caps -> PGA2310s (digital rows facing the Teensy) -> summing resistors along the
front edge -> OPA2134 -> THAT 1646 drivers -> output jacks. DC-DC and rail filters sit behind the PGAs, right of
the Teensy, the far end of the board from nothing in particular: on a board this shape the receivers are 30 mm
away, which is what the +/-15 V bulk and 100n caps are for.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse
import pcbnew
from pcbnew import VECTOR2I, EDA_ANGLE, DEGREES_T

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
NETFILE = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PROJ, 'ghost-fader-narrow.kicad_pcb')
FPDIR = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'

W, H = 156.0, 74.5          # board outline
EDGE = 1.5                  # copper / parts keep-out along the long edges (they sit in the extrusion slots)
EDGE_END = 0.5              # track keep-out at the short ends (the end plates are separate parts)

def mm(v): return pcbnew.FromMM(v)
def pt(x, y): return VECTOR2I(mm(x), mm(y))

# ---------------------------------------------------------------- placement: ref -> (x, y, rotation)
# Anchor is the footprint origin (pad 1 / T pad / body centre, as each library footprint defines it).
# Jacks: T pad 15.5 mm in from the end, nose through the end plate; the body face sits 1.45 mm past the board edge.
def jack_in(c): return (W - 15.5, c - 5.79, 0)     # nose points +x (right end plate)
def jack_out(c): return (15.5, c + 5.79, 180)      # nose points -x (left end plate)
JY_L, JY_R = 25.25, 49.25                          # jack centres across the board, 24 mm apart
PLACE = {
    # right end: inputs. Left end: outputs.
    'J1': jack_in(JY_L), 'J2': jack_in(JY_R), 'J3': jack_out(JY_L), 'J4': jack_out(JY_R),
    # RF caps at the jack pins, vertical, one column per end
    'C1': (129.5, 18.75, 270), 'C2': (129.5, 27, 270), 'C7': (129.5, 42.75, 270), 'C8': (129.5, 51, 270),
    'C9': (26.5, 18.75, 270), 'C10': (26.5, 27, 270), 'C15': (26.5, 42.75, 270), 'C16': (26.5, 51, 270),
    # input receivers, inputs (pins 1-4) facing the jacks, 100n above and below each
    'U1': (118, JY_L, 180), 'U2': (118, JY_R, 180),
    'C22': (116, 18, 0), 'C21': (116, 32.5, 0), 'C24': (116, 42, 0), 'C23': (116, 56.5, 0),
    # +/-15 V bulk, input end, rear strip beside J1
    'C40': (140, 8, 0), 'C41': (149, 8, 0),
    # Teensy, USB end 1.5 mm inside the rear edge (the connector overhangs its board by about that much)
    'U9': (78, 19.3, 0),
    # DIP switch left of the Teensy, its pins 5-8 next to Teensy pins 6-9
    'SW1': (58, 12, 0),
    # LED at the rear edge left of the USB, bent back to face the rear wall
    'LED1': (63, 4.5, 0),
    # pull-ups / pull-down / LED resistor, vertical, between SW1 and the PGAs
    'R15': (54.5, 24.5, 270), 'R16': (58, 24.5, 270), 'R1': (61.5, 24.5, 270), 'R14': (65, 24.5, 270),
    # PGA2310s in front of the Teensy, digital rows (pins 1-8) at y 41 facing it, analog rows at y 48.6
    'U3': (77, 41, 270), 'U4': (100, 41, 270),
    # coupling caps and +/-15 V 100n along the analog rows
    'C4': (57.5, 54.5, 0), 'C26': (63.5, 51.5, 270), 'C25': (68, 51.5, 270), 'C3': (73.5, 54.5, 0),
    'C6': (80.5, 54.5, 0), 'C29': (86.5, 51.5, 270), 'C28': (91, 51.5, 270), 'C5': (96.5, 54.5, 0),
    # 5 V logic decoupling by the PGA digital rows
    'C27': (56, 41, 270), 'C30': (103, 36.5, 0),
    # power, right of the Teensy: USB 5 V -> FB1 -> C11 -> PS1; L1/L2 down from the converter outputs; 100u bulk
    'FB1': (90, 4.5, 0), 'C11': (104, 5.2, 0), 'C14': (113, 5.2, 0), 'PS1': (91, 14, 0),
    'L1': (103.7, 21.5, 270), 'L2': (108.78, 21.5, 270), 'C12': (94, 24, 0), 'C13': (94, 32, 0),
    # summer: op-amp front-left, feedback and summing resistors vertical along the front edge
    'U5': (45.5, 62.5, 0), 'C31': (56, 60.5, 270), 'C32': (35, 70, 0),
    'R4': (59.5, 59.5, 270), 'R5': (63, 59.5, 270), 'R8': (66.5, 59.5, 270), 'R9': (70, 59.5, 270),
    'R6': (73.5, 59.5, 270), 'R2': (77, 59.5, 270), 'R3': (80.5, 59.5, 270), 'R7': (84, 59.5, 270),
    # output drivers behind the output jacks, sense caps above and below, build-outs and 100n to the right
    'U6': (38, JY_L, 0), 'C17': (36, 15.5, 0), 'C18': (36, 32, 0),
    'R10': (44, 8.5, 0), 'R11': (42.5, 37.5, 0), 'C33': (44, 22, 270), 'C34': (48.5, 22, 270),
    'U7': (38, JY_R, 0), 'C19': (36, 41, 0), 'C20': (36, 57.5, 0),
    'R12': (43, 44.5, 0), 'R13': (30, 65, 0), 'C35': (44, 47.5, 270), 'C36': (48.5, 47.5, 270),
    # +/-15 V bulk, output end, rear strip beside J3
    'C42': (7, 8, 0), 'C43': (16, 8, 0),
}

# Reference labels, world coordinates (x, y, angle). Parts not listed use a rule for their footprint type.
LABELS = {
    'U9': (78, 38.7, 0), 'SW1': (62.5, 7.5, 0), 'PS1': (100.5, 20.5, 0), 'U5': (49.3, 58.9, 0),
    'U3': (68.1, 44.8, 0), 'U4': (91.1, 44.8, 0), 'LED1': (59.3, 4.5, 90),
    'L1': (100.7, 27, 90), 'L2': (111.8, 27, 90), 'C11': (109.6, 5.2, 90), 'C14': (118.6, 5.2, 90),
    'U1': (118, 20.9, 0), 'U2': (118, 45.5, 0), 'U6': (38, 20.9, 0), 'U7': (38, 45.5, 0),
    'R13': (35, 62, 0), 'C32': (38.5, 67, 0), 'C31': (53, 72.4, 0), 'C27': (56, 38.8, 0),
}
REF_ABOVE = {'C40', 'C41', 'C42', 'C43'}   # 6.3 mm radial caps whose label goes above the can

def label_for(ref, name, x, y, rot):
    if ref in LABELS: return LABELS[ref]
    vertical = rot in (90, 270)
    if name.startswith('CP_Radial_D6.3'): return (x + 1.25, y + (-3.9 if ref in REF_ABOVE else 3.9), 0)
    if name.startswith('CP_Radial_D5'): return (x + 1.25, y + 3.25, 0)
    if (name.startswith('R_Axial') or name.startswith('L_Axial')) and rot == 270: return (x, y + 12.4, 90)
    if (name.startswith('R_Axial') or name.startswith('L_Axial')) and vertical: return (x, y - 12.4, 90)
    if name.startswith('C_Disc') and rot == 270: return (x + 2.2, y + 2.5, 90)   # label stands beside the body
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

# ---------------------------------------------------------------- track/via keep-out strips along every edge
# The long edges sit in the aluminium slots; the router does not know about copper-to-edge clearance, so fence it.
def rule_area(name, poly):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
    z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    z.SetLayerSet(pcbnew.LSET.AllCuMask(2))
    z.SetZoneName(name)
    o = z.Outline(); o.NewOutline()
    for x, y in poly: o.Append(mm(x), mm(y))
    board.Add(z)
rule_area('KEEPOUT_REAR', [(0, 0), (W, 0), (W, EDGE), (0, EDGE)])
rule_area('KEEPOUT_FRONT', [(0, H - EDGE), (W, H - EDGE), (W, H), (0, H)])
rule_area('KEEPOUT_LEFT', [(0, 0), (EDGE_END, 0), (EDGE_END, H), (0, H)])
rule_area('KEEPOUT_RIGHT', [(W - EDGE_END, 0), (W, 0), (W, H), (W - EDGE_END, H)])

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
    for x, y in [(0, EDGE), (W, EDGE), (W, H - EDGE), (0, H - EDGE)]: poly.Append(mm(x), mm(y))   # off the slots
    board.Add(z)

# ---------------------------------------------------------------- silkscreen labels
def text(txt, x, y, size=1.5, layer=pcbnew.F_SilkS, rot=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt); t.SetPosition(pt(x, y)); t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(0.2))
    t.SetTextAngle(EDA_ANGLE(rot, DEGREES_T))
    if layer == pcbnew.B_SilkS: t.SetMirrored(True)
    board.Add(t)
text('GHOST FADER rev B  narrow / 1455K', 112, 66, 1.8)
text('USB', 78, 5, 1.2, pcbnew.B_SilkS)
text('IN L', 146, 13.5, 1.2); text('IN R', 146, 61, 1.2)
text('OUT L', 10, 13.5, 1.2); text('OUT R', 10, 61, 1.2)
text('IN L', 146, 13.5, 1.2, pcbnew.B_SilkS); text('IN R', 146, 61, 1.2, pcbnew.B_SilkS)
text('OUT L', 10, 13.5, 1.2, pcbnew.B_SilkS); text('OUT R', 10, 61, 1.2, pcbnew.B_SilkS)

board.BuildListOfNets()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(OUT, board)
print('wrote', OUT, len(comps), 'footprints,', len(nets), 'nets')
