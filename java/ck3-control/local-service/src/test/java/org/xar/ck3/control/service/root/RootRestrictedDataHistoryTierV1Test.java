package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.logging.Handler;
import java.util.logging.Level;
import java.util.logging.LogRecord;
import java.util.logging.Logger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverPersistentPlanningState.RetainedDataReplayAccess;
import org.xar.ck3.control.continuity.writer.ArchiveOriginalEvidencePort;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive.RootDataHistoryTier;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Genuine private Root token and real owned Win32 CAS. This grants no Game, Native, writer or retirement authority. */
final class RootRestrictedDataHistoryTierV1Test {
    @TempDir Path root;
    private static final RawJson BODY=body(0);
    private static final ActionPorts.HistoricalReadLimits TINY=new ActionPorts.HistoricalReadLimits(4,128L<<10,12);
    private static final Object METRICS_LOCK=new Object();

    @Test void genericBoundsStayClosedAndTheRealRootTierReportsItsActualStoreLimits()throws Exception {
        assertThrows(ContractViolationException.class,()->new ActionPorts.HistoricalReadLimits(16384,256L<<20,16384));
        assertThrows(ContractViolationException.class,()->new ActionPorts.HistoricalReadLimits(8192,256L<<20,32772));
        assertThrows(ContractViolationException.class,()->new ActionPorts.HistoricalReadLimits(1,(256L<<20)+1,4));
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("actual-tier"),false)){
            int actions=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();
            var ref=new AtomicReference<ExactRef>();
            List<Map<String,Long>> metrics=captureMetrics(()->fixture.writer.locked(same->{
                ref.set(fixture.archive.preserveMaterial(BODY));
                ExactRef head=same.persistedHead();writeQualification(Path.of(head.path()),true);
                try(var owner=owner(fixture,same)){
                    var data=owner.archive();var source=owner.dataReplaySource();
                    data.inSameGameHistoricalRecoveryScope(same,scoped->{
                        assertSame(data,scoped);assertFalse(scoped instanceof NativeOutcomeArchive);assertNull(scoped.scopedDriverDecoder());
                        writeQualification(Path.of(head.path()),false);
                        var access=source.openAccess(scoped,same);assertNotNull(access);assertTrue(access.accepts(scoped));access.requireCurrent();
                        Object first=access.beginCapture();Set<ExactRef> dependencies;
                        try{assertEquals(BODY,scoped.loadMaterial(ref.get()));dependencies=access.dependencies(first).orElseThrow();assertEquals(Set.of(ref.get()),dependencies);}
                        finally{access.closeCapture(first);}
                        pairQualification(ref.get(),false);
                        Object propagated=access.beginCapture();
                        try{assertTrue(access.verify(dependencies));assertEquals(dependencies,access.dependencies(propagated).orElseThrow());}
                        finally{access.closeCapture(propagated);}
                        assertThrows(UnsupportedOperationException.class,()->scoped.preserveRequest(null));
                        assertThrows(UnsupportedOperationException.class,()->scoped.preserveRead(null));
                        access.requireCurrent();return true;
                    });
                    pairQualification(ref.get(),true);writeQualification(Path.of(head.path()),true);
                }
                return null;
            }));
            assertEquals(1,metrics.size(),metrics.toString());Map<String,Long> actual=metrics.getFirst();
            // These are emitted by the actual Store after the View-selected scope completed, not enum getter mirrors.
            assertEquals(16384L,metric(actual,"maximum_entries"));assertEquals(256L<<20,metric(actual,"maximum_retained_bytes"));
            assertEquals(32772L,metric(actual,"maximum_handles"));assertTrue(metric(actual,"publication_attempts")>0);
            assertTrue(metric(actual,"acquired_retained")>0);assertTrue(metric(actual,"peak_entries")>0);
            assertEquals(1,metric(actual,"finish_succeeded"));assertEquals(0,metric(actual,"validation_failed"));
            assertEquals(actions,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());pairQualification(ref.get(),true);
        }
    }

    @Test void privateRootTierRequiresItsExactViewLiveSessionAndOwningThread()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("owner"),false);var other=new ActionWriterIntegrationFixture(root.resolve("foreign"),false)){
            var foreignSession=new CompletableFuture<ContinuityStorePort.Session>();var release=new CountDownLatch(1);
            var foreignOwner=CompletableFuture.runAsync(()->{
                try{other.writer.locked(foreign->{
                    foreignSession.complete(foreign);
                    try{if(!release.await(30,TimeUnit.SECONDS))throw new IOException("foreign test session was not released");}
                    catch(InterruptedException failure){Thread.currentThread().interrupt();throw new IOException("foreign test session interrupted",failure);}
                    return null;
                });}catch(IOException|RuntimeException failure){foreignSession.completeExceptionally(failure);throw new CompletionException(failure);}
            });
            try{
                var foreign=foreignSession.get(10,TimeUnit.SECONDS);
                fixture.writer.locked(same->{
                    try(var owner=owner(fixture,same);var otherView=owner(fixture,same)){
                        var source=owner.dataReplaySource();var data=owner.archive();var calls=new AtomicInteger();
                        ActionPorts.CheckedArchiveRead<Boolean> work=ignored->{calls.incrementAndGet();return true;};
                        assertThrows(Exception.class,()->fixture.archive.inRootDataHistoricalRecoveryScope(null,data,same,RootDataHistoryTier.V1,work));
                        assertThrows(Exception.class,()->source.inHistoricalRecoveryScope(data,same,null,work));
                        assertThrows(Exception.class,()->source.inHistoricalRecoveryScope(null,same,RootDataHistoryTier.V1,work));
                        assertThrows(Exception.class,()->source.inHistoricalRecoveryScope(fixture.archive,same,RootDataHistoryTier.V1,work));
                        assertThrows(Exception.class,()->source.inHistoricalRecoveryScope(otherView.archive(),same,RootDataHistoryTier.V1,work));
                        assertThrows(Exception.class,()->source.inHistoricalRecoveryScope(data,null,RootDataHistoryTier.V1,work));
                        assertNotSame(same,foreign);assertFalse(foreignOwner.isDone(),"foreign Session must really remain held by its owning thread");
                        assertThrows(Exception.class,()->source.inHistoricalRecoveryScope(data,foreign,RootDataHistoryTier.V1,work));
                        var crossedThread=CompletableFuture.supplyAsync(()->{
                            try{return source.inHistoricalRecoveryScope(data,same,RootDataHistoryTier.V1,work);}
                            catch(IOException failure){throw new CompletionException(failure);}
                        });
                        assertThrows(java.util.concurrent.ExecutionException.class,()->crossedThread.get(10,TimeUnit.SECONDS));
                        assertEquals(0,calls.get(),"a token, facade or enum value cannot manufacture a permitted callback");
                        assertTrue(data.<Boolean>inSameGameHistoricalRecoveryScope(same,scoped->{assertSame(data,scoped);return true;}));
                    }
                    return null;
                });
            }finally{release.countDown();foreignOwner.get(10,TimeUnit.SECONDS);}
        }
    }

    @Test void caughtWritePoisonsTheRootReadScopeAndNormalOrExceptionalCloseReleasesRealPairs()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("close"),false)){
            var ref=new AtomicReference<ExactRef>();var ledger=new AtomicReference<byte[]>();int actions=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();
            fixture.writer.locked(same->{
                ref.set(fixture.archive.preserveMaterial(BODY));ledger.set(fixture.ledgerBytes());
                ExactRef head=same.persistedHead();writeQualification(Path.of(head.path()),true);
                try(var owner=owner(fixture,same)){
                    var data=owner.archive();
                    assertTrue(data.<Boolean>inSameGameHistoricalRecoveryScope(same,scoped->{assertEquals(BODY,scoped.loadMaterial(ref.get()));pairQualification(ref.get(),false);writeQualification(Path.of(head.path()),false);return true;}));
                    pairQualification(ref.get(),true);writeQualification(Path.of(head.path()),true);
                    IOException marker=new IOException("owned Root V1 callback failure");
                    assertSame(marker,assertThrows(IOException.class,()->data.inSameGameHistoricalRecoveryScope(same,scoped->{
                        assertEquals(BODY,scoped.loadMaterial(ref.get()));pairQualification(ref.get(),false);writeQualification(Path.of(head.path()),false);throw marker;
                    })));
                    pairQualification(ref.get(),true);writeQualification(Path.of(head.path()),true);
                    assertThrows(IOException.class,()->data.inSameGameHistoricalRecoveryScope(same,scoped->{
                        assertEquals(BODY,scoped.loadMaterial(ref.get()));pairQualification(ref.get(),false);writeQualification(Path.of(head.path()),false);
                        assertThrows(RuntimeException.class,()->scoped.preserveMaterial(body(99)));return true;
                    }));
                    pairQualification(ref.get(),true);writeQualification(Path.of(head.path()),true);
                }
                return null;
            });
            assertArrayEquals(ledger.get(),fixture.ledgerBytes());assertArrayEquals(BODY.bytes(),Files.readAllBytes(Path.of(ref.get().path())));
            assertEquals(actions,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());
        }
    }

    @Test void scaledPayloadRotationPreservesCustodyAndEntryFallbackCannotHealADisqualifiedTrace()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("rotation"),false)){
            RawJson firstBody=largeBody(1),secondBody=largeBody(2);
            fixture.writer.locked(same->{
                ExactRef firstRef=fixture.archive.preserveMaterial(firstBody),secondRef=fixture.archive.preserveMaterial(secondBody);
                try(var owner=owner(fixture,same)){
                    var data=owner.archive();var source=owner.dataReplaySource();
                    data.inHistoricalReadScope(same,TINY,scoped->{
                        assertSame(data,scoped);var access=source.openAccess(scoped,same);assertNotNull(access);
                        Object first=access.beginCapture();
                        try{assertEquals(firstBody,scoped.loadMaterial(firstRef));assertEquals(Set.of(firstRef),access.dependencies(first).orElseThrow());}
                        finally{access.closeCapture(first);}
                        assertEquals(secondBody,scoped.loadMaterial(secondRef));
                        pairQualification(firstRef,false);pairQualification(secondRef,false);
                        Object propagated=access.beginCapture();
                        try{
                            assertTrue(access.verify(Set.of(firstRef)),"payload pressure must not retire original custody");
                            assertEquals(Set.of(firstRef),access.dependencies(propagated).orElseThrow());
                        }finally{access.closeCapture(propagated);}
                        byte[] cold=scoped.loadMaterial(firstRef).bytes();assertArrayEquals(firstBody.bytes(),cold);
                        cold[cold.length-3]^=1;assertArrayEquals(firstBody.bytes(),scoped.loadMaterial(firstRef).bytes());
                        pairQualification(firstRef,false);pairQualification(secondRef,false);return true;
                    });
                    pairQualification(firstRef,true);pairQualification(secondRef,true);
                    var entryLimited=new ActionPorts.HistoricalReadLimits(1,128L<<10,12);
                    data.inHistoricalReadScope(same,entryLimited,scoped->{
                        var access=source.openAccess(scoped,same);assertNotNull(access);
                        assertEquals(firstBody,scoped.loadMaterial(firstRef));pairQualification(firstRef,false);
                        Object incomplete=access.beginCapture();
                        try{
                            assertEquals(secondBody,scoped.loadMaterial(secondRef));pairQualification(secondRef,true);
                            assertTrue(access.dependencies(incomplete).isEmpty(),"a fallback original has no continuously held dependency");
                            assertEquals(firstBody,scoped.loadMaterial(firstRef));pairQualification(firstRef,false);
                            Object nested=access.beginCapture();
                            try{assertTrue(access.verify(Set.of(firstRef)));assertEquals(Set.of(firstRef),access.dependencies(nested).orElseThrow());}
                            finally{access.closeCapture(nested);}
                            assertTrue(access.dependencies(incomplete).isEmpty(),"held and nested dependencies cannot heal the disqualified outer trace");
                        }finally{access.closeCapture(incomplete);}
                        Object fresh=access.beginCapture();
                        try{assertEquals(firstBody,scoped.loadMaterial(firstRef));assertTrue(access.verify(Set.of(firstRef)));assertEquals(Set.of(firstRef),access.dependencies(fresh).orElseThrow());}
                        finally{access.closeCapture(fresh);}
                        pairQualification(firstRef,false);pairQualification(secondRef,true);return true;
                    });
                    pairQualification(firstRef,true);pairQualification(secondRef,true);
                }
                return null;
            });
        }
    }

    @Test void endingTheRealOwnerDuringWorkCannotPassTheFinalAuthorityCheckOrReviveAnOldAccess()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("authority-end"),false)){
            fixture.writer.locked(same->{
                ExactRef original=fixture.archive.preserveMaterial(BODY);var oldAccess=new AtomicReference<RetainedDataReplayAccess>();
                try(var owner=owner(fixture,same)){
                    var source=owner.dataReplaySource();var data=owner.archive();
                    data.inSameGameHistoricalRecoveryScope(same,scoped->{oldAccess.set(source.openAccess(scoped,same));assertNotNull(oldAccess.get());assertEquals(BODY,scoped.loadMaterial(original));return true;});
                    pairQualification(original,true);assertThrows(Exception.class,()->oldAccess.get().requireCurrent());
                    assertThrows(Exception.class,()->data.inSameGameHistoricalRecoveryScope(same,scoped->{
                        assertEquals(BODY,scoped.loadMaterial(original));pairQualification(original,false);owner.close();return true;
                    }));
                    pairQualification(original,true);assertThrows(IllegalStateException.class,()->data.loadMaterial(original));
                    assertThrows(Exception.class,()->source.openAccess(data,same));
                }
                return null;
            });
        }
    }

    private static RootReservedRetirementArchive owner(ActionWriterIntegrationFixture fixture,ContinuityStorePort.Session same){
        return RootReservedRetirementArchive.create(fixture.archive,same,new ArchiveOriginalEvidencePort(fixture.archive),()->{
            try{fixture.writer.requireSession(same);}catch(IOException failure){throw new UncheckedIOException(failure);}
        },"software-parent","1".repeat(64));
    }
    private static RawJson body(int index){return new RawJson(("["+index+"]").getBytes(StandardCharsets.UTF_8));}
    private static RawJson largeBody(int index){return new RawJson(("{\"id\":"+index+",\"padding\":\""+"x".repeat(80*1024)+"\"}").getBytes(StandardCharsets.UTF_8));}
    @FunctionalInterface private interface Work {void run()throws Exception;}
    private static List<Map<String,Long>> captureMetrics(Work operation)throws Exception {
        synchronized(METRICS_LOCK){
            Logger logger=Logger.getLogger("org.xar.ck3.control.continuity.writer.ImmutableArtifactStore");Level prior=logger.getLevel();
            var result=new ArrayList<Map<String,Long>>();long thread=Thread.currentThread().threadId();
            Handler handler=new Handler(){
                @Override public void publish(LogRecord record){
                    if(record.getLongThreadID()!=thread||!record.getMessage().startsWith("HISTORICAL_CAS_METRICS "))return;
                    Map<String,Long> fields=new HashMap<>();var tokens=java.util.regex.Pattern.compile("([a-z_]+)=([0-9]+)").matcher(record.getMessage());
                    while(tokens.find())fields.put(tokens.group(1),Long.parseLong(tokens.group(2)));result.add(Map.copyOf(fields));
                }
                @Override public void flush(){ }
                @Override public void close(){ }
            };
            handler.setLevel(Level.ALL);logger.addHandler(handler);logger.setLevel(Level.INFO);
            try{operation.run();}finally{logger.removeHandler(handler);logger.setLevel(prior);handler.close();}
            return List.copyOf(result);
        }
    }
    private static long metric(Map<String,Long> row,String name){assertTrue(row.containsKey(name),row.toString());return row.get(name);}
    private static void pairQualification(ExactRef ref,boolean allowed)throws IOException {
        Path payload=Path.of(ref.path());writeQualification(payload.resolveSibling(ref.sha256()+".commit.json"),allowed);writeQualification(payload,allowed);
    }
    /** GENERIC_WRITE and OPEN_EXISTING qualify sharing only, write no bytes, and close every successful handle. */
    private static void writeQualification(Path path,boolean allowed)throws IOException {
        HANDLE handle=Kernel32.INSTANCE.CreateFile(path.toAbsolutePath().toString(),0x40000000,1|2|4,null,3,0x80,null);int error=Kernel32.INSTANCE.GetLastError();
        if(handle==null||WinBase.INVALID_HANDLE_VALUE.equals(handle)){
            if(allowed)throw new IOException("owned qualification failed Win32="+error+": "+path);
            assertEquals(32,error,"only ERROR_SHARING_VIOLATION proves held custody");return;
        }
        if(!Kernel32.INSTANCE.CloseHandle(handle))throw new IOException("owned qualification CloseHandle failed Win32="+Kernel32.INSTANCE.GetLastError());
        assertTrue(allowed,"retained commit or payload was writable while its Root scope was active: "+path);
    }
}
