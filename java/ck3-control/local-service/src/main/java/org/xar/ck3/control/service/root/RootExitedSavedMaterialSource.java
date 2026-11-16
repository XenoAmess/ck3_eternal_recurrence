package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Files;
import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** Reopens the actual latest physical saved material in the original writer after administrative retirement.
 * No caller supplies a pair, confirmation, physical current frame or saved-day credit. */
final class RootExitedSavedMaterialSource {
    private static final int MAX_METADATA=1024*1024;
    private record Located(CheckpointPair pair,WriterContracts.Pin confirmation) { }
    private RootExitedSavedMaterialSource(){ }

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
            RootOrdinaryRuntimeConfiguration configuration,String machineId,org.xar.ck3.control.contracts.GameGeneration oldGame,
            String oldSession,String oldPipe,SourceCheck source,CheckpointFiles files)throws IOException {
        Objects.requireNonNull(core);Objects.requireNonNull(configuration);source.require();
        Path materialRoot=configuration.stateDirectory().resolve("checkpoints/attachments");
        Located located=core.writer().locked(same->{
            var head=same.head();
            StrictJson.require(!head.snapshotNeedsRecovery()&&head.indexRepairs().isEmpty(),
                    "exited saved source requires its complete unrepaired original writer");
            var saved=head.state().toJson().get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD);
            StrictJson.require(saved!=null&&saved.isObject()&&saved.hasNonNull("pair"),
                    "exited restoration requires the canonical latest ordinary saved pair");
            var pair=CheckpointPairCodec.decode(StrictJson.canonical(saved.get("pair")));
            StrictJson.require(pair.frame().machineId().equals(machineId)
                            &&pair.frame().game().equals(oldGame)
                            &&pair.frame().frame().episodeRunId().equals(oldSession),
                    "exited restoration crossed the canonical saved machine, Game or episode");
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
        source.require();return result;
    }
}
