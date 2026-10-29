package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.math.BigInteger;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativePendingInteraction;
import org.xar.ck3.control.wave2.events.interactionbefore.CurrentInteractionPresentation;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.events.interactionfallback.InteractionFallback;
import org.xar.ck3.control.events.interactionfallback.InteractionFallbackCodec;
import org.xar.ck3.control.events.interactionfallback.InteractionFallbackPlanner;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryCodec;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryReader;

/** Complete original left-reply assembly with actual trusted GUI/source reads and no native submission. */
public final class SourceReviewedInteractionContinuation {
    public static final String SCHEMA = "xar.pending-interaction-left-plan-input/v1";
    public static final int MAX_BYTES = 1_048_576;
    private SourceReviewedInteractionContinuation() { }
    public record Input(Optional<ObjectValue> snapshot, Optional<ObjectValue> context, Value originalPlan,
            List<String> actionSteps, boolean registryRequested) {
        public Input { Objects.requireNonNull(snapshot); Objects.requireNonNull(context); Objects.requireNonNull(originalPlan); actionSteps = List.copyOf(actionSteps); }
    }
    public static Input decode(byte[] raw) {
        ObjectValue root = RetainedJson.object(RetainedJson.parse(raw));
        require(root.fields().keySet().equals(Set.of("schema", "snapshot", "context", "original_plan", "action_steps", "registry_requested"))
                && eq(root, "schema", s(SCHEMA)), "exact interaction continuation wrapper required");
        require(v(root, "original_plan") instanceof NullValue || v(root, "original_plan") instanceof ObjectValue, "original interaction plan object or null required");
        List<Value> steps = array(root, "action_steps"); require(steps.size() <= 512, "bounded interaction actions required");
        List<String> actions = new ArrayList<>();
        for (Value step : steps) { require(step instanceof StringValue, "interaction action string required"); actions.add(((StringValue) step).value()); }
        Boolean registry = RetainedJson.bool(v(root, "registry_requested")); require(registry != null, "exact registry request boolean required");
        return new Input(nullableObject(root.get("snapshot")), nullableObject(root.get("context")), root.get("original_plan"), actions, registry);
    }

