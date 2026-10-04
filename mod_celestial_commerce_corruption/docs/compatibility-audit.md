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

## CK3 1.20.0.2 development migration on 2026-10-01

The current source government projection now uses the complete reviewed CK3 1.20.0.2
`celestial_government` definition plus the single `barter = yes` rule. It preserves the new
administrative mechanic, treasury development, estate/bureaucracy/budget flags, AI legend support
and grantable clergy governments. The vanilla obligations definition did not change and the
product obligations file remains byte-identical to its previous source baseline.

The builder and static gate freeze the native government semantic SHA-256 even without a local
game installation; installed-game comparisons additionally check the reviewed baseline. L0,
11 builder tests and the 22-file reproducibility check passed once. New-version runtime validation
is pending, the descriptor still declares the previously tested 1.19.0.6 version, and this work
does not update the public release or weaken old native-bridge contracts. Full input identities,
checks and evidence are recorded in
[the CK3 1.20.0.2 compatibility topic](../../docs/ck3-1.20.0.2-celestial-commerce-corruption-compatibility-2026-10-01.md).


## 2026-10-05：1.20.0.3 / 1.0.1 入库维护候选

状态：**DRAFT / NOT_PUBLISHED / .3 实机 PENDING**。候选 descriptor 为 `version="1.0.1"`、`supported_version="1.20.0.3"`；专用 static validator 同步精确 metadata 合同。这不改变本页旧 .2 实机、RED、getter 缺口或诊断事实，也不把旧证据外推为 .3。

相对上一公开维护版 1.0.0（tag `celestial-commerce-corruption-v1.0.0`，commit `dc91dc1f0a1abd733d274382833a0ab9b3cdb51f`），政府迁移保留完整原版 1.20 能力并只额外启用 barter。事件、四档特质、税率、obligations、九语本地化和素材没有玩法字节变化。既有 .2 政府语义签名在 .3 仍相同，原审阅和历史输出名保持原样；本轮不重新解释旧源证据。

全新 .3 前台输入、实际 policy loader、只读 preflight、最短 D0→D3 和真实生产决议/暂退出/三年冷却方案保存在 `C:/workspace/ck3-upgrade-20261005/ccc-12003-readiness-agent-01/`。这些均为输入准备，不是当次游戏验收。两条夹具 set-unused 和第二事件 typed getter 缺口须按本次实际日志/窗口判定，不能预先清零或声称修复。

发布草稿见 [1.0.1 changelog](../../docs/release-changelogs/celestial-commerce-corruption/1.0.1.md)。维护上传目标只 **3804807463**；正式 tag、.3 report、上传、精确 Change Notes 匿名回读、新缓存与 master commit/push 均待 Root 按实证完成后补录。

本次候选 metadata 的必要检查已经实际通过：专用 static、官方双构建、非 tag 22文件候选 build 和 exact verify 均 exit 0。验证报告 SHA `6f2763c9cf2633aa989f76bdf660f625a4b4246c472300b92ac31a138626f71d`，路径 `C:/workspace/ck3-upgrade-20261005/ccc-12003-readiness-agent-01/root-candidate-validation-05/report.json`。ZIP SHA `8c3a51bd1d7ab0911d09cb6543df9f26c6de5a370414fe127e4817034d8d8c03`；manifest 为 `git_tag=null` 的工作树候选，不是正式 tag release。相对已有 .2待测投影只有 descriptor 变化，其余21运行文件 exact。新 `inputs-06` 和 `plans-06` 准备当次 .3实机，旧输入与 RED历史继续保留。**.3 实机与发布仍 PENDING**。
