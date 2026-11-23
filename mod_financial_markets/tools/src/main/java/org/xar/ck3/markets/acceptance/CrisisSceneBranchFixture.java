package org.xar.ck3.markets.acceptance;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.Clausewitz.Atom;
import org.xar.ck3.save.Clausewitz.Block;
import org.xar.ck3.save.Clausewitz.Entry;

/** Source-derived branch component only. No runner, emission, actor binding or engine credit.
 * The eventual explicit controlled emitter must pin this source and the exact selector input.
 * No condition, death, ledger operation, random distribution or toast is reimplemented here.
 */
public final class CrisisSceneBranchFixture {
    private CrisisSceneBranchFixture() { }
    private record Scene(int id, Block context, Block body) { }

    public static Map<String, byte[]> render(String originalSelectorSource) {
        List<Scene> scenes = scenes(originalSelectorSource);
        StringBuilder contexts = new StringBuilder(), selectors = new StringBuilder(), attempts = new StringBuilder();
        Block original = Clausewitz.parse(originalSelectorSource).block("xfm_crisis_select_scene_effect");
        Entry fallbackInitialization = original.entries().getFirst();
        for (Scene scene : scenes) {
            String suffix = String.format(java.util.Locale.ROOT, "%02d", scene.id());
            String condition = "xfmc20_context_" + suffix + "_trigger";
            String selector = "xfmc20_select_" + suffix + "_effect";
            contexts.append(condition).append(" = ").append(scene.context().render()).append('\n');
            List<Entry> body = new ArrayList<>(); body.add(fallbackInitialization); body.addAll(scene.body().entries());
            selectors.append(selector).append(" = ").append(new Block(body).render()).append('\n');
            attempts.append("xfmc20_attempt_").append(suffix).append("_effect = {\n")
                .append(" if = { limit = { xfm_crisis_terminal_review_trigger = yes }\n")
                .append("  var:xfm_holder = { save_scope_as = xfm_crisis_actor }\n")
                .append("  if = { limit = { ").append(condition).append(" = yes }\n")
                .append("   xfm_crisis_terminal_with_selector_effect = { SELECTOR = ").append(selector).append(" }\n")
                .append("  }\n }\n}\n");
        }
        Map<String, byte[]> files = new LinkedHashMap<>();
        files.put("common/scripted_triggers/xfmc20_contexts.txt", bom(contexts.toString()));
        files.put("common/scripted_effects/xfmc20_selectors.txt", bom(selectors.toString()));
        files.put("common/scripted_effects/xfmc20_attempts.txt", bom(attempts.toString()));
        return java.util.Collections.unmodifiableMap(files);
    }

    private static List<Scene> scenes(String source) {
        if (source == null || source.isBlank() || source.getBytes(StandardCharsets.UTF_8).length > 32768)
            throw new IllegalArgumentException("bounded original selector source required");
        Block root = Clausewitz.parse(source);
        if (root.entries().size() != 1) throw new IllegalArgumentException("one original selector definition required");
        Block original = root.block("xfm_crisis_select_scene_effect");
        if (original.entries().size() != 2 || !original.entries().getFirst().key().equals("set_variable")
                || !original.entries().getLast().key().equals("random_list")
                || !(original.entries().getFirst().value() instanceof Block initial) || sceneId(initial) != 20)
            throw new IllegalArgumentException("original fallback initialization and random list required");
        Block random = original.block("random_list");
        if (random.entries().size() != 20) throw new IllegalArgumentException("exact twenty original branches required");
        List<Scene> result = new ArrayList<>();
        for (int index = 0; index < random.entries().size(); index++) {
            Entry choice = random.entries().get(index);
            if (!choice.key().equals(index == 19 ? "100" : "10") || !(choice.value() instanceof Block branch))
                throw new IllegalArgumentException("unchanged twenty static production weights required");
            List<Entry> context = branch.named("trigger");
            if (context.size() != (index == 19 ? 0 : 1)) throw new IllegalArgumentException("original conditional branch or unconditional fallback required");
            if (!context.isEmpty() && !(context.getFirst().value() instanceof Block))
                throw new IllegalArgumentException("original context block required");
            Block condition = context.isEmpty() ? new Block(List.of()) : (Block) context.getFirst().value();
            Block body = new Block(branch.entries().stream().filter(e -> !e.key().equals("trigger")).toList());
            if (body.entries().size() != 1 || !body.entries().getFirst().key().equals("set_variable")
                    || !(body.entries().getFirst().value() instanceof Block value) || sceneId(value) != index + 1)
                throw new IllegalArgumentException("each original branch must only assign its own scene");
            result.add(new Scene(index + 1, condition, body));
        }
        return List.copyOf(result);
    }

    private static int sceneId(Block variable) {
        if (variable.entries().size() != 2 || !Set.of("name", "value").equals(variable.entries().stream()
                .map(Entry::key).collect(java.util.stream.Collectors.toSet())))
            throw new IllegalArgumentException("one exact scene assignment required");
        if (!(variable.named("name").getFirst().value() instanceof Atom name) || !name.token().equals("xfm_news_scene")
                || !(variable.named("value").getFirst().value() instanceof Atom number))
            throw new IllegalArgumentException("original numeric scene assignment required");
        try { return new java.math.BigDecimal(number.token()).intValueExact(); }
        catch (ArithmeticException | NumberFormatException error) { throw new IllegalArgumentException("integral scene required", error); }
    }
    private static byte[] bom(String text) { return ("\ufeff" + text).getBytes(StandardCharsets.UTF_8); }
}
