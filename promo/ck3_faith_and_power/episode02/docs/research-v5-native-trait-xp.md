# Exact 1.20.0.4 trait XP: offline native semantics

Machine: 4-8e1c2f1861. Observed UTC: 2026-10-21T19:59:37.106880+00:00. EXE SHA256: 98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518. No game/provider call or live qualification.

Raw scale is 100000. Positive base XP uses pilgrim_xp_gain_mult and trait_track_pilgrim_xp_gain_mult. Negative base XP uses their xp_loss_mult counterparts. The effective values add to one before a single fixed-point multiplication:

    factor = 100000 + trait_modifier_raw + track_modifier_raw
    delta = trunc_toward_zero(base_raw * factor / 100000)
    new_xp_raw = clamp(old_xp_raw + delta, 0, 10000000)

Zero base does not write. Missing modifier IDs contribute zero. The factor is not clamped here; negative factors can reverse a delta. Arbitrary huge signed64 overflow behavior is outside the claim.

Registration 5D4B80 selects factory 2D2AA00, whose effect vtable selects executor 2D29CF0. It calls gain/loss helper 28BAF50, clamps to 0..100 XP, writes the slot, then recomputes level. Key builder 30E7B40 formats %s_xp_gain_mult / %s_xp_loss_mult. Track construction prefixes trait_track_. Getter 23036E0 fetches those two IDs; no third generic XP modifier is read by this helper.

Native fold 30E49D0 merges the root and every qualifying threshold block. Accumulator 2303100 adds matching IDs. Source parser/postload normalization remains unclosed, so this does not yet justify a net tier-value sum. add_trait initialization, missing-limit else_if defaults, and complete source activation/stacking remain unknown.

Adjacent JSON contains actual body hashes, exact EXE/tool identity, bounded instruction windows, and corrections to exploratory locator windows. The cap and formula are newly established on this exact .4 EXE; old 1.19 evidence is not reused as current qualification.
