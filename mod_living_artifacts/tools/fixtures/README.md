# Historical threshold producer fixture

`threshold-result-v1-adapter.py.txt` preserves the exact producer source from
commit `5b1408fb3cc7b359eb5a43342861e8a521ab9d28`: 35,832 bytes, SHA-256
`863dfea6abd897a8efe2159f75717108f6b4afd8677e01fa44a6cc48b8c3e2e3`.

This is immutable test input, not a production module or a second implementation.
The persistent regression copies it into an isolated temporary source bundle,
runs the actual historical producer and retained verifier, and exercises the
current public verification consumer. Native frames, saves and close boundaries
in that test are authored fixtures and grant no CK3 acceptance credit.
