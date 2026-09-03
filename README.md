# Ghost Fader

USB-MIDI-controlled volume and pan for two balanced 1/4" line channels. Balanced in, always-balanced out, one input becomes stereo automatically. Bus-powered Teensy 4.0 plus a 2x2 gain matrix of PGA2310 attenuators. Revision B: USB only, no DIN jack, no DC jack.

The full schematic package (block diagram, five sheets, level budget, USB power budget, MIDI map, build order) is `hardware/ghost-fader.html`. This file is the short version.

## Signal chain

```
J1/J2 TRS in -> THAT 1246 (bal->SE, -6 dB) -> 2x PGA2310 (2x2 matrix, 4 gains)
             -> OPA1642 summers (non-inverting, x2) -> THAT 1646 (SE->bal, +6 dB) -> J3/J4 TRS out
```

- Net gain balanced-to-balanced is 0 dB at PGA code 192. PGA range is +31.5 to -95.5 dB in 0.5 dB steps, plus hard mute.
- A TS plug on an input grounds the ring, so unbalanced sources need no switch. A TS plug on an output is handled by the cross-coupled 1646.
- Plug sense: each input jack's ring-normal contact is pulled up to 3.3 V by 1 M and read by the Teensy (pins 2, 3). Tip-normal is grounded.
- Matrix: U3 carries the direct paths (L->L, R->R), U4 the cross paths (L->R, R->L). Mono mode pans the L input across both outputs with a constant-power law; stereo mode uses balance.

## Power

Everything runs from the USB cable. The Teensy's VUSB-VIN pad stays intact, so the VIN pin exports the bus 5 V. That feeds an isolated 5 V -> +/-15 V DC-DC module (Traco TMR 3-0523) for the analog stages and, directly, the PGA2310 logic supply.

| Load | Current at 5 V |
|---|---|
| Teensy 4.0 (600 MHz / 150 MHz) | ~100 mA / ~50 mA |
| PS1 delivering ~35 mA per +/-15 V rail at ~80 % | ~260 mA |
| PGA logic, LED | ~10 mA |
| Total | ~370 mA typical, ~450 mA worst case |

USB 2.0 ports allow 500 mA; USB 3 / USB-C ports allow 900 mA or more. Use a real port or a powered hub, set the Teensy clock to 150 MHz in firmware, and use a data cable (not charge-only).

Ground note: the audio ground is tied to the computer's USB ground. Fine when the same computer also drives the PA through an audio interface. If it hums in a setup where the computer only sends MIDI, add a TI ISO7762 digital isolator on the 4 SPI/mute lines and 2 sense lines and feed the PGA logic from +15 V through a 78L05. That floats the whole analog side.

## Teensy 4.0 pins

| Pin | Signal |
|---|---|
| USB | MIDI in (class-compliant) and 5 V in |
| VIN | USB 5 V out to FB1, PS1, PGA VD |
| 2, 3 | SENSE_L, SENSE_R (external 1 M pull-ups, internal pull-up off) |
| 4-7 | MIDI channel DIP, INPUT_PULLUP |
| 8 | MIDI activity LED |
| 9 | /MUTE to both PGA2310 (10 k pull-down mutes at boot) |
| 10 | /CS |
| 11 (MOSI) | SDI of U3; U3 SDO chains to U4 SDI |
| 13 (SCK) | SCLK |

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
| U3, U4 | 2 | TI PGA2310UA | Stereo volume control, +/-15 V, SPI | 11.00 | PGA2310PA for DIP. Not PGA2311 |
| U5 | 1 | TI OPA1642AID | Dual JFET op-amp | 4.00 | Alt: NE5532 |
| U6, U7 | 2 | THAT 1646S08 | Cross-coupled balanced driver, +6 dB | 5.50 | Alt: TI DRV134 |
| U9 | 1 | PJRC Teensy 4.0 | MCU with USB MIDI | 24.00 | Leave VUSB-VIN pad intact |
| PS1 | 1 | Traco TMR 3-0523 | Isolated DC-DC, 4.5-9 V in, +/-15 V 100 mA | 22.00 | Any 2-3 W +/-15 V module, 5 V in |
| FB1 | 1 | Ferrite bead 600 R @ 100 MHz, >=1 A | Keeps switching noise off USB | 0.20 | |
| J1-J4 | 4 | Neutrik NRJ6HF | 1/4" TRS PCB jack, T and R switching | 3.00 | Switch contacts used on J1, J2 only |
| L1, L2 | 2 | 10 uH, >=300 mA | Rail filters | 0.40 | |
| SW1 | 1 | 4-way DIP | MIDI channel | 0.80 | |
| LED1 | 1 | 3 mm LED | Activity | 0.15 | |
| C3-C6 | 4 | 10 uF non-polar | Coupling into PGA inputs | 0.40 | Nichicon UES or 4.7 uF film |
| C1, C2, C7-C10 + 2 | 8 | 100 pF C0G | RF caps at every jack tip and ring | 0.10 | |
| C11 | 1 | 47 uF 10 V low-ESR | USB-side reservoir | 0.25 | |
| C12, C13 | 2 | 100 uF 25 V | Rail filters | 0.25 | |
| C14 | 1 | 10 uF | 5 V logic rail | 0.10 | |
| Cdec | 12 | 100 nF X7R | One per supply pin | 0.05 | Plus 10 uF per rail near THAT parts |
| R2-R9 | 8 | 10 k 1% | Summing and feedback | 0.05 | |
| R10-R13 | 4 | 10 R | Output build-out | 0.05 | |
| R1, R14 | 2 | 1 M | Plug-sense pull-ups | 0.05 | |
| R15, R16 | 2 | 10 k, 1 k | Mute pull-down, LED | 0.05 | |
| CABLE | 1 | USB A/C to micro-B data cable | Short and thick | 3.00 | |
| ENC | 1 | Hammond 1590BB | Die-cast enclosure | 12.00 | |
| PCB | 1 | 2-layer ~100 x 80 mm | | 10.00 | |

Estimated total: about $145 per unit. Cost-down variant with one PGA2310 and a DG419 routing switch instead of the matrix: about $125, loses cross-feed and mono-sum.

## Notes

- IC pins in the schematic are labelled by function. Take pin numbers from the current datasheet when laying out.
- PGA2310 logic inputs are TTL-threshold, so 3.3 V from the Teensy drives them. Never route a PGA SDO (5 V) back into the Teensy.
- Single star ground at PS1's COM pin. Keep the DC-DC at the far end of the board from the input receivers.
