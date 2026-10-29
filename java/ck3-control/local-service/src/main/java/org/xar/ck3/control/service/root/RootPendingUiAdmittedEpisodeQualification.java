package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs;
import org.xar.ck3.control.application.lifecycle.LifecycleHistoricalPublication;
import org.xar.ck3.control.application.lifecycle.LifecycleProofCodec;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** Joins an actual historical episode admission to independently captured current physical facts.
 * Historical publication DATA cannot mint a Base or authorize a Native action through this source.
 */
final class RootPendingUiAdmittedEpisodeQualification {
    private final RootRuntimeContext context;
    private final RootLifecycleRuntimeFactory.Installed lifecycle;
    private final LifecycleHistoricalPublication historical;
    private final LifecycleEpisodeInputs inputs;
    @FunctionalInterface interface SourceVerifier {
        void require(ContinuityStorePort.Session same,Optional<org.xar.ck3.control.contracts.ExactRef> retained,
                org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification actual) throws IOException;
    }
    private final SourceVerifier sources;

    RootPendingUiAdmittedEpisodeQualification(RootRuntimeContext actualContext,
            RootLifecycleRuntimeFactory.Installed sameLifecycle,SourceVerifier actualSources) throws IOException {
        context=Objects.requireNonNull(actualContext);lifecycle=Objects.requireNonNull(sameLifecycle);sources=Objects.requireNonNull(actualSources);
        lifecycle.requireContext(context);
        historical=new LifecycleHistoricalPublication(context.writer(),context.core().actions(),lifecycle.composite());
        inputs=new LifecycleEpisodeInputs(context.writer(),context.writer()::requireSession,lifecycle.composite(),
                context.adopted().authority(),context.archive(),context.semanticVerifier());
    }

