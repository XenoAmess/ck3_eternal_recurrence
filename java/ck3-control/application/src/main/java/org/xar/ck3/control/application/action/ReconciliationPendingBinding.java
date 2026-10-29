package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Read-only original pending membership and immutable evidence binding.
 * This class neither dispatches nor settles a request and never creates archive material.
 * Live native/source semantics and old-guard manifest-to-Driver verification belong to readiness.
 */
public final class ReconciliationPendingBinding {
    public enum Mode { LIVE_PENDING, HISTORICAL_READ }
    /** Immutable owned bytes only. This DATA record supplies no writer, history or dispatch qualification. */
    public record DriverMaterial(ExactRef reference,byte[] bytes) {
        public DriverMaterial {
            Objects.requireNonNull(reference);Objects.requireNonNull(bytes);bytes=bytes.clone();
            if(reference.bytes()<1||reference.bytes()>WriterContracts.MAX_PIN_BYTES||reference.bytes()!=bytes.length
                    ||!reference.sha256().equals(ActionCodec.sha256(bytes)))throw new IllegalArgumentException("exact owned full Driver bytes/SHA required");
        }
        @Override public byte[] bytes(){return bytes.clone();}
        @Override public boolean equals(Object other){return other instanceof DriverMaterial value&&reference.equals(value.reference)&&Arrays.equals(bytes,value.bytes);}
        @Override public int hashCode(){return Objects.hash(reference,Arrays.hashCode(bytes));}
    }
    /** Original typed inputs only. The private installed Root provider must reverify actual Session/archive/source/event custody. */
    public record HistoryContext(ContinuityStorePort.Session session,WriterContracts.Head head,ActionReceipt original,
            ActionState.Attempt attempt,ExactRef receiptReference,ExactRef recordReference,ReconciliationIdentity identity,
            Mode mode,DriverMaterial beforeDriver,DriverMaterial currentDriver,WriterContracts.Head targetHead) {
        public HistoryContext {
            Objects.requireNonNull(session);Objects.requireNonNull(head);Objects.requireNonNull(original);Objects.requireNonNull(attempt);
            Objects.requireNonNull(receiptReference);Objects.requireNonNull(recordReference);Objects.requireNonNull(identity);Objects.requireNonNull(mode);
            Objects.requireNonNull(beforeDriver);Objects.requireNonNull(currentDriver);Objects.requireNonNull(targetHead);
            var point=identity.historyPoint().orElseThrow(()->new IllegalArgumentException("actual history target point required"));
            StrictJson.require(identity.driverRelation()==ReconciliationIdentity.DriverRelation.HISTORY_APPEND
                    &&!Arrays.equals(beforeDriver.bytes(),currentDriver.bytes())&&attempt.equals(ReconciliationIdentity.primitiveAttempt(original))
                    &&receiptReference.equals(identity.pending().originalReceipt())&&recordReference.bytes()>0
                    &&beforeDriver.reference().equals(identity.pending().originalBeforeDriver())
                    &&currentDriver.reference().equals(identity.evidence().currentOriginalDriver())
                    &&original.command().actionId().equals(identity.pending().actionId())&&original.bodySha256().equals(identity.pending().bodySha256())
                    &&attempt.requestId().equals(identity.pending().requestId())&&point.sequence()==targetHead.state().sequence()&&point.digest().equals(targetHead.digest())
                    &&head.state().machineId().equals(identity.factual().machineId())&&targetHead.state().machineId().equals(head.state().machineId()),
                    "history qualification inputs changed their exact original pending/Driver/target binding");
        }
    }
    @FunctionalInterface public interface HistoryQualification {
        /** Only the actual private Root implementation may qualify the one original unresolved-action history extension. */
        void require(HistoryContext actual)throws IOException;
        static HistoryQualification unavailable(){return DENY_HISTORY;}
    }
    private static final HistoryQualification DENY_HISTORY=actual->{throw new IOException("actual private unresolved-action history qualification is unavailable");};
    private final ContinuityStorePort store;
    private final ActionPorts.OutcomeArchive archive;
    private final org.xar.ck3.control.application.effects.OriginalEvidencePort originals;
    private final HistoryQualification historyQualification;
    public ReconciliationPendingBinding(ContinuityStorePort store,ActionPorts.OutcomeArchive archive,
            org.xar.ck3.control.application.effects.OriginalEvidencePort originals){
        this(store,archive,originals,HistoryQualification.unavailable());
    }
    public ReconciliationPendingBinding(ContinuityStorePort store,ActionPorts.OutcomeArchive archive,
            org.xar.ck3.control.application.effects.OriginalEvidencePort originals,HistoryQualification historyQualification){
        this.store=Objects.requireNonNull(store);this.archive=Objects.requireNonNull(archive);this.originals=Objects.requireNonNull(originals);
        this.historyQualification=Objects.requireNonNull(historyQualification);
    }
    public HistoryQualification historyQualification(){return historyQualification;}
    /** Exact installed owners only. This identity check supplies no history qualification or epoch authority. */
    public void requireOwner(ContinuityStorePort actualStore,ActionPorts.OutcomeArchive actualArchive)throws IOException {
        require(store==actualStore&&archive==actualArchive,"pending binder belongs to another actual writer/archive owner");
    }
    /** Must run before the fresh query. Returns the one canonical original primitive Attempt only. */
    public ActionState.Attempt requirePending(ContinuityStorePort.Session borrowed,ActionReceipt original)throws IOException{
        return inSession(borrowed,bound->{
            WriterContracts.Head actual=borrowed.head();List<WriterContracts.Pin> pins=new ArrayList<>();
            Canonical canonical=canonical(borrowed,actual,bound,original,pins,false);
            finish(borrowed,actual,pins);return canonical.attempt();
        });
    }
    /** Revalidates historical/current membership and original byte custody after fresh evidence collection. */
    public void verify(ContinuityStorePort.Session borrowed,ReconciliationIdentity identity)throws IOException{
        verify(borrowed,identity,false);
    }
    /** Archived read provenance only; never use historical acceptance to acquire a fresh query scope. */
    public void verifyHistorical(ContinuityStorePort.Session borrowed,ReconciliationIdentity identity)throws IOException{
        verify(borrowed,identity,true);
    }
    private void verify(ContinuityStorePort.Session borrowed,ReconciliationIdentity identity,boolean historical)throws IOException{
        Objects.requireNonNull(identity);
        inSession(borrowed,bound->{
            WriterContracts.Head actual=borrowed.head();List<WriterContracts.Pin> pins=new ArrayList<>();
            // Cold verification must stop at the original immutable query target. A future settled receipt
            // may itself contain this reconciliation read; reopening it here would recurse into this proof.
            WriterContracts.Head canonicalHead=actual;
            boolean originalHistoryTarget=historical&&identity.driverRelation()==ReconciliationIdentity.DriverRelation.HISTORY_APPEND;
            if(originalHistoryTarget){
                var point=identity.historyPoint().orElseThrow();
                require(point.sequence()<=actual.state().sequence(),"historical target is beyond the actual current head");
                canonicalHead=borrowed.requireHistoricalHead(point.sequence(),point.digest());
            }
            ActionReceipt original=bound.loadReceipt(identity.pending().originalReceipt());
            Canonical canonical=canonical(borrowed,canonicalHead,bound,original,pins,historical&&!originalHistoryTarget);
            require(canonical.receiptRef().equals(identity.pending().originalReceipt()),"pending receipt is not its actual immutable archive reference");
            ReconciliationIdentity reproduced=identity.driverRelation()==ReconciliationIdentity.DriverRelation.EXACT?
                    ReconciliationIdentity.fromCanonical(original,identity.factual(),identity.source(),identity.sessionId(),identity.connectionGeneration(),identity.pending().originalReceipt(),
                            identity.pending().originalBeforeDriver(),identity.evidence(),identity.observedAt()):
                    ReconciliationIdentity.fromCanonicalHistoryAppend(original,identity.factual(),identity.source(),identity.sessionId(),identity.connectionGeneration(),identity.pending().originalReceipt(),
                            identity.pending().originalBeforeDriver(),identity.evidence(),identity.observedAt(),identity.historyPoint().orElseThrow());
            require(reproduced.equals(identity),"query identity differs from the complete actual canonical pending/Attempt");
            byte[] oldDriver=readOwned(borrowed,bound,identity.pending().originalBeforeDriver(),pins);
            byte[] currentDriver=readOwned(borrowed,bound,identity.evidence().currentOriginalDriver(),pins);
            for(ExactRef ref:identity.evidence().originals())
                if(!ref.equals(identity.evidence().currentOriginalDriver()))readOwned(borrowed,bound,ref,pins);
            if(Arrays.equals(oldDriver,currentDriver)){
                require(identity.driverRelation()==ReconciliationIdentity.DriverRelation.EXACT&&identity.historyPoint().isEmpty(),"equal Driver must retain exact v1 relation");
            }else{
                require(identity.driverRelation()==ReconciliationIdentity.DriverRelation.HISTORY_APPEND,"changed Driver requires explicit history-append v2 DATA");
                var point=identity.historyPoint().orElseThrow();
                require(point.sequence()>=original.sequence()&&point.sequence()<=actual.state().sequence(),"original history target point is outside the pending/current canonical interval");
                if(!historical)require(point.sequence()==actual.state().sequence()&&point.digest().equals(actual.digest()),"live history target differs from the actual current writer head");
                WriterContracts.Head target=borrowed.requireHistoricalHead(point.sequence(),point.digest());
                var context=new HistoryContext(borrowed,actual,original,canonical.attempt(),canonical.receiptRef(),canonical.recordRef(),identity,
                        historical?Mode.HISTORICAL_READ:Mode.LIVE_PENDING,new DriverMaterial(identity.pending().originalBeforeDriver(),oldDriver),
                        new DriverMaterial(identity.evidence().currentOriginalDriver(),currentDriver),target);
                historyQualification.require(context);
            }
            finish(borrowed,actual,pins);return null;
        });
    }
    private record Canonical(ActionState.Attempt attempt,ExactRef receiptRef,ExactRef recordRef){ }
    private Canonical canonical(ContinuityStorePort.Session session,WriterContracts.Head head,
            ActionPorts.OutcomeArchive bound,ActionReceipt original,List<WriterContracts.Pin> pins,boolean historical)throws IOException{
        ActionState.Attempt attempt=ReconciliationIdentity.primitiveAttempt(original);
        ActionReceipt current=ContinuityActionJournal.lookup(head.state(),original.command().actionId(),bound)
                .orElseThrow(()->new IOException("original primitive is absent from the actual canonical action chain"));
        if(!historical){
            ReconciliationIdentity.primitiveAttempt(current);
            require(Arrays.equals(ActionReceiptCodec.encodeReceipt(original,bound),ActionReceiptCodec.encodeReceipt(current,bound)),
                    "original pending receipt changed, settled or was superseded in the current canonical action chain");
        }else{
            require(original.bodySha256().equals(current.bodySha256())
                    &&Arrays.equals(ActionCodec.encodeCommand(original.command()),ActionCodec.encodeCommand(current.command()))
                    &&ActionTransitions.attempt(current.state()).filter(attempt::equals).isPresent(),
                    "historical original body/primitive Attempt did not survive the actual canonical chain");
            var originalDispatch=ActionTransitions.dispatch(original.state());
            require(originalDispatch.isEmpty()||originalDispatch.equals(ActionTransitions.dispatch(current.state())),
                    "historical original dispatch was erased or replaced in the canonical chain");
        }
        ExactRef receiptRef=bound.receiptReferenceOf(original);
        ActionReceipt retained=bound.loadReceipt(receiptRef);
        require(Arrays.equals(ActionReceiptCodec.encodeReceipt(original,bound),ActionReceiptCodec.encodeReceipt(retained,bound)),
                "actual immutable receipt differs from the original canonical pending");
        capture(session,receiptRef,ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES,pins);
        capture(session,bound.receiptReferenceOf(current),ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES,pins);
        capture(session,ContinuityActionJournal.requireHistoricalReceipt(head.state(),current,bound),WriterContracts.MAX_PIN_BYTES,pins);
        ExactRef recordRef=ContinuityActionJournal.requireHistoricalReceipt(head.state(),original,bound);
        capture(session,recordRef,WriterContracts.MAX_PIN_BYTES,pins);
        requireHistoricalPoint(session,head,original,recordRef,bound);
        capture(session,bound.requestReferenceOf(attempt.preparedRequest()),WriterContracts.MAX_PIN_BYTES,pins);
        // The mandatory originals port enforces actual owned-root policy BEFORE the writer opens a reference.
        readOwned(session,bound,attempt.guard().nativeEvidence(),pins);
        readOwned(session,bound,attempt.guard().capabilityEvidence(),pins);
        for(ExactRef ref:attempt.guard().supportingEvidence())readOwned(session,bound,ref,pins);
        return new Canonical(attempt,receiptRef,recordRef);
    }
    private static void requireHistoricalPoint(ContinuityStorePort.Session session,WriterContracts.Head head,
            ActionReceipt original,ExactRef recordRef,ActionPorts.OutcomeArchive bound)throws IOException{
        String basename=String.format(Locale.ROOT,"%08d.json",original.sequence());
        List<WriterContracts.Pin> candidates=head.documents().stream().filter(pin->
                Path.of(pin.reference().path()).getFileName().toString().equals(basename)).toList();
        require(candidates.size()==1,"the canonical pending event is absent or ambiguous in actual retained documents");
        ObjectNode event=ContinuityJson.parseObject(session.readPinned(candidates.getFirst(),ContinuityJson.LEDGER_MAX_BYTES),
                ContinuityJson.LEDGER_MAX_BYTES);
        StrictJson.object(event,Set.of("sequence","at_utc","kind","details","identity","previous_sha256","after"));
        require(StrictJson.integer(event.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER)==original.sequence()
                &&WriterContracts.ACTION_LIFECYCLE_KIND.equals(StrictJson.text(event.get("kind"))),
                "pending metadata is not the original canonical action event");
        ObjectNode details=StrictJson.object(event.get("details"),Set.of("evidence_id","source","receipt_ref"));
        require(StrictJson.text(details.get("evidence_id")).equals(original.command().actionId()+":"+original.sequence())
                &&ExactRef.fromJson(details.get("receipt_ref")).equals(recordRef)
                &&ContinuityJson.same(details.get("source"),
                    org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.source(original.command().source())),
                "actual pending event does not bind its complete original action record/source");
        ContinuityState claimed=ContinuityState.fromJson(event.get("after"),head.state().machineId());
        // The sole writer authenticates this point against its complete actual canonical chain.
        // The event's own JSON/hash is never accepted as its own authority.
        ContinuityState historical=session.requireHistoricalState(original.sequence(),ContinuityJson.digest(claimed.toJson()));
        require(ContinuityActionJournal.requireHistoricalReceipt(historical,original,bound).equals(recordRef),
                "original pending record was not canonical at its own durable event");
        require(ContinuityActionJournal.recordHead(historical).orElseThrow().equals(recordRef),
                "historical action event does not publish this exact original record as its head");
        session.verifyPin(candidates.getFirst());
    }
    private byte[] readOwned(ContinuityStorePort.Session session,ActionPorts.OutcomeArchive bound,
            ExactRef original,List<WriterContracts.Pin> pins)throws IOException{
        // This is a complete RAW read: hello/heartbeat/snapshot are framed packets, not JSON material.
        byte[] owned=originals.read(session,original,WriterContracts.MAX_PIN_BYTES);
        byte[] raw=capture(session,original,WriterContracts.MAX_PIN_BYTES,pins);
        require(Arrays.equals(owned,raw),"owned original bytes differ from the exact same-Session pin");return raw;
    }
    private static byte[] capture(ContinuityStorePort.Session session,ExactRef ref,int maximum,
            List<WriterContracts.Pin> pins)throws IOException{
        WriterContracts.Pin pin=session.capturePin(ref,maximum);
        byte[] raw=session.readPinned(pin,maximum);pins.add(pin);return raw;
    }
    private void finish(ContinuityStorePort.Session session,WriterContracts.Head before,List<WriterContracts.Pin> pins)throws IOException{
        for(WriterContracts.Pin pin:pins)session.verifyPin(pin);
        store.requireSession(session);WriterContracts.Head after=session.head();
        require(ContinuityJson.same(before.state().toJson(),after.state().toJson())&&before.documents().equals(after.documents())
                &&before.absent().equals(after.absent())&&before.indexRepairs().equals(after.indexRepairs())
                &&before.snapshotNeedsRecovery()==after.snapshotNeedsRecovery(),"actual canonical head/original native pins changed during pending verification");
    }
    @FunctionalInterface private interface Work<T>{T run(ActionPorts.OutcomeArchive bound)throws IOException;}
    private <T>T inSession(ContinuityStorePort.Session session,Work<T> work)throws IOException{
        Objects.requireNonNull(session);store.requireSession(session);
        try {
            return archive.inSession(session,bound->{
                try{return work.run(bound);}catch(IOException failure){throw new UncheckedIOException(failure);}
            });
        }catch(UncheckedIOException failure){throw failure.getCause();}
        catch(IllegalArgumentException|IllegalStateException invalid){throw new IOException("actual original pending binding is unavailable",invalid);}
    }
    private static void require(boolean condition,String message)throws IOException{if(!condition)throw new IOException(message);}
}

