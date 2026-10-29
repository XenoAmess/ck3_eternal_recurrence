package org.xar.ck3.control.wave3.runtime.lineage;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.reflect.Modifier;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ProjectionDeploymentProof;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** Static signature/rejection coverage only. A later real producer must supply the actual JAR attestation. */
final class RuntimeCatalogConstructorTest {
    @TempDir Path temporary;

    @Test void actualDiscoveredW3ClassesExposeTheSharedSpiPublicNoArgumentConstructor() throws Exception {
        var providers = ServiceLoader.load(ProjectionPortCatalog.class).stream().map(ServiceLoader.Provider::type)
                .filter(type -> type.getName().startsWith("org.xar.ck3.control.wave3.runtime.")).toList();
        assertFalse(providers.isEmpty(), "missing W3 SPI resources must fail, never skip or invent a provider count");
        for (Class<? extends ProjectionPortCatalog> provider : providers) {
            var constructor = RuntimeCatalogConstructorFixture.requirePublicNoArgument(provider, ProjectionPortCatalog.class);
            assertEquals(provider, constructor.getDeclaringClass());
            assertEquals(0, constructor.getParameterCount());
            assertTrue(Modifier.isPublic(constructor.getModifiers()));
        }
    }

    @Test void privateArgumentOnlyAbstractAndUnrelatedClassesCannotStandInForTheRealConstructor() {
        for (Class<?> invalid : List.of(PrivateConstructor.class, ArgumentOnlyConstructor.class,
                AbstractCatalog.class, String.class)) {
            assertThrows(IOException.class, () -> RuntimeCatalogConstructorFixture.requirePublicNoArgument(
                    invalid, ProjectionPortCatalog.class));
        }
    }

    @Test void aSourceOrSurefireClassFileCannotBecomeAnActualJarLineage() throws Exception {
        Path source = temporary.resolve("SourceOnly.java"); Files.writeString(source, "source declaration only");
        Path descriptor = temporary.resolve("descriptor.txt"); Files.writeString(descriptor, "source-only provider declaration\n");
        Path classFile = temporary.resolve("target-classes.class"); Files.write(classFile, new byte[] {(byte) 0xca, (byte) 0xfe});
        var profile = new ProjectionDeploymentProof.OperationProfile("fixture-only", 1, 1);
        var catalog = new ProjectionDeploymentProof.BoundCatalog(
                "org.xar.ck3.control.wave3.runtime.fixture.SourceOnlyCatalog", ControlBuild.FileRef.measure(classFile),
                ControlBuild.FileRef.measure(source), ControlBuild.FileRef.measure(descriptor),
                ControlBuild.FileRef.measure(descriptor).sha256(), List.of(profile));
        var identity = new ProjectionDeploymentProof.Identity("xar.projection-host-identity/v1",
                ProjectionDeploymentProof.PRODUCER, ProjectionDeploymentProof.VERSION,
                ProjectionDeploymentProof.CALL_SCHEMA, ProjectionDeploymentProof.RESULT_SCHEMA,
                ProjectionDeploymentProof.MAX_ENVELOPE_BYTES, List.of(profile));
        var proof = new ProjectionDeploymentProof.Attestation(identity, List.of(catalog));
        IOException error = assertThrows(IOException.class, () -> RuntimeCatalogConstructorFixture.inspect(
                proof, List.of(ControlBuild.FileRef.measure(classFile))));
        assertTrue(error.getMessage().contains("JAR"));
    }

    @Test void fullAndCaptureReceiptKindsRoundTripWithoutAnImplicitOrNumericFallback() throws Exception {
        Path placeholder = temporary.resolve("explicit-unqualified-input.json");
        Files.writeString(placeholder, "synthetic input contract only");
        var reference = ControlBuild.FileRef.measure(placeholder);
        var mapper = ControlBuild.strictMapper();
        for (var kind : org.xar.ck3.control.build.ProjectionCaptureScope.Qualification.values()) {
            var expected = new RuntimeCatalogConstructorFixture.Input("xar.runtime-catalog-constructor-input/v1",
                    "fixture-machine", kind, reference, reference, reference, List.of(reference));
            assertEquals(expected, mapper.readValue(mapper.writeValueAsBytes(expected),
                    RuntimeCatalogConstructorFixture.Input.class));
            com.fasterxml.jackson.databind.node.ObjectNode malformed = mapper.valueToTree(expected);
            malformed.put("qualification", 0);
            assertThrows(IOException.class, () -> mapper.treeToValue(malformed,
                    RuntimeCatalogConstructorFixture.Input.class));
            malformed.putNull("qualification");
            assertThrows(IOException.class, () -> mapper.treeToValue(malformed,
                    RuntimeCatalogConstructorFixture.Input.class));
            malformed.remove("qualification");
            assertThrows(IOException.class, () -> mapper.treeToValue(malformed,
                    RuntimeCatalogConstructorFixture.Input.class));
        }
    }

    public static final class PrivateConstructor implements ProjectionPortCatalog {
        private PrivateConstructor() { }
        @Override public List<RegisteredProjection> registrations() { return List.of(); }
    }
    public static final class ArgumentOnlyConstructor implements ProjectionPortCatalog {
        public ArgumentOnlyConstructor(String input) { }
        @Override public List<RegisteredProjection> registrations() { return List.of(); }
    }
    public abstract static class AbstractCatalog implements ProjectionPortCatalog {
        public AbstractCatalog() { }
    }
}
