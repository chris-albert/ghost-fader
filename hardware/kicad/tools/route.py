#!/usr/bin/env python3
"""Autoroute ghost-fader.kicad_pcb with Freerouting, then refill the ground pours.

  python3 tools/route.py <board.kicad_pcb> <freerouting launcher or jar> [passes]

The launcher is either the macOS app's Contents/MacOS/freerouting binary or a freerouting jar (run with java).
Uses KiCad's bundled Python (pcbnew). Exports a Specctra DSN, routes it, imports the SES back into the board.
"""
import sys, os, subprocess
import pcbnew

board_path, fr = sys.argv[1], sys.argv[2]
passes = sys.argv[3] if len(sys.argv) > 3 else '100'
base = os.path.splitext(board_path)[0]
dsn, ses = base + '.dsn', base + '.ses'

board = pcbnew.LoadBoard(board_path)
for t in list(board.GetTracks()):        # start from an unrouted board
    board.Remove(t)
zones = [z for z in board.Zones() if not z.GetIsRuleArea()]   # route GND with real tracks, then put the pours back on top; keepouts stay for the DSN
for z in zones:
    board.Remove(z)
assert pcbnew.ExportSpecctraDSN(board, dsn), 'DSN export failed'

cmd = ['java', '-jar', fr] if fr.endswith('.jar') else [fr]
cmd += ['-de', dsn, '-do', ses, '-mp', passes, '-l', 'en']
print(' '.join(cmd))
r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
tail = (r.stdout + r.stderr).strip().splitlines()[-8:]
print('\n'.join(tail))
assert os.path.exists(ses), 'freerouting produced no .ses'

assert pcbnew.ImportSpecctraSES(board, ses), 'SES import failed'
for z in zones:
    board.Add(z)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(board_path, board)
tracks = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK']
vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
print(f'routed: {len(tracks)} track segments, {len(vias)} vias -> {board_path}')
