# Ghost Fader

USB-MIDI-controlled volume and pan for two balanced 1/4" line channels. Balanced in, always-balanced out, one input becomes stereo automatically. Bus-powered Seeed XIAO RP2040 plus a 2x2 gain matrix of PGA2310 attenuators. Revision C: USB only, no DIN jack, no DC jack; a XIAO RP2040 and a 2 W Traco TBA 2-0522 (+/-12 V) replace rev B's Teensy 4.0 and TMR 3-0523, which takes about $35 off the parts cost without touching the audio path.

The full schematic package (block diagram, five sheets, level budget, USB power budget, MIDI map, build order) is published at https://chris-albert.github.io/ghost-fader/ (source: `docs/index.html`). This file is the short version.

## Signal chain

```
J1/J2 TRS in -> THAT 1246 (bal->SE, -6 dB) -> 2x PGA2310 (2x2 matrix, 4 gains)
             -> OPA1642 summers (non-inverting, x2) -> THAT 1646 (SE->bal, +6 dB) -> J3/J4 TRS out
```

- Net gain balanced-to-balanced is 0 dB at PGA code 192. PGA range is +31.5 to -95.5 dB in 0.5 dB steps, plus hard mute.
- A TS plug on an input grounds the ring, so unbalanced sources need no switch. A TS plug on an output is handled by the cross-coupled 1646.
- Plug sense: each input jack's ring-normal contact is pulled up to 3.3 V by 1 M and read by the XIAO (D0, D1). Tip-normal is grounded.
- Matrix: U3 carries the direct paths (L->L, R->R), U4 the cross paths (L->R, R->L). Mono mode pans the L input across both outputs with a constant-power law; stereo mode uses balance.

## Power

Everything runs from the USB cable. There is no external power supply, DC jack or wall adapter. The XIAO's 5V pin is USB VBUS straight through, so it exports the bus 5 V. That feeds PS1, a small isolated 5 V -> +/-12 V DC-DC converter soldered to the board (Traco TBA 2-0522, 2 W, SIP-7), for the analog stages and, directly, the PGA2310 logic supply.

PS1 is unregulated: the rails follow the USB voltage and the load, from about +/-11 V on a sagging port to about +/-14 V at 5.25 V and light load. Every part on the rails is rated for that (the PGA2310 absolute maximum is 16 V, which is why the +/-15 V TBA 2-0523 is not used). Headroom at +/-12 V is about 2 dB less than on +/-15 V: the output driver clips near +22 dBu instead of +24. Total rail capacitance, about 120 uF per rail, stays under the 220 uF the TBA 2 allows.

| Load | Current at 5 V |
|---|---|
| XIAO RP2040 | ~30 mA |
| PS1 delivering ~30 mA per +/-12 V rail at ~80 % | ~180 mA |
| PGA logic (15 mA each), LED | ~30 mA |
| Total | ~250 mA typical, ~320 mA worst case |

USB 2.0 ports allow 500 mA; USB 3 / USB-C ports allow 900 mA or more. Use a real port or a powered hub and a data cable (not charge-only).

Ground note: the audio ground is tied to the computer's USB ground. Fine when the same computer also drives the PA through an audio interface. If it hums in a setup where the computer only sends MIDI, add a TI ISO7762 digital isolator on the 4 SPI/mute lines and 2 sense lines and feed the PGA logic from +12 V through a 78L05. That floats the whole analog side.

## XIAO RP2040 pins

| Pin | Signal |
|---|---|
| USB-C | MIDI in (class-compliant, TinyUSB) and 5 V in |
| 5V | USB 5 V out to FB1, PS1, PGA VD |
| 3V3 | Plug-sense pull-ups |
| D0, D1 (GP26, GP27) | SENSE_L, SENSE_R (external 1 M pull-ups, internal pull-up off) |
| D2-D5 (GP28, GP29, GP6, GP7) | MIDI channel DIP, INPUT_PULLUP |
| D6 (GP0) | /MUTE to both PGA2310 (10 k pull-down mutes at boot) |
| D7 (GP1) | /CS |
| D8 (GP2, SCK) | SCLK |
| D9 (GP4, the MISO pin) | MIDI activity LED. Nothing comes back from the PGAs, so bit-bang the frame or leave SPI RX unassigned |
| D10 (GP3, MOSI) | SDI of U3; U3 SDO chains to U4 SDI |

The schematic symbol numbers the XIAO's 14 pins as Seeed's footprint does: 1-7 down the left row from the USB end (D0-D6), 8-14 up the right row (D7-D10, 3V3, GND, 5V).

SPI frame: 32 bits per update, U4's 16-bit word first, then U3's. Each word is the right-channel byte then the left. Code = 192 + 2 * dB, 0 = mute.

## MIDI map (proposed)

| CC | Function |
|---|---|
| 7 | Volume, 127 = 0 dB, 40*log10(v/127) dB |
| 10 | Pan (mono: constant power; stereo: balance) |
| 14, 15 | L / R input trim, +/-12 dB, 64 = 0 dB |
| 85 | Mono sum on/off |
| 120 | Hard mute |

