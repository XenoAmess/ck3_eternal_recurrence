package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;
import org.xar.ck3.control.g2.m6.SwayLifecycle;

/** Actionless actual completion/opinion reads; only a real retained episode may consume M6 lifecycle facts. */
public final class SwaySelectedObservation {
    private final SwayCanonicalDomain domain;private final ActionPorts.OutcomeArchive archive;
    private final PlanningReadPort reads;private final SwayRootReads definitions;
    public SwaySelectedObservation(SwayCanonicalDomain domain,ActionPorts.OutcomeArchive archive,PlanningReadPort reads,SwayRootReads definitions) {
        this.domain=Objects.requireNonNull(domain);this.archive=Objects.requireNonNull(archive);this.reads=Objects.requireNonNull(reads);this.definitions=Objects.requireNonNull(definitions);
    }
    public SwayObservationReads.DirectBatch read(ContinuityStorePort.Session same,SwayActionLifecycle.View current,SwayObservationReads.DirectQuery query)throws IOException {
        require(query.subject().actors().actorCharacterId()==current.before().frame().identity().player().longValueExact(),"direct Sway read crossed current player");
        var definition=definitions.direct(query);var result=reads.read(same,definition,new PlanningReadRequest(current.before(),current.source(),current.sessionId(),definition.operation(),SwayObservationReads.arguments(query),current.deadline()));
        if(!(result instanceof PlanningReadResult.Known<SwayObservationReads.DirectPlane> known))throw new IOException("actual direct Sway native observation unavailable");
        var originals=archive.withSession(same);NativeRecordedEvidenceVerifier.requireRead(known.receipt(),originals);
        require(known.receipt().request().before().equals(current.before())&&known.receipt().request().source().equals(current.source())&&known.receipt().request().sessionId().equals(current.sessionId()),"direct Sway original crossed full frame/source/session");
        var batch=new SwayObservationReads.DirectBatch(known.value(),Optional.empty());var actors=query.subject().actors();var ledger=domain.load(same).ledger();
        var retained=ledger.resolved().filter(value->value.identity().actorCharacterId()==actors.actorCharacterId()&&value.identity().targetCharacterId()==actors.targetCharacterId()
                &&value.lifecycle().origin().game().equals(current.before().game())&&query.subject().instance().map(subject->subject.equals(value.identity().nativeSubject())).orElse(true));
        if(retained.isEmpty())return batch;
        var episode=retained.orElseThrow();var original=SwayFormalCodec.m6Episode(episode);var normalized=known.value().normalized();
        var actualInputs=new M6TerminalSourceComposition.Inputs(query.kind()==SwayObservationReads.Kind.COMPLETION?Optional.of(normalized):Optional.empty(),Optional.empty(),Optional.empty(),query.kind()==SwayObservationReads.Kind.OPINION?Optional.of(normalized):Optional.empty());
        var compositionInputs=actualInputs;
        if(query.kind()==SwayObservationReads.Kind.OPINION)compositionInputs=new M6TerminalSourceComposition.Inputs(episode.lifecycle().latest().flatMap(value->value.proof().inputs().completion()),Optional.empty(),Optional.empty(),Optional.of(normalized));
        var composition=M6TerminalSourceComposition.compose(original,compositionInputs);
        var observed=SwayLifecycle.observe(episode.lifecycle(),original,actualInputs,current.before());
        var change=new SwayFormalState.LifecycleObserved(observed);var reduced=SwayFormalState.reduce(ledger,change);
        if(!java.util.Arrays.equals(SwayFormalCodec.encode(ledger),SwayFormalCodec.encode(reduced)))domain.commit(same,change,new SwayTransitionCodec.Proofs(List.of(originals.readReferenceOf(known.receipt())),Optional.empty(),Optional.empty()));
        return new SwayObservationReads.DirectBatch(batch.primary(),Optional.of(composition.wire()));
    }
}
