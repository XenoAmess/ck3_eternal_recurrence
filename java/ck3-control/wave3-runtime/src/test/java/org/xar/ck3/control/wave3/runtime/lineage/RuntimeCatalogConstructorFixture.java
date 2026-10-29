package org.xar.ck3.control.wave3.runtime.lineage;

import java.io.IOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.Modifier;
import java.net.URL;
import java.net.URLClassLoader;
import java.net.URISyntaxException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ProjectionCaptureScope.Qualification;
import org.xar.ck3.control.build.ProjectionDeploymentProof;
import org.xar.ck3.control.build.ProjectionDeploymentProof.Attestation;
import org.xar.ck3.control.build.ProjectionDeploymentProof.BoundCatalog;
import org.xar.ck3.control.build.WindowsJobProcess;

/**
 * Read-only test consumer of the existing shared producer's real attestation.
 * It inspects constructors without instantiating a catalog or initializing its
 * class. Its report grants no build, deployment, native, process or Game authority.
 * The qualified shared producer remains responsible for the full artifact/source
 * attestation; this consumer never manufactures one from source declarations.
 */
public final class RuntimeCatalogConstructorFixture {
    private static final String W3_PREFIX = "org.xar.ck3.control.wave3.runtime.";
    private static final String SPI = "org.xar.ck3.control.contracts.projection.ProjectionPortCatalog";
    private static final int INPUT_MAX_BYTES = 65_536;
    private static final int ATTESTATION_MAX_BYTES = 524_288;

    /** Preserves the existing shared qualification; capture-only is never promoted to PASS. */
    public record Input(String schema, String machineId, Qualification qualification,
            ControlBuild.FileRef producerReceiptRef,
            ControlBuild.FileRef catalogInventoryRef, ControlBuild.FileRef attestationRef,
            List<ControlBuild.FileRef> completeDeployment) {
        public Input {
            if (!"xar.runtime-catalog-constructor-input/v1".equals(schema) || machineId == null
                    || !machineId.matches("[a-z0-9][a-z0-9-]{0,63}") || machineId.equals("unknown")) {
                throw new IllegalArgumentException("Exact same-machine constructor-inspection input required");
            }
            Objects.requireNonNull(qualification); Objects.requireNonNull(producerReceiptRef);
            Objects.requireNonNull(catalogInventoryRef);
            Objects.requireNonNull(attestationRef);
            if (producerReceiptRef.bytes() < 1 || producerReceiptRef.bytes() > ControlBuild.BUILD_RECEIPT_MAX_BYTES
                    || catalogInventoryRef.bytes() < 1
                    || catalogInventoryRef.bytes() > ProjectionDeploymentProof.MAX_OBSERVATION_BYTES) {
                throw new IllegalArgumentException("Bounded actual shared build and fresh catalog inventory required");
            }
            if (attestationRef.bytes() < 1 || attestationRef.bytes() > ATTESTATION_MAX_BYTES) {
                throw new IllegalArgumentException("Bounded real shared attestation reference required");
            }
            completeDeployment = List.copyOf(completeDeployment);
            if (completeDeployment.isEmpty() || completeDeployment.size() > 256) {
                throw new IllegalArgumentException("Finite complete actual deployment required");
            }
        }
    }

    /** The existing BoundCatalog remains the sole artifact/provider/source/profile representation. */
    public record ConstructorLineage(BoundCatalog catalog, String declaringClass,
            String jvmConstructorDescriptor, boolean finalProviderClass) {
        public ConstructorLineage {
            Objects.requireNonNull(catalog);
            if (!catalog.providerClass().equals(declaringClass) || !"()V".equals(jvmConstructorDescriptor)) {
                throw new IllegalArgumentException("Exact public no-argument provider constructor required");
            }
        }
    }

