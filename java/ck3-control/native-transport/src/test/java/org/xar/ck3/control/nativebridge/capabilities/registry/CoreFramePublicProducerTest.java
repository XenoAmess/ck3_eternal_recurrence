package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.nativebridge.NativeTransportReplayTestFactory;
import org.xar.ck3.control.nativebridge.NativePacketPort;
import org.xar.ck3.control.nativebridge.NativePipeEndpoint;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Real frozen compatibility producers -> offline pipe packets -> transport -> typed public registry/encoder.
 * No test Root, Game authority, profile qualification or private episode token is manufactured.
 */
final class CoreFramePublicProducerTest {
    @TempDir Path temporary;
    private int sequence;
    private static final String CONTRACT_SHA="c8b6798113e87d5f8141eb13b318a5f7e88855f99eecbc63d215211c6462f42e";
    private static final String IDENTITY_SHA="9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086";
    private static final String ORIGINAL_PRODUCER="""
        import ast,base64,hashlib,importlib.util,json,struct,sys,threading,types
        from pathlib import Path
        source=Path(sys.argv[1]); body=source.read_bytes()
        if hashlib.sha256(body).hexdigest()!=sys.argv[2]: raise RuntimeError('original Native send source drift')
        package=types.ModuleType('original_core'); package.__path__=[str(source.parent)]; sys.modules['original_core']=package
        for leaf,sha in [('version_identity',sys.argv[3]),('core_frame_contract',sys.argv[4])]:
            path=source.with_name(leaf+'.py')
            if hashlib.sha256(path.read_bytes()).hexdigest()!=sha: raise RuntimeError('original core contract source drift')
            spec=importlib.util.spec_from_file_location('original_core.'+leaf,path)
            module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)
        value=json.loads(base64.b64decode(sys.argv[5]))
        if sys.argv[6]=='normalize':
            normalized=sys.modules['original_core.core_frame_contract'].normalize_core_frame_v1(value)
            sys.stdout.buffer.write(json.dumps(normalized,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
        else:
            tree=ast.parse(body.decode('utf-8-sig')); cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NativeNamedPipeServer')
            send=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='send'); captured=[]
            def write(handle,packet): captured.append(packet); return True
            scope={'json':json,'struct':struct,'MAXIMUM_FRAME_BYTES':64*1024*1024,'_write_all':write,'BridgeUnavailableError':RuntimeError}
            future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
            exec(compile(ast.fix_missing_locations(ast.Module(body=[future,send],type_ignores=[])),str(source),'exec'),scope)
            scope['send'](types.SimpleNamespace(_write_lock=threading.Lock(),_current_handle=lambda:1),value)
            if len(captured)!=1: raise RuntimeError('original send must write exactly one packet')
            sys.stdout.buffer.write(base64.b64encode(captured[0]))
        """;

    @Test void originalAvailablePrefixFeedsTheTypedServiceAndKeepsCompleteSnapshotFalse() throws Exception {
        var original=normalize(partial());var port=new Replay(original,false);port.packets.add(send(hello(true)));
        try(var transport=NativeTransportReplayTestFactory.create(port,config(),16,16)) {
            var registry=new PublicBindings();var binding=registry.register(PublicMethod.QUERY_CORE_FRAME_V1,CoreFramePublicCodec.Request.class,CoreFrame.class,
                    request->{try{return CoreFramePublicCodec.decodeOutcome(transport.readCoreFrame(Instant.now().plusSeconds(15)));}
                        catch(IOException failure){throw new UncheckedIOException(failure);}},CoreFramePublicCodec::decodeArguments,CoreFramePublicCodec::encode,
                    new PublicRoutes.Target(CoreFramePublicCodec.class.getName(),"decodeOutcome",new ExactRef("fixture/core-codec.java",1,"0".repeat(64))),
                    PublicRoutes.Status.IMPLEMENTED,"offline real native/public compatibility codecs only");
            assertFalse(registry.frozen());registry.freeze(Set.of(PublicMethod.QUERY_CORE_FRAME_V1));
            RawJson actual=binding.invoke(new PublicBindings.Value(raw("{}")));
            assertEquals(RegistryJson.object(original),RegistryJson.object(actual));assertFalse(RegistryJson.object(actual).get("complete_snapshot").booleanValue());
            var prefix=assertInstanceOf(CoreFrame.Partial.class,CoreFrame.decode(actual)).prefix();
            assertEquals(Integer.MIN_VALUE,prefix.localPlayerId());assertEquals(Integer.MIN_VALUE+1,prefix.playedCharacterId());
            assertEquals(1,port.writes);assertEquals(2,port.reads);assertTrue(transport.latestObservedSnapshot().isEmpty());
        }
    }

