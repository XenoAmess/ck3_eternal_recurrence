package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.parallel.ResourceLock;
import org.junit.jupiter.api.parallel.Resources;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Real immutable filesystem/Bootstrap guard/App reader software chain. Temporary issuer cards are test inputs,
 * never production financial authority, a Core, complete Operator qualification, a Native lease, or a Game.
 */
@ResourceLock(Resources.SYSTEM_OUT)
final class RootApplicationConfigurationProducerTest {
    @TempDir Path temporary;
    private static final Instant NOW=Instant.parse("2026-10-24T09:50:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    private record Fixture(Path root,Path asset,Path control,Path target,RootApplicationConfiguration configuration) { }

    @Test void actualFieldsSoleCodecQuoteConcreteGuardAndPublishedReaderPreserveTwentySourceOriginals()throws IOException {
        Fixture fixture=fixture("published");var actual=fixture.configuration();
        var prepared=RootApplicationConfigurationProducer.prepare(actual,fixture.target(),CLOCK);
        byte[] encoded=StrictJson.canonical(actual.toJson(),RootApplicationConfiguration.MAXIMUM_BYTES);
        assertArrayEquals(encoded,prepared.bytes());assertEquals(actual,prepared.configuration());
        assertEquals(Kind.APPLICATION,prepared.quote().kind());assertEquals(20,actual.writerSources().size());
        byte[] detached=prepared.bytes();detached[0]^=1;assertArrayEquals(encoded,prepared.bytes());
        assertFalse(Files.exists(fixture.target()));
        var published=prepared.createNew(binding(fixture,prepared.quote()));
        assertEquals(prepared.expected(),published.original());assertEquals(encoded.length,published.original().bytes());
        assertArrayEquals(encoded,Files.readAllBytes(fixture.target()));assertEquals(actual,published.readExact(CLOCK));
        assertEquals(actual,RootApplicationConfiguration.readExact(published.original()));
        assertEquals(actual.writerSources(),published.readExact(CLOCK).writerSources());
        assertEquals(SharedSourceFiles.nativeFile(fixture.target()),published.nativeFile());
        assertFalse(Files.exists(actual.ledger().snapshot()),"configuration production cannot create the canonical ledger");
        assertFalse(Files.exists(actual.artifactRoot()),"configuration publication grants no archive/Core creation");
        assertThrows(IOException.class,()->prepared.createNew(bindingReference(fixture)));
        assertArrayEquals(encoded,Files.readAllBytes(fixture.target()));
    }

    @Test void absentActualOriginalsRelativeOutputAndMutableLedgerTargetsFailBeforePublication()throws IOException {
        Fixture fixture=fixture("missing");var actual=fixture.configuration();
        assertThrows(RootApplicationConfigurationProducer.Missing.class,()->RootApplicationConfigurationProducer.prepare(null,fixture.target(),CLOCK));
        assertThrows(RootApplicationConfigurationProducer.Missing.class,()->RootApplicationConfigurationProducer.prepare(actual,Path.of("application.json"),CLOCK));
        for(Path target:List.of(actual.ledger().snapshot(),actual.ledger().lock(),actual.ledger().events().resolve("00000001.json"),
                Path.of(actual.ledger().anchor().path()),Path.of(actual.nativeLaunchPlan().path()),Path.of(actual.writerSources().getFirst().path())))
            assertThrows(IOException.class,()->RootApplicationConfigurationProducer.prepare(actual,target,CLOCK));
        Files.delete(Path.of(actual.nativeLaunchPlan().path()));
        assertThrows(IOException.class,()->RootApplicationConfigurationProducer.prepare(actual,fixture.target(),CLOCK));
        assertFalse(Files.exists(fixture.target()));
    }

    @Test void historicalMachineReviewRemainDataWhileStrictAppFieldsRejectWrongShape()throws IOException {
        Fixture fixture=fixture("types");var actual=fixture.configuration();
        var expired=new RootApplicationConfiguration(actual.machineId(),actual.mode(),NOW.minusSeconds(1),actual.nativeLaunchPlan(),
                actual.ledger(),actual.writerSources(),actual.artifactRoot(),actual.maximumArtifactBytes());
        assertEquals(expired,RootApplicationConfigurationProducer.prepare(expired,fixture.target(),CLOCK).configuration());
        String foreign="foreign-software-machine";
        var other=new RootApplicationConfiguration(foreign,actual.mode(),actual.reviewAt(),actual.nativeLaunchPlan(),
                new WriterContracts.Layout(actual.ledger().snapshot(),actual.ledger().anchor(),foreign),actual.writerSources(),actual.artifactRoot(),actual.maximumArtifactBytes());
        assertEquals(other,RootApplicationConfigurationProducer.prepare(other,fixture.target(),CLOCK).configuration());
        assertThrows(IllegalArgumentException.class,()->new RootApplicationConfiguration(actual.machineId(),actual.mode(),actual.reviewAt(),actual.nativeLaunchPlan(),
                actual.ledger(),List.of(),actual.artifactRoot(),actual.maximumArtifactBytes()));
        for(int mode=0;mode<4;mode++) {
            ObjectNode json=actual.toJson();
            switch(mode) {case 0->json.remove("maximum_artifact_bytes");case 1->json.putNull("maximum_artifact_bytes");
                case 2->json.put("maximum_artifact_bytes",true);case 3->json.put("maximum_artifact_bytes",1.0);default->throw new AssertionError();}
            assertThrows(IllegalArgumentException.class,()->RootApplicationConfiguration.fromJson(json));
        }
        ObjectNode sources=actual.toJson();sources.putArray("writer_sources");
        assertThrows(IllegalArgumentException.class,()->RootApplicationConfiguration.fromJson(sources));
        assertFalse(Files.exists(fixture.target()));
    }

    @Test void equalBytesAndTimestampsCannotReplaceAPreparedWriterSourceNativeIdentity()throws IOException {
        Fixture fixture=fixture("source-identity");var actual=fixture.configuration();
        var prepared=RootApplicationConfigurationProducer.prepare(actual,fixture.target(),CLOCK);
        Path source=Path.of(actual.writerSources().getFirst().path());replaceEqualBytes(source);
        actual.requireCurrent(CLOCK); // Exact bytes/SHA alone still agree; the producer also retained physical identity.
        assertThrows(IOException.class,prepared::requireCurrent);assertThrows(IOException.class,prepared::quote);
        assertFalse(Files.exists(fixture.target()));
    }

    @Test void absentOrWrongOutputRolePermitNeverCreatesApplicationBytes()throws IOException {
        Fixture fixture=fixture("permit");var prepared=RootApplicationConfigurationProducer.prepare(fixture.configuration(),fixture.target(),CLOCK);
        assertThrows(RootApplicationConfigurationProducer.Missing.class,()->prepared.createNew(null));
        var quote=prepared.quote();var wrong=new Output(Kind.MCP_ADMISSION,quote.fileName(),quote.bytes(),quote.sha256());
        FileRef authority=binding(fixture,wrong);
        assertThrows(IOException.class,()->prepared.createNew(authority));assertFalse(Files.exists(fixture.target()));
    }

    @Test void actualCreateThenExpiredReturnRetainsBytesAndCannotRetryTheUnknownPublication()throws IOException {
        Fixture fixture=fixture("unknown");
        Clock expiresAfterCreate=new Clock() {
            public ZoneId getZone(){return ZoneOffset.UTC;}
            public Clock withZone(ZoneId zone){return this;}
            public Instant instant(){return Files.exists(fixture.target())?NOW.plusSeconds(7200):NOW;}
        };
        var prepared=RootApplicationConfigurationProducer.prepare(fixture.configuration(),fixture.target(),expiresAfterCreate);
        FileRef authority=binding(fixture,prepared.quote());byte[] expected=prepared.bytes();
        assertThrows(IOException.class,()->prepared.createNew(authority));
        assertTrue(Files.isRegularFile(fixture.target()),"the actual guard wrote before the returned qualification expired");
        assertArrayEquals(expected,Files.readAllBytes(fixture.target()));var nativeOriginal=SharedSourceFiles.nativeFile(fixture.target());
        assertThrows(RootApplicationConfigurationProducer.Missing.class,()->prepared.createNew(authority));
        assertEquals(nativeOriginal,SharedSourceFiles.nativeFile(fixture.target()));
        assertThrows(IOException.class,()->RootApplicationConfigurationProducer.prepare(fixture.configuration(),fixture.target(),CLOCK));
    }

    @Test void publishedSameContentReplacementCannotBorrowTheOriginalPublicationCustody()throws IOException {
        Fixture fixture=fixture("output-identity");var prepared=RootApplicationConfigurationProducer.prepare(fixture.configuration(),fixture.target(),CLOCK);
        var published=prepared.createNew(binding(fixture,prepared.quote()));replaceEqualBytes(fixture.target());
        assertEquals(fixture.configuration(),RootApplicationConfiguration.readExact(FileRef.measure(fixture.target())));
        assertThrows(IOException.class,()->published.readExact(CLOCK));
    }

    @Test void publishedConsumerAlsoRetainsTheActualWriterSourcePhysicalOriginals()throws IOException {
        Fixture fixture=fixture("published-source-identity");
        var prepared=RootApplicationConfigurationProducer.prepare(fixture.configuration(),fixture.target(),CLOCK);
        var published=prepared.createNew(binding(fixture,prepared.quote()));
        replaceEqualBytes(Path.of(fixture.configuration().writerSources().getFirst().path()));
        fixture.configuration().requireCurrent(CLOCK);
        assertEquals(fixture.configuration(),RootApplicationConfiguration.readExact(published.original()));
        assertThrows(IOException.class,()->published.readExact(CLOCK));
    }

    @Test void firstApplicationCommandLineUsesExplicitFieldsWithoutAnExistingApplicationFile()throws IOException {
        Fixture fixture=fixture("first-cli",WriterContracts.MAXIMUM_CONFIGURED_SOURCES);String[] quote=arguments(fixture,"QUOTE",null);
        var invocation=RootApplicationConfigurationProducer.arguments(quote);
        assertEquals(fixture.configuration(),invocation.actual());assertEquals(fixture.target(),invocation.target());assertNull(invocation.binding());
        var prepared=RootApplicationConfigurationProducer.prepare(invocation.actual(),invocation.target(),CLOCK);
        assertArrayEquals(StrictJson.canonical(fixture.configuration().toJson(),RootApplicationConfiguration.MAXIMUM_BYTES),prepared.bytes());
        var quoted=RootBootstrapProtocol.decode(RootApplicationConfigurationProducer.execute(quote,CLOCK),
                RootBootstrapProtocol.FRAME_BYTES-1,RootBootstrapProtocol.Quote.class);
        assertApplicationQuote(quoted,fixture,prepared.quote());assertFalse(Files.exists(fixture.target()));
        FileRef binding=binding(fixture,quoted.outputs().getFirst());
        var create=RootApplicationConfigurationProducer.arguments(arguments(fixture,"CREATE_NEW",binding));
        assertEquals(fixture.configuration(),create.actual());assertEquals(binding,create.binding());assertFalse(Files.exists(fixture.target()));
        var result=StrictJson.parse(RootApplicationConfigurationProducer.execute(arguments(fixture,"CREATE_NEW",binding),CLOCK));
        assertEquals("CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION",result.path("status").textValue());
        FileRef published=ControlBuild.strictMapper().treeToValue(result.get("original"),FileRef.class);
        assertEquals(fixture.configuration(),RootApplicationConfiguration.readExact(published));
        assertEquals(WriterContracts.MAXIMUM_CONFIGURED_SOURCES,RootApplicationConfiguration.readExact(published).writerSources().size());
        String[] missing=quote.clone();missing[0]="CREATE_NEW";
        assertThrows(IllegalArgumentException.class,()->RootApplicationConfigurationProducer.arguments(missing));
        for(String invalid:List.of("0","true","1.0",Integer.toString(WriterContracts.MAXIMUM_CONFIGURED_SOURCES+1),"2147483648")) {
            String[] count=quote.clone();count[14]=invalid;
            assertThrows(IllegalArgumentException.class,()->RootApplicationConfigurationProducer.arguments(count));
        }
        String[] relative=quote.clone();relative[7]="snapshot.json";
        assertThrows(IllegalArgumentException.class,()->RootApplicationConfigurationProducer.arguments(relative));
        String[] unsafe=quote.clone();unsafe[12]="1.0";
        assertThrows(IllegalArgumentException.class,()->RootApplicationConfigurationProducer.arguments(unsafe));
    }

    @Test void firstJsonRequestReusesTheActualProducerGuardAndSoleApplicationReader()throws IOException {
        Fixture fixture=fixture("json-request");
        var quote=new RootApplicationConfigurationProducer.Request(RootApplicationConfigurationProducer.Mode.QUOTE,
                fixture.configuration(),fixture.target(),null);
        byte[] quoteBytes=RootApplicationConfigurationProducer.encodeRequest(quote);
        assertEquals(quote,RootApplicationConfigurationProducer.decodeRequest(quoteBytes));
        assertArrayEquals(quoteBytes,RootApplicationConfigurationProducer.encodeRequest(
                RootApplicationConfigurationProducer.decodeRequest(quoteBytes)));
        var quoted=RootBootstrapProtocol.decode(RootApplicationConfigurationProducer.execute(
                RootApplicationConfigurationProducer.decodeRequest(quoteBytes),CLOCK),
                RootBootstrapProtocol.FRAME_BYTES-1,RootBootstrapProtocol.Quote.class);
        var prepared=RootApplicationConfigurationProducer.prepare(fixture.configuration(),fixture.target(),CLOCK);
        assertApplicationQuote(quoted,fixture,prepared.quote());assertFalse(Files.exists(fixture.target()));
        FileRef guard=binding(fixture,quoted.outputs().getFirst());
        var create=new RootApplicationConfigurationProducer.Request(RootApplicationConfigurationProducer.Mode.CREATE_NEW,
                fixture.configuration(),fixture.target(),guard);
        var result=StrictJson.parse(RootApplicationConfigurationProducer.execute(
                RootApplicationConfigurationProducer.decodeRequest(RootApplicationConfigurationProducer.encodeRequest(create)),CLOCK));
        assertEquals("CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION",result.path("status").textValue());
        FileRef original=ControlBuild.strictMapper().treeToValue(result.get("original"),FileRef.class);
        assertEquals(prepared.expected(),original);
        assertEquals(fixture.configuration(),RootApplicationConfiguration.readExact(original));
        assertFalse(Files.exists(fixture.configuration().ledger().snapshot()));
    }

    @Test void jsonRequestKeepsExactFieldsAndTheOriginalApplicationNumericContract()throws IOException {
        Fixture fixture=fixture("json-request-contract");
        var request=new RootApplicationConfigurationProducer.Request(RootApplicationConfigurationProducer.Mode.QUOTE,
                fixture.configuration(),fixture.target(),null);
        byte[] original=RootApplicationConfigurationProducer.encodeRequest(request);
        var missing=(ObjectNode)StrictJson.parse(original);missing.remove("binding_ref");
        assertThrows(IllegalArgumentException.class,()->RootApplicationConfigurationProducer.decodeRequest(StrictJson.canonical(missing)));
        var extra=(ObjectNode)StrictJson.parse(original);extra.put("application_file","no-existing-original-required");
        assertThrows(IllegalArgumentException.class,()->RootApplicationConfigurationProducer.decodeRequest(StrictJson.canonical(extra)));
        for(String value:List.of("true","1.0","null")) {
            var invalid=(ObjectNode)StrictJson.parse(original);
            ((ObjectNode)invalid.get("actual")).set("maximum_artifact_bytes",StrictJson.parse(value.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->RootApplicationConfigurationProducer.decodeRequest(ControlBuild.strictMapper().writeValueAsBytes(invalid)));
        }
        var create=(ObjectNode)StrictJson.parse(original);create.put("mode","CREATE_NEW");
        assertThrows(IllegalArgumentException.class,()->RootApplicationConfigurationProducer.decodeRequest(StrictJson.canonical(create)));
        assertFalse(Files.exists(fixture.target()));
    }

    @Test void actualSharedBootstrapMainPublishesTheFirstApplicationThroughItsRequestSchema()throws Exception {
        Fixture base=fixture("shared-bootstrap-main",65);Clock live=Clock.systemUTC();Instant observed=live.instant();
        var old=base.configuration();
        var actual=new RootApplicationConfiguration(old.machineId(),old.mode(),observed.plusSeconds(3600),
                old.nativeLaunchPlan(),old.ledger(),old.writerSources(),old.artifactRoot(),old.maximumArtifactBytes());
        var fixture=new Fixture(base.root(),base.asset(),base.control(),base.target(),actual);
        var quote=new RootApplicationConfigurationProducer.Request(RootApplicationConfigurationProducer.Mode.QUOTE,actual,fixture.target(),null);
        FileRef quoteRequest=write(fixture.root().resolve("quote-request.json"),RootApplicationConfigurationProducer.encodeRequest(quote));
        var quoted=RootBootstrapProtocol.line(invokeBootstrap(quoteRequest),RootBootstrapProtocol.Quote.class);
        var prepared=RootApplicationConfigurationProducer.prepare(actual,fixture.target(),live);
        assertApplicationQuote(quoted,fixture,prepared.quote());assertFalse(Files.exists(fixture.target()));
        FileRef binding=binding(fixture,quoted.outputs().getFirst(),observed);
        var create=new RootApplicationConfigurationProducer.Request(RootApplicationConfigurationProducer.Mode.CREATE_NEW,actual,fixture.target(),binding);
        FileRef createRequest=write(fixture.root().resolve("create-request.json"),RootApplicationConfigurationProducer.encodeRequest(create));
        var result=StrictJson.parse(invokeBootstrap(createRequest));
        assertEquals("CREATED_READBACK_VERIFIED_NOT_RUNTIME_ADMISSION",result.path("status").textValue());
        FileRef original=ControlBuild.strictMapper().treeToValue(result.get("original"),FileRef.class);
        assertEquals(prepared.expected(),original);assertEquals(actual,RootApplicationConfiguration.readExact(original));
        assertEquals(65,RootApplicationConfiguration.readExact(original).writerSources().size());
        quoteRequest.verify();createRequest.verify();
        assertFalse(Files.exists(actual.ledger().snapshot()));
    }

    private static byte[] invokeBootstrap(FileRef request)throws Exception {
        var bytes=new ByteArrayOutputStream();PrintStream original=System.out;
        try(var output=new PrintStream(bytes,true,StandardCharsets.UTF_8)) {
            System.setOut(output);RootJavaBootstrapInputs.main(new String[]{request.path(),Long.toString(request.bytes()),request.sha256()});
        }finally{System.setOut(original);}
        return bytes.toByteArray();
    }

    private static void assertApplicationQuote(RootBootstrapProtocol.Quote quote,Fixture fixture,Output expected) {
        assertInstanceOf(RootBootstrapProtocol.OrdinaryQuote.class,quote);
        assertEquals("xar.java-root-bootstrap-phase-quote/v1",quote.schema());assertEquals("APPLICATION",quote.phase());
        assertEquals(fixture.configuration().machineId(),quote.machineId());assertEquals(fixture.configuration().reviewAt().toString(),quote.reviewAtUtc());
        assertEquals(fixture.asset().toString(),quote.assetRoot());assertEquals(List.of(expected),quote.outputs());
        assertEquals(List.of(),quote.outputDirectories());assertEquals(List.of(),quote.retainedInputs());
        assertEquals("AWAITING_REAL_INDEPENDENT_ISSUER_BINDING",quote.authority());
    }

    private Fixture fixture(String name)throws IOException {
        return fixture(name,20);
    }
    private Fixture fixture(String name,int sourceCount)throws IOException {
        Path root=Files.createDirectory(temporary.resolve(name)),input=Files.createDirectory(root.resolve("inputs"));
        Path asset=Files.createDirectory(root.resolve("assets")),control=Files.createDirectory(root.resolve("control"));
        String machine=WindowsJobProcess.currentMachineId();
        ExactRef plan=exact(write(input.resolve("native-plan.json"),"{\"software_original\":\"native-plan\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        ExactRef anchor=exact(write(input.resolve("ledger-anchor.json"),"{\"software_original\":\"anchor\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        var sources=new ArrayList<ExactRef>();
        for(int index=0;index<sourceCount;index++)sources.add(exact(write(input.resolve("operator-source-"+index+".txt"),("actual software original "+index).getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        var config=new RootApplicationConfiguration(machine,HostMode.MCP_STDIO,NOW.plusSeconds(3600),plan,
                new WriterContracts.Layout(root.resolve("ledger/snapshot.json"),anchor,machine),sources,root.resolve("immutable-archive"),64L<<20);
        return new Fixture(root,asset,control,asset.resolve("application.json"),config);
    }

    /** One real finite guard for one temporary APPLICATION file. This is software capacity, never a production permit. */
    private FileRef binding(Fixture fixture,Output output)throws IOException {
        return binding(fixture,output,NOW);
    }
    private FileRef binding(Fixture fixture,Output output,Instant observed)throws IOException {
        Clock clock=Clock.fixed(observed,ZoneOffset.UTC);
        String machine=WindowsJobProcess.currentMachineId(),review=observed.plusSeconds(3600).toString();
        var declaration=new Declaration(DECLARATION,PURPOSE,machine,"/root","application-software-fixture",observed.minusSeconds(1).toString(),review,
                fixture.asset().toString(),SharedSourceFiles.nativeDirectory(fixture.asset()),fixture.control().toString(),SharedSourceFiles.nativeDirectory(fixture.control()),
                1536L*1024,512L*1024,1<<20,64,List.of(output),List.of(),List.of());
        FileRef declarationRef=write(fixture.control().resolve("declaration.json"),encode(declaration));
        FileRef census=write(fixture.control().resolve("census.json"),encode(RootBootstrapOutputGuard.observeAssetRoot(declarationRef,clock)));
        ObjectNode policy=StrictJson.object().put("policy_version","1.0.0");var rules=policy.putObject("capacity");
        rules.put("safety_floor_bytes",2L<<30).put("safety_ceiling_bytes",20L<<30).put("default_project_quota_ceiling_bytes",100L<<30)
                .put("safety_volume_fraction",new java.math.BigDecimal("0.05")).put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(fixture.control().resolve("policy.json"),ControlBuild.strictMapper().writeValueAsBytes(policy));
        Path volume=fixture.asset().getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        ObjectNode financial=StrictJson.object().put("scope","temporary-software-actual-volume-only").put("machine_id",machine)
                .put("total_bytes",total).put("usable_bytes",free).put("old_workpackage_actual_is_unknown",true);
        FileRef head=write(fixture.control().resolve("financial.json"),StrictJson.canonical(financial));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,
                null,Math.subtractExact(total,free),head);
        var capacity=new CapacityRelease(CAPACITY,PURPOSE,machine,"/root",ISSUER,"application-software-fixture",observed.toString(),review,
                policyRef,declarationRef,census,head,2L<<20,List.of(new Volume(volume.toString(),2L<<20,0,0,total,review,usage,List.of(),0)),List.of());
        FileRef release=write(fixture.control().resolve("capacity.json"),encode(capacity));
        return write(fixture.control().resolve("binding.json"),encode(new Binding(BINDING,PURPOSE,machine,"/root",ISSUER,
                "application-software-fixture",observed.toString(),review,declarationRef,census,release)));
    }
    private static FileRef bindingReference(Fixture fixture)throws IOException {return FileRef.measure(fixture.control().resolve("binding.json"));}
    private static String[] arguments(Fixture fixture,String mode,FileRef binding) {
        var config=fixture.configuration();var values=new ArrayList<String>();
        values.add(mode);values.add(config.machineId());values.add(config.mode().name());values.add(config.reviewAt().toString());
        triplet(values,config.nativeLaunchPlan());values.add(config.ledger().snapshot().toString());triplet(values,config.ledger().anchor());
        values.add(config.artifactRoot().toString());values.add(Long.toString(config.maximumArtifactBytes()));values.add(fixture.target().toString());
        values.add(Integer.toString(config.writerSources().size()));for(ExactRef source:config.writerSources())triplet(values,source);
        if(binding!=null)triplet(values,exact(binding));return values.toArray(String[]::new);
    }
    private static void triplet(ArrayList<String> values,ExactRef ref){values.add(ref.path());values.add(Long.toString(ref.bytes()));values.add(ref.sha256());}
    private static FileRef write(Path path,byte[] bytes)throws IOException {Files.write(path,bytes);return FileRef.measure(path);}
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static void replaceEqualBytes(Path original)throws IOException {
        Path replacement=original.resolveSibling(original.getFileName()+".replacement");Files.copy(original,replacement);
        Files.setLastModifiedTime(replacement,Files.getLastModifiedTime(original));Files.move(replacement,original,StandardCopyOption.REPLACE_EXISTING);
    }
}
