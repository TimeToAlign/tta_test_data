"""Build ``MTD_sample.zip``: four themes of the Musical Theme Dataset, all sixteen files each.

Usage, from anywhere::

    python data/mtd/make_sample.py /path/to/MTD_1.0.0.zip
    python data/mtd/make_sample.py /path/to/MTD_1.0.0.zip --check

The archive ``MTD_1.0.0.zip`` (https://www.audiolabs-erlangen.de/resources/MIR/MTD)
is read in place; nothing is extracted from it. The script writes
``MTD_sample.zip`` beside itself (``--out`` names another path), holding for
each theme of :data:`THEMES`:

* byte copies of the members MTD licenses under CC BY 4.0
  (:data:`LICENSED`), and of its ``LICENSE``;
* stand-ins for the members it does not license (:data:`STAND_INS`), each
  written here from the licensed files only, shaped like MTD's own files of
  that folder: ``data_EDM-orig_MID``, ``data_EDM-corr_MID`` and
  ``data_EDM-alig_MID`` from the theme's ``data_SCORE_MID`` and
  ``data_ALIGNMENT``, the three EDM CSV note lists from those stand-in MIDI
  files, ``data_SCORE_XML`` from ``data_SCORE_MID``, ``data_AUDIO`` from the
  excerpt's times in ``data_META``, and the two EDM PDFs as a page saying what
  they stand in for.

``--check`` compares every stand-in with MTD's own file of the same theme,
read in place, and prints what agrees and what differs; ``README.md`` beside
this script records the result.

The output is byte-identical on every run: members in sorted order, fixed
timestamps and attributes, no data that depends on the machine or the time.
Requires Python 3.10+ and mido.
"""

from __future__ import annotations

import argparse
import io
import sys
import wave
import zipfile
from bisect import bisect_right
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import mido

#: The themes of the sample, by the stem of their file names.
THEMES: tuple[str, ...] = (
    "MTD0807_Beethoven_Op002No1-01",
    "MTD0808_Beethoven_Op002No1-01",
    "MTD1044_Beethoven_Op055-02",
    "MTD1080_Beethoven_Op067-04",
)

#: The folders MTD licenses under CC BY 4.0, with their file name extension.
LICENSED: dict[str, str] = {
    "data_ALIGNMENT": "csv",
    "data_META": "json",
    "data_SCORE_CSV": "csv",
    "data_SCORE_IMG": "pdf",
    "data_SCORE_MID": "mid",
    "data_SCORE_SIB": "sib",
}

#: The folders MTD does not license, written here as stand-ins.
STAND_INS: dict[str, str] = {
    "data_AUDIO": "wav",
    "data_EDM-alig_CSV": "csv",
    "data_EDM-alig_MID": "mid",
    "data_EDM-corr_CSV": "csv",
    "data_EDM-corr_IMG": "pdf",
    "data_EDM-corr_MID": "mid",
    "data_EDM-orig_CSV": "csv",
    "data_EDM-orig_IMG": "pdf",
    "data_EDM-orig_MID": "mid",
    "data_SCORE_XML": "xml",
}

#: Ticks per quarter of every MIDI file of the MTD.
PPQ = 480

#: Microseconds per quarter: EDM-orig at 120 bpm, EDM-corr and EDM-alig at 60.
TEMPO_ORIG = 500_000
TEMPO_CORR = 1_000_000

#: Velocity of every note of MTD's EDM files.
EDM_VELOCITY = 60

#: The excerpt stand-in: mono, 8,000 frames per second, 16 bits.
WAV_RATE = 8000

#: A zip member's timestamp: year, month, day, hour, minute, second.
Date = tuple[int, int, int, int, int, int]

#: Timestamp of the stand-ins and of the folder entries in the zip.
STAND_IN_DATE: Date = (2026, 11, 26, 0, 0, 0)

