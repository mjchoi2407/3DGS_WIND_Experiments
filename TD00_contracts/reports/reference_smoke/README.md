# Reference smoke evidence

이 폴더의 `run_manifest.json`, `td00_smoke_report.json`, `reference_complete.json`은 TD00 scaffold를 먼저 커밋한 뒤 clean-source smoke가 발행한다. 마지막 marker가 앞의 두 파일 hash와 일치할 때만 완전한 reference evidence로 인정한다. Generator는 내용이 다른 기존 reference를 자동으로 덮어쓰지 않는다.