    public record Report(String schema, String machineId, String observedAtUtc, Qualification qualification,
            ControlBuild.FileRef producerReceiptRef, ControlBuild.FileRef catalogInventoryRef,
            ControlBuild.FileRef attestationRef, List<ConstructorLineage> constructors,
            boolean deploymentQualificationGranted) {
        public Report {
            if (!"xar.runtime-catalog-constructor-inspection/v1".equals(schema)
                    || deploymentQualificationGranted) {
                throw new IllegalArgumentException("Constructor inspection cannot grant deployment qualification");
            }
            Objects.requireNonNull(machineId); Instant.parse(observedAtUtc);
            Objects.requireNonNull(qualification); Objects.requireNonNull(producerReceiptRef);
            Objects.requireNonNull(catalogInventoryRef);
            Objects.requireNonNull(attestationRef); constructors = List.copyOf(constructors);
            if (constructors.isEmpty()) throw new IllegalArgumentException("Actual W3 catalog constructors required");
        }
    }

    private RuntimeCatalogConstructorFixture() { }

    public static void main(String[] args) throws IOException {
        if (args.length != 1) throw new IllegalArgumentException("One explicit typed input path required");
        Input input = ControlBuild.strictMapper().readValue(readBounded(Path.of(args[0]), INPUT_MAX_BYTES), Input.class);
        String machine = WindowsJobProcess.currentMachineId();
        if (!machine.equals(input.machineId())) throw new IOException("Actual constructor-inspection machine differs");
        input.producerReceiptRef().verify(); input.catalogInventoryRef().verify();
        ProjectionDeploymentProof.CatalogInventory inventory = ControlBuild.strictMapper().readValue(
                readBounded(Path.of(input.catalogInventoryRef().path()), ProjectionDeploymentProof.MAX_OBSERVATION_BYTES),
                ProjectionDeploymentProof.CatalogInventory.class);
        input.attestationRef().verify();
        Attestation proof = ControlBuild.strictMapper().readValue(
                readBounded(Path.of(input.attestationRef().path()), ATTESTATION_MAX_BYTES), Attestation.class);
        // Both branches require the real shared producer. A hand-written Attestation
        // DTO is insufficient, and a capture receipt is never coerced into BuildReceipt.
        Attestation revalidated = switch (input.qualification()) {
            case FULL_SOFTWARE -> {
                ControlBuild.BuildReceipt build = ControlBuild.acceptedReceipt(Path.of(input.producerReceiptRef().path()));
                if (!build.completeDeployment().equals(input.completeDeployment())) {
                    throw new IOException("Constructor-inspection closure differs from accepted full build");
                }
                yield ProjectionDeploymentProof.attest(build, proof.identity(), inventory, machine);
            }
            case TEST_COMPILED_CAPTURE_ONLY -> {
                ControlBuild.CaptureBuildReceipt build = ControlBuild.acceptedCaptureReceipt(Path.of(input.producerReceiptRef().path()));
                if (!build.completeDeployment().equals(input.completeDeployment())) {
                    throw new IOException("Constructor-inspection closure differs from accepted capture-only compilation");
                }
                yield ProjectionDeploymentProof.attestCapture(build, proof.identity(), inventory, machine);
            }
        };
        if (!revalidated.equals(proof)) throw new IOException("Supplied attestation differs from the shared actual producer");
        List<ConstructorLineage> constructors = inspect(proof, input.completeDeployment());
        input.producerReceiptRef().verify(); input.catalogInventoryRef().verify(); input.attestationRef().verify();
        Report report = new Report("xar.runtime-catalog-constructor-inspection/v1", machine,
                Instant.now().toString(), input.qualification(), input.producerReceiptRef(), input.catalogInventoryRef(),
                input.attestationRef(), constructors, false);
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(report);
        if (raw.length > INPUT_MAX_BYTES) throw new IOException("Constructor metadata exceeds finite output budget");
        System.out.write(raw); System.out.write('\n');
    }

