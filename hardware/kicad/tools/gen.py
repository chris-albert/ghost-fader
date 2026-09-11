#!/usr/bin/env python3
"""Generate the Ghost Fader KiCad 9 schematic (root + 5 sheets), symbol lib and footprints."""
import sys, os, math, uuid, json
sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse, dump, libsym, pins as sympins, Q

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
KLIB = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/'
PROJECT = 'ghost-fader'
DATE = '2026-09-09'
REV = 'D'
G = 2.54

def U(): return str(uuid.uuid4())
def g(n): return round(n * G, 4)

# ---------------------------------------------------------------- symbols
def pin(num, name, x, y, rot, etype='passive', length=2.54):
    return ['pin', etype, 'line', ['at', f'{x:g}', f'{y:g}', f'{rot:g}'], ['length', f'{length:g}'],
            ['name', Q(name), ['effects', ['font', ['size', '1.27', '1.27']]]],
            ['number', Q(num), ['effects', ['font', ['size', '1.27', '1.27']]]]]

def prop(name, val, x=0, y=0, hide=False, justify=None):
    eff = ['effects', ['font', ['size', '1.27', '1.27']]]
    if justify: eff.append(['justify', justify])
    if hide: eff.append(['hide', 'yes'])
    return ['property', Q(name), Q(val), ['at', f'{x:g}', f'{y:g}', '0'], eff]

BOX = {}   # GhostFader box symbols: (hw, hh)
def boxsym(name, refpfx, w, h, pinlist, desc, units=1):
    """pinlist: (num, name, side, pos, etype). side L/R/T/B, pos = offset along the side (mm, lib coords, y up)."""
    hw, hh = w / 2, h / 2
    s = ['symbol', Q(name), ['pin_names', ['offset', '1.016']], ['exclude_from_sim', 'no'], ['in_bom', 'yes'], ['on_board', 'yes'],
         prop('Reference', refpfx, -hw, hh + 1.27, justify='left'), prop('Value', name, hw, -hh - 1.27, justify='right'),
         prop('Footprint', '', hide=True), prop('Datasheet', '', hide=True), prop('Description', desc, hide=True)]
    body = ['symbol', Q(f'{name}_0_1'), ['rectangle', ['start', f'{-hw:g}', f'{hh:g}'], ['end', f'{hw:g}', f'{-hh:g}'],
            ['stroke', ['width', '0.254'], ['type', 'default']], ['fill', ['type', 'background']]]]
    s.append(body)
    u = ['symbol', Q(f'{name}_1_1')]
    for num, pname, side, pos, et in pinlist:
        if side == 'L': u.append(pin(num, pname, -hw - 2.54, pos, 0, et))
        elif side == 'R': u.append(pin(num, pname, hw + 2.54, pos, 180, et))
        elif side == 'T': u.append(pin(num, pname, pos, hh + 2.54, 270, et))
        elif side == 'B': u.append(pin(num, pname, pos, -hh - 2.54, 90, et))
    s.append(u)
    BOX[f'GhostFader:{name}'] = (hw, hh)
    return s

CUSTOM = {}
CUSTOM['THAT1246'] = boxsym('THAT1246', 'U', 15.24, 15.24, [
    ('2', 'In-', 'L', 2.54, 'input'), ('3', 'In+', 'L', -2.54, 'input'),
    ('6', 'Vout', 'R', 2.54, 'output'), ('5', 'Sense', 'R', -2.54, 'input'), ('8', 'NC', 'R', -5.08, 'no_connect'),
    ('1', 'Ref', 'B', -2.54, 'input'), ('4', 'Vee', 'B', 2.54, 'power_in'), ('7', 'Vcc', 'T', 0, 'power_in')],
    'THAT 1246 balanced line receiver, -6 dB, SO-8')
CUSTOM['THAT1646'] = boxsym('THAT1646', 'U', 15.24, 15.24, [
    ('4', 'In', 'L', 0, 'input'),
    ('8', 'Out+', 'R', 5.08, 'output'), ('7', 'Sns+', 'R', 2.54, 'input'), ('2', 'Sns-', 'R', -2.54, 'input'), ('1', 'Out-', 'R', -5.08, 'output'),
    ('3', 'Gnd', 'B', -2.54, 'power_in'), ('5', 'Vee', 'B', 2.54, 'power_in'), ('6', 'Vcc', 'T', 0, 'power_in')],
    'THAT 1646 OutSmarts balanced line driver, +6 dB, SO-8')
CUSTOM['PGA2310'] = boxsym('PGA2310', 'U', 20.32, 25.4, [
    ('16', 'VINL', 'L', 10.16, 'input'), ('9', 'VINR', 'L', 5.08, 'input'),
    ('1', 'ZCEN', 'L', 0, 'input'), ('2', '~{CS}', 'L', -2.54, 'input'), ('3', 'SDI', 'L', -5.08, 'input'),
    ('6', 'SCLK', 'L', -7.62, 'input'), ('8', '~{MUTE}', 'L', -10.16, 'input'),
    ('14', 'VOUTL', 'R', 10.16, 'output'), ('11', 'VOUTR', 'R', 5.08, 'output'), ('7', 'SDO', 'R', -7.62, 'output'),
    ('12', 'VA+', 'T', -5.08, 'power_in'), ('4', 'VD+', 'T', 5.08, 'power_in'),
    ('15', 'AGNDL', 'B', -7.62, 'power_in'), ('10', 'AGNDR', 'B', -2.54, 'power_in'), ('5', 'DGND', 'B', 2.54, 'power_in'), ('13', 'VA-', 'B', 7.62, 'power_in')],
    'TI PGA2310 stereo audio volume control, +/-15 V max analog, SPI, DIP-16')
CUSTOM['TBA2_Dual'] = boxsym('TBA2_Dual', 'PS', 20.32, 15.24, [
    ('1', '+Vin', 'L', 5.08, 'power_in'), ('2', '-Vin', 'L', -5.08, 'power_in'),
    ('6', '+Vout', 'R', 5.08, 'power_out'), ('5', 'Common', 'R', 0, 'power_out'), ('4', '-Vout', 'R', -5.08, 'power_out')],
    'TRACO TBA 2 series isolated 2 W unregulated DC-DC, dual output, SIP-7 (pins 3, 7 absent)')
CUSTOM['ISO7762F'] = boxsym('ISO7762F', 'U', 20.32, 25.4, [
    ('1', 'VCC1', 'L', 10.16, 'power_in'), ('2', 'INA', 'L', 5.08, 'input'), ('3', 'INB', 'L', 2.54, 'input'), ('4', 'INC', 'L', 0, 'input'), ('5', 'IND', 'L', -2.54, 'input'),
    ('6', 'OUTE', 'L', -5.08, 'output'), ('7', 'OUTF', 'L', -7.62, 'output'), ('8', 'GND1', 'L', -10.16, 'power_in'),
    ('16', 'VCC2', 'R', 10.16, 'power_in'), ('15', 'OUTA', 'R', 5.08, 'output'), ('14', 'OUTB', 'R', 2.54, 'output'), ('13', 'OUTC', 'R', 0, 'output'), ('12', 'OUTD', 'R', -2.54, 'output'),
    ('11', 'INE', 'R', -5.08, 'input'), ('10', 'INF', 'R', -7.62, 'input'), ('9', 'GND2', 'R', -10.16, 'power_in')],
    'TI ISO7762F six-channel digital isolator, 4 forward / 2 reverse, fail-safe low outputs, SOIC-16 wide (DW)')
CUSTOM['L78L05'] = boxsym('L78L05', 'U', 12.7, 7.62, [
    ('3', 'VI', 'L', 0, 'power_in'), ('1', 'VO', 'R', 0, 'power_out'), ('2', 'GND', 'B', 0, 'power_in')],
    '100 mA 5 V linear regulator, TO-92 (1 = out, 2 = gnd, 3 = in)')
# Seeed XIAO RP2040. Pin numbers follow Seeed's footprint: 1-7 down the left row from the USB end (D0-D6),
# 8-14 up the right row from the far end (D7-D10, 3V3, GND, 5V), so 14 is opposite 1 at the USB end.
xleft = [('1', 'D0/GP26'), ('2', 'D1/GP27'), ('3', 'D2/GP28'), ('4', 'D3/GP29'), ('5', 'D4/SDA/GP6'), ('6', 'D5/SCL/GP7'), ('7', 'D6/TX/GP0')]
xright = [('14', '5V'), ('13', 'GND'), ('12', '3V3'), ('11', 'D10/MOSI/GP3'), ('10', 'D9/MISO/GP4'), ('9', 'D8/SCK/GP2'), ('8', 'D7/RX/GP1')]
xpins = [(num, n, 'L', 7.62 - i * 2.54, 'bidirectional') for i, (num, n) in enumerate(xleft)]
xpins += [(num, n, 'R', 7.62 - i * 2.54, {'5V': 'power_out', 'GND': 'power_in', '3V3': 'power_out'}.get(n, 'bidirectional')) for i, (num, n) in enumerate(xright)]
CUSTOM['XIAO_RP2040'] = boxsym('XIAO_RP2040', 'U', 33.02, 20.32, xpins,
    'Seeed Studio XIAO RP2040: USB-C, RP2040, 11 GPIO. Pin numbers as on the Seeed footprint (1-7 left row from the USB end, 8-14 right row from the far end).')