#: Key signatures with flats, as mido names them; the others spell with sharps.
_FLAT_KEYS = {"F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb", "Dm", "Gm", "Cm", "Fm", "Bbm", "Ebm", "Abm"}
_SHARP_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
_FLAT_NAMES = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
_FIFTHS = {
    "Cb": -7, "Gb": -6, "Db": -5, "Ab": -4, "Eb": -3, "Bb": -2, "F": -1, "C": 0,
    "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7,
    "Abm": -7, "Ebm": -6, "Bbm": -5, "Fm": -4, "Cm": -3, "Gm": -2, "Dm": -1, "Am": 0,
    "Em": 1, "Bm": 2, "F#m": 3, "C#m": 4, "G#m": 5, "D#m": 6, "A#m": 7,
}  # fmt: skip


# region Reading the licensed files


@dataclass(frozen=True)
class Note:
    """A note in ticks: onset, end, MIDI pitch."""

    start: int
    end: int
    pitch: int


@dataclass(frozen=True)
class Score:
    """What the stand-ins take from a theme's ``data_SCORE_MID`` file."""

    notes: tuple[Note, ...]
    key: str
    meter: tuple[int, int]
    pickup: int
    end_of_track: int


def read_score_midi(data: bytes) -> Score:
    """The notes, key, meter, pickup and end of track of a SCORE MIDI file.

    The meter is the last time signature the file states; a first time
    signature followed by another at tick *t* > 0 makes the first *t* ticks a
    pickup (Sibelius writes a pickup bar as a bar of its own length).

    Raises:
        ValueError: If the file is not at 480 ticks per quarter, states no time
            signature, or states more than a pickup and one meter.
    """
    midi = mido.MidiFile(file=io.BytesIO(data))
    if midi.ticks_per_beat != PPQ:
        raise ValueError(f"expected {PPQ} ticks per quarter, got {midi.ticks_per_beat}")
    notes: list[Note] = []
    keys: list[str] = []
    meters: list[tuple[int, tuple[int, int]]] = []
    end_of_track = 0
    for track in midi.tracks:
        now = 0
        sounding: dict[tuple[int, int], int] = {}
        for message in track:
            now += message.time
            if message.type == "note_on" and message.velocity > 0:
                sounding[(message.channel, message.note)] = now
            elif message.type in ("note_on", "note_off"):
                start = sounding.pop((message.channel, message.note))
                notes.append(Note(start, now, message.note))
            elif message.type == "key_signature":
                keys.append(message.key)
            elif message.type == "time_signature":
                meters.append((now, (message.numerator, message.denominator)))
            elif message.type == "end_of_track":
                end_of_track = max(end_of_track, now)
    if not meters or len(meters) > 2:
        raise ValueError(f"expected one meter, with or without a pickup; got {meters}")
    pickup = meters[1][0] if len(meters) == 2 else 0
    return Score(
        notes=tuple(sorted(notes, key=lambda n: (n.start, n.pitch))),
        key=keys[0] if keys else "C",
        meter=meters[-1][1],
        pickup=pickup,
        end_of_track=end_of_track,
    )


def read_alignment(data: bytes) -> list[tuple[Fraction, Fraction]]:
    """The rows of a ``data_ALIGNMENT`` file as exact (quarters, seconds) pairs."""
    lines = data.decode("utf-8").splitlines()
    if lines[0] != '"MID";"WAV"':
        raise ValueError(f"unexpected alignment header {lines[0]!r}")
    rows = []
    for line in lines[1:]:
        if line:
            mid, wav = line.split(";")
            rows.append((Fraction(Decimal(mid)), Fraction(Decimal(wav))))
    return rows


def excerpt_seconds(meta: bytes) -> Fraction:
    """``EndTime - StartTime`` of a META file, exact (``mm:ss.s`` each)."""
    import json

    fields = json.loads(meta)

    def seconds(text: str) -> Fraction:
        minutes, rest = text.split(":")
        return Fraction(int(minutes) * 60) + Fraction(Decimal(rest))

    return seconds(fields["EndTime"]) - seconds(fields["StartTime"])


