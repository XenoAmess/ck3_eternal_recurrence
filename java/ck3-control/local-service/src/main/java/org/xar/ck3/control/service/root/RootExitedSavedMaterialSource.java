package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Files;
import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialStore;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** Reopens the actual latest physical saved material in the original writer after administrative retirement.
 * No caller supplies a pair, confirmation, physical current frame or saved-day credit. */
final class RootExitedSavedMaterialSource {
    private static final int MAX_METADATA=1024*1024;
    private record Located(CheckpointPair pair,WriterContracts.Pin confirmation) { }
    private record LocatedImported(RootOrdinaryRuntimeConfiguration configuration,CheckpointPair pair,ExactRef confirmation) { }
    private RootExitedSavedMaterialSource(){ }

    record ImportedData(SessionIdentity owner,SessionIdentity physicalSaveOwner,CheckpointPair pair,
            WriterContracts.Pin entry,WriterContracts.Pin sourceConfirmation,DriverStateSnapshot.Complete physicalSavedDriver,
            DriverObservationAssembler.Complete archivedBefore,DriverSnapshotFacts.Known archivedDriver,String headDigest) { }

    @FunctionalInterface private interface ImportedRead<T> {
        T read(ImportedData imported,RootJavaSavedBootstrap.ConfirmedSource source)throws IOException;
    }

    /**
     * The explicit historical request locates the independent physical SAVE. The current writer separately
     * supplies the actual original imported entry and archived opening. Results carry DATA only.
     */
    static ImportedData readImportedData(ExactRef originalRecoveryRequest,RootApplicationAssembly.Core currentCore,
            SessionIdentity owner,Clock clock)throws IOException {
        return readImported(originalRecoveryRequest,currentCore,owner,clock,(data,original)->data);
    }

    /** Also replays the physical SAVE's privately archived capability state under its original issuer. */
    static RootRestoreMaterials.ImportedRestoreOriginal readImportedRestoreOriginal(ExactRef originalRecoveryRequest,
            RootApplicationAssembly.Core currentCore,SessionIdentity owner,Clock clock)throws IOException {
        return readImported(originalRecoveryRequest,currentCore,owner,clock,(data,original)->{
            var result=new RootRestoreMaterials.ImportedRestoreOriginal(data,original.readOriginalPhysicalSave());
            result.requireAbandoned(owner,data.archivedDriver());return result;
        });
    }

    private static <T> T readImported(ExactRef originalRecoveryRequest,RootApplicationAssembly.Core currentCore,
            SessionIdentity owner,Clock clock,ImportedRead<T> read)throws IOException {
        var inputs=locateImported(originalRecoveryRequest,currentCore,owner);
        try(var prepared=RootOrdinaryRuntimeAssembly.prepareReadOnlySavedSource(inputs.configuration(),clock)) {
            var source=qualifyImported(inputs,prepared);
            return read.read(readImportedEntry(currentCore,owner,source),source);
        }
    }
    private static LocatedImported locateImported(ExactRef originalRecoveryRequest,RootApplicationAssembly.Core currentCore,
            SessionIdentity owner)throws IOException {
        Objects.requireNonNull(currentCore);Objects.requireNonNull(owner);
        Path requestPath=Path.of(originalRecoveryRequest.path());
        StrictJson.require(requestPath.isAbsolute()&&requestPath.normalize().equals(requestPath),
                "explicit imported Saved source requires a normalized absolute request");
        var row=StrictJson.parse(RootLoadedReplacementRecoveryInputs.read(originalRecoveryRequest,MAX_METADATA),MAX_METADATA);
        StrictJson.require(RootLoadedSavedResumeMain250.requestMode(row)==3,"exact original loaded Saved recovery request required");
        String machine=StrictJson.text(row.get("machineId"));
        StrictJson.require(machine.equals(owner.machineId())&&machine.equals(currentCore.configuration().machineId()),
                "imported Saved request crossed the original owner or writer machine");
        var targetConfiguration=RootSavedRuntimeConfigurationInputs.readSource(ExactRef.fromJson(row.get("newRuntimeConfiguration")));
        Path targetRoot=targetConfiguration.stateDirectory().getParent();
        StrictJson.require(machine.equals(targetConfiguration.machineId())&&currentCore.configuration().ledger().snapshot()
                        .equals(targetRoot.resolve("continuity/continuity.json")),
                "original loaded Saved request belongs to another target writer");
        Path ownerDirectory=Path.of(StrictJson.text(row.get("ownerDirectory")));
        StrictJson.require(ownerDirectory.isAbsolute()&&ownerDirectory.normalize().equals(ownerDirectory),
                "original loaded Saved request owner directory must be absolute and normalized");
        var configuration=RootSavedRuntimeConfigurationInputs.readSource(ExactRef.fromJson(row.get("sourceRuntimeConfiguration")));
        Path physicalRoot=configuration.stateDirectory().getParent();
        StrictJson.require(machine.equals(configuration.machineId())&&!physicalRoot.startsWith(targetRoot)
                        &&!targetRoot.startsWith(physicalRoot),"imported Saved requires its distinct original SAVE writer");
        var confirmation=ExactRef.fromJson(row.get("sourceConfirmation"));
        var pair=CheckpointPairCodec.decode(RootLoadedReplacementRecoveryInputs.read(
                ExactRef.fromJson(row.get("checkpointPair")),MAX_METADATA));
        return new LocatedImported(configuration,pair,confirmation);
    }
    private static RootJavaSavedBootstrap.ConfirmedSource qualifyImported(LocatedImported input,
            RootOrdinaryRuntimeAssembly.Prepared prepared)throws IOException {
        return RootJavaSavedBootstrap.qualifyOriginalConfirmation(prepared.openSavedSourceCore(),new NativeCheckpointFiles(),
                input.configuration().stateDirectory().resolve("checkpoints/attachments"),prepared.plan().pipeName(),input.pair(),input.confirmation());
    }

