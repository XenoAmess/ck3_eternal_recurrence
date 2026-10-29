package org.xar.ck3.control.platform;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.WindowsPreloadCustody;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativePipeEndpoint;
import org.xar.ck3.control.nativebridge.NativeProcessGuard;

/** Opaque original Java-created Game or attached restartable business JVM Game. */
public final class ManagedGameSession implements GameLifecycle.Port,AutoCloseable {
    public enum Mode { OWNED, ATTACHED }
    public record Shutdown(GameGeneration generation,WindowsJobProcess.CommandResult terminal,
            WindowsJobProcess.Accounting beforeTermination,List<WindowsJobProcess.ProcessIdentity> finalGameInventory,
            boolean wasRunning,boolean cleanupProven,GameLifecycle.TerminalKind kind,ExactRef evidence){
        public Shutdown{finalGameInventory=List.copyOf(finalGameInventory);}
    }
    private final NativeLaunchPlan plan;
    private final WindowsJobProcess process;
    private final WindowsPreloadCustody.Lease custody;
    private final SteamOfflineProbe.QualifiedOffline offline;
    private final NativeGameTransport transport;
    private final LifecycleEvidence evidence;
    private final JavaGameLifecycle owner;
    private final GameGeneration generation;
    private final WindowsJobProcess.ProcessIdentity originalIdentity;
    private final NativePhysicalSourceAccess physicalSource;
    private GameWatchdog watchdog;
    private Shutdown shutdown;
    private WindowsJobProcess.CommandResult naturalExit;
    private boolean stopping,closed;
    private final Mode mode;
    private final WindowsJobProcess.ReadOnlyProcessHandle attachedHandle;

    ManagedGameSession(NativeLaunchPlan plan,WindowsJobProcess process,WindowsPreloadCustody.Lease custody,
            SteamOfflineProbe.QualifiedOffline offline,NativeGameTransport transport,LifecycleEvidence evidence,JavaGameLifecycle owner,
            NativePipeEndpoint.Config actualConfig,NativeProcessGuard actualGuard){
        this.mode=Mode.OWNED;
        this.plan=plan;this.process=process;this.custody=custody;this.offline=offline;this.transport=transport;this.evidence=evidence;this.owner=owner;
        this.originalIdentity=process.identity();this.generation=generation(originalIdentity);
        this.attachedHandle=null;
        this.physicalSource=new NativePhysicalSourceAccess(this,Objects.requireNonNull(actualConfig),Objects.requireNonNull(actualGuard));
    }

    ManagedGameSession(NativeLaunchPlan plan,WindowsJobProcess.ReadOnlyProcessHandle handle,WindowsJobProcess.ProcessIdentity identity,
            GameGeneration generation,NativeGameTransport transport,LifecycleEvidence evidence,NativePipeEndpoint.Config actualConfig,NativeProcessGuard actualGuard){
        this.mode=Mode.ATTACHED;
        this.plan=plan;this.attachedHandle=Objects.requireNonNull(handle);this.originalIdentity=Objects.requireNonNull(identity);
        this.generation=Objects.requireNonNull(generation);this.transport=Objects.requireNonNull(transport);this.evidence=Objects.requireNonNull(evidence);
        this.process=null;this.custody=null;this.offline=null;this.owner=null;
        this.physicalSource=new NativePhysicalSourceAccess(this,Objects.requireNonNull(actualConfig),Objects.requireNonNull(actualGuard));
    }

