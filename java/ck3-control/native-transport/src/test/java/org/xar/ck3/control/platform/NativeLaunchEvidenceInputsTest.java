package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Declared input selection is DATA; the unchanged real three-stage reader rejects invalid originals. */
final class NativeLaunchEvidenceInputsTest {
    @TempDir Path root;
    private FileRef data(String name)throws IOException {
        Path path=root.resolve(name);Files.createDirectories(path.getParent());Files.writeString(path,"{}");return FileRef.measure(path);
    }
    @Test void declaredNativeSubsetKeepsActualArtifactsAndOriginalStagePinsWithoutCreatingProof()throws Exception {
        var source=data("native/source.cpp");var runtime=data("java/Source.java");
        var dll=data("bridge-data.bin");var injector=data("injector-data.bin");
        var stages=new NativeLaunchEvidence.Inputs(data("env-invalid.json"),data("build-invalid.json"),data("register-invalid.json"));
        var review=new LaunchSourceBinding.Review("software-machine",Instant.now(),dll,dll,injector,stages,root.resolve("native"),List.of(runtime,source));
        var expected=NativeLaunchEvidence.reviewedBuild(review);
        assertEquals(List.of(source),expected.completeSources());assertEquals(dll,expected.bridgeDll());
        assertEquals(injector,expected.injector());assertEquals(stages,expected.inputs());
        assertThrows(IOException.class,()->NativeLaunchEvidence.verifyOriginal(expected,new NativeBridgeLaunchEvidence()));
        assertThrows(IllegalStateException.class,()->LaunchSourceBinding.accept(review).nativeProof());
    }
    @Test void absentRootStagesSourcesAndDuplicateRefsAreNormalInputRejections()throws Exception {
        var source=data("native/source.cpp");var artifact=data("artifact.bin");
        var stages=new NativeLaunchEvidence.Inputs(data("env.json"),data("build.json"),data("register.json"));
        assertThrows(IOException.class,()->NativeLaunchEvidence.reviewedBuild(null));
        assertThrows(IOException.class,()->NativeLaunchEvidence.reviewedBuild(new LaunchSourceBinding.Review(
                "software-machine",null,artifact,artifact,artifact,null,root.resolve("native"),List.of(source))));
        assertThrows(IOException.class,()->NativeLaunchEvidence.reviewedBuild(new LaunchSourceBinding.Review(
                "software-machine",null,artifact,artifact,artifact,stages,null,List.of(source))));
        assertThrows(IOException.class,()->NativeLaunchEvidence.reviewedBuild(new LaunchSourceBinding.Review(
                "software-machine",null,artifact,artifact,artifact,stages,root.resolve("other"),List.of(source))));
        assertThrows(IOException.class,()->NativeLaunchEvidence.reviewedBuild(new LaunchSourceBinding.Review(
                "software-machine",null,artifact,artifact,artifact,stages,root.resolve("native"),List.of(source,source))));
    }
}
