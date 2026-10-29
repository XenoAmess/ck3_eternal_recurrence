package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.NativeProof;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Request;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.platform.ManagedGameSession;

/** Current physical Game custody plus the actual native/package closure, scoped to the original writer. */
public final class RootNativeSourceAuthority implements NativeReadinessCollector.SourceAuthority {
    private final ContinuityWriter writer;
    private final NativeOutcomeArchive archive;
    private final ManagedGameSession game;
    private record HistoricalPackage(RootPackageNativeVerifier verifier,Request request,FileRef hostConfiguration) {
        HistoricalPackage {Objects.requireNonNull(verifier);Objects.requireNonNull(request);Objects.requireNonNull(hostConfiguration);}
    }
    private final java.util.Optional<HistoricalPackage> historical;
    private final Clock clock;
    private final java.util.IdentityHashMap<NativeReadinessCollector.SourceQualification, QualifiedMetadata> qualified = new java.util.IdentityHashMap<>();
    private QualifiedMetadata latestQualified;
    /** Only this source authority creates metadata after actual physical qualification. A digest alone grants no authority. */
    public static final class QualifiedMetadata {
        private final RootNativeSourceAuthority owner;
        private final ContinuityStorePort.Session session;
        private final NativeReadinessCollector.SourceQualification qualification;
        private final String epoch;
        private final ExactRef executable, manifest;
        private final org.xar.ck3.control.continuity.writer.WriterContracts.Pin manifestPin;
        private QualifiedMetadata(RootNativeSourceAuthority owner, ContinuityStorePort.Session session,
                NativeReadinessCollector.SourceQualification qualification, String epoch, ExactRef executable, ExactRef manifest,
                org.xar.ck3.control.continuity.writer.WriterContracts.Pin manifestPin) {
            this.owner=owner;this.session=session;this.qualification=qualification;this.epoch=epoch;this.executable=executable;this.manifest=manifest;this.manifestPin=manifestPin;
        }
        public String ownerSourceEpoch() { return epoch; }
        public ExactRef gameExecutable() { return executable; }
        public ExactRef epochManifest() { return manifest; }
        public void requireCurrent(ContinuityStorePort.Session borrowed) throws IOException {
            owner.writer.requireSession(borrowed);
            if (borrowed != session) throw new IOException("qualified source metadata escaped its original writer scope");
            qualification.assertCurrent(borrowed); borrowed.verifyPin(manifestPin);
        }
    }
    public QualifiedMetadata metadata(ContinuityStorePort.Session borrowed, NativeReadinessCollector.SourceQualification actual) throws IOException {
        return optionalMetadata(borrowed,actual).orElseThrow(()->new IOException("historical source metadata is absent in the ordinary runtime"));
    }
    public java.util.Optional<QualifiedMetadata> optionalMetadata(ContinuityStorePort.Session borrowed, NativeReadinessCollector.SourceQualification actual) throws IOException {
        Objects.requireNonNull(actual);writer.requireSession(borrowed);
        if(actual.proof().isEmpty())return java.util.Optional.empty();
        writer.requireSession(borrowed); QualifiedMetadata result;
        synchronized (qualified) { result=qualified.get(Objects.requireNonNull(actual)); }
        if (result == null) throw new IOException("source qualification was not minted by this actual physical source authority");
        result.requireCurrent(borrowed); return java.util.Optional.of(result);
    }
    /** Reuses only this authority's latest real qualification in the identical active writer scope. */
    public QualifiedMetadata currentMetadata(ContinuityStorePort.Session borrowed)throws IOException {
        return optionalCurrentMetadata(borrowed).orElseThrow(()->new IOException("historical source metadata is absent in the ordinary runtime"));
    }
    public java.util.Optional<QualifiedMetadata> optionalCurrentMetadata(ContinuityStorePort.Session borrowed)throws IOException {
        writer.requireSession(borrowed);QualifiedMetadata result;
        synchronized(qualified){result=latestQualified;}
        if(historical.isEmpty())return java.util.Optional.empty();
        if(result==null||result.session!=borrowed)throw new IOException("actual current source metadata has not been qualified in this writer scope");
        result.requireCurrent(borrowed);return java.util.Optional.of(result);
    }
    /** Historical DATA only: reopens a manifest previously issued by this authority. This never
     * refreshes its qualification, invokes an expired guard, or grants a current source epoch. */
    public java.util.Optional<ExactRef> retainedEpochManifestOriginal(ContinuityStorePort.Session same) throws IOException {
        writer.requireSession(same); final QualifiedMetadata original;
        synchronized (qualified) { original=latestQualified; }
        if (original==null) return java.util.Optional.empty();
        ExactRef retained=original.epochManifest();
        var pin=same.capturePin(retained,16<<20);
        byte[] bytes=archive.readArtifact(same,retained,16<<20);
        if (bytes.length!=retained.bytes()
                || !org.xar.ck3.control.application.driver.DriverJson.sha256(bytes).equals(retained.sha256()))
            throw new IOException("retained historical source-epoch original differs");
        same.verifyPin(pin); return java.util.Optional.of(retained);
    }
    /** Historical origin verification uses original v3 witnesses, never a current or expired live guard. */
    public void requireArchivedOrigin(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.action.GuardEvidence original,
            org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive originals) throws IOException {
        if(historical.isEmpty())return;
        RootArchivedNativeSourceReader.requireOrigin(writer,archive,same,original,originals);
    }
    /** Ordinary runtime has no historical package/source qualification to issue. */
    public RootNativeSourceAuthority(ContinuityWriter writer,NativeOutcomeArchive archive,ManagedGameSession game,Clock clock) {
        this.writer=Objects.requireNonNull(writer);this.archive=Objects.requireNonNull(archive);
        this.game=Objects.requireNonNull(game);this.clock=Objects.requireNonNull(clock);historical=java.util.Optional.empty();
        if(archive.writer()!=writer)throw new IllegalArgumentException("runtime must retain the same writer/archive");
    }
    public RootNativeSourceAuthority(ContinuityWriter writer, NativeOutcomeArchive archive, ManagedGameSession game,
            RootPackageNativeVerifier verifier, Request request, FileRef actualHostConfiguration, Clock clock) {
        this.writer = Objects.requireNonNull(writer); this.archive = Objects.requireNonNull(archive); this.game = Objects.requireNonNull(game);
        historical=java.util.Optional.of(new HistoricalPackage(verifier,request,actualHostConfiguration));this.clock = Objects.requireNonNull(clock);
        if (archive.writer() != writer) throw new IllegalArgumentException("source authority must share the exact original writer/archive");
    }
    @Override public NativeReadinessCollector.SourceQualification verify(ContinuityStorePort.Session borrowed,
            SessionIdentity identity, Complete frame, Known driver, NativeGameTransport.TransportDiagnostics received,
            GameLifecycle.Running process, Instant deadline) throws IOException {
        if(historical.isEmpty())return NativeReadinessCollector.SourceQualification.none();
        writer.requireSession(borrowed); requireGame(identity, frame, process, deadline);
        if (!driver.stamp().game().equals(identity.game()) || !driver.stamp().episodeRunId().equals(frame.identity().frame().episodeRunId()))
            throw new IOException("source authority received a different original Driver episode");
        return qualify(borrowed, identity, frame.source().sourceRef(), received, deadline);
    }
    /** Frontend uses the same physical source authority without fabricating a gameplay actor or Driver. */
    public NativeReadinessCollector.SourceQualification verifyFrontend(ContinuityStorePort.Session borrowed,
            org.xar.ck3.control.application.action.NativeObservationPort.TransportSession transport,
            org.xar.ck3.control.g2.common.G2Source source, ExactRef actualRoutePacket,
            NativeGameTransport.TransportDiagnostics received, Instant deadline) throws IOException {
        return verifyPhysicalOrigin(borrowed, transport, source, actualRoutePacket, received, deadline);
    }
    /** Terminal native observations retain their actual predecessor Driver and never fabricate a gameplay/frontend actor. */
    public NativeReadinessCollector.SourceQualification verifyLifecycle(ContinuityStorePort.Session borrowed,
            org.xar.ck3.control.application.action.NativeObservationPort.TransportSession transport,
            org.xar.ck3.control.g2.common.G2Source source, ExactRef actualNativeSnapshot,
            NativeGameTransport.TransportDiagnostics received, Instant deadline) throws IOException {
        if(historical.isEmpty())return NativeReadinessCollector.SourceQualification.none();
        writer.requireSession(borrowed);
        var observed=game.nativeTransport().latestObservedSnapshot().orElseThrow(()->new IOException("actual owned terminal Native snapshot absent"));
        byte[] original=archive.readArtifact(borrowed,actualNativeSnapshot,Math.min(org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES+4,
                org.xar.ck3.control.continuity.writer.ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES));
        if(!observed.session().equals(transport)||!java.util.Arrays.equals(observed.originalPacket(),original))
            throw new IOException("terminal original packet is not the actual ManagedGameSession transport's latest snapshot");
        return verifyPhysicalOrigin(borrowed, transport, source, actualNativeSnapshot, received, deadline);
    }
    /** A source qualification covers physical source custody only; origin-specific codecs and guards prove its business route. */
    public NativeReadinessCollector.SourceQualification verifyPhysicalOrigin(ContinuityStorePort.Session borrowed,
            org.xar.ck3.control.application.action.NativeObservationPort.TransportSession transport,
            org.xar.ck3.control.g2.common.G2Source source, ExactRef actualOriginPacket,
            NativeGameTransport.TransportDiagnostics received, Instant deadline) throws IOException {
        if(historical.isEmpty())return NativeReadinessCollector.SourceQualification.none();
        writer.requireSession(borrowed); Objects.requireNonNull(source); Objects.requireNonNull(actualOriginPacket);
        SessionIdentity identity = new SessionIdentity(transport.machineId(), transport.game(), transport.sessionId());
        // This exact packet must already have been physically archived by its actual origin producer under this writer.
        archive.readArtifact(borrowed, actualOriginPacket, Math.min(org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES + 4,
                org.xar.ck3.control.continuity.writer.ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES));
        if (!source.machineId().equals(identity.machineId()) || !received.session().orElseThrow().equals(transport))
            throw new IOException("actual origin and held transport source differ");
        return qualify(borrowed, identity, source.sourceRef(), received, deadline);
    }
    private NativeReadinessCollector.SourceQualification qualify(ContinuityStorePort.Session borrowed,
            SessionIdentity identity, ExactRef sourceRef, NativeGameTransport.TransportDiagnostics received, Instant deadline) throws IOException {
        HistoricalPackage configured=historical.orElseThrow();
        RootPackageNativeVerifier verifier=configured.verifier();Request request=configured.request();FileRef hostConfiguration=configured.hostConfiguration();
        writer.requireSession(borrowed); requirePhysicalGame(identity, deadline); game.verify();
        var actualDiagnostics = game.nativeTransport().diagnostics();
        if (!actualDiagnostics.session().equals(received.session()) || actualDiagnostics.receivedState() != received.receivedState()
                || !java.util.Arrays.equals(actualDiagnostics.originalHello().orElseThrow().original().packet().value(), received.originalHello().orElseThrow().original().packet().value())
                || !java.util.Arrays.equals(actualDiagnostics.latestHeartbeat().orElseThrow().original().packet().value(), received.latestHeartbeat().orElseThrow().original().packet().value()))
            throw new IOException("source qualification does not hold the collector's actual transport diagnostics");
        NativeProof proof = verifier.verify(request, hostConfiguration);
        var sourceDataPin = borrowed.capturePin(sourceRef, org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);
        if (!proof.machineId().equals(identity.machineId()) || !game.launchPlan().sources().review().gameExecutable().equals(proof.expected().gameExecutable()))
            throw new IOException("current managed Game differs from actual package/native proof");
        List<SharedSourceFiles.Witness> held = new ArrayList<>();
        hostConfiguration.verify();
        SharedSourceFiles.Witness hostWitness = SharedSourceFiles.observe(Path.of(hostConfiguration.path()));
        if (hostWitness.source().bytes() != hostConfiguration.bytes() || !hostWitness.source().sha256().equals(hostConfiguration.sha256())
                || !Path.of(hostWitness.source().path()).toRealPath().equals(Path.of(hostConfiguration.path()).toRealPath()))
            throw new IOException("actual host configuration changed while acquiring source custody");
        held.add(hostWitness);
        java.util.LinkedHashMap<String,FileRef> custody = new java.util.LinkedHashMap<>();
        for (FileRef source : proof.completeEvidenceClosure()) retainCustody(custody,source);
        for (FileRef source : game.launchPlan().sources().review().completeRuntimeSources()) retainCustody(custody,source);
        // Retain every stable-epoch role explicitly, even when another evidence closure only
        // references its manifest. The original native identity cannot be reconstructed later.
        for (FileRef source : proof.expected().completeSources()) retainCustody(custody,source);
        retainCustody(custody,proof.expected().bridgeDll()); retainCustody(custody,proof.expected().injector());
        retainCustody(custody,proof.expected().gameExecutable()); retainCustody(custody,proof.expected().launcherSettings());
        for (FileRef source : custody.values()) {
            source.verify(); SharedSourceFiles.Witness witness = SharedSourceFiles.observe(Path.of(source.path()));
            if (witness.source().bytes() != source.bytes() || !witness.source().sha256().equals(source.sha256())
                    || !Path.of(witness.source().path()).toRealPath().equals(Path.of(source.path()).toRealPath()))
                throw new IOException("source changed while acquiring physical custody"); held.add(witness);
        }
        ExactRef epochManifest = sourceEpoch(borrowed, proof);
        var epochPin = borrowed.capturePin(epochManifest,16<<20);
        var document = RootNativeSourceProofProducer.document(identity,clock.instant().toString(),proof,
                hostConfiguration,sourceRef,epochManifest,held);
        byte[] encoded = org.xar.ck3.control.application.readiness.NativeSourceProofCodec.encode(document);
        if (encoded.length < 1 || encoded.length > (16 << 20)) throw new IOException("complete source proof exceeds finite role limit");
        ExactRef retained = archive.preserveArtifact(borrowed, encoded, 16 << 20);
        if (!java.util.Arrays.equals(encoded,archive.readArtifact(borrowed,retained,16<<20)))
            throw new IOException("original v3 source proof differs from its actual immutable readback");
        NativeReadinessCollector.SourceGuard guard = actualSession -> {
            writer.requireSession(actualSession);
            if (actualSession != borrowed) throw new IOException("source qualification cannot move to another writer session");
            requirePhysicalGame(identity, deadline); game.verify();
            actualSession.verifyPin(sourceDataPin);
            actualSession.verifyPin(epochPin);
            for (SharedSourceFiles.Witness witness : held) SharedSourceFiles.assertUnchanged(witness);
            if (!verifier.verify(request, hostConfiguration).equals(proof)) throw new IOException("actual native/package proof changed within readiness scope");
            for (SharedSourceFiles.Witness witness : held) SharedSourceFiles.assertUnchanged(witness);
        };
        guard.assertCurrent(borrowed);
        var qualification = new NativeReadinessCollector.SourceQualification(retained, guard);
        var metadata = new QualifiedMetadata(this,borrowed,qualification,epochManifest.sha256(),exact(proof.expected().gameExecutable()),epochManifest,epochPin);
        synchronized (qualified) {
            qualified.entrySet().removeIf(entry -> entry.getValue().session != borrowed);
            if (qualified.size() >= 256) throw new IOException("bounded active source qualifications exceeded; retain the original scope");
            qualified.put(qualification,metadata);
            latestQualified=metadata;
        }
        return qualification;
    }
    private record EpochInput(String role,FileRef source) { }
    /** Stable software identity: actual reviewed inputs only; no observation timestamp, Game PID, grant receipt or transient proof hash. */
    private ExactRef sourceEpoch(ContinuityStorePort.Session borrowed,NativeProof proof) throws IOException {
        java.util.TreeMap<String,EpochInput> selected=new java.util.TreeMap<>();
        for (FileRef ref:game.launchPlan().sources().review().completeRuntimeSources()) epochInput(selected,"java_runtime",ref);
        for (FileRef ref:proof.expected().completeSources()) epochInput(selected,"native_source",ref);
        epochInput(selected,"bridge_dll",proof.expected().bridgeDll()); epochInput(selected,"injector",proof.expected().injector());
        epochInput(selected,"game_executable",proof.expected().gameExecutable()); epochInput(selected,"launcher_settings",proof.expected().launcherSettings());
        var definition=StrictJson.object();definition.put("schema","xar.java-root-source-epoch/v1");definition.put("machine_id",proof.machineId());
        var rows=definition.putArray("inputs");
        for (EpochInput input:selected.values()) {
            var row=rows.addObject();row.put("role",input.role());
            var ref=row.putObject("source");ref.put("path",normalized(input.source()));ref.put("bytes",input.source().bytes());ref.put("sha256",input.source().sha256());
        }
        byte[] bytes=org.xar.ck3.control.build.ControlBuild.strictMapper().writeValueAsBytes(definition);
        if(bytes.length<1||bytes.length>(16<<20))throw new IOException("complete stable software epoch manifest exceeds its actual archive lane");
        ExactRef result=archive.preserveArtifact(borrowed,bytes,16<<20);
        if(!java.util.Arrays.equals(bytes,archive.readArtifact(borrowed,result,16<<20)))throw new IOException("source epoch manifest differs from its actual immutable readback");
        return result;
    }
    private static void epochInput(java.util.Map<String,EpochInput> selected,String role,FileRef ref)throws IOException {
        String key=role+":"+normalized(ref);EpochInput prior=selected.putIfAbsent(key,new EpochInput(role,ref));
        if(prior!=null&&(prior.source().bytes()!=ref.bytes()||!prior.source().sha256().equals(ref.sha256())))throw new IOException("stable source epoch contains conflicting physical source aliases");
    }
    private static String normalized(FileRef ref)throws IOException {
        return Path.of(ref.path()).toRealPath().toString().replace('\\','/').toLowerCase(java.util.Locale.ROOT);
    }
    private static void retainCustody(java.util.Map<String,FileRef> selected,FileRef ref)throws IOException {
        String key=normalized(ref);FileRef old=selected.putIfAbsent(key,ref);
        if(old!=null&&(old.bytes()!=ref.bytes()||!old.sha256().equals(ref.sha256())))throw new IOException("actual physical source closure contains conflicting aliases");
    }
    private void requirePhysicalGame(SessionIdentity identity, Instant deadline) throws IOException {
        if (!clock.instant().isBefore(deadline) || !game.generation().equals(identity.game())
                || !game.machineId().equals(identity.machineId()) || !game.sessionId().equals(identity.sessionId())
                || !(game.inspect(identity.game(), deadline) instanceof GameLifecycle.Running))
            throw new IOException("source qualification lost independently measured current Game/session");
    }
    private void requireGame(SessionIdentity identity, Complete frame, GameLifecycle.Running process, Instant deadline) throws IOException {
        if (!clock.instant().isBefore(deadline) || !game.generation().equals(identity.game()) || !process.measured().equals(identity.game())
                || !game.machineId().equals(identity.machineId()) || !game.sessionId().equals(identity.sessionId())
                || !frame.identity().game().equals(identity.game()) || !frame.sessionId().equals(identity.sessionId()))
            throw new IOException("source qualification crossed the current held Game/session/deadline");
    }
    private static ExactRef exact(FileRef source) { return new ExactRef(source.path(), source.bytes(), source.sha256()); }
}