    public Mode mode(){return mode;}
    /** Original launch inputs only. This attachment cannot issue an action, open a pipe or grant Ready. */
    public static final class NativePhysicalSourceAccess {
        private final ManagedGameSession owner;
        private final NativePipeEndpoint.Config config;
        private final NativeProcessGuard guard;
        private NativePhysicalSourceAccess(ManagedGameSession owner,NativePipeEndpoint.Config config,NativeProcessGuard guard) {
            this.owner=owner;this.config=config;this.guard=guard;
        }
        public void requireOwner(ManagedGameSession identical)throws IOException {
            if(owner!=identical)throw new IOException("physical launch attachment belongs to another original managed Game");
            owner.requirePhysicalSource(this);
        }
        public NativePipeEndpoint.Config actualConfig()throws IOException {owner.requirePhysicalSource(this);return config;}
        public NativeProcessGuard actualGuard()throws IOException {owner.requirePhysicalSource(this);return guard;}
    }
    /** Borrow the original Config and guard retained from the single suspended launch callback. */
    public synchronized NativePhysicalSourceAccess presentationAccess()throws IOException {
        requirePhysicalSource(physicalSource);return physicalSource;
    }
    private synchronized void requirePhysicalSource(NativePhysicalSourceAccess actual)throws IOException {
        if(actual!=physicalSource||actual.owner!=this)throw new IOException("physical launch attachment lost its original managed owner");
        verify();var config=actual.config;
        if(!config.game().equals(generation)||!config.machineId().equals(machineId())||!config.sessionId().equals(sessionId())
                ||!config.pipeName().equals(plan.pipeName())||!config.expectedBridgeVersion().equals(plan.bridgeVersion())
                ||!config.expectedAdapterId().equals(plan.adapterId()))
            throw new IOException("physical launch inputs differ from the exact original Game, source, session or native endpoint");
        actual.guard.verify(generation);verify();
    }
    static GameGeneration generation(WindowsJobProcess.ProcessIdentity identity){
        return new GameGeneration(identity.pid(),new PythonOnlyUInt64(new BigInteger(identity.creationFiletimeDecimal())));
    }
    public GameGeneration generation(){return generation;}
    public String machineId(){return physicalSource.config.machineId();}
    public String sessionId(){return plan.sessionId();}
    public NativeLaunchPlan launchPlan(){return plan;}
    public List<String> command(){java.util.ArrayList<String> command=new java.util.ArrayList<>();command.add(plan.sources().review().gameExecutable().path());command.addAll(plan.gameArguments());return List.copyOf(command);}
    public WindowsJobProcess.ProcessIdentity identity(){return originalIdentity;}
    public synchronized NativeGameTransport nativeTransport()throws IOException{verify();return transport;}
    public synchronized void verify()throws IOException{
        if(closed||stopping||shutdown!=null)throw new IOException("Original managed Game is closed/stopping");
        if(mode==Mode.OWNED){
            custody.verify();
            if(!process.isRunning()||!generation.equals(generation(custody.targetIdentity())))throw new IOException("Original held Game generation exited or changed");
        } else {
            try{
                if(attachedHandle.waitZero()!=258L)throw new IOException("Attached Game generation exited or changed");
                if(!generation.equals(generation(attachedHandle.identity())))throw new IOException("Attached Game generation exited or changed");
            }catch(RuntimeException failure){throw new IOException("Attached Game generation exited or changed",failure);}
        }
    }
    /** One owner handshake after actual HELLO and tracking, independent of any business worker lifetime. */
    public synchronized void activateRuntime()throws IOException{
        if(mode!=Mode.OWNED)throw new IOException("Runtime activation is owner-only operation");
        if(watchdog!=null)throw new IOException("Original managed Game runtime is already activated");
        verify();
        custody.activateRuntime();
        watchdog=new GameWatchdog(this);
    }
    @Override public synchronized GameLifecycle.Observation inspect(GameGeneration expected,Instant deadline)throws IOException{
        Win32Host.deadline(deadline);
        if(!generation.equals(expected))return unavailable("Caller expected a different original Game generation");
        if(shutdown!=null)return new GameLifecycle.Exited(generation,shutdown.terminal().exitCode(),shutdown.kind()==GameLifecycle.TerminalKind.DEADLINE,shutdown.kind(),shutdown.evidence());
        if(stopping)return unavailable("Original stop entered but complete cleanup terminal is not proved; no replay");
        if(closed)return unavailable("Game resources closed without a complete terminal");
        try{
            if(mode==Mode.ATTACHED){
                long wait=attachedHandle.waitZero();
                if(wait==258L){
                    verify();return new GameLifecycle.Running(generation,evidence.write(LifecycleEvidence.Event.RUNNING,originalIdentity,null,null,null,"Actual process is running with its original generation"));
                }
                if(wait==0L){
                    long exit=attachedHandle.exitCode();
                    return new GameLifecycle.Exited(generation,(int)exit,false,GameLifecycle.TerminalKind.NATURAL_EXIT,evidence.write(LifecycleEvidence.Event.EXITED,originalIdentity,null,null,GameLifecycle.TerminalKind.NATURAL_EXIT,"Actual signal+DWORD exit"));
                }
                return unavailable("Attached wait result other than 0/258");
            }
            if(process.isRunning()){
                verify();return new GameLifecycle.Running(generation,evidence.write(LifecycleEvidence.Event.RUNNING,process.identity(),process.accounting(),null,null,"Actual process is running with its original generation"));
            }
            if(process.accounting().activeProcesses()!=0)return unavailable("Root signalled but original Job still has active descendants");
            if(naturalExit==null)naturalExit=consumeSignalledRoot(process,deadline);
            ExactRef proof=evidence.write(LifecycleEvidence.Event.EXITED,process.identity(),naturalExit.accounting(),naturalExit,GameLifecycle.TerminalKind.NATURAL_EXIT,"Actual signalled root plus Job0; exit259 remains a nonzero natural exit");
            return new GameLifecycle.Exited(generation,naturalExit.exitCode(),false,GameLifecycle.TerminalKind.NATURAL_EXIT,proof);
        }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("Actual lifecycle inspection interrupted",interrupted);}
        catch(IOException|RuntimeException failure){return unavailable(failure.toString());}
    }
    private GameLifecycle.Unavailable unavailable(String detail)throws IOException{
        String bounded=detail.substring(0,Math.min(2048,detail.length()));
        WindowsJobProcess.Accounting acc=(mode==Mode.OWNED&&!closed)?process.accounting():null;
        ExactRef proof=evidence.write(LifecycleEvidence.Event.UNAVAILABLE,originalIdentity,acc,null,GameLifecycle.TerminalKind.UNKNOWN,bounded);
        return new GameLifecycle.Unavailable(bounded,proof);
    }
    public synchronized Shutdown stopTracked(GameGeneration expected,Instant deadline,boolean requireRunning)throws IOException,InterruptedException{
        if(mode!=Mode.OWNED)throw new IOException("Stop is owner-only operation");
        return stop(expected,deadline,requireRunning,GameLifecycle.TerminalKind.OWNER_STOP);
    }
    synchronized Shutdown stop(GameGeneration expected,Instant deadline,boolean requireRunning,GameLifecycle.TerminalKind kind)throws IOException,InterruptedException{
        if(mode!=Mode.OWNED)throw new IOException("Stop is owner-only operation");
        if(!generation.equals(expected))throw new IOException("Stop belongs to a different original Game generation");
        if(shutdown!=null)return shutdown;
        if(stopping||closed)throw new IOException("Previous stop is UNKNOWN; no second mutation");
        Win32Host.deadline(deadline);stopping=true;
        try{
        WindowsJobProcess.Accounting before=process.accounting();boolean wasRunning=process.isRunning();
        if(kind==GameLifecycle.TerminalKind.NATURAL_EXIT&&before.activeProcesses()!=0)kind=GameLifecycle.TerminalKind.OWNER_STOP;
        evidence.write(LifecycleEvidence.Event.STOP_REQUESTED,process.identity(),before,null,kind,requireRunning&&!wasRunning?"Expected running Game was already signalled; preserve terminal":"Owner stopping original Job, never reopening PID");
        IOException trackingFailure=null;
        try{owner.verifyTracking(this);}catch(IOException invalid){trackingFailure=invalid;}
        if(before.activeProcesses()!=0)process.terminate(125);
        WindowsJobProcess.CommandResult actual=process.await(Duration.ofSeconds(20),deadline,()->{});
        ExactRef terminalProof=evidence.write(LifecycleEvidence.Event.STOPPED,process.identity(),actual.accounting(),actual,kind,"Original root wait/exit and Job accounting consumed before cleanup");
        if(!cleanupProven(process,actual))throw new IOException("Original Job cleanup is not proved: "+actual);
        Win32Host.ProcessInventory observedInventory=Win32Host.processInventory("ck3.exe",deadline);
        evidence.writeInventory("AFTER_STOP",observedInventory);
        List<WindowsJobProcess.ProcessIdentity> finalInventory=observedInventory.qualifiedRunning().stream().map(Win32Host.ProcessRow::identity).toList();
        if(!finalInventory.isEmpty())throw new IOException("Global CK3 inventory is not empty; unsafe marker retained");
        if(trackingFailure!=null){process.close();closed=true;throw new IOException("Original Job0 proved but tracking changed; unsafe marker retained",trackingFailure);}
        IOException cleanup=null;
        try{transport.close();}catch(IOException failure){cleanup=failure;}
        try{custody.close();}catch(IOException failure){if(cleanup==null)cleanup=failure;else cleanup.addSuppressed(failure);}
        try{offline.close();}catch(IOException failure){if(cleanup==null)cleanup=failure;else cleanup.addSuppressed(failure);}
        if(cleanup!=null)throw cleanup;
        process.close();closed=true;
        owner.clearTrackingAfterProvenExit(this);
        shutdown=new Shutdown(generation,actual,before,finalInventory,wasRunning,true,kind,terminalProof);
        if(watchdog!=null)watchdog.cancel();
        return shutdown;
        }catch(IOException|InterruptedException|RuntimeException failure){
            // Cleanup requests on the original held Job are permitted after an unknown stop; no ACK becomes proof.
            try{process.close();}catch(RuntimeException cleanup){failure.addSuppressed(cleanup);}closed=true;
            try{transport.close();}catch(IOException|RuntimeException cleanup){failure.addSuppressed(cleanup);}
            try{custody.close();}catch(IOException|RuntimeException cleanup){failure.addSuppressed(cleanup);}
            try{offline.close();}catch(IOException|RuntimeException cleanup){failure.addSuppressed(cleanup);}
            if(watchdog!=null)watchdog.cancel();
            throw failure;
        }
    }
    private static Instant min(Instant a,Instant b){return a.isBefore(b)?a:b;}
    /** Resource/execution failure remains in the terminal; cleanup proves only the original root signal and Job0. */
    static boolean cleanupProven(WindowsJobProcess process,WindowsJobProcess.CommandResult actual){
        return !process.isRunning()&&actual.accounting().activeProcesses()==0;
    }
    static WindowsJobProcess.CommandResult consumeSignalledRoot(WindowsJobProcess process,Instant deadline)throws IOException,InterruptedException{
        if(process.isRunning()||process.accounting().activeProcesses()!=0)throw new IOException("Original signalled root and Job0 required before consuming natural exit");
        return process.await(Duration.ofSeconds(1),min(deadline,Instant.now().plusSeconds(1)),()->{});
    }
    synchronized GameLifecycle.TerminalKind watchdogCheck()throws IOException{
        if(mode!=Mode.OWNED)return null;
        if(shutdown!=null||closed||stopping)return null;
        if(!process.isRunning())return GameLifecycle.TerminalKind.NATURAL_EXIT;
        verify();return null;
    }
    @Override public void close()throws IOException{
        if(mode==Mode.ATTACHED){
            synchronized(this){
                if(closed)return;
                closed=true;
            }
            IOException cleanup=null;
            try{transport.close();}catch(IOException|RuntimeException failure){cleanup=(failure instanceof IOException)?(IOException)failure:new IOException("Transport close failed",failure);}
            try{attachedHandle.close();}catch(RuntimeException failure){if(cleanup==null)cleanup=new IOException("Handle close failed",failure);else cleanup.addSuppressed(new IOException("Handle close failed",failure));}
            if(cleanup!=null)throw cleanup;
            return;
        }
        try{stopTracked(generation,Instant.now().plusSeconds(25),false);}
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("Game shutdown interrupted; unsafe marker retained",interrupted);}
    }
}
