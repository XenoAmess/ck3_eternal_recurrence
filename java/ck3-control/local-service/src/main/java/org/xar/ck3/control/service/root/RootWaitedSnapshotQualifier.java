package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverObservationFacts;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeGameTransport;

/** Qualifies one already waited FullSnapshot for DATA export. It neither observes again nor grants ordinary readiness or actions. */
public final class RootWaitedSnapshotQualifier {
    private RootWaitedSnapshotQualifier() { }
    @FunctionalInterface public interface QualifiedWork<T> {T read(Qualified actual)throws IOException;}
    /** Private construction and callback lifetime prevent bare JSON/full DATA from becoming a Root source qualification. */
    public static final class Qualified {
        private final RootApplicationSession root;
        private final RootRuntimeContext context;
        private final ContinuityStorePort.Session same;
        private final FullSnapshot actual;
        private final Instant deadline;
        private final String head;
        private final long sequence;
        private final NativeReadinessCollector.SourceQualification qualification;
        private final java.util.Optional<RootNativeSourceAuthority.QualifiedMetadata> metadata;
        private final PublicSnapshotCodec.FullSnapshotOriginals originals;
        private final Thread thread=Thread.currentThread();
        private boolean active=true;
        private Qualified(RootApplicationSession root,RootRuntimeContext context,ContinuityStorePort.Session same,
                FullSnapshot actual,Instant deadline,String head,long sequence,
                NativeReadinessCollector.SourceQualification qualification,java.util.Optional<RootNativeSourceAuthority.QualifiedMetadata> metadata,
                PublicSnapshotCodec.FullSnapshotOriginals originals) {
            this.root=root;this.context=context;this.same=same;this.actual=actual;this.deadline=deadline;
            this.head=head;this.sequence=sequence;this.qualification=qualification;this.metadata=metadata;this.originals=originals;
        }
        public void requireCurrent()throws IOException {
            require(active&&thread==Thread.currentThread(),"waited source qualification escaped its actual callback/thread");
            requireOwner(root,context,same,deadline);unchangedHead(same,head,sequence);
            sameFrame(actual.actual(),context.transport().currentSnapshot(deadline));
            qualification.assertCurrent(same);if(metadata.isPresent())metadata.orElseThrow().requireCurrent(same);
            unchangedHead(same,head,sequence);
        }
        public PublicSnapshotCodec.FullSnapshotOriginals originals()throws IOException {requireCurrent();return originals;}
        public java.util.Optional<String> ownerSourceEpoch()throws IOException {requireCurrent();return metadata.map(RootNativeSourceAuthority.QualifiedMetadata::ownerSourceEpoch);}
        public java.util.Optional<ExactRef> gameExecutable()throws IOException {requireCurrent();return metadata.map(RootNativeSourceAuthority.QualifiedMetadata::gameExecutable);}
    }
    /** Caller holds root.withPublicStandaloneRead: this joins that exact calls/writer scope and never acquires another observation. */
    public static <T>T withQualified(RootApplicationSession root,RootRuntimeContext context,
            ContinuityStorePort.Session same,FullSnapshot waited,Instant deadline,QualifiedWork<T> work)throws IOException {
        Objects.requireNonNull(root);Objects.requireNonNull(context);Objects.requireNonNull(same);
        Objects.requireNonNull(waited);Objects.requireNonNull(deadline);Objects.requireNonNull(work);
        try {
            require(waited.actual()!=null&&waited.facts()!=null&&waited.semantic()!=null&&waited.originalEvidence()!=null&&waited.fullBindingSha256()!=null,
                    "waited FullSnapshot has missing actual Native/Driver/source material");
            requireOwner(root,context,same,deadline);var originalHead=same.head();
            String head=originalHead.digest();long sequence=originalHead.state().sequence();
            var adopted=context.adopted();var transport=context.transport();
            adopted.producer().requireSameTransport(transport,context.source());
            return adopted.authority().withFrozenFacts(same,frozen->{
                require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual current Driver facts unavailable for waited DATA");
                var known=(DriverSnapshotFacts.Known)frozen.state();
                DriverObservationFacts facts=known.observation().orElseThrow(()->new IOException("actual current Driver has no waited observation facts"));
                require(known.stamp().game().equals(root.identity().game())&&known.stamp().driverVersion()==facts.driverVersion()
                        &&known.stamp().episodeEpoch()==facts.episodeEpoch()&&known.stamp().episodeRunId().equals(facts.driver().session().episodeRunId())
                        &&Arrays.equals(known.driver().encode(),facts.driver().encode()),"waited DATA crossed the authoritative complete Driver/stamp");
                require(facts.source().equals(context.source()),"waited DATA crossed actual Root source");
                var archive=context.archive().withSession(same);
                byte[] nativePacket=archive.loadNativeFrame(waited.originalEvidence());
                requireExact(waited.originalEvidence(),nativePacket,"waited original native packet");
                require(Arrays.equals(nativePacket,waited.actual().originalPacket()),"waited original packet is not the archived original");
                RawJson manifest=archive.loadMaterial(facts.semanticFactsEvidence());
                ExactRef driverReference=DriverObservationEvidenceReader.currentDriverReference(facts.semanticFactsEvidence(),manifest);
                RawJson driver=archive.loadMaterial(driverReference);
                FullSnapshot verified=verifyData(waited,transport.currentSnapshot(deadline),facts,manifest,driver,context.core().observationAssembler());
                require(verified.actual().session().equals(adopted.session()),"waited DATA crossed the adopted transport connection generation");
                require(!verified.actual().observedAt().isAfter(context.clock().instant())&&!verified.actual().observedAt().isAfter(deadline),
                        "actual waited packet carries a future observation time");
                var received=transport.diagnostics();
                require(received.receivedState()==NativeGameTransport.ReceivedState.HELLO_VERIFIED
                        &&received.session().filter(verified.actual().session()::equals).isPresent(),"actual waited transport session is not held");
                var hello=received.originalHello().orElseThrow(()->new IOException("actual waited transport HELLO missing"));
                var heartbeat=received.latestHeartbeat().orElseThrow(()->new IOException("actual waited transport heartbeat missing"));
                ExactRef helloRef=context.archive().preserveArtifact(same,hello.original().packet().value(),FRAME_LIMIT);
                ExactRef heartbeatRef=context.archive().preserveArtifact(same,heartbeat.original().packet().value(),FRAME_LIMIT);
                // This is the actual physical source authority. A capability string, copied receipt or DATA codec cannot mint it.
                var qualification=context.sources().verifyPhysicalOrigin(same,verified.actual().session(),context.source(),verified.originalEvidence(),received,deadline);
                var metadata=context.sources().optionalMetadata(same,qualification);
                var originals=new PublicSnapshotCodec.FullSnapshotOriginals(verified,helloRef,heartbeatRef,qualification.proof(),manifest,driver);
                var scoped=new Qualified(root,context,same,verified,deadline,head,sequence,qualification,metadata,originals);
                Throwable originalFailure=null;
                try {
                    scoped.requireCurrent();T result=work.read(scoped);scoped.requireCurrent();
                    // The callback cannot turn a frozen Driver replacement into the original waited facts.
                    adopted.authority().withFrozenFacts(same,ending->{
                        require(ending.state() instanceof DriverSnapshotFacts.Known,"actual Driver disappeared during waited DATA export");
                        var current=(DriverSnapshotFacts.Known)ending.state();
                        require(current.stamp().equals(known.stamp())&&Arrays.equals(current.driver().encode(),known.driver().encode())
                                &&current.originalHistoryBasis().equals(known.originalHistoryBasis())&&current.actionRows().equals(known.actionRows())
                                &&current.auxiliary().equals(known.auxiliary())&&current.loop().equals(known.loop()),"waited DATA export replaced the actual frozen Driver/facts");
                        sameFacts(facts,current.observation().orElseThrow(()->new IOException("actual waited observation was replaced")));return null;
                    });
                    unchangedHead(same,head,sequence);return result;
                }catch(IOException|RuntimeException|Error failure){originalFailure=failure;throw failure;}
                finally {
                    try{scoped.requireCurrent();}
                    catch(IOException changed){if(originalFailure!=null)originalFailure.addSuppressed(changed);else throw changed;}
                    finally{scoped.active=false;}
                }
            });
        }catch(UncheckedIOException unavailable){throw unavailable.getCause();}
        catch(IllegalArgumentException|IllegalStateException|java.util.NoSuchElementException unavailable) {
            throw new IOException("actual waited snapshot source qualification unavailable: "+unavailable.getMessage(),unavailable);
        }
    }
    private static final int FRAME_LIMIT=Math.min(DriverJson.MAX_NATIVE_BYTES+4,ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES);
    private static void requireOwner(RootApplicationSession root,RootRuntimeContext context,ContinuityStorePort.Session same,Instant deadline)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(deadline);
        require(root.ownedBy(context.core())&&!root.isRetired()&&context.core().sessionAccess().current()==root
                &&context.actions()==root&&context.adopted()==root.driver()&&context.writer()==root.writer()
                &&context.archive()==root.archive()&&context.core().archive()==root.archive(),"waited DATA crossed actual current Core/Root/Driver/writer/archive");
        var session=root.identity();var actual=context.adopted().session();
        require(actual.machineId().equals(session.machineId())&&actual.game().equals(session.game())&&actual.sessionId().equals(session.sessionId())
                &&context.source().machineId().equals(session.machineId()),"waited DATA crossed actual current physical Game/session");
    }
    /** Sole DATA verifier used by actual qualification and producer/consumer regression. It cannot construct Qualified. */
    static FullSnapshot verifyData(FullSnapshot supplied,ObservedFrame cached,DriverObservationFacts currentFacts,
            RawJson originalFacts,RawJson originalDriver,DriverObservationAssembler assembler)throws IOException {
        require(supplied!=null&&supplied.actual()!=null&&supplied.facts()!=null&&supplied.semantic()!=null
                &&supplied.originalEvidence()!=null&&supplied.fullBindingSha256()!=null&&cached!=null&&currentFacts!=null
                &&originalFacts!=null&&originalDriver!=null&&assembler!=null,"waited DATA has missing original Native/Driver/source fields");
        try {
            sameFrame(supplied.actual(),cached);sameFacts(supplied.facts(),currentFacts);
            requireExact(supplied.originalEvidence(),cached.originalPacket(),"current waited packet");
            ObservedFrame reconstructed=DriverObservationEvidenceReader.nativeFrame(currentFacts.semanticFactsEvidence(),originalFacts,cached.originalPacket());
            sameFrame(cached,reconstructed);
            DriverObservationFacts decoded=DriverObservationEvidenceReader.decode(currentFacts.semanticFactsEvidence(),originalFacts,originalDriver,reconstructed);
            sameFacts(currentFacts,decoded);
            FullSnapshot verified=assembler.projectFull(cached,currentFacts,supplied.originalEvidence());
            require(verified.semantic().equals(supplied.semantic())&&verified.fullBindingSha256().equals(supplied.fullBindingSha256())
                    &&verified.originalEvidence().equals(supplied.originalEvidence()),"waited full semantic/source binding differs from actual cached Native and current Driver originals");
            return verified;
        }catch(IllegalArgumentException|IllegalStateException malformed){throw new IOException("waited Native/Driver original DATA unavailable: "+malformed.getMessage(),malformed);}
    }
    private static void sameFrame(ObservedFrame expected,ObservedFrame actual)throws IOException {
        require(expected.session().equals(actual.session())&&expected.snapshotId().equals(actual.snapshotId())
                &&expected.nativeRevision().equals(actual.nativeRevision())&&expected.observedAt().equals(actual.observedAt())
                &&Arrays.equals(expected.state().bytes(),actual.state().bytes())&&Arrays.equals(expected.originalPacket(),actual.originalPacket()),
                "waited packet differs from actual cached original Native frame/session/revision/time");
    }
    private static void sameFacts(DriverObservationFacts expected,DriverObservationFacts actual)throws IOException {
        require(expected.driverVersion()==actual.driverVersion()&&expected.episodeEpoch()==actual.episodeEpoch()
                &&expected.transport().equals(actual.transport())&&expected.snapshotId().equals(actual.snapshotId())
                &&expected.nativeRevision().equals(actual.nativeRevision())&&expected.nativeStateSha256().equals(actual.nativeStateSha256())
                &&expected.publicRevision().equals(actual.publicRevision())&&expected.observationVersion()==actual.observationVersion()
                &&expected.source().equals(actual.source())&&expected.originalSemanticFields().equals(actual.originalSemanticFields())
                &&expected.semanticFactsEvidence().equals(actual.semanticFactsEvidence())&&Arrays.equals(expected.driver().encode(),actual.driver().encode()),
                "waited facts differ from actual authoritative Driver/version/episode/source/manifest");
    }
    private static void unchangedHead(ContinuityStorePort.Session same,String digest,long sequence)throws IOException {
        var current=same.head();require(current.digest().equals(digest)&&current.state().sequence()==sequence,"waited DATA qualification/export changed the canonical writer head");
    }
    private static void requireExact(ExactRef source,byte[] bytes,String role)throws IOException {
        require(source.bytes()==bytes.length&&source.sha256().equals(DriverJson.sha256(bytes)),role+" differs from its exact preserved reference");
    }
    private static void require(boolean condition,String reason)throws IOException {if(!condition)throw new IOException(reason);}
}
