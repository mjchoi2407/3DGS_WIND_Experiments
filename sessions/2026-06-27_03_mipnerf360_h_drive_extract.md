# 2026-06-27 Mip-NeRF 360 H-drive extraction

## Context

The user has two Mip-NeRF 360 archives at the H drive root:

- `/mnt/h/360_v2.zip`
- `/mnt/h/360_extra_scenes.zip`

Only `bonsai`, `garden`, and `stump` are needed from `360_v2.zip`. All scenes from `360_extra_scenes.zip` were intended for use.

## Actions

- Extracted selected `360_v2.zip` scenes directly from `/mnt/h` into WSL:
  - `raw/mipnerf360/bonsai`
  - `raw/mipnerf360/garden`
  - `raw/mipnerf360/stump`
- Extracted `treehill` from `/mnt/h/360_extra_scenes.zip`.
- Attempted to extract and test `flowers` from `/mnt/h/360_extra_scenes.zip`.
- Quarantined the partial `flowers` extraction as `raw/mipnerf360/flowers_incomplete_from_corrupt_zip`.
- After the user redownloaded `/mnt/h/360_extra_scenes.zip`, tested and extracted `flowers/*` successfully.

## Verification

Usable scenes:

| Scene | Size | Files | Status |
| --- | ---: | ---: | --- |
| `bonsai` | `1.4G` | `1,172` | ready |
| `garden` | `2.9G` | `744` | ready |
| `stump` | `1.5G` | `504` | ready |
| `flowers` | `2.5G` | `696` | ready |
| `treehill` | `1.8G` | `568` | ready |

Old partial `flowers` extraction:

- Partial folder: `raw/mipnerf360/flowers_incomplete_from_corrupt_zip`
- Extracted files: `80`
- Size: `753M`
- Status: quarantined; do not use

The first archive copy failed with both `unzip` and Python `zipfile`, and the user confirmed that Windows-side extraction of the same archive also failed. The redownloaded archive passed:

```bash
unzip -tq /mnt/h/360_extra_scenes.zip 'flowers/*'
```

with:

```text
No errors detected in /mnt/h/360_extra_scenes.zip for the 703 files tested.
```

## Next steps

- Use `bonsai`, `garden`, `stump`, `flowers`, and `treehill` for Mip-NeRF 360 style scene tests.
- Remove `flowers_incomplete_from_corrupt_zip` later if the quarantined partial copy is no longer useful for debugging.
- For object-centric aerodynamic tests, continue prioritizing CO3D categories such as `kite`, `plant`, `teddybear`, `toyplane`, and `umbrella`.
