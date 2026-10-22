package org.xar.ck3.control.build;

import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Properties;
import java.util.Set;
import java.util.jar.JarFile;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

/** Verifies actual packaged ServiceLoader providers against the one qualified deployment and source graph. */
public final class ProjectionDeploymentProof {
    public static final String PRODUCER = "java-quarkus-projection/v1";
    public static final String VERSION = "0.1.0";
    public static final String CALL_SCHEMA = "xar.projection-call/v1";
    public static final String RESULT_SCHEMA = "xar.projection-result/v1";
    public static final String SERVICE_ENTRY = "META-INF/services/org.xar.ck3.control.contracts.projection.ProjectionPortCatalog";
    static final String OPERATION_CLASS = "org.xar.ck3.control.contracts.projection.ProjectionOperation";
    public static final int MAX_VALUE_BYTES = 8 << 20;
    public static final int MAX_ENVELOPE_BYTES = MAX_VALUE_BYTES + 4096;
    public static final int MAX_OBSERVATION_BYTES = 1 << 18;
    private ProjectionDeploymentProof() {}

    public record OperationProfile(String operation, int inputMaxBytes, int outputMaxBytes) {
        public OperationProfile {
            if (operation == null || !operation.matches("[a-z][a-z0-9]*(?:-[a-z0-9]+)*") || operation.length() > 128
                    || inputMaxBytes < 1 || inputMaxBytes > MAX_VALUE_BYTES
                    || outputMaxBytes < 1 || outputMaxBytes > MAX_VALUE_BYTES) {
                throw new IllegalArgumentException("Exact canonical operation wire and independent finite byte profiles required");
            }
        }
    }

    public record Identity(String schema, String producer, String producerVersion, String requestSchema,
                           String resultSchema, int envelopeMaxBytes, List<OperationProfile> operations) {
        public Identity {
            operations = uniqueProfiles(operations);
            if (!"xar.projection-host-identity/v1".equals(schema) || !PRODUCER.equals(producer) || !VERSION.equals(producerVersion)
                    || !CALL_SCHEMA.equals(requestSchema) || !RESULT_SCHEMA.equals(resultSchema)
                    || envelopeMaxBytes != MAX_ENVELOPE_BYTES) throw new IllegalArgumentException("Exact qualified projection identity required");
        }
    }

    public record CatalogIdentity(String providerClass, String artifactPath, List<OperationProfile> operations) {
        public CatalogIdentity {
            requireProviderName(providerClass); Objects.requireNonNull(artifactPath);
            if (!Path.of(artifactPath).isAbsolute()) throw new IllegalArgumentException("Actual provider code-source path required");
            operations = uniqueProfiles(operations);
            if (operations.isEmpty()) throw new IllegalArgumentException("Registered catalog must expose an actual operation");
        }
    }

    public record CatalogInventory(String schema, String machineId, String observedAtUtc, List<CatalogIdentity> catalogs) {
        public CatalogInventory {
            Objects.requireNonNull(machineId); Instant.parse(observedAtUtc); catalogs = List.copyOf(catalogs);
            if (!"xar.projection-host-catalogs/v1".equals(schema) || machineId.isBlank() || machineId.equals("unknown")
                    || catalogs.isEmpty() || catalogs.size() > 128
                    || catalogs.stream().map(CatalogIdentity::providerClass).distinct().count() != catalogs.size()) {
                throw new IllegalArgumentException("Actual unique finite catalog inventory with machine binding required");
            }
        }
    }

    public record BoundCatalog(String providerClass, ControlBuild.FileRef artifactRef,
            ControlBuild.FileRef providerSourceRef, ControlBuild.FileRef descriptorSourceRef,
            String packagedDescriptorSha256, List<OperationProfile> operations) {
        public BoundCatalog {
            requireProviderName(providerClass); Objects.requireNonNull(artifactRef);
            Objects.requireNonNull(providerSourceRef); Objects.requireNonNull(descriptorSourceRef);
            if (packagedDescriptorSha256 == null || !packagedDescriptorSha256.matches("[0-9a-f]{64}")) {
                throw new IllegalArgumentException("Exact packaged descriptor SHA required");
            }
            operations = uniqueProfiles(operations);
        }
    }

    public record Attestation(Identity identity, List<BoundCatalog> catalogs) {
        public Attestation { Objects.requireNonNull(identity); catalogs = List.copyOf(catalogs); }
    }

    private record JarCoordinates(String artifactId, String version) {}
    private record PackagedCatalog(String providerClass, ControlBuild.FileRef artifact, JarCoordinates coordinates, String descriptorSha256) {}

