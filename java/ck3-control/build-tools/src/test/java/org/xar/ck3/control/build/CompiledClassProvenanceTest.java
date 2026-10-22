package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import javax.tools.ToolProvider;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Actual javac runs in this Maven test JVM; these fixtures never claim a successful external Maven/Job receipt. */
final class CompiledClassProvenanceTest {
    @TempDir Path temporary;
    private static final String SOURCE = """
            package sample;
            public class Origins {
                static final long LONG = 9223372036854775806L;
                static final double DOUBLE = 123456.789;
                static final String TEXT = "\\0é𝄞";
                String value;
                String value() { return value; }
                Runnable action() { return () -> System.out.print(TEXT); }
                public static class Child {}
            }
            class Sibling {}
            """;

    @Test void actualLongDoubleModifiedUtfLambdaInnerAndSiblingBindTheirSourceFile() throws Exception {
        Fixture fixture = compile("actual", true);
        for (String name : List.of("Origins", "Origins$Child", "Sibling")) {
            var actual = attest(fixture, fixture.output().resolve("sample/" + name + ".class"));
            assertEquals("sample." + name, actual.binaryName()); assertEquals("Origins.java", actual.sourceFile());
            assertEquals(fixture.sourceRef(), actual.sourceRef()); assertEquals(fixture.output().toRealPath().toString(), actual.runtimeOrigin());
            actual.classRef().verify(); actual.sourceRef().verify();
            assertEquals(actual, ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(actual),
                    CompiledClassProvenance.Origin.class));
        }
    }

    @Test void actualModuleClassSupportsModuleAndPackageConstants() throws Exception {
        Path module = Files.createDirectories(temporary.resolve("module")), sourceRoot = Files.createDirectories(module.resolve("src/main/java"));
        Path descriptor = Files.writeString(sourceRoot.resolve("module-info.java"), "module fixture.module { exports sample; }");
        Path source = Files.writeString(Files.createDirectories(sourceRoot.resolve("sample")).resolve("Origins.java"), SOURCE);
        Path output = Files.createDirectories(temporary.resolve("module-output"));
        javac(output, true, descriptor, source);
        var descriptorRef = ControlBuild.FileRef.measure(descriptor);
        var actual = CompiledClassProvenance.attest(output, ControlBuild.FileRef.measure(output.resolve("module-info.class")),
                module, CompiledClassProvenance.SourceSet.MAIN, List.of(descriptorRef, ControlBuild.FileRef.measure(source)));
        assertEquals("module-info", actual.binaryName()); assertEquals("module-info.java", actual.sourceFile());
        assertEquals(descriptorRef, actual.sourceRef());
    }

    @Test void validUnusedDynamicConstantKeepsPoolAlignment() throws Exception {
        Fixture fixture = compile("dynamic", true); Path file = fixture.output().resolve("sample/Origins.class");
        byte[] original = Files.readAllBytes(file); Pool pool = pool(original);
        assertTrue(pool.fieldNameAndType() > 0, "actual javac field reference supplies a field descriptor");
        byte[] altered = new byte[original.length + 5];
        System.arraycopy(original, 0, altered, 0, pool.end()); putU2(altered, 8, pool.count() + 1);
        altered[pool.end()] = 17; putU2(altered, pool.end() + 1, 0); putU2(altered, pool.end() + 3, pool.fieldNameAndType());
        System.arraycopy(original, pool.end(), altered, pool.end() + 5, original.length - pool.end());
        Files.write(file, altered);
        assertEquals("sample.Origins", attest(fixture, file).binaryName());
    }

    @Test void renamedClassAndForgedInternalBinaryCannotAcquireAnOrigin() throws Exception {
        Fixture fixture = compile("names", true); Path file = fixture.output().resolve("sample/Origins.class");
        Path renamed = Files.copy(file, fixture.output().resolve("sample/Forgery.class"));
        assertThrows(IOException.class, () -> attest(fixture, renamed));
        byte[] altered = Files.readAllBytes(file); replaceAscii(altered, "sample/Origins", "sample/Forgery"); Files.write(file, altered);
        assertThrows(IOException.class, () -> attest(fixture, file));
    }

    @Test void sourceMustBeExactlyOnePinnedFileInTheActualModuleAndSourceSet() throws Exception {
        Fixture fixture = compile("source", true); Path file = fixture.output().resolve("sample/Origins.class");
        var classRef = ControlBuild.FileRef.measure(file);
        assertThrows(IOException.class, () -> CompiledClassProvenance.attest(fixture.output(), classRef, fixture.module(),
                CompiledClassProvenance.SourceSet.TEST, List.of()));
        assertThrows(IOException.class, () -> CompiledClassProvenance.attest(fixture.output(), classRef, fixture.module(),
                CompiledClassProvenance.SourceSet.TEST, List.of(fixture.sourceRef(), fixture.sourceRef())));
        assertThrows(IOException.class, () -> CompiledClassProvenance.attest(fixture.output(), classRef, fixture.module(),
                CompiledClassProvenance.SourceSet.MAIN, List.of(fixture.sourceRef())));
        Path otherModule = Files.createDirectories(temporary.resolve("other-module"));
        Path otherSource = Files.copy(Path.of(fixture.sourceRef().path()), Files.createDirectories(otherModule.resolve("src/test/java/sample")).resolve("Origins.java"));
        assertThrows(IOException.class, () -> CompiledClassProvenance.attest(fixture.output(), classRef, fixture.module(),
                CompiledClassProvenance.SourceSet.TEST, List.of(ControlBuild.FileRef.measure(otherSource))));
        // A same-basename file in another module is never borrowed or treated as an ambiguity in the bound module.
        assertEquals(fixture.sourceRef(), CompiledClassProvenance.attest(fixture.output(), classRef, fixture.module(),
                CompiledClassProvenance.SourceSet.TEST, List.of(ControlBuild.FileRef.measure(otherSource), fixture.sourceRef())).sourceRef());
        Files.writeString(Path.of(fixture.sourceRef().path()), SOURCE + "// changed after actual snapshot\n");
        assertThrows(IOException.class, () -> attest(fixture, file));
    }

    @Test void classMutationAndMissingOrDuplicatedSourceFileAreRejected() throws Exception {
        Fixture fixture = compile("pinned", true); Path file = fixture.output().resolve("sample/Origins.class");
        var before = ControlBuild.FileRef.measure(file); byte[] original = Files.readAllBytes(file);
        byte[] changed = original.clone(); changed[0] = 0; Files.write(file, changed);
        assertThrows(IOException.class, () -> CompiledClassProvenance.attest(fixture.output(), before, fixture.module(),
                CompiledClassProvenance.SourceSet.TEST, List.of(fixture.sourceRef())));
        assertThrows(IOException.class, () -> attest(fixture, file));
        Fixture noSource = compile("no-source", false);
        assertThrows(IOException.class, () -> attest(noSource, noSource.output().resolve("sample/Origins.class")));
        Pool pool = pool(original); int attributes = classAttributes(original, pool.end());
        int position = attributes + 2, sourceAttribute = -1;
        for (int index = 0; index < u2(original, attributes); index++) {
            if (u2(original, position) == pool.sourceAttributeName()) sourceAttribute = position;
            position += 6 + (int) u4(original, position + 2);
        }
        assertTrue(sourceAttribute >= 0); assertEquals(2, u4(original, sourceAttribute + 2));
        byte[] duplicate = Arrays.copyOf(original, original.length + 8);
        putU2(duplicate, attributes, u2(original, attributes) + 1);
        System.arraycopy(original, sourceAttribute, duplicate, original.length, 8); Files.write(file, duplicate);
        assertThrows(IOException.class, () -> attest(fixture, file));
    }

    @Test void byteBoundariesAndMalformedModifiedUtfNeverBecomeAnOrigin() throws Exception {
        Fixture fixture = compile("malformed", true); Path file = fixture.output().resolve("sample/Origins.class");
        byte[] original = Files.readAllBytes(file);
        for (int length : List.of(1, 9, original.length - 1)) {
            Files.write(file, Arrays.copyOf(original, length)); assertThrows(IOException.class, () -> attest(fixture, file));
        }
        Files.write(file, Arrays.copyOf(original, original.length + 1)); assertThrows(IOException.class, () -> attest(fixture, file));
        for (int lead : List.of(0, 0x80, 0xf0)) {
            byte[] malformed = original.clone(); int offset = asciiOffset(malformed, "sample/Origins"); malformed[offset] = (byte) lead;
            Files.write(file, malformed); assertThrows(IOException.class, () -> attest(fixture, file));
        }
        byte[] malformed = original.clone(); int offset = asciiOffset(malformed, "sample/Origins");
        malformed[offset] = (byte) 0xc0; malformed[offset + 1] = (byte) 0xaf; Files.write(file, malformed);
        assertThrows(IOException.class, () -> attest(fixture, file), "overlong non-NUL modified UTF-8 must be rejected");
        var huge = new ControlBuild.FileRef(file.toAbsolutePath().toString(), CompiledClassProvenance.MAX_CLASS_BYTES + 1L, "0".repeat(64));
        assertThrows(IOException.class, () -> CompiledClassProvenance.attest(fixture.output(), huge, fixture.module(),
                CompiledClassProvenance.SourceSet.TEST, List.of(fixture.sourceRef())));
    }

    private record Fixture(Path module, Path output, ControlBuild.FileRef sourceRef) {}
    private Fixture compile(String name, boolean sourceAttribute) throws IOException {
        Path module = Files.createDirectories(temporary.resolve(name));
        Path source = Files.writeString(Files.createDirectories(module.resolve("src/test/java/sample")).resolve("Origins.java"), SOURCE);
        Path output = Files.createDirectories(module.resolve("target/test-classes")); javac(output, sourceAttribute, source);
        return new Fixture(module, output, ControlBuild.FileRef.measure(source));
    }
    private static void javac(Path output, boolean sourceAttribute, Path... sources) throws IOException {
        var compiler = ToolProvider.getSystemJavaCompiler(); assertNotNull(compiler, "Actual JDK compiler required, never skip");
        var arguments = new java.util.ArrayList<>(List.of("-encoding", "UTF-8", sourceAttribute ? "-g:source" : "-g:none", "-proc:none", "-d", output.toString()));
        for (Path source : sources) arguments.add(source.toString());
        try (var diagnostic = new ByteArrayOutputStream()) {
            assertEquals(0, compiler.run(null, diagnostic, diagnostic, arguments.toArray(String[]::new)), diagnostic.toString(StandardCharsets.UTF_8));
        }
    }
    private static CompiledClassProvenance.Origin attest(Fixture fixture, Path file) throws IOException {
        return CompiledClassProvenance.attest(fixture.output(), ControlBuild.FileRef.measure(file), fixture.module(),
                CompiledClassProvenance.SourceSet.TEST, List.of(fixture.sourceRef()));
    }

    // Locate real javac structures only to mutate the actual entry bytes; these offsets never stand in for production provenance.
    private record Pool(int end, int count, int fieldNameAndType, int sourceAttributeName) {}
    private static Pool pool(byte[] bytes) throws IOException {
        try (var input = new DataInputStream(new ByteArrayInputStream(bytes))) {
            input.skipNBytes(8); int count = input.readUnsignedShort(), field = 0, sourceName = 0;
            for (int index = 1; index < count; index++) {
                switch (input.readUnsignedByte()) {
                    case 1 -> { if (input.readUTF().equals("SourceFile")) sourceName = index; }
                    case 3, 4 -> input.skipNBytes(4);
                    case 5, 6 -> { input.skipNBytes(8); index++; }
                    case 7, 8, 16, 19, 20 -> input.skipNBytes(2);
                    case 9 -> { input.readUnsignedShort(); field = input.readUnsignedShort(); }
                    case 10, 11, 12, 17, 18 -> input.skipNBytes(4);
                    case 15 -> input.skipNBytes(3);
                    default -> throw new IOException("Unexpected actual compiler constant");
                }
            }
            return new Pool(bytes.length - input.available(), count, field, sourceName);
        }
    }
    private static int classAttributes(byte[] bytes, int poolEnd) throws IOException {
        try (var input = new DataInputStream(new ByteArrayInputStream(bytes, poolEnd, bytes.length - poolEnd))) {
            input.skipNBytes(6); input.skipNBytes(2L * input.readUnsignedShort());
            for (int section = 0; section < 2; section++) {
                int count = input.readUnsignedShort();
                for (int member = 0; member < count; member++) {
                    input.skipNBytes(6); int attributes = input.readUnsignedShort();
                    for (int attribute = 0; attribute < attributes; attribute++) { input.readUnsignedShort(); input.skipNBytes(Integer.toUnsignedLong(input.readInt())); }
                }
            }
            return bytes.length - input.available();
        }
    }
    private static int asciiOffset(byte[] bytes, String value) {
        byte[] expected = value.getBytes(StandardCharsets.US_ASCII);
        outer: for (int offset = 0; offset <= bytes.length - expected.length; offset++) {
            for (int index = 0; index < expected.length; index++) if (bytes[offset + index] != expected[index]) continue outer;
            return offset;
        }
        throw new AssertionError("Actual compiler constant not found: " + value);
    }
    private static void replaceAscii(byte[] bytes, String before, String after) {
        assertEquals(before.length(), after.length()); int offset = asciiOffset(bytes, before);
        System.arraycopy(after.getBytes(StandardCharsets.US_ASCII), 0, bytes, offset, after.length());
    }
    private static int u2(byte[] bytes, int offset) { return ((bytes[offset] & 255) << 8) | (bytes[offset + 1] & 255); }
    private static long u4(byte[] bytes, int offset) { return ((long) u2(bytes, offset) << 16) | u2(bytes, offset + 2); }
    private static void putU2(byte[] bytes, int offset, int value) { bytes[offset] = (byte) (value >>> 8); bytes[offset + 1] = (byte) value; }
}
