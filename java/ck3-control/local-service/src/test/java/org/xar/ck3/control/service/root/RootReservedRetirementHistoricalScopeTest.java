package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.continuity.writer.ArchiveOriginalEvidencePort;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;

/** Actual archive/filesystem scope boundaries only; no Game, Native action or retirement permission. */
final class RootReservedRetirementHistoricalScopeTest {
    @TempDir Path root;
    private static final RawJson BODY=new RawJson("[1]".getBytes(StandardCharsets.UTF_8));
    private static final ActionPorts.HistoricalReadLimits LIMITS=new ActionPorts.HistoricalReadLimits(8,1L<<20,32);

    @Test void defaultSameGameScopeKeepsNativeCustodyAndOnlyExposesTheRestrictedView()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("same-game"),false)){
            var escaped=new AtomicReference<ActionPorts.OutcomeArchive>();
            ExactRef ref=fixture.writer.locked(same->{
                ExactRef original=fixture.archive.preserveMaterial(BODY);
                writeQualification(Path.of(original.path()),true);
                try(var owner=owner(fixture,same)){
                    var data=owner.archive();escaped.set(data);
                    data.inSameGameHistoricalRecoveryScope(same,callback->{
                        assertSame(data,callback);assertFalse(callback instanceof NativeOutcomeArchive);
                        assertNull(callback.scopedDriverDecoder());
                        assertEquals(BODY,callback.loadMaterial(original));
                        writeQualification(Path.of(original.path()),false);
                        assertThrows(UnsupportedOperationException.class,()->callback.preserveRequest(null));
                        assertThrows(UnsupportedOperationException.class,()->callback.preserveRead(null));
                        return true;
                    });
                    writeQualification(Path.of(original.path()),true);
                    return original;
                }
            });
            assertThrows(IllegalStateException.class,()->escaped.get().loadMaterial(ref));
        }
    }

    @Test void caughtPublicationCannotSucceedAndOriginalCustodyIsReleased()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("write-denied"),false)){
            var original=new AtomicReference<ExactRef>();
            assertThrows(IOException.class,()->fixture.writer.locked(same->{
                ExactRef ref=fixture.archive.preserveMaterial(BODY);original.set(ref);
                try(var owner=owner(fixture,same)){
                    return owner.archive().inHistoricalReadScope(same,LIMITS,callback->{
                        assertEquals(BODY,callback.loadMaterial(ref));
                        assertThrows(RuntimeException.class,()->callback.preserveMaterial(new RawJson("[2]".getBytes(StandardCharsets.UTF_8))));
                        return true;
                    });
                }
            }));
            writeQualification(Path.of(original.get().path()),true);
        }
    }

    @Test void wrongSessionAndThreadCannotBorrowTheActualDataScope()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("ownership"),false)){
            fixture.writer.locked(same->{
                ExactRef ref=fixture.archive.preserveMaterial(BODY);
                try(var owner=owner(fixture,same)){
                    var data=owner.archive();
                    assertThrows(RuntimeException.class,()->data.inHistoricalReadScope(null,LIMITS,ignored->true));
                    var foreign=CompletableFuture.supplyAsync(()->{
                        try{return data.inHistoricalReadScope(same,LIMITS,ignored->true);}
                        catch(IOException failure){throw new CompletionException(failure);}
                    });
                    var failure=assertThrows(java.util.concurrent.ExecutionException.class,()->foreign.get(10,TimeUnit.SECONDS));
                    assertInstanceOf(IllegalStateException.class,failure.getCause());
                    assertEquals(BODY,data.inHistoricalReadScope(same,LIMITS,callback->callback.loadMaterial(ref)));
                    return true;
                }
            });
        }
    }

    private static RootReservedRetirementArchive owner(ActionWriterIntegrationFixture fixture,ContinuityStorePort.Session same){
        return RootReservedRetirementArchive.create(fixture.archive,same,new ArchiveOriginalEvidencePort(fixture.archive),()->{
            try{fixture.writer.requireSession(same);}catch(IOException failure){throw new UncheckedIOException(failure);}
        },"software-parent","1".repeat(64));
    }
    /** Opens only an access qualification handle, writes no bytes, and always closes success. */
    private static void writeQualification(Path path,boolean allowed)throws IOException {
        HANDLE handle=Kernel32.INSTANCE.CreateFile(path.toAbsolutePath().toString(),0x40000000,1|2|4,null,3,0x80,null);
        int error=Kernel32.INSTANCE.GetLastError();
        if(handle==null||WinBase.INVALID_HANDLE_VALUE.equals(handle)){
            if(allowed)throw new IOException("owned access qualification failed Win32="+error+": "+path);
            assertEquals(32,error,"retained CAS custody must deny writes by sharing, not missing or inaccessible files");return;
        }
        boolean closed=Kernel32.INSTANCE.CloseHandle(handle);int closeError=Kernel32.INSTANCE.GetLastError();
        if(!closed)throw new IOException("qualification CloseHandle failed Win32="+closeError);
        assertTrue(allowed,"actual retention must remain held throughout the restricted callback");
    }
}