    public static Attestation attest(ControlBuild.BuildReceipt build, Identity identity, CatalogInventory inventory,
                                     String machineId) throws IOException {
        Objects.requireNonNull(build); Objects.requireNonNull(identity); Objects.requireNonNull(inventory); Objects.requireNonNull(machineId);
        if (!"PASS".equals(build.status()) || build.error() != null || build.targetKind() != ControlBuild.TargetKind.SERVICE_FAST_JAR
                || build.sourcePins().isEmpty() || build.completeDeployment().isEmpty()) throw new IOException("Accepted service deployment build required");
        if (!machineId.equals(build.machineId()) || !machineId.equals(inventory.machineId())) throw new IOException("Catalog/build machine mismatch");
        Instant observed = Instant.parse(inventory.observedAtUtc()), now = Instant.now();
        if (observed.isAfter(now.plusSeconds(5)) || observed.isBefore(now.minus(Duration.ofSeconds(30)))) {
            throw new IOException("Fresh actual catalog observation required");
        }
        return attestClosure(Path.of(build.sourceRoot()), build.sourcePins(), build.completeDeployment(), identity, inventory);
    }

    /** Explicit capture-only source/artifact attestation; this never converts capture compilation to software PASS. */
    public static Attestation attestCapture(ControlBuild.CaptureBuildReceipt build, Identity identity,
            CatalogInventory inventory, String machineId) throws IOException {
        Objects.requireNonNull(build); Objects.requireNonNull(identity); Objects.requireNonNull(inventory); Objects.requireNonNull(machineId);
        if (build.qualification() != ControlBuild.CaptureQualification.TEST_COMPILED_CAPTURE_ONLY
                || build.tests() != ControlBuild.CaptureTestState.NOT_RUN || !machineId.equals(build.machineId())
                || !machineId.equals(inventory.machineId())) throw new IOException("Exact same-machine capture-only compilation required");
        Instant observed = Instant.parse(inventory.observedAtUtc()), now = Instant.now();
        if (observed.isAfter(now.plusSeconds(5)) || observed.isBefore(now.minusSeconds(30))) throw new IOException("Fresh actual catalog observation required");
        return attestClosure(Path.of(build.sourceRoot()), build.sourcePins(), build.completeDeployment(), identity, inventory);
    }

    /** Shared packaged-artifact regression seam; production uses the accepted full BuildReceipt above. */
    static Attestation attestClosure(Path sourceRoot, List<ControlBuild.FileRef> sources,
            List<ControlBuild.FileRef> deployment, Identity identity, CatalogInventory inventory) throws IOException {
        List<PackagedCatalog> packaged = packagedCatalogs(deployment);
        if (packaged.size() != inventory.catalogs().size()) throw new IOException("Catalog descriptor and actual ServiceLoader inventory differ");
        Map<String, OperationProfile> operationUnion = new HashMap<>(); List<BoundCatalog> bound = new ArrayList<>();
        Set<String> compiledOperations = compiledOperationWires(deployment);
        for (CatalogIdentity actual : inventory.catalogs()) {
            PackagedCatalog expected = packaged.stream().filter(item -> item.providerClass().equals(actual.providerClass())).findFirst()
                    .orElseThrow(() -> new IOException("Undeclared provider or provider alias"));
            if (!Path.of(actual.artifactPath()).toRealPath().equals(Path.of(expected.artifact().path()).toRealPath())) {
                throw new IOException("Actual provider code source is not its qualified descriptor JAR");
            }
            ControlBuild.FileRef descriptor = uniqueSource(sources, "/src/main/resources/" + SERVICE_ENTRY,
                    expected.coordinates(), sourceRoot);
            ControlBuild.FileRef provider = uniqueSource(sources, "/src/main/java/"
                    + actual.providerClass().split("\\$", 2)[0].replace('.', '/') + ".java", expected.coordinates(), sourceRoot);
            List<String> sourceProviders = parseDescriptor(java.nio.file.Files.readAllBytes(Path.of(descriptor.path())));
            if (!sourceProviders.contains(actual.providerClass()) || !descriptor.sha256().equals(expected.descriptorSha256())) {
                throw new IOException("Packaged descriptor differs from complete actual source descriptor");
            }
            for (OperationProfile profile : actual.operations()) {
                if (!compiledOperations.contains(profile.operation()) || operationUnion.putIfAbsent(profile.operation(), profile) != null) {
                    throw new IOException("Unknown operation, operation alias or duplicate registration");
                }
            }
            bound.add(new BoundCatalog(actual.providerClass(), expected.artifact(), provider, descriptor, expected.descriptorSha256(), actual.operations()));
        }
        Map<String, OperationProfile> identityOperations = profileMap(identity.operations());
        if (!operationUnion.equals(identityOperations)) throw new IOException("Identity operations/profiles differ from actual catalog registration");
        bound.sort(Comparator.comparing(BoundCatalog::providerClass));
        for (ControlBuild.FileRef source : sources) source.verify();
        for (ControlBuild.FileRef file : deployment) file.verify();
        return new Attestation(identity, bound);
    }