def copysym(lib, name, newname=None, value=None):
    s = libsym(KLIB + lib + '.kicad_sym', name)
    s = json.loads(json.dumps(s))  # deep copy (loses Q) -> re-mark quoted strings below
    def requote(e):
        if isinstance(e, list): return [requote(x) for x in e]
        return e
    s = requote(s)
    # deep copy lost Q types; re-parse via dump of original instead
    s = parse(dump(libsym(KLIB + lib + '.kicad_sym', name)))[0]
    base = name
    if newname:
        for e in s:
            if isinstance(e, list) and e[0] == 'symbol' and str(e[1]).startswith(base + '_'):
                e[1] = Q(newname + str(e[1])[len(base):])
        s[1] = Q(newname); base = newname
    if value:
        for e in s:
            if isinstance(e, list) and e[0] == 'property' and e[1] == 'Value': e[2] = Q(value)
    return lib, base, s

LIBSYMS = {}   # lib_id -> sexp
for lib, name in [('Device', 'R'), ('Device', 'C'), ('Device', 'C_Polarized'), ('Device', 'L'), ('Device', 'FerriteBead'), ('Device', 'LED'),
                  ('Switch', 'SW_DIP_x04'), ('Connector_Audio', 'AudioJack3_SwitchTR'),
                  ('power', 'GND'), ('power', '+12V'), ('power', '-12V'), ('power', '+5V'), ('power', '+5VA'), ('power', '+3V3'), ('power', 'PWR_FLAG')]:
    _, base, s = copysym(lib, name)
    LIBSYMS[f'{lib}:{base}'] = s
_, base, s = copysym('Amplifier_Operational', 'LM2904', newname='OPA2134', value='OPA2134')
_own = parse(dump(libsym(KLIB + 'Amplifier_Operational.kicad_sym', 'OPA2134')))[0]
_props = {e[1]: e for e in _own if isinstance(e, list) and e[0] == 'property'}
s = [e for e in s if not (isinstance(e, list) and e[0] == 'property')]
for i, e in enumerate(_own):
    if isinstance(e, list) and e[0] == 'property': s.insert(len([x for x in s if not (isinstance(x, list) and x[0] == 'symbol')]), e)
CUSTOM['OPA2134'] = s   # LM2904 drawing + OPA2134 properties, kept in the project library
# GND_USB: the USB-side ground (XIAO, USB-C shell, isolator side 1, DC-DC input). Same drawing as GND, its own net.
_, _, s = copysym('power', 'GND', newname='GND_USB', value='GND_USB')
for e in s:
    if isinstance(e, list) and e[0] == 'property' and e[1] == 'Description': e[2] = Q('Power symbol creates a global label with name "GND_USB", the USB-side ground')
CUSTOM['GND_USB'] = s
LIBSYMS_WRITE_EXTRA = {}
for k, v in CUSTOM.items():
    LIBSYMS[f'GhostFader:{k}'] = v

PINPOS = {}  # lib_id -> {(unit, num): (x, y)}
PINLIST = {}  # lib_id -> [(unit, num, x, y)]
PINUNITS = {}
for k, s in LIBSYMS.items():
    d = {}; lst = []
    for unit, num, name, et, x, y, rot, ln in sympins(s):
        d[(int(unit), num)] = (x, y)
        d.setdefault((0, num), (x, y))
        lst.append((int(unit), num, x, y))
    PINPOS[k] = d; PINLIST[k] = lst; PINUNITS[k] = len({u for u, *_ in lst if u != 0})

FOOTPRINTS = {
    'R': 'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal',
    'C': 'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm',
    'CNP': 'Capacitor_THT:CP_Radial_D5.0mm_P2.50mm',
    'CP': 'Capacitor_THT:CP_Radial_D6.3mm_P2.50mm',
    'L': 'Inductor_THT:L_Axial_L7.0mm_D3.3mm_P10.16mm_Horizontal_Fastron_MICC',
    'LED': 'LED_THT:LED_D3.0mm',
    'DIP4': 'Button_Switch_THT:SW_DIP_SPSTx04_Slide_6.7x11.72mm_W7.62mm_P2.54mm_LowProfile',
    'DIP16': 'Package_DIP:DIP-16_W7.62mm',
    'DIP8': 'Package_DIP:DIP-8_W7.62mm',
    'SO8': 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
    'SO16W': 'Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm',
    'TO92': 'Package_TO_SOT_THT:TO-92_Inline_Wide',
    'XIAO': 'GhostFader:XIAO_RP2040_THT',
    'TBA2': 'Converter_DCDC:Converter_DCDC_TRACO_TBA2-xxxx_Dual_THT',
    'JACK': 'Connector_Audio:Jack_6.35mm_Neutrik_NRJ6HF_Horizontal',
}

def symbbox(lib_id, unit):
    xs, ys = [], []
    for e in LIBSYMS[lib_id]:
        if not (isinstance(e, list) and e[0] == 'symbol'): continue
        u = int(str(e[1]).split('_')[-2])
        if u not in (0, unit): continue
        for gph in e:
            if not isinstance(gph, list): continue
            if gph[0] == 'rectangle':
                for k in ('start', 'end'):
                    v = [x for x in gph if isinstance(x, list) and x[0] == k][0]; xs.append(float(v[1])); ys.append(float(v[2]))
            elif gph[0] == 'polyline':
                pts = [x for x in gph if isinstance(x, list) and x[0] == 'pts'][0]
                for xy in pts[1:]: xs.append(float(xy[1])); ys.append(float(xy[2]))
            elif gph[0] == 'circle':
                c = [x for x in gph if isinstance(x, list) and x[0] == 'center'][0]; r = float([x for x in gph if isinstance(x, list) and x[0] == 'radius'][0][1])
                xs += [float(c[1]) - r, float(c[1]) + r]; ys += [float(c[2]) - r, float(c[2]) + r]
            elif gph[0] == 'arc':
                for k in ('start', 'mid', 'end'):
                    v = [x for x in gph if isinstance(x, list) and x[0] == k][0]; xs.append(float(v[1])); ys.append(float(v[2]))
    if not xs: return (-1.27, -1.27, 1.27, 1.27)
    return (min(xs), min(ys), max(xs), max(ys))

