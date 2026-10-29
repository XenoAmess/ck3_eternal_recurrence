package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;

/** Actual operator physical originals. This package-private issuer supplies neither ordinary Ready nor actor-CAS permission. */
final class RootOperatorPhysicalEvidence {
    private static final int FRAME_LIMIT=Math.min(DriverJson.MAX_NATIVE_BYTES+4,ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES);
    private RootOperatorPhysicalEvidence() { }

    /** Private minting binds original bytes and physical qualification to one actual Root and writer scope. */
    static final class Captured {
        private final RootRuntimeContext context;
        private final RootApplicationSession root;
        private final ContinuityStorePort.Session same;
        private final FullSnapshot full;
        private final Known known;
        private final ExactRef hello,heartbeat,driver,auxiliary;
        private final SourceQualification source;
        private final Optional<RootNativeSourceAuthority.QualifiedMetadata> metadata;
        private final Instant deadline;
        private final Optional<NativeFreshSnapshotPort.Received> fresh;
        private Captured(RootRuntimeContext context,RootApplicationSession root,ContinuityStorePort.Session same,
                FullSnapshot full,Known known,ExactRef hello,ExactRef heartbeat,ExactRef driver,ExactRef auxiliary,
                SourceQualification source,Optional<RootNativeSourceAuthority.QualifiedMetadata> metadata,Instant deadline,Optional<NativeFreshSnapshotPort.Received> fresh) {
            this.context=context;this.root=root;this.same=same;this.full=full;this.known=known;
            this.hello=hello;this.heartbeat=heartbeat;this.driver=driver;this.auxiliary=auxiliary;
            this.source=source;this.metadata=Objects.requireNonNull(metadata);this.deadline=deadline;this.fresh=Objects.requireNonNull(fresh);
        }
        void requireRetained(ContinuityStorePort.Session borrowed)throws IOException {
            requireOwner(context,root,borrowed,deadline);
            StrictJson.require(borrowed==same,"operator physical originals escaped their original writer scope");
            source.assertCurrent(same);if(metadata.isPresent())metadata.orElseThrow().requireCurrent(same);
            var archive=context.archive().withSession(same);
            StrictJson.require(Arrays.equals(archive.loadNativeFrame(full.originalEvidence()),full.actual().originalPacket())
                    &&Arrays.equals(archive.loadFullMaterial(driver).bytes(),known.driver().encode()),
                    "operator physical packet or full predecessor Driver original changed");
            archive.loadFullMaterial(auxiliary);
            if(fresh.isPresent()){
                var received=fresh.get();
                received.acknowledgement().custody().orElseThrow(()->new IOException("actual independent READ custody is absent")).verify(received.acknowledgement());
                StrictJson.require(received.originalFrame().equals(full.actual()),"operator physical frame differs from the actual independent READ receipt");
            }
            context.archive().readArtifact(same,hello,1<<20);
            context.archive().readArtifact(same,heartbeat,1<<20);
        }
        Optional<NativeFreshSnapshotPort.Received> fresh(){return fresh;}
        FullSnapshot full(){return full;}
        Known known(){return known;}
        ExactRef hello(){return hello;}
        ExactRef heartbeat(){return heartbeat;}
        ExactRef driver(){return driver;}
        ExactRef auxiliary(){return auxiliary;}
        SourceQualification source(){return source;}
        Optional<RootNativeSourceAuthority.QualifiedMetadata> metadata(){return metadata;}
    }

