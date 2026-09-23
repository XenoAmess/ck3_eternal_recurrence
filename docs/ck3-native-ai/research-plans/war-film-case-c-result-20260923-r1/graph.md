# CASE-C observed result graph

```mermaid
flowchart LR
    A[W day19 checkpoint / fresh CASE-C identity] -->|speed2 and resume| B[Existing W4 routes progress]
    B -.->|No in_combat publication in 68 checked snapshots| C[Actual CombatID: unbound]
    B -->|date 53145504| D[Pending interaction 16777352]
    D -->|pause-map and fresh paused readback| E[Stop at CASE-C day30]
    C -.->|not entered| F[Optional one-battle terminal]
```

Solid edges reflect this window's official readbacks. Dashed edges remain unknown or not entered. The graph does not infer that no short battle occurred between samples. [readback.json](readback.json) contains exact source paths, hashes and the 68 sampled snapshot references. The checked preparation plan remains [r2](../war-film-case-c-20260923-r2/plan.json).
