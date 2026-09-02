# Phase-two loader callback RTTI owner and return lifetime (2026-09-02)

This bounded package binds the first paused runtime vptr to one exact-build
MSVC RTTI owner, then uses that closed owner contract for one separately
bounded callback entry/return observation. It does not repeat the existing
loader timeout or change the public bridge.

## Exact-build RTTI owner

The reproducible read-only extractor
`extract_phase2_loader_callback_runtime_owner.py` follows the absolute
CompleteObjectLocator pointer at runtime vtable RVA `0x408A450 - 8`. On CK3
`1.19.0.6` (EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`)
it closes this unique chain:

- CompleteObjectLocator RVA `0x45BD3B0`, signature `1`, self RVA matching;
- TypeDescriptor RVA `0x514FE60`;
- RTTI name `.?AV?$_Func_impl_no_alloc@P6AXXZX$$V@std@@`;
- undecorated owner
  `class std::_Func_impl_no_alloc<void (__cdecl*)(void),void>`;
- two expected hierarchy entries: that concrete wrapper and
  `std::_Func_base<void>`;
- slot-2 target RVA `0x947BD0`, bytes `48 FF 61 08`, decoded as
  `jmp qword ptr [rcx+0x08]`.

Therefore this runtime object is a no-allocation `std::function<void()>`
implementation wrapping a plain `void (__cdecl*)(void)` function pointer at
`receiver+0x08`. The extractor artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\runtime-owner-extract.json`,
SHA-256
`1EFA4CA63C955EB03FAEBCE66FEDCCD1AF0CBE97497D1FA22594825C23C05A10`.
No process was started for this step.

## One entry/return observation

The paired `open_kaishek` preflight used main
`17caa288eb980aab0b652358e9e94a9901131619`; its artifact SHA-256 is
`A8CEBA9DB43ADFEA5E7AA1E851C00FBCA55D07BADBAEAD251CCBA6116135586E`.
It retains the known full-root schema-only validator RED and is not CK3 live
evidence.

The single private debug run then stopped at callback call RVA `0x3B9AB90`,
read the wrapper's concrete callback, resumed the exact call, and stopped at
continuation RVA `0x3B9AB93`. It observed:

- the same OS thread `34296` at entry and return;
- runtime vtable RVA `0x408A450` and slot-2 target RVA `0x947BD0`, matching
  the closed owner contract;
- concrete callback RVA `0x2045330` at `receiver+0x08`;
- `node+0x88`, receiver vptr, and concrete callback pointer unchanged at the
  immediate post-return continuation;
- both one-shot breakpoint bytes restored.

The capture took 14.834 seconds and is retained at
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\callback-entry-return-capture.json`,
SHA-256
`88906E06EE88A910E8A9D1C2E190CC29EB6624DABD52B6C10140A722F2F64919`.

The capture's semantic fields close one synchronous entry/return and
immediate wrapper-lifetime observation. Its top-level result remains
`RED` because the utility checked the process handle before closing its
kill-on-close Job and recorded `cleanup-unproven`. An independent immediate
inventory found PID `23768` absent and zero CK3 processes; its SHA-256 is
`EA9A9BD3275D1F7418AAAD4983CAE333D10D8A826E0B507CFEB1E47148238456`.
The utility now rechecks after closing the Job, but no second CK3 run was made.

## Boundary and next entry

Phase two remains **native-readiness RED + not-live**. This one invocation
does not identify the business/source-file owner of concrete callback RVA
`0x2045330`, generalize to later loader nodes, or prove seed readiness. The
next bounded entry is either a static constructor/caller binding for
`0x2045330` or a separately authorized observation of the later stalled
node's callback identity. Do not repeat the `database_callback_stall` timeout
and do not widen the public bridge/readiness contract.
