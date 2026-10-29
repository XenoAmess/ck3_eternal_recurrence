package org.xar.ck3.control.service.root;
import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol;
/** Controlled OS boundary exercises the actual retained-handle producer; never a Managed/Core qualification. */
final class NormalExitRetainedObserverTest{
    static final class Api implements NormalExitRetainedObserver.Api,NormalExitRetainedObserver.Handle{
        int opens,closes,waits,codes;long wait=258,code=259;boolean failWait;NormalExitRetainedObserver.Identity identity=new NormalExitRetainedObserver.Identity(41,new BigInteger("133700000000000001"));
        public NormalExitRetainedObserver.Handle open(long pid){assertEquals(41,pid);opens++;return this;}public NormalExitRetainedObserver.Identity identity(){return identity;}
        public long waitZero()throws IOException{waits++;if(failWait)throw new IOException("actual controlled wait failure");return wait;}public long exitCode(){codes++;return code;}public void close(){closes++;}
    }
    private static NormalExitRetainedObserver pin(Api api)throws IOException{var clock=new AtomicLong(10);return NormalExitRetainedObserver.capture(api,api.identity,()->clock.getAndAdd(10_000_000_000L));}
    @Test void originalHandleTimeoutIsRequiredBeforeConfirmAndWait0Code259IsAnExit()throws Exception{
        var api=new Api();var owner=pin(api);assertEquals(258,owner.verifyBeforeConfirm().get("wait_result").intValue());api.wait=0;api.code=259;
        var process=owner.observe(0);assertTrue(process.exitObserved());assertEquals(259,process.exitCode().orElseThrow());
        var facts=NormalExitProtocol.classify(Optional.empty(),process,Optional.empty(),owner.identity());assertTrue(facts.processExitObserved());assertFalse(facts.typedNormalExitObserved());
        assertEquals(NormalExitProtocol.FactStatus.PROCESS_EXIT_OBSERVED_NONZERO,facts.status());assertEquals(1,api.opens);assertEquals(0,api.closes);owner.close();owner.close();assertEquals(1,api.closes);
    }
    @Test void identityDriftAndSignalBeforeConfirmDoNotCreateAReadyPin()throws Exception{
        var api=new Api();var owner=pin(api);api.wait=0;assertThrows(IllegalArgumentException.class,owner::verifyBeforeConfirm);api.wait=258;
        api.identity=new NormalExitRetainedObserver.Identity(41,new BigInteger("133700000000000002"));assertThrows(IllegalArgumentException.class,owner::verifyBeforeConfirm);assertFalse(owner.observe(0).identityVerified());owner.close();
    }
    @Test void failedWaitStillReadsIndependentExitCodeWithoutReopeningOrClosing()throws Exception{
        var api=new Api();var owner=pin(api);api.failWait=true;var result=owner.observe(0);assertFalse(result.exitObserved());assertEquals(259,result.exitCode().orElseThrow());assertEquals(1,api.codes);assertEquals(1,api.opens);assertEquals(0,api.closes);owner.close();
    }
    @Test void failedDurabilityRetainsOriginalHandleAndSuccessfulReadbackClosesOnlyAfterFact()throws Exception{
        var api=new Api();var owner=pin(api);api.wait=0;api.code=0;var process=owner.observe(0);var fact=new RawJson("{\"actual_controlled_exit\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var failing=new NormalExitRetainedObserver.FactStore(){public ExactRef preserve(RawJson value)throws IOException{throw new IOException("real fact store failed before durability");}public RawJson read(ExactRef ref){throw new AssertionError();}};
        assertThrows(IOException.class,()->NormalExitRetainedObserver.preserveBeforeClose(owner,process,fact,failing));assertEquals(0,api.closes);
        var store=new NormalExitRetainedObserver.FactStore(){public ExactRef preserve(RawJson value){assertEquals(0,api.closes);return new ExactRef("controlled-fact",value.bytes().length,ActionCodec.sha256(value.bytes()));}public RawJson read(ExactRef ref){assertEquals(0,api.closes);return fact;}};
        NormalExitRetainedObserver.preserveBeforeClose(owner,process,fact,store);assertEquals(1,api.closes);assertThrows(IllegalArgumentException.class,()->owner.observe(0));assertEquals(1,api.opens);
    }
}