# endregion


# region Writing the stand-ins


def _note_messages(notes: tuple[Note, ...]) -> list[tuple[int, int, int, int]]:
    """``(tick, pitch, order, velocity)``: note-ons, each note ended by a note-on of velocity 0.

    Sorted as MTD's EDM files order them: by tick, then pitch; a note's end
    before an onset of the same pitch at the same tick.
    """
    events = []
    for note in notes:
        events.append((note.start, note.pitch, 1, EDM_VELOCITY))
        events.append((note.end, note.pitch, 0, 0))
    return sorted(events)


def _timed(events: list[tuple[int, mido.Message | mido.MetaMessage]]) -> list:
    """Messages at absolute ticks turned into a track of delta times."""
    track = []
    now = 0
    for tick, message in events:
        track.append(message.copy(time=tick - now))
        now = tick
    return track


def _meta(score: Score) -> list[mido.MetaMessage]:
    """The time and key signature of an EDM file: the theme's meter and key."""
    numerator, denominator = score.meter
    return [
        mido.MetaMessage(
            "time_signature",
            numerator=numerator,
            denominator=denominator,
            clocks_per_click=24,
            notated_32nd_notes_per_beat=8,
        ),
        mido.MetaMessage("key_signature", key=score.key),
    ]


def _save(midi: mido.MidiFile) -> bytes:
    buffer = io.BytesIO()
    midi.save(file=buffer)
    return buffer.getvalue()


def edm_shaped_midi(score: Score, notes: tuple[Note, ...]) -> bytes:
    """A MIDI file as MTD writes EDM-corr and EDM-alig.

    Type 1 at 480 ticks per quarter. The meta track holds the tempo 1,000,000 µs
    per quarter (60 bpm), the theme's time and key signature, and ends at tick
    1; the note track holds a program change and the notes at velocity 60, each
    ended by a note-on of velocity 0, and ends one tick after the last note.
    """
    meta = mido.MidiTrack(
        [mido.MetaMessage("set_tempo", tempo=TEMPO_CORR), *_meta(score)]
        + [mido.MetaMessage("end_of_track", time=1)]
    )
    events: list[tuple[int, mido.Message | mido.MetaMessage]] = [
        (0, mido.Message("program_change", program=0))
    ]
    for tick, pitch, _, velocity in _note_messages(notes):
        events.append((tick, mido.Message("note_on", note=pitch, velocity=velocity)))
    events.append((max(n.end for n in notes) + 1, mido.MetaMessage("end_of_track")))
    midi = mido.MidiFile(type=1, ticks_per_beat=PPQ)
    midi.tracks += [meta, mido.MidiTrack(_timed(events))]
    return _save(midi)


def edm_orig_midi(score: Score) -> bytes:
    """A MIDI file as MTD writes EDM-orig.

    Type 0 at 480 ticks per quarter: the theme's time and key signature, the
    tempo 500,000 µs per quarter (120 bpm), the notes at velocity 60 each ended
    by a note-on of velocity 0; the track ends at the end of the last note.
    """
    events: list[tuple[int, mido.Message | mido.MetaMessage]] = [
        (0, message) for message in _meta(score)
    ]
    events.append((0, mido.MetaMessage("set_tempo", tempo=TEMPO_ORIG)))
    for tick, pitch, _, velocity in _note_messages(score.notes):
        events.append((tick, mido.Message("note_on", note=pitch, velocity=velocity)))
    events.append((max(n.end for n in score.notes), mido.MetaMessage("end_of_track")))
    midi = mido.MidiFile(type=0, ticks_per_beat=PPQ)
    midi.tracks.append(mido.MidiTrack(_timed(events)))
    return _save(midi)


