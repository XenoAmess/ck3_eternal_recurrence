package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.*;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;

/** Actual software transport packets -> typed source scope -> sole VFS service -> original Python response parity.
 * A software transport never qualifies an actual Root, native observer, Game, or loaded asset. */
final class CoaVfsProducerConsumerTest {
    private static final String LOGICAL="gfx/coat_of_arms/patterns/shared.dds";
    private static final String CURRENT="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    @TempDir Path temporary;
    @Test void strictLimitsProducerReaderRoundTripRejectsMissingNullWrongTypesAndUnknownFields(){
        var limits=new CoaVfs.Limits(1L<<30,1L<<28);assertEquals(limits,CoaVfs.decodeLimits(CoaVfs.encodeLimits(limits)));
        for(String bad:List.of("{}","{\"schema\":\"xar.java-coa-vfs-source-read-limits/v1\",\"maximum_source_bytes\":true,\"maximum_archive_bytes\":1}","{\"schema\":\"xar.java-coa-vfs-source-read-limits/v1\",\"maximum_source_bytes\":2.0,\"maximum_archive_bytes\":1}","{\"schema\":\"xar.java-coa-vfs-source-read-limits/v1\",\"maximum_source_bytes\":2,\"maximum_archive_bytes\":null}","{\"schema\":\"xar.java-coa-vfs-source-read-limits/v1\",\"maximum_source_bytes\":2,\"maximum_archive_bytes\":1,\"default\":true}"))assertThrows(IllegalArgumentException.class,()->CoaVfs.decodeLimits(raw(bad)));
        assertThrows(IllegalArgumentException.class,()->new CoaVfs.Limits(0,1));assertThrows(IllegalArgumentException.class,()->new CoaVfs.Limits(1,2));
    }
    @Test void actualCurrent4PacketCannotRelabelOldBuildOrReadCallerArbitraryMissingPaths()throws Exception {
        var packets=new Packets(hello(CURRENT),heartbeat("{\"rows\":[]}"),snapshot());
        try(var transport=new NativeGameTransport(packets,config(CURRENT),8,2)){
            transport.observe(Instant.parse("2030-01-01T00:00:00Z"));int reads=packets.reads;
            var received=BridgeDiagnosticsCapture.capture(transport.pipeName(),transport.diagnostics(),Optional.empty());
            var input=input(new Vfs(Method.VFS,temporary.resolve("not-an-allowed-game"),LOGICAL),new ExactRef(temporary.resolve("unread/binaries/ck3.exe").toString(),1,CURRENT.toLowerCase(java.util.Locale.ROOT)),received,new CoaVfs.Limits(1,1));
            IOException rejected=assertThrows(IOException.class,()->CoaVfs.project(input));assertTrue(rejected.getMessage().contains("1.19.0.6"));assertEquals(reads,packets.reads);assertEquals(0,packets.writes);
        }
    }
    @Test void changedTypedDiagnosticCopyCannotBecomeAnActualObserverSource()throws Exception {
        var packets=new Packets(hello(FrontendCoaService.EXE_SHA),heartbeat("{\"rows\":[]}"),snapshot());
        try(var transport=new NativeGameTransport(packets,config(FrontendCoaService.EXE_SHA),8,2)){
            transport.observe(Instant.parse("2030-01-01T00:00:00Z"));var actual=BridgeDiagnosticsCapture.capture(transport.pipeName(),transport.diagnostics(),Optional.empty());
            var copied=new BridgeDiagnostics.Received(actual.pipeName(),actual.original(),actual.hello(),actual.heartbeat(),actual.pong(),actual.error(),actual.snapshotPublishDiagnostic(),new BridgeDiagnostics.PrivateObservers(Optional.empty(),Optional.empty(),Optional.empty()),actual.modalChoiceHint(),actual.retainedSnapshot());
            var request=new Vfs(Method.VFS,temporary,LOGICAL);var executable=new ExactRef(temporary.resolve("binaries/ck3.exe").toString(),1,FrontendCoaService.EXE_SHA.toLowerCase(java.util.Locale.ROOT));
            assertThrows(IOException.class,()->CoaVfs.project(input(request,executable,copied,new CoaVfs.Limits(1024,1024))));assertEquals(0,packets.writes);
        }
    }
    @Test void anOldReceivedMountCannotBindAnotherPhysicalSessionAfterColdReplacement()throws Exception {
        var packets=new Packets(hello(FrontendCoaService.EXE_SHA),heartbeat("{\"rows\":[]}"),snapshot());
        try(var transport=new NativeGameTransport(packets,config(FrontendCoaService.EXE_SHA),8,2)){
            transport.observe(Instant.parse("2030-01-01T00:00:00Z"));var actual=BridgeDiagnosticsCapture.capture(transport.pipeName(),transport.diagnostics(),Optional.empty());var old=actual.session().orElseThrow();
            var next=new org.xar.ck3.control.application.action.NativeObservationPort.TransportSession(old.machineId(),new GameGeneration(43,new PythonOnlyUInt64(BigInteger.TWO)),BigInteger.ONE,"software-replacement");
            var source=new G2Source(next.machineId(),Instant.now().toString(),"software-fixture-only",new ExactRef("software-vfs-source",1,"a".repeat(64)));
            var input=new CoaVfs.Input(new Vfs(Method.VFS,temporary,LOGICAL),new ExactRef(temporary.resolve("binaries/ck3.exe").toString(),1,FrontendCoaService.EXE_SHA.toLowerCase(java.util.Locale.ROOT)),actual,next,source,new CoaVfs.Limits(1,1));
            assertThrows(IOException.class,()->CoaVfs.project(input));assertEquals(0,packets.writes);
        }
    }
    @Test void completeOriginalPythonCasesFlowThroughActualComponentServiceAndSharedWire()throws Exception {
        FileRef capture=new FileRef(required("xar.coa.vfs.oracles.path"),Long.parseLong(required("xar.coa.vfs.oracles.bytes")),required("xar.coa.vfs.oracles.sha256"));if(capture.bytes()<1||capture.bytes()>1_048_576)throw new IOException("finite original VFS case roster required");
        capture.verify();var witness=SharedSourceFiles.observe(Path.of(capture.path()));
        var cases=FullJsonTree.parse(Files.readAllBytes(Path.of(capture.path())),1_048_576);assertTrue(cases.isArray()&&!cases.isEmpty());var seen=new HashSet<String>();
        for(var row:cases){StrictJson.object(row,Set.of("case","arguments","diagnostics","executable"));seen.add(StrictJson.text(row.get("case")));
            var request=(Vfs)FrontendCoaCodec.decode(Method.VFS,raw(row.get("arguments").toString()));var diagnostics=row.get("diagnostics");var observer=diagnostics.get("private_observers").get("physfs_mounted_data_observer_v1");
            var ref=row.get("executable");StrictJson.object(ref,Set.of("path","bytes","sha256"));var executable=new ExactRef(StrictJson.text(ref.get("path")),StrictJson.integer(ref.get("bytes"),1,1L<<32),StrictJson.text(ref.get("sha256")));
            var packets=new Packets(hello(FrontendCoaService.EXE_SHA),heartbeat(observer.toString()),snapshot());
            try(var transport=new NativeGameTransport(packets,config(FrontendCoaService.EXE_SHA),8,2)){
                transport.observe(Instant.parse("2030-01-01T00:00:00Z"));var received=BridgeDiagnosticsCapture.capture(transport.pipeName(),transport.diagnostics(),Optional.empty());int reads=packets.reads;
                var budget=new CoaVfs.Limits(16L<<30,8L<<30);var input=input(request,executable,received,budget);
                var service=new FrontendCoaService(List.of(new FrontendCoaService.ComponentBinding(Set.of(Method.VFS),actual->{assertEquals(request,actual);return CoaVfs.project(input);})));var result=service.execute(request);
                var encoded=FrontendCoaCodec.encode(result);assertEquals(result,new Response(encoded));var actual=FullJsonTree.parse(encoded.bytes(),RawJson.MAXIMUM_BYTES);
                assertEquals(originalPython(request,diagnostics.toString()),actual,row.get("case").textValue());assertFalse(actual.get("provenance").get("engine_resolver_called").booleanValue());assertFalse(actual.get("provenance").get("resource_registration_observed").booleanValue());assertEquals(reads,packets.reads);assertEquals(0,packets.writes);
                assertThrows(IOException.class,()->CoaVfs.project(input(request,executable,received,new CoaVfs.Limits(1,1))),"complete reservation fails before original algorithm source reads");
            }
        }
        assertTrue(seen.containsAll(Set.of("later_directory","later_archive","casefold_ligature","not_found")),"complete original VFS coverage roster required; no partial pass");SharedSourceFiles.assertUnchanged(witness);capture.verify();
    }
    private com.fasterxml.jackson.databind.JsonNode originalPython(Vfs request,String diagnostics)throws Exception {
        String code="""
            import hashlib,json,pathlib,sys
            root=pathlib.Path(sys.argv[1]);base=root/'ck3_autonomous_player/src/xar_autoplayer'
            pins={'coat_of_arms_vfs_resolution.py':'a453f3840dcbc51e9cc020a21089c36d843e803273926e2f64c365a7a7eddbcb','coat_of_arms_resources.py':'fb3831d8a9b0111d2e8a1c20b820105dfa49af8bab09f2b6606991823db5d4f6'}
            for name,sha in pins.items():assert hashlib.sha256((base/name).read_bytes()).hexdigest()==sha
            sys.path.insert(0,str(base.parent))
            from xar_autoplayer.coat_of_arms_vfs_resolution import project_coat_of_arms_vfs_asset_winner_v1
            print(json.dumps(project_coat_of_arms_vfs_asset_winner_v1(json.loads(sys.argv[2]),sys.argv[3],sys.argv[4]),ensure_ascii=False,separators=(',',':')))
            """;
        Path output=temporary.resolve("python-vfs-original.log");var builder=new ProcessBuilder(required("xar.python"),"-B","-X","utf8","-c",code,required("xar.repository.root"),diagnostics,request.directory().toString(),request.logicalPath()).redirectErrorStream(true).redirectOutput(output.toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");var child=builder.start();
        if(!child.waitFor(30,TimeUnit.SECONDS)){child.destroyForcibly();throw new IOException("original Python VFS projection timeout");}assertTrue(Files.size(output)<=1_048_576);assertEquals(0,child.exitValue(),Files.readString(output));return FullJsonTree.parse(Files.readAllBytes(output),1_048_576);
    }
    @Test void originalTypedPublicRequestCannotSelectAnotherGameDirectoryUnderAnActualProfile()throws Exception {
        Path profile=temporary.resolve("retained-profile"),other=temporary.resolve("caller-directory");Files.createDirectories(profile);Files.createDirectories(other);
        var packets=new Packets(hello(FrontendCoaService.EXE_SHA),heartbeat("{\"rows\":[]}"),snapshot());
        try(var transport=new NativeGameTransport(packets,config(FrontendCoaService.EXE_SHA),8,2)){
            transport.observe(Instant.parse("2030-01-01T00:00:00Z"));var received=BridgeDiagnosticsCapture.capture(transport.pipeName(),transport.diagnostics(),Optional.empty());
            var executable=new ExactRef(profile.resolve("binaries/ck3.exe").toString(),1,FrontendCoaService.EXE_SHA.toLowerCase(java.util.Locale.ROOT));
            var rejected=assertThrows(IOException.class,()->CoaVfs.project(input(new Vfs(Method.VFS,other,LOGICAL),executable,received,new CoaVfs.Limits(1024,1024))));assertTrue(rejected.getMessage().contains("game_directory"));assertEquals(0,packets.writes);
        }
        for(String logical:List.of("../gfx/coat_of_arms/patterns/x.dds","/gfx/coat_of_arms/patterns/x.dds","gfx/coat_of_arms/patterns//x.dds","gfx/coat_of_arms/patterns/./x.dds","common/coat_of_arms/x.txt"))assertThrows(IllegalArgumentException.class,()->new Vfs(Method.VFS,profile,logical));
    }
    private static CoaVfs.Input input(Vfs request,ExactRef executable,BridgeDiagnostics.Received actual,CoaVfs.Limits limits){var session=actual.session().orElseThrow();return new CoaVfs.Input(request,executable,actual,session,new G2Source(session.machineId(),Instant.now().toString(),"software-fixture-only",new ExactRef("software-vfs-source",1,"a".repeat(64))),limits);}
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static String required(String name){String value=System.getProperty(name);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_ORIGINAL_COA_VFS_INPUT: "+name);return value;}
    private static String hello(String sha){return "{\"protocol_version\":1,\"type\":\"hello\",\"pid\":42,\"connection_generation\":18446744073709551615,\"bridge_version\":\"fixture\",\"expected_ck3_sha256\":\""+sha+"\",\"game_adapter_id\":\"fixture-adapter\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\"]}";}
    private static String heartbeat(String observer){return "{\"protocol_version\":1,\"type\":\"heartbeat\",\"sequence\":7,\"connection_generation\":18446744073709551615,\"physfs_mounted_data_observer_v1\":"+observer+"}";}
    private static String snapshot(){return "{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"software-vfs\",\"revision\":9,\"state\":{\"paused\":true,\"map_ready\":true,\"date_raw\":1,\"played_character\":{\"character_id\":73,\"alive\":true}}}";}
    private static NativePipeEndpoint.Config config(String sha){return new NativePipeEndpoint.Config("\\\\.\\pipe\\software-vfs","software-vfs-machine",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"software-vfs-session","fixture",sha,"fixture-adapter");}
    private static final class Packets implements NativePacketPort {
        private final ArrayDeque<byte[]> rows=new ArrayDeque<>();private int reads,writes;
        private Packets(String... source){for(String value:source){byte[] body=value.getBytes(StandardCharsets.UTF_8);rows.add(ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array());}}
        public void verify(){}public void awaitConnection(Instant deadline){}public byte[] readPacket(Instant deadline)throws IOException{reads++;if(rows.isEmpty())throw new IOException("software originals exhausted");return rows.removeFirst();}public void writePacket(byte[] bytes,Instant deadline){writes++;throw new AssertionError("VFS must not submit any native request");}public void close(){}
    }
}
