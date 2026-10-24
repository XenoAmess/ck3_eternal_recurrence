package org.xar.ck3.rrf;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Native Faith context plus explicitly source-identified final-choice exclusions. */
public final class RuleProjection {
    private static final String ASCETIC_EXCLUSION = "hesychasm_anachoresis_mortification_exclusivity_desc";
    private RuleProjection() { }
    public static String project(String source) {
        Clausewitz.Block rootBound = Clausewitz.mapAtoms(Clausewitz.parse(source), token -> token.equalsIgnoreCase("root") ? "scope:rrf_projection_faith" : token.toLowerCase(Locale.ROOT).startsWith("root.") ? "scope:rrf_projection_faith" + token.substring(4) : token);
        return finalExclusions(rootBound, false).body();
    }
    private static Clausewitz.Block finalExclusions(Clausewitz.Block block, boolean finalSelection) {
        List<Clausewitz.Entry> result = new ArrayList<>();
        for (Clausewitz.Entry entry : block.entries()) {
            if (finalSelection && entry.key().equals("has_tenet")) {
                if (!(entry.value() instanceof Clausewitz.Atom atom) || !atom.token().matches("tenet_[A-Za-z_0-9]+") || !entry.operator().equals("=")) throw new IllegalArgumentException("cannot project final tenet exclusion");
                result.add(new Clausewitz.Entry("tenet:" + atom.token(), "=", new Clausewitz.Block(List.of(new Clausewitz.Entry("is_in_list", "=", new Clausewitz.Atom("selected_tenets"))))));
            } else if (entry.value() instanceof Clausewitz.Block child) {
                boolean identified = entry.key().equals("custom_description") && child.atom("text", "").equals(ASCETIC_EXCLUSION);
                result.add(new Clausewitz.Entry(entry.key(), entry.operator(), finalExclusions(child, finalSelection || identified)));
            } else result.add(entry);
        }
        return new Clausewitz.Block(result);
    }
}