def aligned_notes(score: Score, rows: list[tuple[Fraction, Fraction]]) -> tuple[Note, ...]:
    """The theme's notes moved to the excerpt's seconds, as MTD makes EDM-alig.

    A position in quarters maps through the alignment rows, linearly between
    the two rows around it (beyond the first or last row, along the first or
    last segment); the second it maps to is a quarter of the 60 bpm file, its
    tick the nearest at 480 per quarter (a half rounds up). A note at an
    aligned onset therefore starts at its row's second.
    """
    mids = [mid for mid, _ in rows]

    def tick(position: Fraction) -> int:
        i = min(max(bisect_right(mids, position) - 1, 0), len(rows) - 2)
        (q0, s0), (q1, s1) = rows[i], rows[i + 1]
        second = s0 + (position - q0) * (s1 - s0) / (q1 - q0)
        return int((second * PPQ + Fraction(1, 2)) // 1)

    return tuple(
        Note(tick(Fraction(n.start, PPQ)), tick(Fraction(n.end, PPQ)), n.pitch) for n in score.notes
    )


def note_list_csv(notes: tuple[Note, ...], tempo: int, *, quoted: bool = True) -> bytes:
    """A CSV note list as MTD writes them: ``Start;Duration;Pitch`` in seconds.

    The second of a tick is ``tick * (seconds_per_quarter / 480)`` in floats,
    the duration the end's second minus the onset's, each as Python writes a
    float (this reproduces every row of MTD's note lists of the four themes
    to the last digit). MTD quotes the header of every note list but
    EDM-alig's.
    """
    per_tick = tempo / 1_000_000 / PPQ
    header = '"Start";"Duration";"Pitch"' if quoted else "Start;Duration;Pitch"
    lines = [header]
    for note in sorted(notes, key=lambda n: (n.start, n.pitch)):
        start = note.start * per_tick
        end = note.end * per_tick
        lines.append(f"{start!r};{end - start!r};{note.pitch}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _spelling(pitch: int, key: str) -> tuple[str, int, int]:
    """Step, alter and octave of a MIDI pitch: flats in a flat key, sharps otherwise."""
    name = (_FLAT_NAMES if key in _FLAT_KEYS else _SHARP_NAMES)[pitch % 12]
    alter = {"#": 1, "b": -1}.get(name[1:], 0)
    return name[0], alter, pitch // 12 - 1


def score_musicxml(score: Score, stem: str) -> bytes:
    """A MusicXML file of the theme's notes, in whole bars of its meter.

    One part, divisions of 480 per quarter (the MIDI file's ticks). A pickup,
    if the SCORE MIDI file states one, is the first bar, at its own length; the
    other bars are whole bars of the meter. A chord lasts from its onset to the
    next onset, or, before a rest and at the end, to one tick after its notes
    end (Sibelius exports every note one tick short); the last bar is filled
    with a rest. So the file ends at the end of its last bar, which lies after
    the SCORE MIDI file's end of track unless the theme ends on a barline.

    Raises:
        ValueError: If a note crosses a barline (the stand-in writes no ties).
    """
    numerator, denominator = score.meter
    bar = PPQ * 4 * numerator // denominator
    onsets = sorted({n.start for n in score.notes})
    chords = []
    for i, onset in enumerate(onsets):
        pitches = sorted(n.pitch for n in score.notes if n.start == onset)
        sounding_end = max(n.end for n in score.notes if n.start == onset) + 1
        end = min(onsets[i + 1], sounding_end) if i + 1 < len(onsets) else sounding_end
        chords.append((onset, end, pitches))
    last = chords[-1][1]
    barlines = [0] if score.pickup == 0 else [0, score.pickup]
    while barlines[-1] < last:
        barlines.append(barlines[-1] + bar)
    fifths = _FIFTHS[score.key]
    mode = "minor" if score.key.endswith("m") else "major"

    measures = []
    for number, (begin, close) in enumerate(
        zip(barlines, barlines[1:]), start=0 if score.pickup else 1
    ):
        content = []
        now = begin
        for onset, end, pitches in chords:
            if not begin <= onset < close:
                continue
            if end > close:
                raise ValueError(f"{stem}: a note at tick {onset} crosses the barline at {close}")
            if onset > now:
                content.append(
                    f"<note><rest/><duration>{onset - now}</duration><voice>1</voice></note>"
                )
            for k, pitch in enumerate(pitches):
                step, alter, octave = _spelling(pitch, score.key)
                alter_tag = f"<alter>{alter}</alter>" if alter else ""
                chord_tag = "<chord/>" if k else ""
                content.append(
                    f"<note>{chord_tag}<pitch><step>{step}</step>{alter_tag}"
                    f"<octave>{octave}</octave></pitch><duration>{end - onset}</duration>"
                    "<voice>1</voice></note>"
                )
            now = end
        if now < close:
            content.append(
                f"<note><rest/><duration>{close - now}</duration><voice>1</voice></note>"
            )
        attributes = ""
        if begin == 0:
            attributes = (
                f"<attributes><divisions>{PPQ}</divisions>"
                f"<key><fifths>{fifths}</fifths><mode>{mode}</mode></key>"
                f"<time><beats>{numerator}</beats><beat-type>{denominator}</beat-type></time>"
                "<clef><sign>G</sign><line>2</line></clef></attributes>"
            )
        implicit = ' implicit="yes"' if score.pickup and begin == 0 else ""
        measures.append(
            f'  <measure number="{number}"{implicit}>\n   {attributes}'
            + "\n   ".join(content)
            + "\n  </measure>\n"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.0 Partwise//EN" '
        '"http://www.musicxml.org/dtds/partwise.dtd">\n'
        '<score-partwise version="3.0">\n'
        f" <work><work-title>Stand-in for MTD/data_SCORE_XML/{stem}.xml</work-title></work>\n"
        " <part-list>\n"
        '  <score-part id="P1"><part-name>Theme</part-name></score-part>\n'
        " </part-list>\n"
        ' <part id="P1">\n' + "".join(measures) + " </part>\n</score-partwise>\n"
    ).encode("utf-8")


def stand_in_pdf(member: str) -> bytes:
    """A valid one-page PDF saying which MTD file it stands in for."""
    lines = [
        f"Stand-in for MTD/{member}",
        "MTD does not license this folder; this page is not MTD's file.",
        "See README.md of the mtd test corpus.",
    ]
    text = "".join(
        f"BT /F1 10 Tf 20 {70 - 18 * i} Td ({line}) Tj ET\n" for i, line in enumerate(lines)
    ).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 90] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(text)).encode() + b" >>\nstream\n" + text + b"endstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(out)


