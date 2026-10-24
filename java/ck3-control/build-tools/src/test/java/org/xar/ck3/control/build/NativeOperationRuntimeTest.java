package org.xar.ck3.control.build;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

/** Real JAR/filesystem regression only; never constructs Native authority or launches a process. */
final class NativeOperationRuntimeTest {
    @TempDir Path temporary;

    @Test void formalJarLocationUsesTheSameCompleteAcceptedRuntime() throws Exception {
        List<ControlBuild.FileRef> runtime = runtime();
        List<ControlBuild.FileRef> qualified = NativeFixtureBuild.operationRuntimeClosure(
                Path.of(runtime.getFirst().path()), runtime, List.copyOf(runtime));
        assertEquals(6, qualified.size());
        assertEquals(new java.util.HashSet<>(runtime), new java.util.HashSet<>(qualified));
    }

    @Test void foreignOrChangedJarAndMismatchedDeploymentCannotPass() throws Exception {
        List<ControlBuild.FileRef> runtime = runtime();
        Path foreign = temporary.resolve("foreign.jar"); Files.copy(Path.of(runtime.getFirst().path()), foreign);
        assertThrows(IOException.class, () -> NativeFixtureBuild.operationRuntimeClosure(foreign, runtime, runtime));
        List<ControlBuild.FileRef> different = new ArrayList<>(runtime);
        different.set(0, ControlBuild.FileRef.measure(foreign));
        assertThrows(IOException.class, () -> NativeFixtureBuild.operationRuntimeClosure(
                Path.of(runtime.getFirst().path()), runtime, different));
        Files.writeString(Path.of(runtime.getFirst().path()), "changed source-only fixture bytes");
        assertThrows(IOException.class, () -> NativeFixtureBuild.operationRuntimeClosure(
                Path.of(runtime.getFirst().path()), runtime, runtime));
    }

    @Test void originalFiniteClassDirectoryStillRejectsUnrelatedClasses() throws Exception {
        List<ControlBuild.FileRef> runtime = runtime();
        Path classes = Files.createDirectory(temporary.resolve("operation-classes"));
        Path operation = classes.resolve("NativeFixtureBuild.class"); Files.write(operation, classBytes());
        assertEquals(7, NativeFixtureBuild.operationRuntimeClosure(classes, runtime, runtime).size());
        Files.write(classes.resolve("Unrelated.class"), classBytes());
        assertThrows(IOException.class, () -> NativeFixtureBuild.operationRuntimeClosure(classes, runtime, runtime));
    }

    private List<ControlBuild.FileRef> runtime() throws IOException {
        List<ControlBuild.FileRef> runtime = new ArrayList<>();
        for (int i = 0; i < 6; i++) {
            Path jar = temporary.resolve("synthetic-runtime-" + i + ".jar");
            try (JarOutputStream output = new JarOutputStream(Files.newOutputStream(jar))) {
                output.putNextEntry(new JarEntry("org/xar/ck3/control/build/NativeFixtureBuild.class"));
                output.write(classBytes()); output.closeEntry();
            }
            runtime.add(ControlBuild.FileRef.measure(jar));
        }
        return List.copyOf(runtime);
    }

    private static byte[] classBytes() throws IOException {
        try (InputStream input = NativeFixtureBuild.class.getResourceAsStream("NativeFixtureBuild.class")) {
            if (input == null) throw new IOException("actual compiled producer class unavailable");
            return input.readAllBytes();
        }
    }
}
