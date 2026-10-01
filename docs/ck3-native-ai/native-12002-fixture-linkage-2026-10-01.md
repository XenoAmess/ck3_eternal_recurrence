# CK3 1.20.0.2 fixture-only linkage repair

The authoritative native bridge CMake graph omitted `src`/`research` includes
from its automatically discovered 1.20 fixtures and omitted shared helper
implementations when their corresponding private live features were disabled.
The C1–C4 default builds demonstrated compile/link failures. The production
DLL/injector from C4 and its full-build RED are preserved; their separate
[ordinary-player qualification](core-native-c4-qualified-scope-2026-10-01.md)
remains the consuming project's bootstrap scope.

This repair changes only `BUILD_TESTING`: a static fixture support library
contains the existing shared readers, planner-open/start helpers and hosted
identity reader. Seven specific fixture targets link it. Discovered fixtures
receive the required source/research include directories. No private production
feature is enabled and the production DLL does not link this test archive.

Validation configured the actual candidate default CMake graph in `C:\cn120f`
and compiled its support archive. The generated Ninja graph confirms all seven
intended fixture links and the absent production dependency. A separate MSVC
Release fixture project in `C:\cn120e` imports the unchanged C4 runtime library
and compiles the same seven fixture sources and helpers from frozen C4 source.
These CTests passed:

| Fixture | Result |
| --- | --- |
| `xar_ck3_12002_activity_feast_costs_test` | PASS |
| `xar_ck3_12002_activity_feast_guest_rule_test` | PASS |
| `xar_ck3_12002_activity_feast_guest_wire_test` | PASS |
| `xar_ck3_12002_activity_feast_planner_open_v1_test` | PASS |
| `xar_ck3_12002_activity_feast_start_test` | PASS |
| `xar_ck3_12002_activity_hosted_identity_test` | PASS |
| `xar_ck3_12002_feast_guests_test` | PASS |

The qualification receipt is
`_runtime/native-fixture-link-repair-20261001/qualification-04.json`, SHA-256
`1c49641a92dd1e311d02e28043db2cd656b93b42fe9e76391f94f276645460af`.
It binds candidate CMake, actual graph/support build, imported runtime library,
independent fixture project, each test executable and result log. The test
command is `ctest --test-dir C:\cn120e --output-on-failure`; the support build
is `cmake --build C:\cn120f --target xar_ck3_12002_feast_fixture_support`.
Both use the installed Visual Studio 18 MSVC environment and its CMake tools.
The frozen runtime library SHA-256 is
`427c60d7b1a8797a82858cc7754202bec67a2a6bd73a6212a274b021840b7c84`.
All 2,743 C4 input files were reread unchanged. Original and immutable-copy
DLL/injector hashes still match their C4 qualification. Production artifacts
were not rebuilt. `open_kaishek` preflight is not applicable to native MSVC
include/link dependency resolution; no CK3 script runtime subset is involved.

The first three independent attempts remain RED with their original logs.
They exposed a separate legacy transport dependency: the 1.20 feast wire and
outcome-value fixtures call a shared 1.19 serializer whose translation unit
also references 1.19 `ReadSnapshot`. Those two targets are outside this repair's
seven-target qualification. No stub, altered fixture assertion or enabled
private production flag was used to make them pass. The full default build
and complete native CTest set remain unqualified. A later package can isolate
the pure serializer or bind its full existing legacy support dependency.

No Steam, desktop, injected DLL session or running game was operated by this
package. The CMake change is owned here; consuming mod repositories need no
copy of this fixture infrastructure.