def silent_wav(seconds: Fraction) -> bytes:
    """A WAV of silence, mono, 8,000 Hz, 16 bit, exactly *seconds* long.

    Raises:
        ValueError: If *seconds* is not a whole number of frames.
    """
    frames = seconds * WAV_RATE
    if frames.denominator != 1:
        raise ValueError(f"{seconds} seconds is not a whole number of frames at {WAV_RATE} Hz")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(WAV_RATE)
        out.writeframes(b"\x00\x00" * int(frames))
    return buffer.getvalue()


def stand_ins(archive: zipfile.ZipFile, stem: str) -> dict[str, bytes]:
    """The stand-ins of one theme, by member path relative to ``MTD/``."""

    def read(folder: str) -> bytes:
        return archive.read(f"MTD/{folder}/{stem}.{LICENSED[folder]}")

    score = read_score_midi(read("data_SCORE_MID"))
    rows = read_alignment(read("data_ALIGNMENT"))
    aligned = aligned_notes(score, rows)
    files = {
        "data_EDM-orig_MID": edm_orig_midi(score),
        "data_EDM-corr_MID": edm_shaped_midi(score, score.notes),
        "data_EDM-alig_MID": edm_shaped_midi(score, aligned),
        "data_EDM-orig_CSV": note_list_csv(score.notes, TEMPO_ORIG),
        "data_EDM-corr_CSV": note_list_csv(score.notes, TEMPO_CORR),
        "data_EDM-alig_CSV": note_list_csv(aligned, TEMPO_CORR, quoted=False),
        "data_SCORE_XML": score_musicxml(score, stem),
        "data_AUDIO": silent_wav(excerpt_seconds(read("data_META"))),
    }
    for folder in ("data_EDM-orig_IMG", "data_EDM-corr_IMG"):
        files[folder] = stand_in_pdf(f"{folder}/{stem}.pdf")
    assert set(files) == set(STAND_INS)
    return {f"{folder}/{stem}.{STAND_INS[folder]}": data for folder, data in files.items()}


