package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageCodec;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.LaunchSourceBinding;
import org.xar.ck3.control.platform.NativeBridgeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.SteamOfflineProbe;

/** Physical source/configuration DATA, never a synthetic successful Native build or running Game. */
final class RootNativeProofConsumerFlowTest {
    private static final List<String> ARTIFACT_SOURCES=List.of("bridge.cpp","current_player_observers12004.cpp",
            "artifact_personal_use12004.cpp","artifact_personal_use12004_native.cpp","player_inventory_window12004_transport.cpp",
            "player_inventory_window12004_json.cpp","character_skill_effect12004_request.cpp","character_skill_effect12004.cpp",
            "character_skill_effect12004_native.cpp","character_skill_effect12004_json.cpp","character_skill_effect12004_mailbox.cpp",
            "ck3_12004_holy_site_relic_context.cpp","ck3_12004_holy_site_relic_context_json.cpp",
            "ck3_12004_holy_site_relic_permissions.cpp","ck3_12004_holy_site_relic_permissions_json.cpp",
            "ck3_12004_holy_site_relic_action_context.cpp","ck3_12004_holy_site_relic_action_context_json.cpp",
            "ck3_12004_holy_site_relic_recognition_matrix.cpp","ck3_12004_holy_site_relic_recognition_matrix_json.cpp",
            "ck3_12004_holy_site_modifier_aggregate.cpp","ck3_12004_holy_site_modifier_aggregate_json.cpp",
            "ck3_12004_holy_site_relic_actions.cpp","ck3_12004_holy_site_relic_actions_json.cpp",
            "holy_site_relic_navigation12004.cpp","holy_site_relic_request12004.cpp","holy_site_relic_action_preview_adapter12004.cpp",
            "ingame_ui_navigation_v1.cpp","ingame_ui_mailbox_v1.cpp","ck3_12004_ingame_ui.cpp",
            "holy_site_creation12004.cpp","holy_site_creation12004_mailbox.cpp","holy_site_creation12004_json.cpp",
            "holy_site_creation12004_navigation.cpp");
    private static final String CROWN="ck3_12004_realm_law_action_mailbox.cpp";
    private static final String HEADER="ck3_autonomous_player/native_bridge/include/xar_bridge/army_observer_research_control_12004.hpp";
    @TempDir Path root;
    private final Instant now=Instant.now();
    private final Clock clock=Clock.fixed(now,ZoneOffset.UTC);
    private int sequence;
    private FileRef lastPlan;

