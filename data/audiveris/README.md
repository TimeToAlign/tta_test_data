# Audiveris: Chaminade, Sérénade op. 29

An Audiveris book of one printed piano piece: what the optical music
recognition program [Audiveris](https://github.com/Audiveris/audiveris) found
on a public-domain scan, read by `AudiverisLoader` (notes and measures) and
`AudiverisLayoutLoader` (pages, systems and measure areas).

| File | Content |
|---|---|
| `IMSLP226462.omr` | The Audiveris book, a ZIP archive: `book.xml` lists the eight scanned pages (sheets) and the recognition steps each one went through; `sheet#N/sheet#N.xml` holds what was recognised on sheet N; `sheet#N/BINARY.png` is the binarised page image (3504 × 4961 pixels). |
| `IMSLP226462.xml` | The MusicXML file Audiveris exported from the same book (sheets 3–7), kept as a comparison for the loader's notes. |

## The work and the edition

- **Work:** Cécile Chaminade (1857–1944), *Sérénade* in D major, op. 29, for
  piano; first published in 1884 (Paris: Enoch frères et Costallat).
- **Edition scanned:** New York: G. Schirmer, 1892, plate 10179; revised and
  fingered by William Scharfenberg (1819–1895). Eight pages: cover, blank
  page, the music on printed pages 3–7, publisher's advertisement.
- **Scan:** IMSLP file #226462, on the IMSLP work page
  <https://imslp.org/wiki/S%C3%A9r%C3%A9nade%2C_Op.29_(Chaminade%2C_C%C3%A9cile)>,
  contributed by Aldona Jones as part of IMSLP's Sibley Mirroring Project
  (scans of the Sibley Music Library, Eastman School of Music, University of
  Rochester, made available through the Internet Archive; source file
  `SIBLEY1802.19362.db0b-39087012739290score`).

## The recognition

Audiveris 5.11.0 (build `9e1e55cd2746037d059345881c53e6a6754bffbd`), run in
batch mode on 2026-11-27 on a TIFF of the scan. The book records the input
path of that run (`C:\dump\Chaminade\Op029\audiveris\_tmp_prep\…`); the
MusicXML file states its encoding date and the software (Audiveris 5.11.0,
ProxyMusic 4.0.3).

| Sheet | Content | Recognised |
|---|---|---|
| 1 | cover | no (`invalid`) |
| 2 | blank | no (`invalid`) |
| 3–7 | the Sérénade, printed pages 3–7 | yes: 4, 5, 5, 5, 5 systems; 20, 20, 22, 22, 27 measures |
| 8 | publisher's advertisement | no (`invalid`) |

Chosen for: sheets Audiveris could not read next to sheets it did; measures
whose recognised durations differ from the time signature (21 of 111);
lower staves without a recognised clef or key on sheet 4; ten head chords
placed in no voice; a final system whose seven measures are complete while
their recognised durations are not.

## Credit and licence

The scanned edition is in the public domain, as IMSLP marks it; the files
here, derived from the scan by Audiveris, are shared on the same terms.
Credit: Cécile Chaminade (composer), William Scharfenberg (editor),
G. Schirmer (publisher), the Sibley Music Library of the Eastman School of
Music and the Internet Archive (scan), Aldona Jones and IMSLP (upload,
<https://imslp.org>). Audiveris is by Hervé Bitteur and contributors, licensed
under the GNU Affero General Public License v3.0
(<https://github.com/Audiveris/audiveris>); its program is not part of this
corpus.
