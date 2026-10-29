package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof;
import org.xar.ck3.control.application.session.BatchLimits;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.service.OrdinarySessionHost;

/** Actual-input acceptance consumer. Host owns afterTurn; no second fixture.advance or private stage is entered. */
public final class RootManagedEpisodeChainInvocation {
    private RootManagedEpisodeChainInvocation() { }
    public record PublishedReadback(RootApplicationSession session,EpisodeWindow.State window,
            CheckpointPair firstPair,ActionReceipt originalFirstSave,WriterContracts.Head head) {
        public PublishedReadback {Objects.requireNonNull(session);Objects.requireNonNull(window);Objects.requireNonNull(firstPair);
            Objects.requireNonNull(originalFirstSave);Objects.requireNonNull(head);}
    }
    public record ObservedBatch(BatchReport report,Optional<PublishedReadback> publication) {
        public ObservedBatch {Objects.requireNonNull(report);Objects.requireNonNull(publication);}
    }

    /**
     * Calls the production HTTP-facing Host exactly once. Original startup/Managed/private lifecycle inputs
     * must already exist; this consumer cannot produce them. A NEXT is completed by Root.batch/afterTurn
     * before Host returns. The attached fixture is an identity witness, never a second transfer engine.
     */
    public static ObservedBatch runBatch(RootEpisodeChainFixture fixture,OrdinarySessionHost actualHost,
            BatchLimits limits,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(fixture);Objects.requireNonNull(actualHost);Objects.requireNonNull(limits);Objects.requireNonNull(deadline);
        var core=fixture.core();var previous=fixture.current();
        require(core.clock().instant().isBefore(deadline)&&!core.clock().instant().plus(limits.wallTime()).isAfter(deadline),
                "actual Host batch must fit the original bounded acceptance deadline");
        require(core.sessionAccess().current()==previous&&previous.ownedBy(core)&&previous.writer()==core.writer()
                &&previous.archive()==core.archive()&&previous.hasInstalledHost()&&!previous.isRetired()
                &&previous.hostForPublication()==actualHost&&actualHost.current().orElse(null)==previous.controllerForPublication(),
                "actual Host batch requires the original installed Core/session/controller, not a replaced fixture");
        WriterContracts.Head before=core.withBorrowed(()->core.writer().borrowedSession().head());
        BatchReport actual=actualHost.batch(previous.identity().sessionId(),limits);
        require(actual.session().equals(previous.identity()),"Host returned another original session report");
        List<ActionReceipt> parents=actual.lifecycleTurns().stream().map(BatchReport.LifecycleTurn::receipt).filter(receipt->
                receipt.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.LifecycleApplied applied
                &&applied.proof().kind()==LifecycleTransitionProof.Kind.NEXT_EPISODE).toList();
        require(parents.size()<=1,"one actual Host batch cannot produce multiple NEXT parents");
        if(parents.isEmpty()) {
            require(core.sessionAccess().current()==previous,"Host changed ownership without its original canonical NEXT report");
            return new ObservedBatch(actual,Optional.empty());
        }
        require(actual.terminal()==BatchReport.Terminal.EPISODE_HANDOFF,"canonical NEXT must retain its actual handoff terminal");
        var parent=parents.getFirst();var successor=core.sessionAccess().current();
        require(successor!=previous&&previous.isRetired()&&successor.ownedBy(core)&&!successor.isRetired()&&successor.hasInstalledHost()
                &&successor.writer()==core.writer()&&successor.archive()==core.archive()
                &&successor.hostForPublication()==actualHost&&actualHost.current().orElse(null)==successor.controllerForPublication()
                &&!previous.identity().game().equals(successor.identity().game())
                &&!previous.identity().sessionId().equals(successor.identity().sessionId()),
                "production afterTurn did not publish the distinct same-Core successor into the identical Host");
        return successor.withPublicStandaloneRead(deadline,same->{
            WriterContracts.Head head=same.head();EpisodeWindow.State window=EpisodeWindow.requireActive(head.state());
            EpisodeWindow.Baseline baseline=window.baseline().orElseThrow();EpisodeWindow.CommittedBegin begin=baseline.begin();
            same.requireEpisodeWindowBegin(begin);
            var beginning=same.requireHistoricalState(begin.sequence(),begin.headDigest());
            require(EpisodeWindow.state(beginning).orElseThrow().phase()==EpisodeWindow.Phase.AWAITING_FIRST_SAVE,
                    "actual BEGIN history did not precede physical first SAVE/BASELINE");
            require(window.begin().equals(begin.begin())&&window.begin().parentActionId().equals(parent.command().actionId())
                    &&window.begin().before().game().equals(previous.identity().game())
                    &&window.begin().before().sessionId().equals(previous.identity().sessionId())
                    &&baseline.savedIdentity().game().equals(successor.identity().game())
                    &&baseline.savedIdentity().sessionId().equals(successor.identity().sessionId())
                    &&head.state().sequence()>before.state().sequence()&&!head.digest().equals(before.digest()),
                    "canonical BEGIN/BASELINE/head do not descend from this actual Host NEXT");
            require(parent.equals(core.archive().loadReceipt(core.archive().receiptReferenceOf(parent))),
                    "Host NEXT lost its original archived canonical parent");
            var rawPair=core.archive().loadMaterial(baseline.pairRef());
            CheckpointPair pair=CheckpointPairCodec.decode(rawPair.bytes());
            require(pair.equals(successor.controllerForPublication().savedPair().orElseThrow())
                    &&pair.saveActionId().equals(baseline.saveActionId())
                    &&pair.frame().game().equals(successor.identity().game())
                    &&pair.frame().frame().episodeRunId().equals(baseline.savedIdentity().episodeRunId())
                    &&pair.frame().frame().identity().player().longValueExact()==baseline.savedIdentity().actorId()
                    &&Arrays.equals(rawPair.bytes(),CheckpointPairCodec.encode(pair)),
                    "the actual new Controller must retain exactly the canonical first physical SAVE pair");
            ActionReceipt save=core.archive().loadReceipt(baseline.canonicalSaveReceiptRef());
            require(save.command().actionId().equals(pair.saveActionId())&&save.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&!save.eligibleAdvance()
                    &&save.command().origin().game().equals(successor.identity().game())
                    &&save.command().sessionId().equals(successor.identity().sessionId())&&save.sequence()>begin.sequence()
                    &&head.state().toJson().path("last_settled_cycles").isIntegralNumber()
                    &&head.state().toJson().path("last_settled_cycles").longValue()==0,
                    "first SAVE/BASELINE must not invent a completed ordinary cycle");
            WriterContracts.Head after=same.head();
            require(after.digest().equals(head.digest())&&after.documents().equals(head.documents())&&after.absent().equals(head.absent())
                    &&after.indexRepairs().equals(head.indexRepairs())&&after.snapshotNeedsRecovery()==head.snapshotNeedsRecovery(),
                    "passive Host publication readback changed the canonical writer head");
            return new ObservedBatch(actual,Optional.of(new PublishedReadback(successor,window,pair,save,head)));
        });
    }
}
