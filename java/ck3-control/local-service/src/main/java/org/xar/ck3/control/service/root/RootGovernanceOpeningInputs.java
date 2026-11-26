package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions.OpeningDateEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.OpeningStage;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
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
                if (!canProjectOpeningDate(document, request.before(), action)) return openingGate(document, request.before(), action);
                return context.collector().borrowCurrent(borrowed, request.before(), request.deadline(), lease -> {
                    var current = lease.frame();
                    StrictJson.require(current.identity().equals(request.before()) && current.source().equals(request.source())
                            && current.sessionId().equals(request.sessionId()), "opening projection crossed its actual current planning request");
                    return openingGate(document, current.identity(), action,
                            importedOpeningAdvance(context, borrowed, document, current, request.deadline()));
                });
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
        Optional<? extends OpeningDateEvidence> advance = Optional.empty();
        if (canProjectOpeningDate(document, actual, action)) {
            context.collector().requireHeldFrame(capture.session(), capture.frame());
            advance = importedOpeningAdvance(context, capture.session(), document, capture.frame(), capture.deadline());
        }
        OpeningGate gate=openingGate(document,actual,action,advance);
        originals.addAll(gate.dateEvidence());
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
        return actualAction(context.archive().withSession(same),same.head().state(),document);
    }
    static Optional<ActionReceipt> actualAction(ActionPorts.OutcomeArchive archive,ContinuityState state,
            GovernanceOpeningDocument.Document document)throws IOException {
        if(document.preparedCommand().isEmpty())return document.actionReceipt().map(archive::loadReceipt);
        var command=org.xar.ck3.control.application.action.ActionCodec.decodeCommand(archive.loadMaterial(document.preparedCommand().orElseThrow()).bytes());
        var canonical=org.xar.ck3.control.application.action.ContinuityActionJournal.lookup(state,command.actionId(),archive);
        if(canonical.isEmpty()) {
            StrictJson.require(document.stage()==OpeningStage.AWAIT_RECEIPT&&document.actionReceipt().isEmpty()&&document.checkpoint().isEmpty(),
                    "opening receipted/checkpointed original lost its canonical action");
            return Optional.empty();
        }
        org.xar.ck3.control.contracts.StrictJson.require(java.util.Arrays.equals(org.xar.ck3.control.application.action.ActionCodec.encodeCommand(command),
                org.xar.ck3.control.application.action.ActionCodec.encodeCommand(canonical.orElseThrow().command())),"opening pending command crossed its canonical receipt");
        return canonical;
    }
    private static Optional<? extends OpeningDateEvidence> importedOpeningAdvance(RootRuntimeContext context, Session same,
            GovernanceOpeningDocument.Document document, Complete current, Instant deadline) throws IOException {
        context.requireCurrent(deadline);
        if (!new Bool(true).equals(current.semantic().get("paused"))
                || !new Bool(true).equals(current.semantic().get("map_ready"))) return Optional.empty();
        StrictJson.require(context.actions() instanceof RootApplicationSession,
                "opening date projection requires the actual Root cycle owner");
        var session = (RootApplicationSession) context.actions();
        var owner = new SessionIdentity(current.identity().machineId(), current.identity().game(), current.sessionId());
        var advance = session.batchJournal().openingDateEvidence(same, owner, document.observed(), current.source(), current.identity());
        context.requireCurrent(deadline);
        return advance;
    }

    static boolean canProjectOpeningDate(GovernanceOpeningDocument.Document document, ObservationIdentity current,
            Optional<ActionReceipt> action) {
        var anchor = document.observed();
        return document.stage() == OpeningStage.AWAIT_SUBMIT && document.preparedCommand().isEmpty()
                && document.actionReceipt().isEmpty() && document.checkpoint().isEmpty() && action.isEmpty()
                && anchor.game().equals(current.game())
                && anchor.frame().identity().dateRaw().compareTo(current.frame().identity().dateRaw()) < 0
                && document.existingObserved().map(existing ->
                        existing.game().equals(current.game())
                        && existing.frame().identity().dateRaw().equals(current.frame().identity().dateRaw())
                        && existing.frame().identity().nativeRevision().compareTo(current.frame().identity().nativeRevision()) <= 0)
                    .orElse(true);
    }

    static OpeningGate openingGate(GovernanceOpeningDocument.Document document,ObservationIdentity current,Optional<ActionReceipt> action) {
        return openingGate(document, current, action, Optional.empty());
    }

    static OpeningGate openingGate(GovernanceOpeningDocument.Document document, ObservationIdentity current,
            Optional<ActionReceipt> action, Optional<? extends OpeningDateEvidence> advance) {
        boolean preparedOnly=document.stage()==OpeningStage.AWAIT_RECEIPT&&document.preparedCommand().isPresent()
                &&document.actionReceipt().isEmpty()&&document.checkpoint().isEmpty()&&action.isEmpty();
        var date = document.observed().frame().identity().dateRaw();
        if (advance.isPresent()) {
            StrictJson.require(canProjectOpeningDate(document, current, action),
                    "only an unissued imported opening can use its actual settled Life date");
            date = advance.orElseThrow().semantic().frame().frame().identity().dateRaw();
        }
        return new OpeningGate(current.frame().episodeRunId(),date,
                preparedOnly?OpeningStage.AWAIT_SUBMIT:document.stage(),action,document.checkpoint(),
                advance.map(OpeningDateEvidence::evidence).orElseGet(List::of));
    }

}
