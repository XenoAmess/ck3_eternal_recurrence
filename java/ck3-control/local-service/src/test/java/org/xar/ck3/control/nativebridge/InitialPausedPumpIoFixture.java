package org.xar.ck3.control.nativebridge;

import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayDeque;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

/** Software Win32 byte I/O into the real endpoint and transport. Issues no Root or Entry authority. */
public final class InitialPausedPumpIoFixture implements AutoCloseable {
    public static final int DATE=53144328;
    private static final String SHA="0".repeat(64);
    private static final String HELLO="{\"type\":\"hello\",\"protocol_version\":1,\"pid\":42,\"connection_generation\":18446744073709551615,\"bridge_version\":\"fixture\",\"expected_ck3_sha256\":\""+SHA+"\",\"game_adapter_id\":\"fixture\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\"]}";
    private static final String STATE="{\"date_raw\":53144328,\"speed\":1,\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":73,\"alive\":true},\"active_event\":null,\"pending_character_interaction\":null,\"one_life_settlement\":null,\"played_character_gold\":{\"raw\":0,\"scale\":100000},\"played_character_prestige\":{\"raw\":0,\"scale\":100000},\"played_character_piety\":{\"raw\":0,\"scale\":100000},\"history\":[],\"active_wars\":[],\"player_armies\":[]}";
    private final Pipe api=new Pipe();
    private final NativePipeEndpoint endpoint;
    private final NativeGameTransport transport;
    private final byte[] firstHeartbeat;
    private final NativeObservationPort.ObservedFrame first;

    public InitialPausedPumpIoFixture() throws IOException,InterruptedException {
        var config=new NativePipeEndpoint.Config("\\\\.\\pipe\\initial-paused-pump-fixture","fixture-machine",
                new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"fixture-session","fixture",SHA,"fixture");
        endpoint=new NativePipeEndpoint(config,game->{
            if(api.guardFailure!=null)throw api.guardFailure;
            if(!game.equals(config.game()))throw new IOException("software Game source changed");
            api.guardChecks++;
        },api,new HANDLE(Pointer.createConstant(7)));
        endpoint.awaitConnection(Instant.now().plusSeconds(5));
        firstHeartbeat=heartbeat(1,"1",true,DATE);
        api.add(packet(HELLO));api.add(firstHeartbeat);api.add(snapshot("paused-first",7));
        // Matches JavaGameLifecycle's real maximumFramesPerOperation, not a tiny test budget.
        transport=new NativeGameTransport(endpoint,config,65_536,16);
        first=transport.observe(Instant.now().plusSeconds(5));
    }
    public NativeGameTransport transport(){return transport;}
    public NativeObservationPort.ObservedFrame first(){return first;}
    public byte[] firstHeartbeat(){return firstHeartbeat.clone();}
    public int readCalls(){return api.readCalls;}
    public int writeCalls(){return api.writes;}
    public void failSource(String message){api.guardFailure=new IOException(message);}
    public void foreignPid(){api.pid=43;}
    public byte[] retainedFailureBytes(){return endpoint.retainedFailureBytes();}
    public byte[] publishHeartbeat(int sequence,String pump,boolean paused,int date)throws IOException {
        byte[] raw=heartbeat(sequence,pump,paused,date);api.add(raw);return raw.clone();
    }
    public byte[] publishSnapshot(String id,int revision)throws IOException {
        byte[] raw=snapshot(id,revision);api.add(raw);return raw.clone();
    }
    public void publishPartial(byte[] raw){api.add(raw);}
    private static byte[] snapshot(String id,int revision)throws IOException {
        return packet("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\""+id+"\",\"revision\":"+revision+",\"state\":"+STATE+"}");
    }
    private static byte[] heartbeat(int sequence,String pump,boolean paused,int date)throws IOException {
        return packet("{\"type\":\"heartbeat\",\"protocol_version\":1,\"pid\":42,\"sequence\":"+sequence+",\"monotonic_ms\":"+(100+sequence)+",\"startup_failure_containment_enabled\":false,\"startup_particle2_stage_recorder_enabled\":false,\"main_thread_query_mailbox_v1\":{\"installed\":true,\"ready\":true,\"stop\":false,\"executor_submission_enabled\":true,\"failure\":0,\"paused\":"+paused+",\"date_raw\":"+date+",\"pump_epochs\":"+pump+"}}");
    }
    private static byte[] packet(String json)throws IOException {
        return NativeWire.packet(json.getBytes(StandardCharsets.UTF_8));
    }
    @Override public void close()throws IOException{transport.close();}
    private static final class Pipe implements NativePipeEndpoint.Api {
        private final ArrayDeque<Byte> bytes=new ArrayDeque<>();
        private int pid=42,readCalls,writes,guardChecks;
        private IOException guardFailure;
        synchronized void add(byte[] raw){for(byte value:raw)bytes.addLast(value);}
        public HANDLE CreateNamedPipeW(String name,int openMode,int pipeMode,int instances,int output,int input,int timeout,Pointer security){
            throw new AssertionError("software fixture never creates an operating-system pipe");
        }
        public boolean ConnectNamedPipe(HANDLE pipe,Pointer overlapped){return true;}
        public boolean GetNamedPipeClientProcessId(HANDLE pipe,IntByReference client){client.setValue(pid);return true;}
        public synchronized boolean PeekNamedPipe(HANDLE pipe,Pointer buffer,int size,Pointer read,IntByReference available,Pointer left){
            available.setValue(bytes.size());return true;
        }
        public synchronized boolean ReadFile(HANDLE file,Pointer buffer,int length,IntByReference read,Pointer overlapped){
            readCalls++;int size=Math.min(length,bytes.size());byte[] raw=new byte[size];
            for(int index=0;index<size;index++)raw[index]=bytes.removeFirst();
            buffer.write(0,raw,0,size);read.setValue(size);return true;
        }
        public boolean WriteFile(HANDLE file,Pointer buffer,int length,IntByReference count,Pointer overlapped){
            writes++;throw new AssertionError("initial paused pump collection must never write a request");
        }
        public boolean DisconnectNamedPipe(HANDLE pipe){return true;}
        public boolean CloseHandle(HANDLE pipe){return true;}
    }
}
