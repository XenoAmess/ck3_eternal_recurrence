package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.FileTime;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Supplier;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Actual file/store and public reducer DATA contracts. No live Game, new Guard issuer or pressure run. */
final class ActionHistoricalReadResource77Test {
    private static final long BYTE_LIMIT=256L*1024*1024;
    private static final ActionPorts.HistoricalReadLimits OLD=new ActionPorts.HistoricalReadLimits(4096,BYTE_LIMIT,8192);
    private static final ActionPorts.HistoricalReadLimits ACTION=new ActionPorts.HistoricalReadLimits(8192,BYTE_LIMIT,16384);
    @TempDir Path directory;
    private record StoreFixture(WriterFixture original,ImmutableArtifactStore store) implements AutoCloseable {
        @Override public void close() throws IOException {original.storage.close();}
    }
    private StoreFixture store(String name) throws IOException {
        var original=new WriterFixture(directory.resolve(name));
        return new StoreFixture(original,new ImmutableArtifactStore(new ImmutableArtifactStore.Config(
                original.layout.snapshot().getParent().resolve("artifacts"),original.layout.lock(),2L<<20),original.storage));
    }

    @Test void declaredNewAndOldTierBoundsAgreeAtBothRealBoundariesWithoutPressureAllocation() throws IOException {
        assertEquals(4096,OLD.maximumPublications());assertEquals(8192,OLD.maximumHandles());
        assertEquals(8192,ACTION.maximumPublications());assertEquals(16384,ACTION.maximumHandles());
        assertEquals(BYTE_LIMIT,OLD.maximumRetainedBytes());assertEquals(BYTE_LIMIT,ACTION.maximumRetainedBytes());
        for(long[] bound:List.of(new long[]{8193,BYTE_LIMIT,16384},new long[]{8192,BYTE_LIMIT,16385},
                new long[]{8192,BYTE_LIMIT+1,16384},new long[]{0,BYTE_LIMIT,16384},
                new long[]{8192,0,16384},new long[]{8192,BYTE_LIMIT,3}))
            assertThrows(IllegalArgumentException.class,()->new ActionPorts.HistoricalReadLimits((int)bound[0],bound[1],(int)bound[2]));
        try(var fixture=store("hard-bound")) {
            fixture.original.writer.locked(session->{
                for(long[] bound:List.of(new long[]{8193,BYTE_LIMIT,16384},new long[]{8192,BYTE_LIMIT,16385},
                        new long[]{8192,BYTE_LIMIT+1,16384},new long[]{0,BYTE_LIMIT,16384},
                        new long[]{8192,0,16384},new long[]{8192,BYTE_LIMIT,3}))
                    assertThrows(IOException.class,()->fixture.store.beginHistoricalReads(session,(int)bound[0],bound[1],(int)bound[2],
                            ()->session.requireWriter(fixture.original.layout.lock())));
                for(var limits:List.of(OLD,ACTION)) {
                    try(var reads=fixture.store.beginHistoricalReads(session,limits.maximumPublications(),limits.maximumRetainedBytes(),limits.maximumHandles(),
                            ()->session.requireWriter(fixture.original.layout.lock()));var trace=reads.traceDependencies()) {
                        assertTrue(trace.retainedDependencies().orElseThrow().isEmpty());
                    }
                }
                return null;
            });
        }
    }

