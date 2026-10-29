package org.xar.ck3.control.wave2.governance.succession;

import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.GameIdentity;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.Session;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;

/** Pure observation over Root-retained originals. No continuation, replay, writer or native authority. */
public final class NativeSuccessionObservation12004 {
    public static final String SCHEMA = "xar.java.native-succession-observation12004/v1";
    public static final String EXECUTABLE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public static final int MAX_REPORT_BYTES = 524288;
    private NativeSuccessionObservation12004() { }

    public enum Reason { ROOT_SOURCE_UNAVAILABLE, SOURCE_REJECTED, GAME_IDENTITY_CHANGED,
        LIFECYCLE_UNSUPPORTED, FRAME_REGRESSED, TITLE_RESULT_MISMATCH, SUCCESSOR_EPISODE_UNOBSERVED,
        GOAL_CONTINUITY_UNOBSERVED, GOAL_CONTINUITY_MISMATCH }
    public enum State { PREDEATH_FROZEN, TRANSITION_RECONCILED, CONTINUATION_OBSERVED, UNAVAILABLE }

    public record Goal(String campaignId, String goalKey, int originCharacterId, int currentCharacterId,
                       BigInteger reconciledSuccessions, ProjectionJson lastSuccession) {
        public Goal {
            nonempty(campaignId); check("dynasty_continuity".equals(goalKey), "unsupported ordinary goal");
            NativeCharacterId.of(originCharacterId); NativeCharacterId.of(currentCharacterId); uint64(reconciledSuccessions);
            check(lastSuccession == null || lastSuccession.isObject(), "goal last succession must be an object");
        }
    }
    public record Proof(Session session, G2Source source, ExactRef rootResultRef, ExactRef turnBundleRef) {
        public Proof {
            Objects.requireNonNull(session); Objects.requireNonNull(source);
            Objects.requireNonNull(rootResultRef); Objects.requireNonNull(turnBundleRef);
            check(session.machineId().equals(source.machineId()), "source machine differs");
            check(source.exactBuild().equals("1.20.0.4@sha256:" + EXECUTABLE_SHA256)
                    && session.executable().sha256().equals(EXECUTABLE_SHA256), "exact current build required");
        }
    }
    public record Frame(Proof proof, Snapshot snapshot, TurnBundle bundle,
                        SuccessionLifecycleBinding lifecycle, Goal goal, ProjectionJson government) {
        public Frame {
            Objects.requireNonNull(proof); Objects.requireNonNull(snapshot); Objects.requireNonNull(bundle);
            Objects.requireNonNull(lifecycle);
            check(snapshot.frame() != null && snapshot.frame().equals(bundle.frame()), "source frame differs");
            check(proof.session().episodeRunId().equals(snapshot.episodeRunId()), "source episode differs");
            check(snapshot.actor() != null && bundle.ruler().equals(snapshot.actor()), "root actor differs");
            check(government == null || government.isObject(), "observed government must be an object");
        }
    }
    public sealed interface Outcome permits Frozen, Transition, Continued, Unavailable { }
    public record Frozen(Frame predecessor, Expectation expectation) implements Outcome {
        public Frozen {
            Objects.requireNonNull(predecessor); Objects.requireNonNull(expectation);
            check(expectation.binding().frame().equals(predecessor.snapshot().frame())
                    && expectation.binding().episodeRunId().equals(predecessor.snapshot().episodeRunId())
                    && expectation.predecessorCharacterId() == predecessor.snapshot().actor().characterId(),
                    "retained estate source differs");
        }
    }
    public record Transition(Frozen retained, Frame successor, Reconciliation reconciliation) implements Outcome {
        public Transition { Objects.requireNonNull(retained); Objects.requireNonNull(successor); Objects.requireNonNull(reconciliation); }
    }
    public record Continued(Transition transition, Frame current) implements Outcome {
        public Continued { Objects.requireNonNull(transition); Objects.requireNonNull(current); }
    }
    public record Unavailable(Reason reason, String detail) implements Outcome {
        public Unavailable { Objects.requireNonNull(reason); nonempty(detail); check(detail.length() <= 512, "bounded detail required"); }
    }
    /** Serializable evidence only. Decoding this record never admits a native source or another action. */
    public record Report(State state, Reason unavailableReason, List<Proof> sources,
                         ProjectionJson expectation, ProjectionJson reconciliation,
                         Goal goal, ProjectionJson government) {
        public Report {
            Objects.requireNonNull(state); sources = List.copyOf(sources);
            int expected = switch (state) { case PREDEATH_FROZEN -> 1; case TRANSITION_RECONCILED -> 2;
                case CONTINUATION_OBSERVED -> 3; case UNAVAILABLE -> 0; };
            check(sources.size() == expected, "report source arity differs");
            check((state == State.UNAVAILABLE) == (unavailableReason != null), "report unavailable branch differs");
            check((state == State.UNAVAILABLE) == (expectation == null), "report expectation branch differs");
            check((state == State.TRANSITION_RECONCILED || state == State.CONTINUATION_OBSERVED)
                    == (reconciliation != null), "report reconciliation branch differs");
            if (expectation != null) { SuccessionCodec.decodeExpectation(expectation.bytes()); }
            check(government == null || government.isObject(), "report government must be object/null");
            check(state != State.CONTINUATION_OBSERVED || goal != null, "continued goal must be observed");
        }
    }

