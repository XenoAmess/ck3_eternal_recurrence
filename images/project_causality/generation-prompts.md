# 《project因果律》宣传视觉生成记录

## 生成环境

- 生成日期：2026-09-18
- 生成方式：OpenAI 内置图像生成
- 身份参考：`character/humanized_avatar_source.png`
- 原始身份参考 SHA-256：`31218C41C1756CC4641A70828B2C381E744C988B13FA1F376B73066E6564DF8A`
- 共同约束：单一人物；白发、红瞳、黑色高领斗篷、胸前红黑白旋纹徽记和青色幽焰不得改变；不生成文字、水印或伪造 UI。

## 透明人物锚点

第一步使用 `identity-preserve` 意图生成全身角色：

```text
Create a polished full-body anime character illustration of exactly the same character, suitable for compositing into title cards and motion graphics. Preserve the short fluffy white hair and exact fringe silhouette, vivid red eyes, pale complexion, calm serious expression, black high-collared cloak, the circular red-black-white spiral chest emblem, and cyan ghostly flames as the signature aura. Preserve the youthful androgynous identity and facial proportions. Full body fully visible from head to feet, neutral three-quarter hero pose, arms and hands naturally readable, centered with generous transparent padding. High-end clean anime key art, crisp controlled linework and subtle cel shading. Exactly one character; no text, watermark, frame, scenery, weapons, crowns, horns, wings or identity changes.
```

第二步使用 `background-extraction` 意图移除背景：

```text
Remove only the black and cyan gradient background, producing a genuinely transparent alpha background. Preserve exactly the complete character from head to boots, face and identity, white hair, red eyes, black cloak and outfit, circular red-black-white spiral chest emblem, pose, hands, proportions, lighting, and the cyan ghostly flame aura immediately surrounding the body. Preserve the full-body composition and padding. Use transparent pixels everywhere outside the character and retained flame aura, with clean anti-aliased edges and no dark matte halo. Do not crop, restyle, repaint the face, change the emblem, add scenery, text, watermark or a baked checkerboard.
```

输出：`character/humanized_avatar_anchor.png`。

## 片名主视觉

```text
Create a 16:9 cinematic title key art for a project about causal systems, CK3 worlds, automation, verification, and infinite evolution. Set it in a vast dark medieval-cosmic archive where parchment maps, subtle heraldic geometry, data constellations, and four luminous causal arcs converge into one coherent mechanism. Preserve the referenced character exactly. Place the character waist-up on the right third, looking calmly toward the viewer, with generous title-safe negative space across the left and center. Use premium anime cinematic key art, cyan flame rim light, restrained ember-gold highlights, deep black, cyan, old gold and small controlled red accents. No text, letters, numbers, watermark, UI screenshots, brand logos, extra characters or generic cyberpunk scenery.
```

输出：`promo/project_causality_key_art.png`。

## “咒”章节图

```text
Depict the referenced character as the calm guide presenting the visible player-facing creations of a CK3 content ecosystem. Place a dark medieval hall behind them, opening onto layered glimpses of dynastic maps, a ruler's life and death, a court, a restored realm, heraldry, contracts, blessings and curses, expressed as symbolic parchment windows and reflected scenes rather than fake readable game UI. Keep the character on the right third, upper body and one open hand visible, with clean dark negative space on the left for typography. Use premium anime cinematic illustration, warm ember-gold product visions contrasted with cyan flames. No text, watermark, fake UI, foreground characters, gore, weapons, crowns, horns, wings or identity changes.
```

输出：`promo/chapter_spell.png`。

## “术”章节图

```text
Depict the referenced character calmly operating a causal loom that turns authoritative documents into generated game content, typed observations, tests, evidence, and release artifacts. Use an immense archive-workshop combining parchment ledgers, precise mechanical rings, luminous data paths, clean abstract code blocks, game-state nodes, and a distant medieval world map. Show a clear left-to-right cause-and-effect flow without readable fake code or UI. Keep the character waist-up on the right third, one hand guiding thin cyan causal threads, and reserve the upper-left as dark title-safe space. Use premium anime cinematic concept art blended with elegant technical illustration. No text, watermark, screenshots, extra characters, hacker clichés, Matrix rain, excessive holograms or identity changes.
```

输出：`promo/chapter_method.png`。

## “道”章节图

```text
Depict the referenced character as a calm arbiter before a monumental archive where principle, evidence, test, and implementation are visibly ordered by causality. Use a dark hall of ivory stone tablets, parchment contracts, balanced scales, exact-build celestial instruments, and one restrained red failure thread returning into a newly illuminated document. Communicate documentation before tests, tests before code, true state above acknowledgements, and evidence levels without readable words. Keep the character upright and waist-up on the right third, one hand near a closed ledger, with quiet black-to-ivory title-safe space on the left. Use solemn premium anime cinematic illustration. No text, watermark, fake code, extra characters, courtroom clichés or identity changes.
```

输出：`promo/chapter_principle.png`。

## “辉煌愿景”章节图

```text
Depict the referenced character witnessing a complete self-evolving causal system: four enormous interlocking luminous loops continuously turn content creation, gameplay observation, decision and action, testing and verification, evidence and release back into better authoritative knowledge. Set it above a living medieval world map, with four harmonized orbital mechanisms made from parchment, heraldic geometry, precise instruments, abstract state nodes, evidence frames, and release artifacts. The loops converge into a radiant causal core and continue beyond the horizon, conveying an infinite automation flywheel rather than a finished static machine. Keep the character on the right third and broad title-safe space on the left. Use hopeful, immense and disciplined premium anime cinematic key art in black, cyan, old gold, ivory and minimal deep red. No text, watermark, fake screenshots, extra characters, generic sci-fi rings, neon city or identity changes.
```

输出：`promo/chapter_vision.png`。
