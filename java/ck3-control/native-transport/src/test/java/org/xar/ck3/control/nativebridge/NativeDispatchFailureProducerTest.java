package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.action.NativeActionPort.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Pointer;
import com.sun.jna.Native;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.Optional;
import java.util.List;
import java.util.ArrayList;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.application.action.RootExecutableBindings;
import org.xar.ck3.control.application.action.ExecutableStepBindings;
import java.util.concurrent.locks.LockSupport;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeFailureCauseCodec;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Real Endpoint and transport with the existing software Win32 byte source. No Game/native qualification. */
final class NativeDispatchFailureProducerTest {
    private static final String SHA="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final String HELLO="""
        {"type":"hello","protocol_version":1,"pid":42,"connection_generation":1,"bridge_version":"source-test",
         "expected_ck3_sha256":"%s","expected_ck3_version":"1.20.0.4","game_adapter_id":"ck3-1.20.0.4-msvc-x64",
         "game_adapter_status":"ready","ck3_build_match":true,
         "capabilities":["game.query.core-frame.v1","game.state.snapshot","game.query.fresh-full-state.v1"]}
        """.formatted(SHA);
    private static Instant deadline(){return Instant.now().plusSeconds(5);}
    private static byte[] packet(String json)throws IOException{return NativeWire.packet(json.getBytes(StandardCharsets.UTF_8));}
    private static final class Api implements NativePipeEndpoint.Api {
        final NativeSnapshotWaitReceiverFixture.Pipe bytes=new NativeSnapshotWaitReceiverFixture.Pipe();
        Instant delayWriteUntil;
        int failPeekAfter = Integer.MAX_VALUE;
        int peekFailureCode=109,disconnectFailureCode,disconnectCalls,closeCalls;
        @Override public HANDLE CreateNamedPipeW(String name,int mode,int pipeMode,int count,int out,int in,int timeout,Pointer security){return bytes.CreateNamedPipeW(name,mode,pipeMode,count,out,in,timeout,security);}
        @Override public boolean ConnectNamedPipe(HANDLE pipe,Pointer overlapped){return bytes.ConnectNamedPipe(pipe,overlapped);}
        @Override public boolean GetNamedPipeClientProcessId(HANDLE pipe,IntByReference pid){return bytes.GetNamedPipeClientProcessId(pipe,pid);}
        @Override public boolean PeekNamedPipe(HANDLE pipe,Pointer buffer,int size,Pointer read,IntByReference available,Pointer left){
            boolean result=bytes.PeekNamedPipe(pipe,buffer,size,read,available,left);
            if(!result)Native.setLastError(peekFailureCode);return result;
        }
        @Override public boolean ReadFile(HANDLE pipe,Pointer buffer,int size,IntByReference read,Pointer overlapped){
            boolean result=bytes.ReadFile(pipe,buffer,size,read,overlapped);
            if(bytes.readBytes>=failPeekAfter)bytes.failPeek=true;
            return result;
        }
        @Override public boolean WriteFile(HANDLE pipe,Pointer buffer,int size,IntByReference written,Pointer overlapped){
            boolean result=bytes.WriteFile(pipe,buffer,size,written,overlapped);
            if(delayWriteUntil!=null)while(Instant.now().isBefore(delayWriteUntil))
                LockSupport.parkNanos(Math.max(1,Duration.between(Instant.now(),delayWriteUntil).toNanos()));
            return result;
        }
        @Override public boolean DisconnectNamedPipe(HANDLE pipe){
            disconnectCalls++;
            if(disconnectFailureCode!=0){Native.setLastError(disconnectFailureCode);return false;}
            return bytes.DisconnectNamedPipe(pipe);
        }
        @Override public boolean CloseHandle(HANDLE pipe){closeCalls++;return bytes.CloseHandle(pipe);}
    }
    /** Direct packet-boundary exceptions exercise the actual transport's IO/runtime catch branches. */
    private static final class PacketFault implements NativePacketPort {
        final NativePipeEndpoint original;Throwable next;boolean hideDisconnection;
        PacketFault(NativePipeEndpoint original){this.original=original;}
        @Override public void verify()throws IOException{original.verify();}
        @Override public void awaitConnection(Instant until)throws IOException,InterruptedException{original.awaitConnection(until);}
        @Override public byte[] readPacket(Instant until)throws IOException,InterruptedException{
            Throwable failure=next;next=null;
            if(failure instanceof IOException io)throw io;
            if(failure instanceof RuntimeException runtime)throw runtime;
            return original.readPacket(until);
        }
        @Override public void writePacket(byte[] originalPacket,Instant until)throws IOException,InterruptedException{original.writePacket(originalPacket,until);}
        @Override public Optional<NativePacketPort.Disconnection> originalDisconnection(){return hideDisconnection?Optional.empty():original.originalDisconnection();}
        @Override public void close()throws IOException{original.close();}
    }
    private static final class Fixture implements AutoCloseable {
        final Api api=new Api();final NativePipeEndpoint endpoint;final PacketFault fault;final NativeGameTransport transport;
        Fixture(int maximumFrames)throws Exception {
            String slash=Character.toString(92);
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"dispatch-failure-source-test",
                    "source-test-machine",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"failure-source-session",
                    "source-test",SHA,"ck3-1.20.0.4-msvc-x64");
            api.bytes.allowWrites=true;api.bytes.add(packet(HELLO));
            endpoint=new NativePipeEndpoint(config,game->{if(api.bytes.guardFailure!=null)throw api.bytes.guardFailure;api.bytes.guardChecks++;},api,new HANDLE(Pointer.createConstant(7)));
            endpoint.awaitConnection(deadline());fault=new PacketFault(endpoint);transport=new NativeGameTransport(fault,config,maximumFrames,16);
            transport.awaitHello(deadline());
        }
        Unknown core()throws InterruptedException{return assertInstanceOf(Unknown.class,transport.readCoreFrame(deadline()));}
        @Override public void close()throws IOException{transport.close();}
    }
    private static FailureCause actualCause(Unknown unknown,FailureKind kind,FailureStage stage)throws IOException {
        FailureCause cause=unknown.failureCause().orElseThrow();assertEquals(kind,cause.kind());assertEquals(stage,cause.stage());
        assertEquals(cause,NativeFailureCauseCodec.decode(NativeFailureCauseCodec.encode(cause)));
        ObjectNode request=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(unknown.originalRequestPacket(),4,unknown.originalRequestPacket().length)));
        assertEquals("execute_step",request.get("type").textValue());assertEquals(unknown.requestId(),request.get("request_id").textValue());
        assertEquals(BigInteger.ZERO,request.get("expected_revision").bigIntegerValue());return cause;
    }
    @Test void actualEndpointResponseDeadlineRetainsEvidenceAndUnresolvedFreshReadCannotWriteAgain()throws Exception {
        try(var fixture=new Fixture(4)){
            var first=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,fixture.transport.readFreshFullState(Instant.now().plusSeconds(2)));
            var unknown=assertInstanceOf(Unknown.class,first.dispatch());var cause=actualCause(unknown,FailureKind.DEADLINE_EXPIRED,FailureStage.RESPONSE_WAIT);
            var observed=cause.deadline().orElseThrow();assertTrue(observed.monotonicExpired()||!observed.observedAt().isBefore(observed.suppliedDeadline()));
            assertEquals(NativePipeEndpoint.TransferFailure.class.getName(),cause.originalException().orElseThrow().javaType());
            assertEquals(NativePacketPort.DeadlineExpired.class.getName(),cause.originalCause().orElseThrow().javaType());
            assertEquals(1,fixture.api.bytes.writes);int reads=fixture.api.bytes.readCalls;
            var held=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,fixture.transport.readFreshFullState(deadline()));
            assertSame(unknown,held.dispatch());assertEquals(1,fixture.api.bytes.writes);assertEquals(reads,fixture.api.bytes.readCalls);
            assertTrue(fixture.transport.pollOriginalOutcome(unknown.requestId()).isEmpty());assertEquals(reads,fixture.api.bytes.readCalls);
        }
    }
    @Test void actualReadIoPreservesTransferExceptionAndDoesNotBecomeADeadline()throws Exception {
        try(var fixture=new Fixture(4)){
            fixture.api.bytes.failPeek=true;Unknown unknown=fixture.core();var cause=actualCause(unknown,FailureKind.TRANSFER_IO,FailureStage.RESPONSE_WAIT);
            assertTrue(cause.deadline().isEmpty());assertEquals(NativePacketPort.ConnectionLost.class.getName(),cause.originalCause().orElseThrow().javaType());
            assertEquals("PeekNamedPipe Win32=109",cause.originalCause().orElseThrow().message());assertEquals(1,fixture.api.bytes.writes);
            var disconnected=fixture.transport.latestStateRevision().orElseThrow();
            assertEquals(NativeGameTransport.StateRevisionKind.DISCONNECTED,disconnected.kind());
            assertEquals(BigInteger.TWO,disconnected.publicRevision());
            assertEquals(109,disconnected.disconnection().orElseThrow().win32Code());
            fixture.transport.close();fixture.transport.close();
            assertSame(disconnected,fixture.transport.latestStateRevision().orElseThrow());
        }
    }
    @Test void actualPartialReadInterruptionRetainsBytesAndCancellationWithoutTimeoutClassification()throws Exception {
        try(var fixture=new Fixture(4)){
            fixture.api.bytes.interruptAfter=fixture.api.bytes.readBytes+1;fixture.api.bytes.add(new byte[]{1});
            try {
                var cause=actualCause(fixture.core(),FailureKind.INTERRUPTED,FailureStage.RESPONSE_WAIT);
                assertTrue(cause.deadline().isEmpty());assertTrue(Thread.currentThread().isInterrupted());
                assertEquals(NativePacketPort.ReadInterrupted.class.getName(),cause.originalException().orElseThrow().javaType());
                assertEquals(InterruptedException.class.getName(),cause.originalCause().orElseThrow().javaType());
                assertArrayEquals(new byte[]{1},fixture.endpoint.retainedFailureBytes());
                assertArrayEquals(new byte[]{1},fixture.transport.diagnostics().lastOriginalPacket().value());
                assertEquals(NativeGameTransport.ReceivedState.TERMINAL,fixture.transport.diagnostics().receivedState());
                assertThrows(IOException.class,fixture.transport::latestObservedSnapshot);
                assertEquals(1,fixture.api.bytes.writes);
            }finally{Thread.interrupted();}
        }
    }
    @Test void actualPartialResponseIoReachesTransportDiagnosticsAndIsNotDecodedOrReplayed()throws Exception {
        try(var fixture=new Fixture(4)){
            fixture.api.failPeekAfter=fixture.api.bytes.readBytes+1;fixture.api.bytes.add(new byte[]{1});
            Unknown unknown=fixture.core();var cause=actualCause(unknown,FailureKind.TRANSFER_IO,FailureStage.RESPONSE_WAIT);
            assertTrue(cause.deadline().isEmpty());assertTrue(unknown.rawReturn().isEmpty());
            assertEquals("PeekNamedPipe Win32=109",cause.originalCause().orElseThrow().message());
            assertArrayEquals(new byte[]{1},fixture.endpoint.retainedFailureBytes());
            var diagnostics=fixture.transport.diagnostics();
            assertArrayEquals(new byte[]{1},diagnostics.lastOriginalPacket().value());
            assertEquals(NativeGameTransport.ReceivedState.TERMINAL,diagnostics.receivedState());
            assertTrue(diagnostics.terminalFailure().orElseThrow().contains("partial original packet"));
            assertEquals(1,fixture.api.bytes.writes);int reads=fixture.api.bytes.readCalls;
            assertInstanceOf(RejectedBeforeDispatch.class,fixture.transport.readCoreFrame(deadline()));
            assertEquals(1,fixture.api.bytes.writes);assertEquals(reads,fixture.api.bytes.readCalls);
            assertArrayEquals(new byte[]{1},fixture.transport.diagnostics().lastOriginalPacket().value());
        }
    }
    @Test void actualPartialMailboxReadKeepsUnknownPoisonAndCannotLeaveAsCompletedOrDeferred()throws Exception {
        try(var fixture=new Fixture(4)){
            fixture.api.failPeekAfter=fixture.api.bytes.readBytes+1;fixture.api.bytes.add(new byte[]{1});
            assertThrows(IOException.class,()->fixture.transport.withMailbox(deadline(),scope->{
                Unknown original=fixture.core();
                assertThrows(IOException.class,()->scope.complete(original));
                assertTrue(fixture.transport.deferredMailboxRead().isEmpty());
                return original;
            }));
            assertTrue(fixture.transport.mailboxDiagnostics().poison().isPresent());
            assertEquals(1,fixture.transport.mailboxDiagnostics().unresolvedRequestIds().size());
            assertArrayEquals(new byte[]{1},fixture.transport.diagnostics().lastOriginalPacket().value());
            assertThrows(IOException.class,()->fixture.transport.withMailbox(deadline(),scope->"forbidden"));
            assertEquals(1,fixture.api.bytes.writes);
        }
    }
    @Test void unrelatedOriginalFramesExhaustOnlyTheFrameBudget()throws Exception {
        try(var fixture=new Fixture(4)){
            for(int i=0;i<4;i++)fixture.api.bytes.add(packet("{\"type\":\"pong\",\"protocol_version\":1,\"request_id\":\"unrelated-"+i+"\"}"));
            var cause=actualCause(fixture.core(),FailureKind.FRAME_BUDGET_EXHAUSTED,FailureStage.RESPONSE_WAIT);
            assertTrue(cause.originalException().isEmpty());assertTrue(cause.originalCause().isEmpty());assertTrue(cause.deadline().isEmpty());assertEquals(1,fixture.api.bytes.writes);
        }
    }
    @Test void deadlineAfterActualWriteBytesRetainsWriteStageAndCannotClaimResponseTimeout()throws Exception {
        try(var fixture=new Fixture(4)){
            Instant supplied=Instant.now().plusSeconds(2);fixture.api.delayWriteUntil=supplied.plusMillis(30);
            Unknown unknown=assertInstanceOf(Unknown.class,fixture.transport.readCoreFrame(supplied));
            var cause=actualCause(unknown,FailureKind.DEADLINE_EXPIRED,FailureStage.WRITE);
            assertEquals(supplied,cause.deadline().orElseThrow().suppliedDeadline());assertEquals(1,fixture.api.bytes.writes);
            assertArrayEquals(unknown.originalRequestPacket(),fixture.api.bytes.written.toByteArray());
        }
    }
    @Test void actualPacketIoAndRuntimeFailuresKeepNullableMessagesWithoutParsingThem()throws Exception {
        for(Throwable original:new Throwable[]{new IOException((String)null),new IllegalStateException("Native transport deadline expired")}){
            try(var fixture=new Fixture(4)){
                fixture.fault.next=original;FailureKind kind=original instanceof IOException?FailureKind.IO_FAILURE:FailureKind.RUNTIME_FAILURE;
                var cause=actualCause(fixture.core(),kind,FailureStage.RESPONSE_WAIT);
                assertEquals(original.getClass().getName(),cause.originalException().orElseThrow().javaType());
                assertEquals(original.getMessage(),cause.originalException().orElseThrow().message());assertTrue(cause.deadline().isEmpty());assertEquals(1,fixture.api.bytes.writes);
                assertEquals(NativeGameTransport.StateRevisionKind.HELLO,fixture.transport.latestStateRevision().orElseThrow().kind());
                assertEquals(BigInteger.ONE,fixture.transport.latestStateRevision().orElseThrow().publicRevision());
            }
        }
    }
    @Test void actualPipeLossCodesAdvanceExactlyOnceAndBlockAnotherSubmission()throws Exception {
        for(int code:new int[]{109,232,233})try(var fixture=new Fixture(4)) {
            fixture.api.peekFailureCode=code;fixture.api.bytes.failPeek=true;
            var unknown=fixture.core();actualCause(unknown,FailureKind.TRANSFER_IO,FailureStage.RESPONSE_WAIT);
            var disconnected=fixture.transport.latestStateRevision().orElseThrow();
            assertEquals(NativeGameTransport.StateRevisionKind.DISCONNECTED,disconnected.kind());
            assertEquals(BigInteger.TWO,disconnected.publicRevision());
            assertEquals(code,disconnected.disconnection().orElseThrow().win32Code());
            assertFalse(disconnected.disconnection().orElseThrow().nativeDisconnectSucceeded());
            assertEquals("PeekNamedPipe",disconnected.disconnection().orElseThrow().operation());
            int reads=fixture.api.bytes.readCalls;
            assertInstanceOf(RejectedBeforeDispatch.class,fixture.transport.readCoreFrame(deadline()));
            assertEquals(1,fixture.api.bytes.writes);assertEquals(reads,fixture.api.bytes.readCalls);
            fixture.transport.close();fixture.transport.close();
            assertSame(disconnected,fixture.transport.latestStateRevision().orElseThrow());
            assertEquals(0,fixture.api.disconnectCalls);assertEquals(1,fixture.api.closeCalls);
        }
    }
    @Test void nativeDisconnectResultsProduceOneTransitionAndUnqualifiedCloseProducesNone()throws Exception {
        for(int code:new int[]{0,109,232,233,5})try(var fixture=new Fixture(4)) {
            var hello=fixture.transport.latestStateRevision().orElseThrow();
            fixture.api.disconnectFailureCode=code;
            if(code==5) {
                assertThrows(IOException.class,fixture.transport::close);
                assertTrue(fixture.transport.latestStateRevision().isEmpty());
            } else {
                fixture.transport.close();
                var disconnected=fixture.transport.latestStateRevision().orElseThrow();
                assertEquals(NativeGameTransport.StateRevisionKind.DISCONNECTED,disconnected.kind());
                assertEquals(BigInteger.TWO,disconnected.publicRevision());
                assertTrue(disconnected.received().order().compareTo(hello.received().order())>0);
                assertEquals("DisconnectNamedPipe",disconnected.disconnection().orElseThrow().operation());
                assertEquals(code,disconnected.disconnection().orElseThrow().win32Code());
                assertEquals(code==0,disconnected.disconnection().orElseThrow().nativeDisconnectSucceeded());
                fixture.transport.close();
                assertSame(disconnected,fixture.transport.latestStateRevision().orElseThrow());
            }
            fixture.transport.close();assertEquals(1,fixture.api.disconnectCalls);assertEquals(1,fixture.api.closeCalls);
        }
    }
    @Test void arbitraryGuardFailureNeedsActualPipeLossBeforeDisconnectedStateCanAdvance()throws Exception {
        for(boolean nativeLoss:new boolean[]{false,true})try(var fixture=new Fixture(4)) {
            var hello=fixture.transport.latestStateRevision().orElseThrow();
            fixture.api.bytes.guardFailure=new IOException("original Game identity source unavailable");
            fixture.api.bytes.failPeek=nativeLoss;fixture.api.peekFailureCode=233;
            assertInstanceOf(RejectedBeforeDispatch.class,fixture.transport.readCoreFrame(deadline()));
            assertEquals(0,fixture.api.bytes.writes);
            if(nativeLoss) {
                var disconnected=fixture.transport.latestStateRevision().orElseThrow();
                assertEquals(NativeGameTransport.StateRevisionKind.DISCONNECTED,disconnected.kind());
                assertEquals(BigInteger.TWO,disconnected.publicRevision());
                assertEquals(233,disconnected.disconnection().orElseThrow().win32Code());
            } else assertSame(hello,fixture.transport.latestStateRevision().orElseThrow());
        }
    }
    @Test void hiddenNativeCloseReceiptCannotBecomeAnAssumedConnectedFalseIncrement()throws Exception {
        try(var fixture=new Fixture(4)) {
            fixture.fault.hideDisconnection=true;fixture.transport.close();
            assertTrue(fixture.transport.latestStateRevision().isEmpty());
            fixture.transport.close();assertEquals(1,fixture.api.disconnectCalls);assertEquals(1,fixture.api.closeCalls);
        }
    }
    @Test void soleCauseCodecRejectsMissingExtraWrongTypesAndFalseDeadlineEvidence() {
        var actual=new FailureCause(FailureKind.IO_FAILURE,FailureStage.WRITE,Optional.of(new OriginalException("java.io.IOException",null)),Optional.empty(),Optional.empty());
        var row=NativeFailureCauseCodec.encodeValue(actual);assertTrue(row.get("exception").get("message").isNull());assertTrue(row.get("deadline").isNull());
        ObjectNode missing=row.deepCopy();missing.remove("deadline");assertThrows(IllegalArgumentException.class,()->NativeFailureCauseCodec.decodeValue(missing));
        assertThrows(IllegalArgumentException.class,()->NativeFailureCauseCodec.decodeValue(row.deepCopy().put("extra",true)));
        assertThrows(IllegalArgumentException.class,()->NativeFailureCauseCodec.decodeValue(row.deepCopy().put("kind",true)));
        assertThrows(IllegalArgumentException.class,()->NativeFailureCauseCodec.decodeValue(row.deepCopy().put("stage","UNKNOWN")));
        assertThrows(IllegalArgumentException.class,()->NativeFailureCauseCodec.decodeValue(row.deepCopy().put("kind","DEADLINE_EXPIRED")));
        ObjectNode wrongMessage=row.deepCopy();((ObjectNode)wrongMessage.get("exception")).put("message",0);
        assertThrows(IllegalArgumentException.class,()->NativeFailureCauseCodec.decodeValue(wrongMessage));
        var emptyMessage=new FailureCause(FailureKind.IO_FAILURE,FailureStage.WRITE,Optional.of(new OriginalException("java.io.IOException","")),Optional.empty(),Optional.empty());
        assertEquals(emptyMessage,NativeFailureCauseCodec.decode(NativeFailureCauseCodec.encode(emptyMessage)));
        var historical=new Unknown("historical","Native transport deadline expired",new byte[0],Optional.empty());
        assertTrue(historical.failureCause().isEmpty());assertNotEquals(historical,new Unknown(historical.requestId(),historical.reason(),historical.originalRequestPacket(),Optional.empty(),Optional.of(actual)));
        assertThrows(IllegalArgumentException.class,()->new DeadlineObservation(Instant.parse("2026-10-25T00:00:01Z"),Instant.parse("2026-10-25T00:00:00Z"),false));
    }
    @Test void allGuiAndDedicatedAubReadContractsShareActualAdvertisedPermissionViews() throws Exception {
        var source=new org.xar.ck3.control.contracts.ExactRef("software-read-inventory",1,"a".repeat(64));
        var gui=new org.xar.ck3.control.nativebridge.capabilities.gui.GuiReads(
                new org.xar.ck3.control.nativebridge.capabilities.gui.GuiReads.Sources(source,source,source,source,source,source,source));
        var port=new org.xar.ck3.control.nativebridge.NativePacketPort(){
            public void verify(){throw new AssertionError("inventory cannot perform Native IO");}
            public void awaitConnection(Instant deadline){throw new AssertionError("inventory cannot connect");}
            public byte[] readPacket(Instant deadline){throw new AssertionError("inventory cannot receive Native state");}
            public void writePacket(byte[] packet,Instant deadline){throw new AssertionError("inventory cannot submit");}
            public void close(){ }
        };
        var config=new org.xar.ck3.control.nativebridge.NativePipeEndpoint.Config("\\\\.\\pipe\\gui-aub-inventory", "software-read-inventory",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"inventory-session","fixture","0".repeat(64),"fixture-adapter");
        // The real registration constructors must remain pure. Any archive invocation fails this inventory test.
        var archive=ActionPorts.OutcomeArchive.class.cast(java.lang.reflect.Proxy.newProxyInstance(
                ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},
                (proxy,method,args)->{throw new AssertionError("inventory cannot use archive: "+method.getName());}));
        try(var transport=new org.xar.ck3.control.nativebridge.NativeGameTransport(port,config,16,64)){
            var aub=new org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations.Registration(transport,archive,
                    new org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations.Sources(source,source,source));
            var all=new ArrayList<ReadContract<?>>(gui.registered());all.add(aub.options());all.add(aub.business().contract());
            var catalog=RootReadContractCatalog.staticOnly(all);
            var bindings=RootExecutableBindings.freeze(List.of(),catalog,List.of(),16);
            assertEquals(9,catalog.contracts().size());assertEquals(7,bindings.installed().size());
            for(var actual:gui.registered())assertEquals(actual.requiredCapability().orElseThrow(),actual.permissionKey());
            for(var dedicated:List.of(aub.options(),aub.business().contract())){
                assertEquals(1,bindings.installed().stream().filter(step->step.operation().equals(dedicated.operation())&&step.guardMode()==dedicated.guardMode()).count());
                assertTrue(catalog.containsIdentity(dedicated));
                assertEquals(ExecutableStepBindings.Kind.READ,bindings.resolve(dedicated.operation(),dedicated.guardMode()).orElseThrow().kind());
            }
            assertTrue(catalog.containsIdentity(gui.aubPolicy));assertTrue(catalog.containsIdentity(gui.aubState));
        }
    }

}