# endregion


# region The zip


def _info(name: str, date: Date, *, directory: bool = False) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=date)
    info.create_system = 3
    if directory:
        info.external_attr = (0o40755 << 16) | 0x10
        info.compress_type = zipfile.ZIP_STORED
    else:
        info.external_attr = 0o100644 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
    return info


def build(archive_path: Path, out: Path) -> None:
    """Write the sample zip from the MTD archive."""
    members: dict[str, tuple[bytes, Date]] = {}
    with zipfile.ZipFile(archive_path) as archive:
        members["LICENSE"] = (archive.read("LICENSE"), archive.getinfo("LICENSE").date_time)
        for stem in THEMES:
            for folder, extension in LICENSED.items():
                name = f"MTD/{folder}/{stem}.{extension}"
                members[name] = (archive.read(name), archive.getinfo(name).date_time)
            for name, data in stand_ins(archive, stem).items():
                members[f"MTD/{name}"] = (data, STAND_IN_DATE)
    folders = {"MTD/"} | {name.rsplit("/", 1)[0] + "/" for name in members if "/" in name}
    entries = sorted([(f, None) for f in folders] + [(m, members[m]) for m in members])
    tmp = out.with_suffix(".part")
    with zipfile.ZipFile(tmp, "w") as zipped:
        for name, held in entries:
            if held is None:
                zipped.writestr(_info(name, STAND_IN_DATE, directory=True), b"")
            else:
                data, date = held
                zipped.writestr(_info(name, date), data, compresslevel=9)
    tmp.replace(out)


# endregion


# region Checking the stand-ins against MTD's own files


def _midi_facts(data: bytes) -> dict[str, object]:
    midi = mido.MidiFile(file=io.BytesIO(data))
    notes, tempos, meters, keys, ends = [], [], [], [], []
    for track in midi.tracks:
        now = 0
        sounding: dict[int, int] = {}
        for message in track:
            now += message.time
            if message.type == "note_on" and message.velocity > 0:
                sounding[message.note] = now
            elif message.type in ("note_on", "note_off"):
                notes.append((sounding.pop(message.note), now, message.note))
            elif message.type == "set_tempo":
                tempos.append(message.tempo)
            elif message.type == "time_signature":
                meters.append((message.numerator, message.denominator))
            elif message.type == "key_signature":
                keys.append(message.key)
            elif message.type == "end_of_track":
                ends.append(now)
    return {
        "type": midi.type,
        "tracks": len(midi.tracks),
        "ticks per quarter": midi.ticks_per_beat,
        "tempo": tempos,
        "time signature": meters,
        "key": keys,
        "notes (onset, end, pitch)": sorted(notes),
        "end of track": max(ends),
    }


def _musicxml_length(data: bytes) -> Fraction:
    """The sum of the bars' lengths in quarters: each bar as long as its longest voice."""
    import xml.etree.ElementTree as ET

    root = ET.fromstring(data)
    divisions = 1
    total = Fraction(0)
    for measure in root.find("part"):
        for element in measure.iter("divisions"):
            divisions = int(element.text)
        position = longest = 0
        for element in measure:
            if element.tag == "note" and element.find("chord") is None:
                position += int(element.find("duration").text)
            elif element.tag == "backup":
                position -= int(element.find("duration").text)
            elif element.tag == "forward":
                position += int(element.find("duration").text)
            longest = max(longest, position)
        total += Fraction(longest, divisions)
    return total


