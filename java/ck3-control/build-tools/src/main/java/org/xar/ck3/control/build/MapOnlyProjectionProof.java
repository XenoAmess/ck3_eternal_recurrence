package org.xar.ck3.control.build;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.jar.JarFile;
import org.w3c.dom.Element;
/** Map-only; never full projection or Native authority. */
public final class MapOnlyProjectionProof {
  public static final String PROVIDER = "org.xar.ck3.control.service.MapAdmissionProjectionCatalog";
  public static final String OPERATION = "map-admission-compose";
  public enum Qualification { MAP_ONLY_CAPTURE }
  private MapOnlyProjectionProof() { }
  public record CatalogRow(String providerClass, String artifactPath,
      List<ProjectionDeploymentProof.OperationProfile> operations) {
    public CatalogRow {
      Objects.requireNonNull(providerClass); Objects.requireNonNull(artifactPath);
      if (!providerClass.matches("[A-Za-z_$][A-Za-z0-9_$]*(?:\\.[A-Za-z_$][A-Za-z0-9_$]*)+")
          || !Path.of(artifactPath).isAbsolute()) throw new IllegalArgumentException("Exact provider and artifact path required");
      operations = List.copyOf(operations);
      if (operations.size() > 256 || operations.stream().map(ProjectionDeploymentProof.OperationProfile::operation)
          .distinct().count() != operations.size()) throw new IllegalArgumentException("Unique finite operations required");
    }
  }
  public record Inventory(String schema, String machineId, String observedAtUtc, List<CatalogRow> catalogs) {
    public Inventory {
      Instant.parse(observedAtUtc); catalogs = List.copyOf(catalogs);
      if (!"xar.projection-host-catalogs/v1".equals(schema) || machineId == null || machineId.isBlank()
          || machineId.equals("unknown") || catalogs.isEmpty() || catalogs.size() > 128
          || catalogs.stream().map(CatalogRow::providerClass).distinct().count() != catalogs.size())
        throw new IllegalArgumentException("Exact finite same-machine catalog observations required");
    }
  }
  public record Binding(ProjectionDeploymentProof.OperationProfile profile, ControlBuild.FileRef artifactRef,
      ControlBuild.FileRef providerSourceRef, ControlBuild.FileRef descriptorSourceRef,
      ControlBuild.FileRef modulePomRef, ControlBuild.FileRef parentPomRef, Coordinates coordinates, String descriptorSha256) {
    public Binding {
      Objects.requireNonNull(profile); Objects.requireNonNull(artifactRef); Objects.requireNonNull(providerSourceRef);
      Objects.requireNonNull(descriptorSourceRef); Objects.requireNonNull(modulePomRef);
      Objects.requireNonNull(parentPomRef); Objects.requireNonNull(coordinates);
      if (!profile.equals(new ProjectionDeploymentProof.OperationProfile(OPERATION,65536,16384))
          || !descriptorSourceRef.sha256().equals(descriptorSha256)) throw new IllegalArgumentException("Exact map binding required");
    }
  }
  public record Admission(Qualification qualification, Binding binding, ControlBuild.FileRef programRef,
      ControlBuild.FileRef identityResponseRef, ControlBuild.FileRef catalogsResponseRef,
      MapAdmissionServiceOwner.ProcessWire processBefore, MapAdmissionServiceOwner.ProcessWire processAfter) {
    public Admission {
      Objects.requireNonNull(processBefore); Objects.requireNonNull(processAfter);
      if (qualification != Qualification.MAP_ONLY_CAPTURE || !Objects.equals(processBefore, processAfter))
        throw new IllegalArgumentException("Map-only same-process admission required");
      Objects.requireNonNull(binding); Objects.requireNonNull(programRef);
      Objects.requireNonNull(identityResponseRef); Objects.requireNonNull(catalogsResponseRef);
    }
    public void verify() throws IOException {
      programRef.verify(); identityResponseRef.verify(); catalogsResponseRef.verify();
      binding.artifactRef().verify(); binding.providerSourceRef().verify();
      binding.descriptorSourceRef().verify(); binding.modulePomRef().verify(); binding.parentPomRef().verify();
    }
  }
  public record BaseProgram(String schema, Qualification qualification, boolean normalQualified,
      boolean nativeAuthority, MapAdmissionServiceOwner.ProgramManifest compiledBase) {
    public BaseProgram {
      if (!"xar.java-map-only-capture-base/v1".equals(schema) || qualification != Qualification.MAP_ONLY_CAPTURE
          || normalQualified || nativeAuthority || compiledBase == null) throw new IllegalArgumentException("Explicit map-only compilation base required");
    }
  }
  static CatalogRow selected(ProjectionDeploymentProof.Identity identity, Inventory inventory, String machine) throws IOException {
    if (!machine.equals(inventory.machineId())) throw new IOException("Map catalog machine mismatch");
    Instant time = Instant.parse(inventory.observedAtUtc()), now = Instant.now();
    if (time.isBefore(now.minusSeconds(30)) || time.isAfter(now.plusSeconds(5))) throw new IOException("Fresh map catalog observation required");
    var profile = new ProjectionDeploymentProof.OperationProfile(OPERATION, 65536, 16384);
    if (!identity.operations().stream().filter(p -> OPERATION.equals(p.operation())).toList().equals(List.of(profile)))
      throw new IOException("Actual map identity profile differs from the original contract");
    List<CatalogRow> candidates = inventory.catalogs().stream().filter(c -> PROVIDER.equals(c.providerClass())).toList();
    long owners = inventory.catalogs().stream().flatMap(c -> c.operations().stream()).filter(p -> OPERATION.equals(p.operation())).count();
    if (candidates.size() != 1 || owners != 1 || !candidates.getFirst().operations().equals(List.of(profile)))
      throw new IOException("Exactly the original map provider and operation profile required");
    return candidates.getFirst();
  }
  static Binding attest(Path sourceRoot, List<ControlBuild.FileRef> sources, List<ControlBuild.FileRef> deployment,
      ProjectionDeploymentProof.Identity identity, Inventory inventory, String machine) throws IOException {
    CatalogRow row = selected(identity, inventory, machine);
    Path actual = Path.of(row.artifactPath()).toRealPath();
    List<ControlBuild.FileRef> artifacts = deployment.stream().filter(r -> Path.of(r.path()).toAbsolutePath().normalize().equals(actual)).toList();
    if (artifacts.size() != 1) throw new IOException("Map code source must be in the exact complete deployment");
    ControlBuild.FileRef artifact = artifacts.getFirst(); artifact.verify();
    ControlBuild.FileRef provider = source(sources, sourceRoot.resolve("local-service/src/main/java/" + PROVIDER.replace('.', '/') + ".java"));
    ControlBuild.FileRef descriptor = source(sources, sourceRoot.resolve("local-service/src/main/resources/" + ProjectionDeploymentProof.SERVICE_ENTRY));
    ControlBuild.FileRef pom = source(sources, sourceRoot.resolve("local-service/pom.xml"));
    ControlBuild.FileRef parent = source(sources, sourceRoot.resolve("pom.xml"));
    Coordinates coordinates = moduleCoordinates(pom, parent);
    byte[] raw = mapJar(actual, coordinates, PROVIDER);
    if (!ProjectionDeploymentProof.parseDescriptor(raw).contains(PROVIDER)
        || !java.util.Arrays.equals(raw, Files.readAllBytes(Path.of(descriptor.path()))))
      throw new IOException("Actual map descriptor differs from the captured source");
    artifact.verify(); provider.verify(); descriptor.verify(); pom.verify(); parent.verify();
    return new Binding(row.operations().getFirst(), artifact, provider, descriptor, pom, parent, coordinates, descriptor.sha256());
  }
  public record Coordinates(String groupId, String artifactId, String version) {
    public Coordinates {
      if (!"org.xar.ck3.control".equals(groupId) || !"ck3-control-local-service".equals(artifactId)
          || version == null || !version.matches("[A-Za-z0-9][A-Za-z0-9_.-]{0,127}"))
        throw new IllegalArgumentException("Map coordinates required");
    }
  }
  static Coordinates moduleCoordinates(ControlBuild.FileRef module, ControlBuild.FileRef parent) throws IOException {
    var root = pom(parent); var local = pom(module); var declared = child(local, "parent");
    if (declared == null || !"ck3-control-parent".equals(text(root,"artifactId"))
        || !text(root,"groupId").equals(text(declared,"groupId"))
        || !text(root,"artifactId").equals(text(declared,"artifactId"))
        || !text(root,"version").equals(text(declared,"version")))
      throw new IOException("Parent/module coordinates differ");
    String relative = text(declared,"relativePath");
    if (relative.isEmpty()) relative = "../pom.xml";
    if (!Path.of(module.path()).getParent().resolve(relative).toAbsolutePath().normalize()
        .equals(Path.of(parent.path()).toAbsolutePath().normalize())) throw new IOException("Module parent path differs");
    String group = text(local,"groupId"), version = text(local,"version");
    if (group.isEmpty()) group = text(declared,"groupId");
    if (version.isEmpty()) version = text(declared,"version");
    Coordinates result = new Coordinates(group, text(local,"artifactId"), version);
    if (!result.groupId().equals(text(root,"groupId")) || !result.version().equals(text(root,"version")))
      throw new IOException("Module/root coordinates differ");
    module.verify(); parent.verify(); return result;
  }
  private static Element pom(ControlBuild.FileRef pin) throws IOException {
    pin.verify(); if (pin.bytes() > 262144) throw new IOException("Finite POM required");
    try {
      var factory = javax.xml.parsers.DocumentBuilderFactory.newInstance(); factory.setNamespaceAware(true);
      factory.setFeature(javax.xml.XMLConstants.FEATURE_SECURE_PROCESSING,true);
      factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_DTD,""); factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_SCHEMA,"");
      factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl",true);
      var root = factory.newDocumentBuilder().parse(Path.of(pin.path()).toFile()).getDocumentElement();
      if (!"project".equals(root.getLocalName())) throw new IOException("Maven project element required");
      pin.verify(); return root;
    } catch (javax.xml.parsers.ParserConfigurationException | org.xml.sax.SAXException e) { throw new IOException("POM invalid",e); }
  }
  private static Element child(Element parent, String name) throws IOException {
    Element found = null;
    for (var n=parent.getFirstChild(); n!=null; n=n.getNextSibling())
      if (n instanceof Element e && name.equals(e.getLocalName())) {
        if (found!=null) throw new IOException("Duplicate direct POM field"); found=e;
      }
    return found;
  }
  private static String text(Element parent, String name) throws IOException {
    var value=child(parent,name); return value==null ? "" : value.getTextContent().strip();
  }
  static byte[] mapJar(Path path, Coordinates expected, String provider) throws IOException {
    try (JarFile jar=new JarFile(path.toFile())) {
      var descriptor=jar.getJarEntry(ProjectionDeploymentProof.SERVICE_ENTRY);
      var manifest=jar.getJarEntry("META-INF/MANIFEST.MF");
      if (descriptor==null || manifest==null || jar.getJarEntry(provider.replace('.','/')+".class")==null)
        throw new IOException("Provider, SPI and manifest required");
      byte[] bytes; try(var in=jar.getInputStream(manifest)) { bytes=in.readNBytes(8193); }
      if(bytes.length>8192) throw new IOException("Finite map manifest required");
      var attrs=new java.util.jar.Manifest(new java.io.ByteArrayInputStream(bytes)).getMainAttributes();
      if(!expected.artifactId().equals(attrs.getValue("Implementation-Title"))
          || !expected.version().equals(attrs.getValue("Implementation-Version"))) throw new IOException("JAR/module coordinates differ");
      try(var in=jar.getInputStream(descriptor)) { return in.readNBytes(65537); }
    }
  }
  private static ControlBuild.FileRef source(List<ControlBuild.FileRef> sources, Path path) throws IOException {
    List<ControlBuild.FileRef> found = sources.stream().filter(r -> Path.of(r.path()).toAbsolutePath().normalize()
        .equals(path.toAbsolutePath().normalize())).toList();
    if (found.size() != 1) throw new IOException("Unique captured map source required");
    found.getFirst().verify(); return found.getFirst();
  }
}