    @Test void originalUnavailablePrefixRetainsReasonAndExplicitNulls() throws Exception {
        var original=normalize(unavailable());var port=new Replay(original,false);port.packets.add(send(hello(true)));
        try(var transport=NativeTransportReplayTestFactory.create(port,config(),16,16)) {
            var actual=CoreFramePublicCodec.decodeOutcome(transport.readCoreFrame(Instant.now().plusSeconds(15)));
            assertEquals(new CoreFrame.Unavailable(true,"core_prefix_unavailable"),actual);
            assertEquals(RegistryJson.object(original),RegistryJson.object(CoreFramePublicCodec.encode(actual)));
            assertEquals(1,port.writes);assertTrue(transport.latestObservedSnapshot().isEmpty());
        }
    }

    @Test void missingActualProfileAndUnknownResultCannotBecomeAPartialOrRetry() throws Exception {
        var original=normalize(partial());var missing=new Replay(original,false);missing.packets.add(send(hello(false)));
        try(var transport=NativeTransportReplayTestFactory.create(missing,config(),16,16)) {
            var refused=transport.readCoreFrame(Instant.now().plusSeconds(15));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,refused);
            assertThrows(IOException.class,()->CoreFramePublicCodec.decodeOutcome(refused));assertEquals(0,missing.writes);
        }
        var lost=new Replay(original,true);lost.packets.add(send(hello(true)));
        try(var transport=NativeTransportReplayTestFactory.create(lost,config(),16,16)) {
            var unknown=transport.readCoreFrame(Instant.now().plusSeconds(15));
            assertInstanceOf(NativeActionPort.Unknown.class,unknown);
            assertThrows(IOException.class,()->CoreFramePublicCodec.decodeOutcome(unknown));assertEquals(1,lost.writes);
        }
    }

    @Test void originalPacketBindingAndProfileAreCheckedBeforePublicNormalization() throws Exception {
        var original=normalize(partial());var port=new Replay(original,false);port.packets.add(send(hello(true)));
        try(var transport=NativeTransportReplayTestFactory.create(port,config(),16,16)) {
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,transport.readCoreFrame(Instant.now().plusSeconds(15)));
            var wrongResult=new NativeActionPort.AckReceived(ack.requestId(),ack.nativeOk(),Optional.of(raw(unavailable())),ack.originalFrame(),ack.originalPacket(),ack.outbound(),ack.custody());
            assertThrows(IOException.class,()->CoreFramePublicCodec.decodeOutcome(wrongResult));
            byte[] request=NativeWire.execute(ack.requestId(),"query-frontend-gui-route-v1",BigInteger.ZERO,bytes("{}"));
            var wrongStep=new NativeActionPort.AckReceived(ack.requestId(),ack.nativeOk(),ack.originalResultToken(),ack.originalFrame(),ack.originalPacket(),Optional.of(new NativeActionPort.OutboundPacket(ack.requestId(),request)));
            assertThrows(IOException.class,()->CoreFramePublicCodec.decodeOutcome(wrongStep));
        }
        for(String bad:List.of(partial().replace("\"complete_snapshot\":false","\"complete_snapshot\":true"),
                partial().replace("1.20.0.4","1.20.0.3"),partial().replace("\"speed\":3","\"speed\":true"),
                partial().replace("\"speed\":3","\"speed\":3.0"),partial().replace("\"speed\":3","\"speed\":null"),
                partial().replace("\"speed\":3,",""),partial().replace("\"speed\":3","\"speed\":3,\"extra\":null"),
                unavailable().replace("\"date_raw\":null","\"date_raw\":0")))
            assertThrows(IllegalArgumentException.class,()->CoreFrame.decode(raw(bad)));
    }

    @Test void noArgumentContractAcceptsMissingNullAndEmptyObjectButRejectsEveryNamedArgument() {
        for(var accepted:List.<PublicBindings.Arguments>of(new PublicBindings.Missing(),new PublicBindings.Null(),new PublicBindings.Value(raw("{}"))))
            assertEquals(CoreFramePublicCodec.Request.INSTANCE,CoreFramePublicCodec.decodeArguments(accepted));
        for(String rejected:List.of("{\"expected_revision\":0}","{\"unused\":null}","[]","false","0","\"x\""))
            assertThrows(IllegalArgumentException.class,()->CoreFramePublicCodec.decodeArguments(new PublicBindings.Value(raw(rejected))));
    }

    private final class Replay implements NativePacketPort {
        private final ArrayDeque<byte[]> packets=new ArrayDeque<>();private final RawJson result;private final boolean loseResult;private int writes,reads;
        Replay(RawJson result,boolean loseResult){this.result=result;this.loseResult=loseResult;}
        @Override public void verify() { }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public byte[] readPacket(Instant deadline)throws IOException {reads++;if(packets.isEmpty())throw new IOException("offline original result lost");return packets.removeFirst();}
        @Override public void writePacket(byte[] packet,Instant deadline)throws IOException {
            writes++;var request=NativeWire.decodeExecuteRequest(packet);
            assertEquals(CoreFrame.STEP,request.step());assertEquals(Optional.of(BigInteger.ZERO),request.expectedRevision());
            assertTrue(request.expectedSnapshotRevision().isEmpty());assertTrue(RegistryJson.object(new RawJson(request.normalizedAdditionalFields().value())).isEmpty());
            if(!loseResult)try{packets.add(send("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+request.requestId()+"\",\"ok\":true,\"result\":"+new String(result.bytes(),StandardCharsets.UTF_8)+"}"));}
                catch(Exception failure){throw new IOException("original producer failed",failure);}
        }
        @Override public void close() { }
    }
    private RawJson normalize(String value)throws Exception{return new RawJson(producer(value,"normalize"));}
    private byte[] send(String value)throws Exception{return Base64.getDecoder().decode(producer(value,"send"));}
    private byte[] producer(String value,String mode)throws Exception {
        String python=required("xar.native.producer.python"),source=required("xar.native.producer.source"),sha=required("xar.native.producer.sha256");
        if(!Path.of(python).isAbsolute()||!Path.of(source).isAbsolute()||!sha.matches("[0-9a-f]{64}"))throw new IllegalStateException("original pinned source/interpreter required");
        Path output=temporary.resolve("core-producer-"+(++sequence)+".out"),error=temporary.resolve("core-producer-"+sequence+".err");
        Process process=new ProcessBuilder(python,"-X","utf8","-c",ORIGINAL_PRODUCER,source,sha,IDENTITY_SHA,CONTRACT_SHA,Base64.getEncoder().encodeToString(bytes(value)),mode)
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if(!process.waitFor(20,TimeUnit.SECONDS)){process.destroyForcibly();throw new IOException("original core producer timed out");}
        if(process.exitValue()!=0)throw new IOException("original core producer failed: "+Files.readString(error,StandardCharsets.UTF_8));return Files.readAllBytes(output);
    }
    private static String required(String name){String value=System.getProperty(name);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN: required original producer property missing: "+name);return value;}
    private static NativePipeEndpoint.Config config(){return new NativePipeEndpoint.Config("\\\\.\\pipe\\core-frame-offline-fixture","fixture-machine",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"fixture-session","fixture",RegistryJson.EXE,"ck3-1.20.0.4-msvc-x64");}
    private static String hello(boolean profile){return "{\"type\":\"hello\",\"protocol_version\":1,\"pid\":42,\"connection_generation\":1,\"bridge_version\":\"fixture\",\"expected_ck3_sha256\":\""+RegistryJson.EXE+"\",\"expected_ck3_version\":\"1.20.0.4\",\"game_adapter_id\":\"ck3-1.20.0.4-msvc-x64\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":"+(profile?"[\"game.query.core-frame.v1\"]":"[]")+"}";}
    private static String base(){return "\"schema\":\"ck3_12004_core_frame_v1\",\"game_version\":\"1.20.0.4\",\"executable_sha256\":\""+RegistryJson.EXE+"\",\"adapter_id\":\"ck3-1.20.0.4-msvc-x64\",\"backend\":\"ck3-1.20.0.4-native-headless-main-thread\",\"complete_snapshot\":false,\"excluded_snapshot_families\":[\"treasury\",\"domain\",\"military\",\"campaign\"],";}
    private static String partial(){return "{"+base()+"\"status\":\"partial\",\"core_available\":true,\"application_main_observed\":true,\"unavailable_reason\":null,\"date_raw\":53144328,\"speed\":3,\"paused\":true,\"local_player_id\":-2147483648,\"map_ready\":true,\"has_played_character\":true,\"played_character_id\":-2147483647,\"played_character_alive\":true}";}
    private static String unavailable(){return "{"+base()+"\"status\":\"unavailable\",\"core_available\":false,\"application_main_observed\":true,\"unavailable_reason\":\"core_prefix_unavailable\",\"date_raw\":null,\"speed\":null,\"paused\":null,\"local_player_id\":null,\"map_ready\":null,\"has_played_character\":null,\"played_character_id\":null,\"played_character_alive\":null}";}
    private static RawJson raw(String value){return new RawJson(bytes(value));}
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
}
