package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual-input assertions for the managed Host pending scenario.
 * No Managed input, Source, private ticket, M7 binding, packet or empty passing scenario is created here.
 */
public final class RootPendingUiAdmittedEpisodeAssertions {
    private RootPendingUiAdmittedEpisodeAssertions() { }
    public record Actual(LifecycleEpisodeInputs producer,LifecycleEpisodeInputs.CurrentAdoptionBinding current,
            ContinuityBatchJournal journal,ContinuityBatchJournal.AdmittedEpisode admitted,DriverSnapshotFacts.Known known) {
        public Actual {Objects.requireNonNull(producer);Objects.requireNonNull(current);Objects.requireNonNull(journal);Objects.requireNonNull(admitted);Objects.requireNonNull(known);}
    }
    /** The scenario supplies actual originals after its real canonical READ or BATCH. */
    public static Actual afterActualReadOrBatch(ContinuityStorePort.Session same,RootRuntimeContext context,
            RootLifecycleRuntimeFactory.Installed installed,RootApplicationSession root,ActionReceipt exactParent,
            Instant deadline) throws IOException {
        if(same==null||context==null||installed==null||root==null||exactParent==null||deadline==null)
            throw new IOException("MISSING_ACTUAL_ADMITTED_ROOT: actual source-qualified same-connection Root inputs are required; NOT_RUN is not PASS");
        installed.requireContext(context);context.core().requireCurrentForAccess(same,root);
        StrictJson.require(root.driver()==context.adopted()&&root.writer()==context.writer()&&root.archive()==context.archive(),"actual Root/current Driver/writer/archive differ");
        String head=same.head().digest();var before=known(context,same);
        var current=installed.admittedCurrent(same,exactParent,deadline)
                .orElseThrow(()->new IOException("MISSING_ACTUAL_HISTORICAL_ADOPTION: READ/BATCH does not have a canonical admitted natural episode"));
        var producer=installed.requireAdmittedCurrentProducer(same,current);
        StrictJson.require(Arrays.equals(ActionCodec.encodeCommand(current.parent().command()),ActionCodec.encodeCommand(exactParent.command()))
                &&current.parent().sequence()==exactParent.sequence()&&current.owner().equals(root.identity())
                &&current.recorded().publication().warmCommit().isEmpty(),"actual Root binding lost its original canonical parent/owner/recorded publication");
        var journal=root.batchJournal();var admitted=journal.admitCurrentEpisode(same,current);
        var actual=known(context,same);
        M7RootEpisodeChainAssertions.afterAdmittedReadOrBatchCurrent(same,producer,current,journal,admitted,actual);
        StrictJson.require(head.equals(same.head().digest())&&Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(before).bytes(),DriverSnapshotFacts.encodeKnownOriginal(actual).bytes()),
                "current episode readoption changed canonical head/full Known or performed a Driver CAS");
        return new Actual(producer,current,journal,admitted,actual);
    }
    public static void publicResumeIsReadOnly(ContinuityStorePort.Session same,RootRuntimeContext context,
            RootLifecycleRuntimeFactory.Installed installed,RootDriverLifecyclePublicCodec.Resume actualRequest,
            Instant deadline) throws IOException {
        installed.requireContext(context);String head=same.head().digest();var before=known(context,same);
        var actual=installed.natural().pendingRuntime().publicResumeMaterial(actualRequest,deadline);
        StrictJson.require(actual.status()==RootDriverLifecycleResumeCodec.Status.CLEAR&&!actual.pending()
                &&!actual.dateAdvanced()&&actual.transition().isEmpty(),"actual already-admitted public resume must retain the original no-pending four-key result");
        var encoded=RootDriverLifecycleResumeCodec.encode(actual);
        StrictJson.require(Arrays.equals(encoded.bytes(),RootDriverLifecycleResumeCodec.encode(RootDriverLifecycleResumeCodec.decode(encoded)).bytes()),"actual original no-pending response did not round-trip through its sole public codec");
        StrictJson.require(head.equals(same.head().digest())&&Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(before).bytes(),DriverSnapshotFacts.encodeKnownOriginal(known(context,same)).bytes()),
                "actual public resume changed the canonical writer/full Known or re-applied finalization");
    }
    /** Executes the installed native timeline read after real readoption; ACK DATA cannot stand in for this read. */
    public static RootDriverLifecyclePublicCodec.Timeline publicTimelineIsReadOnly(
            ContinuityStorePort.Session same,RootRuntimeContext context,
            RootLifecycleRuntimeFactory.Installed installed,RootDriverLifecyclePublicCodec.Query actualRequest,
            Instant deadline) throws IOException {
        if(same==null||context==null||installed==null||actualRequest==null||deadline==null)
            throw new IOException("MISSING_ACTUAL_ADMITTED_ROOT: actual installed timeline inputs are required; NOT_RUN is not PASS");
        installed.requireContext(context);context.writer().requireSession(same);
        var root=context.core().sessionAccess().current();context.core().requireCurrentForAccess(same,root);
        String head=same.head().digest();var before=known(context,same);
        StrictJson.require(RootDriverLifecyclePublicCodec.query(RootDriverLifecyclePublicCodec.encode(actualRequest)).equals(actualRequest),
                "actual admitted timeline request changed its canonical revision during serde");
        var actual=installed.natural().pendingRuntime().publicTimeline(actualRequest,deadline);
        var encoded=RootDriverLifecyclePublicCodec.encode(actual);
        var decoded=RootDriverLifecyclePublicCodec.decodeTimelineData(encoded);
        StrictJson.require(actual.machineId().equals(root.identity().machineId())
                &&actual.original().request().origin().machineId().equals(root.identity().machineId())
                &&actual.original().request().sessionId().equals(root.identity().sessionId())
                &&actual.original().request().before().game().equals(root.identity().game())
                &&actual.original().request().before().frame().revision().equals(actualRequest.expectedRevision())
                &&actual.original().original().nativeOk()
                &&actual.original().requestId().equals(actual.value().requestId())
                &&decoded.querySequence().equals(actual.value().sequence())
                &&decoded.observationRevision().equals(actual.value().observationRevision())
                &&decoded.snapshotRevision().equals(actualRequest.expectedRevision())
                &&decoded.machineId().equals(actual.machineId())&&decoded.observedAtUtc().equals(actual.observedAtUtc())
                &&Arrays.equals(encoded.bytes(),RootDriverLifecyclePublicCodec.encodeTimelineData(decoded).bytes()),
                "actual admitted timeline lost its native receipt, source revision or public uint64 serde");
        StrictJson.require(head.equals(same.head().digest())
                &&Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(before).bytes(),
                        DriverSnapshotFacts.encodeKnownOriginal(known(context,same)).bytes()),
                "actual admitted timeline changed canonical head/full Known or repeated the final business CAS");
        context.core().requireCurrentForAccess(same,root);return actual;
    }
    public static void foreignProducerCannotQualifyRoot(ContinuityStorePort.Session same,
            RootRuntimeContext actualContext,RootLifecycleRuntimeFactory.Installed installed,
            LifecycleEpisodeInputs foreignProducer,LifecycleEpisodeInputs.CurrentAdoptionBinding genuineForeign) throws IOException {
        installed.requireContext(actualContext);foreignProducer.requireCurrentAdoption(same,genuineForeign);
        String head=same.head().digest();boolean refused=false;
        try{installed.requireAdmittedCurrentProducer(same,genuineForeign);}catch(IOException|IllegalArgumentException missing){refused=true;}
        StrictJson.require(refused&&head.equals(same.head().digest()),"another real producer's current binding crossed the Root private issuer or changed the head");
    }
    private static DriverSnapshotFacts.Known known(RootRuntimeContext context,ContinuityStorePort.Session same)throws IOException {
        context.writer().requireSession(same);
        return context.adopted().authority().withFrozenFacts(same,frozen->{if(!(frozen.state() instanceof DriverSnapshotFacts.Known actual))throw new IOException("MISSING_ACTUAL_CURRENT_KNOWN");return actual;});
    }
}
