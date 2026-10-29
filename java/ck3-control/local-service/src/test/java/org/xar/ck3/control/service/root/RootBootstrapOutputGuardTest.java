package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual bounded native temporary roots and immutable producer/consumer. Test issuer cards are software fixtures,
 * never production capacity, a continuity writer, a Game, complete public migration or runtime admission. */
class RootBootstrapOutputGuardTest {
    @TempDir Path root;
    private static final Instant NOW=Instant.parse("2026-10-24T01:00:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    private record Fixture(Path asset,Path control,FileRef binding,FileRef capacity,byte[] body,Clock clock) {
        @Override public byte[] body(){return body.clone();}
        RootBootstrapOutputGuard open()throws IOException{return RootBootstrapOutputGuard.readExact(binding,clock);}
    }
    private Fixture fixture()throws IOException {
        return fixture(Kind.MCP_ADMISSION,"{\"actual_software_fixture\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
    }
    private Fixture fixture(Kind kind,byte[] body)throws IOException {
        return fixture(kind,body,CLOCK);
    }
    private Fixture fixture(Kind kind,byte[] body,Clock clock)throws IOException {
        Instant now=clock.instant();
        Path asset=Files.createDirectory(root.resolve("asset")),control=Files.createDirectory(root.resolve("control"));
        String machine=WindowsJobProcess.currentMachineId(),observed=now.minusSeconds(1).toString(),review=now.plusSeconds(3600).toString();
        var declaration=new Declaration(DECLARATION,PURPOSE,machine,"/root","bootstrap-fixture",observed,review,
                asset.toString(),SharedSourceFiles.nativeDirectory(asset),control.toString(),SharedSourceFiles.nativeDirectory(control),
                1536L*1024,512L*1024,1<<20,64,List.of(new Output(kind,"admission.json",body.length,DriverJson.sha256(body))),List.of(),List.of());
        FileRef declarationRef=write(control.resolve("declaration.json"),encode(declaration));
        AssetCensus census=RootBootstrapOutputGuard.observeAssetRoot(declarationRef,clock);
        FileRef censusRef=write(control.resolve("census.json"),encode(census));
        var policy=StrictJson.object();policy.put("policy_version","1.0.0");var rules=policy.putObject("capacity");
        rules.put("safety_floor_bytes",2L<<30);rules.put("safety_ceiling_bytes",20L<<30);rules.put("default_project_quota_ceiling_bytes",100L<<30);
        rules.put("safety_volume_fraction",new java.math.BigDecimal("0.05"));rules.put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(control.resolve("policy.json"),ControlBuild.strictMapper().writeValueAsBytes(policy));
        Path volume=asset.getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        var financial=StrictJson.object();financial.put("scope","software-fixture-actual-volume-observation");financial.put("machine_id",machine);
        financial.put("total_bytes",total);financial.put("usable_bytes",free);financial.put("old_workpackage_actual_is_unknown",true);
        FileRef head=write(control.resolve("financial.json"),StrictJson.canonical(financial));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,
                null,Math.subtractExact(total,free),head);
        var release=new CapacityRelease(CAPACITY,PURPOSE,machine,"/root",ISSUER,"bootstrap-fixture",now.toString(),review,
                policyRef,declarationRef,censusRef,head,2L<<20,List.of(new Volume(volume.toString(),2L<<20,0,0,total,review,usage,List.of(),0)),List.of());
        FileRef capacity=write(control.resolve("capacity.json"),encode(release));
        var binding=new Binding(BINDING,PURPOSE,machine,"/root",ISSUER,"bootstrap-fixture",now.toString(),review,declarationRef,censusRef,capacity);
        return new Fixture(asset,control,write(control.resolve("binding.json"),encode(binding)),capacity,body,clock);
    }
    @Test void firstTypedDriverPublicationUsesTheActualBodyGuardAndColdDataConsumer()throws Exception {
        Path environment=root.resolve("actual-environment.json");Files.writeString(environment,"{\"software_input_only\":true}");
        var base=RootOriginalDriverRunProfileProducerTest.profile(environment);
        var profile=new RootFrozenRunProfile.Request(base.machineId(),base.observedAt(),base.reviewAt(),base.requestId(),
                base.sessionId(),base.environmentManifest(),RootFrozenRunProfile.LifecycleMode.ORDINARY_CAMPAIGN_SUCCESSION,
                true,base.legacyImport());
        FileRef request=write(root.resolve("driver-producer-request.json"),RootOriginalDriverRunProfileProducer.encode(new RootOriginalDriverRunProfileProducer.Request(profile)));
        Fixture fixture=fixture(Kind.ORIGINAL_DRIVER_RUN_PROFILE,RootFrozenRunProfile.encode(profile),RootOriginalDriverRunProfileProducerTest.CLOCK);
        Path target=fixture.asset().resolve("admission.json");
        var producer=RootOriginalDriverRunProfileProducer.prepare(request,target,RootOriginalDriverRunProfileProducerTest.CLOCK);
        var payload=RootProfileBootstrapInputs.originalDriverRunProfile(producer);assertFalse(Files.exists(target));
        assertEquals(Kind.ORIGINAL_DRIVER_RUN_PROFILE,payload.quote().getFirst().kind());
        try(var guard=fixture.open()){
            var created=payload.createNew(guard);assertEquals(1,created.size());assertEquals(1,guard.accounting().completedOutputs());
            producer.verifyCreated();
            var actual=created.getFirst().original();
            var pins=List.of(
                    new RootRuntimeDefinitionModel.DataPin(RootRuntimeDefinitionModel.DataRole.ORIGINAL_DRIVER_RUN_PROFILE,actual),
                    new RootRuntimeDefinitionModel.DataPin(RootRuntimeDefinitionModel.DataRole.EXPLICIT_FRESH_PACT,actual));
            assertEquals(actual,RootRuntimeDefinitionModel.explicitFreshPactProfile(pins));
            byte[] body=RootRuntimeDefinitions.readData(pins.getFirst());assertEquals(profile,RootFrozenRunProfile.decode(body));
            assertArrayEquals(body,RootRuntimeDefinitions.readData(pins.get(1)));
            assertTrue(RootFrozenRunProfile.decode(body).ordinaryCampaignNoPact());
            assertArrayEquals(RootFrozenRunProfile.encode(profile),body);
            assertThrows(IOException.class,()->payload.createNew(guard));
        }
    }
    @Test void independentFiniteOutputWritesAndReopensActualImmutableOriginalWithoutAContinuityWriter()throws IOException {
        Fixture fixture=fixture();try(var guard=fixture.open()){
            Path target=fixture.asset().resolve("admission.json");
            RootPublicMcpAdmission.requireOutputPlan(guard,target,new Output(Kind.MCP_ADMISSION,"admission.json",fixture.body().length,DriverJson.sha256(fixture.body())));
            guard.requireTargets(List.of(target));var port=guard.files();assertSame(port,guard.files());
            var original=port.createNew(target,fixture.body());port.verify(original);assertArrayEquals(fixture.body(),port.read(original,1<<20));
            guard.requireTargets(List.of(target));assertEquals(1,guard.accounting().completedOutputs());assertEquals(0,guard.accounting().unresolvedPeakBytes());
        }
    }
    @Test void publicationRequestKindUsesTheSameFiniteSingleOutputAuthorityAndGenericCliCannotReplaceItsProducer()throws IOException {
        byte[] body="{\"software_storage_fixture_only\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Fixture fixture=fixture(Kind.RUNTIME_DEFINITIONS_PUBLICATION_REQUEST,body);
        var output=new Output(Kind.RUNTIME_DEFINITIONS_PUBLICATION_REQUEST,"admission.json",body.length,DriverJson.sha256(body));
        Path target=fixture.asset().resolve("admission.json");
        try(var guard=fixture.open()){
            guard.requirePlan(fixture.asset(),List.of(output),List.of(),List.of());
            var original=guard.files().createNew(target,body);guard.files().verify(original);
            assertArrayEquals(body,guard.files().read(original,1<<20));
            assertEquals(1,guard.accounting().completedOutputs());
            assertThrows(IOException.class,()->guard.files().createNew(target,body));
        }
        // Storage evidence only: the fixture body is never accepted as an SDK publication request.
        FileRef raw=write(root.resolve("publication-request-custody-fixture.json"),body);
        var request=new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,WindowsJobProcess.currentMachineId(),
                NOW.plusSeconds(3600).toString(),RootJavaBootstrapInputs.Mode.QUOTE,null,
                List.of(new RootJavaBootstrapInputs.Item(Kind.RUNTIME_DEFINITIONS_PUBLICATION_REQUEST,raw,target.toString())));
        assertThrows(IOException.class,()->RootJavaBootstrapInputs.prepare(request,CLOCK));
        assertThrows(IllegalArgumentException.class,()->new Output(Kind.RUNTIME_DEFINITIONS_PUBLICATION_REQUEST,"too-large.json",(1L<<20)+1,"1".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->new Output(Kind.ARMY_QUERY_HISTORY_CONFIGURATION,"too-large-army.json",65537,"1".repeat(64)));
    }
    @Test void publicAdmissionPublisherRejectsAnotherKindEvenWhenTheSameOutputBytesWerePriced()throws IOException {
        byte[] body="{\"software_storage_fixture_only\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Fixture fixture=fixture(Kind.INITIAL_POLICY,body);Path target=fixture.asset().resolve("admission.json");
        var expected=new Output(Kind.MCP_ADMISSION,"admission.json",body.length,DriverJson.sha256(body));
        try(var guard=fixture.open()) {
            assertThrows(IOException.class,()->RootPublicMcpAdmission.requireOutputPlan(guard,target,expected));
            assertFalse(Files.exists(target));assertEquals(0,guard.accounting().completedOutputs());
        }
    }
    @Test void wrongTypedProducerBodyForeignTargetAndReplaceAreRejectedBeforeWriting()throws IOException {
        Fixture fixture=fixture();try(var guard=fixture.open()){
            Path target=fixture.asset().resolve("admission.json");assertThrows(IOException.class,()->guard.files().createNew(target,new byte[]{'{','}'}));assertFalse(Files.exists(target));
            Path foreign=fixture.control().resolve("wrong-output.json");assertThrows(IOException.class,()->guard.files().createNew(foreign,fixture.body()));assertFalse(Files.exists(foreign));
            assertThrows(IOException.class,()->guard.files().replace(target,fixture.body()));assertFalse(Files.exists(target));
        }
    }
    @Test void exactAuthorityFileIdentityReplacementCannotResetAnOpenBootstrapBudget()throws IOException {
        Fixture fixture=fixture();try(var guard=fixture.open()){
            Path source=Path.of(fixture.capacity().path()),replacement=fixture.control().resolve("replacement.json");Files.copy(source,replacement);
            Files.setLastModifiedTime(replacement,Files.getLastModifiedTime(source));Files.move(replacement,source,StandardCopyOption.REPLACE_EXISTING);
            assertThrows(IOException.class,()->guard.requireTargets(List.of(fixture.asset().resolve("admission.json"))));
        }
    }
    @Test void changedActualCensusExpiredCardAndUnpricedFileAreNeverAcceptedAsEmptyInputs()throws IOException {
        Fixture fixture=fixture();Files.write(fixture.asset().resolve("unpriced.json"),new byte[]{'{','}'});
        assertThrows(IOException.class,fixture::open);Files.delete(fixture.asset().resolve("unpriced.json"));
        assertThrows(IOException.class,()->RootBootstrapOutputGuard.readExact(fixture.binding(),Clock.fixed(NOW.plusSeconds(3601),ZoneOffset.UTC)));
        try(var guard=fixture.open()){
            assertThrows(IOException.class,()->guard.requireTargets(List.of(fixture.asset().resolve("not-declared.json"))));
        }
    }
    @Test void strictIssuerWireRejectsMissingExplicitNullBooleanAndFloatBytes()throws IOException {
        Fixture fixture=fixture();byte[] actual=Files.readAllBytes(Path.of(fixture.capacity().path()));
        var parsed=ControlBuild.strictMapper().readTree(actual);var row=(com.fasterxml.jackson.databind.node.ObjectNode)parsed;
        row.put("joint_maximum_charged_bytes",true);byte[] booleanWire=ControlBuild.strictMapper().writeValueAsBytes(row);
        assertThrows(IOException.class,()->decode(booleanWire,CapacityRelease.class));
        row.put("joint_maximum_charged_bytes",2.0);byte[] floatWire=ControlBuild.strictMapper().writeValueAsBytes(row);
        assertThrows(IOException.class,()->decode(floatWire,CapacityRelease.class));
        row.put("joint_maximum_charged_bytes",2L<<20);((com.fasterxml.jackson.databind.node.ObjectNode)row.withArray("volumes").get(0)).remove("finite_quota_override_bytes");
        byte[] missing=ControlBuild.strictMapper().writeValueAsBytes(row);assertThrows(IOException.class,()->decode(missing,CapacityRelease.class));
    }
    @Test void soleSwayConfigurationEncoderQuotesWritesAndReadsTheSameActualOriginal()throws IOException {
        Path original=root.resolve("sway-formal-original.json");Files.writeString(original,"{\"original_fixture_data\":true}");
        FileRef actual=FileRef.measure(original);var exact=new ExactRef(actual.path(),actual.bytes(),actual.sha256());
        var typed=new RootSwaySourcesFactory.SourceConfiguration(WindowsJobProcess.currentMachineId(),NOW.minusSeconds(1),NOW.plusSeconds(3600),
                root.resolve("original-writer.lock"),original,new OrdinarySwayService.Capabilities(true,true,true),
                new RootRuntimeDomainAssembly.SwayOriginals(exact,Optional.of(exact),exact),false);
        byte[] body=RootSwaySourcesFactory.encode(typed);FileRef input=write(root.resolve("actual-sway-configuration.json"),body);
        Fixture fixture=fixture(Kind.SWAY_CONFIGURATION,body);Path target=fixture.asset().resolve("admission.json");
        var request=new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,WindowsJobProcess.currentMachineId(),NOW.plusSeconds(3600).toString(),
                RootJavaBootstrapInputs.Mode.QUOTE,null,List.of(new RootJavaBootstrapInputs.Item(Kind.SWAY_CONFIGURATION,input,target.toString())));
        var quote=RootJavaBootstrapInputs.prepare(request,CLOCK);assertEquals(Kind.SWAY_CONFIGURATION,quote.quote().get(0).kind());
        assertArrayEquals(body,quote.files().get(0).bytes());
        try(var guard=fixture.open()){
            var witness=guard.files().createNew(target,quote.files().get(0).bytes());
            var output=new FileRef(witness.reference().path(),witness.reference().bytes(),witness.reference().sha256());
            assertEquals(typed,RootSwaySourcesFactory.readExact(output));
        }
    }
    @Test void firstSwayConfigurationRequestUsesTypedFreshDataAndActualFiniteWriterWithoutAPreviousConfigFile()throws IOException {
        var source=new RootSwaySourcesFactory.SourceConfiguration(WindowsJobProcess.currentMachineId(),NOW.minusSeconds(1),NOW.plusSeconds(3600),
                root.resolve("fresh-writer.lock"),root.resolve("absent-fresh-sway-ledger.json"),new OrdinarySwayService.Capabilities(true,true,true),
                new RootRuntimeDomainAssembly.SwayFresh(),false);
        byte[] body=RootSwaySourcesFactory.encode(source);Fixture fixture=fixture(Kind.SWAY_CONFIGURATION,body);
        Path target=fixture.asset().resolve("admission.json");
        var quote=new RootSwayConfigurationProducer.Request(RootSwayConfigurationProducer.SCHEMA,source.machineId(),NOW.plusSeconds(3600).toString(),RootJavaBootstrapInputs.Mode.QUOTE,null,target.toString(),source);
        assertEquals(quote,RootSwayConfigurationProducer.decode(RootSwayConfigurationProducer.encode(quote)));
        var planned=RootSwayConfigurationProducer.prepare(quote,CLOCK);assertFalse(Files.exists(target));
        assertEquals(Kind.SWAY_CONFIGURATION,planned.quote().getFirst().kind());
        assertThrows(IOException.class,()->planned.createNew(CLOCK));assertFalse(Files.exists(target));
        var request=new RootSwayConfigurationProducer.Request(RootSwayConfigurationProducer.SCHEMA,source.machineId(),quote.reviewAtUtc(),RootJavaBootstrapInputs.Mode.CREATE_NEW,fixture.binding(),target.toString(),source);
        assertEquals(request,RootSwayConfigurationProducer.decode(RootSwayConfigurationProducer.encode(request)));
        var publisher=RootSwayConfigurationProducer.prepare(request,CLOCK);var published=publisher.createNew(CLOCK);
        assertEquals(publisher.expected(),published.original());assertEquals(source,RootSwaySourcesFactory.readExact(published.original()));
        assertEquals(SharedSourceFiles.nativeFile(target),published.nativeFile());
        assertThrows(IOException.class,()->publisher.createNew(CLOCK));
        Files.writeString(target,"changed actual Sway DATA");assertThrows(Exception.class,()->RootSwaySourcesFactory.readExact(published.original()));
    }
    @Test void firstSwayRequestRejectsMissingBindingMixedBranchAndWrongScalarBeforeOutput()throws IOException {
        var source=new RootSwaySourcesFactory.SourceConfiguration(WindowsJobProcess.currentMachineId(),NOW.minusSeconds(1),NOW.plusSeconds(3600),root.resolve("writer.lock"),root.resolve("no-ledger"),new OrdinarySwayService.Capabilities(true,true,true),new RootRuntimeDomainAssembly.SwayFresh(),false);
        var request=new RootSwayConfigurationProducer.Request(RootSwayConfigurationProducer.SCHEMA,source.machineId(),NOW.plusSeconds(3600).toString(),RootJavaBootstrapInputs.Mode.QUOTE,null,root.resolve("not-written.json").toString(),source);
        for(String defect:List.of("missing-binding","numeric-mode","wrong-schema","mixed-origin","missing-config")) {
            var row=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootSwayConfigurationProducer.encode(request));
            switch(defect){case "missing-binding"->row.remove("binding_ref");case "numeric-mode"->row.put("mode",1);case "wrong-schema"->row.put("schema","unknown");case "mixed-origin"->((com.fasterxml.jackson.databind.node.ObjectNode)row.at("/configuration/initialization")).putNull("guarded_origin_read");case "missing-config"->row.remove("configuration");default->throw new AssertionError(defect);}
            assertThrows(Exception.class,()->RootSwayConfigurationProducer.decode(StrictJson.canonical(row)),defect);
        }
        assertFalse(Files.exists(Path.of(request.target())));
    }
    @Test void obsoleteV2AuthorityCannotSilentlyAcquireNewOutputKinds()throws IOException {
        Fixture fixture=fixture();byte[] actual=Files.readAllBytes(Path.of(fixture.capacity().path()));
        var value=(com.fasterxml.jackson.databind.node.ObjectNode)ControlBuild.strictMapper().readTree(actual);
        value.put("schema","xar.java-root-bootstrap-capacity/v2");byte[] old=ControlBuild.strictMapper().writeValueAsBytes(value);
        assertThrows(IOException.class,()->decode(old,CapacityRelease.class));
    }
    @Test void profileNestedPathsHaveOneClosedFiniteDirectoryContractAndOldAuthorityIsRejected()throws IOException {
        var output=new Output(Kind.PROFILE_PRESETS,"player/game_rules/presets.txt",17,"1".repeat(64));assertEquals(17,output.bytes());
        assertThrows(IllegalArgumentException.class,()->new Output(Kind.PROFILE_PRESETS,"presets.txt",17,"1".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->new Output(Kind.MCP_TOOLS,"player/tools.json",17,"1".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->new Output(Kind.PROFILE_SETTINGS,"pdx_settings.txt",65537,"1".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->new Output(Kind.COA_READ_LIMITS,"coa.json",4097,"1".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->new Output(Kind.PROFILE_PRESETS,"player/../presets.txt",17,"1".repeat(64)));
        Fixture actual=fixture();var binding=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(
                Files.readAllBytes(Path.of(actual.binding().path())));binding.put("schema","xar.java-root-bootstrap-binding/v3");
        assertThrows(IOException.class,()->RootBootstrapOutputContract.decode(StrictJson.canonical(binding),Binding.class));
    }
    @Test void soleCoaLimitsOriginalFlowsThroughTheActualGenericBootstrapCodecAndImmutablePort()throws IOException {
        var limits=new org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs.Limits(65536,32768);
        byte[] encoded=org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs.encodeLimits(limits).bytes();
        Fixture actual=fixture(Kind.COA_READ_LIMITS,encoded);FileRef input=write(root.resolve("limits-original.json"),encoded);
        var request=new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,WindowsJobProcess.currentMachineId(),NOW.plusSeconds(3600).toString(),
                RootJavaBootstrapInputs.Mode.CREATE_NEW,actual.binding(),List.of(new RootJavaBootstrapInputs.Item(Kind.COA_READ_LIMITS,input,actual.asset().resolve("admission.json").toString())));
        var prepared=RootJavaBootstrapInputs.prepare(request,CLOCK);var written=prepared.createNew(CLOCK).getFirst();
        assertEquals(limits,org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs.decodeLimits(new org.xar.ck3.control.application.action.RawJson(
                RootRuntimeDefinitions.read(written.original(),4096))));assertEquals(input.bytes(),written.original().bytes());
    }
    private static FileRef write(Path path,byte[] bytes)throws IOException{Files.write(path,bytes);return FileRef.measure(path);}
}
