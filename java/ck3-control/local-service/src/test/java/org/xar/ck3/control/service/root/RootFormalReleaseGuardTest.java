package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.TreeSet;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeRunProfileManifest.ReleaseEntry;
import org.xar.ck3.control.build.NativeRunProfileManifest.ReleaseManifest;
import org.xar.ck3.control.build.NativeRunProfileProducer;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Software issuer cards price real temporary files through the one Guard. No Game or publication authority. */
@org.junit.jupiter.api.parallel.Isolated("Original phase uses its actual System.in/out protocol")
class RootFormalReleaseGuardTest {
    @TempDir Path root;
    private static final Instant NOW=Instant.parse("2026-10-25T16:00:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    private static final String TREE="xar-production",MANIFEST=TREE+".manifest.json";
    private record Payload(LinkedHashMap<String,byte[]> bodies,List<Output> outputs,List<String> directories,ReleaseManifest manifest) { }
    private record Fixture(Declaration declaration,FileRef binding,FileRef capacity,Payload payload) {
        Path asset(){return Path.of(declaration.assetRoot());}
        Path control(){return Path.of(declaration.controlRoot());}
        RootBootstrapOutputGuard open()throws IOException{return RootBootstrapOutputGuard.readExact(binding,CLOCK);}
    }
    private static Payload payload()throws IOException {
        var bodies=new LinkedHashMap<String,byte[]>();
        bodies.put(TREE+"/descriptor.mod","version=\"1.0.2\"\nsupported_version=\"1.20.0.3\"\n".getBytes(StandardCharsets.UTF_8));
        // Exercise the new branch's real single-write limit, together with >64 files and >3 directories.
        bodies.put(TREE+"/thumbnail.png",new byte[(1<<20)+1]);
        for(int index=0;index<70;index++)bodies.put(TREE+"/common/group"+(index%30)+"/file"+index+".txt",("# fixture "+index+"\n").repeat(700).getBytes(StandardCharsets.UTF_8));
        var entries=new ArrayList<ReleaseEntry>();var directories=new TreeSet<String>();directories.add(TREE);
        for(String directory:List.of("common","events","gfx","gui","localization"))directories.add(TREE+"/"+directory);
        for(var body:bodies.entrySet()){
            entries.add(new ReleaseEntry(body.getKey().substring(TREE.length()+1),body.getValue().length,DriverJson.sha256(body.getValue())));
            Path parent=Path.of(body.getKey()).getParent();while(parent!=null){directories.add(parent.toString().replace('\\','/'));parent=parent.getParent();}
        }
        entries.sort(java.util.Comparator.comparing(ReleaseEntry::path));
        var manifest=new ReleaseManifest(2,"1.0.2",null,"1".repeat(40),"3784706360",entries);
        bodies.put(MANIFEST,ControlBuild.strictMapper().writeValueAsBytes(manifest));
        var outputs=new ArrayList<Output>();for(var body:bodies.entrySet())outputs.add(new Output(body.getKey().equals(MANIFEST)?Kind.FORMAL_RELEASE_MANIFEST:Kind.FORMAL_RELEASE_PAYLOAD,
                body.getKey(),body.getValue().length,DriverJson.sha256(body.getValue())));
        return new Payload(bodies,List.copyOf(outputs),List.copyOf(directories),manifest);
    }
    private Fixture fixture(Payload payload)throws IOException {
        Path asset=Files.createDirectory(root.resolve("asset")),control=Files.createDirectory(root.resolve("control"));
        return fixture(asset,control,payload);
    }
    private Fixture fixture(Path asset,Path control,Payload payload)throws IOException {
        if(!asset.getRoot().equals(control.getRoot()))throw new IOException("test card requires explicit temporary roots on one data volume");
        String machine=WindowsJobProcess.currentMachineId(),observed=NOW.minusSeconds(1).toString(),review=NOW.plusSeconds(3600).toString();
        long assets=8L<<20,controls=512L<<10,joint=Math.addExact(assets,controls);
        var declaration=new Declaration(FORMAL_DECLARATION,FORMAL_PURPOSE,machine,"/root","formal-fixture",observed,review,
                asset.toString(),SharedSourceFiles.nativeDirectory(asset),control.toString(),SharedSourceFiles.nativeDirectory(control),
                assets,controls,FORMAL_MAXIMUM_SINGLE_BYTES,payload.outputs().size()+payload.directories().size(),payload.outputs(),payload.directories(),List.of());
        FileRef declared=write(control.resolve("declaration.json"),encode(declaration));
        FileRef census=write(control.resolve("census.json"),encode(RootBootstrapOutputGuard.observeAssetRoot(declared,CLOCK)));
        var policy=StrictJson.object();policy.put("policy_version","1.0.0");var rules=policy.putObject("capacity");
        rules.put("safety_floor_bytes",2L<<30);rules.put("safety_ceiling_bytes",20L<<30);rules.put("default_project_quota_ceiling_bytes",100L<<30);
        rules.put("safety_volume_fraction",new java.math.BigDecimal("0.05"));rules.put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(control.resolve("policy.json"),ControlBuild.strictMapper().writeValueAsBytes(policy));
        Path volume=asset.getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        var head=StrictJson.object();head.put("machine_id",machine);head.put("scope","software-fixture-actual-volume-observation");
        head.put("total_bytes",total);head.put("usable_bytes",free);head.put("old_workpackage_actual_is_unknown",true);
        FileRef financial=write(control.resolve("financial.json"),StrictJson.canonical(head));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,null,Math.subtractExact(total,free),financial);
        var release=new CapacityRelease(FORMAL_CAPACITY,FORMAL_PURPOSE,machine,"/root",ISSUER,"formal-fixture",NOW.toString(),review,
                policyRef,declared,census,financial,joint,List.of(new Volume(volume.toString(),joint,0,0,total,review,usage,List.of(),0)),List.of());
        FileRef capacity=write(control.resolve("capacity.json"),encode(release));
        var binding=new Binding(FORMAL_BINDING,FORMAL_PURPOSE,machine,"/root",ISSUER,"formal-fixture",NOW.toString(),review,declared,census,capacity);
        return new Fixture(declaration,write(control.resolve("binding.json"),encode(binding)),capacity,payload);
    }
    @Test void genuinePureProducerUsesSolePhysicalWriterAndItsActualCompleteConsumer()throws Exception {
        try(var software=FormalReleaseTestFixture.create(org.xar.ck3.control.build.FormalReleaseProducer.Mode.PUBLISH_RELEASE,70,1100000)){
            var original=software.actual();var stage=RootProfileBootstrapInputs.formalRelease(original);
            var bodies=new LinkedHashMap<String,byte[]>();
            for(var file:original.payload())bodies.put(original.outputRoot().relativize(file.target()).toString().replace('\\','/'),file.bytes());
            var payload=new Payload(bodies,stage.quote(),stage.outputDirectories(),original.manifest());
            Path control=Files.createDirectory(original.outputRoot().resolveSibling("guard-controls"));
            Fixture actual=fixture(original.outputRoot(),control,payload);
            assertTrue(stage.quote().size()>64);assertTrue(stage.outputDirectories().size()>3);
            assertTrue(stage.quote().stream().anyMatch(output->output.bytes()>1L<<20));
            assertTrue(stage.formalAssetPeakUpperBytes()>1536L*1024);
            assertEquals(Branch.FORMAL_RELEASE,stage.branch());
            try(var guard=actual.open()){
                var outputs=stage.createNew(guard);assertEquals(stage.quote().size(),outputs.size());
                original.verifyCreatedPayload();assertEquals(outputs.size(),guard.accounting().completedOutputs());
                assertEquals(0,guard.accounting().unresolvedPeakBytes());
                assertThrows(IOException.class,()->stage.createNew(guard));
            }
        }
    }
    @Test void sameGuardCreatesLargeFormalTreeAndSharedCompleteConsumerDetectsRealDrift()throws IOException {
        Payload payload=payload();Fixture actual=fixture(payload);
        assertTrue(payload.outputs().size()>64);assertTrue(payload.directories().size()>3);
        assertTrue(payload.bodies().values().stream().mapToLong(bytes->bytes.length).sum()>1536L*1024);
        try(var guard=actual.open()){
            guard.requirePlan(actual.asset(),payload.outputs(),payload.directories(),List.of());guard.createOutputDirectories();
            var files=guard.files();assertSame(files,guard.files());
            guard.requireTargets(payload.outputs().stream().map(output->actual.asset().resolve(output.fileName())).toList());
            for(var body:payload.bodies().entrySet()){
                var written=files.createNew(actual.asset().resolve(body.getKey()),body.getValue());files.verify(written);
                assertArrayEquals(body.getValue(),files.read(written,FORMAL_MAXIMUM_SINGLE_BYTES));
            }
            assertEquals(payload.outputs().size(),guard.accounting().completedOutputs());assertEquals(0,guard.accounting().unresolvedPeakBytes());
            var manifest=ControlBuild.strictMapper().readValue(Files.readAllBytes(actual.asset().resolve(MANIFEST)),ReleaseManifest.class);
            assertEquals(payload.manifest(),manifest);
            var tree=NativeRunProfileProducer.verifyProduction(actual.asset().resolve(TREE),manifest);
            assertEquals(payload.outputs().size()-1,tree.files().size());
            assertThrows(IOException.class,()->files.createNew(actual.asset().resolve(TREE+"/descriptor.mod"),payload.bodies().get(TREE+"/descriptor.mod")));
            Path drift=actual.asset().resolve(TREE+"/common/group0/file0.txt");Files.writeString(drift,"changed");
            assertThrows(IOException.class,()->NativeRunProfileProducer.verifyProduction(actual.asset().resolve(TREE),manifest));
            assertThrows(IOException.class,()->guard.requireTargets(List.of(drift)));
        }
    }
    @Test void ordinaryCardsCannotImportFormalKindsCountsDirectoriesOrByteCeilings()throws IOException {
        Payload payload=payload();Fixture fixture=fixture(payload);Declaration source=fixture.declaration();
        assertThrows(IllegalArgumentException.class,()->copy(source,DECLARATION,PURPOSE,source.assetMaximumChargedBytes(),source.maximumEntries(),payload.outputs(),payload.directories()));
        var ordinary=new Output(Kind.MCP_ADMISSION,"admission.json",1,"1".repeat(64));
        assertThrows(IllegalArgumentException.class,()->copy(source,DECLARATION,PURPOSE,1536L*1024,65,List.of(ordinary),List.of()));
        assertThrows(IllegalArgumentException.class,()->new Output(Kind.MCP_ADMISSION,"admission.json",(1L<<20)+1,"1".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->copy(source,FORMAL_DECLARATION,PURPOSE,8L<<20,source.maximumEntries(),payload.outputs(),payload.directories()));
        assertThrows(IllegalArgumentException.class,()->copy(source,DECLARATION,FORMAL_PURPOSE,8L<<20,source.maximumEntries(),payload.outputs(),payload.directories()));
        assertThrows(IllegalArgumentException.class,()->copy(source,FORMAL_DECLARATION,FORMAL_PURPOSE,FORMAL_MAXIMUM_ASSET_BYTES+1,source.maximumEntries(),payload.outputs(),payload.directories()));
        assertThrows(IllegalArgumentException.class,()->new Output(Kind.FORMAL_RELEASE_PAYLOAD,TREE+"/gfx/large.dds",FORMAL_MAXIMUM_SINGLE_BYTES+1L,"1".repeat(64)));
    }
    @Test void exactTreeAndSiblingManifestPlanRejectsAliasForeignKindsAndUnpricedParents()throws IOException {
        Payload payload=payload();Fixture fixture=fixture(payload);Declaration source=fixture.declaration();
        var missing=new ArrayList<>(payload.directories());missing.remove(TREE+"/common/group0");
        assertThrows(IllegalArgumentException.class,()->copy(source,FORMAL_DECLARATION,FORMAL_PURPOSE,8L<<20,source.maximumEntries(),payload.outputs(),missing));
        var extra=new ArrayList<>(payload.directories());extra.add(TREE+"/unused");extra.sort(String::compareTo);
        assertThrows(IllegalArgumentException.class,()->copy(source,FORMAL_DECLARATION,FORMAL_PURPOSE,8L<<20,source.maximumEntries()+1,payload.outputs(),extra));
        var outputs=new ArrayList<>(payload.outputs());outputs.set(outputs.size()-1,new Output(Kind.FORMAL_RELEASE_MANIFEST,"other.manifest.json",1,"1".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->copy(source,FORMAL_DECLARATION,FORMAL_PURPOSE,8L<<20,source.maximumEntries(),outputs,payload.directories()));
        assertThrows(IllegalArgumentException.class,()->new Output(Kind.FORMAL_RELEASE_PAYLOAD,TREE+"/../escape.txt",1,"1".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->RootBootstrapOutputContract.name("_issuer.json"));
        outputs.set(outputs.size()-1,new Output(Kind.MCP_TOOLS,"tools.json",1,"1".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->copy(source,FORMAL_DECLARATION,FORMAL_PURPOSE,8L<<20,source.maximumEntries(),outputs,payload.directories()));
    }
    @Test void formalWireRoundTripsStrictlyAndIssuerFileIdentityStillCannotResetBudget()throws IOException {
        Fixture actual=fixture(payload());byte[] encoded=encode(actual.declaration());assertEquals(actual.declaration(),decode(encoded,Declaration.class));
        var value=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encoded);value.put("maximum_entries",true);
        byte[] booleanWire=StrictJson.canonical(value);assertThrows(IOException.class,()->decode(booleanWire,Declaration.class));
        value=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encoded);value.remove("retained_inputs");byte[] missing=StrictJson.canonical(value);
        assertThrows(IOException.class,()->decode(missing,Declaration.class));
        try(var guard=actual.open()){
            Path capacity=Path.of(actual.capacity().path()),replacement=actual.control().resolve("replacement.json");
            Files.copy(capacity,replacement);Files.setLastModifiedTime(replacement,Files.getLastModifiedTime(capacity));Files.move(replacement,capacity,StandardCopyOption.REPLACE_EXISTING);
            assertThrows(IOException.class,guard::createOutputDirectories);
            assertFalse(Files.exists(actual.asset().resolve(TREE)));
        }
    }
    @Test void unpricedFileAndMixedBranchBindingRejectBeforeAnyFormalWrite()throws IOException {
        Fixture actual=fixture(payload());Files.writeString(actual.asset().resolve("unpriced.txt"),"x");assertThrows(IOException.class,actual::open);
        Files.delete(actual.asset().resolve("unpriced.txt"));
        var value=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(Files.readAllBytes(Path.of(actual.binding().path())));
        value.put("schema",BINDING);value.put("purpose",PURPOSE);FileRef mixed=write(actual.control().resolve("mixed-binding.json"),StrictJson.canonical(value));
        assertThrows(IOException.class,()->RootBootstrapOutputGuard.readExact(mixed,CLOCK));assertFalse(Files.exists(actual.asset().resolve(TREE)));
    }
    @Test void genericBootstrapCannotCopyAFormalManifestToBypassThePureProducer()throws IOException {
        Payload payload=payload();Fixture actual=fixture(payload());FileRef original=write(root.resolve("raw-formal-manifest.json"),payload.bodies().get(MANIFEST));
        var request=new RootJavaBootstrapInputs.Request(RootJavaBootstrapInputs.SCHEMA,WindowsJobProcess.currentMachineId(),NOW.plusSeconds(3600).toString(),
                RootJavaBootstrapInputs.Mode.QUOTE,null,List.of(new RootJavaBootstrapInputs.Item(Kind.FORMAL_RELEASE_MANIFEST,original,actual.asset().resolve(MANIFEST).toString())));
        assertThrows(IOException.class,()->RootJavaBootstrapInputs.prepare(request,CLOCK));assertFalse(Files.exists(actual.asset().resolve(TREE)));
    }
    @Test void actualBootstrapRequestWireKeepsSeparateGitExecutionAndExactProducerIdentity()throws IOException {
        String machine=WindowsJobProcess.currentMachineId(),review=Instant.now().plusSeconds(600).toString();
        FileRef producer=write(root.resolve("producer-request.json"),"{}".getBytes(StandardCharsets.UTF_8));
        // Serialization data only; no Git executable is opened and no process or write authority is granted.
        var execution=new org.xar.ck3.control.build.FormalReleaseGit.Execution(machine,review,root.resolve("repository"),
                new FileRef(root.resolve("git.exe").toString(),1,"1".repeat(64)),root.resolve("git-captures"),64L<<20);
        var request=new RootProfileBootstrapCommand.FormalReleaseRequest("xar.java-root-formal-release-bootstrap/v1",machine,review,producer,execution);
        byte[] bytes=ControlBuild.strictMapper().writeValueAsBytes(request);
        assertEquals(request,ControlBuild.strictMapper().readValue(bytes,RootProfileBootstrapCommand.FormalReleaseRequest.class));
        var row=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(bytes);
        ((com.fasterxml.jackson.databind.node.ObjectNode)row.get("producer_request")).put("bytes",true);byte[] booleanWire=StrictJson.canonical(row);
        assertThrows(IOException.class,()->ControlBuild.strictMapper().readValue(booleanWire,RootProfileBootstrapCommand.FormalReleaseRequest.class));
        var missing=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(bytes);missing.remove("execution");byte[] missingWire=StrictJson.canonical(missing);
        assertThrows(IOException.class,()->ControlBuild.strictMapper().readValue(missingWire,RootProfileBootstrapCommand.FormalReleaseRequest.class));
    }
    @Test void genuineProducerOriginalPhaseRoundTripsSharedDuplexWireAndIndependentSoftwareBinding()throws Exception {
        try(var software=FormalReleaseTestFixture.create(org.xar.ck3.control.build.FormalReleaseProducer.Mode.PROFILE_STAGING,70,1100000,
                org.xar.ck3.control.build.FormalReleaseProducer.Layout.ISOLATED_PROFILE_IMPORT)){
            var actual=software.actual();var prepared=RootProfileBootstrapInputs.formalRelease(actual);
            var bodies=new LinkedHashMap<String,byte[]>();
            for(var file:actual.payload())bodies.put(actual.outputRoot().relativize(file.target()).toString().replace('\\','/'),file.bytes());
            var payload=new Payload(bodies,prepared.quote(),prepared.outputDirectories(),actual.manifest());
            Path control=Files.createDirectory(actual.outputRoot().resolveSibling("duplex-software-issuer"));
            Fixture cards=fixture(actual.outputRoot(),control,payload);
            byte[] binding=RootBootstrapProtocol.bindingLine(cards.binding());
            var output=new java.io.ByteArrayOutputStream();
            java.io.InputStream originalIn=System.in;java.io.PrintStream originalOut=System.out;
            try{
                System.setIn(new java.io.ByteArrayInputStream(binding));
                System.setOut(new java.io.PrintStream(output,true,StandardCharsets.UTF_8));
                Object created=RootProfileBootstrapCommand.phase(null,"FORMAL_RELEASE_PAYLOAD_AND_MANIFEST",prepared,NOW.plusSeconds(3600).toString(),CLOCK,
                        SharedSourceFiles.observe(Path.of(cards.binding().path())),new SharedSourceFiles.Witness[0]);
                assertInstanceOf(List.class,created);
            }finally{System.setIn(originalIn);System.setOut(originalOut);}
            var lines=output.toString(StandardCharsets.UTF_8).lines().toList();assertEquals(2,lines.size());
            var quote=RootBootstrapProtocol.line((lines.get(0)+"\n").getBytes(StandardCharsets.UTF_8),RootBootstrapProtocol.Quote.class);
            assertEquals(prepared.quote(),quote.outputs());assertEquals(prepared.outputDirectories(),quote.outputDirectories());
            assertEquals("ISOLATED_PROFILE_IMPORT",assertInstanceOf(RootBootstrapProtocol.FormalQuote.class,quote).layout());assertTrue(quote.outputs().size()>64);
            assertTrue(quote.outputs().stream().anyMatch(row->row.fileName().equals("profile/mod-content/xar-production/gfx/interface/icons/traits/_stars_10.dds")));
            var stage=RootBootstrapProtocol.stage((lines.get(1)+"\n").getBytes(StandardCharsets.UTF_8),WindowsJobProcess.currentMachineId());
            RootProfileBootstrapSession.verifyStage(quote,stage);assertEquals(prepared.quote().size(),stage.created().size());
            actual.verifyCreatedPayload();
            assertArrayEquals(new byte[]{1,2,3},Files.readAllBytes(actual.request().productionRoot().resolve("gfx/interface/icons/traits/_stars_10.dds")));
        }
    }
    private static Declaration copy(Declaration source,String schema,String purpose,long assets,int maximum,List<Output> outputs,List<String> directories){
        return new Declaration(schema,purpose,source.machineId(),source.ownerTask(),source.windowId(),source.observedAtUtc(),source.reviewAtUtc(),source.assetRoot(),source.assetDirectory(),
                source.controlRoot(),source.controlDirectory(),assets,source.controlMaximumChargedBytes(),schema.equals(DECLARATION)?1<<20:source.maximumSingleWriteBytes(),maximum,outputs,directories,List.of());
    }
    private static FileRef write(Path path,byte[] bytes)throws IOException{Files.write(path,bytes);return FileRef.measure(path);}
}
