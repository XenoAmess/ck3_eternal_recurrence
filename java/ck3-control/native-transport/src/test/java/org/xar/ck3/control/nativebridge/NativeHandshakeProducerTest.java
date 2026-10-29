package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

/** Actual software endpoint and original Python orchestration. No actual pipe/Game/Driver admission is claimed. */
final class NativeHandshakeProducerTest {
    @TempDir Path temporary;
    private static final String SHA="0".repeat(64);
    private static final String HELLO="{\"type\":\"hello\",\"protocol_version\":1,\"pid\":42,\"connection_generation\":18446744073709551615,\"bridge_version\":\"fixture\",\"expected_ck3_sha256\":\""+SHA+"\",\"game_adapter_id\":\"fixture\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\"]}";
    private static final String STATE="{\"date_raw\":1234,\"speed\":1,\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":73,\"alive\":true},\"active_event\":null,\"pending_character_interaction\":null,\"one_life_settlement\":null,\"played_character_gold\":0,\"played_character_prestige\":0,\"played_character_piety\":0,\"history\":[],\"active_wars\":[],\"player_armies\":[]}";
    @Test void actualOncePingDoesNotWaitForPongAndFirstSnapshotMayPrecedeTheOriginalMatchingPong()throws Exception {
        Replay port=new Replay();port.add(HELLO);port.add(snapshot("first"));try(var transport=transport(port)) {
            assertTrue(transport.handshakeDiagnostics().attempt().isEmpty());transport.awaitHello(deadline());
            var attempt=transport.startHandshake(deadline());assertEquals(NativeGameTransport.PingWriteState.RETURNED,attempt.writeState());
            assertEquals(1,port.written.size());assertTrue(transport.handshakeDiagnostics().pong().isEmpty(),"a successful write is not a PONG");
            var first=transport.observe(deadline());assertEquals("first",first.snapshotId());
            assertTrue(transport.handshakeDiagnostics().pong().isEmpty(),"Python does not gate first snapshot on PONG");
            byte[] originalPong=packet(pong(attempt.requestId(),"42"));port.add(originalPong);port.add(snapshot("next"));transport.observe(deadline());
            var actual=transport.handshakeDiagnostics().pong().orElseThrow();
            assertEquals(attempt.session(),actual.session());assertEquals(attempt.custodyEpoch(),actual.custodyEpoch());assertEquals(attempt.requestId(),actual.requestId());
            assertArrayEquals(originalPong,actual.originalPong().original().packet().value());
            assertTrue(actual.received().order().compareTo(attempt.writeCompleted().orElseThrow().order())>0);
            assertSame(attempt,transport.startHandshake(deadline()));assertEquals(1,port.written.size());
            int reads=port.reads;for(int i=0;i<50;i++)transport.handshakeDiagnostics();assertEquals(reads,port.reads);assertEquals(1,port.written.size());
            byte[] changed=attempt.originalPacket().value();changed[4]^=1;assertArrayEquals(port.written.get(0),attempt.originalPacket().value());
            assertEquals(new BigInteger("18446744073709551615"),actual.session().connectionGeneration());
        }
    }
    @Test void unrelatedPongIsOnlyRawDiagnosticAndIdenticalOriginalDuplicateCannotReplaceFirstCustody()throws Exception {
        Replay port=new Replay();port.add(HELLO);try(var transport=transport(port)) {
            transport.awaitHello(deadline());
            var attempt=transport.startHandshake(deadline());port.add(pong("another-original-id","42"));port.add(snapshot("one"));transport.observe(deadline());
            assertTrue(transport.diagnostics().latestPong().isPresent());assertTrue(transport.handshakeDiagnostics().pong().isEmpty());
            String response=pong(attempt.requestId(),"42");port.add(response);port.add(snapshot("two"));transport.observe(deadline());
            var first=transport.handshakeDiagnostics().pong().orElseThrow();port.add(response);port.add(snapshot("three"));transport.observe(deadline());
            assertSame(first,transport.handshakeDiagnostics().pong().orElseThrow());assertEquals(1,port.written.size());
        }
    }
    @Test void matchingPongRequiresExactActualPidAndRejectsBoolFloatMissingOrConflictingOriginals()throws Exception {
        for(String pid:List.of("43","true","42.0","null","missing")) {
            Replay port=new Replay();port.add(HELLO);try(var transport=transport(port)) {
                transport.awaitHello(deadline());
                var attempt=transport.startHandshake(deadline());String response=pid.equals("missing")?pong(attempt.requestId(),"42").replace(",\"pid\":42",""):pong(attempt.requestId(),pid);
                byte[] invalid=packet(response);port.add(invalid);
                assertThrows(UncheckedIOException.class,()->transport.observe(deadline()));assertTrue(transport.handshakeDiagnostics().pong().isEmpty());
                assertEquals(NativeGameTransport.ReceivedState.TERMINAL,transport.diagnostics().receivedState());assertArrayEquals(invalid,transport.lastOriginalPacket());
                assertThrows(IOException.class,()->transport.startHandshake(deadline()));assertEquals(1,port.written.size());
            }
        }
        Replay port=new Replay();port.add(HELLO);try(var transport=transport(port)) {
            transport.awaitHello(deadline());
            var attempt=transport.startHandshake(deadline());port.add(pong(attempt.requestId(),"42"));port.add(snapshot("accepted"));transport.observe(deadline());
            var first=transport.handshakeDiagnostics().pong().orElseThrow();
            port.add(pong(attempt.requestId(),"42").replace("}",",\"conflicting\":true}"));
            assertThrows(UncheckedIOException.class,()->transport.observe(deadline()));assertSame(first,transport.handshakeDiagnostics().pong().orElseThrow());
        }
    }
    @Test void realWriteFailureOrInterruptionRetainsOriginalUnknownAndCannotResumeOrResendAfterLatePong()throws Exception {
        for(Failure mode:List.of(Failure.IO,Failure.INTERRUPTED,Failure.ZERO_PREFIX,Failure.PARTIAL_WRITE,Failure.POST_VERIFY)) {
            Replay port=new Replay();port.failure=mode;port.add(HELLO);try(var transport=transport(port)) {
                transport.awaitHello(deadline());
                if(mode==Failure.INTERRUPTED)assertThrows(InterruptedException.class,()->transport.startHandshake(deadline()));
                else assertThrows(IOException.class,()->transport.startHandshake(deadline()));
                var attempt=transport.handshakeDiagnostics().attempt().orElseThrow();
                assertEquals(mode==Failure.POST_VERIFY?NativeGameTransport.PingWriteState.RETURNED:NativeGameTransport.PingWriteState.UNKNOWN,attempt.writeState());
                assertTrue(attempt.failure().isPresent());assertTrue(transport.handshakeDiagnostics().pong().isEmpty());
                port.failure=Failure.NONE;assertThrows(IOException.class,()->transport.startHandshake(deadline()));assertEquals(1,port.written.size());
                assertEquals(NativeGameTransport.ReceivedState.TERMINAL,transport.diagnostics().receivedState());
                int reads=port.reads;port.add(pong(attempt.requestId(),"42"));port.add(snapshot("late"));
                assertThrows(UncheckedIOException.class,()->transport.observe(deadline()));assertEquals(reads,port.reads);
                assertEquals(attempt,transport.handshakeDiagnostics().attempt().orElseThrow());assertTrue(transport.handshakeDiagnostics().pong().isEmpty());
                assertEquals(1,port.written.size(),"a disconnected original session cannot silently resume or resend");
            }
        }
    }
    @Test void expiredOriginalDeadlineDoesNotClaimOrWriteAPingAndDoesNotAllocateAnImplicitFreshDeadline()throws Exception {
        Replay port=new Replay();port.add(HELLO);try(var transport=transport(port)) {
            assertThrows(IOException.class,()->transport.startHandshake(Instant.EPOCH));
            assertTrue(transport.handshakeDiagnostics().attempt().isEmpty());assertTrue(port.written.isEmpty());assertEquals(0,port.reads);
            assertThrows(IOException.class,()->transport.startHandshake(deadline()),"start must not implicitly read HELLO before caller adoption guards");
            assertEquals(0,port.reads);transport.awaitHello(deadline());
            Instant actual=deadline();transport.startHandshake(actual);assertEquals(actual,port.actualWriteDeadline);assertEquals(1,port.written.size());
        }
    }
    @Test void typedAdoptionRefusalHasZeroPingAndConcurrentSuccessfulCallersShareExactlyOneAttempt()throws Exception {
        for(var reason:NativeTransportDiagnostics.AdoptionRefusalReason.values()) {
            Replay port=new Replay();port.add(HELLO);try(var transport=transport(port)) {
                transport.awaitHello(deadline());transport.recordAdoptionRefused(reason,"ActualTypedFixtureRefusal","original refusal");
                assertThrows(IOException.class,()->transport.startHandshake(deadline()));assertTrue(port.written.isEmpty());assertTrue(transport.handshakeDiagnostics().attempt().isEmpty());
            }
        }
        Replay port=new Replay();port.add(HELLO);try(var transport=transport(port)) {
            transport.awaitHello(deadline());
            var pool=Executors.newFixedThreadPool(4);try {
                var calls=new ArrayList<java.util.concurrent.Callable<String>>();for(int i=0;i<8;i++)calls.add(()->transport.startHandshake(deadline()).requestId());
                String first=null;for(var result:pool.invokeAll(calls,10,TimeUnit.SECONDS)){String id=result.get(10,TimeUnit.SECONDS);if(first==null)first=id;else assertEquals(first,id);}
            }finally{pool.shutdownNow();assertTrue(pool.awaitTermination(10,TimeUnit.SECONDS));}
            assertEquals(1,port.written.size());var request=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(port.written.get(0),4,port.written.get(0).length)));
            assertEquals("ping",request.get("type").textValue());assertEquals(3,request.size());assertFalse(request.has("step"));assertFalse(request.has("expected_revision"));
        }
    }
    private static final String ORIGINAL="""
        import ast,copy,hashlib,json,sys,threading,types,uuid
        from pathlib import Path
        path=Path(sys.argv[1]);driver=path.with_name('driver.py')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=sys.argv[2]:raise RuntimeError('original Native Driver source drift')
        if hashlib.sha256(driver.read_bytes()).hexdigest()!='eed449063debf1a84216a350f0178d64a9a6602bbfcc266298a810a9bb736fb6':raise RuntimeError('original Driver error contract drift')
        def cls(p,name):
            return next(n for n in ast.parse(p.read_text(encoding='utf-8-sig')).body if isinstance(n,ast.ClassDef) and n.name==name)
        def method(owner,name):
            return next(n for n in cls(path,owner).body if isinstance(n,ast.FunctionDef) and n.name==name)
        scope={'copy':copy,'threading':threading,'uuid':uuid,'PROTOCOL_VERSION':1}
        def install(node):
            future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
            exec(compile(ast.fix_missing_locations(ast.Module(body=[future,node],type_ignores=[])),str(path),'exec'),scope)
        install(cls(driver,'BridgeUnavailableError'))
        install(cls(path,'_NativeBridgeAdoptionRefusedError'))
        state_class=cls(path,'NativeProtocolState');state_class.body=[method('NativeProtocolState',name) for name in ['__init__','ingest','mark_disconnected']]
        install(state_class);install(method('NativeHeadlessGameplayDriver','_ingest'))
        hello=json.loads(sys.argv[3]);results=[]
        # Only adoption outcomes are injected. Original init/ingest/orchestration and emitted packet are executed.
        for reason in [None,'invalid_driver_journal','active_driver_journal_requires_consolidation','legacy_lifecycle_incompatible','persisted_lifecycle_mismatch','send_failure']:
            events=[];sent=[];state=scope['NativeProtocolState']('fixture')
            def adopt(pid):
                events.append('adopt')
                if reason and reason!='send_failure':raise scope['_NativeBridgeAdoptionRefusedError']('actual fixture outcome',reason=reason,attempted_bridge_pid=pid)
            def send(frame):
                events.append('ping');sent.append(frame)
                if reason=='send_failure':raise scope['BridgeUnavailableError']('actual fixture send failure')
            def disconnect():events.append('disconnect');state.mark_disconnected()
            actual=types.SimpleNamespace(state=state,_request_sequence=0,_adopt_bridge_session=adopt,endpoint=types.SimpleNamespace(send=send),_mark_bridge_disconnected_v1=disconnect)
            try:scope['_ingest'](actual,hello)
            except scope['_NativeBridgeAdoptionRefusedError']:pass
            if reason=='send_failure':
                if events!=['adopt','ping','disconnect'] or len(sent)!=1 or state._connected:raise RuntimeError('original failed ping did not disconnect')
            elif reason:
                if events!=['adopt'] or sent:raise RuntimeError('refused original adoption emitted ping')
            else:
                if events!=['adopt','ping'] or len(sent)!=1 or set(sent[0])!={'type','protocol_version','request_id'}:raise RuntimeError('original once ping order/body differs')
                if sent[0]['type']!='ping' or sent[0]['protocol_version']!=1:raise RuntimeError('original ping envelope differs')
                if state._last_pong is not None:raise RuntimeError('original write invented a PONG')
                scope['_ingest'](actual,{'type':'pong','protocol_version':1,'request_id':sent[0]['request_id'],'pid':hello['pid']})
                if len(sent)!=1 or state._last_pong['request_id']!=sent[0]['request_id']:raise RuntimeError('original PONG did not remain an asynchronous diagnostic')
            results.append({'reason':reason,'events':events,'writes':len(sent),'connected':state._connected})
        print(json.dumps(results,separators=(',',':')))
        """;
    @Test void originalPythonIngestActuallyEmitsOnlyAfterSuccessfulInjectedAdoptionAndDoesNotAwaitPong()throws Exception {
        Path nativeSource=Path.of(required("xar.native.producer.source")),python=Path.of(required("xar.native.producer.python"));
        if(!nativeSource.isAbsolute()||!python.isAbsolute())throw new IllegalArgumentException("absolute original Python/source fixture paths required");
        Path output=temporary.resolve("handshake-original.json"),error=temporary.resolve("handshake-original.stderr");
        Process process=new ProcessBuilder(python.toString(),"-X","utf8","-c",ORIGINAL,nativeSource.toString(),"eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603",HELLO)
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if(!process.waitFor(20,TimeUnit.SECONDS)){process.destroyForcibly();throw new IOException("original handshake fixture timed out");}
        if(process.exitValue()!=0)throw new IOException("original handshake fixture failed: "+Files.readString(error,StandardCharsets.UTF_8));
        var result=NativeWire.parse(Files.readAllBytes(output));assertEquals(6,result.size());assertEquals(1,result.get(0).get("writes").intValue());
        for(int i=1;i<5;i++)assertEquals(0,result.get(i).get("writes").intValue());
        assertEquals(1,result.get(5).get("writes").intValue());assertFalse(result.get(5).get("connected").booleanValue());
    }
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("NOT EXECUTED: mandatory original handshake fixture property "+key);return value;}
    private static NativeGameTransport transport(Replay port){return new NativeGameTransport(port,new NativePipeEndpoint.Config("\\\\.\\pipe\\handshake-fixture","fixture-machine",new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("18446744073709551615"))),"fixture-session","fixture",SHA,"fixture"),32,4);}
    private static Instant deadline(){return Instant.now().plusSeconds(30);}
    private static String snapshot(String id){return "{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\""+id+"\",\"revision\":7,\"state\":"+STATE+"}";}
    private static String pong(String requestId,String pid){return "{\"type\":\"pong\",\"protocol_version\":1,\"request_id\":\""+requestId+"\",\"pid\":"+pid+"}";}
    private static byte[] packet(String json)throws IOException {return NativeWire.packet(json.getBytes(StandardCharsets.UTF_8));}
    private enum Failure {NONE,IO,INTERRUPTED,ZERO_PREFIX,PARTIAL_WRITE,POST_VERIFY}
    private static final class Replay implements NativePacketPort {
        private final ArrayDeque<byte[]> received=new ArrayDeque<>();private final List<byte[]> written=new ArrayList<>();private int reads;private Failure failure=Failure.NONE;private Instant actualWriteDeadline;
        synchronized void add(String json)throws IOException {add(packet(json));}
        synchronized void add(byte[] original){received.add(original.clone());}
        @Override public synchronized void verify()throws IOException {if(failure==Failure.POST_VERIFY&&!written.isEmpty())throw new IOException("actual post-write identity read failed");}
        @Override public void awaitConnection(Instant deadline){ }
        @Override public synchronized byte[] readPacket(Instant deadline)throws IOException {reads++;if(received.isEmpty())throw new IOException("original fixture packet queue exhausted");return received.removeFirst().clone();}
        @Override public synchronized void writePacket(byte[] original,Instant deadline)throws IOException,InterruptedException {
            actualWriteDeadline=deadline;
            written.add(original.clone());if(failure==Failure.IO)throw new IOException("actual write completion unavailable");
            if(failure==Failure.INTERRUPTED)throw new InterruptedException("actual original control write interrupted");
            if(failure==Failure.ZERO_PREFIX)throw new NativePipeEndpoint.TransferFailure("actual zero prefix write refused",original,0,false,new IOException("controlled original refusal"));
            if(failure==Failure.PARTIAL_WRITE)throw new NativePipeEndpoint.TransferFailure("actual partial original write",original,5,true,new IOException("controlled partial write"));
        }
        @Override public void close(){ }
    }
}
