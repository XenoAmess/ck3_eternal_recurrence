package org.xar.ck3.control.application.advance;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Read-only view of the one held transport and the complete production semantic assembler. */
public interface AdvanceObservationPort {
    Frame current(ActionCommand parent, Instant deadline);
    Frame next(ActionCommand parent, ObservationIdentity after, Instant deadline);

    /** Original evidence must be preserved before returning. No inferred public revisions or episode IDs. */
    record Frame(ObservationIdentity identity, G2Source source, String sessionId,
            OpportunityJson.Obj semantic, ObservationProvenance provenance, Instant observedAt, ExactRef originalEvidence) {
        public Frame {
            Objects.requireNonNull(identity); Objects.requireNonNull(source); StrictJson.text(sessionId);
            Objects.requireNonNull(semantic); Objects.requireNonNull(provenance); Objects.requireNonNull(observedAt);
            Objects.requireNonNull(originalEvidence); StrictJson.require(originalEvidence.bytes() > 0, "actual original native frame evidence required");
            provenance.validate(identity, originalEvidence);
            StrictJson.require(identity.machineId().equals(source.machineId()), "frame source machine differs");
            // The assembler validates the original full state at its native boundary. The proposal
            // parser's 128 KiB request limit is not a limit on a complete native semantic frame.
            StrictJson.require(identity.frame().snapshotId().equals(OpportunityJson.text(semantic.get("snapshot_id"), "snapshot_id"))
                    && identity.frame().revision().equals(OpportunityJson.integer(semantic.get("revision"), "revision"))
                    && identity.frame().identity().nativeRevision().equals(OpportunityJson.integer(semantic.get("native_revision"), "native_revision"))
                    && identity.frame().identity().dateRaw().equals(OpportunityJson.integer(semantic.get("date_raw"), "date_raw"))
                    && identity.frame().episodeRunId().equals(OpportunityJson.text(semantic.get("episode_run_id"), "episode_run_id"))
                    && identity.frame().identity().player().equals(OpportunityJson.integer(
                        OpportunityJson.object(semantic.get("played_character"), "played_character").get("character_id"), "character_id")),
                    "complete semantic frame differs from its actual observation identity");
            for (String key : List.of("paused", "map_ready")) OpportunityJson.bool(semantic.get(key), key);
            int speed = OpportunityJson.integer(semantic.get("speed"), "speed").intValueExact();
            StrictJson.require(speed >= 1 && speed <= 5, "native speed must be 1..5");
            for (String key : List.of("active_event", "pending_character_interaction", "one_life_terminal_reason"))
                StrictJson.require(semantic.members().containsKey(key), "missing is not explicit null: " + key);
            OpportunityJson.array(semantic.get("active_wars"), "active_wars");
            OpportunityJson.array(semantic.get("player_armies"), "player_armies");
            OpportunityJson.object(semantic.get("diagnostics"), "diagnostics");
        }
        /** A genuine request-backed producer may pass its original query ID. A push never uses this constructor. */
        public Frame(ObservationIdentity identity, G2Source source, String sessionId,
                OpportunityJson.Obj semantic, String queryRequestId, Instant observedAt, ExactRef originalEvidence) {
            this(identity, source, sessionId, semantic, new ObservationProvenance.Query(queryRequestId), observedAt, originalEvidence);
        }
    }
}
