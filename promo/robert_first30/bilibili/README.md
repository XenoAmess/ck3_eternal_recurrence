# 罗贝尔首轮三十年：Bilibili 封面

同一套封面，两种独立构图，主标题“AI执政三十年”，副标题“罗贝尔的30年”。

- [16:9 JPG，1920×1080](robert-first30-cover-16x9.jpg)
- [4:3 JPG，1440×1080](robert-first30-cover-4x3.jpg)

内容依据：[2026-10-19 休假交接](../../../docs/handover/2026-10-19-robert-first30-scoring-vacation-handoff.md)。1066—1096，统治县10→2。人物、地图及战争背景是封面概念插画，不是实机截图或精确疆域图；封面没有使用尚未闭合的总分。

使用内置 image_gen 生成；4:3 使用16:9原图作为视觉参考重新构图。FFmpeg仅负责最终JPG导出及输出尺寸规范化，完整保留两幅画面的内容。生成原件、导出命令、最终尺寸及SHA见[delivery.json](delivery.json)。本任务不操作游戏或视频，不上传到Bilibili。

## 最终提示词：16:9

```text
Use case: ads-marketing.
Create ONE finished Bilibili gaming video thumbnail, exact landscape 16:9 canvas, 2048x1152 pixels. Fill the entire canvas, no letterboxing, no border.
The video is Crusader Kings III / CK3 autonomous AI gameplay: beginning with Robert de Hauteville in 1066, spanning his dynasty for thirty years until 1096. This is an honest dramatic story of war, succession and territorial losses: actual ruled counties fell from 10 to 2. Do not suggest victory, conquest or a known total score.
Art direction: premium cinematic medieval strategy illustration, striking professional Chinese gaming cover, painterly realistic 3D game key art, sharply readable thumbnail at mobile size. Charcoal and aged parchment, warm gold type, muted dark crimson and a tiny restrained cool cyan AI accent. Restrained, editorial, dramatic.
Composition: large expressive portrait on the RIGHT third, an approximately 50-year-old 11th-century Norman duke with a short graying brown beard, worn mail armor, dark crimson wool cloak and modest ducal circlet, troubled intent gaze facing slightly left, warm side light on his face. This is a conceptual illustration, not a counterfeit game screenshot or a claim of exact in-game likeness. Behind and below him is a worn southern-Italy-inspired medieval campaign map, scattered territorial fragments and dim battlefield haze; subtle fine cyan network paths over the map evoke AI strategy without robots or futuristic costume. Keep background quiet behind the typography. Large text dominates LEFT 60%, with generous 6% safe margins, no overlapping the face.
Render these exact texts ONLY, in beautifully legible simplified Chinese:
small top eyebrow: "CK3 · 自主游玩实录"
huge main title on two lines: "AI执政" then "三十年"
medium secondary title: "罗贝尔的30年"
strong lower editorial hook: "10县 → 2县" (10 in parchment white, 2 in muted bright red, clear arrow)
small date line beneath: "1066—1096"
Main title uses heavy confident Chinese display typography, ivory and antique gold, clean edge and subtle dark shadow; make 三十年 especially prominent. The lower hook is integrated elegantly rather than resembling a dashboard or screenshot. Minimal copy, strong visual hierarchy, clear typography, all text accurate and fully inside frame.
Avoid additional words, logos, watermarks, Bilibili mascot, fake interface, score numbers, crowns of an emperor, modern weapons, fantasy monsters, blue decision windows, noisy neon, excessive particles. Return a single beautiful finished image with exact 16:9 aspect ratio.
```

## 最终提示词：4:3

```text
Use case: ads-marketing.
Input image 1 is the approved 16:9 visual reference for the SAME video. Create its matching 4:3 Bilibili cover as ONE finished image. Output exact landscape FOUR TO THREE (4:3), ideally 1440x1080 pixels, full bleed, no borders or letterboxing. The whole image must be 4:3, not a 16:9 image inside a frame.
Keep the same illustrated Norman duke's facial identity, age, short graying beard, mail armor, crimson cloak and modest circlet; the same realistic painterly medieval strategy key art; same charcoal / parchment / gold / muted crimson colors and tiny cyan AI-map paths. Keep the same editorial mood of dynasty, war and territorial losses. Do NOT add characters, scores, screenshots, badges or new words.
Adapt the composition thoughtfully to the taller, narrower 4:3 canvas: portrait occupies the RIGHT 40%, clearly visible and slightly smaller than in the wide cover, including his whole face and circlet. Quiet dark space on LEFT 60% for huge legible typography. Reduce decorative scenery so it cannot crowd text. Preserve southern-Italy-inspired campaign map and smoky medieval castle silhouettes as secondary background. Generous 6% safe margins.
Render the SAME exact simplified Chinese copy, correctly and completely:
top small line: "CK3 · 自主游玩实录"
huge main title in two lines: "AI执政" / "三十年"
medium line: "罗贝尔的30年"
strong lower hook: "10县 → 2县"
small footer: "1066—1096"
Typography must be clean, bold, beautifully typeset, white and antique gold; the "2县" red. Keep text clear of the face. Main words 三十年 must remain very prominent. Preserve the exact narrative: AI played CK3 across thirty years from 1066 to 1096; ruled counties fell from 10 to 2. This is conceptual cover artwork, not an actual screenshot.
No extra text, no watermarks, no interface or blue decision window, no robot, no imperial crown. Deliver only one professionally recomposed 4:3 finished cover.
```