    /** Test seam consumes explicit synthetic proofs; it never qualifies those proofs as actual builds. */
    static List<ConstructorLineage> inspect(Attestation proof, List<ControlBuild.FileRef> deployment) throws IOException {
        Objects.requireNonNull(proof); deployment = List.copyOf(deployment);
        if (deployment.isEmpty() || deployment.size() > 256) throw new IOException("Finite actual JAR closure required");
        List<URL> urls = new ArrayList<>();
        for (ControlBuild.FileRef artifact : deployment) {
            artifact.verify();
            Path path = Path.of(artifact.path());
            if (path.getFileName().toString().endsWith(".jar")) urls.add(path.toUri().toURL());
        }
        if (urls.isEmpty()) throw new IOException("Actual JAR closure required; target/classes is not a JAR");
        List<ConstructorLineage> result = new ArrayList<>();
        try (URLClassLoader loader = new URLClassLoader(urls.toArray(URL[]::new), ClassLoader.getPlatformClassLoader())) {
            Class<?> spi = Class.forName(SPI, false, loader);
            for (BoundCatalog catalog : proof.catalogs()) {
                if (!catalog.providerClass().startsWith(W3_PREFIX)) continue; // W2/domain catalogs keep their own ownership.
                if (!deployment.contains(catalog.artifactRef())
                        || !catalog.artifactRef().path().endsWith(".jar")) {
                    throw new IOException("W3 catalog must bind a member of the complete actual JAR closure");
                }
                catalog.artifactRef().verify(); catalog.providerSourceRef().verify(); catalog.descriptorSourceRef().verify();
                Class<?> provider = Class.forName(catalog.providerClass(), false, loader);
                Constructor<?> constructor = requirePublicNoArgument(provider, spi);
                Path origin = actualCodeSource(provider);
                if (!origin.equals(Path.of(catalog.artifactRef().path()).toRealPath()) || !Files.isRegularFile(origin)) {
                    throw new IOException("Loaded provider CodeSource differs from its attested actual JAR");
                }
                result.add(new ConstructorLineage(catalog, constructor.getDeclaringClass().getName(), "()V",
                        Modifier.isFinal(provider.getModifiers())));
            }
        } catch (ReflectiveOperationException | LinkageError error) {
            throw new IOException("Actual deployed W3 catalog constructor or SPI is unavailable", error);
        }
        if (result.isEmpty()) throw new IOException("Shared attestation contains no actual W3 catalog; never skip");
        for (ControlBuild.FileRef artifact : deployment) artifact.verify();
        for (ConstructorLineage row : result) {
            row.catalog().providerSourceRef().verify(); row.catalog().descriptorSourceRef().verify();
        }
        return List.copyOf(result);
    }

    /** Checked dynamic boundary for classes loaded from the accepted closure, with no unchecked cast. */
    static Constructor<?> requirePublicNoArgument(Class<?> provider, Class<?> spi) throws IOException {
        if (!spi.isInterface() || !spi.isAssignableFrom(provider) || provider.isInterface()
                || !Modifier.isPublic(provider.getModifiers()) || Modifier.isAbstract(provider.getModifiers())) {
            throw new IOException("Concrete public provider of the actual shared SPI required");
        }
        try { return provider.getConstructor(); }
        catch (NoSuchMethodException error) { throw new IOException("Actual public no-argument catalog constructor required", error); }
    }

    private static Path actualCodeSource(Class<?> type) throws IOException {
        var domain = type.getProtectionDomain();
        if (domain == null || domain.getCodeSource() == null || domain.getCodeSource().getLocation() == null) {
            throw new IOException("Actual provider CodeSource missing");
        }
        try {
            var uri = domain.getCodeSource().getLocation().toURI();
            if (!"file".equalsIgnoreCase(uri.getScheme())) throw new IOException("Actual provider file CodeSource required");
            return Path.of(uri).toRealPath();
        } catch (URISyntaxException error) { throw new IOException("Actual provider CodeSource URI invalid", error); }
    }

    private static byte[] readBounded(Path path, int maximum) throws IOException {
        byte[] raw;
        try (var input = Files.newInputStream(path)) { raw = input.readNBytes(maximum + 1); }
        if (raw.length == 0 || raw.length > maximum) throw new IOException("Finite nonempty typed inspection input required");
        return raw;
    }
}