    private FileRef data(String relative)throws IOException {
        Path path=root.resolve(relative);Files.createDirectories(path.getParent());
        Files.writeString(path,"// owned software DATA only: "+relative,StandardOpenOption.CREATE_NEW);
        return FileRef.measure(path);
    }
    private FileRef encoded(String relative,byte[] bytes)throws IOException {
        Path path=root.resolve(relative);Files.createDirectories(path.getParent());Files.write(path,bytes,StandardOpenOption.CREATE_NEW);
        return FileRef.measure(path);
    }
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private Path nativeRoot(){return root.resolve("ck3_autonomous_player/native_bridge");}
    private List<FileRef> sourceFiles()throws IOException {
        var refs=new TreeMap<String,FileRef>();
        for(var role:RootRuntimeNativeOriginals.Role.values()) {
            var ref=data(role.repositoryRelative());refs.put(ref.path(),ref);
        }
        for(String name:ARTIFACT_SOURCES) {
            String relative="ck3_autonomous_player/native_bridge/src/"+name;
            Path path=root.resolve(relative);if(!Files.exists(path)){var ref=data(relative);refs.put(ref.path(),ref);}
        }
        var crown=data("ck3_autonomous_player/native_bridge/src/"+CROWN);refs.put(crown.path(),crown);
        var header=data(HEADER);refs.put(header.path(),header);
        return List.copyOf(refs.values());
    }
    private NativeLaunchPlanCodec.Configuration configuration(List<FileRef> sources,NativeLaunchEvidence.Inputs inputs)throws IOException {
        var game=data("artifacts/"+(sequence++)+"/ck3.exe");
        var bridge=data("artifacts/"+(sequence++)+"/xar_ck3_bridge.dll");
        var injector=data("artifacts/"+(sequence++)+"/xar_ck3_bridge_injector.exe");
        var steam=data("artifacts/"+(sequence++)+"/steam.exe");
        var review=new LaunchSourceBinding.Review(WindowsJobProcess.currentMachineId(),now.plusSeconds(900),
                game,bridge,injector,inputs,nativeRoot(),sources);
        return new NativeLaunchPlanCodec.Configuration("source-data","source-data-session",review,
                root.resolve("profile"),root.resolve("state"),root.resolve("evidence"),
                "\\\\.\\pipe\\source-data-only","software-bridge","software-adapter",new NativeLaunchPlan.NewGame(),false,
                NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of(),1L<<30,64L<<20,
                now.plusSeconds(600),Duration.ofSeconds(5),Duration.ofSeconds(30),
                new SteamOfflineProbe.Plan(review.machineId(),steam,now.plusSeconds(500)),
                NativeLaunchPlan.PreparedProfile.vanilla(),32);
    }
    private NativeLaunchPlan flow(NativeLaunchPlanCodec.Configuration configuration)throws Exception {
        Path parent=root.resolve("plan-"+(sequence++));Files.createDirectories(parent);
        var request=new RootNativeLaunchPlanInputs.Request(configuration,parent.resolve(RootNativeLaunchPlanInputs.FILE_NAME),now.plusSeconds(300));
        var invocation=new RootNativeLaunchPlanInputs.Invocation(RootNativeLaunchPlanInputs.Mode.QUOTE,request,Optional.empty());
        var decoded=RootNativeLaunchPlanInputs.decodeInvocation(RootNativeLaunchPlanInputs.encodeInvocation(invocation));
        assertEquals(invocation,decoded);
        byte[] quote=RootNativeLaunchPlanInputs.execute(decoded,clock);
        var producedQuote=RootBootstrapProtocol.decode(quote,RootBootstrapProtocol.FRAME_BYTES-1,RootBootstrapProtocol.OrdinaryQuote.class);
        assertFalse(Files.exists(request.target()),"QUOTE never claims a formal issuer-authorized publication");
        byte[] actual=RootNativeLaunchPlanInputs.encodeConfiguration(decoded.request().configuration());
        var prepared=RootNativeLaunchPlanInputs.prepare(decoded.request(),clock);
        assertEquals(List.of(prepared.quote()),producedQuote.outputs());
        assertEquals(actual.length,prepared.quote().bytes());
        assertEquals(org.xar.ck3.control.application.driver.DriverJson.sha256(actual),prepared.quote().sha256());
        var file=encoded(root.relativize(request.target()).toString(),actual);
        lastPlan=file;
        var plan=RootProfileBootstrapCommand.readMappedSavedPlan(exact(file));
        assertEquals(configuration,NativeLaunchPlanCodec.describe(plan));
        assertThrows(IllegalStateException.class,()->plan.sources().nativeProof());
        return plan;
    }

