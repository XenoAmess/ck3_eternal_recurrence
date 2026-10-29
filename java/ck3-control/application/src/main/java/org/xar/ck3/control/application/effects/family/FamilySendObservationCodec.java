package org.xar.ck3.control.application.effects.family;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Exact archive-reference wire contract. Decoding DATA performs no dispatch, read, source qualification or domain settlement. */
public final class FamilySendObservationCodec {
    public static final String SCHEMA = "xar.java.family-send-observation/v1";
    private static final Set<String> FIELDS = Set.of("schema", "profile", "action_id", "command_body_sha256",
            "original_request_id", "original_dispatch_ref", "prepared_request_ref", "before_frame", "after_frame",
            "before", "after", "source", "session_id", "before_storage_ref", "after_storage_ref",
            "complete_preparation", "native_pending_full_id", "definition_stable_hash", "actual");
    private FamilySendObservationCodec() { }
    /** References must already belong to the same immutable archive; encoding never creates an original. */
    public static ObjectNode encode(FamilySendObservation value, ActionPorts.OutcomeArchive archive) {
        java.util.Objects.requireNonNull(value); java.util.Objects.requireNonNull(archive);
        ObjectNode result = StrictJson.object().put("schema", SCHEMA).put("profile", value.profile().name())
                .put("action_id", value.actionId()).put("command_body_sha256", value.commandBodySha256())
                .put("original_request_id", value.originalRequestId()).put("session_id", value.sessionId())
                .put("native_pending_full_id", value.nativePendingFullId()).put("definition_stable_hash", value.definitionStableHash());
        result.set("original_dispatch_ref", value.originalDispatchRef().toJson());
        result.set("prepared_request_ref", value.preparedRequestRef().toJson());
        result.set("before_frame", frame(value.beforeFrame())); result.set("after_frame", frame(value.afterFrame()));
        result.set("before", ProposalLifecycleCodec.observation(value.before())); result.set("after", ProposalLifecycleCodec.observation(value.after()));
        result.set("source", ProposalLifecycleCodec.source(value.source()));
        ExactRef beforeRead = readReference(value.beforeStorage(), archive), afterRead = readReference(value.afterStorage(), archive);
        StrictJson.require(!beforeRead.equals(afterRead) && value.completePreparation().contains(beforeRead),
                "both distinct original storage queries and their preparation baseline must already be archived");
        result.set("before_storage_ref", beforeRead.toJson());
        result.set("after_storage_ref", afterRead.toJson());
        var preparation = result.putArray("complete_preparation"); value.completePreparation().forEach(ref -> preparation.add(ref.toJson()));
        result.set("actual", ProposalLifecycleCodec.encodeValues(value.actual())); return result;
    }
    public static FamilySendObservation decode(JsonNode input, ActionPorts.OutcomeArchive archive) {
        java.util.Objects.requireNonNull(archive); ObjectNode value = StrictJson.object(input, FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(value.get("schema"))), "exact typed family-send observation schema required");
        JsonNode raw = value.get("complete_preparation");
        StrictJson.require(raw.isArray() && !raw.isEmpty() && raw.size() <= 32, "bounded complete original preparation refs required");
        var preparation = new ArrayList<ExactRef>(); raw.forEach(ref -> preparation.add(ExactRef.fromJson(ref)));
        var profile = FamilySendObservation.Profile.valueOf(StrictJson.text(value.get("profile")));
        long pending = StrictJson.integer(value.get("native_pending_full_id"), 0, 0xFFFF_FFFEL);
        long definition = StrictJson.integer(value.get("definition_stable_hash"), 0, 0xFFFF_FFFFL);
        var actual = ProposalLifecycleCodec.values(value.get("actual"));
        FamilySendObservation.requireSendOnlyValues(profile, pending, actual);
        String actionId = StrictJson.text(value.get("action_id")), digest = StrictJson.text(value.get("command_body_sha256")),
                requestId = StrictJson.text(value.get("original_request_id")), session = StrictJson.text(value.get("session_id"));
        StrictJson.require(digest.matches("[a-f0-9]{64}") && new java.util.HashSet<>(preparation).size() == preparation.size(),
                "canonical original digest and unique complete preparation refs required");
        var dispatch = ExactRef.fromJson(value.get("original_dispatch_ref")); var prepared = ExactRef.fromJson(value.get("prepared_request_ref"));
        var beforeFrame = frame(value.get("before_frame")); var afterFrame = frame(value.get("after_frame"));
        var before = ProposalLifecycleCodec.decodeObservation(value.get("before")); var after = ProposalLifecycleCodec.decodeObservation(value.get("after"));
        var source = G2Wire.source(value.get("source"));
        var beforeRead = ExactRef.fromJson(value.get("before_storage_ref")); var afterRead = ExactRef.fromJson(value.get("after_storage_ref"));
        for (ExactRef ref : preparation) requireNonempty(ref);
        for (ExactRef ref : java.util.List.of(dispatch, prepared, beforeFrame.nativeFrame(), beforeFrame.driverFacts(),
                afterFrame.nativeFrame(), afterFrame.driverFacts(), beforeRead, afterRead)) requireNonempty(ref);
        StrictJson.require(beforeRead.bytes() > 0 && afterRead.bytes() > 0 && !beforeRead.equals(afterRead)
                && preparation.contains(beforeRead), "both distinct original storage query refs and their preparation baseline are required");
        var originalBefore = archive.loadRead(beforeRead); var originalAfter = archive.loadRead(afterRead);
        StrictJson.require(beforeRead.equals(archive.readReferenceOf(originalBefore))
                && afterRead.equals(archive.readReferenceOf(originalAfter)),
                "family storage original ref changed its canonical archive locator or content identity");
        return new FamilySendObservation(profile, actionId, digest, requestId, dispatch, prepared, beforeFrame, afterFrame,
                before, after, source, session, originalBefore, originalAfter, preparation, pending, definition, actual);
    }
    /** Archive lookup remains read-only and may never silently substitute another original receipt. */
    private static ExactRef readReference(PlanningReadReceipt read, ActionPorts.OutcomeArchive archive) {
        ExactRef ref = archive.readReferenceOf(read); requireNonempty(ref);
        StrictJson.require(read.equals(archive.loadRead(ref)), "family storage locator did not resolve its exact original receipt");
        return ref;
    }
    private static void requireNonempty(ExactRef ref) {
        StrictJson.require(ref.bytes() > 0, "nonempty actual original archive ref required");
    }
    private static ObjectNode frame(NativeEffectEvidence.FrameBasis value) {
        ObjectNode result = StrictJson.object(); result.set("native_frame", value.nativeFrame().toJson());
        result.set("driver_facts", value.driverFacts().toJson()); return result;
    }
    private static NativeEffectEvidence.FrameBasis frame(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("native_frame", "driver_facts"));
        return new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(row.get("native_frame")), ExactRef.fromJson(row.get("driver_facts")));
    }
}

