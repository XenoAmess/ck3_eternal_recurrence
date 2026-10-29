package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** The complete original two fixed-window contracts, including the independent application-owner receipt. */
public final class ArmyWindowCodec {
    public enum Kind {
        OVERVIEW("war_declared_overview", "war-declared-overview", "close", Set.of("", "dismiss", "button_close")),
        RESULTS("war_results", "war-results-window", "dismiss", Set.of("", "close_button"));
        private final String window, suffix, trace; private final Set<String> buttons;
        Kind(String window, String suffix, String trace, Set<String> buttons) { this.window = window; this.suffix = suffix; this.trace = trace; this.buttons = buttons; }
        public String ownerKey() { return this == OVERVIEW ? "war_declared_overview_owner_receipt" : "war_results_window_owner_receipt"; }
        public String step(Operation operation) { return operation.name().toLowerCase(java.util.Locale.ROOT) + "-" + suffix + "-v1"; }
        public String capability(Operation operation) { return "game.command." + step(operation); }
    }
    public enum Operation { QUERY, CLOSE }
    public static final class Observation {
        private final Kind kind; private final Operation operation; private final RawJson normalized, leaf, owner;
        private Observation(Kind kind, Operation operation, ObjectNode normalized, ObjectNode leaf, ObjectNode owner) {
            this.kind = kind; this.operation = operation; this.normalized = new RawJson(bytes(normalized)); this.leaf = new RawJson(bytes(leaf)); this.owner = new RawJson(bytes(owner));
        }
        public Kind kind() { return kind; } public Operation operation() { return operation; }
        public ObjectNode normalized() { return parse(normalized.bytes()); } public ObjectNode leaf() { return parse(leaf.bytes()); } public ObjectNode owner() { return parse(owner.bytes()); }
        public boolean available() { return bool(leaf().get("available")); } public String status() { return text(leaf().get("status")); }
        @Override public boolean equals(Object value) { return value instanceof Observation other && kind == other.kind && operation == other.operation && normalized.equals(other.normalized) && leaf.equals(other.leaf) && owner.equals(other.owner); }
        @Override public int hashCode() { return java.util.Objects.hash(kind,operation,normalized,leaf,owner); }
    }
    private static final String BUILD = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final Set<String> BOOLS = Set.of("available", "accepted", "root_observed", "window_present", "effective_visible", "dispatch_attempted", "dispatch_invoked", "native_handled", "post_observed", "post_window_present", "post_effective_visible", "scope_unchanged", "closure_verified", "application_owner_thread_verified", "paused");
    private static final Set<String> TEXTS = Set.of("status", "unavailable_reason", "button_name", "request_id", "root_observation_source", "post_observation_source");
    private static final Set<String> BASE;
    private static final Set<String> OWNER = Set.of("request_id", "ticket_sequence", "executor_started_sequence", "completed_sequence", "pump_epoch", "thread_id", "date_raw", "connection_generation");
    private static final Set<String> SOURCES = Set.of("guarded_registered_top_level", "guarded_top_level_and_complete_owner_tree");
    private static final BigInteger MAX32 = BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
    static { var fields = new HashSet<>(BOOLS); fields.addAll(TEXTS); fields.addAll(Set.of("schema", "operation", "window_name", "played_character_id", "date_raw", "native_revision", "connection_generation", "pump_epoch", "thread_id", "game_version", "executable_sha256", "ticket_sequence")); BASE = Set.copyOf(fields); }
    private ArmyWindowCodec() { }
    /** Native hello/owner generation is positive; Driver lease generation is independent and may be zero.
     * Caller must verify both actual sources and the planning/action receipt guard. This never grants authority. */
    public static Observation decode(Kind kind, Operation operation, byte[] actualOriginalFrame, String actualRequestId, Context context, BigInteger actualNativeHelloGeneration, BigInteger actualDriverGeneration) {
        require(actualRequestId != null && !actualRequestId.isEmpty(), "original window request ID required"); UInt64.positive(actualNativeHelloGeneration); new UInt64(actualDriverGeneration);
        ObjectNode top = closed(parse(actualOriginalFrame), "type", "protocol_version", "request_id", "ok", "result", kind.ownerKey());
        equal(top.get("type"), "command_result"); require(i32(top.get("protocol_version")) == 1, "window Native protocol differs"); equal(top.get("request_id"), actualRequestId); yes(top.get("ok"));
        ObjectNode owner = object(top.get(kind.ownerKey())); require(names(owner).equals(OWNER), "window independent TOP owner exact shape differs"); equal(owner.get("request_id"), actualRequestId);
        for (String field : Set.of("ticket_sequence", "executor_started_sequence", "completed_sequence", "pump_epoch", "connection_generation")) positive(owner.get(field));
        range(owner.get("thread_id"), BigInteger.ONE, MAX32); i32(owner.get("date_raw"));
        require(owner.get("ticket_sequence").equals(owner.get("executor_started_sequence")) && owner.get("ticket_sequence").equals(owner.get("completed_sequence")), "window owner ticket was not independently started and completed");
        ObjectNode row = object(top.get("result")); var trace = new HashSet<>(BASE); trace.add(kind.trace + "_stage"); trace.add(kind.trace + "_exception_code");
        require(names(row).equals(BASE) || names(row).equals(trace), "missing, additional or partial fixed-window leaf fields");
        equal(row.get("operation"), operation.name().toLowerCase(java.util.Locale.ROOT)); equal(row.get("schema"), "ck3-" + kind.suffix + "-v1"); equal(row.get("window_name"), kind.window);
        equal(row.get("game_version"), "1.20.0.4"); require(text(row.get("executable_sha256")).equalsIgnoreCase(BUILD), "window exact native build differs");
        BOOLS.forEach(field -> bool(row.get(field))); TEXTS.forEach(field -> text(row.get(field))); require(kind.buttons.contains(text(row.get("button_name"))), "fixed window button differs");
        i32(row.get("played_character_id")); i32(row.get("date_raw")); for (String field : Set.of("native_revision", "connection_generation", "pump_epoch", "ticket_sequence")) u64(row.get(field)); range(row.get("thread_id"), BigInteger.ZERO, MAX32);
        equal(row.get("native_revision"), context.nativeRevision()); equal(row.get("connection_generation"), actualNativeHelloGeneration);
        for (String field : Set.of("request_id", "ticket_sequence", "pump_epoch", "thread_id", "date_raw", "connection_generation")) require(row.get(field).equals(owner.get(field)), "window leaf differs from independently captured TOP owner " + field);
        source(row, "root_observed", "window_present", "root_observation_source"); source(row, "post_observed", "post_window_present", "post_observation_source");
        boolean available = b(row,"available"), accepted = b(row,"accepted"), root = b(row,"root_observed"), present = b(row,"window_present"), visible = b(row,"effective_visible"), attempted = b(row,"dispatch_attempted"), invoked = b(row,"dispatch_invoked"), handled = b(row,"native_handled"), postPresent = b(row,"post_window_present"), postVisible = b(row,"post_effective_visible"), closed = b(row,"closure_verified");
        if (root || available || attempted) { equal(row.get("played_character_id"), context.playerId()); equal(row.get("date_raw"), context.dateRaw()); yes(row.get("paused")); }
        require((!visible || present) && (!postVisible || postPresent) && (!handled || invoked) && (!invoked || attempted), "window visibility/dispatch implication differs");
        require(!attempted || operation == Operation.CLOSE && root && b(row,"application_owner_thread_verified") && present && visible && !text(row.get("button_name")).isEmpty(), "window dispatch lacks qualified visible fixed target");
        if (row.has(kind.trace + "_stage")) {
            String stage = text(row.get(kind.trace + "_stage")); BigInteger code = range(row.get(kind.trace + "_exception_code"), BigInteger.ZERO, MAX32);
            boolean valid = switch (stage) { case "not_attempted" -> !attempted && !invoked && code.signum() == 0; case "preflight_rejected", "callback_entered" -> attempted && !invoked && code.signum() == 0; case "callback_returned" -> attempted && invoked && handled && code.signum() == 0; case "callback_exception" -> attempted && !invoked && code.signum() != 0; default -> false; };
            require(valid, "window callback stage contradicts actual dispatch");
        }
        String status = text(row.get("status"));
        if (available) {
            require(root && b(row,"post_observed") && b(row,"scope_unchanged") && b(row,"application_owner_thread_verified") && integer(row.get("pump_epoch")).signum() > 0 && integer(row.get("thread_id")).signum() > 0 && text(row.get("unavailable_reason")).isEmpty(), "available window lacks actual owner/post observation");
            if (operation == Operation.QUERY) require(status.equals(!present ? "absent" : visible ? "visible" : "hidden") && accepted && !attempted && !invoked && !handled && !closed && text(row.get("button_name")).isEmpty() && postPresent == present && postVisible == visible, "query differs from stable independent window observations");
            else if (status.equals("closed_verified")) require(accepted && closed && attempted && invoked && !(postPresent && postVisible), "window close is not independently post verified");
            else require(status.equals(!present ? "already_absent" : "already_hidden") && !visible && !accepted && !closed && !attempted && !invoked && !handled && text(row.get("button_name")).isEmpty() && postPresent == present && postVisible == visible, "window no-op differs from actual non-dispatch state");
        } else require(status.equals(attempted ? "verification_pending" : "unavailable") && !accepted && !closed && !text(row.get("unavailable_reason")).isBlank() && (operation != Operation.QUERY || !attempted), "unavailable window overclaims an outcome");
        ObjectNode normalized = row.deepCopy(); normalized.put("step", kind.step(operation)).put("backend_id", "native-headless").put("sdk_validation_schema", kind.suffix + "-source-v1").put("native_request_id", actualRequestId);
        ObjectNode sourceTop = top.deepCopy(); sourceTop.remove("result"); normalized.set("native_command_result", sourceTop);
        var frame = context.before().frame(); normalized.put("queried_snapshot_id", frame.snapshotId()).put("queried_revision", frame.revision()).put("queried_native_revision", context.nativeRevision()).put("queried_date_raw", context.dateRaw()).put("queried_actor_character_id", context.playerId()).put("queried_connection_generation", actualDriverGeneration);
        if (frame.episodeRunId() == null) normalized.putNull("queried_episode_run_id"); else normalized.put("queried_episode_run_id", frame.episodeRunId());
        return new Observation(kind, operation, normalized, row, owner);
    }
    /** Pure extraction from the same already validated/held Complete; no observation or native command. */
    public static BigInteger driverGeneration(Complete actual) {
        java.util.Objects.requireNonNull(actual);
        var diagnostics = OpportunityJson.object(actual.semantic().get("diagnostics"), "actual Driver diagnostics");
        BigInteger generation = OpportunityJson.integer(diagnostics.get("connection_generation"), "actual Driver connection generation");
        return new UInt64(generation).value();
    }
    private static boolean b(ObjectNode row, String field) { return bool(row.get(field)); }
    private static void source(ObjectNode row, String observed, String present, String field) {
        String source = text(row.get(field)); require(source.isEmpty() || SOURCES.contains(source), "unknown fixed-window observation source");
        require(!b(row,observed) || SOURCES.contains(source), "observed window lacks qualified source"); require(!b(row,observed) || b(row,present) || source.equals("guarded_top_level_and_complete_owner_tree"), "window absence lacks complete owner-tree negative observation");
    }
}