    public static Outcome freeze(Frame frame) {
        Objects.requireNonNull(frame);
        if (!frame.lifecycle().profile().ordinary()) { return unavailable(Reason.LIFECYCLE_UNSUPPORTED, "ordinary lifecycle is not observed"); }
        try {
            byte[] wire = SuccessionPlanningProducer.produce(new SuccessionPlanningProducer.RetainInput(
                    frame.snapshot(), frame.bundle(), frame.snapshot().frame().revision()));
            return new Frozen(frame, SuccessionCodec.decodeExpectation(wire));
        } catch (IllegalArgumentException rejected) { return unavailable(Reason.SOURCE_REJECTED, rejected.getMessage()); }
    }
    public static Outcome reconcile(Frozen retained, Frame successor) {
        Objects.requireNonNull(retained); Objects.requireNonNull(successor);
        Frame previous = retained.predecessor();
        if (!sameGame(previous, successor)) { return unavailable(Reason.GAME_IDENTITY_CHANGED, "different Game birth, executable, connection or session"); }
        if (!previous.lifecycle().equals(successor.lifecycle()) || !successor.lifecycle().profile().ordinary()) {
            return unavailable(Reason.LIFECYCLE_UNSUPPORTED, "ordinary lifecycle/environment changed");
        }
        if (!ordered(previous, successor)) { return unavailable(Reason.FRAME_REGRESSED, "source frame regressed"); }
        try {
            Reconciliation result = SuccessionPolicy.reconcile(retained.expectation(), successor.snapshot(), successor.bundle());
            return new Transition(retained, successor, result);
        } catch (IllegalArgumentException rejected) { return unavailable(Reason.SOURCE_REJECTED, rejected.getMessage()); }
    }
    public static Outcome observeContinued(Transition transition, Frame current) {
        Objects.requireNonNull(transition); Objects.requireNonNull(current);
        if (transition.reconciliation().verdict() != Verdict.MATCHED) {
            return unavailable(Reason.TITLE_RESULT_MISMATCH, "successor or estate did not match; no replay or continuation inferred");
        }
        Frame previous = transition.retained().predecessor();
        if (!sameGame(transition.successor(), current)) { return unavailable(Reason.GAME_IDENTITY_CHANGED, "continued observation belongs to another Game/session"); }
        if (!previous.lifecycle().equals(current.lifecycle()) || !current.lifecycle().profile().ordinary()) {
            return unavailable(Reason.LIFECYCLE_UNSUPPORTED, "continued lifecycle/environment changed");
        }
        if (!ordered(transition.successor(), current)) { return unavailable(Reason.FRAME_REGRESSED, "continued frame regressed"); }
        Snapshot snapshot = current.snapshot(); int successor = transition.reconciliation().actualSuccessorCharacterId();
        if (!Boolean.TRUE.equals(snapshot.paused()) || !Boolean.TRUE.equals(snapshot.mapReady())
                || !Boolean.FALSE.equals(snapshot.terminal()) || snapshot.terminalReason() != null
                || !snapshot.actor().alive() || snapshot.actor().characterId() != successor
                || !Objects.equals(snapshot.episodeCharacterId(), successor)
                || snapshot.episodeRunId().equals(previous.snapshot().episodeRunId())) {
            return unavailable(Reason.SUCCESSOR_EPISODE_UNOBSERVED, "actual new successor episode has not been observed");
        }
        Goal oldGoal = previous.goal(), newGoal = current.goal();
        if (oldGoal == null || newGoal == null) { return unavailable(Reason.GOAL_CONTINUITY_UNOBSERVED, "original high-level goal is missing"); }
        if (!oldGoal.campaignId().equals(newGoal.campaignId()) || !oldGoal.goalKey().equals(newGoal.goalKey())
                || oldGoal.originCharacterId() != newGoal.originCharacterId()
                || oldGoal.currentCharacterId() != transition.reconciliation().predecessorCharacterId()
                || newGoal.currentCharacterId() != successor
                || !newGoal.reconciledSuccessions().equals(oldGoal.reconciledSuccessions().add(BigInteger.ONE))
                || !lastGoalMatches(newGoal, transition.reconciliation())) {
            return unavailable(Reason.GOAL_CONTINUITY_MISMATCH, "goal identity/progress does not match the observed transition");
        }
        return new Continued(transition, current);
    }
    private static boolean lastGoalMatches(Goal goal, Reconciliation reconciliation) {
        if (goal.lastSuccession() == null) { return false; }
        JsonNode actual = StrictJson.parse(goal.lastSuccession().bytes(), SuccessionCodec.MAX_BYTES);
        JsonNode expected = StrictJson.parse(SuccessionCodec.encodeReconciliation(reconciliation), SuccessionCodec.MAX_BYTES);
        for (String field : List.of("predecessor_character_id", "actual_successor_character_id", "matched_inherited_title_ids",
                "expected_other_heir_title_ids", "expected_without_heir_title_ids")) {
            if (!Objects.equals(actual.get(field), expected.get(field))) { return false; }
        }
        return true;
    }
    private static boolean ordered(Frame before, Frame after) {
        return before.snapshot().frame().dateRaw() <= after.snapshot().frame().dateRaw()
                && before.snapshot().frame().revision().compareTo(after.snapshot().frame().revision()) <= 0
                && before.snapshot().frame().nativeRevision().compareTo(after.snapshot().frame().nativeRevision()) <= 0;
    }
    private static boolean sameGame(Frame before, Frame after) {
        Session a = before.proof().session(), b = after.proof().session();
        return a.machineId().equals(b.machineId()) && a.sessionId().equals(b.sessionId()) && a.game().equals(b.game())
                && a.connectionGeneration().equals(b.connectionGeneration()) && a.executable().equals(b.executable())
                && a.executableFileId().equals(b.executableFileId()) && a.executableMtimeNs().equals(b.executableMtimeNs());
    }
    private static Unavailable unavailable(Reason reason, String detail) {
        String value = detail == null || detail.isEmpty() ? reason.name() : detail;
        return new Unavailable(reason, value.substring(0, Math.min(512, value.length())));
    }

