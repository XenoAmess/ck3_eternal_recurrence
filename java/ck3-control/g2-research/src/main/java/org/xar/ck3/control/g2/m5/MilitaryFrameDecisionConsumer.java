package org.xar.ck3.control.g2.m5;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Current;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Unknown;
import org.xar.ck3.control.wave3.planning.military.OrdinaryMilitaryConsumer;

/** Real caller composition after M5 HTTP: ordinary military reads and the existing all-domain shared reservation owner.
 * Neither this class nor a saved receipt may construct a replacement frame dispatcher.
 */
public final class MilitaryFrameDecisionConsumer {
    private MilitaryFrameDecisionConsumer() { }
    public record Consumption(OrdinaryMilitaryConsumer.Result military, M5FrameDispatcher.Dispatch sharedDispatch) {
        public Consumption { Objects.requireNonNull(military); Objects.requireNonNull(sharedDispatch); }
        public boolean formalActionReady() { return false; }
        public boolean authorizesCommandReplay() { return false; }
    }
    /** Obtain the existing typed current input inside the original owner monitor; no new native provider contract is invented here. */
    public static Consumption consumeCurrent(Supplier<OrdinaryMilitaryConsumer.Input> currentMilitaryInput,
            G2Request originalM5Request, G2Response response, M5FrameDispatcher existingFrameOwner) {
        Objects.requireNonNull(currentMilitaryInput); Objects.requireNonNull(existingFrameOwner);
        synchronized (existingFrameOwner) {
            OrdinaryMilitaryConsumer.Input current = Objects.requireNonNull(currentMilitaryInput.get(), "actual current input or explicit Unknown required");
            return consumeObserved(current, originalM5Request, response, existingFrameOwner);
        }
    }
    private static Consumption consumeObserved(OrdinaryMilitaryConsumer.Input militaryInput, G2Request originalM5Request,
                                               G2Response response, M5FrameDispatcher existingFrameOwner) {
        Objects.requireNonNull(militaryInput); Objects.requireNonNull(originalM5Request); Objects.requireNonNull(response); Objects.requireNonNull(existingFrameOwner);
        M5PayloadCodec.OperationRequest operation = M5PayloadCodec.decodeOperation(originalM5Request.payload().bytes());
        require(operation instanceof M5PayloadCodec.ContextRequest, "actual ordinary frame requires M5 decision context");
        OrdinaryMilitaryConsumer.Input boundInput = militaryInput;
        if (militaryInput.origin() instanceof Current current) {
            Obj snapshot = object(((M5PayloadCodec.ContextRequest) operation).context().intakeRequest().get("snapshot"), "actual original intake snapshot");
            var captured = current.snapshot().capture();
            boolean bound = current.source().machineId().equals(originalM5Request.source().machineId())
                    && current.source().buildVersion().equals(originalM5Request.source().exactBuild())
                    && new Text(captured.snapshotId()).equals(snapshot.get("snapshot_id"))
                    && new IntegerValue(captured.revision()).equals(snapshot.get("revision"))
                    && new IntegerValue(captured.nativeRevision()).equals(snapshot.get("native_revision"))
                    && new IntegerValue(BigInteger.valueOf(current.snapshot().dateRaw())).equals(snapshot.get("date_raw"))
                    && new Text(captured.episodeRunId()).equals(snapshot.get("episode_run_id"));
            Value diagnostics = snapshot.get("diagnostics");
            bound = bound && diagnostics instanceof Obj observed
                    && new IntegerValue(captured.connectionGeneration()).equals(observed.get("connection_generation"));
            if (!bound) boundInput = new OrdinaryMilitaryConsumer.Input(militaryInput.route(),
                    new Unknown("original M5 input lacks the independently qualified military source/frame binding"),
                    militaryInput.effectiveContactRows(), militaryInput.ownerCharacterId(), militaryInput.hostileScope(), militaryInput.effectiveHorizonHistory(), militaryInput.rollbackMemory());
        }
        OrdinaryMilitaryConsumer.Result military = OrdinaryMilitaryConsumer.plan(boundInput);
        // Full-strategy M5 analysis stays intact even when the independent military native input is unavailable.
        // The actual existing owner validates its original snapshot/commitments and re-evaluates under its lock.
        M5FrameDispatcher.Dispatch dispatch = M5ReservationConsumer.reserve(originalM5Request, response, existingFrameOwner);
        return new Consumption(military, dispatch);
    }
}
