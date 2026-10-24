package org.xar.ck3.control.build;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.xml.sax.ErrorHandler;
import org.xml.sax.SAXException;
import org.xml.sax.SAXParseException;

/** Exact unfiltered Maven test-resource origins inside one captured source tree. */
final class CompiledTestResourceOrigins {
    private static final String MAVEN = "http://maven.apache.org/POM/4.0.0";
    // Maven testResources addDefaultExcludes=true. Disabling these needs effective-model provenance.
    // https://maven.apache.org/plugins/maven-resources-plugin/testResources-mojo.html#addDefaultExcludes
    private static final List<String> DEFAULT_EXCLUDES = List.of(
            "**/*~", "**/#*#", "**/.#*", "**/%*%", "**/._*", "**/CVS", "**/CVS/**", "**/.cvsignore",
            "**/RCS", "**/RCS/**", "**/SCCS", "**/SCCS/**", "**/vssver.scc", "**/project.pj",
            "**/.svn", "**/.svn/**", "**/.arch-ids", "**/.arch-ids/**", "**/.bzr", "**/.bzr/**", "**/.bzrignore",
            "**/.MySCMServerInfo", "**/.DS_Store", "**/.metadata", "**/.metadata/**", "**/.hg", "**/.hg/**",
            "**/.hgignore", "**/.hgsub", "**/.hgsubstate", "**/.hgtags", "**/.git", "**/.git/**",
            "**/.gitignore", "**/.gitattributes", "**/.gitmodules", "**/BitKeeper", "**/BitKeeper/**",
            "**/ChangeSet", "**/ChangeSet/**", "**/_darcs", "**/_darcs/**", "**/.darcsrepo",
            "**/.darcsrepo/**", "**/-darcs-backup*", "**/.darcs-temp-mail");
    record Copy(ControlBuild.FileRef sourceRef, ControlBuild.FileRef outputRef) { }
    private record Resource(Path directory, Path target, List<String> includes, List<String> excludes) { }
    record Plan(Path snapshot, List<ControlBuild.FileRef> inputs, List<Resource> resources) {
        Plan { inputs = List.copyOf(inputs); resources = List.copyOf(resources); }
        Copy attest(Path outputRoot, Path output) throws IOException {
            require(output.startsWith(outputRoot) && !output.equals(outputRoot)
                    && output.toRealPath().equals(output), "Canonical classpath resource required");
            Path relative = outputRoot.relativize(output);
            var origins = new ArrayList<ControlBuild.FileRef>();
            for (var resource : resources) {
                if (!resource.target().toString().isEmpty() && !relative.startsWith(resource.target())) continue;
                Path inside = resource.target().toString().isEmpty() ? relative : resource.target().relativize(relative);
                String name = inside.toString().replace('\\', '/');
                if (name.isEmpty() || !matchesAny(resource.includes(), name) || matchesAny(resource.excludes(), name)) continue;
                require(!matchesAny(DEFAULT_EXCLUDES, name), "Default-excluded Maven resource is not an attested copy");
                Path candidate = resource.directory().resolve(inside).normalize();
                require(candidate.startsWith(snapshot), "Declared resource escaped captured project");
                var pins = inputs.stream().filter(item -> Path.of(item.path()).equals(candidate)).toList();
                require(pins.size() <= 1, "Duplicate compiler-source resource pin");
                if (!pins.isEmpty() && !origins.contains(pins.getFirst())) origins.add(pins.getFirst());
            }
            require(origins.size() == 1, "Classpath resource has no unique declared compiler-source provenance");
            var source = origins.getFirst(); source.verify();
            require(Path.of(source.path()).toRealPath().equals(Path.of(source.path())), "Resource source alias rejected");
            var actual = ControlBuild.FileRef.measure(output);
            require(source.bytes() == actual.bytes() && source.sha256().equals(actual.sha256()), "Copied classpath resource changed");
            source.verify(); return new Copy(source, actual);
        }
    }
    private CompiledTestResourceOrigins() { }

