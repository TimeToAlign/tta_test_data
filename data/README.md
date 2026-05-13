# Test-data corpora

The contents of this directory are **not tracked in git**. They are downloaded
on demand by `timetoalign.testdata` (a thin wrapper around
[pooch](https://www.fatiando.org/pooch/)) from a release of the
[`tta_test_data`](https://github.com/johentsch/tta_test_data) repository.

## How it works

Each top-level subdirectory of this folder corresponds to one `.tar.gz`
archive in the test-data release. The first time a test or notebook calls
`ensure_data("<name>")`, the matching archive is downloaded, its SHA256 is
verified, and its contents are extracted in place. A sentinel
`.tta_testdata_hash` file is written so subsequent runs skip the re-extract.

The cached `.tar.gz` archives live in pooch's standard cache directory
(`%LOCALAPPDATA%\timetoalign-testdata` on Windows,
`~/.cache/timetoalign-testdata` on Linux,
`~/Library/Caches/timetoalign-testdata` on macOS). Override with the
`TTA_TESTDATA_CACHE` environment variable. Override the extraction location
with `TTA_TESTDATA_DIR`.

## Available corpora

| Name | Contents |
|------|----------|
| `audio` | Audio files used for `AudioLoader`/`BeatGrid` how-tos. |
| `audiolabs_omr` | AudioLabs OMR JSON exports (Wagner WWV086). |
| `fixtures` | Synthetic fixtures (corrupt files, ATON minimals, .lab samples). |
| `hendrix` | TiLiA hierarchy timelines for the *All Along the Watchtower* genesis study. |
| `midi` | Performance and score MIDI specimens. |
| `performance_precision` | Performance-precision benchmark inputs. |
| `score` | Score corpora — Beethoven WoO 71, Op. 18 multimodal, Bruckner 5, Couperin, Rachmaninoff, Wagner, *Out of the Flow* experience. The big one (~750 MB extracted). |
| `supra` | SUPRA piano-roll annotations and audio. |
| `tabular` | CSV/TSV samples for tabular loaders. |
| `target_flows` | Reference flow CSVs used by the score-parsing matrix. |
| `thoresen` | Lasse Thoresen *Sound-Objects* / *Form-Building Patterns* figures. |
| `vienna_1x22` | Vienna 1x22 corpus — Chopin Op. 10 No. 3, 22 performances. |

The canonical list (with SHA256 digests) is `REGISTRY` in
`timetoalign/testdata/__init__.py`.

## Fetching from code

```python
from timetoalign.testdata import ensure_data

DATA_DIR = ensure_data("vienna_1x22")            # single corpus
score_dir, midi_dir = ensure_data("score", "midi")  # multiple
```

## Publishing a new test-data release

1. Modify the corpora under `tests/data/<name>/` locally (during development
   they exist as extracted files even though git ignores them).
2. From the `timetoalign/` directory, rebuild the archives::

       python scripts/package_testdata.py

   The script prints a `REGISTRY = { ... }` block.
3. Create a GitHub release in `johentsch/tta_test_data` and upload the
   `dist/testdata/*.tar.gz` files as assets, e.g. via `gh`::

       gh release create testdata-vN dist/testdata/*.tar.gz \
           --repo johentsch/tta_test_data \
           --title "Test data vN"

4. Bump `RELEASE_TAG` and paste the new `REGISTRY` in
   `timetoalign/testdata/__init__.py`.
