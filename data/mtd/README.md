# Musical Theme Dataset: four themes

`MTD_sample.zip` holds four themes of the Musical Theme Dataset (MTD 1.0.0)
with all sixteen files each, in the layout of the MTD archive, read in place
by `MtdLoader`:

    MTD_sample.zip
    ├── LICENSE
    └── MTD
        ├── data_ALIGNMENT/<stem>.csv      copied
        ├── data_AUDIO/<stem>.wav          stand-in
        ├── data_EDM-alig_CSV/<stem>.csv   stand-in
        ├── data_EDM-alig_MID/<stem>.mid   stand-in
        ├── data_EDM-corr_CSV/<stem>.csv   stand-in
        ├── data_EDM-corr_IMG/<stem>.pdf   stand-in
        ├── data_EDM-corr_MID/<stem>.mid   stand-in
        ├── data_EDM-orig_CSV/<stem>.csv   stand-in
        ├── data_EDM-orig_IMG/<stem>.pdf   stand-in
        ├── data_EDM-orig_MID/<stem>.mid   stand-in
        ├── data_META/<stem>.json          copied
        ├── data_SCORE_CSV/<stem>.csv      copied
        ├── data_SCORE_IMG/<stem>.pdf      copied
        ├── data_SCORE_MID/<stem>.mid      copied
        ├── data_SCORE_SIB/<stem>.sib      copied
        └── data_SCORE_XML/<stem>.xml      stand-in

| Theme | Movement | Recording | Chosen for |
|---|---|---|---|
| `MTD0807_Beethoven_Op002No1-01` | Piano Sonata Op. 2 No. 1, I | Brendel | two themes of one movement; a piano theme; a triplet (`6.66667` is `20/3` quarters) |
| `MTD0808_Beethoven_Op002No1-01` | the same | the same track | the second theme of that movement |
| `MTD1044_Beethoven_Op055-02` | Symphony No. 3, II | Abbado | an orchestra theme; sixths of a quarter (`3.16667` is `19/6`) |
| `MTD1080_Beethoven_Op067-04` | Symphony No. 5, IV | Abbado | an orchestra theme; thirds of a quarter; `StartTime` written with two decimals (`01:00.75`); `MidiTransposition` 5 |

The four themes were also chosen among those whose score encoding
(`data_SCORE_MID`) and corrected EDM encoding (`data_EDM-corr_MID`) hold the
same notes: the same onsets, ends and pitches at 480 ticks per quarter. The
stand-ins below rely on it.

## Rebuilding the zip

    python data/mtd/make_sample.py /path/to/MTD_1.0.0.zip

`make_sample.py` (Python 3.10+, mido) reads the MTD archive in place and
writes `MTD_sample.zip` beside itself. The result is byte-identical on every
run (sorted members, fixed timestamps and attributes); a copied member keeps
its timestamp in the MTD archive, a stand-in and every folder entry carry
2026-11-26. `--check` compares each stand-in with MTD's own file of the
same theme, read in place, and prints the differences recorded below.

## Why stand-ins

MTD's `LICENSE` puts only `data_ALIGNMENT`, `data_META`, `data_SCORE_CSV`,
`data_SCORE_IMG`, `data_SCORE_MID` and `data_SCORE_SIB` (with the archive's
README, demo notebook and environment file) under the Creative Commons
Attribution 4.0 International License. `data_AUDIO`, `data_SCORE_XML` and
the `data_EDM-*` folders are not licensed. This corpus is published openly,
so it holds no file of those folders: each is replaced by a stand-in that
`make_sample.py` writes from the licensed files of the same theme only.
`MtdLoader` requires all sixteen files of a theme, and reads the MIDI files
(notes, end of track) and the MusicXML file (its bars' lengths); the other
files it names without parsing them. The stand-ins are shaped so that the
loader reads from them what it reads from MTD's own files.

## What is copied

Byte for byte from `MTD_1.0.0.zip`: the six licensed files of each theme
(`data_ALIGNMENT`, `data_META`, `data_SCORE_CSV`, `data_SCORE_IMG`,
`data_SCORE_MID`, `data_SCORE_SIB`) and the archive's `LICENSE`.

## The stand-ins, and how each is made

All MIDI stand-ins take the notes of the theme's `data_SCORE_MID` file, its
key signature, and its meter (the last time signature it states; a first,
shorter one is its pickup).

- **`data_EDM-orig_MID`**: type 0 at 480 ticks per quarter; the theme's time
  and key signature, tempo 500,000 µs per quarter (120 bpm), the notes at
  velocity 60, each ended by a note-on of velocity 0; the track ends at the
  end of the last note.
- **`data_EDM-corr_MID`**: type 1 at 480 ticks per quarter; a meta track
  (tempo 1,000,000 µs per quarter, i.e. 60 bpm, the time and key signature,
  ending at tick 1) and a note track (a program change, the notes at
  velocity 60, ending one tick after the last note). Messages at one tick are
  ordered by pitch, a note's end before an onset of the same pitch.
- **`data_EDM-alig_MID`**: shaped as EDM-corr; each note's onset and end
  are mapped through the alignment rows, linearly between the two rows
  around it, as MTD's paper describes EDM-alig. The second a position maps to
  is a quarter of this 60 bpm file, its tick the nearest at 480 per quarter
  (a half rounds up), so a note at an aligned onset starts at its row's
  second.
- **`data_EDM-orig_CSV`, `data_EDM-corr_CSV`, `data_EDM-alig_CSV`**: the
  notes of the stand-in MIDI file of the same encoding, at its tempo:
  `Start;Duration;Pitch` in seconds, a tick's second
  `tick * (seconds_per_quarter / 480)`, the duration the end's second minus
  the onset's, each written as Python writes a float; the header quoted
  (`"Start";"Duration";"Pitch"`) but in EDM-alig, as MTD writes them.
- **`data_SCORE_XML`**: a minimal MusicXML 3.0 file (one part, divisions
  480, key, time and clef in the first bar), the theme's notes from
  `data_SCORE_MID` in whole bars of its meter, the pickup as a bar of its
  own length marked `implicit="yes"`. A note lasts until the next onset, or
  until one tick after its MIDI end where a rest follows and at the end
  (Sibelius exports every note one tick short); the last bar is filled with
  a rest. So the file ends at the end of its last bar: in all four themes
  after the SCORE MIDI file's end of track, as in MTD (the loader's
  "participation child" case, which MTD shows in 1,246 themes).