    static Plan read(Path snapshot, ControlBuild.FileRef pom, List<ControlBuild.FileRef> inputs) throws IOException {
        require(snapshot.isAbsolute() && snapshot.equals(snapshot.normalize()), "Canonical captured root required");
        Path module = Path.of(pom.path()).getParent();
        require(module.startsWith(snapshot) && !module.equals(snapshot), "Selected POM outside captured project");
        Element project = project(pom, inputs); rejectProfiles(project);
        checkParents(snapshot, module, project, inputs, 0);
        var build = optional(project, "build");
        var declarations = build == null ? null : optional(build, "testResources");
        var resources = new ArrayList<Resource>();
        if (declarations == null) resources.add(new Resource(module.resolve("src/test/resources"), Path.of(""), List.of("**"), List.of()));
        else {
            for (var entry : children(declarations, "testResource")) {
                for (var node : elements(entry)) require(List.of("directory", "targetPath", "filtering", "includes", "excludes").contains(name(node)),
                        "Unsupported test-resource field");
                require(value(entry, "filtering", "false").equals("false"), "Filtered resources need transformation provenance");
                String directory = expand(value(entry, "directory", null), module);
                Path declared = Path.of(directory);
                require(!declared.isAbsolute() || directory.startsWith(module.toString()), "Absolute foreign resource directory rejected");
                Path base = (declared.isAbsolute() ? declared : module.resolve(declared)).normalize();
                require(base.startsWith(snapshot), "Declared resource directory escaped captured project");
                resources.add(new Resource(base, relative(value(entry, "targetPath", ""), true),
                        patterns(entry, "includes", "include", List.of("**")), patterns(entry, "excludes", "exclude", List.of())));
            }
            require(resources.size() <= 64, "Finite resource directories required");
        }
        return new Plan(snapshot, inputs, resources);
    }
    private static void checkParents(Path snapshot, Path module, Element project, List<ControlBuild.FileRef> inputs, int depth) throws IOException {
        var parent = optional(project, "parent"); if (parent == null) return;
        require(depth < 16, "Finite captured parent chain required");
        String relative = value(parent, "relativePath", "../pom.xml");
        require(!relative.isEmpty() && !Path.of(relative).isAbsolute(), "External parent resource semantics not attested");
        Path path = module.resolve(relative).normalize(); require(path.startsWith(snapshot), "POM parent escaped captured project");
        var pins = inputs.stream().filter(item -> Path.of(item.path()).equals(path)).toList();
        require(pins.size() == 1, "Parent POM absent from captured sources");
        Element ancestor = project(pins.getFirst(), inputs); rejectProfiles(ancestor);
        var build = optional(ancestor, "build");
        require(build == null || optional(build, "testResources") == null, "Inherited test resources need effective-model provenance");
        checkParents(snapshot, path.getParent(), ancestor, inputs, depth + 1);
    }
    private static void rejectProfiles(Element project) throws IOException {
        var profiles = optional(project, "profiles");
        if (profiles != null) for (var profile : children(profiles, "profile")) {
            var build = optional(profile, "build");
            require(build == null || optional(build, "testResources") == null, "Profile-dependent resources need effective-model provenance");
        }
    }
    private static Element project(ControlBuild.FileRef pom, List<ControlBuild.FileRef> inputs) throws IOException {
        require(inputs.stream().filter(pom::equals).count() == 1 && pom.bytes() <= (256 << 10), "One bounded captured POM source required");
        pom.verify(); require(Path.of(pom.path()).toRealPath().equals(Path.of(pom.path())), "POM alias rejected");
        try {
            var factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true); factory.setXIncludeAware(false); factory.setExpandEntityReferences(false);
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
            factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
            factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, ""); factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            var parser = factory.newDocumentBuilder();
            parser.setErrorHandler(new ErrorHandler() {
                @Override public void warning(SAXParseException error) throws SAXException { throw error; }
                @Override public void error(SAXParseException error) throws SAXException { throw error; }
                @Override public void fatalError(SAXParseException error) throws SAXException { throw error; }
            });
            byte[] raw;
            try (var input = Files.newInputStream(Path.of(pom.path()))) { raw = input.readNBytes((256 << 10) + 1); }
            require(raw.length <= (256 << 10), "POM exceeded finite parse bound");
            Element result = parser.parse(new ByteArrayInputStream(raw)).getDocumentElement();
            require(result != null && name(result).equals("project") && (result.getNamespaceURI() == null || MAVEN.equals(result.getNamespaceURI())),
                    "Captured Maven project required");
            pom.verify(); return result;
        } catch (javax.xml.parsers.ParserConfigurationException | SAXException | IllegalArgumentException error) {
            throw new IOException("Captured POM is not a safe supported resource contract", error);
        }
    }
    private static String name(Element element) { return element.getLocalName() == null ? element.getTagName() : element.getLocalName(); }
    private static List<Element> elements(Element parent) throws IOException {
        var result = new ArrayList<Element>();
        for (Node node = parent.getFirstChild(); node != null; node = node.getNextSibling()) if (node instanceof Element child) {
            require(child.getNamespaceURI() == null || MAVEN.equals(child.getNamespaceURI()), "Foreign POM namespace rejected"); result.add(child);
        }
        return result;
    }
    private static List<Element> children(Element parent, String name) throws IOException {
        var result = new ArrayList<Element>(); for (var child : elements(parent)) if (name.equals(name(child))) result.add(child); return result;
    }
    private static Element optional(Element parent, String name) throws IOException {
        var matches = children(parent, name); require(matches.size() <= 1, "Repeated POM field: " + name);
        return matches.isEmpty() ? null : matches.getFirst();
    }
    private static String value(Element parent, String name, String fallback) throws IOException {
        var child = optional(parent, name);
        if (child == null) { require(fallback != null, "Missing POM resource field: " + name); return fallback; }
        require(elements(child).isEmpty(), "Scalar POM resource field required"); return child.getTextContent().trim();
    }
    private static String expand(String value, Path module) throws IOException {
        require(value != null && !value.isBlank() && value.length() <= 4096, "Bounded resource directory required");
        String result = value.replace("${project.basedir}", module.toString()).replace("${basedir}", module.toString());
        require(!result.contains("${"), "Unresolved POM resource property"); return result;
    }
    private static Path relative(String value, boolean empty) throws IOException {
        require(value.length() <= 4096 && (empty || !value.isEmpty()) && !value.contains("${")
                && !value.contains("\\") && !value.contains(":") && !value.startsWith("/"), "Relative Maven resource path required");
        Path path = Path.of(value);
        require(!path.isAbsolute() && path.equals(path.normalize()) && !path.startsWith(".."), "Resource target escaped output root"); return path;
    }
    private static List<String> patterns(Element parent, String field, String item, List<String> fallback) throws IOException {
        var list = optional(parent, field); if (list == null) return fallback;
        var result = new ArrayList<String>();
        for (var element : elements(list)) {
            require(item.equals(name(element)), "Unexpected resource pattern field");
            require(elements(element).isEmpty(), "Scalar Maven resource pattern required");
            String pattern = element.getTextContent().trim();
            require(!pattern.isEmpty() && !pattern.contains("\\") && !pattern.contains(":") && !pattern.startsWith("/")
                    && !pattern.contains("$" + "{") && java.util.Arrays.stream(pattern.split("/", -1))
                        .noneMatch(part -> part.equals("..") || part.equals(".")), "Relative Maven resource pattern required");
            require(pattern.length() <= 512, "Finite resource pattern required"); result.add(pattern.endsWith("/") ? pattern + "**" : pattern);
        }
        require(result.size() <= 128 && (!field.equals("includes") || !result.isEmpty()),
                "Finite nonempty explicit include patterns required"); return List.copyOf(result);
    }
    private static boolean matchesAny(List<String> patterns, String name) { return patterns.stream().anyMatch(pattern -> ant(pattern.split("/", -1), name.split("/", -1))); }
    private static boolean ant(String[] pattern, String[] name) {
        boolean[] previous = new boolean[name.length + 1]; previous[0] = true;
        for (String part : pattern) {
            boolean[] next = new boolean[name.length + 1];
            if (part.equals("**")) { next[0] = previous[0]; for (int j = 1; j <= name.length; j++) next[j] = previous[j] || next[j - 1]; }
            else for (int j = 1; j <= name.length; j++) next[j] = previous[j - 1] && segment(part, name[j - 1]);
            previous = next;
        }
        return previous[name.length];
    }
    private static boolean segment(String pattern, String name) {
        boolean[] previous = new boolean[name.length() + 1]; previous[0] = true;
        for (int i = 0; i < pattern.length(); i++) {
            char token = pattern.charAt(i); boolean[] next = new boolean[name.length() + 1];
            if (token == '*') { next[0] = previous[0]; for (int j = 1; j <= name.length(); j++) next[j] = previous[j] || next[j - 1]; }
            else for (int j = 1; j <= name.length(); j++) next[j] = previous[j - 1] && (token == '?' || token == name.charAt(j - 1));
            previous = next;
        }
        return previous[name.length()];
    }
    private static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }
}


