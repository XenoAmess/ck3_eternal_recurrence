package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.UUID;
import java.util.function.LongSupplier;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol.*;
import org.xar.ck3.control.platform.ManagedGameSession;

/** One query-only original handle. No process discovery, signal, termination, native pipe or snapshot path. */
public final class NormalExitRetainedObserver implements AutoCloseable {
    static final long SIGNALED=0,TIMEOUT=258,FAILED=0xffff_ffffL;
    record Identity(long pid,BigInteger creation){Identity{require(pid>0&&pid<=0xffff_ffffL&&creation.signum()>0&&creation.compareTo(StrictJson.UINT64_MAX)<=0,"exact process generation required");}}
    interface Handle extends AutoCloseable {Identity identity()throws IOException;long waitZero()throws IOException;long exitCode()throws IOException;void close()throws IOException;}
    @FunctionalInterface interface Api{Handle open(long pid)throws IOException;}
    interface FactStore{org.xar.ck3.control.contracts.ExactRef preserve(org.xar.ck3.control.application.action.RawJson value)throws IOException;org.xar.ck3.control.application.action.RawJson read(org.xar.ck3.control.contracts.ExactRef ref)throws IOException;}
    static org.xar.ck3.control.contracts.ExactRef preserveBeforeClose(NormalExitRetainedObserver owner,ProcessObservation actual,
            org.xar.ck3.control.application.action.RawJson value,FactStore store)throws IOException{
        require(actual.identity().equals(owner.identity()),"exit fact belongs to another original retained handle");
        var ref=store.preserve(value);require(store.read(ref).equals(value)&&ref.bytes()==value.bytes().length
                &&ref.sha256().equals(org.xar.ck3.control.application.action.ActionCodec.sha256(value.bytes())),"actual exit fact was not durably preserved/read back");
        if(actual.exitObserved())owner.close();return ref;
    }
    private final Handle original;private final RetainedIdentity identity;private final LongSupplier clock;
    private boolean closed;private Optional<String> closeError=Optional.empty();
    private NormalExitRetainedObserver(Handle original,RetainedIdentity identity,LongSupplier clock){this.original=original;this.identity=identity;this.clock=clock;}
    /** The caller cannot select a PID or substitute a process API on the production entry. */
    public static NormalExitRetainedObserver open(ManagedGameSession actual)throws IOException{
        Objects.requireNonNull(actual).verify();var expected=actual.identity();
        var observer=capture(pid->{
            WindowsJobProcess.ReadOnlyProcessHandle held;
            try{held=WindowsJobProcess.retainReadOnlyProcess(pid);}catch(RuntimeException failure){throw new IOException("retain actual normal-exit query handle",failure);}
            return new Handle(){
                public Identity identity()throws IOException{try{var value=held.identity();return new Identity(value.pid(),new BigInteger(value.creationFiletimeDecimal()));}catch(RuntimeException failure){throw new IOException("original handle identity unavailable",failure);}}
                public long waitZero()throws IOException{try{return held.waitZero();}catch(RuntimeException failure){throw new IOException("original handle wait failed",failure);}}
                public long exitCode()throws IOException{try{return held.exitCode();}catch(RuntimeException failure){throw new IOException("original handle exit code failed",failure);}}
                public void close()throws IOException{try{held.close();}catch(RuntimeException failure){throw new IOException("original handle close failed",failure);}}
            };
        },new Identity(expected.pid(),new BigInteger(expected.creationFiletimeDecimal())),System::nanoTime);
        try{actual.verify();return observer;}catch(IOException|RuntimeException failure){observer.close();throw failure;}
    }
    /** Package-only controlled OS edge for meaningful tests; cannot mint a ManagedGameSession or a Root source permission. */
    static NormalExitRetainedObserver capture(Api api,Identity expected,LongSupplier clock)throws IOException{
        Objects.requireNonNull(api);Objects.requireNonNull(expected);Objects.requireNonNull(clock);Handle handle=api.open(expected.pid());
        try{require(handle.identity().equals(expected),"retained process birth differs from the original managed generation");
            return new NormalExitRetainedObserver(handle,new RetainedIdentity(BigInteger.valueOf(expected.pid()),expected.creation(),UUID.randomUUID().toString()),clock);
        }catch(IOException|RuntimeException|Error failure){try{handle.close();}catch(IOException|RuntimeException close){failure.addSuppressed(close);}throw failure;}
    }
    public RetainedIdentity identity(){return identity;}
    public static BigInteger monotonicNow(){return unsigned(System.nanoTime());}
    private static BigInteger unsigned(long value){return new BigInteger(Long.toUnsignedString(value));}
    private void open(){require(!closed,"original retained normal-exit handle is closed");}
    private boolean identityCurrent()throws IOException{return original.identity().equals(new Identity(identity.pid().longValueExact(),identity.creationFiletime()));}
    public synchronized ObjectNode verifyBeforeConfirm()throws IOException{
        open();require(identityCurrent(),"original retained handle identity changed before confirmation");long wait=dword(original.waitZero());
        require(wait==TIMEOUT,"original process is not proven running before confirmation (WAIT_TIMEOUT required)");
        var result=identityJson();return result.put("wait_result",wait).put("verified_monotonic_ns",unsigned(clock.getAsLong())).put("observation_clock_domain","driver_monotonic_v1");
    }
    public synchronized ProcessObservation observe(int timeoutMs){
        open();require(timeoutMs>=0&&timeoutMs<=5000,"bounded process-only observation wait required");var errors=new ArrayList<String>();boolean identityVerified=false;
        try{identityVerified=identityCurrent();if(!identityVerified)errors.add("original handle identity differs from its retained pin");}catch(IOException|RuntimeException failure){errors.add("identity: "+failure);}
        long wait=FAILED,start=clock.getAsLong();
        try{
            do{wait=dword(original.waitZero());if(wait!=TIMEOUT||timeoutMs==0||clock.getAsLong()-start>=timeoutMs*1_000_000L)break;Thread.sleep(10);}while(true);
        }catch(InterruptedException interrupted){Thread.currentThread().interrupt();wait=FAILED;errors.add("wait: interrupted");}
        catch(IOException|RuntimeException failure){wait=FAILED;errors.add("wait: "+failure);}
        // Independent even if wait timed out/failed. In particular code259 is not evidence of liveness.
        OptionalLong code=OptionalLong.empty();try{code=OptionalLong.of(dword(original.exitCode()));}catch(IOException|RuntimeException failure){errors.add("exit_code: "+failure);}
        WaitState state=wait==SIGNALED?WaitState.SIGNALED:wait==TIMEOUT?WaitState.TIMEOUT:WaitState.FAILED;
        return new ProcessObservation(identity,wait,state,code,identityVerified,identityVerified&&state==WaitState.SIGNALED&&code.isPresent(),unsigned(clock.getAsLong()),timeoutMs,state==WaitState.TIMEOUT,"driver_monotonic_v1",errors);
    }
    public ObjectNode identityJson(){return StrictJson.object().put("pid",identity.pid()).put("creation_filetime_100ns",identity.creationFiletime()).put("retained_handle_token",identity.handleToken());}
    public static ObjectNode json(ProcessObservation value){var result=StrictJson.object().put("pid",value.identity().pid()).put("creation_filetime_100ns",value.identity().creationFiletime()).put("retained_handle_token",value.identity().handleToken())
            .put("wait_result",value.waitResult()).put("wait_state",value.waitState().name().toLowerCase(java.util.Locale.ROOT)).put("process_identity_verified",value.identityVerified()).put("process_exit_observed",value.exitObserved())
            .put("observed_monotonic_ns",value.observedMonotonicNs()).put("timeout_ms",value.timeoutMs()).put("observation_deadline_reached",value.deadlineReached()).put("observation_clock_domain",value.clockDomain());
        if(value.exitCode().isPresent())result.put("exit_code",value.exitCode().getAsLong());else result.putNull("exit_code");var errors=result.putArray("errors");value.errors().forEach(errors::add);return result;}
    public synchronized Optional<String> closeError(){return closeError;}
    @Override public synchronized void close(){if(closed)return;closed=true;try{original.close();}catch(IOException|RuntimeException failure){closeError=Optional.of(failure.toString());}}
    private static long dword(long value){require(value>=0&&value<=0xffff_ffffL,"unsigned DWORD required");return value;}
}
