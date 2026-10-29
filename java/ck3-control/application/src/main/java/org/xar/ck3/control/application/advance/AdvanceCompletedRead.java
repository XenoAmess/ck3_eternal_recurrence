package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Typed view of the sole original-compatible producer. Root verifies canonical membership under the same session first. */
public final class AdvanceCompletedRead {
    private final ActionReceipt receipt;
    private final BigInteger start,end;
    private final AdvanceClock.ProgressStatus progress;
    private final ObservationIdentity ending;
    private final ExactRef originalResult;
    private AdvanceCompletedRead(ActionReceipt receipt,BigInteger start,BigInteger end,AdvanceClock.ProgressStatus progress,ObservationIdentity ending,ExactRef originalResult){this.receipt=receipt;this.start=start;this.end=end;this.progress=progress;this.ending=ending;this.originalResult=originalResult;}
    /** UNKNOWN and control-only return before touching any archive. Reconciliation without the original full result stays absent. */
    public static Optional<AdvanceCompletedRead> read(ActionReceipt actualCanonical,ActionPorts.OutcomeArchive sameWriterArchive){
        Objects.requireNonNull(actualCanonical);Objects.requireNonNull(sameWriterArchive);
        if(actualCanonical.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED||actualCanonical.applied().isEmpty()||!LifeAdvanceComposite.accepts(actualCanonical.command().operation().value()))return Optional.empty();
        Optional<RawJson> original=AdvanceResult.compatibleResult(actualCanonical,sameWriterArchive);if(original.isEmpty())return Optional.empty();
        Obj body=DriverJson.object(original.orElseThrow().bytes(),RawJson.MAXIMUM_BYTES);BigInteger start=integer(body.get("starting_date_raw"),"starting_date_raw"),end=integer(body.get("ending_date_raw"),"ending_date_raw");
        String wire=text(body.get("progress_status"),"progress_status");AdvanceClock.ProgressStatus progress=AdvanceClock.ProgressStatus.valueOf(wire.toUpperCase(java.util.Locale.ROOT));require(AdvanceResult.progressStatus(progress).equals(wire),"advance progress spelling differs from sole producer");
        var effect=actualCanonical.applied().orElseThrow().observation();require(bool(body.get("paused"),"paused")&&effect.actual().contains(new ExpectedBoolean(new FieldKey("paused"),true))&&effect.actual().contains(new ExpectedText(new FieldKey("progress_status"),wire)),"advance result paused/progress differs from the actual applied effect");
        require(start.signum()>=0&&end.compareTo(start)>=0&&end.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"completed native calendar range regressed");
        return Optional.of(new AdvanceCompletedRead(actualCanonical,start,end,progress,effect.after(),sameWriterArchive.materialReferenceOf(original.orElseThrow())));
    }
    public ActionReceipt receipt(){return receipt;}public OperationKey step(){return receipt.command().operation();}
    public BigInteger startDateRaw(){return start;}public BigInteger endDateRaw(){return end;}
    public AdvanceClock.ProgressStatus progressStatus(){return progress;}public boolean paused(){return true;}
    public ObservationIdentity endingFrame(){return ending;}public ExactRef originalResultRef(){return originalResult;}
    /** Complete immutable semantic endpoint, never the Ready snapshot observed when the callback happens. */
    public AdvanceObservationPort.Frame endingFrame(LifeAdvanceEvidence.BoundFrameVerifier sameRootLifeReplay,ActionPorts.OutcomeArchive sameWriterArchive){return LifeAdvanceEvidence.endingFrame(receipt,sameWriterArchive,sameRootLifeReplay);}
}
