package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ExactRef;

/** Application code can validate the exact borrowed authority through the shared port alone. */
final class BorrowedWriterPortTest {
    @TempDir Path root;
    @Test void portRejectsAnotherWriterEvenWithTheSameOriginalLockPath() throws Exception {
        assertTrue(Platform.isWindows());
        WriterFixture fixture=new WriterFixture(root);
        ContinuityStorePort original=fixture.writer;
        ContinuityStorePort foreign=new ContinuityWriter(fixture.layout, List.of(LedgerFiles.read(fixture.source,65_536).pin().reference()), new TransitionAuthority(){
                    @Override public String revalidate(ContinuityState state,Request request){return ContinuityJson.digest(request.detailsObject());}
                    @Override public ContinuityState reduce(ContinuityState state,Request request){return OriginalWindowReducer.reduce(state,request);}
                }, StorageWriteGuardTestSupport.forLayout(fixture.layout));
        original.locked(session->{
            original.requireSession(session);
            // Path equality alone would accept this foreign authority. The actual implementation does not.
            assertThrows(IOException.class,()->foreign.requireSession(session));
            assertThrows(IOException.class,()->original.requireSession(null));
            assertSame(session,fixture.writer.activeSession().orElseThrow());
            return null;
        });
        assertTrue(fixture.writer.activeSession().isEmpty());
        foreign.locked(session->{foreign.requireSession(session);assertThrows(IOException.class,()->original.requireSession(session));return null;});
    }
    @Test void oldPortDefaultsRemainExplicitlyUnavailable() {
        ContinuityStorePort unavailable=new ContinuityStorePort(){
            @Override public Prepared preview(Request request)throws IOException{throw new IOException("not installed");}
            @Override public Receipt commit(Prepared prepared)throws IOException{throw new IOException("not installed");}
            @Override public ExactRef persistedHead()throws IOException{throw new IOException("not installed");}
            @Override public <T>T locked(SessionWork<T> work)throws IOException{throw new IOException("not installed");}
        };
        IOException failure=assertThrows(IOException.class,()->unavailable.requireSession(null));
        assertTrue(failure.getMessage().contains("actual original writer session authority"));
    }
}