    public static Report report(Outcome outcome) {
        if (outcome instanceof Unavailable rejected) {
            return new Report(State.UNAVAILABLE, rejected.reason(), List.of(), null, null, null, null);
        }
        Frozen frozen; Transition transition = null; Frame last; State state; List<Proof> sources = new ArrayList<>();
        if (outcome instanceof Frozen value) { frozen = value; last = value.predecessor(); state = State.PREDEATH_FROZEN; }
        else if (outcome instanceof Transition value) { transition = value; frozen = value.retained(); last = value.successor(); state = State.TRANSITION_RECONCILED; }
        else { Continued value = (Continued) outcome; transition = value.transition(); frozen = transition.retained(); last = value.current(); state = State.CONTINUATION_OBSERVED; }
        sources.add(frozen.predecessor().proof());
        if (transition != null) { sources.add(transition.successor().proof()); }
        if (state == State.CONTINUATION_OBSERVED) { sources.add(last.proof()); }
        return new Report(state, null, sources, ProjectionJson.object(SuccessionCodec.encodeExpectation(frozen.expectation()), SuccessionCodec.MAX_BYTES),
                transition == null ? null : ProjectionJson.object(SuccessionCodec.encodeReconciliation(transition.reconciliation()), SuccessionCodec.MAX_BYTES),
                last.goal(), last.government());
    }
    public static byte[] encode(Report report) {
        ObjectNode out = StrictJson.object(); out.put("schema", SCHEMA); out.put("state", wire(report.state()));
        if (report.unavailableReason() == null) { out.putNull("unavailable_reason"); }
        else { out.put("unavailable_reason", wire(report.unavailableReason())); }
        ArrayNode sources = out.putArray("sources");
        for (Proof proof : report.sources()) { sources.add(proofNode(proof)); }
        rawProjection(out, "expectation_base64", report.expectation()); rawProjection(out, "reconciliation_base64", report.reconciliation());
        rawProjection(out, "government_base64", report.government());
        out.set("goal", goalNode(report.goal()));
        out.put("native_queries", 0).put("game_commands", 0).put("ledger_writes", 0).put("submission_authorized", false)
                .put("natural_death_proven", false).put("realm_preservation_proven", false);
        return StrictJson.canonical(out, MAX_REPORT_BYTES);
    }
    public static Report decodeReport(byte[] raw) {
        ObjectNode node = StrictJson.object(StrictJson.parse(raw, MAX_REPORT_BYTES), Set.of("schema", "state", "unavailable_reason",
                "sources", "expectation_base64", "reconciliation_base64", "government_base64", "goal", "native_queries", "game_commands",
                "ledger_writes", "submission_authorized", "natural_death_proven", "realm_preservation_proven"));
        check(SCHEMA.equals(StrictJson.text(node.get("schema"))), "observation schema changed");
        for (String key : List.of("native_queries", "game_commands", "ledger_writes")) { check(StrictJson.integer(node.get(key), 0, 0) == 0, "observation has an action count"); }
        for (String key : List.of("submission_authorized", "natural_death_proven", "realm_preservation_proven")) {
            check(node.get(key).isBoolean() && !node.get(key).booleanValue(), "observation cannot grant authority or unobserved outcomes");
        }
        State state = enumeration(State.class, StrictJson.text(node.get("state")));
        Reason reason = node.get("unavailable_reason").isNull() ? null : enumeration(Reason.class, StrictJson.text(node.get("unavailable_reason")));
        check(node.get("sources").isArray() && node.get("sources").size() <= 3, "bounded source proof array required");
        List<Proof> sources = new ArrayList<>(); for (JsonNode source : node.get("sources")) { sources.add(proof(source)); }
        return new Report(state, reason, sources, rawProjection(node.get("expectation_base64")), rawProjection(node.get("reconciliation_base64")),
                reportGoal(node.get("goal")), rawProjection(node.get("government_base64")));
    }
    static Goal goal(JsonNode node) {
        if (node == null || node.isNull()) { return null; }
        check(node.isObject(), "goal object required");
        check(StrictJson.integer(node.get("format_version"), 1, 1) == 1, "goal format changed");
        JsonNode progress = node.get("progress"); check(progress != null && progress.isObject(), "goal progress required");
        return new Goal(StrictJson.text(node.get("campaign_id")), StrictJson.text(node.get("goal_key")),
                NativeCharacterId.fromJson(node.get("origin_character_id")).value(),
                NativeCharacterId.fromJson(node.get("current_character_id")).value(),
                StrictJson.integer(progress.get("reconciled_successions"), BigInteger.ZERO, StrictJson.UINT64_MAX),
                projection(progress.get("last_succession")));
    }
    private static JsonNode goalNode(Goal goal) {
        if (goal == null) { return com.fasterxml.jackson.databind.node.NullNode.instance; }
        ObjectNode out = StrictJson.object(); out.put("campaign_id", goal.campaignId())
                .put("goal_key", goal.goalKey()).put("origin_character_id", goal.originCharacterId()).put("current_character_id", goal.currentCharacterId())
                .put("reconciled_successions_decimal", goal.reconciledSuccessions().toString());
        rawProjection(out, "last_succession_base64", goal.lastSuccession()); return out;
    }
    private static Goal reportGoal(JsonNode value) {
        if (value.isNull()) { return null; }
        ObjectNode node = StrictJson.object(value, Set.of("campaign_id", "goal_key", "origin_character_id",
                "current_character_id", "reconciled_successions_decimal", "last_succession_base64"));
        String count = StrictJson.text(node.get("reconciled_successions_decimal"));
        check(count.matches("0|[1-9][0-9]{0,19}"), "canonical goal count decimal required");
        return new Goal(StrictJson.text(node.get("campaign_id")), StrictJson.text(node.get("goal_key")),
                NativeCharacterId.fromJson(node.get("origin_character_id")).value(),
                NativeCharacterId.fromJson(node.get("current_character_id")).value(),
                new BigInteger(count), rawProjection(node.get("last_succession_base64")));
    }
    private static void rawProjection(ObjectNode out, String key, ProjectionJson value) {
        if (value == null) { out.putNull(key); } else { out.put(key, Base64.getEncoder().encodeToString(value.bytes())); }
    }
    private static ProjectionJson rawProjection(JsonNode value) {
        if (value.isNull()) { return null; }
        String text = StrictJson.text(value); byte[] bytes = Base64.getDecoder().decode(text);
        check(Base64.getEncoder().encodeToString(bytes).equals(text), "canonical original-byte base64 required");
        return ProjectionJson.object(bytes, MAX_REPORT_BYTES);
    }
    private static void projection(ObjectNode out, String key, ProjectionJson value) {
        if (value == null) { out.putNull(key); } else { out.set(key, StrictJson.parse(value.bytes(), MAX_REPORT_BYTES)); }
    }
    private static ProjectionJson projection(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        check(value.isObject(), "object/null observation field required");
        return ProjectionJson.object(StrictJson.canonical(value, MAX_REPORT_BYTES), MAX_REPORT_BYTES);
    }
    private static ObjectNode proofNode(Proof proof) {
        Session s = proof.session(); ObjectNode out = StrictJson.object();
        ObjectNode session = out.putObject("session"); session.put("machine_id", s.machineId()).put("session_id", s.sessionId())
                .put("pid_decimal", Long.toString(s.game().pid())).put("creation_filetime", s.game().creationFiletime())
                .put("episode_run_id", s.episodeRunId()).put("connection_generation", s.connectionGeneration())
                .put("executable_file_id", s.executableFileId()).put("executable_mtime_ns", s.executableMtimeNs());
        session.set("executable", s.executable().toJson());
        ObjectNode source = out.putObject("source"); source.put("machine_id", proof.source().machineId())
                .put("observed_at_utc", proof.source().observedAtUtc()).put("exact_build", proof.source().exactBuild());
        source.set("source_ref", proof.source().sourceRef().toJson());
        out.set("root_result_ref", proof.rootResultRef().toJson()); out.set("turn_bundle_ref", proof.turnBundleRef().toJson()); return out;
    }
    private static Proof proof(JsonNode value) {
        ObjectNode out = StrictJson.object(value, Set.of("session", "source", "root_result_ref", "turn_bundle_ref"));
        ObjectNode s = StrictJson.object(out.get("session"), Set.of("machine_id", "session_id", "pid_decimal", "creation_filetime",
                "episode_run_id", "connection_generation", "executable", "executable_file_id", "executable_mtime_ns"));
        String pid = StrictJson.text(s.get("pid_decimal")); check(pid.matches("[1-9][0-9]{0,9}"), "canonical PID decimal required");
        Session session = new Session(StrictJson.text(s.get("machine_id")), StrictJson.text(s.get("session_id")),
                new GameIdentity(Long.parseLong(pid), StrictJson.text(s.get("creation_filetime"))), StrictJson.text(s.get("episode_run_id")),
                StrictJson.text(s.get("connection_generation")), ExactRef.fromJson(s.get("executable")),
                StrictJson.text(s.get("executable_file_id")), StrictJson.text(s.get("executable_mtime_ns")));
        ObjectNode source = StrictJson.object(out.get("source"), Set.of("machine_id", "observed_at_utc", "exact_build", "source_ref"));
        return new Proof(session, new G2Source(StrictJson.text(source.get("machine_id")), StrictJson.text(source.get("observed_at_utc")),
                StrictJson.text(source.get("exact_build")), ExactRef.fromJson(source.get("source_ref"))),
                ExactRef.fromJson(out.get("root_result_ref")), ExactRef.fromJson(out.get("turn_bundle_ref")));
    }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    private static <E extends Enum<E>> E enumeration(Class<E> type, String value) { return Enum.valueOf(type, value.toUpperCase(Locale.ROOT)); }
}