    @Test void actualProducerCodecPhysicalReaderFeedsAllFourSourceConsumersWithoutNativeProof()throws Exception {
        var sources=sourceFiles();var plan=flow(configuration(sources,null));
        var selected=RootArtifactsSourcesFactory.nativeSources(nativeRoot().resolve("src"),plan);
        assertEquals(ARTIFACT_SOURCES.size(),selected.size());
        for(var ref:selected.values())new FileRef(ref.path(),ref.bytes(),ref.sha256()).verify();
        assertEquals(CROWN,Path.of(RootRuntimeCatalogFactory.crownDefinition(plan).path()).getFileName().toString());
        assertEquals(root.resolve(HEADER),Path.of(RootDriverProductSourcesFactory.nativeCutSource(plan,HEADER).path()));
        var originals=new ArrayList<RootRuntimeNativeOriginals.Original>();
        for(var role:RootRuntimeNativeOriginals.Role.values())originals.add(new RootRuntimeNativeOriginals.Original(role,
                role.repositoryRelative(),FileRef.measure(root.resolve(role.repositoryRelative()))));
        var config=new RootRuntimeNativeOriginals.Configuration(RootRuntimeNativeOriginals.SCHEMA,
                WindowsJobProcess.currentMachineId(),now.minusSeconds(1).toString(),now.plusSeconds(300).toString(),originals);
        var original=encoded("native-originals.json",RootRuntimeNativeOriginals.encode(config));
        var bound=RootRuntimeNativeOriginals.readExact(original,clock);bound.requireQualifiedCut(plan);
        Files.writeString(root.resolve(HEADER),"changed source");
        assertThrows(IOException.class,()->RootDriverProductSourcesFactory.nativeCutSource(plan,HEADER));
        Files.writeString(root.resolve(RootRuntimeNativeOriginals.Role.RITE_CREATION_NATIVE_HEADER.repositoryRelative()),"changed original source");
        assertThrows(IOException.class,()->bound.requireQualifiedCut(plan));
    }

    @Test void sourceConsumersRejectAbsentOrDuplicatedDeclaredRefsThroughTheSameDataFlow()throws Exception {
        var sources=sourceFiles();var absent=new ArrayList<>(sources);
        absent.removeIf(ref->Path.of(ref.path()).getFileName().toString().equals("bridge.cpp"));
        var missing=flow(configuration(absent,null));
        assertThrows(IOException.class,()->RootArtifactsSourcesFactory.nativeSources(nativeRoot().resolve("src"),missing));
        var duplicate=new ArrayList<>(sources);duplicate.add(sources.stream().filter(ref->ref.path().endsWith(CROWN)).findFirst().orElseThrow());
        var doubled=flow(configuration(duplicate,null));
        assertThrows(IOException.class,()->RootRuntimeCatalogFactory.crownDefinition(doubled));
        assertThrows(IOException.class,()->RootDriverProductSourcesFactory.nativeCutSource(doubled,"absent.hpp"));
    }

    @Test void genuineLifecycleAndStockGuardsRejectMissingOrMalformedOriginalStagesNormally()throws Exception {
        var sources=sourceFiles();var missing=flow(configuration(sources,null));var reader=new RecordingRealReader();
        var producer=exact(sources.getFirst());
        assertThrows(IOException.class,()->RootManagedLifecycleFactory.requireProducer(missing,producer,reader));
        assertThrows(IOException.class,()->RootH2743StockPredicateAdmission.qualifiedNativeCut(missing,reader));
        assertEquals(0,reader.calls);
        var stages=new NativeLaunchEvidence.Inputs(encoded("env-invalid.json","{}".getBytes()),
                encoded("build-invalid.json","{}".getBytes()),encoded("registration-invalid.json","{}".getBytes()));
        var malformed=flow(configuration(sources,stages));
        assertThrows(IOException.class,()->RootManagedLifecycleFactory.requireProducer(malformed,producer,reader));
        assertThrows(IOException.class,()->RootH2743StockPredicateAdmission.qualifiedNativeCut(malformed,reader));
        assertEquals(2,reader.calls,"both real guards reach the existing original-stage reader");
        assertEquals(malformed.sources().review().bridgeDll(),reader.last.bridgeDll());
        assertEquals(malformed.sources().review().injector(),reader.last.injector());
    }