    @Test void oldSmallEntryHandleAndByteCapsStillPerformFullFallbackAndReleaseTheirRealPairs() throws IOException {
        try(var fixture=store("small-caps")) {
            byte[] first="first controlled store original".getBytes(StandardCharsets.UTF_8);
            byte[] second="second controlled store original".getBytes(StandardCharsets.UTF_8);
            Pin a=publish(fixture,first),b=publish(fixture,second);
            FileTime stampA=Files.getLastModifiedTime(Path.of(a.reference().path()));
            FileTime stampB=Files.getLastModifiedTime(Path.of(b.reference().path()));
            byte[] head=Files.readAllBytes(fixture.original.layout.snapshot());
            for(var limits:List.of(new ActionPorts.HistoricalReadLimits(1,65536,8),
                    new ActionPorts.HistoricalReadLimits(4,65536,4),new ActionPorts.HistoricalReadLimits(8192,1,16384))) {
                var released=new java.util.concurrent.atomic.AtomicReference<Pin>();
                var firstFailure=new java.util.concurrent.atomic.AtomicReference<IOException>();
                IOException escaped=assertThrows(IOException.class,()->fixture.original.writer.locked(session->{
                    try(var reads=fixture.store.beginHistoricalReads(session,limits.maximumPublications(),limits.maximumRetainedBytes(),limits.maximumHandles(),
                            ()->session.requireWriter(fixture.original.layout.lock()));var trace=reads.traceDependencies()) {
                        assertArrayEquals(first,fixture.store.read(a,100));
                        assertArrayEquals(second,fixture.store.read(b,100));
                        assertTrue(trace.retainedDependencies().isEmpty(),"unretained or retired custody cannot certify the complete dependency proof");
                        boolean writableA=pairWriteAllowed(a.reference()),writableB=pairWriteAllowed(b.reference());
                        if(limits.maximumRetainedBytes()==1) {
                            assertTrue(writableA&&writableB,"the byte-one profile cannot retain either payload pair");
                        } else {
                            assertEquals(1,(writableA?0:1)+(writableB?0:1),"entry-one/handle-four retain exactly one complete pair, without prescribing which one");
                        }
                        Pin original=writableB?b:a;
                        assertTrue(writableA||writableB,"the controlled cap fixture must expose an actually released pair; never skip the fresh negative");
                        released.set(original);
                        byte[] changed=(original==a?first:second).clone();changed[0]^=1;
                        Files.write(Path.of(original.reference().path()),changed,StandardOpenOption.TRUNCATE_EXISTING);
                        Files.setLastModifiedTime(Path.of(original.reference().path()),original==a?stampA:stampB);
                        // Read the actual corrupted, released original. Restored metadata cannot hide changed content.
                        firstFailure.set(assertThrows(IOException.class,()->fixture.store.read(original,100)));
                        assertTrue(contains(assertThrows(IOException.class,()->fixture.store.read(original,100)),firstFailure.get()));
                    }
                    return null;
                }));
                assertNotNull(released.get());assertNotNull(firstFailure.get());assertTrue(contains(escaped,firstFailure.get()));
                qualifyPair(a.reference(),true);qualifyPair(b.reference(),true);
                Pin original=released.get();byte[] restored=original==a?first:second;
                Files.write(Path.of(original.reference().path()),restored,StandardOpenOption.TRUNCATE_EXISTING);
                Files.setLastModifiedTime(Path.of(original.reference().path()),original==a?stampA:stampB);
                fixture.original.writer.locked(session->{
                    try(var reads=fixture.store.beginHistoricalReads(session,8192,BYTE_LIMIT,16384,
                            ()->session.requireWriter(fixture.original.layout.lock()));var trace=reads.traceDependencies()) {
                        assertArrayEquals(restored,fixture.store.read(original,100));
                        assertTrue(reads.verifyRetainedDependencies(trace.retainedDependencies().orElseThrow()));
                    }
                    return null;
                });
                qualifyPair(a.reference(),true);qualifyPair(b.reference(),true);
                assertArrayEquals(head,Files.readAllBytes(fixture.original.layout.snapshot()));
            }
        }
    }

    @Test void newTierFreshAuthorityAndMetadataFailuresRemainPoisonedAndCloseBeforeANewScope() throws IOException {
        try(var fixture=store("fresh-poison")) {
            byte[] payload="new-tier-held-original".getBytes(StandardCharsets.UTF_8);
            Pin pin=publish(fixture,payload);FileTime stamp=Files.getLastModifiedTime(Path.of(pin.reference().path()));
            IOException marker=new IOException("specific original scope authority failure");
            AtomicBoolean active=new AtomicBoolean(true);
            IOException failed=assertThrows(IOException.class,()->fixture.original.writer.locked(session->{
                try(var reads=fixture.store.beginHistoricalReads(session,8192,BYTE_LIMIT,16384,()->{
                        session.requireWriter(fixture.original.layout.lock());if(!active.get())throw marker;
                    });var trace=reads.traceDependencies()) {
                    assertArrayEquals(payload,fixture.store.read(pin,100));
                    var dependencies=trace.retainedDependencies().orElseThrow();active.set(false);
                    assertSame(marker,assertThrows(IOException.class,()->reads.verifyRetainedDependencies(dependencies)));
                    active.set(true);assertTrue(contains(assertThrows(IOException.class,()->reads.verifyRetainedDependencies(dependencies)),marker));
                }
                return null;
            }));
            assertTrue(contains(failed,marker));qualifyPair(pin.reference(),true);
            assertThrows(IOException.class,()->fixture.original.writer.locked(session->{
                try(var reads=fixture.store.beginHistoricalReads(session,8192,BYTE_LIMIT,16384,
                        ()->session.requireWriter(fixture.original.layout.lock()));var trace=reads.traceDependencies()) {
                    assertArrayEquals(payload,fixture.store.read(pin,100));var dependencies=trace.retainedDependencies().orElseThrow();
                    try {
                        Files.setLastModifiedTime(Path.of(pin.reference().path()),FileTime.fromMillis(stamp.toMillis()+10000));
                        assertThrows(IOException.class,()->reads.verifyRetainedDependencies(dependencies));
                    } finally {Files.setLastModifiedTime(Path.of(pin.reference().path()),stamp);}
                    assertThrows(IOException.class,()->reads.verifyRetainedDependencies(dependencies));
                }
                return null;
            }));
            qualifyPair(pin.reference(),true);
            fixture.original.writer.locked(session->{
                try(var reads=fixture.store.beginHistoricalReads(session,8192,BYTE_LIMIT,16384,
                        ()->session.requireWriter(fixture.original.layout.lock()));var trace=reads.traceDependencies()) {
                    assertArrayEquals(payload,fixture.store.read(pin,100));
                    assertTrue(reads.verifyRetainedDependencies(trace.retainedDependencies().orElseThrow()));
                }
                return null;
            });
            qualifyPair(pin.reference(),true);
        }
    }

