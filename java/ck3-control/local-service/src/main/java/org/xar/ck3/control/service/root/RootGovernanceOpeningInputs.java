package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.planning.governance.GovernanceOpeningDocument;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.OpeningGate;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual same-head producer for the planner's opening flag; no missing-state false default. */
public final class RootGovernanceOpeningInputs implements RootPlanningInputsFactory.OpeningInputs {
    private final List<ExactRef> producerSources;
    public RootGovernanceOpeningInputs(List<ExactRef> actualProducerSources) {
        producerSources=List.copyOf(actualProducerSources);
        StrictJson.require(!producerSources.isEmpty() && producerSources.stream().allMatch(ref->ref.bytes()>0),"registered opening producer closure required");
    }
    public org.xar.ck3.control.application.planning.governance.GovernanceStateSupplier.BodyContract<OpeningGate> stateContract(RootRuntimeContext context) {
        Objects.requireNonNull(context);
        return new org.xar.ck3.control.application.planning.governance.GovernanceStateSupplier.BodyContract<>(DomainBodies.Slot.OPENING_GATE,
                GovernanceOpeningDocument.SCHEMA,producerSources,(request,original)->{
            try {
                var borrowed=context.borrowedSession();context.writer().requireSession(borrowed);context.requireCurrent(request.deadline());
                var document=GovernanceOpeningDocument.decode(original);GovernanceOpeningDocument.requireSameEpisode(document,request.before(),request.source());
                if(!document.observed().game().equals(request.before().game())) {
                    var read=borrowed.readDomain(DomainBodies.Slot.OPENING_GATE);
                    if(!(read instanceof DomainBodies.Available available)||!java.util.Arrays.equals(original,available.canonicalBody()))throw new IOException("opening restored body differs from actual registered original");
                    restoration(context,borrowed,document,request.before(),request.source(),request.deadline(),available);
                } else StrictJson.require(document.sessionId().equals(request.sessionId()),"opening ordinary consumer crossed its actual session");
                Optional<ActionReceipt> action=actualAction(context,borrowed,document);
                action.ifPresent(receipt->StrictJson.require(receipt.command().before().equals(document.observed())
                        && receipt.command().source().equals(document.source()),"opening ordinary consumer changed its original command"));
                return new OpeningGate(document.observed().frame().episodeRunId(),document.observed().frame().identity().dateRaw(),document.stage(),action,document.checkpoint());
            } catch(InterruptedException interrupted) {
                Thread.currentThread().interrupt();throw new IllegalStateException("actual opening restoration check interrupted",interrupted);
            } catch(IOException unavailable) {throw new IllegalStateException("actual opening body unavailable",unavailable);}
        });
    }
    @Override public RootPlanningInputsFactory.OpeningObservation collect(RootPlanningInputsFactory.Capture capture)throws IOException {
        Objects.requireNonNull(capture);RootRuntimeContext context=capture.context();context.writer().requireSession(capture.session());
        StrictJson.require(context.borrowedSession()==capture.session(),"opening input must use the actual already-borrowed Session");
        context.requireCurrent(capture.deadline());var actual=capture.frame().identity();ExactRef head=capture.session().persistedHead();
        var available=retainedBody(capture.session(),head);var reference=available.reference();
        var document=GovernanceOpeningDocument.decode(available.canonicalBody());GovernanceOpeningDocument.requireSameEpisode(document,actual,capture.frame().source());
        List<ExactRef> originals=new ArrayList<>();originals.add(head);originals.add(reference.payload());originals.addAll(reference.producerSources());originals.addAll(document.originals());
        if(!document.observed().game().equals(actual.game())) {
            try {
                originals.addAll(restoration(context,capture.session(),document,actual,capture.frame().source(),capture.deadline(),available));
            } catch(InterruptedException interrupted) { Thread.currentThread().interrupt();throw new IOException("opening restoration validation interrupted",interrupted); }
        } else StrictJson.require(document.sessionId().equals(capture.frame().sessionId()),"same-Game opening body crossed its actual session");
        Optional<ActionReceipt> action=actualAction(context,capture.session(),document);
        action.ifPresent(receipt->{
            StrictJson.require(receipt.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay
                    && receipt.command().before().equals(document.observed())
                    && receipt.command().source().equals(document.source()),"opening pending receipt is not its exact original action/source");
            document.checkpoint().ifPresent(checkpoint->StrictJson.require(checkpoint.actionId().equals(receipt.command().actionId()),"opening checkpoint/action differs"));
        });
        OpeningGate gate=new OpeningGate(actual.frame().episodeRunId(),document.observed().frame().identity().dateRaw(),document.stage(),action,document.checkpoint());
        StrictJson.require(head.equals(capture.session().persistedHead()),"opening input reads changed the writer head");
        return new RootPlanningInputsFactory.OpeningObservation(new RootPlanningInputsFactory.FieldSource(actual,capture.frame().source(),
                capture.frame().sessionId(),originals.stream().distinct().toList()),gate);
    }
    DomainBodies.Available retainedBody(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ExactRef head)throws IOException {
        var read=same.readDomain(DomainBodies.Slot.OPENING_GATE);
        if(!(read instanceof DomainBodies.Available available))throw new IOException("actual registered opening body unavailable; fresh entry or qualified restoration must publish it first");
        var reference=available.reference();
        StrictJson.require(available.head().equals(head) && reference.slot()==DomainBodies.Slot.OPENING_GATE
                && reference.contractSchema().equals(GovernanceOpeningDocument.SCHEMA)
                && DomainBodies.reference(same.head().state(),DomainBodies.Slot.OPENING_GATE).filter(reference::equals).isPresent(),
                "opening state crossed the actual head/schema/slot/member");
        return available;
    }
    private static List<ExactRef> restoration(RootRuntimeContext context,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            GovernanceOpeningDocument.Document document,org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity actual,
            org.xar.ck3.control.g2.common.G2Source source,java.time.Instant deadline,DomainBodies.Available current)throws IOException,InterruptedException {
        context.writer().requireSession(same);var restored=context.requireRestoration(deadline);var originalProof=context.restorationOriginal(same);var material=originalProof.material();
        StrictJson.require(restored.session().game().equals(actual.game())&&restored.source().equals(source)
                &&restored.episodeRunId().equals(actual.frame().episodeRunId())&&material.pair().equals(restored.pair())&&originalProof.pair().equals(restored.pair())
                &&restored.pair().frame().frame().identity().player().equals(document.observed().frame().identity().player())
                &&restored.pair().frame().frame().identity().dateRaw().compareTo(document.observed().frame().identity().dateRaw())>=0,
                "opening continuation lacks the actual current private saved-pair restoration binding");
        var original=DomainBodies.reference(material.originalHead(),DomainBodies.Slot.OPENING_GATE);
        boolean savedBody=original.filter(current.reference()::equals).isPresent();
        StrictJson.require(document.observed().game().equals(restored.pair().frame().game())||savedBody,
                "historical opening anchor is absent from the actual restored saved writer head");
        if(savedBody)StrictJson.require(java.util.Arrays.equals(current.canonicalBody(),context.archive().readArtifact(same,original.orElseThrow().payload(),1_048_576)),
                "actual saved opening body no longer matches its physical archived original");
        return List.of(originalProof.basis(),material.reference(),restored.originalHistoryBasis(),restored.pair().driver().reference(),restored.pair().save().reference());
    }
    private static Optional<ActionReceipt> actualAction(RootRuntimeContext context,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            GovernanceOpeningDocument.Document document)throws IOException {
        if(document.preparedCommand().isEmpty())return context.archive().inSession(same,archive->document.actionReceipt().map(archive::loadReceipt));
        var command=context.archive().inSession(same,archive->org.xar.ck3.control.application.action.ActionCodec.decodeCommand(archive.loadMaterial(document.preparedCommand().orElseThrow()).bytes()));
        var state=same.head().state();var canonical=context.archive().inSession(same,archive->org.xar.ck3.control.application.action.ContinuityActionJournal.lookup(state,command.actionId(),archive));
        if(canonical.isEmpty())throw new IOException("opening prepared original has no canonical INTENT; no receipt or replay permission is fabricated");
        org.xar.ck3.control.contracts.StrictJson.require(java.util.Arrays.equals(org.xar.ck3.control.application.action.ActionCodec.encodeCommand(command),
                org.xar.ck3.control.application.action.ActionCodec.encodeCommand(canonical.orElseThrow().command())),"opening pending command crossed its canonical receipt");
        return canonical;
    }
}