    private record PackageFixture(JavaRuntimePackageModel.Request request,FileRef hostFile,FileRef launchPlan) { }
    private PackageFixture packageFixture(NativeLaunchPlanCodec.Configuration configuration,
            NativeLaunchPlanCodec.Configuration selected)throws Exception {
        flow(configuration);String prefix="package-"+(sequence++)+"/";Files.createDirectories(root.resolve(prefix));
        var launchPlan=lastPlan;
        var anchor=data(prefix+"ledger/anchor.json");var writer=data(prefix+"writer-source.java");
        var host=new RootApplicationConfiguration(configuration.review().machineId(),HostMode.MCP_STDIO,now.plusSeconds(300),exact(launchPlan),
                new WriterContracts.Layout(root.resolve(prefix+"ledger/snapshot.json"),exact(anchor),configuration.review().machineId()),
                List.of(exact(writer)),root.resolve(prefix+"immutable"),1<<20);
        var hostInvocation=new RootApplicationConfigurationProducer.Request(RootApplicationConfigurationProducer.Mode.QUOTE,
                host,root.resolve(prefix+"application.json"),null);
        var hostDecoded=RootApplicationConfigurationProducer.decodeRequest(RootApplicationConfigurationProducer.encodeRequest(hostInvocation));
        assertEquals(hostInvocation,hostDecoded);
        RootApplicationConfigurationProducer.execute(hostDecoded,clock);
        var hostPrepared=RootApplicationConfigurationProducer.prepare(host,hostDecoded.target(),clock);
        assertFalse(Files.exists(hostDecoded.target()));
        var hostFile=encoded(prefix+"application.json",hostPrepared.bytes());assertEquals(hostPrepared.expected(),hostFile);
        var env=encoded(prefix+"package-env-invalid.json","{}".getBytes());var build=encoded(prefix+"package-build-invalid.json","{}".getBytes());
        var registration=encoded(prefix+"package-registration-invalid.json","{}".getBytes());var settings=data(prefix+"launcher-settings.json");
        var nativeInputs=new JavaRuntimePackageModel.NativeInputs(env,build,registration,selected.review().nativeSourceRoot().toString(),
                selected.review().completeRuntimeSources().stream().filter(ref->Path.of(ref.path()).startsWith(selected.review().nativeSourceRoot())).toList(),
                selected.review().bridgeDll(),selected.review().injector(),selected.review().gameExecutable(),settings,
                selected.bridgeVersion(),selected.adapterId());
        var java=data(prefix+"jdk/bin/java.exe");var service=data(prefix+"service-build-invalid.json");
        var request=new JavaRuntimePackageModel.Request(JavaRuntimePackageModel.REQUEST_SCHEMA,host.machineId(),"data-rejection-only",
                now.toString(),now.plusSeconds(300).toString(),root.resolve(prefix+"package-output").toString(),service,
                new JavaRuntimePackageModel.JavaHome(root.resolve(prefix+"jdk").toString(),java,List.of(java)),nativeInputs,
                List.of(new JavaRuntimePackageModel.ContractPin("software-source",writer)),hostFile,
                new JavaRuntimePackageModel.LaunchSettings(host.mode(),31337,32L<<20,64L<<20,root.resolve(prefix+"temp").toString(),
                        root.resolve(prefix+"temp/native").toString()),List.of(),1<<20);
        var requestFile=encoded(prefix+"package-request.json",JavaRuntimePackageCodec.encodeRequest(request));
        var decodedRequest=JavaRuntimePackageCodec.readRequest(requestFile);assertEquals(request,decodedRequest);
        assertEquals(host,RootApplicationConfiguration.readExact(hostFile));
        return new PackageFixture(decodedRequest,hostFile,launchPlan);
    }

