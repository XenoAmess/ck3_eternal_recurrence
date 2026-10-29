package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadlineCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignSchedule;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;

/** Real temporary files, codecs, finite Guard and original Root data consumers. Source bodies are explicitly
 * software custody fixtures; these tests grant no Native source-cut, normal-exit, Game or runtime admission. */
class RootPlanningSettingsInputsProducerTest {
    @TempDir Path root;
    private static final Instant NOW=Instant.parse("2026-10-26T01:00:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    private record Fixture(RootPlanningSettingsInputsProducer.Request request,FileRef original,Path asset,Path inputs) { }
    private Fixture fixture()throws IOException {
        Path inputs=Files.createDirectory(root.resolve("inputs")),asset=Files.createDirectory(root.resolve("asset"));
        String machine=WindowsJobProcess.currentMachineId(),observed=NOW.minusSeconds(1).toString(),review=NOW.plusSeconds(3600).toString();
        var natives=new ArrayList<RootRuntimeNativeOriginals.Original>();
        Path originals=Files.createDirectory(inputs.resolve("native"));
        for(var role:RootRuntimeNativeOriginals.Role.values()){
            Path directory=Files.createDirectory(originals.resolve(role.name()));
            Path leaf=directory.resolve(Path.of(role.repositoryRelative()).getFileName());
            natives.add(new RootRuntimeNativeOriginals.Original(role,role.repositoryRelative(),write(leaf,"software custody fixture".getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        }
        var nativeConfig=new RootRuntimeNativeOriginals.Configuration(RootRuntimeNativeOriginals.SCHEMA,machine,observed,review,natives);
        FileRef budget=write(inputs.resolve("budget.json"),new byte[]{'{','}'}),model=write(inputs.resolve("model.json"),new byte[]{'{','}'});
        FileRef inventory=write(inputs.resolve("inventory.json"),new byte[]{'{','}'}),profile=write(inputs.resolve("profile.json"),new byte[]{'{','}'});
        FileRef snapshot=write(inputs.resolve("launch-settings.bin"),new byte[0]);
        FileRef limits=write(inputs.resolve("coa-limits.json"),CoaVfs.encodeLimits(new CoaVfs.Limits(65536,32768)).bytes());
        var queryRequest=new OriginalDriverQueryHistorySettings.Request(machine,NOW.minusSeconds(2),NOW.plusSeconds(3601),
                new OriginalDriverQueryHistorySettings.JavaConfigured(new OriginalDriverQueryHistorySettings.Disabled(),0,
                        OriginalDriverQueryHistorySettings.Admission.ROOT_STORAGE));
        FileRef queryInput=write(inputs.resolve("query-request.json"),OriginalDriverQueryHistorySettings.encodeRequest(queryRequest));
        FileRef producer=write(inputs.resolve("RootArmyQueryHistoryConfigurationProducer.java"),"// software custody fixture".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        FileRef query=write(inputs.resolve("query-settings.json"),OriginalDriverQueryHistorySettings.encode(new OriginalDriverQueryHistorySettings.Document(
                new OriginalDriverQueryHistorySettings.SourceRefs(exact(queryInput),exact(producer)),queryRequest)));
        var lifecycle=new RootRuntimeDomainSettings.Lifecycle(inputs.resolve("state").toString(),inputs.resolve("saves").toString(),
                inputs.resolve("tutorial.txt").toString(),inputs.resolve("evidence").toString(),List.of("clock-status"),1000);
        var settings=new RootRuntimeDomainSettings.Configuration(RootRuntimeDomainSettings.SCHEMA,machine,observed,review,lifecycle,
                inputs.resolve("family-exports").toString(),new RootRuntimeDomainSettings.FormalWar(budget,model,null,null),
                new RootRuntimeDomainSettings.Peacetime(true,true,true),new RootRuntimeDomainSettings.Offline(inputs.resolve("offline").toString(),
                        inputs.resolve("knowledge").toString(),inputs.resolve("grants.json").toString(),1,1),
                new RootRuntimeDomainSettings.NormalExitOriginals(exact(inventory),exact(profile),exact(snapshot)),
                new RootRuntimeDomainSettings.CoaReadLimits(limits),exact(query),new RootRuntimeDomainSettings.PlanFlags(true,true,true,true,true,true,true),null);
        var calendar=OrdinaryCampaignSchedule.calendar("1066.9.15",2);
        var request=new RootPlanningSettingsInputsProducer.Request(RootPlanningSettingsInputsProducer.SCHEMA,machine,observed,review,asset.toString(),
                new RootPlanningSettingsInputsProducer.Life(true,false,true),new RootPlanningSettingsInputsProducer.Timings(32,1000,5000),
                new CampaignDeadline.Founding("actual-request-clock-id",calendar.foundingDate(),calendar.foundingRaw(),2),settings,nativeConfig);
        FileRef original=write(inputs.resolve("planning-settings-request.json"),RootPlanningSettingsInputsProducer.encodeRequest(request));
        return new Fixture(request,original,asset,inputs);
    }
    @Test void soleTypedFirstPublisherCreatesAllFiveAndOriginalConsumersReadTheSameBytes()throws IOException {
        Fixture fixture=fixture();var prepared=RootPlanningSettingsInputsProducer.prepare(fixture.original(),CLOCK);
        assertEquals(fixture.request(),RootPlanningSettingsInputsProducer.decodeRequest(Files.readAllBytes(Path.of(fixture.original().path()))));
        assertEquals(List.of(Kind.LIFE_SETTINGS,Kind.ADVANCE_TIMINGS,Kind.CAMPAIGN_DEADLINE,Kind.REMAINING_DOMAIN_SETTINGS,Kind.NATIVE_DOMAIN_ORIGINALS),
                prepared.quote().stream().map(Output::kind).toList());
        assertFalse(Files.exists(fixture.asset().resolve("life-settings.json")));
        FileRef binding=binding(fixture.asset(),prepared.quote());
        try(var guard=RootBootstrapOutputGuard.readExact(binding,CLOCK)){
            var actual=prepared.createNew(guard);assertEquals(5,actual.size());assertEquals(5,guard.accounting().completedOutputs());
            var life=RootAdvanceRuntimeFacts.Settings.decode(exact(actual.get(0).original()),new RawJson(Files.readAllBytes(Path.of(actual.get(0).original().path()))));
            assertTrue(life.crownQueryEnabled());assertFalse(life.crownPausedQueryEnabled());assertTrue(life.warDailyWatchEnabled());
            var timings=RootAdvanceInfrastructureFactory.Timings.decode(exact(actual.get(1).original()),new RawJson(Files.readAllBytes(Path.of(actual.get(1).original().path()))));
            assertEquals(32,timings.maximumFrames());assertEquals(1000,timings.commandTimeout().toMillis());
            var deadline=CampaignDeadlineCodec.decodeConfiguration(Files.readAllBytes(Path.of(actual.get(2).original().path())),OrdinaryCampaignSchedule::calendar);
            assertEquals(fixture.request().campaignDeadline(),deadline.founding());
            assertEquals(fixture.request().remainingDomainSettings(),RootRuntimeDomainSettings.readExact(actual.get(3).original(),CLOCK).configuration());
            assertEquals(fixture.request().nativeDomainOriginals(),RootRuntimeNativeOriginals.readExact(actual.get(4).original(),CLOCK).configuration());
            var generic=new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,fixture.request().machineId(),fixture.request().reviewAtUtc(),
                    RootJavaBootstrapInputs.Mode.QUOTE,null,actual.stream().map(row->new RootJavaBootstrapInputs.Item(row.kind(),row.original(),
                            fixture.inputs().resolve("copy-"+row.kind().name()+".json").toString())).toList());
            var consumed=RootJavaBootstrapInputs.prepare(generic,CLOCK);
            for(int i=0;i<5;i++)assertArrayEquals(prepared.files().get(i).bytes(),consumed.files().get(i).bytes());
            assertThrows(IOException.class,()->prepared.createNew(guard));
        }
    }
    @Test void strictWireRejectsWrongFieldsMissingRequiredNullAndCoercedValues()throws IOException {
        Fixture fixture=fixture();byte[] raw=Files.readAllBytes(Path.of(fixture.original().path()));
        var value=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(raw);
        ((com.fasterxml.jackson.databind.node.ObjectNode)value.get("timings")).put("maximum_frames",true);
        byte[] booleanWire=StrictJson.canonical(value,1<<20);assertThrows(IOException.class,()->RootPlanningSettingsInputsProducer.decodeRequest(booleanWire));
        value=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(raw);
        ((com.fasterxml.jackson.databind.node.ObjectNode)value.get("timings")).put("command_timeout_millis",1.0);
        byte[] floating=StrictJson.canonical(value,1<<20);assertThrows(IOException.class,()->RootPlanningSettingsInputsProducer.decodeRequest(floating));
        value=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(raw);
        ((com.fasterxml.jackson.databind.node.ObjectNode)value.get("remaining_domain_settings")).remove("stock_read");
        byte[] missingNull=StrictJson.canonical(value,1<<20);assertThrows(IOException.class,()->RootPlanningSettingsInputsProducer.decodeRequest(missingNull));
        value=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(raw);value.put("guessed_seed",42);
        byte[] unknown=StrictJson.canonical(value,1<<20);assertThrows(IOException.class,()->RootPlanningSettingsInputsProducer.decodeRequest(unknown));
    }
    @Test void actualPinnedSourceDriftAndExpiredRequestRejectBeforeFirstOutput()throws IOException {
        Fixture fixture=fixture();var prepared=RootPlanningSettingsInputsProducer.prepare(fixture.original(),CLOCK);
        Path original=Path.of(fixture.request().nativeDomainOriginals().originals().getFirst().original().path());
        Files.writeString(original,"changed source fixture");
        assertThrows(IOException.class,prepared::quote);assertThrows(IOException.class,()->RootPlanningSettingsInputsProducer.prepare(fixture.original(),CLOCK));
        assertThrows(IOException.class,()->RootPlanningSettingsInputsProducer.prepare(fixture.original(),Clock.fixed(NOW.plusSeconds(3600),ZoneOffset.UTC)));
        try(var entries=Files.list(fixture.asset())){assertEquals(0,entries.count());}
    }
    @Test void conflictingCalendarIdentityCannotBecomeAQuotedClock()throws IOException {
        Fixture fixture=fixture();var original=fixture.request();var founding=original.campaignDeadline();
        var wrong=new CampaignDeadline.Founding(founding.campaignId(),founding.startDate(),founding.startDateRaw().add(java.math.BigInteger.ONE),founding.months());
        var request=new RootPlanningSettingsInputsProducer.Request(original.schema(),original.machineId(),original.observedAtUtc(),original.reviewAtUtc(),original.outputRoot(),
                original.life(),original.timings(),wrong,original.remainingDomainSettings(),original.nativeDomainOriginals());
        assertThrows(IllegalArgumentException.class,()->RootPlanningSettingsInputsProducer.encodeFiles(request));
    }
    @Test void independentCoreFirstPublisherNeedsOnlyItsActualRequestAndFeedsAllThreeOriginalConsumers()throws IOException {
        Path inputs=Files.createDirectory(root.resolve("core-inputs")),asset=Files.createDirectory(root.resolve("core-output"));
        var calendar=OrdinaryCampaignSchedule.calendar("1066.9.15",360);
        var request=new RootPlanningSettingsInputsProducer.CoreRequest(RootPlanningSettingsInputsProducer.CORE_SCHEMA,
                WindowsJobProcess.currentMachineId(),NOW.minusSeconds(1).toString(),NOW.plusSeconds(3600).toString(),asset.toString(),
                new RootPlanningSettingsInputsProducer.Life(true,true,true),new RootPlanningSettingsInputsProducer.Timings(4096,30000,300000),
                new CampaignDeadline.Founding("declared-clock",calendar.foundingDate(),calendar.foundingRaw(),360));
        FileRef raw=write(inputs.resolve("core-request.json"),RootPlanningSettingsInputsProducer.encodeCoreRequest(request));
        assertEquals(request,RootPlanningSettingsInputsProducer.decodeCoreRequest(Files.readAllBytes(Path.of(raw.path()))));
        var prepared=RootPlanningSettingsInputsProducer.prepareCore(raw,CLOCK);
        assertEquals(List.of(Kind.LIFE_SETTINGS,Kind.ADVANCE_TIMINGS,Kind.CAMPAIGN_DEADLINE),prepared.quote().stream().map(Output::kind).toList());
        var quote=RootBootstrapProtocol.decode(RootBootstrapProtocol.encode(prepared.quoteEnvelope(),1<<20),1<<20,RootBootstrapProtocol.Quote.class);
        assertEquals("CORE_SETTINGS",quote.phase());assertEquals(prepared.quote(),quote.outputs());assertTrue(quote.retainedInputs().isEmpty());
        try(var guard=RootBootstrapOutputGuard.readExact(binding(asset,prepared.quote()),CLOCK)){
            var actual=prepared.createNew(guard);assertEquals(3,actual.size());
            var generic=new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,request.machineId(),request.reviewAtUtc(),
                    RootJavaBootstrapInputs.Mode.QUOTE,null,actual.stream().map(row->new RootJavaBootstrapInputs.Item(row.kind(),row.original(),
                            inputs.resolve("copy-"+row.kind().name()+".json").toString())).toList());
            var consumed=RootJavaBootstrapInputs.prepare(generic,CLOCK);
            for(int i=0;i<3;i++)assertArrayEquals(prepared.files().get(i).bytes(),consumed.files().get(i).bytes());
            assertEquals(request.campaignDeadline(),CampaignDeadlineCodec.decodeConfiguration(Files.readAllBytes(Path.of(actual.get(2).original().path())),OrdinaryCampaignSchedule::calendar).founding());
            assertThrows(IOException.class,()->prepared.createNew(guard));
        }
    }
    @Test void independentCoaLimitsPublisherUsesTheSoleLimitsCodecAndActualPinnedRequest()throws IOException {
        Path inputs=Files.createDirectory(root.resolve("coa-inputs")),asset=Files.createDirectory(root.resolve("coa-output"));
        var request=new RootPlanningSettingsInputsProducer.CoaLimitsRequest(RootPlanningSettingsInputsProducer.COA_SCHEMA,
                WindowsJobProcess.currentMachineId(),NOW.minusSeconds(1).toString(),NOW.plusSeconds(3600).toString(),asset.toString(),new CoaVfs.Limits(1L<<30,1L<<29));
        FileRef raw=write(inputs.resolve("coa-request.json"),RootPlanningSettingsInputsProducer.encodeCoaRequest(request));
        var prepared=RootPlanningSettingsInputsProducer.prepareCoa(raw,CLOCK);
        assertEquals("COA_READ_LIMITS",prepared.quoteEnvelope().phase());
        try(var guard=RootBootstrapOutputGuard.readExact(binding(asset,prepared.quote()),CLOCK)){
            var actual=prepared.createNew(guard);assertEquals(1,actual.size());assertEquals(Kind.COA_READ_LIMITS,actual.getFirst().kind());
            assertEquals(request.limits(),CoaVfs.decodeLimits(new RawJson(Files.readAllBytes(Path.of(actual.getFirst().original().path())))));
            var generic=new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,request.machineId(),request.reviewAtUtc(),RootJavaBootstrapInputs.Mode.QUOTE,
                    null,List.of(new RootJavaBootstrapInputs.Item(Kind.COA_READ_LIMITS,actual.getFirst().original(),inputs.resolve("copy-coa.json").toString())));
            assertArrayEquals(prepared.files().getFirst().bytes(),RootJavaBootstrapInputs.prepare(generic,CLOCK).files().getFirst().bytes());
        }
        Files.writeString(Path.of(raw.path()),"changed request");assertThrows(IOException.class,prepared::quote);
    }
    @Test void strictIndependentCoreRequestsDoNotAcceptAggregateFieldsOrCoercedBounds()throws IOException {
        var calendar=OrdinaryCampaignSchedule.calendar("1066.9.15",360);
        var request=new RootPlanningSettingsInputsProducer.CoreRequest(RootPlanningSettingsInputsProducer.CORE_SCHEMA,
                WindowsJobProcess.currentMachineId(),NOW.minusSeconds(1).toString(),NOW.plusSeconds(3600).toString(),root.resolve("core").toString(),
                new RootPlanningSettingsInputsProducer.Life(true,true,true),new RootPlanningSettingsInputsProducer.Timings(4096,30000,300000),
                new CampaignDeadline.Founding("declared-clock",calendar.foundingDate(),calendar.foundingRaw(),360));
        var wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootPlanningSettingsInputsProducer.encodeCoreRequest(request));
        wire.putNull("native_domain_originals");byte[] unknown=StrictJson.canonical(wire);assertThrows(IOException.class,()->RootPlanningSettingsInputsProducer.decodeCoreRequest(unknown));
        wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootPlanningSettingsInputsProducer.encodeCoreRequest(request));
        ((com.fasterxml.jackson.databind.node.ObjectNode)wire.get("timings")).put("maximum_frames",true);
        byte[] wrong=StrictJson.canonical(wire);assertThrows(IOException.class,()->RootPlanningSettingsInputsProducer.decodeCoreRequest(wrong));
        wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootPlanningSettingsInputsProducer.encodeCoreRequest(request));
        ((com.fasterxml.jackson.databind.node.ObjectNode)wire.get("timings")).put("command_timeout_millis",30000.0);
        byte[] floating=StrictJson.canonical(wire);assertThrows(IOException.class,()->RootPlanningSettingsInputsProducer.decodeCoreRequest(floating));
    }
    private FileRef binding(Path asset,List<Output> outputs)throws IOException {
        Path control=Files.createDirectory(root.resolve("control"));String machine=WindowsJobProcess.currentMachineId(),observed=NOW.minusSeconds(1).toString(),review=NOW.plusSeconds(3600).toString();
        var declaration=new Declaration(DECLARATION,PURPOSE,machine,"/root","settings-software-fixture",observed,review,
                asset.toString(),SharedSourceFiles.nativeDirectory(asset),control.toString(),SharedSourceFiles.nativeDirectory(control),1536L*1024,512L*1024,1<<20,64,outputs,List.of(),List.of());
        FileRef declarationRef=write(control.resolve("declaration.json"),encode(declaration));
        FileRef census=write(control.resolve("census.json"),encode(RootBootstrapOutputGuard.observeAssetRoot(declarationRef,CLOCK)));
        var policy=StrictJson.object().put("policy_version","1.0.0");var rules=policy.putObject("capacity");
        rules.put("safety_floor_bytes",2L<<30);rules.put("safety_ceiling_bytes",20L<<30);rules.put("default_project_quota_ceiling_bytes",100L<<30);
        rules.put("safety_volume_fraction",new BigDecimal("0.05"));rules.put("default_project_quota_volume_fraction",new BigDecimal("0.10"));
        FileRef policyRef=write(control.resolve("policy.json"),StrictJson.canonical(policy));
        Path volume=asset.getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        var financial=StrictJson.object().put("scope","software-fixture-actual-volume-observation").put("machine_id",machine).put("total_bytes",total).put("usable_bytes",free);
        FileRef head=write(control.resolve("financial.json"),StrictJson.canonical(financial));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,null,Math.subtractExact(total,free),head);
        var release=new CapacityRelease(CAPACITY,PURPOSE,machine,"/root",ISSUER,"settings-software-fixture",NOW.toString(),review,
                policyRef,declarationRef,census,head,2L<<20,List.of(new Volume(volume.toString(),2L<<20,0,0,total,review,usage,List.of(),0)),List.of());
        FileRef capacity=write(control.resolve("capacity.json"),encode(release));
        return write(control.resolve("binding.json"),encode(new Binding(BINDING,PURPOSE,machine,"/root",ISSUER,"settings-software-fixture",NOW.toString(),review,declarationRef,census,capacity)));
    }
    private static FileRef write(Path path,byte[] bytes)throws IOException {Files.write(path,bytes);return FileRef.measure(path);}
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
}
