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

final class NativeEnvironmentRuntimeTest {
    @TempDir Path temporary;

    @Test void externalEnvironmentProducerCannotJoinTheMeasuredNativeModuleEvenWithSameJarBytes() throws Exception {
        List<ControlBuild.FileRef> runtime = new ArrayList<>();
        for (int index = 0; index < 6; index++) {
            Path jar = temporary.resolve("runtime-" + index + ".jar");
            try (JarOutputStream output = new JarOutputStream(Files.newOutputStream(jar))) {
                for (Class<?> type : List.of(NativeFixtureBuild.class, NativeBuildEnvironment.class)) {
                    String name = type.getName().replace('.', '/') + ".class";
                    output.putNextEntry(new JarEntry(name));
                    try (InputStream input = type.getClassLoader().getResourceAsStream(name)) {
                        if (input == null) throw new IOException("actual compiled producer unavailable");
                        input.transferTo(output);
                    }
                    output.closeEntry();
                }
            }
            runtime.add(ControlBuild.FileRef.measure(jar));
        }
        Path own = Path.of(runtime.getFirst().path());
        assertEquals(6, NativeFixtureBuild.environmentOperationRuntimeClosure(own, own, runtime, runtime).size());
        Path foreign = temporary.resolve("foreign-same-byte-producer.jar"); Files.copy(own, foreign);
        assertThrows(IOException.class, () -> NativeFixtureBuild.environmentOperationRuntimeClosure(own, foreign, runtime, runtime));
    }
}