    @Test void packageUsesItsOwnOriginalStagesAndBindsThePhysicalHostArtifactsBeforeReadingProof()throws Exception {
        var sources=sourceFiles();var configuration=configuration(sources,null);var fixture=packageFixture(configuration,configuration);
        var decodedRequest=fixture.request();var request=decodedRequest;var hostFile=fixture.hostFile();var launchPlan=fixture.launchPlan();
        var nativeInputs=request.nativeInputs();
        var reader=new RecordingRealReader();var verifier=new RootPackageNativeVerifier(reader);
        assertThrows(IOException.class,()->verifier.verify(decodedRequest,hostFile));
        assertEquals(1,reader.calls,"optional ordinary Review evidence is null; package originals still reach the real reader");
        assertEquals(nativeInputs.stageActuals(),reader.last.inputs().references());
        assertEquals(configuration.review().bridgeDll(),reader.last.bridgeDll());
        byte[] originalPlan=Files.readAllBytes(Path.of(launchPlan.path()));
        Files.writeString(Path.of(launchPlan.path())," ",StandardOpenOption.APPEND);
        assertThrows(IOException.class,()->verifier.verify(decodedRequest,hostFile));
        assertEquals(1,reader.calls,"a valid decoded value with changed physical plan bytes cannot reach original proof lookup");
        Files.write(Path.of(launchPlan.path()),originalPlan);
        var otherDll=data("other-host/xar_ck3_bridge.dll");
        var mismatch=new JavaRuntimePackageModel.NativeInputs(nativeInputs.environmentActual(),nativeInputs.buildActual(),nativeInputs.registrationActual(),nativeInputs.sourceRoot(),
                nativeInputs.completeSources(),otherDll,nativeInputs.injector(),nativeInputs.gameExecutable(),nativeInputs.launcherSettings(),
                nativeInputs.bridgeVersion(),nativeInputs.adapterId());
        var changed=new JavaRuntimePackageModel.Request(request.schema(),request.machineId(),request.generation(),
                request.createdAtUtc(),request.reviewAtUtc(),request.outputRoot(),request.serviceBuildActual(),request.javaHome(),
                mismatch,request.contracts(),request.hostConfiguration(),request.launch(),request.additionalRequiredClasses(),request.maximumOutputBytes());
        var changedFile=encoded("mismatched-package-request.json",JavaRuntimePackageCodec.encodeRequest(changed));
        assertThrows(IOException.class,()->verifier.verify(JavaRuntimePackageCodec.readRequest(changedFile),hostFile));
        assertEquals(1,reader.calls,"a different selected DLL cannot reach the reader for this physical host");
    }

    private static NativeLaunchPlanCodec.Configuration withReview(NativeLaunchPlanCodec.Configuration original,
            Path nativeRoot,List<FileRef> runtimeSources) {
        var before=original.review();var review=new LaunchSourceBinding.Review(before.machineId(),before.expiresAt(),
                before.gameExecutable(),before.bridgeDll(),before.injector(),before.nativeEvidence(),nativeRoot,runtimeSources);
        return new NativeLaunchPlanCodec.Configuration(original.requestId(),original.sessionId(),review,original.profileDirectory(),
                original.stateDirectory(),original.evidenceRoot(),original.pipeName(),original.bridgeVersion(),original.adapterId(),
                original.load(),original.debugMode(),original.windowPolicy(),original.environment(),original.gameMemoryBytes(),
                original.injectorMemoryBytes(),original.deadline(),original.injectorTimeout(),original.startupTimeout(),
                original.steam(),original.preparedProfile(),original.maximumEvidenceRows());
    }

