# 2026-06-27 01 - Umbrella zip resume strategy after local assembly stall

## Observation

- Manual assembly resumed through `part_001`.
- Last observed output:
  - `experiments/M04_mesh_extraction/downloads/co3d/category_zips/umbrella.zip`
  - `6,237,350,151 bytes`
- The system became sluggish and disk active time reached 100%.

## Likely cause

Local assembly reads completed range parts and writes the final zip inside the same WSL VHDX. This can produce heavy read/write amplification and VHDX growth pressure on the Windows host drive.

## Safer continuation

Prefer HTTP resume from the current contiguous prefix instead of local part assembly:

```bash
./experiments/M04_mesh_extraction/scripts/run_umbrella_wget_resume_visible.sh
```

This uses `wget -c` to request only the remaining bytes from the server and append them to the current `umbrella.zip`.

Keep `umbrella.zip.parts/` until the final zip passes:

```bash
unzip -tq experiments/M04_mesh_extraction/downloads/co3d/category_zips/umbrella.zip
```

## Verification after resume

- `wget -c` resume completed successfully at `2026-06-27 00:42:19 KST`.
- Final archive size:
  - `41,944,422,600 bytes`
- `zipinfo -t` summary:
  - `196,513 files`
  - `42,383,010,972 bytes` uncompressed
  - `41,906,971,458 bytes` compressed
- `unzip -tq` result:
  - `No errors detected in compressed data`

Expected extraction path was checked:

```text
experiments/M04_mesh_extraction/raw/co3d/umbrella
```

At verification time, that directory was not present. `raw/co3d` still contained only `kite`, so umbrella extraction either has not been run to the expected experiment path or was extracted elsewhere.
