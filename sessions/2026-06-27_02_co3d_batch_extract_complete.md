# 2026-06-27 02 - CO3D batch extraction complete

## Summary

Completed CO3D category extraction and cleanup for the M04 mesh extraction dataset.

## Categories Verified

| Category | Size | Sequences | Frame annotations | Files |
| --- | ---: | ---: | ---: | ---: |
| `broccoli` | `28G` | `405` | `39,148` | `157,001` |
| `frisbee` | `8.6G` | `133` | `12,911` | `51,782` |
| `kite` | `12G` | `163` | `16,358` | `65,600` |
| `plant` | `51G` | `574` | `56,936` | `228,323` |
| `teddybear` | `50G` | `749` | `72,865` | `292,215` |
| `toyplane` | `18G` | `250` | `24,446` | `98,039` |
| `umbrella` | `40G` | `503` | `48,372` | `193,997` |

## Verification Notes

- `umbrella.zip` was completed through `wget -c` resume after local part assembly caused heavy VHDX I/O.
- `umbrella.zip` final size matched `41,944,422,600 bytes`.
- `unzip -tq` reported no errors for `umbrella.zip`.
- Each category was extracted with:

```bash
ionice -c2 -n7 nice -n 10 unzip -q -n <category.zip> -d experiments/M04_mesh_extraction/raw/co3d
```

- Each category metadata was loaded from `sequence_annotations.jgz` and `frame_annotations.jgz`.
- Zip archives were deleted after successful extraction and metadata checks.
- `plant` extraction was interrupted by a VSCode reload and safely resumed with `unzip -n`.

## Final State

Raw dataset root:

```text
experiments/M04_mesh_extraction/raw/co3d
```

Extracted categories:

```text
broccoli
frisbee
kite
plant
teddybear
toyplane
umbrella
```

Final raw size:

```text
205G
```

Remaining files under `downloads/co3d/category_zips`:

```text
umbrella_assemble_latest.log
umbrella_wget_resume_latest.log
```
