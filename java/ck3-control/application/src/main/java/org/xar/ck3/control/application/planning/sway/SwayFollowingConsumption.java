package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.OrdinaryPlanCompletion;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Installed ordinary completion and cold domain replay share exact gameplay-result custody. */
public final class SwayFollowingConsumption {
    private SwayFollowingConsumption() { }
    @FunctionalInterface public interface ActualResultVerifier {
        void verify(ContinuityStorePort.Session same, ActionReceipt canonical) throws IOException;
    }
    public static OrdinaryPlanCompletion.ExecutionDisposition consume(ContinuityStorePort.Session same,
            SwayCanonicalDomain domain, ActionPorts.OutcomeArchive archive, GameGeneration currentGame,
            NativeEffectEvidence.FrameLoader frames, ActionReceipt actual, ActualResultVerifier verifier,
            SwayOrdinaryExecutor.IndependentFinal independentFinal) throws IOException {
        Objects.requireNonNull(same); Objects.requireNonNull(domain); Objects.requireNonNull(archive);
        Objects.requireNonNull(currentGame); Objects.requireNonNull(frames); Objects.requireNonNull(actual);
        Objects.requireNonNull(verifier); Objects.requireNonNull(independentFinal);
        if (!actual.settled() || !actual.visibleGameplay()) return new OrdinaryPlanCompletion.Unchanged("actual gameplay result required before consuming Sway observations");
        var originals = archive.withSession(same);
        var canonical = ContinuityActionJournal.lookup(same.head().state(), actual.command().actionId(), originals)
                .orElseThrow(() -> new IOException("actual following action absent from canonical chain"));
        var receipt = originals.receiptReferenceOf(canonical);
        require(receipt.equals(originals.receiptReferenceOf(actual)), "following action is not its exact actual canonical result");
        verifier.verify(same, canonical);
        var before = domain.load(same);
        if (before.ledger().resolved().isEmpty()) return new OrdinaryPlanCompletion.Unchanged("no current source-qualified Sway episode to consume");
        if (!before.ledger().resolved().orElseThrow().lifecycle().origin().game().equals(currentGame)) return new OrdinaryPlanCompletion.Unchanged("old Sway Game scope awaits actual source-qualified restoration");
        var independent = Objects.requireNonNull(independentFinal.current(canonical.command()));
        var read = originals.loadRead(independent.independentRootRead());
        var rebuilt = frames.load(independent.originalFrame(), originals);
        require(read.request().before().equals(rebuilt.identity()) && read.request().source().equals(rebuilt.source())
                && read.request().sessionId().equals(rebuilt.sessionId()) && rebuilt.identity().game().equals(currentGame), "following root read differs from its actual rebuilt current frame");
        require(SwayFormalState.atOrAfter(read.request().before(), observedAfter(canonical, originals, frames)), "following root read predates the confirmed gameplay result");
        var change = new SwayFormalState.FollowingGameplay(canonical.command().before(), read.request().before(), receipt);
        var expected = SwayFormalState.reduce(before.ledger(), change);
        if (Arrays.equals(SwayFormalCodec.encode(before.ledger()), SwayFormalCodec.encode(expected))) return new OrdinaryPlanCompletion.Unchanged("no newly consumable source-qualified Sway observation");
        var head = same.head();
        var publication = domain.commitPublication(same, change, new SwayTransitionCodec.Proofs(List.of(independent.independentRootRead()), Optional.empty(), Optional.empty(), List.of(receipt)));
        return new OrdinaryPlanCompletion.Published(head, publication.actual());
    }
    /** Reads the confirmed result's actual poststate; a fresh unrelated root read is insufficient. */
    public static ObservationIdentity observedAfter(ActionReceipt receipt, ActionPorts.OutcomeArchive originals,
            NativeEffectEvidence.FrameLoader frames) {
        var settlement = NativeRecordedEvidenceVerifier.settlement(receipt.state());
        if (settlement instanceof ActionState.Applied applied) return applied.observation().after();
        require(settlement instanceof ActionState.SwaySchedulerCompleted, "confirmed gameplay result has no supported original poststate");
        var scheduler = (ActionState.SwaySchedulerCompleted)settlement;
        require(scheduler.proof().newlyAppliedBusiness().isPresent(), "scheduler without new gameplay cannot consume Sway observations");
        return frames.load(scheduler.proof().finalFrame(), originals).identity();
    }
}
