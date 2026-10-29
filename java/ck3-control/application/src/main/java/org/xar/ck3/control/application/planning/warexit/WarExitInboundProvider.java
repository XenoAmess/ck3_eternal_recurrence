package org.xar.ck3.control.application.planning.warexit;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;

/** Strict same-frame observations for known inbound peace. This supplies no material effect preview. */
public final class WarExitInboundProvider {
    public enum Reason { ACTIVE_WAR_ABSENT, NO_UNIQUE_CURRENT_OPTIONS }
    public sealed interface Result permits Current, NeedRead, Unavailable { ObservationIdentity before(); int warId(); }
    public record Current(ObservationIdentity before, int warId, WarExitEvidence.War war,
            WarExitEvidence.Options options, NativeTerminationOptions validated) implements Result {
        public Current {
            Objects.requireNonNull(before); Objects.requireNonNull(war); Objects.requireNonNull(options);
            Objects.requireNonNull(validated);
            require(warId == war.warId() && warId == options.warId() && warId == validated.warId(), "inbound WarID differs");
        }
    }
    public record NeedRead(ObservationIdentity before, int warId, OperationKey query,
            boolean reachable, Reason reason) implements Result {
        public NeedRead { Objects.requireNonNull(before); Objects.requireNonNull(query); Objects.requireNonNull(reason);
            require(warId > 0 && query.value().equals("query-war-termination-options-" + warId)
                    && reason == Reason.NO_UNIQUE_CURRENT_OPTIONS, "exact inbound options query required"); }
    }
    public record Unavailable(ObservationIdentity before, int warId, Reason reason) implements Result {
        public Unavailable { Objects.requireNonNull(before); require(warId > 0 && reason == Reason.ACTIVE_WAR_ABSENT,
                "explicit absent active war required"); }
    }
    private WarExitInboundProvider() { }

    public static Result project(PlanningRequest request, int warId) {
        Objects.requireNonNull(request);
        return project(request.before(), WarExitEvidence.snapshot(request), request.observations().actionSteps(), warId);
    }

    /** JSON is confined to this validated input boundary; consumers receive the shared immutable records. */
    public static Result project(ObservationIdentity before, ObjectNode snapshot, Set<OperationKey> availableSteps, int warId) {
        Objects.requireNonNull(before); Objects.requireNonNull(snapshot); Objects.requireNonNull(availableSteps);
        require(warId > 0, "positive original inbound WarID required");
        var frame = before.frame(); var actor = WarExitEvidence.object(snapshot.get("played_character"), "current player");
        require(text(snapshot.get("snapshot_id"), frame.snapshotId()) && text(snapshot.get("episode_run_id"), frame.episodeRunId())
                && integer(snapshot.get("revision"), frame.revision())
                && integer(snapshot.get("native_revision"), frame.identity().nativeRevision())
                && integer(snapshot.get("date_raw"), frame.identity().dateRaw())
                && integer(actor.get("character_id"), frame.identity().player()), "inbound snapshot crossed the actual frame");
        ObjectNode diagnostics = WarExitEvidence.object(snapshot.get("diagnostics"), "native diagnostics");
        require(integer(diagnostics.get("bridge_pid"), BigInteger.valueOf(before.game().pid())), "inbound Game PID differs");
        // Validate the source connection even when no row is presently available; missing is not connection zero.
        org.xar.ck3.control.contracts.StrictJson.integer(diagnostics.get("connection_generation"), BigInteger.ONE,
                org.xar.ck3.control.contracts.StrictJson.UINT64_MAX);
        List<WarExitEvidence.War> wars = WarExitEvidence.wars(snapshot).stream().filter(value -> value.warId() == warId).toList();
        if (wars.isEmpty()) return new Unavailable(before, warId, Reason.ACTIVE_WAR_ABSENT);
        JsonNode rows = snapshot.get("war_termination_options");
        List<ObjectNode> current = new ArrayList<>();
        if (rows != null && !rows.isNull()) {
            require(rows.isArray(), "native termination options must be an array");
            for (JsonNode value : rows) {
                ObjectNode row = WarExitEvidence.object(value, "termination row");
                int rowId = WarExitEvidence.positive(row.get("war_id"));
                if (rowId == warId) {
                    // A stale, well-formed binding may require a read; wrong JSON types are rejected first.
                    NativeTerminationOptions.fromCache(row, warId);
                    if (WarExitEvidence.sameFrame(snapshot, row, "episode_run_id")) current.add(row);
                }
            }
        }
        if (current.size() != 1) {
            OperationKey query = new OperationKey("query-war-termination-options-" + warId);
            return new NeedRead(before, warId, query, availableSteps.contains(query), Reason.NO_UNIQUE_CURRENT_OPTIONS);
        }
        ObjectNode selected = current.getFirst();
        require(text(selected.get("source"), "native"), "inbound terms require explicit native query provenance");
        NativeTerminationOptions validated = NativeTerminationOptions.fromCache(selected, warId);
        // The original helper refuses every duplicate WarID. Supply precisely the unique CURRENT row,
        // retaining stale rows in the caller-owned snapshot and history unchanged.
        ObjectNode narrowed = snapshot.deepCopy(); narrowed.putArray("war_termination_options").add(selected.deepCopy());
        WarExitEvidence.Options options = WarExitEvidence.currentOptions(narrowed, warId).orElseThrow();
        WarExitEvidence.War war = wars.getFirst();
        require(war.playerSide() == options.playerSide() && war.primaryLeader() == options.primaryLeader()
                && war.score().filter(score -> score == options.score()).isPresent(), "inbound options differ from the active war");
        return new Current(before, warId, war, options, validated);
    }

    private static boolean integer(JsonNode value, BigInteger expected) {
        return value != null && value.isIntegralNumber() && value.bigIntegerValue().equals(expected);
    }
    private static boolean text(JsonNode value, String expected) {
        return value != null && value.isTextual() && expected.equals(value.textValue());
    }
}
