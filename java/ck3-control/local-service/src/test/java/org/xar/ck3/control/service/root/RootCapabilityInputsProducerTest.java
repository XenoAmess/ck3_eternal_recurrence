package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import java.io.IOException;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.parallel.Isolated;
import org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Real path custody, original request, existing Guard and existing capability decoders. All authority
 * cards are explicitly software fixtures; ACTIVE_NEW startup parameters grant no native/Driver binding. */
@Isolated("the real bootstrap CLI writes its one protocol frame to System.out")
class RootCapabilityInputsProducerTest {
    @TempDir Path root;
    private static final Instant NOW=Instant.parse("2026-10-26T01:00:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    private record Fixture(RootCapabilityInputsProducer.Request request,FileRef original,Path asset,Path driver) { }
    private Fixture fixture(boolean create)throws IOException {
        Path asset=Files.createDirectory(root.resolve("asset")),state=Files.createDirectory(root.resolve("state"));
        Path saves=Files.createDirectory(state.resolve("saves")),queue=Files.createDirectory(state.resolve("queue"));
        Path driver=state.resolve("driver.json");
        var configuration=new RootCapabilityInputsProducer.Configuration(state.toString(),saves.toString(),3,2,true,false);
        var session=new RootCapabilityInputsProducer.FreshSession(RootCapabilityInputsProducer.InitialBinding.FRESH_NEW_EPISODE,
                queue.toString(),driver.toString());
        var quote=new RootCapabilityInputsProducer.Request(RootCapabilityInputsProducer.SCHEMA,WindowsJobProcess.currentMachineId(),
                NOW.minusSeconds(1).toString(),NOW.plusSeconds(3600).toString(),RootJavaBootstrapInputs.Mode.QUOTE,null,asset.toString(),configuration,session);
        FileRef binding=create?binding(asset,RootCapabilityInputsProducer.encodeFiles(quote).stream().map(RootJavaBootstrapInputs.PreparedFile::output).toList()):null;
        var request=new RootCapabilityInputsProducer.Request(quote.schema(),quote.machineId(),quote.observedAtUtc(),quote.reviewAtUtc(),
                create?RootJavaBootstrapInputs.Mode.CREATE_NEW:RootJavaBootstrapInputs.Mode.QUOTE,binding,quote.outputRoot(),configuration,session);
        FileRef original=write(root.resolve("request.json"),RootCapabilityInputsProducer.encodeRequest(request));
        return new Fixture(request,original,asset,driver);
    }
    @Test void realOriginalProducerGuardAndAllExistingLeafConsumersReadIdenticalTwoOutputs()throws IOException {
        Fixture fixture=fixture(true);var prepared=RootCapabilityInputsProducer.prepare(fixture.original(),CLOCK);
        assertEquals(fixture.request(),RootCapabilityInputsProducer.decodeRequest(Files.readAllBytes(Path.of(fixture.original().path()))));
        assertEquals(List.of(Kind.CAPABILITY_CONFIGURATION,Kind.CAPABILITY_SESSION_PRESENTATION),prepared.quote().stream().map(Output::kind).toList());
        assertFalse(Files.exists(fixture.asset().resolve("capability-configuration.json")));assertFalse(Files.exists(fixture.driver()));
        var actual=prepared.createNew(CLOCK);assertEquals(2,actual.size());
        var configuration=DynamicCapabilities.decodeConfiguration(DriverJson.object(RootRuntimeDefinitions.read(actual.get(0).original(),1<<20),1<<20));
        var session=CapabilitySessionPresentation.decode(DriverJson.object(RootRuntimeDefinitions.read(actual.get(1).original(),1<<20),1<<20));
        assertEquals(fixture.request().configuration().value(),configuration);assertEquals(fixture.request().session().value(),session);
        for(var file:prepared.files())assertArrayEquals(file.bytes(),StrictJson.canonical(StrictJson.parse(file.bytes()),1<<20));
        session.validateConfiguration(configuration);assertEquals(CapabilitySessionPresentation.BindingState.ACTIVE_NEW,session.bindingState());
        assertFalse(session.driverStateRestored());assertFalse(Files.exists(fixture.driver()));
        var generic=new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,fixture.request().machineId(),fixture.request().reviewAtUtc(),
                RootJavaBootstrapInputs.Mode.QUOTE,null,actual.stream().map(row->new RootJavaBootstrapInputs.Item(row.kind(),row.original(),
                        root.resolve("copy-"+row.kind().name()+".json").toString())).toList());
        var consumed=RootJavaBootstrapInputs.prepare(generic,CLOCK);
        for(int i=0;i<2;i++)assertArrayEquals(prepared.files().get(i).bytes(),consumed.files().get(i).bytes());
        assertThrows(IOException.class,()->prepared.createNew(CLOCK));
    }
    @Test void strictRequestRejectsMissingNullableUnknownBooleanIntegerAndFloatingInteger()throws IOException {
        Fixture fixture=fixture(false);byte[] raw=Files.readAllBytes(Path.of(fixture.original().path()));
        var node=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(raw);node.remove("binding_ref");
        byte[] missing=StrictJson.canonical(node);assertThrows(IOException.class,()->RootCapabilityInputsProducer.decodeRequest(missing));
        node=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(raw);node.put("pretend_loaded",true);
        byte[] extra=StrictJson.canonical(node);assertThrows(IOException.class,()->RootCapabilityInputsProducer.decodeRequest(extra));
        node=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(raw);
        ((com.fasterxml.jackson.databind.node.ObjectNode)node.get("configuration")).put("route_contact_timeline_speed",true);
        byte[] bool=StrictJson.canonical(node);assertThrows(IOException.class,()->RootCapabilityInputsProducer.decodeRequest(bool));
        node=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(raw);
        ((com.fasterxml.jackson.databind.node.ObjectNode)node.get("configuration")).put("route_contact_effective_timeline_speed",2.0);
        byte[] floating=StrictJson.canonical(node);assertThrows(IOException.class,()->RootCapabilityInputsProducer.decodeRequest(floating));
        node=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(raw);
        ((com.fasterxml.jackson.databind.node.ObjectNode)node.get("session")).put("initial_binding","ACTIVE_RESUMED");
        byte[] wrongBinding=StrictJson.canonical(node);assertThrows(IOException.class,()->RootCapabilityInputsProducer.decodeRequest(wrongBinding));
    }
    @Test void actualDriverStateAppearanceRefusesFreshBeforeAnyOutput()throws IOException {
        Fixture fixture=fixture(false);var prepared=RootCapabilityInputsProducer.prepare(fixture.original(),CLOCK);
        Files.writeString(fixture.driver(),"real existing state fixture");
        assertThrows(IOException.class,prepared::quote);assertThrows(IOException.class,()->RootCapabilityInputsProducer.prepare(fixture.original(),CLOCK));
        try(var entries=Files.list(fixture.asset())){assertEquals(0,entries.count());}
    }
    @Test void replacedActualDirectoryAndChangedPinnedRequestRefuseCustody()throws IOException {
        Fixture fixture=fixture(false);var prepared=RootCapabilityInputsProducer.prepare(fixture.original(),CLOCK);
        Path queue=Path.of(fixture.request().session().queueDirectory());Files.move(queue,queue.resolveSibling("old-queue"));Files.createDirectory(queue);
        assertThrows(IOException.class,prepared::quote);
        Files.writeString(Path.of(fixture.original().path()),"{}");
        assertThrows(IOException.class,()->RootCapabilityInputsProducer.prepare(fixture.original(),CLOCK));
        try(var entries=Files.list(fixture.asset())){assertEquals(0,entries.count());}
    }
    @Test void quoteCannotWriteAndForeignExpiredOrFutureRequestsCannotPrepare()throws IOException {
        Fixture fixture=fixture(false);var prepared=RootCapabilityInputsProducer.prepare(fixture.original(),CLOCK);
        assertThrows(IOException.class,()->prepared.createNew(CLOCK));
        assertThrows(IOException.class,()->RootCapabilityInputsProducer.prepare(fixture.original(),Clock.fixed(NOW.plusSeconds(3600),ZoneOffset.UTC)));
        assertThrows(IOException.class,()->RootCapabilityInputsProducer.prepare(fixture.original(),Clock.fixed(NOW.minusSeconds(2),ZoneOffset.UTC)));
        var request=fixture.request();var foreign=new RootCapabilityInputsProducer.Request(request.schema(),"a-different-machine",request.observedAtUtc(),request.reviewAtUtc(),
                request.mode(),request.bindingRef(),request.outputRoot(),request.configuration(),request.session());
        assertThrows(IOException.class,()->RootCapabilityInputsProducer.prepare(foreign,CLOCK));
        try(var entries=Files.list(fixture.asset())){assertEquals(0,entries.count());}
    }
    @Test void actualCapabilityRequestThroughOriginalCliProducesIssuerProtocolQuote()throws Exception {
        Fixture fixture=fixture(false);var selected=fixture.request();Instant now=Clock.systemUTC().instant();
        var request=new RootCapabilityInputsProducer.Request(selected.schema(),selected.machineId(),now.minusSeconds(1).toString(),
                now.plusSeconds(300).toString(),RootJavaBootstrapInputs.Mode.QUOTE,null,selected.outputRoot(),selected.configuration(),selected.session());
        FileRef original=write(root.resolve("cli-request.json"),RootCapabilityInputsProducer.encodeRequest(request));
        var stdout=new ByteArrayOutputStream();PrintStream prior=System.out;
        try(var capture=new PrintStream(stdout,true,StandardCharsets.UTF_8)){
            System.setOut(capture);
            try{RootJavaBootstrapInputs.main(new String[]{original.path(),Long.toString(original.bytes()),original.sha256()});}
            finally{System.setOut(prior);}
        }
        var quote=RootBootstrapProtocol.line(stdout.toByteArray(),RootBootstrapProtocol.Quote.class);
        assertInstanceOf(RootBootstrapProtocol.OrdinaryQuote.class,quote);
        assertEquals("xar.java-root-bootstrap-phase-quote/v1",quote.schema());
        assertEquals("CAPABILITY_INITIAL_CONFIGURATION",quote.phase());assertEquals(selected.machineId(),quote.machineId());
        assertEquals(request.reviewAtUtc(),quote.reviewAtUtc());assertEquals(selected.outputRoot(),quote.assetRoot());
        assertEquals("AWAITING_REAL_INDEPENDENT_ISSUER_BINDING",quote.authority());
        assertEquals(List.of(),quote.outputDirectories());assertEquals(List.of(),quote.retainedInputs());
        assertEquals(RootCapabilityInputsProducer.prepare(original,Clock.systemUTC()).quote(),quote.outputs());
        try(var entries=Files.list(fixture.asset())){assertEquals(0,entries.count());}
        assertFalse(Files.exists(fixture.driver()));
    }
    private FileRef binding(Path asset,List<Output> outputs)throws IOException {
        Path control=Files.createDirectory(root.resolve("control"));String machine=WindowsJobProcess.currentMachineId(),observed=NOW.minusSeconds(1).toString(),review=NOW.plusSeconds(3600).toString();
        var declaration=new Declaration(DECLARATION,PURPOSE,machine,"/root","capability-software-fixture",observed,review,
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
        var release=new CapacityRelease(CAPACITY,PURPOSE,machine,"/root",ISSUER,"capability-software-fixture",NOW.toString(),review,
                policyRef,declarationRef,census,head,2L<<20,List.of(new Volume(volume.toString(),2L<<20,0,0,total,review,usage,List.of(),0)),List.of());
        FileRef capacity=write(control.resolve("capacity.json"),encode(release));
        return write(control.resolve("binding.json"),encode(new Binding(BINDING,PURPOSE,machine,"/root",ISSUER,"capability-software-fixture",NOW.toString(),review,declarationRef,census,capacity)));
    }
    private static FileRef write(Path path,byte[] bytes)throws IOException {Files.write(path,bytes);return FileRef.measure(path);}
}
