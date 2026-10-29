package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;
import org.xar.ck3.control.g2.m6.SwayLifecycle;

/** Original Service producer: independent journal cursors, actual archived reads and the one M6/domain consumer. */
public final class SwaySelectedJournal {
    private final SwayCanonicalDomain domain;
    private final ActionPorts.OutcomeArchive archive;
    private final PlanningReadPort reads;
    private final SwayRootReads definitions;
    public SwaySelectedJournal(SwayCanonicalDomain domain,ActionPorts.OutcomeArchive archive,PlanningReadPort reads,SwayRootReads definitions) {
        this.domain=Objects.requireNonNull(domain);this.archive=Objects.requireNonNull(archive);this.reads=Objects.requireNonNull(reads);this.definitions=Objects.requireNonNull(definitions);
    }
    /** Caller retains its actual currentOwned freeze and original borrowed writer across both source reads and consumption. */
    public SwayObservationReads.JournalBatch read(ContinuityStorePort.Session same,SwayActionLifecycle.View current,SwayObservationReads.JournalQuery query)throws IOException {
        require(query.subject().actorCharacterId()==current.before().frame().identity().player().longValueExact(),"public journal subject crossed current player");
        var primary=readPlane(same,current,query);
        var peerKind=query.kind()==SwayObservationReads.Kind.EXECUTION?SwayObservationReads.Kind.TERMINATION:SwayObservationReads.Kind.EXECUTION;
        var peer=readPlane(same,current,new SwayObservationReads.JournalQuery(peerKind,query.subject(),BigInteger.ZERO));
        var batch=new SwayObservationReads.JournalBatch(primary.value(),peer.value(),Optional.empty());
        var execution=query.kind()==SwayObservationReads.Kind.EXECUTION?primary:peer;var termination=query.kind()==SwayObservationReads.Kind.TERMINATION?primary:peer;
        var originals=archive.withSession(same);
        for(var original:List.of(primary.receipt(),peer.receipt())) {
            NativeRecordedEvidenceVerifier.requireRead(original,originals);
            require(original.request().before().equals(current.before())&&original.request().source().equals(current.source())
                    &&original.request().sessionId().equals(current.sessionId()),"journal source pair crossed current full frame/source/session");
        }
        var ledger=domain.load(same).ledger();
        if(ledger.resolved().filter(value->value.identity().nativeSubject().equals(query.subject())&&value.lifecycle().origin().game().equals(current.before().game())).isEmpty())return batch;
        var episode=ledger.resolved().orElseThrow();var original=SwayFormalCodec.m6Episode(episode);
        var inputs=new M6TerminalSourceComposition.Inputs(Optional.empty(),Optional.of(execution.value().normalized()),Optional.of(termination.value().normalized()),Optional.empty());
        var composition=M6TerminalSourceComposition.compose(original,inputs);var observed=SwayLifecycle.observe(episode.lifecycle(),original,inputs,current.before());
        domain.commit(same,new SwayFormalState.LifecycleObserved(observed),new SwayTransitionCodec.Proofs(
                List.of(originals.readReferenceOf(primary.receipt()),originals.readReferenceOf(peer.receipt())),Optional.empty(),Optional.empty()));
        return new SwayObservationReads.JournalBatch(batch.primary(),batch.independentPeer(),Optional.of(composition.wire()));
    }
    private PlanningReadResult.Known<SwayObservationReads.JournalPlane> readPlane(ContinuityStorePort.Session same,SwayActionLifecycle.View current,SwayObservationReads.JournalQuery query)throws IOException {
        var definition=definitions.journal(query);var actual=reads.read(same,definition,new PlanningReadRequest(current.before(),current.source(),current.sessionId(),definition.operation(),SwayObservationReads.arguments(query),current.deadline()));
        if(actual instanceof PlanningReadResult.Known<SwayObservationReads.JournalPlane> known)return known;
        if(actual instanceof PlanningReadResult.Unavailable<SwayObservationReads.JournalPlane> missing)throw new IOException("actual native Sway journal unavailable: "+missing.reason());
        throw new IOException("actual native Sway journal has no typed result");
    }
}