    @Test void physicalHostNativeRootAndCompleteCutMustMatchBeforeTheOriginalStageReader()throws Exception {
        var sources=sourceFiles();var selected=configuration(sources,null);
        var nativeSource=sources.stream().filter(ref->Path.of(ref.path()).startsWith(nativeRoot())).findFirst().orElseThrow();
        var missing=new ArrayList<>(sources);missing.remove(nativeSource);
        var extra=new ArrayList<>(sources);extra.add(data("ck3_autonomous_player/native_bridge/src/extra-host-only.cpp"));
        var replaced=new ArrayList<>(missing);replaced.add(data("ck3_autonomous_player/native_bridge/src/replaced-source.cpp"));
        var duplicate=new ArrayList<>(sources);duplicate.add(nativeSource);
        var wrongPin=new ArrayList<>(missing);wrongPin.add(new FileRef(nativeSource.path(),nativeSource.bytes(),"f".repeat(64)));
        Path otherRoot=root.resolve("different-native-root");Files.createDirectory(otherRoot);
        var sameBytesAtAnotherRoot=new ArrayList<FileRef>();
        for(var source:sources) {
            Path original=Path.of(source.path());
            if(original.startsWith(nativeRoot())) {
                Path target=otherRoot.resolve(nativeRoot().relativize(original));
                var copy=encoded(root.relativize(target).toString(),Files.readAllBytes(original));
                assertEquals(source.bytes(),copy.bytes());assertEquals(source.sha256(),copy.sha256());
                sameBytesAtAnotherRoot.add(copy);
            } else sameBytesAtAnotherRoot.add(source);
        }
        assertFalse(Files.isSameFile(nativeRoot(),otherRoot),"equal source bytes cannot make two roots the same physical input");
        var cases=Map.of("missing-root",withReview(selected,null,sources),
                "different-root-same-source-bytes",withReview(selected,otherRoot,sameBytesAtAnotherRoot),
                "missing-physical-root",withReview(selected,root.resolve("absent-native-root"),sources),
                "missing-native-source",withReview(selected,nativeRoot(),missing),
                "extra-native-source",withReview(selected,nativeRoot(),extra),
                "replaced-native-source",withReview(selected,nativeRoot(),replaced),
                "duplicated-native-source",withReview(selected,nativeRoot(),duplicate),
                "changed-native-pin",withReview(selected,nativeRoot(),wrongPin));
        for(var variant:cases.entrySet()) {
            var fixture=packageFixture(variant.getValue(),selected);var reader=new RecordingRealReader();
            assertEquals(selected.review().gameExecutable(),variant.getValue().review().gameExecutable());
            assertEquals(selected.review().bridgeDll(),variant.getValue().review().bridgeDll());
            assertEquals(selected.review().injector(),variant.getValue().review().injector());
            assertNull(variant.getValue().review().nativeEvidence(),"ordinary DATA is not required to carry proof");
            assertThrows(IOException.class,()->new RootPackageNativeVerifier(reader).verify(fixture.request(),fixture.hostFile()),variant.getKey());
            assertEquals(0,reader.calls,variant.getKey()+" must fail before original stage lookup");
        }
    }

    @Test void nonNativeRuntimeRefsRemainInThePhysicalHostWhileTheMatchingNativeCutReachesTheRealReader()throws Exception {
        var sources=sourceFiles();var selected=configuration(sources,null);
        var runtime=data("runtime/AdditionalRuntime.java");var withRuntime=new ArrayList<>(sources);withRuntime.add(runtime);
        var fixture=packageFixture(withReview(selected,nativeRoot(),withRuntime),selected);var reader=new RecordingRealReader();
        var actual=RootProfileBootstrapCommand.readMappedSavedPlan(exact(fixture.launchPlan()));
        assertTrue(actual.sources().review().completeRuntimeSources().contains(runtime));
        assertThrows(IOException.class,()->new RootPackageNativeVerifier(reader).verify(fixture.request(),fixture.hostFile()));
        assertEquals(1,reader.calls,"matching physical Native cut permits the genuine reader to inspect the request's invalid original stages");
        assertFalse(reader.last.completeSources().contains(runtime));
    }

    static final class RecordingRealReader implements NativeLaunchEvidence.Port {
        private final NativeBridgeLaunchEvidence delegate=new NativeBridgeLaunchEvidence();
        int calls;NativeLaunchEvidence.Expected last;
        @Override public NativeLaunchEvidence.Proof verify(NativeLaunchEvidence.Expected expected)throws IOException {
            calls++;last=expected;return delegate.verify(expected);
        }
    }
}
