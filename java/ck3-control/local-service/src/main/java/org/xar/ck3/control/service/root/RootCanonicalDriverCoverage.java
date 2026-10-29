package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual private Driver issuer -> canonical publication index -> original archived action coverage. */
public final class RootCanonicalDriverCoverage implements DriverBootstrap.HistoryCoverageReader {
    private sealed interface Basis permits Resolved,Current { }
    private record Resolved(RootLegacyResumeRuntime.Prepared prepared,WriterContracts.Receipt receipt) implements Basis { }
    private record Current() implements Basis { }
    private record Actual(DriverStateSnapshot.Complete driver,long version,long epoch,GameGeneration game,String sessionId) { }
    private final RootRuntimeContext context;private final Basis basis;
    private RootCanonicalDriverCoverage(RootRuntimeContext context,Basis basis){this.context=context;this.basis=basis;}
    static RootCanonicalDriverCoverage resolved(RootRuntimeContext context,RootLegacyResumeRuntime.Prepared prepared,
            WriterContracts.Receipt receipt)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(prepared);Objects.requireNonNull(receipt);
        var same=context.writer().borrowedSession();prepared.requireOwner(same,context.transport(),context.source(),context.archive());
        prepared.requireCommitted(same,receipt);return new RootCanonicalDriverCoverage(context,new Resolved(prepared,receipt));
    }
    public static RootCanonicalDriverCoverage current(RootRuntimeContext actual)throws IOException {
        Objects.requireNonNull(actual);actual.adopted();actual.game().verify();return new RootCanonicalDriverCoverage(actual,new Current());
    }
    @Override public Optional<? extends DriverBootstrap.ArchivedActionCoverage> originalFor(ActionReceipt actual)throws IOException {
        var same=context.writer().borrowedSession();context.writer().requireSession(same);context.game().verify();String head=same.head().digest();
        var archive=context.archive().withSession(same);Actual owner;
        if(basis instanceof Resolved resolved) {
            var seed=resolved.prepared().seed(same,resolved.receipt());
            owner=new Actual(DriverStateSnapshot.decodeComplete(context.archive().readArtifact(same,seed.fullDriver(),DriverCheckpointStore.MAX_DRIVER_BYTES)),
                    seed.driverVersion(),seed.episodeEpoch(),seed.expectedSession().game(),seed.expectedSession().sessionId());
        }else {
            var adopted=context.adopted();var known=adopted.authority().withFrozenFacts(same,frozen->{
                var state=frozen.state();
                StrictJson.require(state instanceof DriverSnapshotFacts.Known,"actual full current Driver required for canonical history recovery");return (DriverSnapshotFacts.Known)state;
            });
            StrictJson.require(adopted.session().game().equals(known.stamp().game())&&known.stamp().game().equals(context.game().generation())
                    &&adopted.source().equals(context.source()),"actual Driver coverage crossed its private Root owner");
            owner=new Actual(known.driver(),known.stamp().driverVersion(),known.stamp().episodeEpoch(),known.stamp().game(),adopted.session().sessionId());
        }
        var found=DriverActionHistoryState.findCommittedCoverage(same,actual,archive);
        if(found.isEmpty())return Optional.empty();var committed=found.orElseThrow();var publication=committed.publication();
        StrictJson.require(owner.version()>=committed.afterVersion()&&owner.epoch()==committed.episodeEpoch()
                &&owner.game().equals(actual.command().before().game())
                &&owner.driver().session().episodeRunId().equals(actual.command().before().frame().episodeRunId()),
                "canonical publication is not covered by the actual private Driver version/epoch/Game/episode");
        var after=DriverStateSnapshot.decodeComplete(context.archive().readArtifact(same,committed.afterDriver(),DriverCheckpointStore.MAX_DRIVER_BYTES));
        requireSurvivingSession(same,archive,after,committed.afterVersion(),owner);
        StrictJson.require(after.commandHistory().size()<=owner.driver().commandHistory().size(),
                "canonical action publication is not a surviving prefix of this actual full Driver");
        for(int index=0;index<after.commandHistory().size();index++)StrictJson.require(Arrays.equals(after.commandHistory().get(index).originalRow().json(),
                owner.driver().commandHistory().get(index).originalRow().json()),"current Driver changed the exact canonical action history prefix");
        ExactRef receipt=archive.receiptReferenceOf(actual);DriverBootstrap.ArchivedActionCoverage result;
        if(committed.legacyRow().isPresent()) {
            ExactRef source=committed.legacyRow().orElseThrow();var row=DriverJson.object(archive.loadFullMaterial(source).bytes(),DriverJson.MAX_NATIVE_BYTES);
            long index=OpportunityJson.integer(row.get("index"),"original legacy history index").longValueExact();
            StrictJson.safe(index,1);StrictJson.require(index<=owner.driver().commandHistory().size()
                    &&Arrays.equals(owner.driver().commandHistory().get(Math.toIntExact(index-1)).originalRow().json(),archive.loadFullMaterial(source).bytes()),
                    "actual canonical legacy row is absent from the private full Driver");
            DriverActionHistoryCodec.verifyLegacy(same,actual,row,archive);result=new DriverBootstrap.ArchivedHistoryRow(receipt,index,source);
        }else {
            DriverActionHistoryCodec.verifyCanonicalOnly(same,actual,committed.originalSource(),archive);
            result=new DriverBootstrap.ArchivedCanonicalOnly(receipt,committed.originalSource());
        }
        context.writer().requireSession(same);StrictJson.require(head.equals(same.head().digest()),"canonical history reader changed its actual writer Head");
        return Optional.of(result);
    }
    /** Only this actual Root context can supply its installed zero-dispatch source replay verifier. */
    @Override public void requireOperatorNonRebind(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            ActionReceipt actual,org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive requestedArchive)throws IOException {
        Objects.requireNonNull(requestedArchive);context.writer().requireSession(same);context.game().verify();
        String head=same.head().digest();
        var installed=context.bindings().actualArchivedVerifier(actual.command().operation())
                .orElseThrow(()->new IOException("actual installed Root operator archived verifier is unavailable"));
        DriverOperatorNonRebindOriginals.requireCanonical(same,actual,context.archive().withSession(same),installed);
        context.game().verify();context.writer().requireSession(same);
        StrictJson.require(head.equals(same.head().digest()),"operator non-rebind coverage changed the actual Root writer Head");
    }
    /** Existing history survives an explicit operator only through its actual canonical, archived source chain. */
    private void requireSurvivingSession(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive archive,DriverStateSnapshot.Complete original,
            long originalVersion,Actual owner)throws IOException {
        var old=original.session();var current=owner.driver().session();
        StrictJson.require(old.pipeName().equals(current.pipeName())&&old.bridgePid()==current.bridgePid()
                &&old.episodeRunId().equals(current.episodeRunId()),"canonical action crossed actual pipe/PID/episode");
        if(old.actorId().equals(current.actorId()))return;
        long version=originalVersion;var actor=old.actorId();boolean observed=false;
        for(var change:org.xar.ck3.control.continuity.EpisodeWindow.operatorLineage(same.head().state())) {
            var before=change.before();
            if(!before.game().equals(owner.game())||!before.sessionId().equals(owner.sessionId())
                    ||!before.episodeRunId().equals(current.episodeRunId())||before.epoch()!=owner.epoch()
                    ||change.afterDriverVersion()<=originalVersion)continue;
            StrictJson.require(change.beforeDriverVersion()>=version&&change.afterDriverVersion()<=owner.version()
                    &&java.math.BigInteger.valueOf(before.actorId()).equals(actor),"operator chain does not continue the exact surviving action subject/version");
            var receipt=org.xar.ck3.control.application.action.ContinuityActionJournal.lookup(same.head().state(),change.actionId(),archive)
                    .orElseThrow(()->new IOException("actual canonical operator receipt is absent from current surviving history"));
            org.xar.ck3.control.application.action.ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),receipt,archive);
            DriverOperatorRebindOriginals.requireCanonical(same,receipt,archive);
            var completion=DriverOperatorRebindOriginals.requireOriginals(receipt,archive);
            var publication=DriverOperatorRebindOriginals.decodePublication(archive.loadMaterial(completion.originals().privateProof()));
            StrictJson.require(publication.transition().equals(change),"current operator lineage differs from its actual receipt/source/Driver originals");
            version=change.afterDriverVersion();actor=java.math.BigInteger.valueOf(change.after().actorId());observed=true;
        }
        StrictJson.require(observed&&actor.equals(current.actorId()),"current actor has no complete actual canonical operator lineage from the preserved action history");
    }
}
