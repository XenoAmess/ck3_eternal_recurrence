package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Implementation-aware DATA witness for the actual private static
 * OrdinaryCycleTransitions.isFullySavedFinishedBatch. It invokes the real helper
 * and the real private parseState via reflection only. No live authority, writer,
 * Native, Pin, or external artifact is used.
 */
final class FullySavedFinishedRecovery308Test {
    private static final String MACHINE = "witness-machine";
    private static final String SESSION = "witness-session";
    private static final String BATCH = "witness-batch";
    private static final String HEAD_REF = "head-ref";
    private static final String PAIR_REF = "pair-ref";
    private static final String STATE_SCHEMA = "xar.java-ordinary-cycle-state/v2";
    private static final String PAIR_SCHEMA = "xar.java-checkpoint-pair/v1";

    @Test void actualPureHelperAcceptsCleanProfileAndRejectsFiniteMutations() throws Throwable {
        var clean = cleanState();
        var owner = ownerFor(clean);
        var branch = parseState(clean);
        assertTrue(invokeIsFullySavedFinishedBatch(clean, owner, branch), "clean fully-saved finished profile must satisfy the actual pure helper");

        var mutations = new TreeSet<String>();
        mutations.add("wrong-boundary");
        mutations.add("non-running");
        mutations.add("wrong-owner");
        mutations.add("pending-receipt");
        mutations.add("absent-head");
        mutations.add("completed-mismatch");
        mutations.add("saved-state-mismatch");
        mutations.add("missing-pair");

        for (var mutation : mutations) {
            var state = mutate(clean, mutation);
            var mutatedOwner = ownerFor(state);
            var mutatedBranch = parseState(state);
            assertFalse(invokeIsFullySavedFinishedBatch(state, mutatedOwner, mutatedBranch),
                    "actual pure helper must reject mutation: " + mutation);
        }
    }

    private static ContinuityState cleanState() {
        ObjectNode row = StrictJson.object();
        row.put("schema", "root.ck3.continuity-window/v1");
        row.put("machine_id", MACHINE);
        row.put("sequence", 1);
        row.put("status", "running");
        row.put("window_id", 1);
        row.put("start_date_raw", 0);
        row.put("target_date_raw", 24);
        row.put("target_days", 1);
        row.put("last_settled_cycles", 22);
        row.put("last_settled_date_raw", 0);
        row.put("last_event_identity", "0000000000000000000000000000000000000000000000000000000000000000");

        ObjectNode boundary = StrictJson.object();
        boundary.put("evidence_id", BATCH + ":BATCH_FINISHED");
        boundary.put("batch_id", BATCH);
        boundary.put("boundary", "BATCH_FINISHED");
        boundary.set("session", sessionJson());
        row.set(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD, boundary);

        ObjectNode cycle = StrictJson.object();
        cycle.put("schema", STATE_SCHEMA);
        cycle.set("session", sessionJson());
        cycle.put("basis_cycles", 0);
        cycle.put("completed_cycles", 22);
        cycle.set("head", refJson(HEAD_REF));
        cycle.putNull("pending_receipt");
        cycle.putNull("retained_legacy_pending_digest");
        cycle.putNull("origin_frame");
        cycle.putNull("episode_origin");
        row.set(WriterContracts.ORDINARY_CYCLE_FIELD, cycle);

        ObjectNode saved = StrictJson.object();
        saved.set("pair", pairJson());
        saved.set("state", cycle.deepCopy());
        row.set(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD, saved);

        return ContinuityState.fromJson(row, MACHINE);
    }

