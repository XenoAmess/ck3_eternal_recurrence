package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeRequestChronologyCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.*;

/** Real C++ serializer oracle -> unchanged Java packet/ACK consumers. No synthetic positive result JSON. */
final class CommandResultFrameEscapeInteropTest {
    private static final int MAX=65536;
    private static final String HEADER_SHA="43400e4e35e9daf1642673a30674cf4d83ea7edae88ce558a29e9a4a277e0375";
    private static final String ENTRY_SHA="227781db63e96ce256804b8d9fec2ee1cc05bf74b83d71462e1b1e744dc03a33";
    @TempDir Path temporary;
    private record Case(String name,String request,String step,String status,boolean ok) { }
    private static List<String> strings() {
        var controls=new StringBuilder("all-control:");
        for(int value=0;value<32;value++)controls.append((char)value);
        var remaining=new StringBuilder("DEL-and-C1:").append((char)127);
        for(int value=128;value<160;value++)remaining.append((char)value);
        char quote=34,slash=92;
        return List.of("quotes:"+quote+"double"+quote,"backslash:"+slash+slash,
                controls.toString(),"C:"+slash+"mods"+slash+"quoted"+quote+(char)10+"next"+slash+"file.dds",
                "Unicode: 汉字 é ﬃ 𝄞 🙂",remaining.toString());
    }
    @Test void realProducerEscapesAllReturnedStringsOnSuccessAndFailureWithoutChangingOriginalBytes()throws Exception {
        Oracle oracle=Oracle.open(temporary);
        for(String text:strings())for(boolean ok:List.of(false,true)){
            var expected=new Case("returned-content","request-汉字-🙂",text,text,ok);
            byte[] body=oracle.produce(expected);
            var original=NativeWire.object(NativeWire.parse(body));
            assertEquals(expected.request(),NativeWire.text(original.get("request_id")));
            byte[] packet=NativeWire.packet(body);
            var actual=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
            assertArrayEquals(packet,actual.packet().value());assertArrayEquals(body,actual.payload().value());
            assertEquals(expected.request(),actual.requestId());assertEquals(ok,actual.nativeOk());
            if(ok){
                assertEquals(NativeWire.Presence.ABSENT,actual.error().presence());
                var result=NativeWire.object(NativeWire.parse(actual.result().token().orElseThrow().value()));
                assertEquals(text,NativeWire.text(result.get("step")));
                assertEquals(text,NativeWire.text(result.get("status")));assertTrue(result.get("accepted").booleanValue());
            }else{
                assertEquals(NativeWire.Presence.ABSENT,actual.result().presence());
                assertEquals(text,NativeWire.text(NativeWire.parse(actual.error().token().orElseThrow().value())));
            }
            byte[] first=actual.packet().value();first[0]=0;
            assertArrayEquals(packet,actual.packet().value(),"retained source packet must be immutable");
        }
        oracle.requireCurrent();
    }
    @Test void realProducerAlsoEscapesUnsafeIdsWhileJavaKeepsItsExistingRequestIdAdmission()throws Exception {
        Oracle oracle=Oracle.open(temporary);
        for(String unsafe:strings().subList(0,4))for(boolean ok:List.of(false,true)){
            var expected=new Case("unsafe-id",unsafe,"ordinary-step","ordinary-status",ok);
            byte[] body=oracle.produce(expected);
            assertEquals(unsafe,NativeWire.text(NativeWire.object(NativeWire.parse(body)).get("request_id")));
            assertThrows(IOException.class,()->NativeWire.decode(NativeWire.packet(body)),
                    "valid JSON escaping grants no new request-id permission");
        }
    }
    @Test void mutationsOfARealProducerEnvelopeRejectMissingNullAndWrongRequiredFieldTypes()throws Exception {
        Oracle oracle=Oracle.open(temporary);
        byte[] body=oracle.produce(new Case("strict-envelope","strict-request","strict-step","strict-status",true));
        var original=NativeWire.object(NativeWire.parse(body));
        for(String field:List.of("type","protocol_version","request_id","ok")){
            var missing=original.deepCopy();missing.remove(field);assertBad(missing);
            var nil=original.deepCopy();nil.putNull(field);assertBad(nil);
            var array=original.deepCopy();array.set(field,StrictJson.object().arrayNode());assertBad(array);
            var number=original.deepCopy();number.put(field,17);assertBad(number);
        }
        var revision=original.deepCopy();revision.put("protocol_version",1.0);assertBad(revision);
        var boolRevision=original.deepCopy();boolRevision.put("protocol_version",true);assertBad(boolRevision);
        var stringOk=original.deepCopy();stringOk.put("ok","true");assertBad(stringOk);
        // result/error are deliberately optional opaque tokens at this shared layer.
        var absent=original.deepCopy();absent.remove("result");
        assertEquals(NativeWire.Presence.ABSENT,result(absent).result().presence());
        var nil=original.deepCopy();nil.putNull("result");nil.putNull("error");
        var nullFields=result(nil);assertEquals(NativeWire.Presence.NULL,nullFields.result().presence());
        assertEquals("null",new String(nullFields.result().token().orElseThrow().value(),StandardCharsets.UTF_8));
        assertEquals(NativeWire.Presence.NULL,nullFields.error().presence());
        var opaque=original.deepCopy();opaque.put("result",17);
        assertEquals("17",new String(result(opaque).result().token().orElseThrow().value(),StandardCharsets.UTF_8));
    }
    private static NativeWire.CommandResult result(ObjectNode value)throws IOException {
        return (NativeWire.CommandResult)NativeWire.decode(NativeWire.packet(FullJsonTree.encode(value,MAX)));
    }
    private static void assertBad(ObjectNode value){assertThrows(IOException.class,()->result(value));}
    @Test void actualSerializerBytesReachTheOriginalAckAndColdChronologyConsumersWithoutResubmission()throws Exception {
        Oracle oracle=Oracle.open(temporary);
        String text=String.join("|",strings());
        for(boolean ok:List.of(false,true)){
            var endpoint=new Packets(oracle,text,ok);
            try(var transport=new NativeGameTransport(endpoint,configuration(),16,4)){
                Instant deadline=Instant.now().plusSeconds(60);
                var held=transport.observe(deadline);
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,transport.readCoreFrame(deadline));
                assertEquals(ok,ack.nativeOk());assertEquals(1,endpoint.writes);
                assertArrayEquals(endpoint.produced,ack.originalPacket());
                assertArrayEquals(endpoint.written,ack.outbound().orElseThrow().originalPacket());
                var decoded=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(ack.originalPacket()));
                assertArrayEquals(decoded.payload().value(),ack.originalFrame().bytes());
                if(ok){
                    assertArrayEquals(decoded.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes());
                    var result=NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes()));
                    assertEquals(text,NativeWire.text(result.get("status")));
                }else{
                    assertTrue(ack.originalResultToken().isEmpty());
                    assertEquals(text,NativeWire.text(NativeWire.parse(decoded.error().token().orElseThrow().value())));
                }
                var chronology=ack.custody().orElseThrow();chronology.verify(ack);
                var cold=NativeRequestChronologyCodec.decode(NativeRequestChronologyCodec.encode(chronology));
                assertEquals(chronology,cold);cold.verify(ack);
                assertArrayEquals(held.originalPacket(),transport.latestObservedSnapshot().orElseThrow().originalPacket());
                assertTrue(transport.pollOriginalOutcome(ack.requestId()).isEmpty());
                assertEquals(1,endpoint.writes,"reading the retained outcome must not resend an action");
            }
        }
    }
    private static NativePipeEndpoint.Config configuration(){
        String slash=Character.toString((char)92);
        return new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"serializer-interop","software-serializer-machine",
                new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"software-serializer-session","fixture",
                "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518","ck3-1.20.0.4-msvc-x64");
    }
    private static final class Packets implements NativePacketPort {
        private final ArrayDeque<byte[]> incoming=new ArrayDeque<>();
        private final Oracle oracle;private final String status;private final boolean ok;
        private int writes;private byte[] produced,written;
        private Packets(Oracle oracle,String status,boolean ok)throws IOException{
            this.oracle=oracle;this.status=status;this.ok=ok;
            var hello=StrictJson.object().put("protocol_version",1).put("type","hello").put("pid",42)
                    .put("connection_generation",1).put("bridge_version","fixture")
                    .put("expected_ck3_sha256",configuration().expectedGameSha256()).put("expected_ck3_version","1.20.0.4")
                    .put("game_adapter_id","ck3-1.20.0.4-msvc-x64").put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.set("capabilities",StrictJson.object().arrayNode().add("game.query.core-frame.v1"));
            incoming.add(NativeWire.packet(FullJsonTree.encode(hello,MAX)));
            var snapshot=StrictJson.object().put("protocol_version",1).put("type","state_snapshot")
                    .put("snapshot_id","serializer-interop").put("revision",9);
            var state=StrictJson.object().put("paused",true).put("map_ready",true).put("date_raw",1);
            state.set("played_character",StrictJson.object().put("character_id",73).put("alive",true));
            snapshot.set("state",state);incoming.add(NativeWire.packet(FullJsonTree.encode(snapshot,MAX)));
        }
        public void verify(){ }
        public void awaitConnection(Instant deadline){ }
        public byte[] readPacket(Instant deadline)throws IOException{
            if(incoming.isEmpty())throw new IOException("no actual producer response queued");return incoming.removeFirst();
        }
        public void writePacket(byte[] original,Instant deadline)throws IOException{
            writes++;if(writes!=1)throw new IOException("interop may submit its fixed read only once");
            written=original.clone();var request=NativeWire.decodeExecuteRequest(original);
            try{
                byte[] body=oracle.produce(new Case("actual-ack",request.requestId(),request.step(),status,ok));
                produced=NativeWire.packet(body);incoming.add(produced);
            }catch(InterruptedException interrupted){
                Thread.currentThread().interrupt();throw new IOException("actual serializer oracle interrupted",interrupted);
            }
        }
        public void close(){ }
    }
    /** Exact Root-produced test fixture DATA. This grants no native build or runtime qualification. */
    private record Manifest(String machineId,FileRef executable,FileRef header,FileRef entry,FileRef buildReceipt) { }
    private static final class Oracle {
        private final Manifest manifest;private final FileRef manifestRef;private final Path scratch;
        private final List<SharedSourceFiles.Witness> witnesses;private int invocation;
        private Oracle(Manifest manifest,FileRef manifestRef,Path scratch,List<SharedSourceFiles.Witness> witnesses){
            this.manifest=manifest;this.manifestRef=manifestRef;this.scratch=scratch;this.witnesses=List.copyOf(witnesses);
        }
        private static Oracle open(Path scratch)throws IOException {
            String path=required("xar.command.result.oracle.manifest");
            FileRef pin;
            try{pin=new FileRef(path,Long.parseLong(required("xar.command.result.oracle.bytes")),required("xar.command.result.oracle.sha256"));}
            catch(IllegalArgumentException invalid){throw new IOException("NOT_RUN_REQUIRED_ACTUAL_CPP_ORACLE: invalid exact manifest pin",invalid);}
            need(pin.bytes()>0&&pin.bytes()<=MAX,"bounded original oracle manifest required");
            var witnesses=new ArrayList<SharedSourceFiles.Witness>();retain(pin,witnesses);
            var root=StrictJson.parse(read(pin,MAX),MAX);
            StrictJson.object(root,Set.of("schema","machine_id","abi","executable","producer_header","oracle_entry","build_receipt"));
            need(StrictJson.text(root.get("schema")).equals("xar.cpp-command-result-frame-oracle/v1"),"exact actual oracle schema required");
            need(StrictJson.text(root.get("abi")).equals("stdin-le-u32-utf8-v1"),"exact binary stdin and JSON-LF stdout oracle required");
            String machine=StrictJson.text(root.get("machine_id"));
            need(machine.equals(WindowsJobProcess.currentMachineId()),"actual oracle belongs to another machine");
            var manifest=new Manifest(machine,file(root.get("executable"),16L<<20),file(root.get("producer_header"),4096),
                    file(root.get("oracle_entry"),8192),file(root.get("build_receipt"),MAX));
            need(manifest.header().bytes()==1392&&manifest.header().sha256().equals(HEADER_SHA),"actual shared producer header pin differs");
            need(manifest.entry().bytes()==1491&&manifest.entry().sha256().equals(ENTRY_SHA),"actual pure C++ oracle entry pin differs");
            need(Path.of(manifest.executable().path()).getFileName().toString().endsWith(".exe"),"actual direct compiled oracle executable required");
            for(FileRef source:List.of(manifest.executable(),manifest.header(),manifest.entry(),manifest.buildReceipt()))retain(source,witnesses);
            // Original Root compiler-stage DATA only. Its command/source/dependency/admission and
            // original custody remain Root acceptance; this receipt is no arbitrary-build authority.
            var terminal=ControlBuild.strictMapper().readValue(read(manifest.buildReceipt(),MAX),WindowsJobProcess.CommandResult.class);
            need(terminal.passed(),"Root actual compiler command did not naturally finish with its zero-member bounded Job");
            var oracle=new Oracle(manifest,pin,scratch,witnesses);oracle.requireCurrent();return oracle;
        }
        private byte[] produce(Case value)throws IOException,InterruptedException {
            requireCurrent();byte[] request=binary(value);
            Path call=Files.createDirectory(scratch.resolve("cpp-oracle-"+(++invocation))).toAbsolutePath();
            Path stdout=call.resolve("stdout.jsonl"),stderr=call.resolve("stderr.log");
            Instant deadline=Instant.now().plusSeconds(30);
            var command=new WindowsJobProcess.CommandSpec(Path.of(manifest.executable().path()),List.of(),call,
                    System.getenv(),stdout,stderr,256L<<20);
            var sources=List.of(manifestRef,manifest.header(),manifest.entry(),manifest.buildReceipt());
            WindowsJobProcess.StdioGuard guard=()->{
                requireCurrent();
                if(Files.exists(stdout))need(Files.size(stdout)<=MAX,"finite actual oracle stdout required");
                if(Files.exists(stderr))need(Files.size(stderr)<=4096,"finite actual oracle stderr required");
            };
            var spec=new WindowsJobProcess.OwnedStdioSpec(command,WindowsJobProcess.ConsoleMode.NO_WINDOW,
                    manifest.executable(),sources,deadline,MAX,32768,MAX,guard);
            try(var child=WindowsJobProcess.startOwnedStdio(spec)){
                var write=child.write(request,deadline);child.closeInput();
                var arrival=child.readLine(deadline);
                var terminal=child.awaitExit(call.resolve("job-diagnostic.json")).commandResult();
                need(terminal.passed(),"actual C++ serializer oracle command failed or did not drain");
                need(write.bytesWritten()==request.length&&write.identity().equals(arrival.identity())
                        &&write.sessionNonce().equals(arrival.sessionNonce())&&arrival.sequence()==1
                        &&arrival.identity().equals(terminal.identity()),"actual oracle stdin/stdout/terminal process custody differs");
                byte[] actual=arrival.rawBytes();
                need(actual.length>1&&actual[actual.length-1]==10,"actual JSON-LF serializer frame missing");
                assertArrayEquals(actual,Files.readAllBytes(stdout),"shared owned stdio audit must retain actual received bytes");
                guard.verify();return actual;
            }finally{requireCurrent();}
        }
        private void requireCurrent()throws IOException{
            for(var source:witnesses)SharedSourceFiles.assertUnchanged(source);
            need(manifest.machineId().equals(WindowsJobProcess.currentMachineId()),"oracle physical machine changed");
        }
        private static byte[] binary(Case value)throws IOException {
            var target=new ByteArrayOutputStream();
            string(target,value.request());string(target,value.step());target.write(value.ok()?1:0);string(target,value.status());
            return target.toByteArray();
        }
        private static void string(ByteArrayOutputStream target,String value)throws IOException{
            byte[] bytes=value.getBytes(StandardCharsets.UTF_8);need(bytes.length<=8192,"original finite C++ string bound required");
            target.write(ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).array());target.write(bytes);
        }
        private static FileRef file(JsonNode value,long maximum)throws IOException{
            StrictJson.object(value,Set.of("path","bytes","sha256"));
            var ref=new FileRef(StrictJson.text(value.get("path")),StrictJson.integer(value.get("bytes"),1,maximum),StrictJson.text(value.get("sha256")));
            need(Path.of(ref.path()).isAbsolute()&&Path.of(ref.path()).normalize().equals(Path.of(ref.path())),"exact absolute oracle source required");return ref;
        }
        private static void retain(FileRef ref,List<SharedSourceFiles.Witness> target)throws IOException{
            ref.verify();var observed=SharedSourceFiles.observe(Path.of(ref.path()));
            need(observed.source().bytes()==ref.bytes()&&observed.source().sha256().equals(ref.sha256()),"oracle source changed while acquiring custody");target.add(observed);
        }
        private static byte[] read(FileRef ref,int maximum)throws IOException{
            need(ref.bytes()>0&&ref.bytes()<=maximum,"bounded exact original oracle input required");
            try(var input=Files.newInputStream(Path.of(ref.path()))){
                byte[] raw=input.readNBytes(maximum+1);need(raw.length==ref.bytes(),"original oracle input size changed");ref.verify();return raw;
            }
        }
        private static String required(String name)throws IOException {
            String value=System.getProperty(name);
            if(value==null||value.isBlank())throw new IOException("NOT_RUN_REQUIRED_ACTUAL_CPP_ORACLE: "+name);
            return value;
        }
        private static void need(boolean condition,String reason)throws IOException{if(!condition)throw new IOException(reason);}
    }
}
