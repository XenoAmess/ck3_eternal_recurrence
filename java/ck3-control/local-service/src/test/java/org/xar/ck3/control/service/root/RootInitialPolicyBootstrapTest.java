package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.InitialDriverState;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Real policy bytes -> existing finite guard -> physical readback -> actual initial Driver consumer.
 * Environment and issuer inputs are explicit software fixtures, never first-live sources or authority. */
final class RootInitialPolicyBootstrapTest {
    private static final Instant NOW=Instant.parse("2026-10-25T21:00:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    @TempDir Path directory;

    @Test void bothExplicitSourceSelectionsPublishThroughTheOriginalGuardAndReachTheRealInitialDriver()throws Exception {
        for(var lifecycle:List.of(InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION,InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE)){
            Path root=Files.createDirectory(directory.resolve(lifecycle.name()));
            FileRef environment=environment(root,lifecycle);Path asset=Files.createDirectory(root.resolve("asset"));
            var quoteRequest=request(RootJavaBootstrapInputs.Mode.QUOTE,null,environment,lifecycle,asset.resolve("policy.json"));
            var quoted=RootInitialPolicyBootstrap.prepare(quoteRequest,CLOCK);
            assertEquals(Kind.INITIAL_POLICY,quoted.quote().getFirst().kind());assertFalse(Files.exists(asset.resolve("policy.json")));
            assertEquals(quoteRequest,RootInitialPolicyBootstrap.decode(RootInitialPolicyBootstrap.encode(quoteRequest)));
            FileRef binding=softwareBinding(root,asset,quoted.quote());
            var createRequest=request(RootJavaBootstrapInputs.Mode.CREATE_NEW,binding,environment,lifecycle,asset.resolve("policy.json"));
            var prepared=RootInitialPolicyBootstrap.prepare(createRequest,CLOCK);assertEquals(quoted.expected(),prepared.expected());
            var created=prepared.createNew(CLOCK);assertEquals(prepared.expected(),created.original());
            var policy=InitialEpisodePolicy.readExact(created.exact(),environment);policy.verify();assertEquals(lifecycle,policy.kind());
            assertArrayEquals(InitialEpisodePolicy.produce(environment,lifecycle,createRequest.fresh()).bytes(),Files.readAllBytes(Path.of(created.original().path())));
            var driver=InitialDriverState.create(frame(),"software-policy-pipe","software-policy-episode",policy);
            var restored=DriverStateSnapshot.decodeComplete(driver.driver().encode());
            if(lifecycle==InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION)assertInstanceOf(DriverStateSnapshot.Value.class,restored.campaignGoal());
            else assertInstanceOf(DriverStateSnapshot.NullValue.class,restored.campaignGoal());
            assertThrows(IOException.class,()->prepared.createNew(CLOCK));
        }
    }
    @Test void missingOrMistypedSelectionCannotBorrowTheHistoricalEnvironmentAndQuotesDoNotWrite()throws Exception {
        Path root=Files.createDirectory(directory.resolve("strict"));FileRef environment=environment(root,InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION);
        var request=request(RootJavaBootstrapInputs.Mode.QUOTE,null,environment,InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION,root.resolve("policy.json"));
        byte[] wire=RootInitialPolicyBootstrap.encode(request);
        var missing=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(wire);missing.remove("fresh");
        assertThrows(IOException.class,()->RootInitialPolicyBootstrap.decode(StrictJson.canonical(missing)));
        var wrong=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(wire);wrong.put("fresh",true);
        assertThrows(IOException.class,()->RootInitialPolicyBootstrap.decode(StrictJson.canonical(wrong)));
        var prepared=RootInitialPolicyBootstrap.prepare(request,CLOCK);assertThrows(IOException.class,()->prepared.createNew(CLOCK));
        var mismatch=new RootInitialPolicyBootstrap.Request(request.schema(),request.machineId(),request.observedAtUtc(),request.reviewAtUtc(),request.mode(),null,
                environment,InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE,InitialEpisodePolicy.FreshPact.ROGUE_REQUIRED,request.target());
        assertThrows(IllegalArgumentException.class,()->RootInitialPolicyBootstrap.prepare(mismatch,CLOCK));
        assertFalse(Files.exists(Path.of(request.target())));
    }
    @Test void actualSharedThreeArgumentCliQuotesTheSourceBoundPolicyWithoutAnExistingPolicyOriginal()throws Exception {
        Path root=Files.createDirectory(directory.resolve("shared-cli"));
        FileRef environment=environment(root,InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION);
        Instant observed=Instant.now();Path target=root.resolve("policy.json");
        var request=new RootInitialPolicyBootstrap.Request(RootInitialPolicyBootstrap.SCHEMA,WindowsJobProcess.currentMachineId(),
                observed.toString(),observed.plusSeconds(300).toString(),RootJavaBootstrapInputs.Mode.QUOTE,null,environment,
                InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION,InitialEpisodePolicy.FreshPact.ORDINARY_NO_PACT,
                target.toString().replace('\\','/'));
        FileRef original=write(root.resolve("request.json"),RootInitialPolicyBootstrap.encode(request));
        var bytes=new java.io.ByteArrayOutputStream();
        synchronized(RootJavaBootstrapInputs.class){
            var before=System.out;
            try(var output=new java.io.PrintStream(bytes,true,StandardCharsets.UTF_8)){
                System.setOut(output);RootJavaBootstrapInputs.main(new String[]{original.path(),Long.toString(original.bytes()),original.sha256()});
            }finally{System.setOut(before);}
        }
        var quote=RootBootstrapProtocol.line(bytes.toByteArray(),RootBootstrapProtocol.Quote.class);
        assertInstanceOf(RootBootstrapProtocol.OrdinaryQuote.class,quote);
        assertEquals("xar.java-root-bootstrap-phase-quote/v1",quote.schema());
        assertEquals("INITIAL_POLICY",quote.phase());assertEquals(request.machineId(),quote.machineId());
        assertEquals(request.reviewAtUtc(),quote.reviewAtUtc());assertEquals(root.toString(),quote.assetRoot());
        assertEquals(RootInitialPolicyBootstrap.prepare(request,Clock.systemUTC()).quote(),quote.outputs());
        assertEquals(List.of(),quote.outputDirectories());assertEquals(List.of(),quote.retainedInputs());
        assertEquals("AWAITING_REAL_INDEPENDENT_ISSUER_BINDING",quote.authority());
        assertFalse(Files.exists(target));original.verify();environment.verify();
    }
    private static RootInitialPolicyBootstrap.Request request(RootJavaBootstrapInputs.Mode mode,FileRef binding,FileRef environment,
            InitialEpisodePolicy.Lifecycle lifecycle,Path target){
        return new RootInitialPolicyBootstrap.Request(RootInitialPolicyBootstrap.SCHEMA,WindowsJobProcess.currentMachineId(),NOW.minusSeconds(1).toString(),
                NOW.plusSeconds(300).toString(),mode,binding,environment,lifecycle,lifecycle==InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE
                ?InitialEpisodePolicy.FreshPact.ROGUE_REQUIRED:InitialEpisodePolicy.FreshPact.ORDINARY_NO_PACT,target.toString().replace('\\','/'));
    }
    private static FileRef environment(Path root,InitialEpisodePolicy.Lifecycle lifecycle)throws IOException {
        var original=StrictJson.object().put("format_version",1).put("environment_sha256","a".repeat(64));
        original.putObject("rules").putArray("profile").addObject().put("rule","xar_enabled")
                .put("setting",lifecycle==InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE?"xar_on":"xar_off");
        return write(root.resolve("historical-environment-software-fixture.json"),StrictJson.canonical(original));
    }
    private static FileRef softwareBinding(Path root,Path asset,List<Output> outputs)throws IOException {
        Path control=Files.createDirectory(root.resolve("control"));String machine=WindowsJobProcess.currentMachineId(),review=NOW.plusSeconds(300).toString();
        var declaration=new Declaration(DECLARATION,PURPOSE,machine,"/root","initial-policy-software-fixture",NOW.minusSeconds(1).toString(),review,
                asset.toString(),SharedSourceFiles.nativeDirectory(asset),control.toString(),SharedSourceFiles.nativeDirectory(control),
                1536L*1024,512L*1024,1<<20,64,outputs,List.of(),List.of());
        FileRef declared=write(control.resolve("declaration.json"),encode(declaration));
        FileRef census=write(control.resolve("census.json"),encode(RootBootstrapOutputGuard.observeAssetRoot(declared,CLOCK)));
        var policy=StrictJson.object().put("policy_version","1.0.0");var limits=policy.putObject("capacity");
        limits.put("safety_floor_bytes",2L<<30);limits.put("safety_ceiling_bytes",20L<<30);limits.put("default_project_quota_ceiling_bytes",100L<<30);
        limits.put("safety_volume_fraction",new java.math.BigDecimal("0.05"));limits.put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(control.resolve("policy.json"),StrictJson.canonical(policy));Path volume=asset.getRoot();
        long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        FileRef financial=write(control.resolve("financial.json"),StrictJson.canonical(StrictJson.object().put("scope","software-fixture-volume-observation").put("machine_id",machine)));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,
                null,Math.subtractExact(total,free),financial);
        var release=new CapacityRelease(CAPACITY,PURPOSE,machine,"/root",ISSUER,"initial-policy-software-fixture",NOW.toString(),review,
                policyRef,declared,census,financial,2L<<20,List.of(new Volume(volume.toString(),2L<<20,0,0,total,review,usage,List.of(),0)),List.of());
        FileRef capacity=write(control.resolve("capacity.json"),encode(release));
        return write(control.resolve("binding.json"),encode(new Binding(BINDING,PURPOSE,machine,"/root",ISSUER,"initial-policy-software-fixture",
                NOW.toString(),review,declared,census,capacity)));
    }
    private static FileRef write(Path target,byte[] bytes)throws IOException {
        Files.write(target,bytes,StandardOpenOption.CREATE_NEW);return FileRef.measure(target);
    }
    private static NativeObservationPort.ObservedFrame frame(){
        byte[] state="{\"paused\":true,\"map_ready\":true,\"date_raw\":24000,\"played_character\":{\"character_id\":29829,\"alive\":true},\"active_event\":null,\"pending_character_interaction\":null,\"active_wars\":[],\"player_armies\":[]}".getBytes(StandardCharsets.UTF_8);
        byte[] body=("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"software-policy-frame\",\"revision\":1,\"state\":"+new String(state,StandardCharsets.UTF_8)+"}").getBytes(StandardCharsets.UTF_8);
        byte[] packet=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("software-machine",game,BigInteger.ONE,"software-session"),
                "software-policy-frame",BigInteger.ONE,new RawJson(state),packet,NOW);
    }
}
