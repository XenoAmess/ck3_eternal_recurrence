package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.OriginalMcpCapture.OriginalMcpSourceSet;
import org.xar.ck3.control.build.OriginalMcpCapture.OriginalModule;
import org.xar.ck3.control.build.OriginalMcpCapture.OriginalSource;

/** Source metadata selection does not qualify implementation files or authorize a Game operation. */
final class OriginalMcpSourceSelectionDataTest {
    @TempDir Path temporary;
    private record Fixture(OriginalMcpSourceSet sources,List<OriginalSource> rows,List<Path> files) { }
    private Fixture fixture()throws IOException {
        var rows=new ArrayList<OriginalSource>();var files=new ArrayList<Path>();
        for(OriginalModule module:OriginalModule.values()) {
            Path file=temporary.resolve(module.name()+".py");Files.writeString(file,"# recorded test metadata\n");
            var observed=SharedSourceFiles.observe(file);rows.add(new OriginalSource(module,observed.source(),observed.nativeFile()));files.add(file);
        }
        return new Fixture(new OriginalMcpSourceSet(rows.get(0),rows.get(1),rows.get(2),rows.get(3)),List.copyOf(rows),List.copyOf(files));
    }
    @Test void recordedExactReferencesRemainSelectableAfterHistoricalFilesAreRemoved()throws Exception {
        var actual=fixture();for(Path file:actual.files())Files.delete(file);
        for(OriginalSource row:actual.rows())assertSame(row,actual.sources().requireOriginal(row.original()));
    }
    @Test void foreignAndNullReferencesKeepTheirClosedTypedRefusalWithoutReadingRecordedFiles()throws Exception {
        var actual=fixture();for(Path file:actual.files())Files.delete(file);
        var foreign=new FileRef(temporary.resolve("outside.py").toString(),1,"a".repeat(64));
        var failure=assertThrows(IOException.class,()->actual.sources().requireOriginal(foreign));
        assertTrue(failure.getMessage().contains("outside the actual captured four-module table"),failure.toString());
        assertThrows(NullPointerException.class,()->actual.sources().requireOriginal(null));
    }
    @Test void explicitVerificationAndRoleIdentityContractsRemainSeparateFromMetadataSelection()throws Exception {
        var actual=fixture();actual.sources().verify();
        assertThrows(IllegalArgumentException.class,()->new OriginalMcpSourceSet(actual.rows().get(0),actual.rows().get(0),actual.rows().get(2),actual.rows().get(3)));
        for(Path file:actual.files())Files.delete(file);
        assertThrows(IOException.class,()->actual.sources().verify());
    }
}