    /** The original accepted BEFORE packet retains its actual timestamp and caller revision; it is not a new receive. */
    static Captured captureBefore(RootRuntimeContext context,RootApplicationSession root,ContinuityStorePort.Session same,
            Instant deadline)throws IOException,InterruptedException {
        return capture(context,root,same,deadline,false);
    }
    /** The AFTER call makes an independent native READ outside any prior Driver freeze, then projects Full DATA only. */
    static Captured capture(RootRuntimeContext context,RootApplicationSession root,ContinuityStorePort.Session same,
            Instant deadline)throws IOException,InterruptedException {
        return capture(context,root,same,deadline,true);
    }
    private static Captured capture(RootRuntimeContext context,RootApplicationSession root,ContinuityStorePort.Session same,
            Instant deadline,boolean independent)throws IOException,InterruptedException {
        requireOwner(context,root,same,deadline);
        var transport=context.transport();
        synchronized(transport) {
            transport.awaitHello(deadline);transport.verifyHeld(deadline);
            Optional<NativeFreshSnapshotPort.Received> fresh;
            ObservedFrame actual;
            if(independent){
                NativeFreshSnapshotPort.Result receivedFresh=transport.readFreshFullState(deadline);
                if(receivedFresh instanceof NativeFreshSnapshotPort.Unavailable unavailable)
                    receivedFresh=transport.collectFreshFullState(unavailable.dispatch().requestId(),deadline);
                if(!(receivedFresh instanceof NativeFreshSnapshotPort.Received received))
                    throw new IOException("actual source-bound fresh full-state READ is unavailable; preserve its original readonly attempt");
                fresh=Optional.of(received);actual=received.originalFrame();
            }else{
                fresh=Optional.empty();actual=transport.currentSnapshot(deadline);
            }
            requireOwner(context,root,same,deadline);
            StrictJson.require(actual.session().equals(context.adopted().session()),
                    "operator observation crossed the original adopted physical connection");
            ExactRef packet=context.archive().preserveArtifact(same,actual.originalPacket(),FRAME_LIMIT);
            return context.adopted().authority().withFrozenRawObservation(actual,same,frozen->{
                var known=frozen.state();var facts=frozen.facts();
                StrictJson.require(known.stamp().game().equals(root.identity().game())&&facts.source().equals(context.source())
                        &&facts.driverVersion()==known.stamp().driverVersion()&&facts.episodeEpoch()==known.stamp().episodeEpoch()
                        &&Arrays.equals(facts.driver().encode(),known.driver().encode()),
                        "operator physical originals crossed the actual frozen predecessor Driver");
                var full=context.core().observationAssembler().projectFull(actual,facts,packet);
                var received=transport.diagnostics();
                StrictJson.require(received.receivedState()==NativeGameTransport.ReceivedState.HELLO_VERIFIED
                        &&received.terminalFailure().isEmpty()&&received.session().filter(actual.session()::equals).isPresent(),
                        "operator physical transport is not the actual held verified connection");
                var hello=received.originalHello().orElseThrow(()->new IOException("operator actual HELLO is absent"));
                var heartbeat=received.latestHeartbeat().orElseThrow(()->new IOException("operator actual heartbeat is absent"));
                StrictJson.require(!actual.observedAt().isAfter(context.clock().instant())
                        &&!heartbeat.observedAt().isAfter(context.clock().instant())&&!hello.observedAt().isAfter(actual.observedAt()),
                        "operator original physical observation has a future or pre-HELLO timestamp");
                ExactRef helloRef=context.archive().preserveArtifact(same,hello.original().packet().value(),1<<20);
                ExactRef heartbeatRef=context.archive().preserveArtifact(same,heartbeat.original().packet().value(),1<<20);
                var source=context.sources().verifyPhysicalOrigin(same,actual.session(),context.source(),packet,received,deadline);
                var metadata=context.sources().optionalMetadata(same,source);
                var archive=context.archive().withSession(same);
                RawJson manifest=archive.loadFullMaterial(facts.semanticFactsEvidence());
                ExactRef driver=DriverObservationEvidenceReader.currentDriverReference(facts.semanticFactsEvidence(),manifest);
                StrictJson.require(Arrays.equals(archive.loadFullMaterial(driver).bytes(),known.driver().encode()),
                        "operator frozen predecessor differs from its original archived Driver");
                ExactRef auxiliary=archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(known.auxiliary())));
                var captured=new Captured(context,root,same,full,known,helloRef,heartbeatRef,driver,auxiliary,source,metadata,deadline,fresh);
                captured.requireRetained(same);return captured;
            });
        }
    }
    private static void requireOwner(RootRuntimeContext context,RootApplicationSession root,
            ContinuityStorePort.Session same,Instant deadline)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(root);Objects.requireNonNull(same);Objects.requireNonNull(deadline);
        context.writer().requireSession(same);context.requireCurrent(deadline);
        StrictJson.require(root.ownedBy(context.core())&&context.actions()==root&&context.adopted()==root.driver()
                &&context.writer()==root.writer()&&context.archive()==root.archive()
                &&context.core().sessionAccess().current()==root&&!root.isRetired(),
                "operator originals require the identical actual current Root/Core/Driver/writer/archive");
        StrictJson.require(context.clock().instant().isBefore(deadline),"operator physical read deadline expired");
    }
}