    @Test void ordinaryOuterScopeUsesNewTierOnceWhileOutsideAndNonPredispatchRoutesKeepTheOldProfile() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("action-roles"),true)) {
            ActionReceipt retained=fixture.coordinator.execute(fixture.command("resource-original"));
            ActionState.Unknown unknown=assertInstanceOf(ActionState.Unknown.class,retained.state());
            int writes=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();
            fixture.writer.locked(session->{
                var head=session.head();byte[] ledger=fixture.ledgerBytes();
                ActionCommand original=retained.command();
                ActionCommand next=new ActionCommand(original.actionId()+"-next",original.origin(),original.source(),original.sessionId(),
                        original.operation(),original.arguments(),original.expectation(),original.claims(),original.deadline(),original.protocolIdentity());
                var intent=originalRequest(fixture,head,next,new ActionState.IntentDurable());
                ObservedArchive observed=new ObservedArchive(fixture.archive);
                var legacy=authority(observed.archive,null);var borrowed=authority(observed.archive,()->session);
                ContinuityState expected=legacy.reduce(head.state(),intent);assertTrue(observed.scopes.isEmpty());
                assertEquals(expected.toJson(),borrowed.withReadValidation(head,intent,session,same->borrowed.reduce(head.state(),intent)).toJson());
                assertEquals(List.of(ACTION),observed.scopes,"captured canonical replay must reuse the outer scope instead of beginning a nested scope");
                observed.scopes.clear();assertEquals(expected.toJson(),borrowed.reduce(head.state(),intent).toJson());
                assertEquals(List.of(OLD),observed.scopes,"outside the captured ordinary path keeps the old canonical-reader profile");
                observed.scopes.clear();
                assertEquals(expected.toJson(),legacy.withReadValidation(head,intent,session,same->legacy.reduce(head.state(),intent)).toJson());
                assertTrue(observed.scopes.isEmpty(),"a no-borrow public adapter retains its original full route");
                var repeatedUnknown=originalRequest(fixture,head,original,unknown);
                ContinuityState unknownExpected=legacy.reduce(head.state(),repeatedUnknown);
                observed.scopes.clear();assertEquals(unknownExpected.toJson(),borrowed.withReadValidation(head,repeatedUnknown,session,
                        same->borrowed.reduce(head.state(),repeatedUnknown)).toJson());
                assertEquals(List.of(OLD),observed.scopes,"a real non-predispatch UNKNOWN continuation is not widened");
                // The actual fixture issued this Attempt through its existing controlled software path.
                // UNKNOWN->Submitting remains prohibited; testing its outer resource selection grants no replay.
                var submitting=originalRequest(fixture,head,original,new ActionState.Submitting(unknown.attempt().orElseThrow()));
                IllegalArgumentException originalRejection=assertThrows(IllegalArgumentException.class,()->legacy.reduce(head.state(),submitting));
                observed.scopes.clear();
                IllegalArgumentException actualRejection=assertThrows(IllegalArgumentException.class,()->borrowed.withReadValidation(head,submitting,session,
                        same->borrowed.reduce(head.state(),submitting)));
                assertEquals(originalRejection.getMessage(),actualRejection.getMessage());assertEquals(List.of(ACTION),observed.scopes);
                assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(head.digest(),session.head().digest());return null;
            });
            assertEquals(writes,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());
        }
    }

    private static Pin publish(StoreFixture fixture,byte[] raw) throws IOException {
        return fixture.original.writer.locked(session->fixture.store.publish(raw,100));
    }
    private static boolean contains(Throwable value,Throwable marker) {
        if(value==marker)return true;if(value.getCause()!=null&&contains(value.getCause(),marker))return true;
        return Arrays.stream(value.getSuppressed()).anyMatch(item->contains(item,marker));
    }
    // Original NativeArchiveHistoricalScope225Test software-only Windows file qualification.
    private static void qualify(Path path,boolean allowed) throws IOException {
        HANDLE handle=Kernel32.INSTANCE.CreateFile(path.toAbsolutePath().toString(),0x40000000,1|2|4,null,3,0x80,null);
        int error=Kernel32.INSTANCE.GetLastError();
        if(handle==null||WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
            if(allowed)throw new IOException("owned file write qualification unexpectedly refused Win32="+error+": "+path);
            assertEquals(32,error);return;
        }
        if(!Kernel32.INSTANCE.CloseHandle(handle))throw new IOException("controlled qualification CloseHandle failed");
        assertTrue(allowed,"custody unexpectedly allowed write access: "+path);
    }
    private static boolean writeAllowed(Path path) throws IOException {
        HANDLE handle=Kernel32.INSTANCE.CreateFile(path.toAbsolutePath().toString(),0x40000000,1|2|4,null,3,0x80,null);
        int error=Kernel32.INSTANCE.GetLastError();
        if(handle==null||WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
            if(error!=32)throw new IOException("owned custody probe failed for a reason other than sharing Win32="+error+": "+path);
            return false;
        }
        if(!Kernel32.INSTANCE.CloseHandle(handle))throw new IOException("controlled custody-probe CloseHandle failed");
        return true;
    }
    private static boolean pairWriteAllowed(ExactRef ref) throws IOException {
        Path data=Path.of(ref.path());
        boolean metadata=writeAllowed(data.resolveSibling(ref.sha256()+".commit.json"));
        boolean payload=writeAllowed(data);
        assertEquals(metadata,payload,"metadata and data must have consistent complete-pair custody");
        return payload;
    }
    private static void qualifyPair(ExactRef ref,boolean allowed) throws IOException {
        Path data=Path.of(ref.path());qualify(data.resolveSibling(ref.sha256()+".commit.json"),allowed);qualify(data,allowed);
    }
    private static ActionContinuityAuthority authority(ActionPorts.OutcomeArchive archive,Supplier<ContinuityStorePort.Session> sessions) {
        ActionPorts.GuardPort guard=(head,command)->{throw new AssertionError("pure reducer cannot obtain Guard evidence");};
        ActionPorts.RecordedEvidenceVerifier verifier=(head,receipt)->{throw new AssertionError("pure reducer cannot grant evidence");};
        ActionPorts.PreparationPort policy=new ActionPorts.PreparationPort() {
            @Override public NativeRequest prepare(ActionCommand command){throw new AssertionError("pure reducer cannot prepare Native requests");}
        };
        return sessions==null?new ActionContinuityAuthority("owned-software-authority",archive,guard,verifier,Clock.systemUTC(),policy)
                :new ActionContinuityAuthority("owned-software-authority",archive,guard,verifier,Clock.systemUTC(),policy,sessions);
    }
    private static WriterContracts.Request originalRequest(ActionWriterIntegrationFixture fixture,WriterContracts.Head head,ActionCommand command,ActionState next) {
        var receipt=new ActionReceipt(1,Math.addExact(head.state().sequence(),1),command,ActionCodec.bodySha256(command),next);
        var receiptRef=fixture.archive.preserveReceipt(receipt);
        var recordRef=fixture.archive.preserveRecord(new ActionRecord(receipt,ContinuityActionJournal.recordHead(head.state())));
        var details=StrictJson.object();details.put("evidence_id",command.actionId()+":"+receipt.sequence());
        details.set("source",ProposalLifecycleCodec.source(command.source()));details.set("receipt_ref",recordRef.toJson());
        return new WriterContracts.Request(ContinuityActionJournal.KIND,ContinuityJson.canonical(details),List.of(recordRef,receiptRef));
    }
    private static final class ObservedArchive {
        final List<ActionPorts.HistoricalReadLimits> scopes=new ArrayList<>();
        final ActionPorts.OutcomeArchive archive;
        ObservedArchive(ActionPorts.OutcomeArchive actual) {
            archive=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                    new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,arguments)->{
                        if(method.getName().equals("inHistoricalReadScope"))scopes.add((ActionPorts.HistoricalReadLimits)arguments[1]);
                        try{return method.invoke(actual,arguments);}catch(InvocationTargetException failure){throw failure.getCause();}
                    });
        }
    }
}