    static PreparedImportedRestore prepareImportedRestore(ExactRef originalRecoveryRequest,RootApplicationAssembly.Core currentCore,
            RootOrdinaryRuntimeConfiguration targetConfiguration,CheckpointFiles targetFiles,SessionIdentity owner,Clock clock)throws IOException {
        var inputs=locateImported(originalRecoveryRequest,currentCore,owner);
        StrictJson.require(currentCore.configuration().ledger().snapshot().equals(targetConfiguration.stateDirectory().getParent()
                        .resolve("continuity/continuity.json")),"prepared imported SAVE crossed the actual target configuration");
        var prepared=RootOrdinaryRuntimeAssembly.prepareReadOnlySavedSource(inputs.configuration(),clock);
        try {
            var source=qualifyImported(inputs,prepared);
            var data=readImportedEntry(currentCore,owner,source);
            var stores=RootJavaSavedBootstrap.checkpointStores(currentCore,targetFiles,
                    targetConfiguration.stateDirectory().resolve("checkpoints/attachments"),prepared.plan().pipeName(),source.pair());
            return new PreparedImportedRestore(prepared,currentCore,source,data,stores,originalRecoveryRequest,targetConfiguration.stateDirectory());
        }catch(IOException|RuntimeException|Error failure) {
            try{prepared.close();}catch(IOException|RuntimeException|Error close){if(close!=failure)failure.addSuppressed(close);}
            throw failure;
        }
    }
    /** One actual readonly old source retained by the cold predecessor throughout its writer work. */
    static final class PreparedImportedRestore implements AutoCloseable,SavedAttachmentSourceStore.ImportedSourceRead {
        private final RootOrdinaryRuntimeAssembly.Prepared prepared;
        private final RootApplicationAssembly.Core target;
        private final RootJavaSavedBootstrap.ConfirmedSource source;
        private final ImportedData imported;
        private final RootJavaSavedBootstrap.CheckpointStores stores;
        private final SavedAttachmentSourceStore.ImportedOrigin origin;
        private final Path targetStateDirectory;
        private boolean closed;
        private PreparedImportedRestore(RootOrdinaryRuntimeAssembly.Prepared prepared,RootApplicationAssembly.Core target,
                RootJavaSavedBootstrap.ConfirmedSource source,ImportedData imported,RootJavaSavedBootstrap.CheckpointStores stores,
                ExactRef request,Path targetStateDirectory) {
            this.prepared=prepared;this.target=target;this.source=source;this.imported=imported;this.stores=stores;
            this.origin=new SavedAttachmentSourceStore.ImportedOrigin(imported.owner(),request,imported.entry(),imported.sourceConfirmation());
            this.targetStateDirectory=targetStateDirectory;
        }
        ImportedData imported(){return imported;}
        Path targetStateDirectory(){return targetStateDirectory;}
        SavedCheckpointMaterialStore materialStore(){return stores.materials();}
        DriverCheckpointStore driverCheckpoints(){return stores.drivers();}
        SavedAttachmentSourceStore.SavedMaterial material(ContinuityStorePort.Session same)throws IOException {
            requireOpen(same);
            return stores.materials().ordinaryStore().bindImported(same,origin,source.originalMaterial(),this);
        }
        RootRestoreMaterials.PhysicalSavedOriginal readOriginalPhysicalSave(ContinuityStorePort.Session same)throws IOException {
            requireOpen(same);return source.readOriginalPhysicalSave(same);
        }
        @Override public <T> T read(ContinuityStorePort.Session same,SavedAttachmentSourceStore.ImportedSourceWork<T> work)throws IOException {
            requireOpen(same);return source.withOriginalWriter(same,work);
        }
        private void requireOpen(ContinuityStorePort.Session same)throws IOException {
            if(closed)throw new IOException("imported physical SAVE source lease is closed");
            target.writer().requireSession(same);
        }
        @Override public void close()throws IOException {
            if(!closed){closed=true;prepared.close();}
        }
    }

