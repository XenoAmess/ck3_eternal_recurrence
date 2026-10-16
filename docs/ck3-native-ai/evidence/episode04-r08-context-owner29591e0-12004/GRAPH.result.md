# R08 context-owner candidate29591E0: actual source result

machine_id: desktop-3fevhd2-1c74096080. Static exact4 source only; no game action.

```mermaid
flowchart TD
 C[Character1C0 context C] --> A[C18 to C2C0 / C20 to C2C8 copies]
 A --> D[28A6535 to held28D6170 ID cleanup]
 D --> G{C byte1D8 nonzero?}
 G -->|yes; clearbyte beforecall| E[28A65BE to29591E0 C and localdescriptor]
 C --> I[C1E0 pointer / signedDWORD1EC count:4B FullID sequence]
 I --> E
 E --> L[Generationchecked registrylookup/fallback]
 L --> U[230F8E0 opaque call]
 U --> T{rawDWORD return85C equals50726F76?}
 T --> Q{postcallR10 plus48 DWORD64 signed lessorequal1?}
 Q --> B{candidate equals QWORD postcallR10plus338 plus620; byte8 nonzero?}
 B --> O[880340 localdescriptor and address oflocalcandidate; opaquecall]
 O --> X[Caller pointerlist;2468AC0; indexedoutput from entryRDX]
 C -. producerunknown .-> CD[C28 / C30]
 CD -. sourceconsumerknown; sameoccurrenceunbound .-> N[28A6D10 signed NET application]
 N -. militarycategory plus sameapplication plus payer plus triggerunknown .-> P[paid amount / payer / cadence NULL]
 X -. indexedoutput is not provedwallet .-> P
```

Only the snapshot copies are proved context writes here. The225B source has stack stores but no direct nonstack store; its two opaquecalls remain opaque. Exactly54 saved instructions span three genuine extents; both continuations explicitly CHAININFO to29591E0. All saved ordinary branches resolve within the225B union, ending RET29592C0. This does not expand callee/exception effects or infer runtime execution.

The1D8 gate is a raw source branch, not a proved business dirtyflag or payment trigger. A helper running later in this invocation cannot produce the already-completed earlier copies; cross-invocation effects remain unknown.