def _musicxml_pitches(data: bytes) -> list[int]:
    import xml.etree.ElementTree as ET

    steps = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    pitches = []
    for pitch in ET.fromstring(data).iter("pitch"):
        alter = pitch.find("alter")
        pitches.append(
            12 * (int(pitch.find("octave").text) + 1)
            + steps[pitch.find("step").text]
            + (0 if alter is None else int(float(alter.text)))
        )
    return pitches


def _csv_rows(data: bytes) -> list[list[str]]:
    return [line.split(";") for line in data.decode("utf-8").splitlines() if line]


def check(archive_path: Path) -> int:
    """Print, per theme and stand-in, what agrees with MTD's own file and what differs."""
    differences = 0
    with zipfile.ZipFile(archive_path) as archive:
        for stem in THEMES:
            print(f"== {stem}")
            for name, mine in stand_ins(archive, stem).items():
                theirs = archive.read(f"MTD/{name}")
                folder = name.split("/")[0]
                if mine == theirs:
                    print(f"  {folder}: byte-identical")
                    continue
                if name.endswith(".mid"):
                    a, b = _midi_facts(mine), _midi_facts(theirs)
                    found = {k: (a[k], b[k]) for k in a if a[k] != b[k]}
                    if not found:
                        found["bytes"] = "the same notes, tempo, signatures and end of track"
                elif name.endswith(".csv"):
                    a, b = _csv_rows(mine), _csv_rows(theirs)
                    found = {}
                    if a[0] != b[0]:
                        found["header"] = (a[0], b[0])
                    if [r[2] for r in a[1:]] != [r[2] for r in b[1:]]:
                        found["pitches"] = ([r[2] for r in a[1:]], [r[2] for r in b[1:]])
                    for column, k in (("Start", 0), ("Duration", 1)):
                        diffs = [
                            (x[k], y[k]) for x, y in zip(a[1:], b[1:], strict=True) if x[k] != y[k]
                        ]
                        if diffs:
                            worst = max(abs(float(x) - float(y)) for x, y in diffs)
                            found[column] = (
                                f"{len(diffs)} of {len(a) - 1} differ, by at most {worst:.3g} s"
                            )
                elif name.endswith(".xml"):
                    found = {}
                    la, lb = _musicxml_length(mine), _musicxml_length(theirs)
                    if la != lb:
                        found["length (quarters)"] = (la, lb)
                    pa, pb = _musicxml_pitches(mine), _musicxml_pitches(theirs)
                    if pa != pb:
                        found["pitches"] = (pa, pb)
                    found["bytes"] = "a minimal file, not Sibelius's export"
                elif name.endswith(".wav"):
                    with wave.open(io.BytesIO(mine)) as w1, wave.open(io.BytesIO(theirs)) as w2:
                        d1 = Fraction(w1.getnframes(), w1.getframerate())
                        d2 = Fraction(w2.getnframes(), w2.getframerate())
                        found = {"seconds": (d1, d2)} if d1 != d2 else {}
                        found["format"] = (
                            (w1.getnchannels(), w1.getframerate(), 8 * w1.getsampwidth()),
                            (w2.getnchannels(), w2.getframerate(), 8 * w2.getsampwidth()),
                        )
                        found["samples"] = "silence"
                else:
                    found = {"bytes": "a page naming the file stood in for"}
                print(f"  {folder}: differs (stand-in, MTD)")
                for key, value in found.items():
                    print(f"      {key}: {value}")
                differences += 1
    return differences


# endregion


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("archive", type=Path, help="MTD_1.0.0.zip, read in place")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().with_name("MTD_sample.zip"),
        help="the zip to write (default: MTD_sample.zip beside this script)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare the stand-ins with MTD's own files instead of writing the zip",
    )
    args = parser.parse_args(argv)
    if args.check:
        check(args.archive)
        return 0
    build(args.archive, args.out)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