# ---------------------------------------------------------------- sheet builder
class Part:
    def __init__(self, sheet, lib_id, ref, value, x, y, rot=0, mirror=None, unit=1, fp='', hide_value=False):
        self.sheet, self.lib_id, self.ref, self.value = sheet, lib_id, ref, value
        self.x, self.y, self.rot, self.mirror, self.unit, self.fp = x, y, rot, mirror, unit, fp
        self.uuid = U(); self.hide_value = hide_value
    def xf(self, px, py):
        t = math.radians(self.rot); c, s = round(math.cos(t)), round(math.sin(t))
        rx, ry = px * c - py * s, px * s + py * c
        if self.mirror == 'x': ry = -ry
        if self.mirror == 'y': rx = -rx
        return round(self.x + rx, 4), round(self.y - ry, 4)
    def p(self, num):
        d = PINPOS[self.lib_id]
        key = (self.unit, str(num)) if (self.unit, str(num)) in d else (0, str(num))
        return self.xf(*d[key])
    def fields(self):
        """Return (ref_at, ref_just, val_at, val_just, angle, hide_value)."""
        x, y, rot = self.x, self.y, self.rot
        ang = {0: 0, 90: 90, 180: 0, 270: 90}[rot]
        lib = self.lib_id
        if lib.startswith('power:') or lib == 'GhostFader:GND_USB':
            name = self.value
            up = (rot == 0) != (name in ('GND', 'GND_USB'))
            vy = y - 3.81 if up else y + 3.81
            return ((x, y), 'left', (x, vy), 'center', 0, name == 'PWR_FLAG')
        if lib in BOX and not lib.endswith('OPA2134'):
            hw, hh = BOX[lib]
            return ((x + hw - 2.54, y - hh - 3.81), 'left', (x + hw - 2.54, y - hh - 1.27), 'left', 0, False)
        if lib.endswith('OPA2134'):
            if self.unit == 3: return ((x + 2.54, y - 1.27), 'left', (x + 2.54, y + 1.27), 'left', 0, False)
            return ((x - 5.08, y - 6.35), 'left', (x - 5.08, y + 6.35), 'left', 0, False)
        x0, y0, x1, y1 = symbbox(lib, self.unit)
        corners = [self.xf(px, py) for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
        bx0, bx1 = min(c[0] for c in corners), max(c[0] for c in corners)
        by0, by1 = min(c[1] for c in corners), max(c[1] for c in corners)
        two_pin = lib.split(':')[1] in ('R', 'C', 'C_Polarized', 'L', 'FerriteBead', 'LED')
        horizontal = two_pin and abs(self.p('1')[0] - self.p('2')[0]) > abs(self.p('1')[1] - self.p('2')[1])
        if two_pin and not horizontal:
            return ((bx1 + 1.27, y - 1.27), 'left', (bx1 + 1.27, y + 1.27), 'left', ang, False)
        if two_pin:
            return ((x, by0 - 1.27), 'center', (x, by1 + 1.27), 'center', ang, False)
        return ((bx0, by0 - 1.27), 'left', (bx0, by1 + 1.27), 'left', ang, False)
    def sexp(self, path):
        d = PINPOS[self.lib_id]
        nums = sorted({n for (u, n) in d if u in (0, self.unit)} if not self.lib_id.endswith('OPA2134') else {n for (u, n) in d if u == self.unit}, key=lambda s: (len(s), s))
        m = f' (mirror {self.mirror})' if self.mirror else ''
        lines = [f'(symbol (lib_id "{self.lib_id}") (at {self.x:g} {self.y:g} {self.rot:g}){m} (unit {self.unit}) (exclude_from_sim no) (in_bom {"no" if self.ref.startswith("#") else "yes"}) (on_board {"no" if self.ref.startswith("#") else "yes"}) (dnp no) (uuid "{self.uuid}")']
        (rx, ry), rj, (vx, vy), vj, ang, hv = self.fields()
        hv = hv or self.hide_value
        hvs = ' (hide yes)' if hv else ''
        hr = ' (hide yes)' if self.ref.startswith('#') else ''
        js = lambda j: '' if j == 'center' else f' (justify {j})'
        lines.append(f'  (property "Reference" "{self.ref}" (at {rx:g} {ry:g} {ang}) (effects (font (size 1.27 1.27)){js(rj)}{hr}))')
        lines.append(f'  (property "Value" "{self.value}" (at {vx:g} {vy:g} {ang}) (effects (font (size 1.27 1.27)){js(vj)}{hvs}))')
        lines.append(f'  (property "Footprint" "{self.fp}" (at {self.x:g} {self.y:g} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        lines.append(f'  (property "Datasheet" "" (at {self.x:g} {self.y:g} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        for n in nums:
            lines.append(f'  (pin "{n}" (uuid "{U()}"))')
        lines.append(f'  (instances (project "{PROJECT}" (path "{path}" (reference "{self.ref}") (unit {self.unit}))))')
        lines.append(')')
        return '\n'.join(lines)

class Sheet:
    def __init__(self, fname, title, comment=''):
        self.fname, self.title, self.comment = fname, title, comment
        self.parts, self.items, self.libs = [], [], set()
        self.wires, self.juncs, self.labpts = [], set(), set()
        self.sheet_uuid = U()   # uuid of the (sheet ...) element in the root
        self.file_uuid = U()
        self.npwr = 0
    def place(self, lib_id, ref, value, x, y, rot=0, mirror=None, unit=1, fp='', hide_value=False):
        p = Part(self, lib_id, ref, value, x, y, rot, mirror, unit, fp, hide_value)
        self.parts.append(p); self.libs.add(lib_id); return p
    def pwr(self, name, x, y, rot=0):
        self.npwr += 1
        lib = 'GhostFader:GND_USB' if name == 'GND_USB' else f'power:{name}'
        return self.place(lib, f'#PWR{self.npwr:03d}', name, x, y, rot)
    def flag(self, x, y, rot=0):
        self.npwr += 1
        return self.place('power:PWR_FLAG', f'#FLG{self.npwr:03d}', 'PWR_FLAG', x, y, rot)
    def wire(self, *pts):
        for a, b in zip(pts, pts[1:]):
            if a == b: continue
            assert a[0] == b[0] or a[1] == b[1], f'diagonal wire {a}->{b} on {self.fname}'
            self.wires.append(((round(a[0], 4), round(a[1], 4)), (round(b[0], 4), round(b[1], 4))))
    def junc(self, x, y):
        self.juncs.add((round(x, 4), round(y, 4)))
    def nc(self, pt):
        self.items.append(f'(no_connect (at {pt[0]:g} {pt[1]:g}) (uuid "{U()}"))')
    def label(self, name, x, y, rot=0):
        self.labpts.add((round(x, 4), round(y, 4)))
        j = {0: 'left bottom', 180: 'right bottom', 90: 'left bottom', 270: 'right bottom'}[rot]
        self.items.append(f'(label "{name}" (at {x:g} {y:g} {rot}) (effects (font (size 1.27 1.27)) (justify {j})) (uuid "{U()}"))')
    def glabel(self, name, x, y, rot=0, shape='input'):
        self.labpts.add((round(x, 4), round(y, 4)))
        j = {0: 'left', 180: 'right', 90: 'left', 270: 'right'}[rot]
        self.items.append(f'(global_label "{name}" (shape {shape}) (at {x:g} {y:g} {rot}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {j})) (uuid "{U()}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x:g} {y:g} 0) (effects (font (size 1.27 1.27)) (hide yes))))')
    def text(self, s, x, y, size=1.27):
        s = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        self.items.append(f'(text "{s}" (exclude_from_sim no) (at {x:g} {y:g} 0) (effects (font (size {size:g} {size:g})) (justify left bottom)) (uuid "{U()}"))')
    # stub helpers: draw a wire from a pin outward and terminate with something
    def stub(self, pt, d, n=2):
        dx, dy = {'L': (-1, 0), 'R': (1, 0), 'U': (0, -1), 'D': (0, 1)}[d]
        end = (round(pt[0] + dx * n * G, 4), round(pt[1] + dy * n * G, 4))
        self.wire(pt, end); return end
    def stub_pwr(self, pt, d, name, n=2):
        end = self.stub(pt, d, n)
        rot = {'U': 0, 'D': 180, 'L': 0, 'R': 0}[d] if name not in ('GND', 'GND_USB') else {'D': 0, 'U': 180, 'L': 0, 'R': 0}[d]
        self.pwr(name, *end, rot)
        return end
    def stub_glabel(self, pt, d, name, n=2, shape='input'):
        end = self.stub(pt, d, n)
        self.glabel(name, *end, {'L': 180, 'R': 0, 'U': 90, 'D': 270}[d], shape); return end
    def stub_label(self, pt, d, name, n=2):
        end = self.stub(pt, d, n)
        self.label(name, *end, {'L': 180, 'R': 0, 'U': 90, 'D': 270}[d]); return end
    def decap(self, x, y, ref, val, rail, kind='C', gnd='GND'):
        """Vertical bypass cap between rail (top) and gnd, or gnd (top) and a negative rail."""
        lib = {'C': 'Device:C', 'CP': 'Device:C_Polarized'}[kind]
        fp = FOOTPRINTS[{'C': 'C', 'CP': 'CP'}[kind]]
        if rail.startswith('-'):
            self.pwr(gnd, x, y, 180); self.place(lib, ref, val, x, y + 3.81, 0, fp=fp); self.pwr(rail, x, y + 7.62, 180)
        else:
            self.pwr(rail, x, y, 0); self.place(lib, ref, val, x, y + 3.81, 0, fp=fp); self.pwr(gnd, x, y + 7.62, 0)
    def pinpoints(self):
        pts = []
        for p in self.parts:
            for unit, num, x, y in PINLIST[p.lib_id]:
                if unit in (0, p.unit) or (unit != 0 and PINUNITS[p.lib_id] == 1):
                    pts.append(p.xf(x, y))
        return pts
    def finalize_wires(self):
        from collections import Counter
        pinpts = self.pinpoints()
        splitpts = set(pinpts) | self.juncs | self.labpts | {a for a, b in self.wires} | {b for a, b in self.wires}
        segs = []
        for a, b in self.wires:
            if a[0] == b[0]:
                inside = sorted(p for p in splitpts if p[0] == a[0] and min(a[1], b[1]) < p[1] < max(a[1], b[1]))
                if a[1] > b[1]: inside = inside[::-1]
            else:
                inside = sorted(p for p in splitpts if p[1] == a[1] and min(a[0], b[0]) < p[0] < max(a[0], b[0]))
                if a[0] > b[0]: inside = inside[::-1]
            chain = [a] + inside + [b]
            segs += list(zip(chain, chain[1:]))
        ends = Counter()
        for a, b in segs: ends[a] += 1; ends[b] += 1
        pc = Counter(pinpts)
        for pt, n in ends.items():
            if n + pc[pt] >= 3: self.juncs.add(pt)
        for a, b in segs:
            self.items.append(f'(wire (pts (xy {a[0]:g} {a[1]:g}) (xy {b[0]:g} {b[1]:g})) (stroke (width 0) (type default)) (uuid "{U()}"))')
        for x, y in sorted(self.juncs):
            self.items.append(f'(junction (at {x:g} {y:g}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')
    def write(self, root_uuid):
        self.finalize_wires()
        path = f'/{root_uuid}/{self.sheet_uuid}'
        out = [f'(kicad_sch (version 20250114) (generator "ghost-fader-gen") (generator_version "9.0") (uuid "{self.file_uuid}") (paper "A3")',
               f'  (title_block (title "{self.title}") (date "{DATE}") (rev "{REV}") (company "Ghost Fader") (comment 1 "{self.comment}") (comment 2 "https://chris-albert.github.io/ghost-fader/"))',
               '  (lib_symbols']
        for lib in sorted(self.libs):
            for name, src in LIBSYMS_WRITE_EXTRA.get(lib, [(lib, LIBSYMS[lib])]):
                sym = parse(dump(src))[0]
                sym[1] = Q(name)
                out.append(dump(sym, 2))
        out.append('  )')
        out += self.items
        out += [p.sexp(path) for p in self.parts]
        out.append(')')
        open(os.path.join(OUT, self.fname), 'w').write('\n'.join(out) + '\n')

# ---------------------------------------------------------------- Sheet 1: input
def build_input():
    s = Sheet('input.kicad_sch', 'Ghost Fader - Sheet 1: Balanced inputs', 'THAT 1246 receivers, plug sense')
    def channel(y0, J, U, Ct, Cr, Rp, side):
        j = s.place('Connector_Audio:AudioJack3_SwitchTR', J, 'NRJ6HF', 40.64, y0, fp=FOOTPRINTS['JACK'])
        S, R, RN, T, TN = j.p('S'), j.p('R'), j.p('RN'), j.p('T'), j.p('TN')
        # sleeve up to ground, tip-normal down to ground
        s.wire(S, (50.8, S[1]), (50.8, S[1] - 5.08)); s.pwr('GND', 50.8, S[1] - 5.08, 180)
        s.wire(TN, (50.8, TN[1]), (50.8, TN[1] + 5.08)); s.pwr('GND', 50.8, TN[1] + 5.08, 0)
        # ring-normal = plug sense
        s.stub_glabel(RN, 'R', f'SENSE_{side}', 4, 'output')
        u = s.place('GhostFader:THAT1246', U, 'THAT1246S08', 99.06, y0 + 2.54, fp=FOOTPRINTS['SO8'])
        inm, inp, vout, sense, ncp = u.p('2'), u.p('3'), u.p('6'), u.p('5'), u.p('8')
        assert inm[1] == R[1] and inp[1] == T[1]
        # tip -> In+ with RF cap to ground (below); ring -> In- with RF cap to ground (above)
        s.wire(T, inp); s.junc(63.5, T[1])
        ct = s.place('Device:C', Ct, '100p C0G', 63.5, T[1] + 3.81, fp=FOOTPRINTS['C']); s.pwr('GND', *ct.p('2'), 0)
        s.wire(R, inm); s.junc(71.12, R[1])
        cr = s.place('Device:C', Cr, '100p C0G', 71.12, R[1] - 3.81, fp=FOOTPRINTS['C']); s.pwr('GND', *cr.p('1'), 180)
        # sense tied to output, output leaves as global label
        s.wire(sense, (111.76, sense[1]), (111.76, vout[1])); s.junc(111.76, vout[1])
        s.wire(vout, (111.76, vout[1])); s.stub_glabel((111.76, vout[1]), 'R', f'{side}_SE', 6, 'output')
        s.nc(ncp)
        s.stub_pwr(u.p('1'), 'D', 'GND', 1)
        s.stub_pwr(u.p('4'), 'D', '-12V', 2)
        s.stub_pwr(u.p('7'), 'U', '+12V', 1)
        # plug-sense pull-up, drawn as its own snippet
        px, py = 40.64, y0 + 25.4
        s.pwr('+5VA', px, py, 0)
        r = s.place('Device:R', Rp, '100k', px, py + 3.81, fp=FOOTPRINTS['R'])
        s.wire(r.p('2'), (px, py + 10.16), (px + 7.62, py + 10.16)); s.glabel(f'SENSE_{side}', px + 7.62, py + 10.16, 0, 'output')
        s.text(f'{J} ring-normal contact: shorted to the ring (and so to {U} In-) with no plug,\nopen with any plug. Reads low when empty, high with TS or TRS plugged in.\n100k, not 1M: the ISO7762 input leaks up to 10 uA, and the pin must reach 0.7 x 5 V.', px + 22.86, py + 8.89, 1.0)
    channel(50.8, 'J1', 'U1', 'C1', 'C2', 'R1', 'L')
    channel(116.84, 'J2', 'U2', 'C7', 'C8', 'R14', 'R')
    s.text('Balanced inputs. A TS plug grounds the ring, so unbalanced sources need no switch.\nTHAT 1246 = -6 dB, so +22 dBu peak (9.75 Vrms) becomes 4.9 Vrms, inside the PGA2310 9.5 Vrms full scale.\n100 pF C0G on every tip and ring shunts RF to ground. Tip-normal grounded: an empty input is silent, not noisy.', 33.02, 35.56, 1.27)
    # decoupling for this sheet
    x0 = 200.66
    s.text('Bypass, one per supply pin, within 5 mm of U1 / U2. C40, C41 bulk for the input side.', x0, 45.72, 1.0)
    for i, (ref, val, rail, kind) in enumerate([('C21', '100n', '+12V', 'C'), ('C22', '100n', '-12V', 'C'), ('C23', '100n', '+12V', 'C'), ('C24', '100n', '-12V', 'C'),
                                                ('C40', '10u', '+12V', 'CP'), ('C41', '10u', '-12V', 'CP')]):
        s.decap(x0 + i * 12.7, 53.34, ref, val, rail, kind)
    return s

# ---------------------------------------------------------------- Sheet 2: matrix
def build_matrix():
    s = Sheet('matrix.kicad_sch', 'Ghost Fader - Sheet 2: 2x2 gain matrix and summers', 'PGA2310 pair, OPA2134 summers')
    def pga(uy, ref, cl, cr, sdi_from, sdo_to, outl, outr):
        u = s.place('GhostFader:PGA2310', ref, 'PGA2310PA', 101.6, uy, fp=FOOTPRINTS['DIP16'])
        # coupling caps into the two inputs
        vinl, vinr = u.p('16'), u.p('9')
        c1 = s.place('Device:C', cl, '10u NP', 76.2, vinl[1], 90, fp=FOOTPRINTS['CNP']); s.wire(c1.p('2'), vinl); s.stub_glabel(c1.p('1'), 'L', 'L_SE', 2)
        c2 = s.place('Device:C', cr, '10u NP', 66.04, vinr[1], 90, fp=FOOTPRINTS['CNP']); s.wire(c2.p('2'), vinr); s.stub_glabel(c2.p('1'), 'L', 'R_SE', 2)
        s.stub_pwr(u.p('1'), 'L', '+5VA', 2)
        s.stub_glabel(u.p('2'), 'L', '~{CS}', 4)
        s.stub_glabel(u.p('3'), 'L', sdi_from, 4)
        s.stub_glabel(u.p('6'), 'L', 'SCLK', 4)
        s.stub_glabel(u.p('8'), 'L', '~{MUTE}', 4)
        if sdo_to: s.stub_glabel(u.p('7'), 'R', sdo_to, 4, 'output')
        else: s.nc(u.p('7'))
        s.stub_pwr(u.p('12'), 'U', '+12V', 1)
        s.stub_pwr(u.p('4'), 'U', '+5VA', 1)
        # grounds to one bar
        gy = u.p('15')[1] + 5.08
        for n in ('15', '10', '5'): s.wire(u.p(n), (u.p(n)[0], gy))
        s.wire((u.p('15')[0], gy), (u.p('5')[0], gy)); s.junc(u.p('10')[0], gy); s.pwr('GND', u.p('5')[0], gy, 0)
        s.stub_pwr(u.p('13'), 'D', '-12V', 4)
        # outputs through 10k mix resistors to the summing nodes
        for pinn, (rref, node), dx in (('14', outl, 8.89), ('11', outr, 16.51)):
            pp = u.p(pinn)
            r = s.place('Device:R', rref, '10k', pp[0] + dx, pp[1], 90, fp=FOOTPRINTS['R'])
            s.wire(pp, r.p('1')); s.stub_label(r.p('2'), 'R', node, 2)
        return u
    pga(63.5, 'U3', 'C3', 'C4', 'SDI', 'U3_SDO', ('R2', 'L_SUM'), ('R6', 'R_SUM'))
    pga(129.54, 'U4', 'C5', 'C6', 'U3_SDO', None, ('R7', 'R_SUM'), ('R3', 'L_SUM'))
    s.text('U3 = direct paths (L->L on its left channel, R->R on its right).  U4 = cross paths (L->R on its left channel, R->L on its right).\nSPI chain: XIAO MOSI (D10) -> U8 isolator -> U3 SDI, U3 SDO -> U4 SDI. 32 clocks per update: U4 word first, then U3; each word is right byte then left byte, MSB first.\nZCEN high: gain changes wait for a zero crossing. Code 192 = 0 dB, 0 = mute. Logic supply is +5VA from U10 (sheet 5), on the audio ground; SDO stays on this side.',
           33.02, 170.18, 1.1)
    # summers
    def summer(uy, unit, node, rg, rf, outname):
        a = s.place('GhostFader:OPA2134', 'U5', 'OPA2134PA', 177.8, uy, 0, 'x', unit, fp=FOOTPRINTS['DIP8'])
        inp, inm, out = a.p({1: '3', 2: '5'}[unit]), a.p({1: '2', 2: '6'}[unit]), a.p({1: '1', 2: '7'}[unit])
        assert inm[1] < inp[1], 'mirror should put - on top'
        s.stub_label(inp, 'L', node, 3)
        # - input: to ground through Rg (left) and to output through Rf (over the top)
        s.wire(inm, (154.94, inm[1]))
        r1 = s.place('Device:R', rg, '10k', 151.13, inm[1], 90, fp=FOOTPRINTS['R'])
        s.wire(r1.p('1'), (147.32, inm[1]), (147.32, inm[1] + 7.62)); s.pwr('GND', 147.32, inm[1] + 7.62, 0)
        s.junc(165.1, inm[1])
        top = inm[1] - 7.62
        r2 = s.place('Device:R', rf, '10k', 177.8, top, 90, fp=FOOTPRINTS['R'])
        s.wire((165.1, inm[1]), (165.1, top), r2.p('1'))
        s.wire(r2.p('2'), (190.5, top), (190.5, out[1])); s.junc(190.5, out[1])
        s.wire(out, (190.5, out[1])); s.stub_glabel((190.5, out[1]), 'R', outname, 3, 'output')
    summer(63.5, 1, 'L_SUM', 'R4', 'R5', 'L_OUT_SE')
    summer(129.54, 2, 'R_SUM', 'R8', 'R9', 'R_OUT_SE')
    s.text('Summers: two 10k resistors into the + input make a passive 1/2 mix; the non-inverting x2 stage restores unity.\nWhen one path is muted its PGA output sits at 0 V, so the other still comes through at unity.', 147.32, 152.4, 1.1)
    # U5 power unit + decoupling row
    pu = s.place('GhostFader:OPA2134', 'U5', 'OPA2134PA', 233.68, 63.5, 0, None, 3, fp=FOOTPRINTS['DIP8'])
    s.stub_pwr(pu.p('8'), 'U', '+12V', 1); s.stub_pwr(pu.p('4'), 'D', '-12V', 1)
    x0 = 210.82
    s.text('Bypass, one per supply pin: U3 / U4 VA+, VA-, VD+; U5 V+, V-. C14 bulk on the +5VA logic rail beside U3.', x0, 96.52, 1.0)
    for i, (ref, val, rail, kind) in enumerate([('C25', '100n', '+12V', 'C'), ('C26', '100n', '-12V', 'C'), ('C27', '100n', '+5VA', 'C'),
                                                ('C28', '100n', '+12V', 'C'), ('C29', '100n', '-12V', 'C'), ('C30', '100n', '+5VA', 'C'),
                                                ('C31', '100n', '+12V', 'C'), ('C32', '100n', '-12V', 'C'), ('C14', '10u', '+5VA', 'CP')]):
        s.decap(x0 + (i % 5) * 12.7, 104.14 + (i // 5) * 20.32, ref, val, rail, kind)
    return s

# ---------------------------------------------------------------- Sheet 3: output
def build_output():
    s = Sheet('output.kicad_sch', 'Ghost Fader - Sheet 3: Balanced outputs', 'THAT 1646 cross-coupled drivers')
    def channel(y0, U, J, Csp, Csm, Rp, Rm, Ct, Cr, side):
        u = s.place('GhostFader:THAT1646', U, 'THAT1646S08', 88.9, y0, fp=FOOTPRINTS['SO8'])
        s.stub_glabel(u.p('4'), 'L', f'{side}_OUT_SE', 4)
        outp, snsp, snsm, outm = u.p('8'), u.p('7'), u.p('2'), u.p('1')
        # sense caps (datasheet fig. 5): Sns+ -> C -> Out+, Sns- -> C -> Out-
        for sns, out, ref, cx in ((snsp, outp, Csp, 104.14), (snsm, outm, Csm, 111.76)):
            c = s.place('Device:C', ref, '10u NP', cx, sns[1], 90, fp=FOOTPRINTS['CNP'])
            s.wire(sns, c.p('1')); s.wire(c.p('2'), (119.38, sns[1]), (119.38, out[1])); s.junc(119.38, out[1])
        # build-out resistors to the jack
        rp = s.place('Device:R', Rp, '10R', 127, outp[1], 90, fp=FOOTPRINTS['R'])
        rm = s.place('Device:R', Rm, '10R', 127, outm[1], 90, fp=FOOTPRINTS['R'])
        s.wire(outp, rp.p('1')); s.wire(outm, rm.p('1'))
        j = s.place('Connector_Audio:AudioJack3_SwitchTR', J, 'NRJ6HF', 157.48, y0, 180, fp=FOOTPRINTS['JACK'])
        T, R, S, RN, TN = j.p('T'), j.p('R'), j.p('S'), j.p('RN'), j.p('TN')
        assert T[1] == outp[1], (T, outp)
        s.wire(rp.p('2'), T); s.junc(137.16, T[1])
        ct = s.place('Device:C', Ct, '100p C0G', 137.16, T[1] - 3.81, fp=FOOTPRINTS['C']); s.pwr('GND', *ct.p('1'), 180)
        s.wire(rm.p('2'), (144.78, outm[1]), (144.78, R[1]), R); s.junc(137.16, outm[1])
        cr = s.place('Device:C', Cr, '100p C0G', 137.16, outm[1] + 3.81, fp=FOOTPRINTS['C']); s.pwr('GND', *cr.p('2'), 0)
        s.wire(S, (149.86, S[1]), (149.86, S[1] + 5.08)); s.pwr('GND', 149.86, S[1] + 5.08, 0)
        s.nc(RN); s.nc(TN)
        s.stub_pwr(u.p('6'), 'U', '+12V', 1)
        s.stub_pwr(u.p('3'), 'D', 'GND', 1)
        s.stub_pwr(u.p('5'), 'D', '-12V', 2)
    channel(50.8, 'U6', 'J3', 'C17', 'C18', 'R10', 'R11', 'C9', 'C10', 'L')
    channel(111.76, 'U7', 'J4', 'C19', 'C20', 'R12', 'R13', 'C15', 'C16', 'R')
    s.text('THAT 1646 = +6 dB cross-coupled driver. A TS plug on the output shorts Out- to ground; OutSmarts keeps the full signal on the tip.\n10 uF non-polar sense caps (datasheet figure 5) drop output DC offset from 250 mV to 15 mV. 10 R build-outs isolate cable capacitance.\nOutput jack switch contacts are not used.', 33.02, 35.56, 1.27)
    x0 = 200.66
    s.text('Bypass, one per supply pin, within 5 mm of U6 / U7. C42, C43 bulk for the output side.', x0, 45.72, 1.0)
    for i, (ref, val, rail, kind) in enumerate([('C33', '100n', '+12V', 'C'), ('C34', '100n', '-12V', 'C'), ('C35', '100n', '+12V', 'C'), ('C36', '100n', '-12V', 'C'),
                                                ('C42', '10u', '+12V', 'CP'), ('C43', '10u', '-12V', 'CP')]):
        s.decap(x0 + i * 12.7, 53.34, ref, val, rail, kind)
    return s

# ---------------------------------------------------------------- Sheet 4: control
def build_control():
    s = Sheet('control.kicad_sch', 'Ghost Fader - Sheet 4: Control', 'XIAO RP2040, USB MIDI, ISO7762F isolator, plug sense, SPI')
    t = s.place('GhostFader:XIAO_RP2040', 'U9', 'XIAO RP2040', 101.6, 101.6, fp=FOOTPRINTS['XIAO'])
    # left row: D0-D6. Everything on the XIAO is on the USB side (GND_USB); MCU_* nets go through U8.
    s.stub_label(t.p('1'), 'L', 'MCU_SENSE_L', 4)
    s.stub_label(t.p('2'), 'L', 'MCU_SENSE_R', 4)
    sw = s.place('Switch:SW_DIP_x04', 'SW1', 'MIDI channel', 45.72, 104.14, fp=FOOTPRINTS['DIP4'])
    for tp, sp in (('3', '8'), ('4', '7'), ('5', '6'), ('6', '5')):
        assert t.p(tp)[1] == sw.p(sp)[1]
        s.wire(sw.p(sp), t.p(tp))
    for sp in ('1', '2', '3', '4'):
        s.wire(sw.p(sp), (33.02, sw.p(sp)[1]))
    s.wire((33.02, sw.p('1')[1]), (33.02, sw.p('4')[1] + 5.08))
    s.pwr('GND_USB', 33.02, sw.p('4')[1] + 5.08, 0)
    s.stub_label(t.p('7'), 'L', 'MCU_~{MUTE}', 4)
    # right row, bottom up: D7-D10, 3V3, GND, 5V
    s.stub_label(t.p('8'), 'R', 'MCU_~{CS}', 4)
    s.stub_label(t.p('9'), 'R', 'MCU_SCLK', 4)
    s.stub_glabel(t.p('10'), 'R', 'LED', 4, 'output')
    s.stub_label(t.p('11'), 'R', 'MCU_SDI', 4)
    v33 = t.p('12'); s.wire(v33, (132.08, v33[1])); s.pwr('+3V3', 132.08, v33[1], 0)
    gnd = t.p('13'); s.wire(gnd, (127, gnd[1]), (127, gnd[1] - 5.08)); s.pwr('GND_USB', 127, gnd[1] - 5.08, 180)
    vin = t.p('14'); s.wire(vin, (124.46, vin[1]), (124.46, vin[1] - 5.08)); s.glabel('USB_5V', 124.46, vin[1] - 5.08, 90, 'output')
    # isolator: side 1 (pins 1-8) on the USB ground, side 2 (pins 9-16) on the audio ground
    u = s.place('GhostFader:ISO7762F', 'U8', 'ISO7762FDW', 182.88, 101.6, fp=FOOTPRINTS['SO16W'])
    s.stub_pwr(u.p('1'), 'L', '+3V3', 2)
    s.stub_label(u.p('2'), 'L', 'MCU_SCLK', 4)
    s.stub_label(u.p('3'), 'L', 'MCU_SDI', 4)
    s.stub_label(u.p('4'), 'L', 'MCU_~{CS}', 4)
    s.stub_label(u.p('5'), 'L', 'MCU_~{MUTE}', 4)
    s.stub_label(u.p('6'), 'L', 'MCU_SENSE_L', 4)
    s.stub_label(u.p('7'), 'L', 'MCU_SENSE_R', 4)
    s.stub_pwr(u.p('8'), 'L', 'GND_USB', 2)
    s.stub_pwr(u.p('16'), 'R', '+5VA', 2)
    s.stub_glabel(u.p('15'), 'R', 'SCLK', 4, 'output')
    s.stub_glabel(u.p('14'), 'R', 'SDI', 4, 'output')
    s.stub_glabel(u.p('13'), 'R', '~{CS}', 4, 'output')
    s.stub_glabel(u.p('12'), 'R', '~{MUTE}', 4, 'output')
    s.stub_glabel(u.p('11'), 'R', 'SENSE_L', 4)
    s.stub_glabel(u.p('10'), 'R', 'SENSE_R', 4)
    s.stub_pwr(u.p('9'), 'R', 'GND', 2)
    s.text('U8 ISO7762F: channels A-D carry SCLK, SDI, /CS, /MUTE from the XIAO (3.3 V) to the PGAs (5 V);\nE and F bring the plug-sense lines back. Side 1 runs from the XIAO 3V3 pin, side 2 from +5VA.\nF suffix = outputs fall to 0 when the other side is unpowered: the PGAs stay muted until the XIAO is up.\nThe RP2040 pins are not 5 V tolerant, so side 1 must stay on 3.3 V.', 152.4, 124.46, 1.0)
    # isolator bypass, one per side
    s.text('Bypass at U8: C39 on VCC1 (USB side), C44 on VCC2 (audio side).', 215.9, 88.9, 1.0)
    s.decap(220.98, 96.52, 'C39', '100n', '+3V3', 'C', gnd='GND_USB')
    s.decap(233.68, 96.52, 'C44', '100n', '+5VA', 'C')
    # LED snippet
    ly = 149.86
    s.glabel('LED', 48.26, ly, 180)
    r16 = s.place('Device:R', 'R16', '1k', 57.15, ly, 90, fp=FOOTPRINTS['R']); s.wire((48.26, ly), r16.p('1'))
    led = s.place('Device:LED', 'LED1', 'MIDI act', 68.58, ly, 180, fp=FOOTPRINTS['LED'])
    s.wire(r16.p('2'), led.p('2'))
    s.wire(led.p('1'), (76.2, ly), (76.2, ly + 5.08)); s.pwr('GND_USB', 76.2, ly + 5.08, 0)
    s.text('MIDI activity LED on D9 (GP4), about 2 mA. USB side.', 86.36, ly + 1.27, 1.0)
    # mute pull-down snippet (audio side, on the isolated /MUTE net)
    s.glabel('~{MUTE}', 48.26, 137.16, 180);
    r15 = s.place('Device:R', 'R15', '10k', 57.15, 137.16, 90, fp=FOOTPRINTS['R'])
    s.wire((48.26, 137.16), r15.p('1')); s.wire(r15.p('2'), (63.5, 137.16), (63.5, 139.7)); s.pwr('GND', 63.5, 139.7, 0)
    s.text('R15 holds both PGA2310s muted until the firmware writes its first gains: no power-on thump. Audio side, after U8.', 73.66, 138.43, 1.0)
    s.text('U9 is a Seeed XIAO RP2040 on header pins. Pin numbers are Seeed\'s: 1-7 down the left row from the USB end, 8-14 up the right row.\nIts USB-C is the only connector: class-compliant MIDI in (TinyUSB), 5 V in. The 5V pin is USB VBUS straight through, so it feeds the board.\nSPI0: D8 (GP2) SCK, D10 (GP3) MOSI, D7 (GP1) /CS, D6 (GP0) /MUTE. D9 (GP4, the MISO pin) drives the LED: bit-bang the 32-bit frame or leave SPI RX unassigned.\nNothing on the XIAO touches the audio ground: the four control lines and two sense lines cross U8, power crosses PS1. GND_USB is the USB-side ground.\nDIP switch on D2-D5 (GP28, GP29, GP6, GP7), closed = 0, internal pull-ups on. Plug sense on D0, D1 (GP26, GP27), internal pull-ups off (100k to +5VA on sheet 1).', 33.02, 45.72, 1.1)
    return s

# ---------------------------------------------------------------- Sheet 5: power
def build_power():
    s = Sheet('power.kicad_sch', 'Ghost Fader - Sheet 5: Power', 'USB 5 V in, isolated +/-12 V and +5VA, USB ground split from audio ground')
    y = 63.5
    s.glabel('USB_5V', 38.1, y, 180)
    fb = s.place('Device:FerriteBead', 'FB1', '600R@100MHz 1A', 49.53, y, 90, fp=FOOTPRINTS['L'])
    s.wire((38.1, y), fb.p('1'))
    ps = s.place('GhostFader:TBA2_Dual', 'PS1', 'TBA 2-0522', 91.44, y + 5.08, fp=FOOTPRINTS['TBA2'])
    vinp, vinm, vop, com, vom = ps.p('1'), ps.p('2'), ps.p('6'), ps.p('5'), ps.p('4')
    assert vinp[1] == y
    s.wire(fb.p('2'), vinp); s.junc(60.96, y); s.junc(71.12, y)
    c11 = s.place('Device:C_Polarized', 'C11', '47u low-ESR', 60.96, y + 3.81, fp=FOOTPRINTS['CP']); s.pwr('GND_USB', *c11.p('2'), 0)
    s.wire((71.12, y), (71.12, y - 7.62)); s.pwr('+5V', 71.12, y - 7.62, 0)
    s.flag(66.04, y - 7.62, 0); s.wire((66.04, y - 7.62), (71.12, y - 7.62)); s.junc(71.12, y - 7.62)
    s.wire(vinm, (73.66, vinm[1]), (73.66, vinm[1] + 5.08)); s.pwr('GND_USB', 73.66, vinm[1] + 5.08, 0)
    s.flag(66.04, vinm[1] + 5.08, 0); s.wire((66.04, vinm[1] + 5.08), (73.66, vinm[1] + 5.08)); s.junc(73.66, vinm[1] + 5.08)
    # +12 V
    l1 = s.place('Device:L', 'L1', '10uH 300mA', 113.03, vop[1], 90, fp=FOOTPRINTS['L'])
    s.wire(vop, l1.p('1')); s.wire(l1.p('2'), (144.78, vop[1])); s.pwr("+12V", 144.78, vop[1], 0); s.junc(121.92, vop[1])
    c12 = s.place('Device:C_Polarized', 'C12', '100u 25V', 121.92, vop[1] - 3.81, 180, fp=FOOTPRINTS['CP']); s.pwr('GND', *c12.p('2'), 180)
    s.flag(132.08, vop[1], 0); s.junc(132.08, vop[1])
    # star ground
    s.wire(com, (106.68, com[1]), (106.68, com[1] + 12.7)); s.pwr('GND', 106.68, com[1] + 12.7, 0)
    s.text('audio star ground', 109.22, com[1] + 18.5, 1.0)
    # -12 V
    l2 = s.place('Device:L', 'L2', '10uH 300mA', 113.03, vom[1], 90, fp=FOOTPRINTS['L'])
    s.wire(vom, l2.p('1')); s.wire(l2.p('2'), (144.78, vom[1])); s.pwr("-12V", 144.78, vom[1], 180); s.junc(121.92, vom[1])
    c13 = s.place('Device:C_Polarized', 'C13', '100u 25V', 121.92, vom[1] + 3.81, 180, fp=FOOTPRINTS['CP']); s.pwr('GND', *c13.p('1'), 0)
    s.flag(132.08, vom[1], 180); s.junc(132.08, vom[1])
    # +5VA: PGA logic and isolator side 2, from +12 V through a 78L05, on the audio ground
    y5 = 114.3
    s.pwr('+12V', 104.14, y5 - 5.08, 0); s.wire((104.14, y5 - 5.08), (104.14, y5))
    u10 = s.place('GhostFader:L78L05', 'U10', 'L78L05', 127, y5, fp=FOOTPRINTS['TO92'])
    vi, vo, ug = u10.p('3'), u10.p('1'), u10.p('2')
    assert vi[1] == y5 and vo[1] == y5
    s.wire((104.14, y5), vi); s.junc(110.49, y5)
    c37 = s.place('Device:C', 'C37', '100n', 110.49, y5 + 3.81, fp=FOOTPRINTS['C']); s.pwr('GND', *c37.p('2'), 0)
    s.stub_pwr(ug, 'D', 'GND', 1)
    s.wire(vo, (147.32, y5)); s.junc(140.97, y5)
    c38 = s.place('Device:C', 'C38', '100n', 140.97, y5 + 3.81, fp=FOOTPRINTS['C']); s.pwr('GND', *c38.p('2'), 0)
    s.wire((147.32, y5), (147.32, y5 - 5.08)); s.pwr('+5VA', 147.32, y5 - 5.08, 0)
    s.text('U10 78L05: +5VA for the PGA2310 logic, U8 side 2 and the plug-sense pull-ups, about 15 mA.\nOn the audio ground, so the 5 V logic never references USB. Input up to +14 V, 0.15 W in the TO-92.', 104.14, y5 + 18, 1.0)
    # barrier: one Y cap and a bleed resistor between the two grounds, at PS1
    bx, by = 177.8, 55.88
    s.pwr('GND_USB', bx, by, 180); s.wire((bx, by), (bx, by + 7.62)); s.junc(bx, by + 7.62)
    c45 = s.place('Device:C', 'C45', '1n 1kV', bx, by + 11.43, fp=FOOTPRINTS['C'])
    r17 = s.place('Device:R', 'R17', '1M', bx + 12.7, by + 11.43, fp=FOOTPRINTS['R'])
    assert c45.p('1')[1] == by + 7.62 and r17.p('1')[1] == by + 7.62
    s.wire((bx, by + 7.62), (bx + 12.7, by + 7.62))
    s.wire(c45.p('2'), (bx, by + 20.32)); s.wire(r17.p('2'), (bx + 12.7, by + 15.24), (bx + 12.7, by + 20.32), (bx, by + 20.32)); s.junc(bx, by + 15.24)
    s.pwr('GND', bx, by + 20.32, 0)
    s.text('Ground barrier. GND_USB (XIAO, USB-C shell, U8 side 1, PS1 input) and GND (everything audio, U8 side 2,\nPS1 output) meet only here: C45 gives the converter\'s switching noise a local return so it does not\nradiate as common mode, R17 stops the audio side floating away when nothing is plugged in.\nPlace both at PS1, on the 2 mm gap in the ground pours. No other copper crosses the gap.', bx - 12.7, by + 38, 1.0)
    s.text('No external power supply. Everything runs from the USB 5 V that the XIAO passes out on its 5V pin (sheet 4).\nPS1 is a board-mounted isolated 2 W DC-DC module: 5 V in, +/-12 V 80 mA out. Unregulated: the rails follow USB voltage and load,\nabout +/-11 V on a sagging port and up to +/-14 V at 5.25 V and light load; every part on the rails is rated for that (PGA2310 max 16 V).\nRails: +12 V ~55 mA (analog ~40 mA plus U10 ~15 mA), -12 V ~40 mA; the TBA 2 gives 80 mA per rail. Budget at 5 V: XIAO ~30 mA, PS1 ~230 mA, LED 2 mA;\n~260 mA typical, 330 mA worst case; USB 2.0 allows 500 mA. PS1 is the only power path across the ground barrier: its 1.5 kV isolation is what floats the audio side.\nAudio grounds meet once at PS1 Common. Keep PS1 at the far end of the board from J1 / J2. Total rail capacitance stays under the 220 uF the TBA 2 allows.', 33.02, 45.72, 1.1)
    s.text('Flags (unlabelled) mark +5V, +12V, -12V and GND_USB as driven for ERC, since they sit behind FB1 / L1 / L2 or the XIAO.', 147.32, 88.9, 1.0)
    return s

# ---------------------------------------------------------------- Root
def build_root(sheets):
    root_uuid = U()
    out = [f'(kicad_sch (version 20250114) (generator "ghost-fader-gen") (generator_version "9.0") (uuid "{root_uuid}") (paper "A4")',
           f'  (title_block (title "Ghost Fader - Rev D") (date "{DATE}") (rev "{REV}") (company "Ghost Fader") (comment 1 "USB-MIDI volume and pan for two balanced line channels") (comment 2 "https://chris-albert.github.io/ghost-fader/"))',
           '  (lib_symbols)']
    def txt(t, x, y, size=1.27):
        t = t.replace('"', '\\"').replace('\n', '\\n')
        return f'  (text "{t}" (exclude_from_sim no) (at {x:g} {y:g} 0) (effects (font (size {size:g} {size:g})) (justify left bottom)) (uuid "{U()}"))'
    out.append(txt('Ghost Fader', 25.4, 33.02, 3.5))
    out.append(txt('USB-MIDI-controlled volume and pan for two balanced 1/4" line channels. Bus powered, no external supply.\nSheets: 1 input, 2 matrix, 3 output, 4 control, 5 power. Nets between sheets are global labels; rails are power symbols.\nTwo grounds: GND_USB (XIAO, USB) and GND (audio). Only PS1 (power) and U8 (control) cross between them, plus C45 / R17.', 25.4, 40.64, 1.27))
    for i, sh in enumerate(sheets):
        x, y = 25.4 + (i % 3) * 63.5, 55.88 + (i // 3) * 33.02
        w, h = 50.8, 20.32
        out.append(f'  (sheet (at {x:g} {y:g}) (size {w:g} {h:g}) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000)) (uuid "{sh.sheet_uuid}")')
        out.append(f'    (property "Sheetname" "{sh.title.split(": ")[1]}" (at {x:g} {y - 0.7:g} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))')
        out.append(f'    (property "Sheetfile" "{sh.fname}" (at {x:g} {y + h + 0.6:g} 0) (effects (font (size 1.27 1.27)) (justify left top)))')
        out.append(f'    (instances (project "{PROJECT}" (path "/{root_uuid}" (page "{i + 2}"))))')
        out.append('  )')
    out.append(txt('Signal flow:  J1/J2 -> U1/U2 THAT1246 (-6 dB) -> C3-C6 -> U3/U4 PGA2310 2x2 matrix -> R2-R9 + U5 OPA2134 summers (x2) -> U6/U7 THAT1646 (+6 dB) -> J3/J4\nControl:      XIAO RP2040 USB MIDI -> U8 ISO7762F -> SPI (SCLK, SDI, /CS) + /MUTE -> U3 -> U4.  Plug sense from J1/J2 ring-normal contacts, back through U8.\nPower:        XIAO 5V pin (USB 5 V) -> FB1 -> PS1 TBA 2-0522 -> +/-12 V (audio ground).  +12 V -> U10 78L05 -> +5VA for PGA logic and U8 side 2.', 25.4, 130, 1.1))
    out.append('  (sheet_instances (path "/" (page "1")))')
    out.append(')')
    open(os.path.join(OUT, f'{PROJECT}.kicad_sch'), 'w').write('\n'.join(out) + '\n')
    return root_uuid

def write_project():
    pro = {"board": {"design_settings": {"defaults": {}, "rules": {'max_error': 0.005, 'min_clearance': 0.2, 'min_connection': 0.0, 'min_copper_edge_clearance': 0.25, 'min_groove_width': 0.0, 'min_hole_clearance': 0.25, 'min_hole_to_hole': 0.25, 'min_microvia_diameter': 0.2, 'min_microvia_drill': 0.1, 'min_resolved_spokes': 1, 'min_silk_clearance': 0.0, 'min_text_height': 0.8, 'min_text_thickness': 0.08, 'min_through_hole_diameter': 0.3, 'min_track_width': 0.2, 'min_via_annular_width': 0.1, 'min_via_diameter': 0.6, 'solder_mask_to_copper_clearance': 0.0, 'use_height_for_length_calcs': True}}, "layer_presets": [], "viewports": []},
           "boards": [], "cvpcb": {"equivalence_files": []},
           "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
           "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3},
           "net_settings": {"classes": [{'bus_width': 12, 'clearance': 0.25, 'diff_pair_gap': 0.25, 'diff_pair_via_gap': 0.25, 'diff_pair_width': 0.2, 'line_style': 0, 'microvia_diameter': 0.3, 'microvia_drill': 0.1, 'name': 'Default', 'pcb_color': 'rgba(0, 0, 0, 0.000)', 'priority': 2147483647, 'schematic_color': 'rgba(0, 0, 0, 0.000)', 'track_width': 0.3, 'via_diameter': 0.8, 'via_drill': 0.4, 'wire_width': 6}, {'bus_width': 12, 'clearance': 0.25, 'diff_pair_gap': 0.25, 'diff_pair_via_gap': 0.25, 'diff_pair_width': 0.2, 'line_style': 0, 'microvia_diameter': 0.3, 'microvia_drill': 0.1, 'name': 'Power', 'pcb_color': 'rgba(0, 0, 0, 0.000)', 'priority': -1, 'schematic_color': 'rgba(0, 0, 0, 0.000)', 'track_width': 0.6, 'via_diameter': 0.9, 'via_drill': 0.5, 'wire_width': 6}], "meta": {"version": 4}, "netclass_patterns": [{'netclass': 'Power', 'pattern': '+5V'}, {'netclass': 'Power', 'pattern': 'USB_5V'}, {'netclass': 'Power', 'pattern': '+12V'}, {'netclass': 'Power', 'pattern': '-12V'}, {'netclass': 'Power', 'pattern': 'GND'}, {'netclass': 'Power', 'pattern': 'GND_USB'}, {'netclass': 'Power', 'pattern': '+5VA'}, {'netclass': 'Power', 'pattern': 'Net-(PS1-+Vout)'}, {'netclass': 'Power', 'pattern': 'Net-(PS1--Vout)'}]},
           "pcbnew": {"page_layout_descr_file": ""},
           "schematic": {"drawing": {}, "legacy_lib_dir": "", "legacy_lib_list": [], "meta": {"version": 1}},
           "sheets": [], "text_variables": {}}
    json.dump(pro, open(os.path.join(OUT, f'{PROJECT}.kicad_pro'), 'w'), indent=2)
    open(os.path.join(OUT, 'sym-lib-table'), 'w').write('(sym_lib_table (version 7)\n  (lib (name "GhostFader")(type "KiCad")(uri "${KIPRJMOD}/GhostFader.kicad_sym")(options "")(descr "Ghost Fader project symbols"))\n)\n')
    open(os.path.join(OUT, 'fp-lib-table'), 'w').write('(fp_lib_table (version 7)\n  (lib (name "GhostFader")(type "KiCad")(uri "${KIPRJMOD}/GhostFader.pretty")(options "")(descr "Ghost Fader project footprints"))\n)\n')
    # symbol library with the custom parts
    lib = ['(kicad_symbol_lib (version 20241209) (generator "ghost-fader-gen") (generator_version "9.0")']
    for k, v in CUSTOM.items(): lib.append(dump(v, 1))
    lib.append(')')
    open(os.path.join(OUT, 'GhostFader.kicad_sym'), 'w').write('\n'.join(lib) + '\n')
    # footprints
    fpdir = os.path.join(OUT, 'GhostFader.pretty'); os.makedirs(fpdir, exist_ok=True)
    def fp(name, desc, pads, outline, attr='through_hole', extra=()):
        o = [f'(footprint "{name}" (version 20241229) (generator "ghost-fader-gen") (generator_version "9.0") (layer "F.Cu")',
             f'  (descr "{desc}")', f'  (attr {attr})',
             f'  (property "Reference" "REF**" (at 0 {outline[1] - 2:g} 0) (layer "F.SilkS") (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))',
             f'  (property "Value" "{name}" (at 0 {outline[3] + 2:g} 0) (layer "F.Fab") (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))',
             f'  (property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))',
             f'  (property "Description" "{desc}" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))']
        x0, y0, x1, y1 = outline
        for layer in ('F.SilkS', 'F.Fab'):
            for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
                o.append(f'  (fp_line (start {a[0]:g} {a[1]:g}) (end {b[0]:g} {b[1]:g}) (stroke (width 0.12) (type solid)) (layer "{layer}") (uuid "{U()}"))')
        for (ax, ay), (bx, by) in extra:   # extra silk/fab lines, e.g. a connector that overhangs the body
            for layer in ('F.SilkS', 'F.Fab'):
                o.append(f'  (fp_line (start {ax:g} {ay:g}) (end {bx:g} {by:g}) (stroke (width 0.12) (type solid)) (layer "{layer}") (uuid "{U()}"))')
        cy0 = min([y0] + [min(a[1], b[1]) for a, b in extra])
        o.append(f'  (fp_rect (start {x0 - 0.5:g} {cy0 - 0.5:g}) (end {x1 + 0.5:g} {y1 + 0.5:g}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{U()}"))')
        for num, x, y, shape in pads:
            o.append(f'  (pad "{num}" thru_hole {shape} (at {x:g} {y:g}) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask") (uuid "{U()}"))')
        o.append(')')
        open(os.path.join(fpdir, f'{name}.kicad_mod'), 'w').write('\n'.join(o) + '\n')
    # XIAO RP2040 on 2 x 7 header pins, 0.6 in row spacing, USB-C at the top (-y). Pad numbers follow Seeed's footprint:
    # 1-7 down the left row from the USB end, 8-14 up the right row. Body 21 x 17.8 mm; the USB-C shell overhangs the top edge by 1.4 mm.
    pads = []
    for i in range(7):
        pads.append((str(i + 1), -7.62, -7.62 + i * 2.54, 'rect' if i == 0 else 'circle'))
        pads.append((str(14 - i), 7.62, -7.62 + i * 2.54, 'circle'))
    usb = [((-4.5, -10.5), (-4.5, -11.9)), ((-4.5, -11.9), (4.5, -11.9)), ((4.5, -11.9), (4.5, -10.5))]
    fp('XIAO_RP2040_THT', 'Seeed Studio XIAO RP2040 on 2 x 7 header pins, 0.6 in row spacing, 2.54 mm pitch. Pad numbers as on the Seeed footprint (1-7 left row from the USB end, 8-14 right row from the far end). USB-C overhangs the top edge by 1.4 mm.', pads, (-8.89, -10.5, 8.89, 10.5), extra=usb)

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    sheets = [build_input(), build_matrix(), build_output(), build_control(), build_power()]
    root = build_root(sheets)
    for sh in sheets: sh.write(root)
    write_project()
    print('wrote', OUT)
