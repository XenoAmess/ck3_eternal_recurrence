package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.platform.*;

/** Real tiny physical files and actual producer/reader paths. No Game, Native reads, writer or admission is fabricated. */
final class MappedSavedPolicyTest {
    @TempDir Path root;
    private final NativeCheckpointFiles files=new NativeCheckpointFiles();
    private ControlBuild.FileRef metadata(String name){return new ControlBuild.FileRef(root.resolve(name).toString(),1,"c".repeat(64));}
    private record Fixture(NativeLaunchPlan plan,ControlBuild.FileRef env,Path source,Path actual,CheckpointPair.FileWitness original) { }
    private Fixture fixture(boolean inPlace)throws Exception {
        Path profile=Files.createDirectories(root.resolve("profile/save games")).getParent();
        Path state=Files.createDirectory(root.resolve("state"));
        Path source=inPlace?profile.resolve("save games/checkpoint.ck3"):root.resolve("old/checkpoint.ck3");
        Files.createDirectories(source.getParent());Files.writeString(source,"software-only-source-SAVE",StandardOpenOption.CREATE_NEW);
        Path actual=profile.resolve("save games/checkpoint.ck3");if(!inPlace)Files.copy(source,actual);
        ObjectNode manifest=StrictJson.object().put("environment_sha256","e".repeat(64)).put("profile_dir",profile.toString()).put("state_dir",state.toString());
        manifest.putObject("rules").putArray("profile");manifest.putObject("load_profile").putArray("enabled_mods");
        Path envPath=root.resolve("environment-data.json");Files.write(envPath,StrictJson.canonical(manifest));
        var env=ControlBuild.FileRef.measure(envPath);Instant deadline=Instant.now().plusSeconds(300);String machine="test-machine-1";
        var sources=LaunchSourceBinding.accept(new LaunchSourceBinding.Review(machine,deadline,metadata("ck3.exe"),metadata("bridge.dll"),metadata("injector.exe"),
                new NativeLaunchEvidence.Inputs(metadata("env-meta.json"),metadata("build.json"),metadata("registration.json")),root,List.of()));
        var saved=new NativeLaunchPlan.SavedGame("checkpoint",ControlBuild.FileRef.measure(source));
        var plan=new NativeLaunchPlan("mapped-policy-fixture","mapped-session",sources,profile,state,root.resolve("evidence"),
                "\\\\.\\pipe\\mapped-policy-fixture","fixture-bridge","fixture-adapter",saved,false,NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,
                Map.of(),1L<<30,64L<<20,deadline,Duration.ofSeconds(5),Duration.ofSeconds(30),
                new SteamOfflineProbe.Plan(machine,metadata("steam.exe"),deadline),
                NativeLaunchPlan.PreparedProfile.explicit(env,ProfileKind.SAVED_VANILLA,List.of(),List.of(env)),32);
        return new Fixture(plan,env,source,actual,files.observe(source).orElseThrow());
    }
    private ExactRef write(String name,byte[] bytes)throws IOException {
        Path target=root.resolve(name);Files.write(target,bytes,StandardOpenOption.CREATE_NEW);return files.observe(target).orElseThrow().reference();
    }
    private ExactRef produce(Fixture f)throws Exception {
        try(var held=NativeSavedGameClone.qualify(f.plan(),f.original())) {
            return write("policy.json",InitialEpisodePolicy.produceSavedMaterialized(f.env(),f.plan(),f.original(),held).bytes());
        }
    }
    private CheckpointPair pair(Fixture f)throws Exception {
        Path driver=root.resolve("driver.json"),ack=root.resolve("ack.json");Files.writeString(driver,"driver-data");Files.writeString(ack,"ack-data");
        var frame=new ProposalLifecycle.ObservationIdentity("test-machine-1",new GameGeneration(123,new PythonOnlyUInt64(BigInteger.valueOf(100))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.ONE,BigInteger.valueOf(240)),"native:1",BigInteger.ONE,"episode-1"),1);
        return new CheckpointPair(f.original(),files.observe(driver).orElseThrow(),frame,"lineage-1",1,"save-1",files.observe(ack).orElseThrow().reference(),Instant.now());
    }
    private static void replaceEqual(Path original)throws IOException {
        Path replacement=original.resolveSibling("replacement-"+original.getFileName());Files.copy(original,replacement);
        Files.setLastModifiedTime(replacement,Files.getLastModifiedTime(original));
        Files.move(original,original.resolveSibling("retained-"+original.getFileName()),StandardCopyOption.ATOMIC_MOVE);
        Files.move(replacement,original,StandardCopyOption.ATOMIC_MOVE);
    }
    @Test void actualMappedPreparedQuoteFeedsOnlyTheTypedV2IssuerPreflight()throws Exception {
        var f=fixture(false);var pair=pair(f);ExactRef pairRef=write("pair.json",CheckpointPairCodec.encode(pair));
        ExactRef planRef=write("plan-data.json",NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(f.plan())).toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
        Path assets=Files.createDirectory(root.resolve("policy-assets")),controls=Files.createDirectory(root.resolve("issuer-controls"));
        Path target=assets.resolve("policy.json"),declarationTarget=controls.resolve("declaration.json");
        String review=f.plan().deadline().toString(),machine=f.plan().sources().review().machineId();
        var request=new RootProfileBootstrapCommand.SavedMaterializedPolicyRequest("xar.java-root-initial-saved-native-policy-bootstrap/v2",
                machine,review,f.env(),((NativeLaunchPlan.SavedGame)f.plan().load()).save(),planRef,target.toString(),pairRef);
        var existing=NativeSavedGamePreparation.requirePrepared(f.plan(),f.original(),Clock.systemUTC());
        try(var held=NativeSavedGameClone.qualify(f.plan(),f.original())) {
            var prepared=RootProfileBootstrapInputs.initialSavedMaterializedPolicy(f.env(),f.plan(),pair,planRef,pairRef,held,target)
                    .withExistingAllocatedInput(existing);
            var quote=new RootBootstrapProtocol.OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1","INITIAL_SAVED_MATERIALIZED_POLICY",
                    machine,review,prepared.assetRoot().toString(),prepared.quote(),prepared.outputDirectories(),prepared.retainedInputs(),
                    "AWAITING_REAL_INDEPENDENT_ISSUER_BINDING");
            byte[] line=RootBootstrapProtocol.quoteLine(quote);ExactRef original=write("actual-mapped-quote.jsonl",line);
            var quoteRef=new ControlBuild.FileRef(original.path(),original.bytes(),original.sha256());
            var metadata=RootPolicyProducerPreflight.declarationRequest(request,quote,quoteRef,line,"mapped-window",controls,declarationTarget,65536,262144,65536,64);
            assertEquals(quoteRef,metadata.actualPhaseQuote());assertFalse(Files.exists(declarationTarget));assertFalse(Files.exists(target));
            assertEquals(RootBootstrapOutputContract.Kind.INITIAL_POLICY,quote.outputs().getFirst().kind());
            assertEquals(f.original().reference().path(),request.actualSave().path());
            var legacy=new RootProfileBootstrapCommand.SavedNativePolicyRequest("xar.java-root-initial-saved-native-policy-bootstrap/v1",
                    machine,review,f.env(),request.actualSave(),planRef,target.toString());
            assertThrows(IOException.class,()->RootPolicyProducerPreflight.declarationRequest(legacy,quote,quoteRef,line,
                    "mapped-window",controls,declarationTarget,65536,262144,65536,64));
            assertThrows(IOException.class,()->RootPolicyProducerPreflight.declarationRequest(request,quote,quoteRef,
                    java.util.Arrays.copyOf(line,line.length-1),"mapped-window",controls,declarationTarget,65536,262144,65536,64));
            held.requireCurrent(f.plan(),f.original());files.verify(f.original());
        }
    }
    @Test void actualV2ProducerReaderAndQuoteKeepSourceAndCloneSeparateAndCloseInvalidatesQuote()throws Exception {
        var f=fixture(false);var pair=pair(f);ExactRef pairRef=write("pair.json",CheckpointPairCodec.encode(pair));
        ExactRef planRef=write("plan-data.json",NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(f.plan())).toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
        byte[] oldPair=CheckpointPairCodec.encode(pair);RootProfileBootstrapInputs.Prepared prepared;
        try(var held=NativeSavedGameClone.qualify(f.plan(),f.original())) {
            byte[] bytes=InitialEpisodePolicy.produceSavedMaterialized(f.env(),f.plan(),f.original(),held).bytes();
            var row=StrictJson.object(StrictJson.parse(bytes,1<<20),Set.of("schema","environment_manifest","episode_projection","succession_lifecycle","saved_game","source_saved_game","source_clone"));
            assertEquals(InitialEpisodePolicy.MATERIALIZED_SAVED_SCHEMA,row.get("schema").textValue());assertTrue(row.get("succession_lifecycle").isNull());
            assertEquals(f.original().reference(),ExactRef.fromJson(row.get("source_saved_game")));
            assertEquals(f.actual().toString(),ExactRef.fromJson(row.get("saved_game")).path());
            assertArrayEquals(StrictJson.canonical(held.observation().toJson(),1<<20),StrictJson.canonical(row.get("source_clone"),1<<20));
            var accepted=InitialEpisodePolicy.readExactSaved(write("policy.json",bytes),f.plan());
            accepted.requireInitialSavedProjection(f.plan(),f.original(),held.observation());
            prepared=RootProfileBootstrapInputs.initialSavedMaterializedPolicy(f.env(),f.plan(),pair,planRef,pairRef,held,root.resolve("published-policy.json"));
            assertEquals(1,prepared.quote().size());assertEquals(bytes.length,prepared.quote().getFirst().bytes());
            assertEquals(RootBootstrapOutputContract.Kind.INITIAL_POLICY,prepared.quote().getFirst().kind());
            assertTrue(prepared.retainedInputs().isEmpty());assertTrue(prepared.outputDirectories().isEmpty());
            assertThrows(IllegalArgumentException.class,()->accepted.requireSavedProjection(f.plan()));
        }
        assertThrows(UncheckedIOException.class,prepared::quote);assertArrayEquals(oldPair,CheckpointPairCodec.encode(pair));
    }
    private ExactRef currentConfiguration(Fixture f,ExactRef policy)throws Exception {
        var plan=write("current-plan.json",StrictJson.canonical(NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(f.plan()))));
        var row=StrictJson.object().put("schema","xar.java-ordinary-runtime-configuration/v1").put("machine_id","test-machine-1")
                .put("state_dir",f.plan().stateDirectory().toString()).put("stock_game_root",root.resolve("stock").toString())
                .put("native_implementation",root.resolve("implementation.json").toString()).put("launch_plan_file",plan.path())
                .put("initial_policy_file",policy.path()).put("campaign_deadline_file",root.resolve("deadline.json").toString())
                .put("formal_war_budget",root.resolve("war-budget.json").toString()).put("formal_war_model",root.resolve("war-model.json").toString())
                .put("authority_id","mapped-config-data");
        var build=org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Build.CK3_1210;
        row.putObject("configured_build").put("version",build.version()).put("exe_sha256",build.sha256());
        return write("runtime-config.json",StrictJson.canonical(row));
    }
    @Test void exactCurrentConfigurationRetainsActualOwnerPlanWhileSourceReadStaysHistoricalAfterCloneSave()throws Exception {
        var f=fixture(false);var policy=produce(f);var configuration=currentConfiguration(f,policy);
        assertThrows(IOException.class,()->RootOrdinaryRuntimeConfiguration.read(Path.of(configuration.path())));
        var loaded=RootSavedRuntimeConfigurationInputs.readLoaded(configuration,f.plan());
        var equal=NativeLaunchPlanCodec.fromJson(NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(f.plan()))).accept();
        assertSame(f.plan(),loaded.retainBoundLaunchPlan(equal));loaded.initialPolicy().requireSavedHistory(f.plan());
        // The explicit original route reads this policy and its actual saved clone before same-Game recovery.
        RootLoadedSavedResumeMain250.requirePolicyRoute(loaded.initialPolicy(),3);
        try(var held=NativeSavedGameClone.qualify(f.plan(),f.original())) {
            loaded.initialPolicy().requireInitialSavedProjection(f.plan(),f.original(),held.observation());
        }
        Files.writeString(f.actual(),"SDK-save-after-token",StandardOpenOption.TRUNCATE_EXISTING);
        var source=RootSavedRuntimeConfigurationInputs.readSource(configuration);
        var actual=source.retainBoundLaunchPlan(equal);source.initialPolicy().requireSavedHistory(actual);
        assertTrue(source.initialPolicy().isMaterializedSaved());files.verify(f.original());
        // Configuration DATA alone does not restore the mapped clone or admit the legacy retained route.
        assertThrows(IOException.class,()->RootLoadedSavedResumeMain250.requirePolicyRoute(source.initialPolicy(),0));
        RootLoadedSavedResumeMain250.requirePolicyRoute(source.initialPolicy(),1);
        RootLoadedSavedResumeMain250.requirePolicyRoute(source.initialPolicy(),2);
        RootLoadedSavedResumeMain250.requirePolicyRoute(source.initialPolicy(),4);
        assertThrows(Exception.class,()->source.initialPolicy().requireInitialSavedProjection(actual,f.original()));
    }
    @Test void currentConfigurationRejectsCrossedOwnerPlanAndChangedExactSourceWithoutWritingFallback()throws Exception {
        var f=fixture(false);var configuration=currentConfiguration(f,produce(f));byte[] before=Files.readAllBytes(Path.of(configuration.path()));
        var changed=NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(f.plan()));changed.put("request_id","crossed-owner-request");
        var crossed=NativeLaunchPlanCodec.fromJson(changed).accept();
        assertThrows(IOException.class,()->RootSavedRuntimeConfigurationInputs.readLoaded(configuration,crossed));
        assertArrayEquals(before,Files.readAllBytes(Path.of(configuration.path())));
        Files.writeString(Path.of(configuration.path()),"{}",StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(IOException.class,()->RootSavedRuntimeConfigurationInputs.readSource(configuration));
        assertFalse(Files.exists(root.resolve("continuity")));files.verify(f.original());
    }
    @Test void legacyInPlaceConfigurationKeepsItsExistingLoadedRouteSet()throws Exception {
        var f=fixture(true);var policy=write("v1-config-policy.json",InitialEpisodePolicy.produceSaved(f.env(),((NativeLaunchPlan.SavedGame)f.plan().load()).save()).bytes());
        var configuration=currentConfiguration(f,policy);var loaded=RootSavedRuntimeConfigurationInputs.readLoaded(configuration,f.plan());
        assertFalse(loaded.initialPolicy().isMaterializedSaved());
        for(int mode=0;mode<=3;mode++)RootLoadedSavedResumeMain250.requirePolicyRoute(loaded.initialPolicy(),mode);
    }
    @Test void actualDefaultSourceRosterIncludesConfigurationReaderAndBothSavedPublicConsumers() {
        var sources=RootRuntimeConfigurationSources.requiredSavedEntrySourceTypes();
        assertTrue(sources.contains(RootSavedRuntimeConfigurationInputs.class));
        assertTrue(sources.contains(RootJavaSavedBootstrapMain249.class));assertTrue(sources.contains(RootLoadedSavedResumeMain250.class));
        assertTrue(sources.contains(RootOrdinaryRuntimeConfiguration.class));assertTrue(sources.contains(InitialEpisodePolicy.class));
    }
    @Test void integerNodeRoundTripPreservesExactMappingButNeverMasksFileIdOrWrongNumericType()throws Exception {
        var f=fixture(false);
        try(var held=NativeSavedGameClone.qualify(f.plan(),f.original())) {
            ObjectNode emitted=held.observation().toJson();
            ObjectNode decoded=(ObjectNode)StrictJson.parse(StrictJson.canonical(emitted,1<<20),1<<20);
            assertNotEquals(emitted.get("original_save").get("ref").get("bytes").getClass(),
                    decoded.get("original_save").get("ref").get("bytes").getClass());
            assertArrayEquals(StrictJson.canonical(emitted,1<<20),StrictJson.canonical(decoded,1<<20));
            byte[] bytes=InitialEpisodePolicy.produceSavedMaterialized(f.env(),f.plan(),f.original(),held).bytes();
            var policy=InitialEpisodePolicy.readExactSaved(write("numeric-roundtrip-policy.json",bytes),f.plan());
            policy.requireInitialSavedProjection(f.plan(),f.original(),held.observation());
            ObjectNode root=(ObjectNode)StrictJson.parse(bytes,1<<20);
            var changedId=root.deepCopy();var identity=(ObjectNode)changedId.get("source_clone").get("actual_native_identity");
            identity.put("file_id_decimal",identity.get("file_id_decimal").textValue().equals("0")?"1":"0");
            var wrongIdentity=InitialEpisodePolicy.readExactSaved(write("changed-id-policy.json",StrictJson.canonical(changedId,1<<20)),f.plan());
            assertThrows(IllegalArgumentException.class,()->wrongIdentity.requireInitialSavedProjection(f.plan(),f.original(),held.observation()));
            var floating=root.deepCopy();((ObjectNode)floating.get("source_clone").get("actual_save").get("ref"))
                    .put("bytes",new java.math.BigDecimal(f.original().reference().bytes()+".0"));
            var floatingRef=write("floating-bytes-policy.json",ControlBuild.strictMapper().writeValueAsBytes(floating));
            assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.readExactSaved(floatingRef,f.plan()));
            held.requireCurrent(f.plan(),f.original());
        }
    }
    @Test void ordinarySdkStyleSaveCanChangeCloneWhileHistoricalPolicyAndImmutableClosureRemainCurrent()throws Exception {
        var f=fixture(false);var policy=InitialEpisodePolicy.readExactSaved(produce(f),f.plan());
        policy.requireInitialSavedProjection(f.plan(),f.original());
        Files.writeString(f.actual(),"new-SDK-save-bytes",StandardOpenOption.TRUNCATE_EXISTING);
        policy.verify();policy.requireSavedHistory(f.plan());
        assertFalse(policy.evidenceClosure().stream().anyMatch(ref->ref.path().equals(f.actual().toString())));
        assertTrue(policy.evidenceClosure().contains(f.original().reference()));
        assertThrows(Exception.class,()->policy.requireInitialSavedProjection(f.plan(),f.original()));files.verify(f.original());
    }
    @Test void equalContentCloneReplacementDoesNotRefreshPersistedFileIdentity()throws Exception {
        var f=fixture(false);var policy=InitialEpisodePolicy.readExactSaved(produce(f),f.plan());
        replaceEqual(f.actual());assertEquals(f.original().reference().sha256(),files.observe(f.actual()).orElseThrow().reference().sha256());
        policy.verify();assertThrows(Exception.class,()->policy.requireInitialSavedProjection(f.plan(),f.original()));
        assertThrows(Exception.class,()->policy.requireInitialSavedProjection(f.plan(),f.original(),NativeSavedGameClone.observe(f.plan(),f.original())));
    }
    @Test void originalEqualContentReplacementCannotBecomeHistoricalSource()throws Exception {
        var f=fixture(false);var policy=InitialEpisodePolicy.readExactSaved(produce(f),f.plan());replaceEqual(f.source());
        assertThrows(Exception.class,policy::verify);assertThrows(Exception.class,()->policy.requireInitialSavedProjection(f.plan(),f.original()));
    }
    @Test void missingCloneNeverCreatesAnImplicitCopyOrAQuote()throws Exception {
        var f=fixture(false);Files.delete(f.actual());
        assertThrows(IOException.class,()->NativeSavedGameClone.qualify(f.plan(),f.original()));
        assertThrows(IOException.class,()->NativeSavedGamePreparation.requirePrepared(f.plan(),f.original(),Clock.systemUTC()));
        assertFalse(Files.exists(f.actual()));files.verify(f.original());
    }
    @Test void closedRealCustodyCannotProduceNewPolicyBytes()throws Exception {
        var f=fixture(false);var held=NativeSavedGameClone.qualify(f.plan(),f.original());held.close();
        assertThrows(IOException.class,()->InitialEpisodePolicy.produceSavedMaterialized(f.env(),f.plan(),f.original(),held));
    }
    @Test void sameDecodedPlanCannotReplaceTheBoundPlanObject()throws Exception {
        var f=fixture(false);var policy=InitialEpisodePolicy.readExactSaved(produce(f),f.plan());
        var decoded=NativeLaunchPlanCodec.fromJson(NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(f.plan()))).accept();
        assertNotSame(f.plan(),decoded);assertThrows(IllegalArgumentException.class,()->policy.requireSavedHistory(decoded));
    }
    @Test void tamperedHistoricalMappingTypesUnknownFieldsAndRoleSwapsAreRejected()throws Exception {
        var f=fixture(false);ObjectNode original=(ObjectNode)StrictJson.parse(Files.readAllBytes(Path.of(produce(f).path())),1<<20);
        var numeric=original.deepCopy();((ObjectNode)numeric.get("source_clone").get("actual_native_identity")).put("file_id_decimal",123);
        assertThrows(Exception.class,()->InitialEpisodePolicy.readExactSaved(write("numeric.json",StrictJson.canonical(numeric)),f.plan()));
        var extra=original.deepCopy();((ObjectNode)extra.get("source_clone")).put("available",true);
        assertThrows(Exception.class,()->InitialEpisodePolicy.readExactSaved(write("extra.json",StrictJson.canonical(extra)),f.plan()));
        var roles=original.deepCopy();roles.set("source_saved_game",roles.get("saved_game"));
        assertThrows(Exception.class,()->InitialEpisodePolicy.readExactSaved(write("roles.json",StrictJson.canonical(roles)),f.plan()));
    }
    @Test void requestV2IsStrictAndV1SchemaAndSevenFieldsRemainSeparate()throws Exception {
        var f=fixture(false);ExactRef planRef=new ExactRef(root.resolve("plan-data.json").toString(),1,"a".repeat(64));
        ExactRef pairRef=new ExactRef(root.resolve("pair-data.json").toString(),1,"b".repeat(64));
        var request=new RootProfileBootstrapCommand.SavedMaterializedPolicyRequest("xar.java-root-initial-saved-native-policy-bootstrap/v2",
                "test-machine-1",Instant.now().plusSeconds(200).toString(),f.env(),((NativeLaunchPlan.SavedGame)f.plan().load()).save(),planRef,root.resolve("new-policy.json").toString(),pairRef);
        var mapper=ControlBuild.strictMapper();byte[] encoded=mapper.writeValueAsBytes(request);
        assertEquals(request,mapper.readValue(encoded,RootProfileBootstrapCommand.SavedMaterializedPolicyRequest.class));
        ObjectNode row=mapper.readValue(encoded,ObjectNode.class);assertEquals(8,row.size());assertTrue(row.has("source_pair"));
        var missing=row.deepCopy();missing.remove("source_pair");assertThrows(IOException.class,()->mapper.treeToValue(missing,RootProfileBootstrapCommand.SavedMaterializedPolicyRequest.class));
        var alias=row.deepCopy();alias.put("schema","xar.java-root-initial-saved-native-policy-bootstrap/v1");
        assertThrows(IOException.class,()->mapper.treeToValue(alias,RootProfileBootstrapCommand.SavedMaterializedPolicyRequest.class));
        var wrong=row.deepCopy();((ObjectNode)wrong.get("source_pair")).put("bytes",true);
        assertThrows(IOException.class,()->mapper.treeToValue(wrong,RootProfileBootstrapCommand.SavedMaterializedPolicyRequest.class));
        var legacy=new RootProfileBootstrapCommand.SavedNativePolicyRequest("xar.java-root-initial-saved-native-policy-bootstrap/v1",
                request.machineId(),request.reviewAtUtc(),f.env(),request.actualSave(),planRef,request.target());
        ObjectNode legacyRow=mapper.valueToTree(legacy);assertEquals(7,legacyRow.size());assertFalse(legacyRow.has("source_pair"));
        assertThrows(IOException.class,()->mapper.treeToValue(row,RootProfileBootstrapCommand.SavedNativePolicyRequest.class));
    }
    @Test void v1InPlaceProducerAndReaderRetainTheirOldWireAndPhysicalContract()throws Exception {
        var f=fixture(true);byte[] raw=InitialEpisodePolicy.produceSaved(f.env(),((NativeLaunchPlan.SavedGame)f.plan().load()).save()).bytes();
        ObjectNode row=(ObjectNode)StrictJson.parse(raw,1<<20);assertEquals(5,row.size());assertEquals(InitialEpisodePolicy.SAVED_SCHEMA,row.get("schema").textValue());
        var policy=InitialEpisodePolicy.readExactSaved(write("v1-policy.json",raw),f.plan());
        assertFalse(policy.isMaterializedSaved());policy.requireSavedProjection(f.plan());policy.requireInitialSavedProjection(f.plan(),f.original());
        assertArrayEquals(raw,InitialEpisodePolicy.produceSaved(f.env(),((NativeLaunchPlan.SavedGame)f.plan().load()).save()).bytes());
    }
    @Test void mappedV2CannotUseAnInPlaceSourceThatOrdinarySaveWouldOverwrite()throws Exception {
        var f=fixture(true);
        try(var held=NativeSavedGameClone.qualify(f.plan(),f.original())) {
            assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.produceSavedMaterialized(f.env(),f.plan(),f.original(),held));
        }
        files.verify(f.original());
    }
    @Test void transportPhaseAndDeploymentClosureIncludeActualMappedProducerAndRealCustodyNests() {
        var mode=RootProfileBootstrapCommand.Mode.INITIAL_SAVED_MATERIALIZED_POLICY;
        assertEquals(List.of("INITIAL_SAVED_MATERIALIZED_POLICY"),RootBootstrapProtocol.commandPhases(mode));
        assertEquals(RootBootstrapProtocol.commandPhases(mode),RootBootstrapProtocol.Mode.INITIAL_SAVED_MATERIALIZED_POLICY.phases());
        var classes=RootBootstrapRuntime.requiredClasses(RootBootstrapProtocol.Mode.INITIAL_SAVED_MATERIALIZED_POLICY);
        for(String name:List.of("NativeSavedGameClone$Observation","QualifiedCloneCustody","NativeSavedGamePreparation$Existing","NativeSavedGamePreparation$ExistingCensus"))
            assertTrue(classes.contains("org.xar.ck3.control.platform."+name));
        assertTrue(classes.contains("org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes$DirectoryReadOnlyLease"));
    }
}
