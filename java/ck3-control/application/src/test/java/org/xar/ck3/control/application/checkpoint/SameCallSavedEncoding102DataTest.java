package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;

final class SameCallSavedEncoding102DataTest {
    @Test void exactSavedOperandIsEncodedOnceOnlyWithinTheOriginalStrictLocalScope() throws Exception {
        byte[] raw=resource("driver1475.json.gz",8*1024*1024);
        assertEquals(5255697,raw.length);
        assertEquals("092b7df37ab70b5d28981b1c681fbf96cc1e58f0029706bab15fd741adc705f4",sha(raw));
        byte[] pairRaw=resource("pair1475.json.gz",1024*1024);
        assertEquals(1825,pairRaw.length);
        CheckpointPair pair=CheckpointPairCodec.decode(pairRaw);
        DriverStateSnapshot.Complete saved=DriverStateSnapshot.decodeComplete(raw);
        assertEquals(229,saved.commandHistory().size());
        assertEquals(229,pair.historyIndex());
        // This local prefix is projection DATA, not a canonical historical writer or a physical permit.
        DriverStateSnapshot.Complete before=withHistory(saved,saved.commandHistory().subList(0,228));

        AtomicInteger originalCalls=new AtomicInteger();
        byte[] originalEncoding=CheckpointCommitVerifier.saveProjectionEncoding(before,saved,pair,originalCalls::incrementAndGet);
        CheckpointCommitVerifier.requireCombinedSaveDriver(saved,saved,null,originalCalls::incrementAndGet);
        assertEquals(2,originalCalls.get(),"original target saved operand is encoded twice");

        AtomicInteger reusedCalls=new AtomicInteger();
        byte[] first=CheckpointCommitVerifier.saveProjectionEncoding(before,saved,pair,reusedCalls::incrementAndGet);
        Map.Entry<DriverStateSnapshot.Complete,byte[]> once=CheckpointCommitVerifier.sameCallSavedEncoding(before,saved,first);
        assertNotNull(once);
        assertSame(saved,once.getKey());
        assertArrayEquals(originalEncoding,once.getValue());
        CheckpointCommitVerifier.requireCombinedSaveDriver(saved,saved,once,reusedCalls::incrementAndGet);
        assertEquals(1,reusedCalls.get(),"only the duplicate target operand is skipped, not the combined encoder");
        assertNull(once.getValue());
        CheckpointCommitVerifier.requireCombinedSaveDriver(saved,saved,once,reusedCalls::incrementAndGet);
        assertEquals(2,reusedCalls.get(),"a consumed holder cannot skip another encode");

        DriverStateSnapshot.Complete small=small(BigInteger.valueOf(31254));
        DriverStateSnapshot.Complete equalOther=small(BigInteger.valueOf(31254));
        AtomicInteger counter=new AtomicInteger();
        byte[] encoded=CheckpointCommitVerifier.saveProjectionEncoding(small,small,pair,counter::incrementAndGet);
        var foreign=CheckpointCommitVerifier.sameCallSavedEncoding(small,small,encoded);
        CheckpointCommitVerifier.requireCombinedSaveDriver(equalOther,equalOther,foreign,counter::incrementAndGet);
        assertEquals(2,counter.get(),"equal values with a different identity use the fixed encoder");
        assertNull(foreign.getValue());

        var changed=withSession(small,new DriverStateSnapshot.Session(small.session().pipeName(),
                small.session().bridgePid(),small.session().actorId(),"different-episode"));
        var mismatch=CheckpointCommitVerifier.sameCallSavedEncoding(small,small,encoded);
        RuntimeException rejected=assertThrows(RuntimeException.class,()->
                CheckpointCommitVerifier.requireCombinedSaveDriver(small,changed,mismatch,null));
        assertEquals("combined canonical SAVE Driver differs from the verified complete projection",rejected.getMessage());
        assertNull(mismatch.getValue(),"the owned bytes are consumed even when the original comparison rejects");
        assertThrows(RuntimeException.class,()->CheckpointCommitVerifier.saveProjectionEncoding(small,changed,pair,null));

        var nonplain=small(new BigInteger("31254") { });
        counter.set(0);
        byte[] nonplainBytes=CheckpointCommitVerifier.saveProjectionEncoding(nonplain,nonplain,pair,counter::incrementAndGet);
        assertNull(CheckpointCommitVerifier.sameCallSavedEncoding(nonplain,nonplain,nonplainBytes));
        assertNull(CheckpointCommitVerifier.sameCallSavedEncoding(nonplain,small,encoded));
        CheckpointCommitVerifier.requireCombinedSaveDriver(nonplain,nonplain,null,counter::incrementAndGet);
        assertEquals(2,counter.get());

        // The oversized buffer tests retention eligibility only; it is not claimed as a Driver encoding.
        assertNull(CheckpointCommitVerifier.sameCallSavedEncoding(small,small,new byte[8*1024*1024+1]));
        var failing=CheckpointCommitVerifier.sameCallSavedEncoding(small,small,encoded);
        RuntimeException originalFailure=new RuntimeException("original DATA encoder completion failure");
        RuntimeException seen=assertThrows(RuntimeException.class,()->CheckpointCommitVerifier.requireCombinedSaveDriver(
                equalOther,equalOther,failing,()->{throw originalFailure;}));
        assertSame(originalFailure,seen);
        assertNull(failing.getValue());
        CheckpointCommitVerifier.requireSaveProjection(before,saved,pair);
    }

    private static DriverStateSnapshot.Complete small(BigInteger actor) {
        var session=new DriverStateSnapshot.Session("\\\\.\\pipe\\p102-data",102152,actor,"p102-data-episode");
        var history=List.of(new DriverStateSnapshot.HistoryEntry(1,
                new DriverStateSnapshot.Value("{\"index\":1}".getBytes(StandardCharsets.UTF_8))));
        var nil=new DriverStateSnapshot.NullValue();
        return new DriverStateSnapshot.Complete(session,history,nil,nil,nil,nil,nil,nil,
                new DriverStateSnapshot.Value("[]".getBytes(StandardCharsets.UTF_8)));
    }
    private static DriverStateSnapshot.Complete withHistory(DriverStateSnapshot.Complete source,
            List<DriverStateSnapshot.HistoryEntry> history) {
        return new DriverStateSnapshot.Complete(source.session(),history,source.lastCheckpoint(),source.rollbackWarFailure(),
                source.managedRestoreTransaction(),source.successionExpectation(),source.successionLifecycle(),
                source.campaignGoal(),source.rollbackWarFailures());
    }
    private static DriverStateSnapshot.Complete withSession(DriverStateSnapshot.Complete source,DriverStateSnapshot.Session session) {
        return new DriverStateSnapshot.Complete(session,source.commandHistory(),source.lastCheckpoint(),source.rollbackWarFailure(),
                source.managedRestoreTransaction(),source.successionExpectation(),source.successionLifecycle(),
                source.campaignGoal(),source.rollbackWarFailures());
    }
    private static byte[] resource(String name,int maximum) throws IOException {
        var input=SameCallSavedEncoding102DataTest.class.getResourceAsStream("encoding102/"+name);
        if(input==null)throw new IOException("exact P102 DATA resource absent: "+name);
        try(var zip=new GZIPInputStream(input)) {
            byte[] raw=zip.readNBytes(maximum+1);
            if(raw.length==0||raw.length>maximum||zip.read()!=-1)throw new IOException("bounded exact DATA resource required");
            return raw;
        }
    }
    private static String sha(byte[] raw) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }
}
