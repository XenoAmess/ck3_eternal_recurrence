# kaishek-ck3-11906-profile

Version-pinned CK3 1.19.0.6 profile. Build fingerprint, directory schema,
scope links, and certified semantics are kept separate from the generic core.
`Ck3Profile11906` exposes both the validator-facing schema view and an
immutable `GameProfile`/`Profile` projection for IR and differential tooling.
The Phase 0 opcode table is syntax-level only: no entry is runtime-certified
until an exact-build differential artifact exists. The profile is not valid
for another executable hash without a new profile.
