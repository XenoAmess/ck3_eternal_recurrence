# M3 selected release source closure

This package publishes the already verified selected release components from M3 165/167/168/170. It adds a Java namespace and uses the repository's existing NativeTaskMemory contract. It does not add an execution platform, process attachment, POM dependency, or CI registration.

The nine production files are under src/main/java/org/xar/ck3/research/m3. The seven independent existing case/validation files are under src/test/java/org/xar/ck3/research/m3. The only source changes are package/import declarations and the following exact-width storage method names:

| Previous supplied-storage API | Existing shared API |
| --- | --- |
| RegistrationApi149.Memory | NativeTaskMemory |
| read64 | readPointer |
| read32 | readInt32 |
| write64 | writeInt64 |
| write32 | writeInt32 |

The closure reuses existing NativeTaskMemory, its retained/InGameIdlerEventDispatch.Memory parent, Free83Inputs, and Free83Candidate. No compiled dependency directory is required. M1 commit c5b816 is retained in the formal baseline; its government components are not dependencies of this release chain. The M7 RequestRetry4223b94 belongs to the separate allocation path. LoadSharedGetterC45df0 has a different source address and contract and cannot replace the retained AllocatorSelector165 getter for receiver+0x408.

ReleaseWrapper167 preserves the original scalar-facing port: inline rows returns receiver+8 before memory access, followed otherwise by the first dynamic selector call and fresh returned-object vptr/slot10 reads. BoundReleaseSelector167 only intercepts the explicitly supplied selector code identity. GlobalReleaseWrapper168 explicitly receives incomingRax and preserves it on the null-row path. BoundGlobalRelease168 is specific to the 855830 caller, where incomingRax is the selected returned receiver. Unselected targets are delegated to caller-owned typed ports; no native call is dispatched by these Java classes.

SelectedFreeEffects170 is a separate effect-only consumer. It returns unsupported outcomes for unselected targets, uses the current shared-memory heap value only on the selected nonzero path, and calls the existing Free83 implementation once. CALLEE_RETURNED means normal completion of the supplied Java port. It does not mean heap-free success or a Game action. This interface does not synthesize the scalar return of the native chain. In the controlled Native171 witness two mapper returns had different high32 RAX bits while producing the same32-bit cell; the existing Free83 void/int projection cannot restore those raw bits.

The existing Java cases are standalone main classes, not JUnit tests and not registered in Surefire or CI by this change. Their literal inputs and expected values are retained. This delivery prepares one source-only namespace closure compile from20 source files with Java21, -Xlint:all and -Werror; existing cases and Native witnesses are not rerun for this delivery. SOURCE-CLOSURE172.txt lists the exact repository-relative source files, including the four existing shared files. A worker can compile from repository root into its own output directory using that list; it must not treat the old D paths inside historical evidence as classpath dependencies. The separate STRICT-ACTUAL172.json receipt records whether and when that compile has actually run.

For a later explicitly required manual validation, the entry points are org.xar.ck3.research.m3.ReleaseValidation167 and GlobalReleaseValidation168, each requiring one caller-selected output directory, and FreeEffectsValidation170, which requires no arguments. This delivery does not execute them again or claim a new behavior pass from compilation.

The local D-only delivery retains unchanged historical evidence under portable-delivery172/evidence; those files are not part of this Git source publication: ACTUAL167 covers the first Java/controlled58B validation; ACTUAL168 includes the first controlled14B static validation; ACTUAL170 covers the effect-only Java consumer; ACTUAL171 covers the first controlled six-body163B static chain. The local D-only EVIDENCE-INDEX172.json records each original and exact hash. This Git publication includes the relative source list and first compile result, and requires no historical evidence file to compile. These prove finite owned fixtures, not a natural caller or current Game object. Natural CALL3F95DD0 ownership, dynamic concrete vptr production, bank+EF0/name72 production, full ABI/EH and Game execution remain unknown.

First namespace closure compile: 2026-10-31T16:05:23.236117Z to16:05:24.150847Z, exit0 in0.914726seconds. All20 explicit source files compiled with no binary classpath and preserved hashes. No existing cases or Native witnesses were executed again. The repository-relative result file is m3-selected-release-closure172-result.json in this docs directory.

The result's source hashes identify the exact D candidates used in that first compile. Formal adoption removed trailing spaces from two blank Java lines and restored two test files' original missing final newlines after patch packaging added them. Java execution tokens and algorithms are unchanged. A candidate physical hash is evidence of that compile input, rather than a requirement that the formatted Git blob have the same byte hash.