    private static ContinuityState mutate(ContinuityState clean, String mutation) {
        ObjectNode row = clean.toJson().deepCopy();
        switch (mutation) {
            case "wrong-boundary":
                ((ObjectNode)row.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD)).put("boundary", "BATCH_INTERRUPTED");
                break;
            case "non-running":
                row.put("status", "repair_required");
                break;
            case "wrong-owner":
                ((ObjectNode)((ObjectNode)row.get(WriterContracts.ORDINARY_CYCLE_FIELD)).get("session")).put("session_id", "other-session");
                break;
            case "pending-receipt":
                ((ObjectNode)row.get(WriterContracts.ORDINARY_CYCLE_FIELD)).set("pending_receipt", refJson("pending-ref"));
                break;
            case "absent-head":
                ((ObjectNode)row.get(WriterContracts.ORDINARY_CYCLE_FIELD)).putNull("head");
                break;
            case "completed-mismatch":
                ((ObjectNode)row.get(WriterContracts.ORDINARY_CYCLE_FIELD)).put("completed_cycles", 21);
                break;
            case "saved-state-mismatch":
                ((ObjectNode)((ObjectNode)row.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD)).get("state")).set("head", refJson("other-head"));
                break;
            case "missing-pair":
                ((ObjectNode)row.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD)).putNull("pair");
                break;
            default:
                throw new AssertionError("unknown mutation");
        }
        return ContinuityState.fromJson(row, MACHINE);
    }

    private static SessionIdentity ownerFor(ContinuityState state) {
        var session = state.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD).get("session");
        return new SessionIdentity(
                StrictJson.text(session.get("machine_id")),
                GameGeneration.fromJson(session.get("game")),
                StrictJson.text(session.get("session_id"))
        );
    }

    private static ObjectNode sessionJson() {
        ObjectNode row = StrictJson.object();
        row.put("machine_id", MACHINE);
        row.set("game", gameJson());
        row.put("session_id", SESSION);
        return row;
    }

    private static ObjectNode gameJson() {
        ObjectNode row = StrictJson.object();
        row.put("pid", 1);
        row.put("creation_filetime", "1");
        return row;
    }

    private static ObjectNode refJson(String path) {
        ObjectNode row = StrictJson.object();
        row.put("path", path);
        row.put("bytes", 1);
        row.put("sha256", "0000000000000000000000000000000000000000000000000000000000000000");
        return row;
    }

    private static ObjectNode pairJson() {
        ObjectNode row = StrictJson.object();
        row.put("schema", PAIR_SCHEMA);
        row.set("save", fileWitnessJson("save-ref"));
        row.set("driver", fileWitnessJson("driver-ref"));
        row.set("frame", frameJson());
        row.put("lineage_id", "witness-lineage");
        row.put("history_index", 1);
        row.put("save_action_id", "witness-save");
        row.set("native_ack_ref", refJson("ack-ref"));
        row.put("observed_at_utc", "2020-01-01T00:00:00Z");
        return row;
    }

    private static ObjectNode fileWitnessJson(String path) {
        ObjectNode row = StrictJson.object();
        row.set("ref", refJson(path));
        row.put("identity_schema", "xar.file-stat-identity.os-ns-decimal.v1");
        row.set("identity", identityJson());
        return row;
    }

    private static ObjectNode identityJson() {
        ObjectNode row = StrictJson.object();
        row.put("bytes", 1);
        row.put("file_id", "1");
        row.put("mtime_ns", "1");
        return row;
    }

    private static ObjectNode frameJson() {
        ObjectNode row = StrictJson.object();
        row.put("machine_id", MACHINE);
        row.set("game", gameJson());
        row.set("frame", frameIdentityJson());
        row.put("observation_version", 3);
        return row;
    }

    private static ObjectNode frameIdentityJson() {
        ObjectNode row = StrictJson.object();
        row.put("date_raw", "0");
        row.put("episode_run_id", "witness-run");
        row.put("native_revision", "1");
        row.put("played_character_id", "1");
        row.put("revision", "1");
        row.put("snapshot_id", "native:1");
        return row;
    }

    private static boolean invokeIsFullySavedFinishedBatch(ContinuityState state, SessionIdentity owner, Object branch) throws Throwable {
        var method = OrdinaryCycleTransitions.class.getDeclaredMethod("isFullySavedFinishedBatch", ContinuityState.class, SessionIdentity.class, branch.getClass());
        method.setAccessible(true);
        try {
            var result = method.invoke(null, state, owner, branch);
            if (!(result instanceof Boolean)) throw new ClassCastException("expected Boolean result");
            return (Boolean)result;
        } catch (InvocationTargetException failure) {
            throw failure.getCause();
        }
    }

    private static Object parseState(ContinuityState state) throws Throwable {
        var method = OrdinaryCycleTransitions.class.getDeclaredMethod("parseState", JsonNode.class);
        method.setAccessible(true);
        try {
            return method.invoke(null, state.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD));
        } catch (InvocationTargetException failure) {
            throw failure.getCause();
        }
    }
}