# Phase 2 producer-identity live terminal (2026-09-02)

## Frozen candidate

- Exact source commit: `da4378774850184cd9771616bda90e279301d6fe`.
- Clean source ZIP: `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\producer-freeze-da43787\source-da43787-clean.zip`, SHA-256 `7411C9136F4A3946E83585D2A628DDDAB0D51B79012EAEC77B072635FC2E043A`.
- Acceptance manifest: `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\producer-freeze-da43787\producer-identity-observer-no-launch-manifest.json`, SHA-256 `4D882BF8B3C222B7932AABB506BD1A571E419EF274502C670F04C8CB2330A4C0`.
- Producer-only DLL SHA-256: `567B5C18DA5282539088273A23EDFB458529CF4B62C637BA5CD3F9E209C3DD3C`.
- Injector SHA-256: `2FAE7AA325F448E26348CFC6C093D8C4349F09EC9F2F66937D99E551E6AC6CC4`.
- The acceptance gate was enabled with `--list-domain-observer-gate` and the exact manifest. G2 private options remained off.

## Unique live result

The only CK3 launch used PID `62944`, starting at `2026-09-02T15:44:54.725020+00:00` and ending at `2026-09-02T15:45:09.809812+00:00`. The terminal result is typed `RED` with reason code `LegalConsentNotAuthorized`:

> Paradox legal/consent modal does not match the authorized document kinds.

The shared legal handler was authorized only for a Paradox User Agreement, EULA, Terms of Use, or an exact semantic equivalent. It performed zero clicks, accepted no optional consent, and stopped before loader observation. The isolated `telemetry_consent.json` remained `{"telemetry_consent_choice":"no_choice"}`. The post-stop marker hashes are:

- `account.json`: `BACF2F16616DB6B187F43E7A1096183765076AAA067D628ED4329E9164A27F38`.
- `telemetry_consent.json`: `957EB138EEF7AF1187EB7138ABA2E4648ECDD726ED130C7DCA4D90CFB7694211`.

Because the modal did not enter an authorized acceptance stage, the handler did not create an acceptance before/after screenshot pair or before/after marker pair. The legal evidence records this boundary; it must not be represented as a successful consent acceptance. The current handler also does not retain the rejected modal OCR rows or screenshot, so this artifact cannot identify the modal more narrowly without another separately authorized attempt.

The producer observer itself installed successfully (`installed=true`, `failure=0`), but both `0x3B9CFD2` and `0x3B9CFD7` entry counts are zero and `read_failure_count=0`. These zero counters mean only that the legal-policy stop occurred before the producer seam. They are not an observer failure and do not resolve producer task identity.

## Cleanup and invariants

Cleanup is `GREEN`: the supervisor and driver stopped, shutdown returned `ok=true`, `cleanup_proven=true`, `tree_gone=true`, the job contained zero processes, the global CK3 inventory was empty, and cleanup checks had no failures. The runner also records `driver_closed=true`, `runtime_unchanged=true`, and `clean_source_unchanged=true`. Source-tree manifests before and after are byte-identical, both SHA-256 `1C0103648E99D28119FA3DE17516A23A75B30E0715327387376D9D8D84B3E88F`.

No second CK3 launch is permitted for this candidate. A previous command rejected before launch because its pipe did not match the required run-unique 32-lowercase-hex form; that pre-launch RED is separately preserved at `Z:\p2r-producer-da43787-artifacts-prelaunch-red1` and is not counted as a live attempt.

## Evidence

All live evidence is under `Z:\p2r-producer-da43787-artifacts`:

| Artifact | SHA-256 |
|---|---|
| `runner-report.json` | `D663CCF6D2035EC3371FA55F688E36C9A7E2419166E6C4E5CFDE36A3CE2D6518` |
| `00_phase2_native_session_start.json` | `4D91CC146D4DCBE55F214CE7C00C8F948B8AFD7A4F3D94EC50F3439E925FD5BC` |
| `01_phase2_legal_consent.json` | `F8AB66E6C5FAB6642D3FE1262B3C36218D4D7994D485CEBBADDBF86F584055E9` |
| `09_phase2_native_session_cleanup.json` | `6B8D82759C8FD4B356DE6E4974DCE6977A306BB1783605C96D87C34C2F116AF7` |
| `list-domain-observer-gate.json` | `B37811B03999A818B9D5152058CE5EECBF2E8CB176FE1502AF9F22CADC5A5866` |
| `open_kaishek-preflight.json` | `EF49446AF7774FF5B5B1065AA2121430940CEF4A53A281E0F8DC46121B50429C` |
| `preflight.json` | `57DEFE731012BC842D09AD5AABD6CFE851609A83E39C195CD1F6A7BE24653B43` |
| `source-zip-manifest.json` | `7871F39120F9C7AC2FF7C5861CCE2AC162BD4237073DFDB34F89FD75BC70D391` |
| `phase2-producer-identity-observer-v1-postprocess.json` | `B910696575E5E67993C34C61DF04127234B8C746733682A4E2BA75C9D18394F0` |
| `terminal-evidence-index.json` | `3403D78C0C209FBF04538EA77B48CBA5999B7B00B471C16E889BF40CEF0AAC69` |

The terminal index is the concise entry point. The runner report remains authoritative for the exact session, observer heartbeat, source identity, external dependency hashes, traceback, and final cleanup record.
