package org.xar.ck3.control.wave2.events.eventtraits;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Arrays;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact-source phase facts. This is neither a script evaluator nor live evidence. */
public final class EventEffectPhase {
    public static final String SCHEMA = "xar.ck3.source-bound-event-effect-phase/v1";
    public static final String EXE = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public static final String HEALTH_PATH = "events/health_events.txt";
    public static final String HEALTH_SHA = "74073e049a416c744b36a2a996fa467610705e38d53c836b050f1ac6f66e1212";
    private static final Set<String> FIELDS = Set.of("schema", "event_definition_key", "source", "native_option_index",
        "immediate_effects", "option_effects", "after_effects", "tooltip_only", "complete_effect_set", "live_evidence");
    private EventEffectPhase() { }

    public enum Phase { IMMEDIATE, OPTION, AFTER }
    public enum Effect {
        ILL_REMOVED, TREATMENT_CLEANED, HAD_EVENT_FLAG_SET, POEM_CONTEXT_CREATED,
        LIFESTYLE_POET_ADDED, JOURNALLER_ADDED, STRESS_CHANGED,
        CONDITIONAL_STRESS_AND_FULFILLMENT, POEM_CONTEXT_CLEANED
    }
    public record SourceBinding(String ck3Build, String exeSha256, String definitionPath, String definitionSha256) {
        public SourceBinding {
            StrictJson.text(ck3Build); StrictJson.text(definitionPath);
            exeSha256 = sha(exeSha256); definitionSha256 = sha(definitionSha256);
        }
    }
    public record Phases(String eventDefinitionKey, SourceBinding source, int nativeIndex,
                         List<Effect> immediateEffects, List<Effect> optionEffects,
                         List<Effect> afterEffects, boolean tooltipOnly) {
        public Phases {
            StrictJson.text(eventDefinitionKey); Objects.requireNonNull(source);
            StrictJson.require(nativeIndex >= 0, "nonnegative authored native option required");
            immediateEffects = List.copyOf(immediateEffects); optionEffects = List.copyOf(optionEffects);
            afterEffects = List.copyOf(afterEffects);
        }
        public List<Effect> effects(Phase phase) {
            return switch (Objects.requireNonNull(phase)) {
                case IMMEDIATE -> immediateEffects; case OPTION -> optionEffects; case AFTER -> afterEffects;
            };
        }
        public boolean optionAdds(EventTraitMembership.Trait trait) {
            return optionEffects.contains(switch (Objects.requireNonNull(trait)) {
                case LIFESTYLE_POET -> Effect.LIFESTYLE_POET_ADDED; case JOURNALLER -> Effect.JOURNALLER_ADDED;
            });
        }
        public boolean liveEvidence() { return false; }
        public boolean completeEffectSet() { return false; }
    }

    /** Unknown source/build/key/index stays unknown. It does not block legal unfamiliar-event continuation. */
    public static Optional<Phases> classify(String key, SourceBinding source, int nativeIndex) {
        Objects.requireNonNull(source); StrictJson.text(key);
        if (!"1.20.0.4".equals(source.ck3Build()) || !EXE.equals(source.exeSha256())) return Optional.empty();
        if ("health.1101".equals(key) && nativeIndex == 0 && HEALTH_PATH.equals(source.definitionPath())
                && HEALTH_SHA.equals(source.definitionSha256())) {
            return Optional.of(new Phases(key, source, nativeIndex, List.of(Effect.ILL_REMOVED, Effect.TREATMENT_CLEANED),
                List.of(), List.of(), true));
        }
        if (!PoetTraitOutcome.EVENT.equals(key) || nativeIndex < 0 || nativeIndex > 2
                || !PoetTraitOutcome.SOURCE_PATH.equals(source.definitionPath())
                || !PoetTraitOutcome.SOURCE_SHA256.equalsIgnoreCase(source.definitionSha256())) return Optional.empty();
        List<Effect> selected = switch (nativeIndex) {
            case 0 -> List.of(Effect.LIFESTYLE_POET_ADDED, Effect.CONDITIONAL_STRESS_AND_FULFILLMENT);
            case 1 -> List.of(Effect.JOURNALLER_ADDED, Effect.CONDITIONAL_STRESS_AND_FULFILLMENT);
            default -> List.of(Effect.STRESS_CHANGED, Effect.CONDITIONAL_STRESS_AND_FULFILLMENT);
        };
        return Optional.of(new Phases(key, source, nativeIndex, List.of(Effect.HAD_EVENT_FLAG_SET, Effect.POEM_CONTEXT_CREATED),
            selected, List.of(Effect.POEM_CONTEXT_CLEANED), false));
    }

    /** Retain source knowledge in full command detail; no authority or health result is encoded. */
    public static byte[] encode(Phases phases) {
        Objects.requireNonNull(phases);
        StrictJson.require(classify(phases.eventDefinitionKey(), phases.source(), phases.nativeIndex()).filter(phases::equals).isPresent(),
            "phase facts must equal the exact reviewed source");
        return StrictJson.canonical(tree(phases), 4096);
    }
    public static Phases decode(byte[] raw) {
        ObjectNode value = StrictJson.object(StrictJson.parse(raw, 4096), FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(value.get("schema"))), "exact event effect phase schema required");
        ObjectNode source = StrictJson.object(value.get("source"), Set.of("ck3_build", "exe_sha256", "definition_path", "definition_sha256"));
        var binding = new SourceBinding(StrictJson.text(source.get("ck3_build")), StrictJson.text(source.get("exe_sha256")),
            StrictJson.text(source.get("definition_path")), StrictJson.text(source.get("definition_sha256")));
        var classified = classify(StrictJson.text(value.get("event_definition_key")), binding,
            Math.toIntExact(StrictJson.integer(value.get("native_option_index"), 0, Integer.MAX_VALUE)));
        StrictJson.require(classified.isPresent(), "reviewed source/build/event/option required");
        var expected = classified.orElseThrow();
        StrictJson.require(Arrays.equals(StrictJson.canonical(tree(expected), 4096), StrictJson.canonical(value, 4096)),
            "phase/source/type/presentation facts differ from reviewed source");
        return expected;
    }
    private static ObjectNode tree(Phases phases) {
        ObjectNode value = StrictJson.object(); value.put("schema", SCHEMA).put("event_definition_key", phases.eventDefinitionKey())
            .put("native_option_index", phases.nativeIndex()).put("tooltip_only", phases.tooltipOnly())
            .put("complete_effect_set", false).put("live_evidence", false);
        SourceBinding binding = phases.source(); value.putObject("source").put("ck3_build", binding.ck3Build()).put("exe_sha256", binding.exeSha256())
            .put("definition_path", binding.definitionPath()).put("definition_sha256", binding.definitionSha256());
        for (Phase phase : Phase.values()) {
            var effects = value.putArray(phase.name().toLowerCase(Locale.ROOT) + "_effects");
            phases.effects(phase).forEach(effect -> effects.add(effect.name().toLowerCase(Locale.ROOT)));
        }
        return value;
    }
    private static String sha(String value) {
        StrictJson.require(value != null && value.matches("[0-9A-Fa-f]{64}"), "exact SHA256 required");
        return value.toLowerCase(Locale.ROOT);
    }
}