    private static List<PackagedCatalog> packagedCatalogs(List<ControlBuild.FileRef> deployment) throws IOException {
        List<PackagedCatalog> catalogs = new ArrayList<>(); Set<String> providers = new HashSet<>();
        for (ControlBuild.FileRef file : deployment) {
            file.verify(); Path path = Path.of(file.path());
            if (!path.getFileName().toString().endsWith(".jar")) continue;
            try (JarFile jar = new JarFile(path.toFile())) {
                var descriptor = jar.getJarEntry(SERVICE_ENTRY);
                if (descriptor == null) continue;
                JarCoordinates coordinates = coordinates(jar);
                byte[] raw;
                try (InputStream input = jar.getInputStream(descriptor)) { raw = input.readNBytes(65537); }
                for (String provider : parseDescriptor(raw)) {
                    if (!providers.add(provider) || jar.getJarEntry(provider.replace('.', '/') + ".class") == null) {
                        throw new IOException("Duplicate provider alias or absent provider class in declaring JAR");
                    }
                    catalogs.add(new PackagedCatalog(provider, file, coordinates, digest(raw)));
                    if (catalogs.size() > 128) throw new IOException("Catalog count exceeds finite inventory");
                }
            }
        }
        if (catalogs.isEmpty()) throw new IOException("Actual deployment lacks packaged catalog descriptors");
        return List.copyOf(catalogs);
    }

    static List<String> parseDescriptor(byte[] raw) throws IOException {
        if (raw.length == 0 || raw.length > 65536) throw new IOException("Finite nonempty ServiceLoader descriptor required");
        String body = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
        List<String> result = new ArrayList<>(); Set<String> seen = new HashSet<>();
        for (String line : body.split("\\R", -1)) {
            String name = line.strip(); if (name.isEmpty()) continue;
            try { requireProviderName(name); } catch (IllegalArgumentException error) { throw new IOException("Canonical provider name without aliases required", error); }
            if (!seen.add(name)) throw new IOException("Duplicate provider in source or packaged descriptor");
            result.add(name);
        }
        if (result.isEmpty() || result.size() > 128) throw new IOException("Finite provider inventory required");
        return List.copyOf(result);
    }

    private static JarCoordinates coordinates(JarFile jar) throws IOException {
        List<String> properties = jar.stream().map(java.util.jar.JarEntry::getName)
                .filter(name -> name.startsWith("META-INF/maven/org.xar.ck3.control/") && name.endsWith("/pom.properties")).toList();
        if (properties.size() != 1) throw new IOException("Exactly one qualified project artifact identity required for provider JAR");
        Properties values = new Properties();
        try (InputStream input = jar.getInputStream(jar.getJarEntry(properties.getFirst()))) {
            byte[] raw = input.readNBytes(8193); if (raw.length > 8192) throw new IOException("Finite Maven artifact coordinates required");
            values.load(new java.io.ByteArrayInputStream(raw));
        }
        if (!"org.xar.ck3.control".equals(values.getProperty("groupId"))
                || !"0.1.0-SNAPSHOT".equals(values.getProperty("version"))
                || values.getProperty("artifactId") == null || values.getProperty("artifactId").isBlank()) {
            throw new IOException("Provider JAR must belong to the qualified control artifact/version");
        }
        return new JarCoordinates(values.getProperty("artifactId"), values.getProperty("version"));
    }

    private static ControlBuild.FileRef uniqueSource(List<ControlBuild.FileRef> sources, String suffix,
            JarCoordinates coordinates, Path sourceRoot) throws IOException {
        List<ControlBuild.FileRef> candidates = new ArrayList<>();
        Path root = sourceRoot.toAbsolutePath().normalize();
        for (ControlBuild.FileRef source : sources) {
            Path actual = Path.of(source.path()).toAbsolutePath().normalize();
            if (!actual.startsWith(root)) throw new IOException("Source escaped accepted root");
            String relative = root.relativize(actual).toString().replace('\\', '/');
            if (!relative.endsWith(suffix) || relative.indexOf('/') < 1) continue;
            String module = relative.substring(0, relative.indexOf('/'));
            Path pom = sourceRoot.resolve(module).resolve("pom.xml");
            ControlBuild.FileRef pin = sources.stream().filter(ref -> Path.of(ref.path()).normalize().equals(pom.normalize())).findFirst()
                    .orElseThrow(() -> new IOException("Provider source module POM absent from accepted source graph"));
            pin.verify(); source.verify();
            if (coordinates.artifactId().equals(moduleArtifactId(pom))) candidates.add(source);
        }
        if (candidates.size() != 1) throw new IOException("Provider source/descriptor must bind exactly one artifact module");
        return candidates.getFirst();
    }

