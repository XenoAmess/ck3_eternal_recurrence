package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;

/** Retained original script knowledge only; this class never reads or qualifies a loaded helper. */
public final class RiteDeclineSourceKnowledge {
    private static final String RESOURCE = "/interactionknowledge/rite-decline-static-source-12004-v1.json";
    private static final String RESOURCE_SHA = "fc1b951850d3e3f9a14a5d050bf09ccceed687e6421b29202621c2a474ff36cb";
    private static final String KEY = "sway_ruler_to_my_rite_interaction";
    private static final String EXE_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final String SOURCE_SHA = "2db73b0da8572e218f1a677a91ff4281a890ade115e6dc40e696ecb59c0b1049";
    private static final String DECLINE_SHA = "3456f3e5fc7a63a535196fae2485cd3d4e4033072aade07e3fc3e85c9ea2e1b2";
    private static final String HELPER_SHA = "fc4c77974a7844c31c1271dcc2ace24b17906620a832658919aa281e42a2b94f";
    private static final String BODY_SHA = "bdc2796645f727418a71044db5a6e6e3dda4c8e435a64e474c0f67f50a881fe1";
    private static final long KEY_HASH = 3_472_262_802L;
    private RiteDeclineSourceKnowledge() { }

    public record SourceSnapshot(String relative, int bytes, String sha256, int firstLine, int lastLine,
            String key, String body, String bodySha256) {
        public SourceSnapshot {
            require("common/scripted_effects/pam_effects.txt".equals(relative) && bytes == 369_911
                    && HELPER_SHA.equals(sha256) && firstLine == 11_753 && lastLine == 11_785
                    && "pam_sway_to_rite_on_decline_effect".equals(key) && BODY_SHA.equals(bodySha256)
                    && body != null && sha(body.getBytes(StandardCharsets.UTF_8)).equals(bodySha256),
                    "exact retained rite-decline helper source required");
        }
    }

    public record Knowledge(SourceSnapshot helper, String remainingDeclineEffects) {
        public Knowledge {
            Objects.requireNonNull(helper);
            require(remainingDeclineEffects != null && !remainingDeclineEffects.isBlank()
                    && remainingDeclineEffects.length() <= 1_024, "bounded remaining decline source explanation required");
        }
        public boolean runtimeHelperSourceVerified() { return false; }
        public boolean materialEffectsVerified() { return false; }
        public boolean semanticOptimal() { return false; }
        public boolean nativeAiEquivalent() { return false; }

        public ObjectValue json() {
            return obj(f("schema", s("xar.rite-decline-static-source-knowledge/v1")), f("build", s("1.20.0.4")),
                    f("exe_sha256", s(EXE_SHA)), f("canonical_key", s(KEY)), f("deterministic_key_hash", i(KEY_HASH)),
                    f("interaction_source_sha256", s(SOURCE_SHA)), f("on_decline_sha256", s(DECLINE_SHA)),
                    f("helper_source", obj(f("relative", s(helper.relative())), f("bytes", i(helper.bytes())), f("sha256", s(helper.sha256())),
                            f("first_line", i(helper.firstLine())), f("last_line", i(helper.lastLine())), f("key", s(helper.key())),
                            f("body", s(helper.body())), f("body_sha256", s(helper.bodySha256())))),
                    f("recipient_opinion_clause", obj(f("predicate", s("is_ai = yes")), f("modifier", s("annoyed_opinion")), f("delta", i(-10)))),
                    f("remaining_decline_effects", s(remainingDeclineEffects)), f("runtime_helper_source_verified", b(false)),
                    f("material_effects_verified", b(false)), f("semantic_optimal", b(false)), f("native_ai_equivalent", b(false)));
        }
    }

