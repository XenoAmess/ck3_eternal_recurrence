package org.xar.ck3.control.application.lifecycle;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Full assembler view. Missing/dead/changed native player is preserved without inventing an ObservationIdentity. */
public interface LifecycleObservationPort {
    Snapshot current(ActionCommand parent, Instant deadline) throws InterruptedException;
    Snapshot next(ActionCommand parent, Snapshot previous, Instant deadline) throws InterruptedException;
    record Snapshot(ObservedFrame actual, G2Source source, OpportunityJson.Obj semantic,
            DriverSnapshotFacts.Known facts, ExactRef originalEvidence) {
        public Snapshot {
            Objects.requireNonNull(actual); Objects.requireNonNull(source); Objects.requireNonNull(semantic);
            Objects.requireNonNull(facts); Objects.requireNonNull(originalEvidence);
            StrictJson.require(source.machineId().equals(actual.session().machineId())
                    && originalEvidence.bytes()==actual.originalPacket().length
                    && originalEvidence.sha256().equals(LifecycleJson.sha(actual.originalPacket()))
                    && actual.snapshotId().equals(OpportunityJson.text(semantic.get("snapshot_id"),"snapshot_id"))
                    && actual.nativeRevision().equals(OpportunityJson.integer(semantic.get("native_revision"),"native_revision")),
                    "same original native packet/source/frame evidence required");
            StrictJson.require(facts.stamp().game().equals(actual.session().game())
                    && facts.driver().session().episodeRunId().equals(OpportunityJson.text(semantic.get("episode_run_id"),"episode_run_id")),
                    "semantic projection crossed actual Game/Driver episode facts");
            for (String key : java.util.List.of("one_life_terminal_reason","succession_reconciliation","one_life_settlement"))
                StrictJson.require(semantic.members().containsKey(key),"missing is not null: "+key);
        }
        public BigInteger dateRaw() { return OpportunityJson.integer(semantic.get("date_raw"),"date_raw"); }
        public BigInteger revision() { return OpportunityJson.integer(semantic.get("revision"),"revision"); }
        public boolean paused() { return OpportunityJson.bool(semantic.get("paused"),"paused"); }
        public boolean mapReady() { return OpportunityJson.bool(semantic.get("map_ready"),"map_ready"); }
    }
}