    private static String moduleArtifactId(Path pom) throws IOException {
        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance(); factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, ""); factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            Element project = factory.newDocumentBuilder().parse(pom.toFile()).getDocumentElement();
            for (Node child = project.getFirstChild(); child != null; child = child.getNextSibling()) {
                if (child instanceof Element element && "artifactId".equals(element.getLocalName())) return element.getTextContent().strip();
            }
            throw new IOException("Direct module artifact identity missing");
        } catch (javax.xml.parsers.ParserConfigurationException | org.xml.sax.SAXException error) {
            throw new IOException("Module artifact identity invalid", error);
        }
    }

    /**
     * The standalone build-tools bootstrap deliberately has no reactor dependency.
     * This single reflection boundary reads the actual shared enum from qualified deployment JARs;
     * it does not maintain a second operation registry or load any provider/native implementation.
     */
    private static Set<String> compiledOperationWires(List<ControlBuild.FileRef> deployment) throws IOException {
        return sharedEnumWires(deployment, OPERATION_CLASS);
    }

    static Set<String> sharedEnumWires(List<ControlBuild.FileRef> deployment, String enumClass) throws IOException {
        if (!enumClass.startsWith("org.xar.ck3.control.contracts.projection.")) throw new IOException("Shared projection enum required");
        List<URL> urls = new ArrayList<>(); int owners = 0;
        for (ControlBuild.FileRef file : deployment) {
            Path path = Path.of(file.path()); if (!path.getFileName().toString().endsWith(".jar")) continue;
            try (JarFile jar = new JarFile(path.toFile())) { if (jar.getJarEntry(enumClass.replace('.', '/') + ".class") != null) owners++; }
            urls.add(path.toUri().toURL());
        }
        if (owners != 1 || urls.size() > 256) throw new IOException("Unique actual shared operation enum JAR required");
        try (URLClassLoader loader = new URLClassLoader(urls.toArray(URL[]::new), ClassLoader.getPlatformClassLoader())) {
            Class<?> type = Class.forName(enumClass, false, loader);
            if (!type.isEnum()) throw new IOException("Actual shared projection operation type must be enum");
            Object[] values = type.getEnumConstants(); Set<String> wires = new HashSet<>();
            if (values == null || values.length < 1 || values.length > 256) throw new IOException("Finite shared operation enum required");
            var wire = type.getMethod("wire");
            for (Object value : values) {
                Object observed = wire.invoke(value);
                if (!(observed instanceof String name) || name.length() > 128
                        || !name.matches("[a-z][a-z0-9]*(?:-[a-z0-9]+)*") || !wires.add(name)) {
                    throw new IOException("Actual shared projection enum wire is invalid or aliased");
                }
            }
            return Set.copyOf(wires);
        } catch (ReflectiveOperationException | LinkageError error) { throw new IOException("Qualified shared operation enum unavailable", error); }
    }

    private static Map<String, OperationProfile> profileMap(List<OperationProfile> profiles) {
        Map<String, OperationProfile> result = new HashMap<>(); for (OperationProfile profile : profiles) result.put(profile.operation(), profile);
        return Map.copyOf(result);
    }

    private static List<OperationProfile> uniqueProfiles(List<OperationProfile> profiles) {
        Objects.requireNonNull(profiles); List<OperationProfile> result = List.copyOf(profiles);
        if (result.size() > 256 || result.stream().map(OperationProfile::operation).distinct().count() != result.size()) {
            throw new IllegalArgumentException("Unique exact finite operation profiles required");
        }
        return result;
    }

    private static String digest(byte[] raw) {
        try { return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (java.security.NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }

    private static void requireProviderName(String name) {
        if (name == null || name.length() > 512 || !name.matches("[A-Za-z_$][A-Za-z0-9_$]*(?:\\.[A-Za-z_$][A-Za-z0-9_$]*)+")) {
            throw new IllegalArgumentException("Canonical qualified provider class required");
        }
    }
}