## Parts list

Prices are approximate single-piece USD.

| Ref | Qty | Part | Description | ~$ ea | Notes |
|---|---|---|---|---|---|
| U1, U2 | 2 | THAT 1246S08 | Balanced line receiver, -6 dB | 5.50 | Alt: TI INA137 |
| U3, U4 | 2 | TI PGA2310PA | Stereo volume control, +/-15 V, SPI, DIP-16 | 11.00 | PGA2310UA for SOIC. Not PGA2311 |
| U5 | 1 | TI OPA2134PA | Dual JFET op-amp, DIP-8 | 4.00 | Alt: NE5532P |
| U6, U7 | 2 | THAT 1646S08 | Cross-coupled balanced driver, +6 dB | 5.50 | Alt: TI DRV134 |
| U9 | 1 | Seeed XIAO RP2040 | MCU with USB-C, class-compliant USB MIDI via TinyUSB | 5.00 | On header pins. Its 5V pin is USB VBUS and feeds the board |
| PS1 | 1 | Traco TBA 2-0522 | Board-mounted isolated DC-DC, 4.5-5.5 V in, +/-12 V 80 mA, 2 W, unregulated, SIP-7 | 5.00 | Fed from USB 5 V, not an external supply. Any industry-standard SIP-7 2 W +/-12 V module (Mornsun B0512, RECOM RB-0512D) has the same pinout. Not a +/-15 V part: unregulated rails would pass the PGA2310's 16 V maximum at light load |
| FB1 | 1 | Ferrite bead 600 R @ 100 MHz, >=1 A | Keeps switching noise off USB | 0.20 | |
| J1-J4 | 4 | Neutrik NRJ6HF | 1/4" TRS PCB jack, T and R switching | 3.00 | Switch contacts used on J1, J2 only |
| L1, L2 | 2 | 10 uH, >=300 mA | Rail filters | 0.40 | |
| SW1 | 1 | 4-way DIP | MIDI channel | 0.80 | |
| LED1 | 1 | 3 mm LED | Activity | 0.15 | |
| C3-C6, C17-C20 | 8 | 10 uF non-polar | C3-C6 coupling into PGA inputs, C17-C20 THAT 1646 sense caps | 0.40 | Nichicon UES |
| C1, C2, C7-C10, C15, C16 | 8 | 100 pF C0G | RF caps at every jack tip and ring | 0.10 | |
| C11 | 1 | 47 uF 10 V low-ESR | USB-side reservoir | 0.25 | |
| C12, C13 | 2 | 100 uF 25 V | Rail filters | 0.25 | |
| C14 | 1 | 10 uF | 5 V logic rail | 0.10 | |
| C21-C36 | 16 | 100 nF X7R | One per supply pin | 0.05 | |
| C40-C43 | 4 | 10 uF 25 V | +/-12 V bulk, input end and output end | 0.10 | |
| R2-R9 | 8 | 10 k 1% | Summing and feedback | 0.05 | |
| R10-R13 | 4 | 10 R | Output build-out | 0.05 | |
| R1, R14 | 2 | 1 M | Plug-sense pull-ups | 0.05 | |
| R15, R16 | 2 | 10 k, 1 k | Mute pull-down, LED | 0.05 | |
| CABLE | 1 | USB A/C to USB-C data cable | Short and thick | 3.00 | |
| ENC | 1 | Hammond 1590BB | Die-cast enclosure | 12.00 | |
| PCB | 1 | 2-layer 108 x 80 mm | Gerbers in `hardware/gerbers/` | 10.00 | Corner notches clear the 1590BB lid-screw bosses |

Estimated total: about $110 per unit, or about $100 with the narrow board in a printed box instead of the 1590BB. Cost-down variant with one PGA2310 and a DG419 routing switch instead of the matrix: about $90, loses cross-feed and mono-sum.

## Full schematic

`hardware/kicad/` is a KiCad 9 project: root sheet plus input, matrix, output, control and power sheets, with a project symbol library (THAT 1246/1646, PGA2310, OPA2134, XIAO RP2040, TBA 2) and a footprint for the XIAO on header pins; the TBA 2 uses KiCad's stock SIP-7 footprint. ERC passes with zero violations and the netlist has been checked pin-for-pin against `hardware/kicad/tools/check.py`. `bom.csv` is the KiCad BOM export. Rendered sheets and a PDF are in `docs/schematic/` and on the published page.

Every part has a footprint; the jacks use KiCad's stock Neutrik NRJ6HF horizontal footprint, whose pad names match the symbol. The schematic is generated by `hardware/kicad/tools/gen.py`; edit it in KiCad directly from here on, or edit the generator and rerun it (it needs KiCad's stock symbol libraries at the macOS install path).

## PCB

`hardware/kicad/ghost-fader.kicad_pcb` is a routed 2-layer board, 108 x 80 mm, DRC clean against the schematic (the only warnings are the jack noses' and the USB-C shell's silkscreen crossing the board edge, which is inherent to the footprints). Gerbers, Excellon drill file and drill map are in `hardware/gerbers/` and zipped as `hardware/ghost-fader-gerbers.zip`; upload the zip as-is to JLCPCB, PCBWay or OSH Park (2 layers, 1.6 mm, any finish). Renders are in `docs/pcb/` and on the published page.

