# 이번 후보 전용 재현 스크립트

Workspace root에서 기존 `.venv/bin/python`으로 실행한다. 다운로드는 인터넷 접근이 필요하다.
원본 파일이 이미 있으면 Poly Haven 다운로드 스크립트는 크기·MD5를 검사하고 재사용한다.
그 외 생성 단계는 해당 감사의 파생 파일을 갱신하므로 보존된 다른 실행에 적용하지 않는다.

1. `fetch_mesh_candidates.py`: 목록에 고정된 6개 Poly Haven glTF 4K 및 별도 알파 파일 다운로드.
2. 공식 `http://graphics.berkeley.edu/resources/GarmentLibrary/garmentlibrary.zip`을 artifact root에 저장한다. ZIP 내 경로가 추출 루트 밖으로 나가지 않는지 확인한 뒤 `berkeley_garments/`로 추출하고 `zipfile.ZipFile.testzip()`이 `None`인지 확인한다. 원본 크기는 manifest 참조.
3. `https://storage.googleapis.com/dm-meshgraphnets/flag_simple/meta.json`을 artifact root의 `flag_meta.txt`로 저장한다.
4. `fetch_flag_sample.py` → `parse_flag_sample.py`: 검증 분할의 첫 레코드 다운로드·배열/OBJ 파생.
5. `audit_mesh_candidates.py` → `audit_garments.py`: 구조 수치와 TFRecord CRC32C 검사.
6. `finalize_audit.py`: 원본 인덱스 검사 추가·acquisition manifest 생성. Berkeley ZIP CRC 완료를 전제로 하므로 2번을 생략하지 않는다.
7. `mesh_previews.py`, `garment_previews.py`: 구조 그림 생성. `MPLCONFIGDIR=/tmp/wind_mesh_matplotlib` 사용 가능.

예시:

```bash
.venv/bin/python experiments/mesh_candidate_audit/evidence/scripts/audit_mesh_candidates.py
.venv/bin/python experiments/mesh_candidate_audit/evidence/scripts/audit_garments.py
.venv/bin/python experiments/mesh_candidate_audit/evidence/scripts/finalize_audit.py
```

NumPy·SciPy·trimesh·Pillow·matplotlib가 필요하다. 주 환경 패키지는 설치·변경하지 않았다.
스크립트의 SHA256은 [sha256.json](sha256.json), 검사 환경 버전은 상위 manifest에 있다.
구조 검사 수치는 물리 솔버의 수렴이나 렌더러 호환성 통과 판정이 아니다.
