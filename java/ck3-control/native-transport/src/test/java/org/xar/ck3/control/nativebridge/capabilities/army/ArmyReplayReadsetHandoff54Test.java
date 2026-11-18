package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.junit.jupiter.api.Assumptions.assumeTrue;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryReference.inReplayReadScope;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.time.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.SharedSourceFiles.DirectoryIdentity;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryReference.*;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryStore.StoredFile;

/** Unrun focused source. Real-Windows independent consumer lease tests physical handoff;
 * controlled faults test producer lifecycle only, never Root/Installed/Game availability. */
final class ArmyReplayReadsetHandoff54Test {
    @TempDir Path temporary;
    private static final Instant NOW=Instant.parse("2026-11-18T00:00:00Z");
    private static final ReplayReadLimits LIMITS=new ReplayReadLimits(8,1024*1024);
    private static final Path MEMORY=Path.of(".").toAbsolutePath().normalize().resolve("handoff54-software");
    private record Fixture(Path folder,Path path,byte[] bytes,RawJson numeric,RawJson summary) { }
    private static Fixture fixture(Path folder,int id)throws Exception {
        Path path=folder.resolve("army-query-"+String.format("%032x",id)+".json");
        RawJson numeric=new RawJson(("{\"step\":\"query-army-strengths-v1\",\"accepted\":true,\"query_sequence\":1,"
                +"\"queried_snapshot_id\":\"software\",\"queried_revision\":1,\"queried_native_revision\":1,\"army_strengths\":[]}")
                .getBytes(StandardCharsets.UTF_8));
        byte[] bytes=Arrays.copyOf(numeric.bytes(),numeric.byteLength()+1);bytes[bytes.length-1]=10;
        RawJson summary=ArmyQueryHistoryStore.buildSummary(numeric,Optional.of(new StoredFile(path,bytes.length,sha(bytes))),Optional.empty(),Optional.empty());
        return new Fixture(folder,path,bytes,numeric,summary);
    }
    private static String sha(byte[] bytes)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
    private static ReadResult read(Fixture f)throws IOException{return ArmyQueryHistoryReference.read(f.summary(),f.folder(),f.bytes().length);}
    @Test void realIndependentConsumerLeaseCoversTheWholeGapAfterProducerScopeExit()throws Exception {
        assumeTrue(Platform.isWindows());var f=fixture(temporary,1);Files.write(f.path(),f.bytes());
        var original=new AtomicReference<AuthenticatedReplayOriginal>();
        var consumer=new AtomicReference<IdentityBearingFileAttributes.ReadOnlyLease>();
        try {
            inReplayReadScope(LIMITS,Clock.fixed(NOW,ZoneOffset.UTC),NOW.plusSeconds(30),authenticated->{
                assertNull(original.get());authenticated.requireCurrent();
                var pin=authenticated.pin();assertEquals(f.bytes().length,pin.reference().bytes());
                var held=IdentityBearingFileAttributes.leaseBoundedWindows(Path.of(pin.reference().path()),Math.toIntExact(pin.reference().bytes()));
                consumer.set(held);var acquired=held.originalRead();
                try {assertEquals(pin.reference().sha256(),sha(acquired.bytes()));}
                catch(Exception failure){throw new IOException(failure);}
                var identity=(IdentityBearingFileAttributes.WindowsFileIdentity)acquired.attributes().fileKey();
                assertEquals(pin.identity().volumeSerialDecimal(),identity.volumeSerialDecimal());
                assertEquals(pin.identity().fileIdDecimal(),identity.fileIdDecimal());
                assertEquals(pin.identity().creationFiletimeDecimal(),identity.creationFiletimeDecimal());
                assertEquals(pin.identity().modifiedInstant(),acquired.attributes().lastModifiedTime().toInstant().toString());
                held.releaseOriginalBytes();authenticated.requireCurrent();original.set(authenticated);
            },()->{var first=read(f);assertSame(first,read(f));return first;});
            // Producer peer HANDLE is now closed. The independently owned consumer HANDLE still denies mutations.
            original.get().requireCurrent();consumer.get().verifyCurrent();
            assertThrows(IOException.class,()->Files.write(f.path(),new byte[]{0},StandardOpenOption.WRITE));
            assertThrows(IOException.class,()->Files.delete(f.path()));
            consumer.get().close();consumer.set(null);
            Files.delete(f.path());assertThrows(IOException.class,()->original.get().requireCurrent());
        }finally {if(consumer.get()!=null)consumer.get().close();}
    }
    @Test void onePrivateAuthenticatedObjectPerEntryAndItsPinIncludesArtifactLfExactly()throws Exception {
        var f=fixture(MEMORY,2);var io=new Identities(f);var leases=new Leases(f);var clock=new TestClock();
        var originals=new ArrayList<AuthenticatedReplayOriginal>();
        inReplayReadScope(LIMITS,clock,NOW.plusSeconds(30),io,leases,originals::add,()->{
            var first=read(f);assertSame(first,read(f));assertSame(first,read(f));return null;
        });
        assertEquals(1,originals.size());assertEquals(1,leases.opens);assertEquals(1,leases.reads);assertEquals(1,leases.closes);
        var original=originals.getFirst();original.requireCurrent();
        assertEquals(f.bytes().length,original.pin().reference().bytes());
        assertEquals(f.numeric().byteLength()+1,original.pin().reference().bytes());
        assertEquals(sha(f.bytes()),original.pin().reference().sha256());
        assertEquals("18446744073709551615",original.pin().identity().fileIdDecimal());
        assertEquals("1970-01-01T00:00:00.000000100Z",original.pin().identity().modifiedInstant());
        assertTrue(Arrays.stream(AuthenticatedReplayOriginal.class.getDeclaredConstructors()).allMatch(c->java.lang.reflect.Modifier.isPrivate(c.getModifiers())));
    }
    @Test void actualNoArmyPathDoesNotCreateAnExternalDependencyOrAcquireAHandle()throws Exception {
        var f=fixture(MEMORY,3);var io=new Identities(f);var leases=new Leases(f);
        inReplayReadScope(LIMITS,new TestClock(),NOW.plusSeconds(30),io,leases,
                original->{throw new AssertionError("no actual Army sidecar was read");},()->"no-Army-proof");
        assertEquals(0,leases.opens);assertEquals(0,io.verifications);
    }
    @Test void failedConsumerRetentionRejectsTheSourceProofAndClosesProducerPeerImmediately()throws Exception {
        var f=fixture(MEMORY,4);var leases=new Leases(f);var sent=new AtomicReference<AuthenticatedReplayOriginal>();
        IOException denied=new IOException("actual consumer readset admission failed");
        assertThrows(IOException.class,()->inReplayReadScope(LIMITS,new TestClock(),NOW.plusSeconds(30),new Identities(f),leases,
                original->{sent.set(original);throw denied;},()->{
                    assertSame(denied,assertThrows(IOException.class,()->read(f)));
                    assertEquals(1,leases.closes);return "cannot-be-sealed";
                }));
        assertThrows(IOException.class,()->sent.get().requireCurrent());
    }
    @Test void postScopeClockExpiryAndMetadataFailureRemainStickyEvenWhenLaterRestored()throws Exception {
        for(boolean expired:List.of(false,true)) {
            var f=fixture(MEMORY,expired?6:5);var io=new Identities(f);var leases=new Leases(f);var clock=new TestClock();
            var sent=new AtomicReference<AuthenticatedReplayOriginal>();
            inReplayReadScope(LIMITS,clock,NOW.plusSeconds(30),io,leases,sent::set,()->read(f));
            if(expired)clock.now=NOW.plusSeconds(30);else io.drift=true;
            assertThrows(IOException.class,()->sent.get().requireCurrent());
            clock.now=NOW;io.drift=false;
            assertThrows(IOException.class,()->sent.get().requireCurrent());assertEquals(1,leases.closes);
        }
    }
    @Test void callbackBodyOrCleanupFailureInvalidatesEveryAlreadyIssuedAuthenticatedOriginal()throws Exception {
        for(boolean closeFailure:List.of(false,true)) {
            var f=fixture(MEMORY,closeFailure?8:7);var leases=new Leases(f);leases.failClose=closeFailure;
            var sent=new AtomicReference<AuthenticatedReplayOriginal>();
            assertThrows(IOException.class,()->inReplayReadScope(LIMITS,new TestClock(),NOW.plusSeconds(30),new Identities(f),leases,
                    sent::set,()->{read(f);if(!closeFailure)throw new IOException("original proof failed after handoff");return null;}));
            assertThrows(IOException.class,()->sent.get().requireCurrent());
            if(!closeFailure)assertEquals(1,leases.closes);
        }
    }
    @Test void postScopeAuthenticatedOriginalCannotCrossTheOriginalOwnerThread()throws Exception {
        var f=fixture(MEMORY,9);var sent=new AtomicReference<AuthenticatedReplayOriginal>();
        inReplayReadScope(LIMITS,new TestClock(),NOW.plusSeconds(30),new Identities(f),new Leases(f),sent::set,()->read(f));
        var problem=new AtomicReference<Throwable>();
        Thread other=new Thread(()->{try{sent.get().requireCurrent();}catch(Throwable failure){problem.set(failure);}});
        other.start();other.join();assertInstanceOf(IOException.class,problem.get());
        assertThrows(IOException.class,()->sent.get().requireCurrent());
    }
    private static FileStamp stamp(Fixture f){return new FileStamp("1","18446744073709551615","116444736000000000","116444736000000001",f.bytes().length);}
    private static final class Identities implements FileIO {
        private final Fixture fixture;private int verifications;private boolean drift;
        Identities(Fixture fixture){this.fixture=fixture;}
        @Override public Resolved resolve(Path path,Path folder) {
            assertEquals(fixture.path(),path);assertEquals(fixture.folder(),folder);
            return new Resolved(folder,path,new DirectoryIdentity("1","2","3"),stamp(fixture));
        }
        @Override public ReadHandle open(Resolved original){throw new AssertionError("producer must use the actual lease adapter");}
        @Override public void verify(Resolved original,FileStamp identity)throws IOException {
            verifications++;if(drift)throw new IOException("software directory or full identity drift");
            assertEquals(stamp(fixture),identity);
        }
    }
    private static final class Leases implements ReplayLeaseFactory {
        private final Fixture fixture;private int opens,reads,closes;private boolean failClose;
        Leases(Fixture fixture){this.fixture=fixture;}
        @Override public ReplayLease acquire(Path path,int maximum) {
            assertEquals(fixture.path(),path);assertTrue(fixture.bytes().length<=maximum);opens++;
            return new ReplayLease() {
                private boolean closed,retired;
                private void open()throws IOException{if(closed)throw new IOException("software lease closed");}
                @Override public ReplayOriginal original()throws IOException {
                    open();if(retired)throw new IOException("software bytes retired");reads++;
                    return new ReplayOriginal(stamp(fixture),fixture.bytes().clone());
                }
                @Override public FileStamp current()throws IOException{open();return stamp(fixture);}
                @Override public void retireBytes()throws IOException{open();retired=true;}
                @Override public void close()throws IOException {
                    if(closed)return;if(failClose)throw new IOException("software native close UNKNOWN");closed=true;closes++;
                }
            };
        }
    }
    private static final class TestClock extends Clock {
        private Instant now=NOW;
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){assertEquals(ZoneOffset.UTC,zone);return this;}
        @Override public Instant instant(){return now;}
    }
}
