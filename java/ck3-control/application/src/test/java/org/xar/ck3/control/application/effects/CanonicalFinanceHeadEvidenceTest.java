package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/** Executes the real finance head producer; a canonical archive lookup cannot substitute for readPinned. */
final class CanonicalFinanceHeadEvidenceTest {
    private static ExactRef ref(String name,byte[] bytes) {
        return new ExactRef(Path.of("target",name).toAbsolutePath().toString(),bytes.length,ActionCodec.sha256(bytes));
    }
    private static WriterContracts.Pin pin(ExactRef ref) {
        return new WriterContracts.Pin(ref,new WriterContracts.FileIdentity("10","18446744073709551614","133700000000000001","2026-10-23T18:45:00Z",ref.bytes()));
    }
    private static ActionPorts.OutcomeArchive archive(byte[] expected,AtomicInteger preserved) {
        ExactRef archived=ref("canonical-archive-material.json",expected);var saved=new AtomicReference<RawJson>();
        return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
            if(method.getName().equals("preserveMaterial")) { assertArrayEquals(expected,((RawJson)args[0]).bytes());saved.set((RawJson)args[0]);preserved.incrementAndGet();return archived; }
            if(method.getName().equals("loadMaterial")) { assertEquals(archived,args[0]);return saved.get(); }
            throw new AssertionError("unexpected archive path "+method.getName());
        });
    }
    @Test void actualWriterOriginalBytesArePreservedWithoutReencodingOrArbitraryArchiveReads() throws Exception {
        byte[] raw="\ufeff{  \"sequence\":18446744073709551615, \"pending\":null }\n".getBytes(StandardCharsets.UTF_8);
        ExactRef original=ref("mutable-writer-head.json",raw);var pin=pin(original);var reads=new AtomicInteger();var checked=new AtomicInteger();var preserved=new AtomicInteger();
        Session session=(Session)Proxy.newProxyInstance(Session.class.getClassLoader(),new Class<?>[]{Session.class},(proxy,method,args)->switch(method.getName()) {
            case "persistedHead"->original;
            case "capturePin"->{assertEquals(original,args[0]);yield pin;}
            case "verifyPin"->{assertEquals(pin,args[0]);checked.incrementAndGet();yield null;}
            case "readPinned"->{assertEquals(pin,args[0]);reads.incrementAndGet();yield raw.clone();}
            default->throw new AssertionError("unexpected writer path "+method.getName());
        });
        ExactRef frozen=CanonicalFinanceHeadEvidence.preserve(session,original,archive(raw,preserved),1048576);
        assertNotEquals(original.path(),frozen.path());assertEquals(original.sha256(),frozen.sha256());assertEquals(1,reads.get());assertEquals(1,preserved.get());assertEquals(2,checked.get());
    }
    @Test void unavailableOrChangedPinnedOriginalDoesNotBecomeArchivedQualification() {
        byte[] raw="{\"sequence\":1}".getBytes(StandardCharsets.UTF_8);ExactRef original=ref("head.json",raw);var pin=pin(original);
        for(boolean unavailable:new boolean[]{true,false}) {
            var preserved=new AtomicInteger();Session session=(Session)Proxy.newProxyInstance(Session.class.getClassLoader(),new Class<?>[]{Session.class},(proxy,method,args)->switch(method.getName()) {
                case "persistedHead"->original;
                case "capturePin"->pin;
                case "verifyPin"->null;
                case "readPinned"->{if(unavailable)throw new IOException("original identity unavailable");yield new byte[]{'{','}'};}
                default->throw new AssertionError(method.getName());
            });
            if(unavailable)assertThrows(IOException.class,()->CanonicalFinanceHeadEvidence.preserve(session,original,archive(raw,preserved),1048576));
            else assertThrows(IllegalArgumentException.class,()->CanonicalFinanceHeadEvidence.preserve(session,original,archive(raw,preserved),1048576));
            assertEquals(0,preserved.get());
        }
    }
}