    public static Optional<ObjectValue> plan(Input input, TrustedEventSourceContext trusted) {
        Objects.requireNonNull(input); Objects.requireNonNull(trusted);
        ObjectValue snapshot = input.snapshot().orElse(null); ObjectValue context = input.context().orElse(null);
        if (snapshot == null || context == null) return Optional.empty();
        ObjectValue pending = o(snapshot, "pending_character_interaction");
        if (pending == null || !eq(context, "status", s("available"))) return Optional.empty();
        NativePendingInteraction.Pending nativePending;
        try { nativePending = NativePendingInteraction.decode(StrictJson.parse(RetainedJson.encode(pending))).orElseThrow(); }
        catch (IllegalArgumentException invalidNativePending) { return Optional.empty(); }
        BigInteger pendingId = BigInteger.valueOf(nativePending.instanceId());
        if (pendingId.equals(BigInteger.valueOf(-1)) || pendingId.bitLength() > 31
                || !v(context, "pending_interaction_id").equals(v(pending, "instance_id"))
                || number(context, "pending_interaction_id") == null || number(context, "snapshot_revision") == null || number(context, "date_raw") == null
                || !v(context, "snapshot_revision").equals(v(snapshot, "native_revision")) || !v(context, "date_raw").equals(v(snapshot, "date_raw"))) return Optional.empty();
        InteractionFallback.ReplyLegality replyLegality = legality(o(context, "legality"));
        ObjectValue binding = binding(snapshot);
        CurrentInteractionPresentation.Presentation presentation;
        try {
            presentation = CurrentInteractionPresentation.derive(StrictJson.parse(RetainedJson.encode(binding)),
                    nativePending, StrictJson.parse(RetainedJson.encode(context)), Set.copyOf(input.actionSteps()));
        } catch (IllegalArgumentException invalidCurrentPresentation) { return Optional.empty(); }
        var frame = presentation.binding();
        var projected = new InteractionFallback.Request(new InteractionFallback.Binding(frame.snapshotId(), frame.revision(),
                frame.nativeRevision(), frame.dateRaw(), frame.episodeRunId(), frame.paused(), frame.mapReady(),
                frame.actorCharacterId(), frame.connectionGeneration(), frame.bridgePid()),
                new InteractionFallback.Pending(nativePending.instanceId(), nativePending.senderCharacterId().intValueExact(),
                        nativePending.autoAcceptNotification()),
                new InteractionFallback.Context(InteractionFallback.Status.AVAILABLE, frame.nativeRevision(), frame.dateRaw(),
                        nativePending.instanceId(), new InteractionFallback.Definition(presentation.definition(),
                                presentation.definitionHash().longValueExact()), replyLegality),
                originalPlan(input.originalPlan()), new LinkedHashSet<>(input.actionSteps()));
        InteractionFallback.Candidate candidate = InteractionFallbackPlanner.plan(projected).candidate();
        if (candidate == null) return Optional.empty();
        verifyGui(trusted);
        InteractionFallback.Selection choice = candidate.selection();
        String key = presentation.definition(); BigInteger hash = presentation.definitionHash();
        ObjectValue known = null; ObjectValue audit = obj(f("status", s("not_needed")));
        if (key != null && hash != null && hash.signum() >= 0 && hash.bitLength() <= 32) {
            Optional<InteractionFallback.ReviewedRule> compiled = InteractionFallbackPlanner.reviewedRule(new InteractionFallback.Definition(key, hash.longValueExact()));
            if (compiled.isPresent()) {
                InteractionFallback.ReviewedRule rule = compiled.orElseThrow();
                try {
                    byte[] source = trusted.readInteractionSource(trusted.stockGameDirectory().resolve(rule.source()), 2_097_152);
                    if (sha(source).equals(rule.sourceSha256())) known = compiledRule(rule);
                } catch (TrustedEventSourceContext.UnavailableException unavailable) {
                    if (unavailable.failureKind() != TrustedEventSourceContext.FailureKind.OPTIONAL_EVIDENCE_UNAVAILABLE) throw unavailable;
                }
            }
        }
        if (known == null && input.registryRequested()) {
            InteractionRegistry.Result review = lookup(context, trusted);
            ObjectValue result = RetainedJson.object(RetainedJson.parse(InteractionHostJson.encodeRegistry(review)));
            known = o(result, "reviewed"); audit = o(result, "audit");
        }
        // Optional knowledge cannot weaken the original root witnesses or the exact fallback GUI pin.
        verifyGui(trusted);
        ObjectValue gui = RetainedJson.object(RetainedJson.parse(org.xar.ck3.control.contracts.StrictJson.canonical(InteractionFallbackCodec.guiBinding())));
        List<ObjectValue> normal = objects(gui, "normal_channel");
        ObjectValue nativeLegality = o(context, "legality"); List<Value> replies = new ArrayList<>();
        for (ObjectValue row : normal) replies.add(row.with("native_legality", v(nativeLegality, text(row, "action"))));
        ObjectValue selection = choice.action() == InteractionFallback.Action.ACKNOWLEDGE ? o(gui, "auto_accept_channel") : normal.getFirst();
        selection = put(selection, f("native_legal", b(choice.nativeLegal())), f("action_reachable", b(choice.actionReachable())));
        gui = gui.with("current_presentation", RetainedJson.parse(StrictJson.canonical(CurrentInteractionPresentation.encode(presentation))));
        boolean isKnown = known != null; String step = choice.proposed() ? choice.action().step() : null;
        String classification = isKnown ? text(known, "classification") : "uncovered_pending_character_interaction";
        ObjectValue capture = obj(f("schema", s("xar.pending-interaction-left-reply/v1")), f("kind", s("pending_character_interaction")),
                f("policy", s("user-authorized-native-gui-left-reply")), f("pending_interaction_id", v(pending, "instance_id")),
                f("interaction_definition_key", s(key)), f("binding", binding), f("context", context), f("gui_binding", gui),
                f("reply_options", new ArrayValue(replies)), f("selection", selection), f("registry_known", b(isKnown)), f("reviewed_rule", known == null ? NULL : known),
                f("offline_registry_audit", audit), f("presented_choice_policy", NULL), f("offline_followup_required", b(!isKnown)),
                f("original_plan", input.originalPlan()), f("semantic_optimal", b(false)), f("native_ai_equivalent", b(false)));
        String phase = !choice.nativeLegal() ? InteractionFallback.Phase.DISABLED.wire() : !choice.actionReachable() ? InteractionFallback.Phase.UNSUPPORTED.wire()
                : isKnown ? InteractionFallback.Phase.REVIEWED.wire() : InteractionFallback.Phase.FALLBACK.wire();
        return Optional.of(obj(f("policy", s("one-life-turn-v1")), f("phase", s(phase)), f("selected_step", s(step)),
                f("reason", s(choice.proposed() ? isKnown ? text(known, "reason") : InteractionFallback.UNKNOWN_REASON : InteractionFallback.UNAVAILABLE_REASON)),
                f("pending_character_interaction", pending), f("decision", obj(f("classification", s(classification)), f("registry_known", b(isKnown)),
                        f("selected_action", s(choice.proposed() ? choice.action().wire() : null)), f("selected_step", s(step)),
                        f("display_position", s(choice.position())), f("semantic_optimal", b(false)))), f("unhandled_interaction_fallback", capture)));
    }
    /** Pure original-plan projection shared by the ordinary and private notification consumers. */
    public static InteractionFallback.OriginalPlan originalPlan(Value original) {
        require(original instanceof NullValue || original instanceof ObjectValue, "original pending plan object or null required");
        ObjectValue plan = o(original);
        Value phaseToken = v(plan, "phase"), selectedToken = v(plan, "selected_step");
        require(phaseToken instanceof NullValue || phaseToken instanceof StringValue, "original pending phase string or null required");
        require(selectedToken instanceof NullValue || selectedToken instanceof StringValue, "original pending selected step string or null required");
        String phase = text(plan, "phase"), selected = text(plan, "selected_step");
        if (phase == null) phase = "pending_character_interaction";
        ObjectValue decision = o(plan, "decision"), definition = o(decision, "definition_classification");
        Value gaps = v(decision, "marriage_contract_gaps");
        boolean blockedMarriage = selected == null && phase.equals("pending_character_interaction_degraded_blocked")
                && ("known_marriage_special".equals(text(decision, "classification"))
                    || "evidence_invalid".equals(text(decision, "classification"))
                        && "arrange_marriage_interaction".equals(text(decision, "interaction_key"))
                        && gaps instanceof ArrayValue rows && !rows.values().isEmpty())
                && "arrange_marriage_interaction".equals(text(definition, "definition_key"));
        return new InteractionFallback.OriginalPlan(phase, selected, blockedMarriage, o(plan, "unhandled_interaction_fallback") != null);
    }
    private static ObjectValue binding(ObjectValue snapshot) {
        ObjectValue binding = obj();
        for (String field : List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "paused", "map_ready")) binding = binding.with(field, v(snapshot, field));
        binding = binding.with("actor_character_id", v(o(snapshot, "played_character"), "character_id"));
        ObjectValue diagnostics = o(snapshot, "diagnostics");
        for (String field : List.of("connection_generation", "bridge_pid")) binding = binding.with(field,
                snapshot.fields().containsKey(field) ? snapshot.get(field) : v(diagnostics, field));
        return binding;
    }
    public static void verifyGui(TrustedEventSourceContext trusted) {
        trusted.requireInteractionGui(InteractionFallback.GUI_SHA256);
    }
    private static InteractionRegistry.Result lookup(ObjectValue context, TrustedEventSourceContext trusted) {
        InteractionRegistry.Lookup lookup;
        try {
            ObjectValue nativeDefinition = o(context, "definition");
            ObjectValue request = obj(f("schema", s("xar.interaction-registry-lookup/v1")), f("build", v(context, "build")),
                    f("definition", obj(f("canonical_key", v(nativeDefinition, "canonical_key")), f("deterministic_key_hash", v(nativeDefinition, "deterministic_key_hash")))),
                    f("gui_sha256", s(InteractionFallback.GUI_SHA256)));
            lookup = InteractionRegistryCodec.parseLookup(RetainedJson.encode(request));
        } catch (IllegalArgumentException invalidNativeIdentity) { return new InteractionRegistry.Unknown(InteractionRegistry.UnknownReason.NO_MATCH, List.of()); }
        // Required source failures raised by the reader are not malformed optional lookup input.
        return new InteractionRegistryReader(trusted.machineId()).load(trusted, lookup);
    }
    private static InteractionFallback.ReplyLegality legality(ObjectValue original) {
        return new InteractionFallback.ReplyLegality(legal(original, "accept"), legal(original, "reject"), legal(original, "block"), legal(original, "acknowledge"));
    }
    private static InteractionFallback.Legality legal(ObjectValue original, String action) {
        if (original == null || !original.fields().containsKey(action)) return new InteractionFallback.Legality(InteractionFallback.Presence.MISSING, null, null, null);
        Value value = original.get(action); if (value instanceof NullValue) return new InteractionFallback.Legality(InteractionFallback.Presence.NULL, null, null, null);
        ObjectValue row = o(value);
        if (row == null) throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection("native interaction legality object required");
        String status = text(row, "status"); InteractionFallback.Status state = "available".equals(status) ? InteractionFallback.Status.AVAILABLE
                : "unavailable".equals(status) ? InteractionFallback.Status.UNAVAILABLE : InteractionFallback.Status.INVALID;
        Value allowedToken = v(row, "allowed");
        if (!(allowedToken instanceof NullValue) && !(allowedToken instanceof BooleanValue)) {
            throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection("native interaction allowed boolean or null required");
        }
        Boolean allowed = RetainedJson.bool(allowedToken);
        return new InteractionFallback.Legality(InteractionFallback.Presence.VALUE, state, allowed, text(row, "reason"));
    }
    private static ObjectValue compiledRule(InteractionFallback.ReviewedRule rule) {
        return obj(f("classification", s(rule.classification())), f("preferred_action", s(rule.preferredAction())), f("deterministic_key_hash", i(rule.deterministicKeyHash())),
                f("source", s(rule.source())), f("source_sha256", s(rule.sourceSha256())), f("source_lines", s(rule.sourceLines())), f("reason", s(rule.reason())));
    }
    private static Optional<ObjectValue> nullableObject(Value value) {
        require(value instanceof NullValue || value instanceof ObjectValue, "optional interaction object or explicit null required"); return Optional.ofNullable(o(value));
    }
    public static byte[] encode(Optional<ObjectValue> plan) { return RetainedJson.encode(plan.<Value>map(value -> value).orElse(NULL)); }
}