Layout, rear edge at the top:

- The four jacks sit along one long edge, IN L, IN R, OUT L, OUT R at 19, 39, 68 and 90 mm from the left edge. Their threaded noses stick 1.5 mm past the board edge so the panel nuts have thread to bite. Drill the enclosure wall on those centres.
- Signal flows down and around: jacks -> RF caps -> THAT 1246 receivers (rotated so the inputs face the jacks) -> coupling caps -> the two PGA2310s side by side, analog pins facing up and SPI pins facing the XIAO -> OPA2134 summer and its resistors on the right -> THAT 1646 drivers under the output jacks with their sense caps and build-outs.
- The XIAO is at the front-left with its USB-C face flush with the front edge; cut a slot in the front wall for the plug. The DIP switch is next to it, and the DC-DC converter, ferrite, reservoir and rail filters sit front-centre, the far corner from the input receivers.
- Every decoupling cap is within a few mm of its supply pin. The +/-12 V bulk pairs are at the input end (C40/C41, between J2 and J3) and the output end (C42/C43, right edge).
- Ground is a solid pour on both layers, stitched by the ground tracks the router laid first, so the "star at PS1 COM" of the schematic notes becomes a plane. Power nets are 0.6 mm tracks, signals 0.3 mm, 0.25 mm clearance; anyone can fab it.
- The board is held by the four jack nuts. The corners are notched 7.5 x 6.5 mm to clear the 1590BB lid-screw bosses. Check fit against the actual box before ordering: the inside is about 112 x 86 mm at the base, so there is 2 to 3 mm each way.

The LED is a through-hole 3 mm at the front-right corner; bend it to face the front panel or fit a light pipe. To regenerate the board from the schematic (placement is a table in `tools/build_pcb.py`, routing is Freerouting):

```
cd hardware/kicad
kicad-cli sch export netlist --format kicadsexpr -o /tmp/gf.net ghost-fader.kicad_sch
<KiCad python3> tools/build_pcb.py /tmp/gf.net          # placement, outline, pours, rules
<KiCad python3> tools/route.py ghost-fader.kicad_pcb <freerouting launcher or jar>
kicad-cli pcb drc --severity-all --schematic-parity -o /tmp/drc.rpt ghost-fader.kicad_pcb
```

`<KiCad python3>` is the interpreter bundled with KiCad (on macOS `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`), which has the `pcbnew` module. Freerouting 1.9 was used; 2.4 routes the same board but writes an empty session file from the command line.

## Narrow in-line PCB

`hardware/kicad/ghost-fader-narrow.kicad_pcb` is the same schematic on a second, independent board shaped for a signal chain: 207 x 38 mm, inputs on the right end, outputs on the left, the XIAO's USB-C out of the middle of the rear long edge, so the box sits in-line like a pedal. It is as narrow as two side-by-side jacks allow: the NRJ6HF jacks sit on an 18 mm pitch (34.8 mm) plus edge clearance. The XIAO (21 mm long) lies across the board with its USB-C at the rear edge. It needs a 3D-printed box: about 40 x 210 mm inside, a ledge under the long board edges, two jack holes in each end wall on the jack centres (10 and 28 mm from the rear edge of the board, at the NRJ6HF bushing height), a USB-C slot and a 3 mm LED hole in the rear wall. No mounting holes; the four jack nuts hold the board. Routed, DRC clean against the schematic (the same jack-nose silkscreen warnings as the main board), 0.6 mm power tracks, 0.3 mm signals, ground pour both sides. Gerbers in `hardware/gerbers-narrow/` and `hardware/ghost-fader-narrow-gerbers.zip`; renders in `docs/pcb-narrow/`. The 1590BB board above is unchanged.

Everything runs in columns along the length, left to right: output jacks, RF caps, drivers with their sense caps stacked, build-outs and 100n, summer with its resistors, coupling caps, the two PGA2310s stacked across the board with their SPI rows facing each other, XIAO, DIP switch and pull-ups over the +/-12 V bulk caps, DC-DC with the ferrite, reservoir and rail filters, receivers, bulk caps, RF caps, input jacks. Most reference labels sit on the part bodies because there is no room beside them; they read on the bare board. Parts come within 1 mm of the long edges, so give the printed walls clearance above the board edge.

To regenerate: same steps as above with `tools/build_pcb_narrow.py` in place of `tools/build_pcb.py` and `ghost-fader-narrow.kicad_pcb` as the board.

## Notes

- The overview sheets label IC pins by function. The KiCad schematic in `hardware/kicad/` has the real pin numbers and is the one to lay out from.
- PGA2310 logic inputs are TTL-threshold, so 3.3 V from the XIAO drives them. Never route a PGA SDO (5 V) back into the XIAO.
- Ground is a pour on both layers; the DC-DC is at the far end of the board from the input receivers.