    private static ImportedData readImportedEntry(RootApplicationAssembly.Core currentCore,SessionIdentity owner,
            RootJavaSavedBootstrap.ConfirmedSource source)throws IOException {
        var archive=currentCore.archive();
        return currentCore.writer().locked(same->archive.inHistoricalReadScope(same,
                new ActionPorts.HistoricalReadLimits(16,32L*1024*1024,32),data->{
            var original=RootJavaSavedBootstrap.existingSavedSource(source,same,archive);
            var entry=original.getValue();
            var marker=ContinuityJson.parseObject(entry.details(),MAX_METADATA);
            StrictJson.require(OrdinaryCycleTransitions.sessionFromJson(marker.get("session")).equals(owner)
                            &&!source.physicalSaveOwner().game().equals(owner.game()),
                    "imported Saved entry crossed the actual target runtime or original SAVE Game");
            RootJavaSavedBootstrap.requireSavedSourceOriginals(source,archive,same,marker);
            var facts=data.loadFullMaterial(ExactRef.fromJson(marker.get("driver_facts")));
            var manifestReference=DriverSnapshotFacts.observationOriginalReference(facts).orElseThrow(()->
                    new IOException("imported Saved entry lacks its actual opening observation manifest"));
            var manifest=data.loadFullMaterial(manifestReference);
            var driverReference=DriverObservationEvidenceReader.currentDriverReference(manifestReference,manifest);
            StrictJson.require(driverReference.equals(ExactRef.fromJson(marker.get("full_driver"))),
                    "imported Saved opening differs from its original target Driver");
            var nativeFrame=DriverObservationEvidenceReader.retainedNativeFrame(manifestReference,manifest,data);
            byte[] packet=nativeFrame.originalPacket();
            var nativeReference=data.nativeFrameReference(ActionCodec.sha256(packet),packet.length);
            var observation=DriverObservationEvidenceReader.decode(manifestReference,manifest,data.loadFullMaterial(driverReference),nativeFrame,data);
            var known=DriverSnapshotFacts.decodeKnownOriginal(facts,Optional.of(observation));
            var assembled=currentCore.observationAssembler().assemble(nativeFrame,observation,nativeReference);
            if(!(assembled instanceof DriverObservationAssembler.Complete before))
                throw new IOException("imported Saved opening did not replay a complete original target observation");
            StrictJson.require(before.identity().equals(ProposalLifecycleCodec.decodeObservation(marker.get("opening")))
                            &&before.sessionId().equals(owner.sessionId())
                            &&known.stamp().driverVersion()==StrictJson.integer(marker.get("driver_version"),0,StrictJson.MAX_SAFE_INTEGER)
                            &&known.stamp().episodeEpoch()==StrictJson.integer(marker.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER)
                            &&before.identity().frame().episodeRunId().equals(source.pair().frame().frame().episodeRunId()),
                    "archived opening or retained Driver facts crossed the actual imported Saved entry");
            return new ImportedData(owner,source.physicalSaveOwner(),source.pair(),entry.eventPin(),source.confirmation().eventPin(),
                    source.physicalSavedDriver(),before,known,original.getKey().digest());
        }));
    }