    /** Called by the real interaction analyzer after it binds the actual interaction source and GUI. */
    public static String appendAnalysis(String original, InteractionRegistry.Binding binding, String onDecline) {
        Objects.requireNonNull(original); Objects.requireNonNull(binding);
        if (!binding.build().version().equals("1.20.0.4") || !binding.build().exeSha256().equalsIgnoreCase(EXE_SHA)
                || !binding.definition().canonicalKey().equals(KEY) || binding.definition().deterministicKeyHash() != KEY_HASH
                || !binding.sourceSha256().equalsIgnoreCase(SOURCE_SHA) || onDecline == null
                || !sha(onDecline.getBytes(StandardCharsets.UTF_8)).equals(DECLINE_SHA)) return original;
        Knowledge knowledge = current();
        return original + "\n\nRetained static decline-helper source: the -10 annoyed_opinion clause requires recipient is_ai=yes. "
                + "The actual current recipient predicate, relation change and helper/VFS deployment are not verified. "
                + "This knowledge grants no choice, reply, replay, material result or native-AI ranking authority.\n"
                + new String(RetainedJson.encode(knowledge.json()), StandardCharsets.UTF_8);
    }

    public static Knowledge current() {
        byte[] raw;
        try (var stream = RiteDeclineSourceKnowledge.class.getResourceAsStream(RESOURCE)) {
            if (stream == null) throw new IllegalArgumentException("mandatory rite decline source knowledge resource missing");
            raw = stream.readNBytes(16_385);
        } catch (IOException error) { throw new IllegalArgumentException("rite decline source knowledge unavailable", error); }
        require(raw.length <= 16_384 && sha(raw).equals(RESOURCE_SHA), "rite decline source knowledge pin differs");
        return decode(raw);
    }

    /** Runtime validation precedes construction; no JSON true value can grant runtime or material authority. */
    static Knowledge decode(byte[] raw) {
        require(raw != null && raw.length > 0 && raw.length <= 16_384, "bounded rite decline source knowledge required");
        ObjectValue root = RetainedJson.object(RetainedJson.parse(raw));
        require(root.fields().keySet().equals(Set.of("schema", "build", "exe_sha256", "canonical_key", "deterministic_key_hash",
                "interaction_source_sha256", "on_decline_sha256", "helper_source", "recipient_opinion_clause", "remaining_decline_effects",
                "runtime_helper_source_verified", "material_effects_verified", "semantic_optimal", "native_ai_equivalent")),
                "exact rite decline source knowledge fields required");
        require(eq(root, "schema", s("xar.rite-decline-static-source-knowledge/v1")) && eq(root, "build", s("1.20.0.4"))
                && eq(root, "exe_sha256", s(EXE_SHA)) && eq(root, "canonical_key", s(KEY)) && eq(root, "deterministic_key_hash", i(KEY_HASH))
                && eq(root, "interaction_source_sha256", s(SOURCE_SHA)) && eq(root, "on_decline_sha256", s(DECLINE_SHA)),
                "rite decline build, definition or interaction source differs");
        for (String field : Set.of("runtime_helper_source_verified", "material_effects_verified", "semantic_optimal", "native_ai_equivalent"))
            require(eq(root, field, b(false)), "retained rite decline knowledge cannot grant " + field);
        ObjectValue helper = o(root, "helper_source"), opinion = o(root, "recipient_opinion_clause");
        require(helper != null && helper.fields().keySet().equals(Set.of("relative", "bytes", "sha256", "first_line", "last_line", "key", "body", "body_sha256"))
                && opinion != null && opinion.fields().keySet().equals(Set.of("predicate", "modifier", "delta")), "exact helper and opinion source clauses required");
        require(eq(opinion, "predicate", s("is_ai = yes")) && eq(opinion, "modifier", s("annoyed_opinion")) && eq(opinion, "delta", i(-10)),
                "rite decline opinion must retain its conditional source meaning");
        return new Knowledge(new SourceSnapshot(text(helper, "relative"), exactInt(helper, "bytes"), text(helper, "sha256"),
                exactInt(helper, "first_line"), exactInt(helper, "last_line"), text(helper, "key"), text(helper, "body"), text(helper, "body_sha256")),
                text(root, "remaining_decline_effects"));
    }

    private static int exactInt(ObjectValue row, String field) {
        var value = number(row, field); require(value != null && value.bitLength() <= 31, "exact integer source field required: " + field);
        return value.intValueExact();
    }
}
