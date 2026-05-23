# tta_test_data

Test corpora for the [Time To Align!](https://github.com/TimeToAlign/timetoalign)
library. Consumed by `timetoalign.testdata` (a thin pooch-based fetcher) in
the main repository.

## Layout

```
data/
├── audio/                  Audio specimens for AudioLoader/BeatGrid examples
├── audiolabs_omr/          AudioLabs OMR JSON exports (Wagner WWV086)
├── fixtures/               Synthetic fixtures (corrupt files, ATON, .lab)
├── hendrix/                TiLiA hierarchy timelines for the Watchtower genesis study
├── midi/                   Performance + score MIDI specimens
├── performance_precision/  Performance-precision benchmark inputs
├── score/                  Score corpora (Beethoven, Bruckner, Couperin, Rachmaninoff, Wagner, …)
├── supra/                  SUPRA piano-roll annotations + audio
├── tabular/                CSV/TSV samples for tabular loaders
├── target_flows/           Reference flow CSVs for the score-parsing matrix
├── thoresen/               Lasse Thoresen Sound-Objects / Form-Building Patterns figures
└── vienna_1x22/            Vienna 1x22 — Chopin Op. 10 No. 3, 22 performances
```

Add new corpora as additional top-level subdirectories of `data/` — the
packaging step picks them up automatically.

## Publishing a release

The consuming library fetches `<name>.tar.gz` release assets, not the raw
`data/` tree. Pushing a tag of the form `testdata-vN` triggers
[`.github/workflows/release.yml`](./.github/workflows/release.yml), which:

1. Tarballs each top-level subdirectory of `data/` into `dist/<name>.tar.gz`.
2. Computes SHA256 digests.
3. Creates a GitHub release with the tarballs as assets and the registry
   block in the release notes.

```bash
git add data/<name>/<new-files>
git commit -m "add <name> corpus"
git push
git tag testdata-v2
git push origin testdata-v2     # CI publishes the release
```

After the release is up, copy the `REGISTRY = {...}` block from the release
notes into `timetoalign/testdata/__init__.py` and bump `RELEASE_TAG`.

### Caveat: confirm the workflow actually queued

Tag-only `on: push: tags:` triggers occasionally get dropped by GitHub
Actions — the tag lands on the remote, but no workflow run is queued and
no release is published. Always verify after pushing the tag:

```bash
gh run list --workflow=release.yml --limit 3
# or:
gh api repos/TimeToAlign/tta_test_data/actions/runs --jq '.total_count'
```

If no new run appears within ~30 seconds, delete and re-push the tag to
re-fire the event:

```bash
git push origin :refs/tags/testdata-vN
git push origin testdata-vN
```

Do not bump `RELEASE_TAG` / `REGISTRY` in the consumer until the run has
completed and the release page lists the new `.tar.gz` assets.

## Building locally

```bash
python scripts/package.py
```

Outputs to `dist/` and prints the same `REGISTRY` block CI would emit. Useful
for verifying changes before tagging.
