package org.xar.ck3.control.application.action;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** The installed exact-operation callback owns this immutable configured request, never caller-supplied permission. */
public final class CompositeOperatorQuarantineSource {
    private final ExactRef requestRef;
    private final byte[] requestBytes;
    private final byte[] authorizationBytes;
    private final CompositeOperatorQuarantineRequest request;
    private final OperationKey operation;
    private final String handler;
    private final Clock clock;
    public CompositeOperatorQuarantineSource(ExactRef configuredRequest,byte[] actualRequest,byte[] actualAuthorization,
            GameGeneration installedGame,String installedEpisode,OperationKey installedOperation,String installedHandler,Clock clock) {
        requestRef=Objects.requireNonNull(configuredRequest);requestBytes=actualRequest.clone();authorizationBytes=actualAuthorization.clone();
        require(requestRef.bytes()==requestBytes.length&&requestRef.sha256().equals(ActionCodec.sha256(requestBytes)),"configured operator request bytes/SHA differ");
        request=CompositeOperatorQuarantineRequest.decode(requestBytes);
        require(request.authorizedBy().bytes()==authorizationBytes.length&&request.authorizedBy().sha256().equals(ActionCodec.sha256(authorizationBytes)),"actual operator authorization bytes/SHA differ");
        StrictJson.parse(authorizationBytes,65536);
        require(request.game().equals(installedGame)&&request.episodeRunId().equals(installedEpisode),"operator request is not for this installed Game/episode");
        operation=Objects.requireNonNull(installedOperation);handler=StrictJson.text(installedHandler);this.clock=Objects.requireNonNull(clock);
    }
    public CompositeOperatorQuarantineRequest request(){return request;}
    public ExactRef requestReference(){return requestRef;}
    /** Captures new decision evidence under the original lock. It neither queries nor dispatches Game. */
    public ExactRef capture(ContinuityStorePort.Session same,ActionReceipt original,ActionPorts.OutcomeArchive archive)throws IOException {
        var head=same.head();require(request.issuedAt().compareTo(clock.instant())<=0&&clock.instant().isBefore(request.observationDeadline()),"operator observation decision window expired/not yet issued");
        require(head.state().sequence()==request.expectedHeadSequence()&&head.digest().equals(request.expectedHeadDigest()),"operator request predecessor changed; no stale-head append");
        requireOriginalBinding(original);
        require(archive.receiptReferenceOf(original).equals(request.originalReceipt()),"configured original receipt reference differs");
        var actionHead=ContinuityActionJournal.recordHead(head.state()).orElseThrow();
        var reservations=reservations(actionHead,original,archive);
        var originalState=archive.preserveMaterial(new RawJson(ContinuityJson.canonical(head.state().toJson(),ContinuityJson.LEDGER_MAX_BYTES)));
        var requestMaterial=archive.preserveMaterial(new RawJson(requestBytes));
        archive.preserveMaterial(new RawJson(authorizationBytes));
        var proof=new CompositeOperatorQuarantineObservation(requestRef,requestMaterial,request.originalReceipt(),originalState,head.state().sequence(),head.digest(),actionHead,clock.instant(),reservations);
        var reference=archive.preserveMaterial(new RawJson(proof.encode()));
        require(same.head().digest().equals(head.digest()),"operator evidence capture changed original writer head");return reference;
    }
    public void verify(ContinuityStorePort.Session same,WriterContracts.Head actualHead,ActionReceipt proposed,ActionPorts.OutcomeArchive archive)throws IOException {
        require(same.head().digest().equals(actualHead.digest()),"operator verifier escaped original locked head");
        var proof=CompositeOperatorQuarantineObservation.load(proposed,archive);
        require(proof.requestSource().equals(requestRef)&&Arrays.equals(archive.loadMaterial(proof.requestMaterial()).bytes(),requestBytes),"operator observation is not from the installed configured request");
        var original=archive.loadReceipt(proof.originalReceipt());requireOriginalBinding(original);
        require(proof.originalReceipt().equals(request.originalReceipt())&&proof.predecessorSequence()==request.expectedHeadSequence()&&proof.predecessorDigest().equals(request.expectedHeadDigest()),"operator observation changed configured parent/predecessor");
        require(!proof.observedAt().isBefore(request.issuedAt())&&proof.observedAt().isBefore(request.observationDeadline()),"operator observation outside its distinct authorized window");
        WriterContracts.Head before;
        if(proposed.sequence()==Math.addExact(actualHead.state().sequence(),1)) {
            require(actualHead.state().sequence()==proof.predecessorSequence()&&actualHead.digest().equals(proof.predecessorDigest()),"new operator append requires its actual current predecessor");
            require(clock.instant().isBefore(request.observationDeadline()),"new operator observation cannot reuse expired decision permission");before=actualHead;
        } else {
            require(proposed.sequence()<=actualHead.state().sequence(),"operator archived receipt is in the future");
            before=same.requireHistoricalHead(proof.predecessorSequence(),proof.predecessorDigest());
            var after=same.requireHistoricalCanonicalState(proposed.sequence(),historicalDigest(same,actualHead,proposed.sequence()));
            var canonical=ContinuityActionJournal.lookup(after,proposed.command().actionId(),archive).orElseThrow();
            require(Arrays.equals(ActionReceiptCodec.encodeReceipt(canonical,archive),ActionReceiptCodec.encodeReceipt(proposed,archive)),"operator archived receipt is not its exact original committed event");
        }
        require(Arrays.equals(ContinuityJson.canonical(before.state().toJson(),ContinuityJson.LEDGER_MAX_BYTES),archive.loadMaterial(proof.predecessorState()).bytes()),"operator predecessor snapshot changed");
        require(ContinuityActionJournal.recordHead(before.state()).equals(Optional.of(proof.originalActionHead())),"operator proof changed actual ACTION prefix");
        var atPoint=ContinuityActionJournal.lookup(before.state(),original.command().actionId(),archive).orElseThrow();
        require(Arrays.equals(ActionReceiptCodec.encodeReceipt(atPoint,archive),ActionReceiptCodec.encodeReceipt(original,archive)),"operator parent was not the exact retained unknown at its predecessor");
        require(proof.reservations().equals(reservations(proof.originalActionHead(),original,archive)),"operator first reservation references changed");
    }
    private void requireOriginalBinding(ActionReceipt original) {
        request.requireParent(original);require(original.command().operation().equals(operation)&&((ActionState.CompositeUnknown)original.state()).execution().handlerId().equals(handler),"operator proof has no installed operation/handler binding");
    }
    private static List<CompositeOperatorQuarantineObservation.Reservation> reservations(ExactRef originalHead,ActionReceipt original,ActionPorts.OutcomeArchive archive) {
        var execution=((ActionState.CompositeUnknown)original.state()).execution();
        var first=new ExactRef[execution.children().size()];var seen=new HashSet<ExactRef>();Optional<ExactRef> cursor=Optional.of(originalHead);long previous=Long.MAX_VALUE;
        while(cursor.isPresent()) {
            var ref=cursor.orElseThrow();require(seen.add(ref)&&seen.size()<=100000,"finite complete canonical ACTION prefix required");
            var record=archive.loadRecord(ref);var receipt=record.receipt();require(receipt.sequence()<previous,"operator ACTION prefix order/fork changed");previous=receipt.sequence();
            if(receipt.command().actionId().equals(original.command().actionId())) {
                require(receipt.bodySha256().equals(original.bodySha256()),"operator original action body conflict");
                var composite=ActionTransitions.composite(receipt.state());
                if(composite.isPresent())for(int i=0;i<Math.min(first.length,composite.orElseThrow().children().size());i++) {
                    require(composite.orElseThrow().children().get(i).equals(execution.children().get(i)),"operator original reservation history changed");first[i]=ref;
                }
            }
            cursor=record.previous();
        }
        var result=new ArrayList<CompositeOperatorQuarantineObservation.Reservation>();
        for(int i=0;i<first.length;i++){var child=execution.children().get(i);result.add(new CompositeOperatorQuarantineObservation.Reservation(i+1,child.actionId(),child.bodySha256(),Objects.requireNonNull(first[i],"original reservation absent")));}
        return List.copyOf(result);
    }
    private static String historicalDigest(ContinuityStorePort.Session same,WriterContracts.Head head,long sequence)throws IOException {
        for(var pin:head.documents()) {
            String name=java.nio.file.Path.of(pin.reference().path()).getFileName().toString();
            if(name.equals(String.format(java.util.Locale.ROOT,"%08d.json",sequence))) {
                var transition=same.readHistoricalTransition(pin);require(transition.sequence()==sequence,"operator committed event sequence differs");return ContinuityJson.digest(transition.after().toJson());
            }
        }
        throw new IOException("original operator observation event absent from actual canonical writer chain");
    }
}
