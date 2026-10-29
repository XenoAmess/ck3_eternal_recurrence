package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.FullParityCurrentBindings;
import org.xar.ck3.control.build.FullParityOracleBindings;
import org.xar.ck3.control.build.MavenArgumentFile;

/** Runs inside the ordinary complete service reactor's actual Surefire JVM, with all real v8 inputs. */
final class MavenArgumentTransportIntegrationTest {
    @Test void defaultMavenLoadedTheLongFrozenArgvIntoEveryTypedSurefireConsumer() throws Exception {
        String selected = System.getProperty("xar.army.managers.java.root");
        if (selected == null || selected.isBlank()) throw new IOException("NOT_RUN: actual compiled reactor root is mandatory");
        Path compiled = Path.of(selected).toRealPath(), path = compiled.resolve(MavenArgumentFile.MANIFEST);
        var ref = ControlBuild.FileRef.measure(path);
        assertTrue(ref.bytes() > 0 && ref.bytes() <= MavenArgumentFile.MAXIMUM_BYTES);
        var raw = ControlBuild.strictMapper().readValue(Files.readAllBytes(path), MavenArgumentFile.Manifest.class); ref.verify();
        var manifest = MavenArgumentFile.readManifest(compiled, raw.arguments());
        assertTrue(MavenArgumentFile.required(null, manifest.arguments()), "This regression must exercise an actual command over CMD's 8191 character limit");
        assertEquals("verify", manifest.arguments().getLast());
        assertFalse(manifest.arguments().stream().anyMatch(arg -> arg.equals("-pl") || arg.startsWith("-Dtest=") || arg.startsWith("-DskipTests=")));
        int checked = 0;
        for (String argument : manifest.arguments()) if (argument.startsWith("-Dxar.")) {
            int separator = argument.indexOf('='); assertTrue(separator > 2);
            assertEquals(argument.substring(separator + 1), System.getProperty(argument.substring(2, separator)),
                    "The real Maven/Surefire process lost or changed " + argument.substring(2, separator)); checked++;
        }
        assertTrue(checked >= 117, "All 39 additional exact triples and original inputs must reach Surefire");
        assertEquals(FullParityCurrentBindings.SCHEMA, System.getProperty("xar.fullParity.current.schema"));
        var bindings = FullParityCurrentBindings.fromRecordedArguments(manifest.arguments());
        bindings.requireCompiledRoot(compiled);
        assertEquals(bindings,FullParityOracleBindings.fromRecordedArguments(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4,manifest.arguments()));
        assertEquals(39, bindings.additionalFixtures().size());
        assertEquals(RootRuntimeDefinitions.MAXIMUM_BYTES, FullParityCurrentBindings.Role.ORIGINAL_ROOT_RUNTIME_DEFINITIONS.maxBytes());
        assertEquals(RootRuntimeDefinitionsPublisher.MAXIMUM_REQUEST_BYTES, FullParityCurrentBindings.Role.ORIGINAL_ROOT_RUNTIME_DEFINITIONS_PUBLICATION_REQUEST.maxBytes());
        for (var role : FullParityCurrentBindings.Role.values()) {
            var fixture = bindings.additionalFixtures().stream().filter(value -> value.role() == role).findFirst().orElseThrow();
            assertEquals(fixture.source().path(), System.getProperty(role.pathProperty()));
            assertEquals(Long.toString(fixture.source().bytes()), System.getProperty(role.bytesProperty()));
            assertEquals(fixture.source().sha256(), System.getProperty(role.shaProperty()));
        }
        ref.verify(); manifest.configRef().verify();
    }
}
