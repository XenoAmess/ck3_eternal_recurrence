package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.warexit.WarExitReads;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.WarEntryAssessmentCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Narrow actual4 full-power consumer of the sole installed Army forecast decoder. No Native call or read registry. */
public final class RootWarPowerReads {
    public static final int MAX_NATIVE_PAYLOAD_BYTES = 1 << 20;
    private static final String ACTUAL4_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private RootWarPowerReads() { }

    public static WarEntryAssessmentCodec.Observed requireCurrentPayload(
            PlanningRequest request, WarExitReads.Key key, JsonNode payload) {
        Objects.requireNonNull(request); Objects.requireNonNull(key); Objects.requireNonNull(payload);
        StrictJson.require(key.kind() == WarExitReads.Kind.POWER && key.subject() > 0,
                "one actual full-power target required");
        var identity = request.before().frame().identity();
        var observed = WarEntryAssessmentCodec.normalize(payload,
                new WarEntryAssessmentCodec.Expected(List.of(key.subject()), identity.player(),
                        identity.nativeRevision(), identity.dateRaw()));
        StrictJson.require(observed.build().version().equals("1.20.0.4")
                        && observed.build().sha256().equalsIgnoreCase(ACTUAL4_SHA),
                "actual4 full power cannot borrow another build's result provenance");
        return observed;
    }

    /** The underlying owner has already redecoded the original receipt and published its exact current envelope. */
    public static WarEntryAssessmentCodec.Observed requireCurrentEnvelope(
            PlanningRequest request, WarExitReads.Key key, ObjectNode envelope) {
        StrictJson.object(envelope, Set.of("step", "accepted", "status", "query_sequence", "war_entry_assessments",
                "target_scopes", "queried_snapshot_id", "queried_revision", "queried_native_revision",
                "queried_episode_run_id", "queried_connection_generation"));
        StrictJson.require(StrictJson.text(envelope.get("step")).equals(WarExitReads.step(key))
                        && envelope.get("accepted").isBoolean() && envelope.get("accepted").booleanValue()
                        && StrictJson.text(envelope.get("status")).equals("available"),
                "actual4 power envelope is not the original accepted read");
        StrictJson.integer(envelope.get("query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX);
        var frame = request.before().frame();
        StrictJson.require(StrictJson.text(envelope.get("queried_snapshot_id")).equals(frame.snapshotId())
                        && StrictJson.integer(envelope.get("queried_revision"), BigInteger.ZERO, StrictJson.UINT64_MAX).equals(frame.revision())
                        && StrictJson.integer(envelope.get("queried_native_revision"), BigInteger.ZERO, StrictJson.UINT64_MAX).equals(frame.identity().nativeRevision())
                        && StrictJson.text(envelope.get("queried_episode_run_id")).equals(frame.episodeRunId()),
                "actual4 power publication crossed its original Driver/native/episode frame");
        var snapshot = OpportunityJson.toNode(request.observations().snapshot());
        if (!(snapshot.get("diagnostics") instanceof ObjectNode diagnostics))
            throw new IllegalArgumentException("actual full-power native diagnostics missing");
        StrictJson.require(StrictJson.integer(envelope.get("queried_connection_generation"), BigInteger.ONE, StrictJson.UINT64_MAX)
                        .equals(StrictJson.integer(diagnostics.get("connection_generation"), BigInteger.ONE, StrictJson.UINT64_MAX)),
                "actual4 power publication crossed its original connection generation");
        var expectedScopes = WarEntryAssessmentCodec.targetScopes(snapshot, List.of(key.subject()));
        StrictJson.require(envelope.get("target_scopes").equals(expectedScopes.toNativeJson()),
                "actual4 power selected target no longer has its complete original scope");
        return requireCurrentPayload(request, key, envelope.get("war_entry_assessments"));
    }
}