    /** The actual saved Driver selects the existing explicit projection reader before replacement CREATE. */
    static Optional<RootFrozenRunProfile.FrozenRunProfile> nativeCampaignProfile(
            org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial material,
            NativeLaunchPlan identicalPlan,Clock clock)throws IOException {
        Objects.requireNonNull(material);Objects.requireNonNull(identicalPlan);Objects.requireNonNull(clock);
        boolean nativeCampaign=material.savedDriver().successionLifecycle()
                instanceof org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.NullValue;
        if(!nativeCampaign)return Optional.empty();
        StrictJson.require(material.sourceSemantic().frame().observationVersion()
                        ==org.xar.ck3.control.application.driver.DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,
                "null lifecycle requires the actual saved native campaign observation");
        var profile=preparedInput(identicalPlan,RootFrozenRunProfile.SCHEMA);
        var policy=preparedInput(identicalPlan,InitialEpisodePolicy.SAVED_SCHEMA);
        var frozen=RootFrozenRunProfile.readExact(profile,identicalPlan,policy,clock);
        frozen.requireExplicitNativeCampaign();return Optional.of(frozen);
    }

    /** Select configuration only from this reviewed plan's finite exact prepared closure. */
    private static org.xar.ck3.control.contracts.ExactRef preparedInput(NativeLaunchPlan plan,String schema)throws IOException {
        org.xar.ck3.control.contracts.ExactRef selected=null;
        for(var source:plan.preparedProfile().preparedInputs()) {
            if(source.bytes()<=0||source.bytes()>MAX_METADATA)continue;
            byte[] bytes;
            try(var input=Files.newInputStream(Path.of(source.path()))){bytes=input.readNBytes(MAX_METADATA+1);}
            com.fasterxml.jackson.databind.JsonNode tree;
            try{tree=StrictJson.parse(bytes,MAX_METADATA);}catch(IllegalArgumentException unrelated){continue;}
            if(!tree.isObject()||!tree.path("schema").isTextual()||!schema.equals(tree.path("schema").textValue()))continue;
            source.verify();
            StrictJson.require(bytes.length==source.bytes()&&ActionCodec.sha256(bytes).equals(source.sha256()),
                    "selected prepared Saved projection input changed");
            var exact=new org.xar.ck3.control.contracts.ExactRef(source.path(),source.bytes(),source.sha256());
            StrictJson.require(selected==null||selected.equals(exact),"Saved plan has multiple explicit projection inputs");selected=exact;
        }
        if(selected==null)throw new IOException("Saved plan is missing its exact prepared input: "+schema);
        return selected;
    }

