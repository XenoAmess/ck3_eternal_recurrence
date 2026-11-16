package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Real Windows CAS custody at a manageable boundary, without Game, Native dispatch or a throughput claim. */
final class InitialSourceHistoricalHandleBoundaryTest {
    @TempDir Path directory;
    private record Original(ExactRef reference,byte[] body) {
        private Original {body=body.clone();}
        @Override public byte[] body(){return body.clone();}
    }

    @Test void lastPairNeedsBothCustodyAndTransientRoomWhileEntryBoundsAndEveryCloseStillApply()throws Exception {
        int publications=12;
        // The observed boundary is scaled from the actual owned files, not a production source constant.
        int sufficientHandles=2*publications+2;
        var originals=new ArrayList<Original>();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("owned-fixture"),false)){
            fixture.writer.locked(session->fixture.archive.inSession(session,bound->{
                for(int index=0;index<publications;index++){
                    byte[] body=("{\"owned_handle_boundary\":"+index+"}").getBytes(StandardCharsets.UTF_8);
                    originals.add(new Original(bound.preserveMaterial(new RawJson(body)),body));
                }
                return null;
            }));
            assertEquals(publications,originals.size());
            byte[] ledger=fixture.ledgerBytes();
            fixture.writer.locked(session->{
                fixture.archive.inHistoricalReadScope(session,limits(publications,sufficientHandles),bound->{
                    readAll(bound,originals);
                    assertEquals(publications,heldPairs(originals),"the last pair must stay continuously held with its qualification room");
                    // Re-reading the last pair must preserve both original custody handles.
                    Original last=originals.getLast();assertArrayEquals(last.body(),bound.loadMaterial(last.reference()).bytes());
                    assertTrue(pairHeld(last.reference()));return null;
                });
                assertEquals(0,heldPairs(originals),"successful inner scope must release before the outer writer lock closes");
                fixture.archive.inHistoricalReadScope(session,limits(publications,sufficientHandles-1),bound->{
                    readAll(bound,originals);
                    assertEquals(publications-1,heldPairs(originals),"one fewer handle cannot keep all pairs, regardless of retirement or fallback policy");
                    return null;
                });
                assertEquals(0,heldPairs(originals));
                fixture.archive.inHistoricalReadScope(session,limits(publications-1,sufficientHandles),bound->{
                    readAll(bound,originals);
                    assertEquals(publications-1,heldPairs(originals),"extra handle room must not enlarge the publication entry bound");
                    return null;
                });
                assertEquals(0,heldPairs(originals));
                IOException marker=new IOException("owned historical callback failure after last-pair custody");
                IOException actual=assertThrows(IOException.class,()->fixture.archive.inHistoricalReadScope(session,limits(publications,sufficientHandles),bound->{
                    readAll(bound,originals);assertEquals(publications,heldPairs(originals));throw marker;
                }));
                assertSame(marker,actual);assertEquals(0,heldPairs(originals),"exceptional close must release every retained pair");
                return null;
            });
            assertArrayEquals(ledger,fixture.ledgerBytes(),"historical qualification must not append canonical history");
            for(Original original:originals)assertArrayEquals(original.body(),Files.readAllBytes(Path.of(original.reference().path())));
        }
        assertEquals(0,heldPairs(originals),"fixture close must not leave a CAS custody handle behind");
    }

    private static ActionPorts.HistoricalReadLimits limits(int publications,int handles){
        return new ActionPorts.HistoricalReadLimits(publications,64L*1024*1024,handles);
    }
    private static void readAll(ActionPorts.OutcomeArchive archive,List<Original> originals){
        for(Original original:originals)assertArrayEquals(original.body(),archive.loadMaterial(original.reference()).bytes());
    }
    private static int heldPairs(List<Original> originals)throws IOException {
        int held=0;for(Original original:originals)if(pairHeld(original.reference()))held++;return held;
    }
    private static boolean pairHeld(ExactRef reference)throws IOException {
        Path payload=Path.of(reference.path()),commit=payload.resolveSibling(reference.sha256()+".commit.json");
        boolean metadataHeld=writeDeniedBySharing(commit),payloadHeld=writeDeniedBySharing(payload);
        assertEquals(metadataHeld,payloadHeld,"commit and payload custody must be retained or released as a pair");return metadataHeld;
    }
    /** Qualification only: OPEN_EXISTING + GENERIC_WRITE never writes a byte; every successful probe closes. */
    private static boolean writeDeniedBySharing(Path path)throws IOException {
        HANDLE handle=Kernel32.INSTANCE.CreateFile(path.toAbsolutePath().toString(),0x40000000,1|2|4,null,3,0x80,null);
        int error=Kernel32.INSTANCE.GetLastError();
        if(handle==null||WinBase.INVALID_HANDLE_VALUE.equals(handle)){
            assertEquals(32,error,"only ERROR_SHARING_VIOLATION proves retained custody: "+path);return true;
        }
        if(!Kernel32.INSTANCE.CloseHandle(handle))throw new IOException("owned qualification CloseHandle failed, Win32="+Kernel32.INSTANCE.GetLastError());
        return false;
    }
}
