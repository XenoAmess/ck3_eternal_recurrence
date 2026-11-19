package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.nio.file.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.contracts.ExactRef;

/** Validates actual normal-Maven archive origins and own tiny source bytes; constructs no RuntimeContext or Game. */
final class IncidentImplementationCarrierTest {
    @TempDir Path temporary;
    private static ExactRef actual(){return new RootOrdinaryImplementationMetadata().implementation(EpisodeIncidentJournal.class);}
    private static void readAsIncident(ExactRef source)throws Exception {
        var method=RootIncidentRuntime.class.getDeclaredMethod("read",ExactRef.class,int.class);method.setAccessible(true);
        try{method.invoke(null,source,1<<20);}
        catch(InvocationTargetException rejected){if(rejected.getCause() instanceof Exception cause)throw cause;throw new AssertionError(rejected.getCause());}
    }
    @Test void actualLoadedJournalWholeArchivePassesItsImplementationRole()throws Exception {
        var source=actual();assertTrue(source.bytes()>(1<<20));assertTrue(source.path().endsWith(".jar"));
        RootIncidentRuntime.verifyImplementationSource(source);
        assertEquals(source,EpisodeIncidentJournal.measure(Path.of(source.path())));
    }
    @Test void aDifferentRealLoadedLargeArchiveCannotSubstituteForTheJournalImplementation() {
        var other=new RootOrdinaryImplementationMetadata().implementation(RootRuntimeContext.class);
        assertTrue(other.bytes()>(1<<20));assertNotEquals(actual(),other);
        assertThrows(IllegalArgumentException.class,()->RootIncidentRuntime.verifyImplementationSource(other));
    }
    @Test void sameArchiveWithWrongHashOrAnotherPathCannotBorrowItsLoadedRole() {
        var source=actual();var hash=new ExactRef(source.path(),source.bytes(),"0".repeat(64));
        assertThrows(IllegalArgumentException.class,()->RootIncidentRuntime.verifyImplementationSource(hash));
        var absent=new ExactRef(temporary.resolve("not-the-loaded-journal.jar").toString(),source.bytes(),source.sha256());
        assertThrows(IllegalArgumentException.class,()->RootIncidentRuntime.verifyImplementationSource(absent));
    }
    @Test void theSameGenuineArchiveStillFailsTheUnchangedOneMiBIncidentJsonBoundary() {
        var rejected=assertThrows(IllegalArgumentException.class,()->readAsIncident(actual()));
        assertEquals("Bounded original incident metadata required",rejected.getMessage());
    }
    @Test void legacySmallSourceRemainsExactAndTheNewArtifactRoleIsIndependentlyBounded()throws Exception {
        Path file=temporary.resolve("original-implementation.java");Files.writeString(file,"source-only legacy implementation DATA");
        var source=EpisodeIncidentJournal.measure(file);RootIncidentRuntime.verifyImplementationSource(source);
        Files.writeString(file,"changed original",StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(IllegalArgumentException.class,()->RootIncidentRuntime.verifyImplementationSource(source));
        var oversized=new ExactRef(temporary.resolve("not-read-too-large.jar").toString(),(64L<<20)+1,"a".repeat(64));
        assertThrows(IllegalArgumentException.class,()->RootIncidentRuntime.verifyImplementationSource(oversized));
        assertFalse(Files.exists(Path.of(oversized.path())));
    }
}