    LifecycleEpisodeInputs requireCurrentProducer(ContinuityStorePort.Session same,
            LifecycleEpisodeInputs.CurrentAdoptionBinding actual) throws IOException {
        context.writer().requireSession(same);lifecycle.requireContext(context);inputs.requireCurrentAdoption(same,Objects.requireNonNull(actual));
        var root=context.core().sessionAccess().current();context.core().requireCurrentForAccess(same,root);
        StrictJson.require(root.driver()==context.adopted()&&actual.owner().equals(root.identity()),"current admission producer belongs to another actual Root owner");
        return inputs;
    }
    @FunctionalInterface interface CurrentWork<T> {
        T run(LifecycleEpisodeInputs.CurrentAdoptionBinding actual,RootLifecycleAuthority.SnapshotLease held) throws IOException;
    }
    Optional<LifecycleEpisodeInputs.CurrentAdoptionBinding> bind(ContinuityStorePort.Session same,
            ActionReceipt exactParent,Instant deadline) throws IOException {
        return withCurrent(same,exactParent,deadline,(actual,held)->actual);
    }
    /** Separate current role; the caller holds a new actual NS/M3 lease, never a historical public JSON token. */
    <T>Optional<T> withTransportedCurrent(ContinuityStorePort.Session same,ActionReceipt exactParent,
            org.xar.ck3.control.application.session.ContinuityBatchJournal.ReboundTransport transport,
            RootLifecycleAuthority.SnapshotLease lease,CurrentWork<T> work)throws IOException {
        context.writer().requireSession(same);lifecycle.requireContext(context);lease.assertCurrent(same);
        var root=context.core().sessionAccess().current();context.core().requireCurrentForAccess(same,root);
        StrictJson.require(root.driver()==context.adopted()&&root.writer()==context.writer()&&root.archive()==context.archive()
                &&root.identity().equals(transport.owner()),"transported current belongs to another actual Root owner");
        root.batchJournal().requireHistoricalTransport(same,transport);
        var original=historical.read(same,exactParent.command().actionId());
        StrictJson.require(original.parent().equals(exactParent)
                &&Arrays.equals(ActionCodec.encodeCommand(transport.parent()),ActionCodec.encodeCommand(exactParent.command())),
                "transported current changed the exact canonical settled parent");
        var retained=root.batchJournal().transportedHistoricalEpisodeAdoption(same,root.identity(),original,transport);
        if(retained.isEmpty())return Optional.empty();var ticket=retained.orElseThrow();ticket.requireCurrent(same);
        var source=lease.sourceQualification();source.assertCurrent(same);
        sources.require(same,exactParent.command().lifecycleBefore().evidence().completeSourceQualification(),source);
        var complete=lease.ordinary().orElseThrow(()->new IOException("transported current is not actual complete living gameplay"));
        StrictJson.require(complete.sessionId().equals(root.identity().sessionId())&&complete.identity().game().equals(root.identity().game())
                &&complete.source().equals(context.source())&&Arrays.equals(lease.factsKnown().driver().encode(),lease.fullSnapshot().facts().driver().encode()),
                "transported physical current differs from its actual complete Driver/owner/source");
        String head=same.head().digest();var fresh=lifecycle.physical().semantic(same,root.identity(),lease);
        var actual=inputs.bindTransportedCurrent(same,ticket,fresh);actual.requireCurrent(same);
        T result=Objects.requireNonNull(work.run(actual,lease));actual.requireCurrent(same);
        sources.require(same,exactParent.command().lifecycleBefore().evidence().completeSourceQualification(),source);
        source.assertCurrent(same);lease.assertCurrent(same);
        StrictJson.require(head.equals(same.head().digest()),"transported current consumer changed its independently captured current head");
        return Optional.of(result);
    }
    <T> Optional<T> withCurrent(ContinuityStorePort.Session same,ActionReceipt exactParent,Instant deadline,
            CurrentWork<T> work) throws IOException {
        Objects.requireNonNull(work);
        context.writer().requireSession(same);Objects.requireNonNull(exactParent);Objects.requireNonNull(deadline);
        StrictJson.require(context.clock().instant().isBefore(deadline),"historical adoption needs a fresh finite physical observation window");
        lifecycle.requireContext(context);
        var root=context.core().sessionAccess().current();context.core().requireCurrentForAccess(same,root);
        StrictJson.require(root.driver()==context.adopted()&&root.writer()==context.writer()&&root.archive()==context.archive()
                &&root.identity().machineId().equals(context.game().machineId())&&root.identity().game().equals(context.game().generation())
                &&root.identity().sessionId().equals(context.game().sessionId()),"historical adoption crossed its actual admitted Root/physical Game/session");
        StrictJson.require(exactParent.state() instanceof ActionState.CompositeSettled settled
                &&settled.settlement() instanceof ActionState.LifecycleApplied,"historical adoption requires its actual settled lifecycle parent");
        var actualProof=((ActionState.LifecycleApplied)((ActionState.CompositeSettled)exactParent.state()).settlement()).proof();
        var original=historical.read(same,exactParent.command().actionId());
        StrictJson.require(original.parent().version()==exactParent.version()&&original.parent().sequence()==exactParent.sequence()
                &&original.parent().bodySha256().equals(exactParent.bodySha256())
                &&Arrays.equals(ActionCodec.encodeCommand(original.parent().command()),ActionCodec.encodeCommand(exactParent.command()))
                &&Arrays.equals(LifecycleProofCodec.encode(original.proof()),LifecycleProofCodec.encode(actualProof)),
                "historical adoption changed the exact actual canonical lifecycle parent/proof");
        var retained=root.batchJournal().historicalEpisodeAdoption(same,root.identity(),original);
        if(retained.isEmpty())return Optional.empty();
        var ticket=retained.orElseThrow();ticket.requireCurrent(same);
        String head=same.head().digest();
        return lifecycle.physical().withSnapshot(same,deadline,lease->{
            lease.assertCurrent(same);ticket.requireCurrent(same);
            var full=lease.fullSnapshot();var known=lease.factsKnown();
            var complete=lease.ordinary().orElseThrow(()->new IOException("actual admitted episode current raw/Driver join is not living and complete"));
            var source=lease.sourceQualification();source.assertCurrent(same);
            var metadata=context.sources().optionalMetadata(same,source);
            sources.require(same,exactParent.command().lifecycleBefore().evidence().completeSourceQualification(),source);
            StrictJson.require(complete.identity().machineId().equals(root.identity().machineId())
                    &&complete.identity().game().equals(root.identity().game())&&complete.sessionId().equals(root.identity().sessionId())
                    &&complete.source().equals(context.source())
                    &&complete.connectionGeneration().equals(exactParent.command().lifecycleBefore().connectionGeneration())
                    &&known.stamp().driverVersion()==full.facts().driverVersion()
                    &&known.stamp().episodeEpoch()==full.facts().episodeEpoch()
                    &&Arrays.equals(known.driver().encode(),full.facts().driver().encode()),
                    "actual admitted current physical/source/full Driver facts differ");
            // The sole physical SEM producer borrows this exact active lease; it performs no second capture.
            var fresh=lifecycle.physical().semantic(same,root.identity(),lease);
            var bound=inputs.bindAdmittedCurrent(same,ticket,fresh);bound.requireCurrent(same);
            T result=Objects.requireNonNull(work.run(bound,lease),"actual admitted current work returned no result");
            bound.requireCurrent(same);
            sources.require(same,exactParent.command().lifecycleBefore().evidence().completeSourceQualification(),source);
            if(metadata.isPresent())metadata.orElseThrow().requireCurrent(same);source.assertCurrent(same);lease.assertCurrent(same);
            StrictJson.require(head.equals(same.head().digest()),"historical adoption qualification changed the actual canonical writer head");
            context.core().requireCurrentForAccess(same,root);context.writer().requireSession(same);
            return Optional.of(result);
        });
    }
}