- **`data_AUDIO`**: silence, mono, 8,000 Hz, 16 bit, exactly
  `EndTime − StartTime` of `data_META` long (2.8, 4.5, 7.9 and 5.55 seconds).
- **`data_EDM-orig_IMG`, `data_EDM-corr_IMG`**: a valid one-page PDF
  stating which file it stands in for and that it is not MTD's file.

## How the stand-ins compare with MTD's own files

Checked with `make_sample.py --check` against `MTD_1.0.0.zip`, and with
`MtdLoader` reading these four themes from this zip and from the MTD
archive: the 67 timelines (lengths, the children through which a longer
member takes part, the notes with their onsets, pitches and velocities)
and the 64 claims are equal.

- `data_EDM-orig_MID`, `data_EDM-corr_MID`, `data_EDM-alig_MID`, and
  `data_EDM-orig_CSV`, `data_EDM-corr_CSV`: **byte for byte equal to MTD's
  own files** in all four themes. They are written from the licensed SCORE
  MIDI file and alignment only, by the rules above; that they come out equal
  shows that the rules are MTD's.
- `data_EDM-alig_CSV`: the pitches, and the onsets in seconds within about a
  millisecond (by at most 0.00104 s; durations by at most 0.00167 s). MTD
  writes this note list from the alignment's unrounded seconds (MTD0807's
  third-of-a-triplet onset at `2.2040087100258`), the stand-in from its MIDI
  file's ticks (`1058 / 480`, `2.2041666666666666`).
- `data_SCORE_XML`: the same length as the loader reads it (9, 17, 6 and 17
  quarters, against SCORE MIDI ends of track of 8, 16, 5 and 16) and the
  same pitches in the same order, except in MTD1044, whose MusicXML file
  writes the G5 at quarter 2 (1 1/6 quarters long) as two tied notes and the
  stand-in as one note. Not Sibelius's export otherwise: no layout, no note
  types, beams or tuplet marks, and spelling by the key (flats in a flat key).
- `data_AUDIO`: the same length in seconds; MTD's excerpts are stereo at
  44,100 Hz, and hold the recording.
- `data_EDM-orig_IMG`, `data_EDM-corr_IMG`: not MTD's engraving.

## Credit and licence

Frank Zalkow, Stefan Balke, Vlora Arifi-Müller and Meinard Müller: MTD: A
Multimodal Dataset of Musical Themes for MIR Research. *Transactions of the
International Society for Music Information Retrieval* 3(1), 2020,
<https://doi.org/10.5334/tismir.68>. Website:
<https://www.audiolabs-erlangen.de/resources/MIR/MTD>.

The folders `data_ALIGNMENT`, `data_META`, `data_SCORE_CSV`,
`data_SCORE_IMG`, `data_SCORE_MID` and `data_SCORE_SIB` of the MTD are
licensed under the Creative Commons Attribution 4.0 International License
(`LICENSE` in the archive, copied unchanged). Copyright (c) 2020 Frank
Zalkow, Stefan Balke, Vlora Arifi-Müller and Meinard Müller, International
Audio Laboratories Erlangen. The stand-ins are adaptations of those licensed
files, under the same licence.