    static RootJavaSavedBootstrap.ConfirmedSource qualify(RootApplicationAssembly.Core core,
            RootOrdinaryRuntimeConfiguration configuration,JavaGameLifecycle lifecycle,
            JavaGameLifecycle.ExitedGeneration exited,Instant deadline)throws IOException {
        Objects.requireNonNull(lifecycle);Objects.requireNonNull(exited);
        return qualifyOriginal(core,configuration,exited.machineId(),exited.generation(),exited.sourceSessionId(),
                exited.originalConfiguration().pipeName(),()->exited.requireOwner(lifecycle,deadline),new NativeCheckpointFiles());
    }
    static RootJavaSavedBootstrap.ConfirmedSource qualifyLoaded(RootApplicationAssembly.Core core,
            RootOrdinaryRuntimeConfiguration configuration,CheckpointFiles actualGuardedFiles,org.xar.ck3.control.platform.RootProcessAttach.LoadedReplacement loaded,
            Instant deadline)throws IOException {
        Objects.requireNonNull(loaded);
        var result=qualifyOriginal(core,configuration,loaded.previousOwner().machineId(),loaded.previousOwner().game(),
                loaded.previousOwner().sessionId(),loaded.originalPipe(),()->loaded.requireCurrent(deadline),Objects.requireNonNull(actualGuardedFiles));
        StrictJson.require(result.pair().equals(loaded.pair()),"loaded continuation source changed its original physical saved pair");
        loaded.requireCurrent(deadline);return result;
    }
    @FunctionalInterface private interface SourceCheck { void require()throws IOException; }
    private static RootJavaSavedBootstrap.ConfirmedSource qualifyOriginal(RootApplicationAssembly.Core core,
            RootOrdinaryRuntimeConfiguration configuration,String machineId,GameGeneration oldGame,
            String oldSession,String oldPipe,SourceCheck source,CheckpointFiles files)throws IOException {
        Objects.requireNonNull(core);Objects.requireNonNull(configuration);source.require();
        var expected = new SessionIdentity(machineId,oldGame,oldSession);
        Path materialRoot=configuration.stateDirectory().resolve("checkpoints/attachments");
        Located located=core.writer().locked(same->{
            var head=same.head();
            StrictJson.require(!head.snapshotNeedsRecovery()&&head.indexRepairs().isEmpty(),
                    "exited saved source requires its complete unrepaired original writer");
            var saved=head.state().toJson().get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD);
            StrictJson.require(saved!=null&&saved.isObject()&&saved.hasNonNull("pair"),
                    "exited restoration requires the canonical latest ordinary saved pair");
            var pair=CheckpointPairCodec.decode(StrictJson.canonical(saved.get("pair")));
            requireOrdinaryPairIdentity(head.state(),pair,expected);
            Path path=materialRoot.resolve("checkpoints").resolve(ActionCodec.sha256(CheckpointPairCodec.encode(pair))+".json");
            var witness=files.observe(path).orElseThrow(()->new IOException("original saved material is unavailable"));
            var document=StrictJson.parse(files.read(witness,MAX_METADATA),MAX_METADATA);
            StrictJson.require(document.isObject()&&SavedAttachmentSourceStore.MATERIAL_SCHEMA.equals(StrictJson.text(document.get("schema")))
                            &&pair.equals(CheckpointPairCodec.decode(StrictJson.canonical(document.get("pair"))))
                            &&document.get("original_writer_head") instanceof com.fasterxml.jackson.databind.node.ObjectNode,
                    "saved material locator differs from the canonical physical pair");
            var before=ContinuityState.fromJson((com.fasterxml.jackson.databind.node.ObjectNode)document.get("original_writer_head"),machineId);
            String name=String.format(java.util.Locale.ROOT,"%08d.json",Math.addExact(before.sequence(),1));
            var matches=head.documents().stream().filter(pin->Path.of(pin.reference().path()).getFileName().toString().equals(name)).toList();
            StrictJson.require(matches.size()==1,"saved source requires its unique actual SAVE_CONFIRMED predecessor edge");
            same.verifyPin(matches.getFirst());files.verify(witness);
            StrictJson.require(head.digest().equals(same.head().digest()),"saved source locator changed the original writer");
            return new Located(pair,matches.getFirst());
        });
        var result=RootJavaSavedBootstrap.qualify(core,files,materialRoot,
                oldPipe,located.pair(),located.confirmation());
        requireConfirmedRuntimeOwner(result.confirmation().details(),expected);
        source.require();return result;
    }

    /** The canonical campaign episode is independent of its runtime owner's session ID. */
    static void requireOrdinaryPairIdentity(ContinuityState canonical,CheckpointPair pair,SessionIdentity expected) {
        var state=canonical.toJson();
        StrictJson.require(canonical.machineId().equals(expected.machineId())
                        &&pair.frame().machineId().equals(expected.machineId())
                        &&pair.frame().game().equals(expected.game())
                        &&GameGeneration.fromJson(state.get("game_binding")).equals(expected.game())
                        &&pair.frame().frame().episodeRunId().equals(
                                StrictJson.text(state.path("latest_binding").get("episode_run_id"))),
                "exited restoration crossed the canonical saved machine, Game or episode");
    }

    /** Called on the original SAVE edge after complete source and physical requalification. */
    static void requireConfirmedRuntimeOwner(byte[] confirmedDetails,SessionIdentity expected) {
        var details=ContinuityJson.parseObject(confirmedDetails,MAX_METADATA);
        StrictJson.require("SAVE_CONFIRMED".equals(StrictJson.text(details.get("boundary")))
                        &&OrdinaryCycleTransitions.sessionFromJson(details.get("session")).equals(expected),
                "exited restoration crossed the original SAVE runtime owner");
    }
}
