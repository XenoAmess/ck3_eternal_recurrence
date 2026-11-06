package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;

/** Genuine Driver/pair bytes; enrolled file operations below are unissued DATA, never Win32 or Root qualification. */
final class SameCallSavedDriverRecheck97Test {
    @Test void sameCallSkipsOnlyTheEqualImmutableDecodeAndKeepsEveryPhysicalRecheck() throws Exception {
        byte[] raw=resource("driver1475.json.gz");
        assertEquals(5255697,raw.length);
        assertEquals("092b7df37ab70b5d28981b1c681fbf96cc1e58f0029706bab15fd741adc705f4",DriverCheckpointStore.sha256(raw));
        CheckpointPair pair=CheckpointPairCodec.decode(resource("pair1475.json.gz"));
        assertEquals(raw.length,pair.driver().reference().bytes());
        var expected=DriverStateSnapshot.decodeComplete(raw).session();
        AtomicInteger decoded=new AtomicInteger();
        List<String> twice=List.of("verify","ack","read","verify","verify","ack","read","verify");
        {
            var files=new DataFiles(pair,raw.clone());var read=files.store().readVerifiedOriginalForRecheck(pair,expected,decoded::incrementAndGet);
            assertEquals(1,decoded.get());assertEquals(expected,read.getKey().session());
            assertEquals(List.of("verify","ack","read","verify"),files.trace);
            read.getValue().close();assertEquals(1,decoded.get());assertEquals(twice,files.trace);
            read.getValue().close();assertEquals(2,decoded.get());assertEquals(12,files.trace.size());
        }
        decoded.set(0);
        {
            var files=new DataFiles(pair,raw.clone());var read=files.store().readVerifiedOriginalForRecheck(pair,expected,decoded::incrementAndGet);
            // The raw-array provider is deliberately allowed to violate its physical hash promise here:
            // a different but valid lexical input must take strict decoding, never a ref-only shortcut.
            byte[] changed=new byte[raw.length+1];changed[0]=32;System.arraycopy(raw,0,changed,1,raw.length);files.raw=changed;
            read.getValue().close();assertEquals(2,decoded.get());assertEquals(twice,files.trace);
        }
        decoded.set(0);
        {
            var files=new DataFiles(pair,raw.clone());var read=files.store().readVerifiedOriginalForRecheck(pair,expected,decoded::incrementAndGet);
            files.raw[0]='!';
            assertThrows(IllegalArgumentException.class,()->read.getValue().close());
            files.raw=raw.clone();read.getValue().close();assertEquals(2,decoded.get());
        }
        decoded.set(0);
        {
            var files=new DataFiles(pair,raw.clone());var read=files.store().readVerifiedOriginalForRecheck(pair,expected,decoded::incrementAndGet);
            IOException original=new IOException("original second read failure");files.failure=original;
            assertSame(original,assertThrows(IOException.class,()->read.getValue().close()));
            assertEquals(1,decoded.get());files.failure=null;
            read.getValue().close();assertEquals(2,decoded.get());
            assertEquals(List.of("verify","ack","read","verify","verify","ack","read","verify","ack","read","verify"),files.trace);
        }
        decoded.set(0);
        {
            BigInteger actor=new BigInteger(expected.actorId().toString()) { @java.io.Serial private static final long serialVersionUID=1L; };
            var nonplain=new DriverStateSnapshot.Session(expected.pipeName(),expected.bridgePid(),actor,expected.episodeRunId());
            var files=new DataFiles(pair,raw.clone());var read=files.store().readVerifiedOriginalForRecheck(pair,nonplain,decoded::incrementAndGet);
            read.getValue().close();assertEquals(2,decoded.get());assertEquals(twice,files.trace);
        }
        decoded.set(0);
        {
            byte[] padded=new byte[8*1024*1024+1];Arrays.fill(padded,(byte)32);System.arraycopy(raw,0,padded,padded.length-raw.length,raw.length);
            var ref=new ExactRef(pair.driver().reference().path()+".overcap-DATA",padded.length,DriverCheckpointStore.sha256(padded));
            var driver=new CheckpointPair.FileWitness(ref,new FileStatIdentity(BigInteger.valueOf(padded.length),"1","1"));
            var large=new CheckpointPair(pair.save(),driver,pair.frame(),pair.lineageId(),pair.historyIndex(),pair.saveActionId(),pair.nativeAckRef(),pair.observedAt());
            var files=new DataFiles(large,padded);var read=files.store().readVerifiedOriginalForRecheck(large,expected,decoded::incrementAndGet);
            read.getValue().close();assertEquals(2,decoded.get());assertEquals(twice,files.trace);
        }
        System.out.println("SAVED_DRIVER_RECHECK_DATA_PASS equalDecode1/changedStrict/oneUse/errorClears/nonplain/overcap/freshPhysicalCalls");
    }
    private static byte[] resource(String name)throws IOException {
        try(var input=SameCallSavedDriverRecheck97Test.class.getResourceAsStream("recheck97/"+name)) {
            if(input==null)throw new IOException("exact DATA resource missing");
            try(var gzip=new GZIPInputStream(input)) {
                byte[] raw=gzip.readNBytes(8*1024*1024+1);
                if(raw.length==0||raw.length>8*1024*1024)throw new IOException("bounded actual fixture required");return raw;
            }
        }
    }
    private static final class DataFiles {
        final CheckpointPair pair;final List<String> trace=new ArrayList<>();byte[] raw;IOException failure;
        DataFiles(CheckpointPair pair,byte[] raw){this.pair=pair;this.raw=raw;}
        DriverCheckpointStore store() {
            CheckpointFiles files=(CheckpointFiles)Proxy.newProxyInstance(CheckpointFiles.class.getClassLoader(),new Class<?>[]{CheckpointFiles.class},(proxy,method,args)->{
                if(method.getDeclaringClass()==Object.class)return switch(method.getName()) {
                    case "toString"->"UNISSUED_CHECKPOINT_FILES_DATA";case "hashCode"->System.identityHashCode(proxy);case "equals"->proxy==args[0];default->throw new AssertionError(method);
                };
                return switch(method.getName()) {
                    case "verify"->{assertSame(pair,args[0]);trace.add("verify");yield null;}
                    case "observe"->{assertEquals(Path.of(pair.nativeAckRef().path()),args[0]);trace.add("ack");var ref=pair.nativeAckRef();yield Optional.of(new CheckpointPair.FileWitness(ref,new FileStatIdentity(BigInteger.valueOf(ref.bytes()),"1","1")));}
                    case "read"->{assertSame(pair.driver(),args[0]);assertEquals(DriverCheckpointStore.MAX_DRIVER_BYTES,args[1]);trace.add("read");if(failure!=null)throw failure;yield raw;}
                    default->throw new AssertionError("no other enrolled DATA file operation: "+method.getName());
                };
            });
            return new DriverCheckpointStore(files,Path.of(pair.driver().reference().path()),"UNISSUED_SOURCE_ONLY",new DriverCheckpointStore.SnapshotSupplier(){
                @Override public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work)throws IOException {throw new IOException("no SAVE producer is issued");}
            });
        }
    }
}
