package org.xar.ck3.control.build;

import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

/** Requires actual Windows metadata. Fake .class bytes are software fixtures, never loadable-runtime evidence. */
final class RawWindowClassClosureTest {
    @TempDir Path temporary;
    private Path fixture(String leaf)throws Exception {
        Path root=temporary.resolve(leaf);Files.createDirectory(root);Path pkg=root.resolve("org/xar/ck3/control/build");Files.createDirectories(pkg);
        Files.write(pkg.resolve("RawWindowPreparation.class"),new byte[]{1,2,3});
        Files.write(pkg.resolve("RawWindowPrepareMain.class"),new byte[]{4,5,6});
        Files.write(pkg.resolve("RawWindowPrepareRegressionMain.class"),new byte[]{7,8,9});
        Files.write(pkg.resolve("RawWindowClassClosureMain.class"),new byte[]{10,11,12});return root;
    }
    @Test void actualMetadataProducerAndStrictConsumerPreserveClassFileNativeWitnesses()throws Exception {
        Path root=fixture("classes");var manifest=RawWindowClassClosureMain.capture(root,temporary.resolve("manifest.json"));var actual=RawWindowClassClosureMain.read(manifest);
        assertEquals(WindowsJobProcess.currentMachineId(),actual.machineId());assertEquals(4,actual.classes().size());assertEquals(12,actual.totalBytes());
        for(var file:actual.classes()){assertEquals(file.nativeFile(),SharedSourceFiles.nativeFile(Path.of(file.fileRef().path())));file.fileRef().verify();}
        String json=Files.readString(Path.of(manifest.path()));assertTrue(json.contains("\"file_id_decimal\":\""));
        assertThrows(java.io.IOException.class,()->RawWindowClassClosureMain.capture(root,Path.of(manifest.path())));
        Files.write(root.resolve("org/xar/ck3/control/build/RawWindowPreparation.class"),new byte[]{7,8,9});
        assertThrows(java.io.IOException.class,()->RawWindowClassClosureMain.read(manifest));
    }
    @Test void foreignAndOverCapClassTreesCannotProduceACompleteManifest()throws Exception {
        Path foreign=fixture("foreign");Files.write(foreign.resolve("org/xar/ck3/control/build/Foreign.class"),new byte[]{1});
        assertThrows(IllegalArgumentException.class,()->RawWindowClassClosureMain.capture(foreign,temporary.resolve("foreign.json")));
        assertFalse(Files.exists(temporary.resolve("foreign.json")));
        Path missing=fixture("missing");Files.delete(missing.resolve("org/xar/ck3/control/build/RawWindowPrepareMain.class"));
        assertThrows(java.io.IOException.class,()->RawWindowClassClosureMain.capture(missing,temporary.resolve("missing.json")));
        Path over=fixture("many");for(int index=0;index<29;index++)Files.write(over.resolve("org/xar/ck3/control/build/RawWindowPreparation$Case"+index+".class"),new byte[]{1});
        assertThrows(java.io.IOException.class,()->RawWindowClassClosureMain.capture(over,temporary.resolve("many.json")));
    }
}
