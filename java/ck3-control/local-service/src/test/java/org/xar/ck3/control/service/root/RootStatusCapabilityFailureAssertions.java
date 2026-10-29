package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Objects;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.nativebridge.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;

/** Original failure edges only. Controlled packet replay grants no Managed source scope, lease, Ready or successful provider. */
public final class RootStatusCapabilityFailureAssertions {
    private RootStatusCapabilityFailureAssertions() { }

    public static StatusCapabilityFailure fromOriginalHello(CommandOrigin origin, G2Source source,
            ExactRef originalHello, byte[] actualPacket) {
        Objects.requireNonNull(actualPacket);
        StatusCapabilityFailure failure = assertThrows(StatusCapabilityFailure.class,
                () -> StatusCapabilityFailure.requireAdvertised(origin, source, originalHello, actualPacket));
        assertSame(origin, failure.origin()); assertSame(source, failure.source());
        assertSame(originalHello, failure.originalHello());
        assertEquals("native DLL does not advertise required capability " + failure.requiredCapability(), failure.getMessage());
        return failure;
    }

    /** Controlled protocol/public-error regression only. The original Python send serializer frames
     * declared software packets; a real Java transport owns request/ACK chronology and archive custody.
     * No Managed Game, source qualification, Status handler reachability or business result is claimed. */
    public static PublicServiceFailure fromOriginalRejectedStatus(
            Path workRoot)throws Exception {
        Path work=Files.createDirectory(workRoot.resolve("status-protocol"));
        try(var actual=new ActionWriterIntegrationFixture(work.resolve("archive"),false)) {
            var framer=new OriginalFramer(work);
            var source=actual.observationSource();var game=actual.observationIdentity().game();
            String machine=source.machineId(),session="controlled-status-protocol-session";
            byte[] hello=framer.packet("{\"type\":\"hello\",\"protocol_version\":1,\"pid\":"+game.pid()
                    +",\"connection_generation\":1,\"bridge_version\":\"controlled-protocol\",\"expected_ck3_sha256\":\""+"0".repeat(64)
                    +"\",\"game_adapter_id\":\"controlled-protocol\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,"
                    +"\"capabilities\":[\"game.state.snapshot\",\""+PhysicalStatusIdentity.CAPABILITY+"\"]}");
            byte[] heartbeat=framer.packet("{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":1}");
            byte[] snapshot=framer.packet("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"protocol:7\","
                    +"\"revision\":7,\"state\":{\"date_raw\":1000,\"paused\":false}}");
            var config=new NativePipeEndpoint.Config(
                    "\\\\.\\pipe\\controlled-status-protocol",machine,game,session,"controlled-protocol","0".repeat(64),"controlled-protocol");
            var packets=new RejectedPackets(framer,hello,heartbeat,snapshot);
            return actual.withSoftwareProtocol(packets,config,transport->{
                Instant until=Instant.now().plusSeconds(30);
                var frame=transport.observe(until);
                var originalHello=actual.writer.locked(same->actual.archive.preserveArtifact(same,hello,
                        org.xar.ck3.control.application.readiness.ReadinessArchive.Role.HELLO.maximumBytes()));
                var originalHeartbeat=actual.writer.locked(same->actual.archive.preserveArtifact(same,heartbeat,
                        org.xar.ck3.control.application.readiness.ReadinessArchive.Role.HEARTBEAT.maximumBytes()));
                var originalSnapshot=actual.writer.locked(same->actual.archive.preserveArtifact(same,snapshot,
                        org.xar.ck3.control.application.readiness.ReadinessArchive.Role.NATIVE_PACKET.maximumBytes()));
                var qualification=actual.archive.preserveMaterial(new RawJson(
                        "{\"scope\":\"CONTROLLED_PROTOCOL_DATA_ONLY\"}".getBytes(StandardCharsets.UTF_8)));
                var epoch=actual.archive.preserveMaterial(new RawJson(
                        "{\"epoch\":\"CONTROLLED_PROTOCOL_DATA_ONLY\"}".getBytes(StandardCharsets.UTF_8)));
                var identity=new PhysicalStatusIdentity(frame.session(),frame.snapshotId(),
                        frame.nativeRevision(),source,originalSnapshot,originalHello,originalHeartbeat,qualification,epoch,frame.observedAt());
                var origin=new CommandOrigin.PhysicalStatusOnly(identity);
                var operation=new OperationKey(PhysicalStatusIdentity.OPERATION);
                var contract=new ReadContract<RawJson>(
                        PhysicalStatusIdentity.CONTRACT_ID,operation,Optional.of(PhysicalStatusIdentity.CAPABILITY),
                        PhysicalStatusIdentity.PERMISSION,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                        ReadContract.WireProfile.EXECUTE_STEP,
                        ReadContract.GuardMode.STATUS_ONLY,source.sourceRef(),
                        (request,id)->new NativeRequest(operation.value(),PhysicalStatusIdentity.CAPABILITY,
                                new RawJson(new byte[]{'{','}'})),
                        receipt->{throw new AssertionError("protocol rejection cannot become Known");});
                var request=PlanningReadRequest.newStatusOnly(identity,operation,
                        new OpportunityJson.Obj(Map.of()),until);
                var guard=new GuardEvidence(origin,source,session,identity.connectionGeneration(),
                        operation,originalSnapshot,originalHello,"controlled-protocol-data-only",frame.observedAt(),until,List.of(qualification,epoch));
                var readGuard=new PlanningReadGuard(guard,
                        new PlanningReadGuard.PhysicalStatus(identity),qualification.sha256());
                var reads=new PlanningReadCoordinator(List.of(contract),actual.journal,(head,requested,installed)->{
                    assertSame(contract,installed);assertSame(request,requested);return readGuard;
                },transport,actual.archive,java.time.Clock.systemUTC());
                var head=actual.writer.locked(same->same.head());
                var result=reads.read(contract,request);
                if(!(result instanceof PlanningReadResult.Unavailable<RawJson> unavailable))
                    throw new AssertionError("controlled native false ACK must remain unavailable");
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original().orElseThrow());
                assertFalse(ack.nativeOk());assertEquals(1,packets.writes);
                ack.custody().orElseThrow().verify(ack);
                assertEquals(transport.originalRequestChronology(ack.requestId()).orElseThrow(),ack.custody().orElseThrow());
                assertArrayEquals(packets.outbound,ack.outbound().orElseThrow().originalPacket());
                return actual.writer.locked(same->{
                    var archive=actual.archive.withSession(same);
                    var failure=assertThrows(PublicServiceFailure.class,
                            ()->RootDriverTransportPublicSupplier.sentinelUnavailable(unavailable,request,archive));
                    assertEquals(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED,failure.kind());
                    var reference=failure.originalCandidate().orElseThrow();
                    var retained=assertInstanceOf(NativeActionPort.AckReceived.class,archive.load(reference));
                    assertEquals(ack,retained);assertFalse(retained.nativeOk());retained.custody().orElseThrow().verify(retained);
                    assertEquals(reference,archive.referenceOf(retained));
                    var raw=(NativeWire.CommandResult)NativeWire.decode(retained.originalPacket());
                    var error=NativeWire.parse(raw.error().token().orElseThrow().value());
                    assertTrue(error.isTextual(),"the controlled original framing producer retained the string rejection");
                    assertFalse(NativeWire.object(NativeWire.parse(raw.payload().value())).has("typed_query_failure_v1"));
                    assertEquals("native gameplay step failed: "+error.textValue(),failure.getMessage());
                    var outgoing=NativeWire.decodeExecuteRequest(retained.outbound().orElseThrow().originalPacket());
                    assertEquals(PhysicalStatusIdentity.OPERATION,outgoing.step());assertEquals(Optional.of(frame.nativeRevision()),outgoing.expectedRevision());
                    assertEquals(game,retained.custody().orElseThrow().session().game());assertEquals(1,packets.writes);
                    assertEquals(0,actual.nativeActionWrites());
                    var after=same.head();assertEquals(head.digest(),after.digest());assertEquals(head.documents(),after.documents());
                    assertEquals(head.absent(),after.absent());assertEquals(head.indexRepairs(),after.indexRepairs());
                    assertEquals(head.snapshotNeedsRecovery(),after.snapshotNeedsRecovery());return failure;
                });
            });
        }
    }
    private static final class RejectedPackets implements NativePacketPort {
        private final OriginalFramer framer;
        private final ArrayDeque<byte[]> packets=new ArrayDeque<>();
        private int writes;private byte[] outbound;
        RejectedPackets(OriginalFramer framer,byte[]... original) {
            this.framer=framer;for(byte[] packet:original)packets.addLast(packet.clone());
        }
        @Override public void verify(){ }
        @Override public void awaitConnection(Instant deadline){ }
        @Override public byte[] readPacket(Instant deadline)throws IOException {
            if(packets.isEmpty())throw new IOException("controlled protocol packets exhausted");return packets.removeFirst().clone();
        }
        @Override public void writePacket(byte[] original,Instant deadline)throws IOException {
            if(++writes!=1)throw new IOException("controlled protocol request cannot replay");
            outbound=original.clone();
            var request=NativeWire.decodeExecuteRequest(original);
            assertEquals(PhysicalStatusIdentity.OPERATION,request.step());
            try { packets.addLast(framer.packet("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+request.requestId()
                    +"\",\"ok\":false,\"error\":\"controlled protocol rejection\"}")); }
            catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("original protocol framer interrupted; no replay",interrupted);}
            catch(IOException failure){throw failure;}
            catch(Exception failure){throw new IOException("original protocol framer failed; no replay",failure);}
        }
        @Override public void close(){ }
    }
    /** The unchanged NativeOriginalProducerTest send AST oracle, transported as base64 on Windows. */
    private static final class OriginalFramer {
        private final Path work;private int sequence;
        OriginalFramer(Path work){this.work=work;}
        byte[] packet(String frame)throws Exception {
            String python=required("xar.native.producer.python"),source=required("xar.native.producer.source"),
                    sha=required("xar.native.producer.sha256");
            if(!Path.of(python).isAbsolute()||!Path.of(source).isAbsolute()||!sha.matches("[a-f0-9]{64}"))
                throw new IOException("pinned absolute original framing inputs required");
            var witness=SharedSourceFiles.observe(Path.of(source));
            if(!witness.source().sha256().equals(sha))throw new IOException("original framing source drift");
            String program="""
                    import ast,base64,hashlib,json,struct,sys,threading,types
                    from pathlib import Path
                    source=Path(sys.argv[1]).read_bytes()
                    if hashlib.sha256(source).hexdigest()!=sys.argv[2]: raise RuntimeError('original Native producer source drift')
                    tree=ast.parse(source.decode('utf-8-sig'))
                    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NativeNamedPipeServer')
                    send=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='send')
                    captured=[]
                    def capture(handle,packet):
                        captured.append(packet)
                        return True
                    scope={'json':json,'struct':struct,'MAXIMUM_FRAME_BYTES':64*1024*1024,'_write_all':capture,'BridgeUnavailableError':RuntimeError}
                    future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
                    module=ast.fix_missing_locations(ast.Module(body=[future,send],type_ignores=[]))
                    exec(compile(module,str(Path(sys.argv[1])),'exec'),scope)
                    frame=json.loads(base64.b64decode(sys.argv[3]))
                    if sys.argv[4]=='large': frame['state']['large_native_field']='x'*(1048576+17)
                    owner=types.SimpleNamespace(_write_lock=threading.Lock(),_current_handle=lambda:1)
                    scope['send'](owner,frame)
                    if len(captured)!=1: raise RuntimeError('original producer did not make exactly one packet attempt')
                    sys.stdout.buffer.write(base64.b64encode(captured[0]))
                    """;
            String encoded=Base64.getEncoder().encodeToString(program.getBytes(StandardCharsets.UTF_8));
            String command="import base64;exec(compile(base64.b64decode('"+encoded+"'),'<original-native-send>','exec'))";
            Path output=work.resolve("original-frame-"+(++sequence)+".base64"),error=work.resolve("original-frame-"+sequence+".stderr");
            var builder=new ProcessBuilder(python,"-X","utf8","-c",command,source,sha,
                    Base64.getEncoder().encodeToString(frame.getBytes(StandardCharsets.UTF_8)),"small")
                    .redirectOutput(output.toFile()).redirectError(error.toFile());
            builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
            var child=builder.start();
            try {
                if(!child.waitFor(20,TimeUnit.SECONDS)) {
                    child.destroyForcibly();child.waitFor(2,TimeUnit.SECONDS);
                    throw new IOException("original framing process timed out; no replay");
                }
                if(child.exitValue()!=0)throw new IOException("original framing process failed: "+Files.readString(error));
                if(Files.size(output)>65536)throw new IOException("bounded original framing output exceeded");
                return Base64.getDecoder().decode(Files.readAllBytes(output));
            } finally {
                if(child.isAlive()){child.destroyForcibly();child.waitFor(2,TimeUnit.SECONDS);}
                SharedSourceFiles.assertUnchanged(witness);
            }
        }
        private static String required(String key) {
            String value=System.getProperty(key);
            if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_ORIGINAL_NATIVE_FRAMER: "+key);return value;
        }
    }
}
