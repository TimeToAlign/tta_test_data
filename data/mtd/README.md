# Musical Theme Dataset: four themes

`MTD_sample.zip` holds four themes of the Musical Theme Dataset (MTD 1.0.0)
in the layout of the MTD archive, read in place by `MtdLoader`:

    MTD_sample.zip
    ├── LICENSE
    └── MTD
        ├── data_ALIGNMENT/<stem>.csv
        ├── data_EDM-corr_MID/<stem>.mid
        ├── data_META/<stem>.json
        └── data_SCORE_MID/<stem>.mid

| Theme | Movement | Recording | Chosen for |
|---|---|---|---|
| `MTD0807_Beethoven_Op002No1-01` | Piano Sonata Op. 2 No. 1, I | Brendel | two themes of one movement; a piano theme; a triplet (`6.66667` is `20/3` quarters) |
| `MTD0808_Beethoven_Op002No1-01` | the same | the same track | the second theme of that movement |
| `MTD1044_Beethoven_Op055-02` | Symphony No. 3, II | Abbado | an orchestra theme; sixths of a quarter (`3.16667` is `19/6`) |
| `MTD1080_Beethoven_Op067-04` | Symphony No. 5, IV | Abbado | an orchestra theme; thirds of a quarter; `StartTime` written with two decimals (`01:00.75`) |

## What is copied, and from where

`data_META`, `data_ALIGNMENT` and `data_SCORE_MID` are copied byte for byte
from `MTD_1.0.0.zip`, as is its `LICENSE`.

`data_EDM-corr_MID` holds **copies of the `data_SCORE_MID` files**, byte for
byte, not MTD's own `data_EDM-corr_MID` files. MTD's alignments count the
quarter notes of its corrected EDM encodings (`data_EDM-corr_MID`), which
MTD does not license; its score encodings (`data_SCORE_MID`) are licensed.
The four themes were chosen among those whose two encodings hold the same
notes (the same onsets, ends and pitches at 480 ticks per quarter), so the
licensed file stands for the other one without changing a note. The bytes
differ in MTD (the header, the tempo, controller messages), so the files
here are not MTD's EDM files.

## Credit and licence

Frank Zalkow, Stefan Balke, Vlora Arifi-Müller and Meinard Müller: MTD: A
Multimodal Dataset of Musical Themes for MIR Research. *Transactions of the
International Society for Music Information Retrieval* 3(1), 2020,
<https://doi.org/10.5334/tismir.68>. Website:
<https://www.audiolabs-erlangen.de/resources/MIR/MTD>.

The folders `data_ALIGNMENT`, `data_META` and `data_SCORE_MID` of the MTD are
licensed under the Creative Commons Attribution 4.0 International License
(`LICENSE` in the archive, copied unchanged); the files under
`data_EDM-corr_MID` here are copies of the `data_SCORE_MID` files under the
same licence. Copyright (c) 2020 Frank Zalkow, Stefan Balke, Vlora
Arifi-Müller and Meinard Müller, International Audio Laboratories Erlangen.
