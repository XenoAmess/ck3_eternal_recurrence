# Compatibility and provenance audit

## Upstream baseline

- Steam Workshop item: `3596263413`
- Public title: `Corruption & Trading under the Celestial government`
- Workshop content manifest: `5771315817866202773`
- Download result: authenticated Steam client `OK` on 2026-09-20
- Embedded upstream Git commit: `9faf3bc0c2f0e039df04cb462cf6642e44318a94`
- Upstream Git author/committer: `HydroWood <2242730098@qq.com>`
- Upstream history contains four commits and no remote, tag, `LICENSE`, `COPYING`, or README file.

The downloaded Workshop package included its `.git` directory. The maintained product does not
ship that directory; this document freezes the exact source identity instead.

## CK3 1.19.0.6 conflict classification

1. `common/activities/activity_types/feast.txt` was a stale full-file override. CK3 1.19 already
   handles `government_allows = barter` and `barter_goods` costs in the vanilla feast activity.
   Keeping the upstream file would remove current house-aspiration, accolade, free-feast,
   background, and cost-routing behavior. The maintained product therefore omits the override.
2. `gui/window_county_view.gui` changed one visibility expression but replaced the whole old
   county window. Against 1.19 it was 67 lines ahead and 159 lines behind, including missing
   building shortcuts and current special-building templates. The maintained product omits this
   presentation-only override so the current vanilla GUI remains authoritative.
3. The upstream `celestial_government` block lacked 1.19's
   `allow_as_base_for_baronies = no` and `allow_accolades = yes`, and used the removed
   `active_accolades` modifier instead of `accolades`. The maintained block is the exact 1.19
   vanilla definition plus one intentional rule: `barter = yes`.
4. The decision used `ai_check_interval = { months = 12 }`, while the current decision schema
   requires an integer month count. The maintained decision uses `ai_check_interval = 36` and
   removes the upstream one-day test cooldown in favor of a three-year policy cadence.
5. The English localization had no required leading spaces, and one event option/tool tip was
   hard-coded in Chinese. Both authoring languages now use the same namespaced key inventory.
6. Upstream public copy said the policy granted immediate gold, but the implementation only
   changed the tax obligation and applied trait modifiers. Maintained copy states the actual
   ongoing tax-diversion and barter-production contract; direct treasury withdrawal remains the
   separate vanilla `extract_gold_from_treasury` decision.

## Publication authorization gate

No redistribution license or explicit fork permission was present in the downloaded package.
On 2026-09-20, the repository owner explicitly attested in the Codex task conversation that they
had obtained the original author's permission to redistribute and publish this maintained fork,
and instructed the release to proceed on that basis. The permission artifact itself was not
available for attachment because the owner was away from it; it remains a documentation follow-up
and is not represented here as independently inspected. This dated owner attestation resolves the
project's publication-authorization gate for the 1.0.0 release workflow.
