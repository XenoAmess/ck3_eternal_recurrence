package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Random;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.condition.EnabledOnOs;
import org.junit.jupiter.api.condition.OS;

@EnabledOnOs(value = OS.WINDOWS, disabledReason = "UNAVAILABLE: original Windows NLS/Python differential requires Windows; disabled is not a verified result")
final class LegacyWindowsPathCanonicalizerTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String RESOURCE = "/org/xar/ck3/control/contracts/legacy-windows-path-reference.json";

    // Test oracle only: compile the exact AST expression in the original Rite
    // producer; no copied path algorithm and no new Python production adapter.
    private static final String ORIGINAL_PRODUCER = """
import ast, ctypes, hashlib, json, nt, ntpath, os, pathlib, sys, unicodedata
assert os.name == 'nt', 'reference must be native Windows CPython'
assert sys.version_info[:2] == (3, 13), 'original CPython family changed; reassess the pinned C algorithm'
assert ntpath.normpath is nt._path_normpath, 'native normpath required'
assert ntpath._LCMapStringEx.__module__ == '_winapi', 'original NLS normcase required'
original = pathlib.Path(sys.argv[1])
source = original.read_bytes()
tree = ast.parse(source, filename=str(original))
binding = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_binding')
terms = [node for node in ast.walk(binding) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'normcase']
assert len(terms) == 1
expected = ast.parse('''ntpath.normcase(ntpath.normpath(managed['state_dir']))''', mode='eval')
assert ast.dump(terms[0]) == ast.dump(expected.body), 'original producer changed'
expression = compile(ast.Expression(terms[0]), str(original), 'eval')
class Version(ctypes.Structure):
    _fields_ = [('size', ctypes.c_uint32), ('nls', ctypes.c_uint32), ('defined', ctypes.c_uint32), ('effective', ctypes.c_uint32), ('custom', ctypes.c_ubyte * 16)]
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.GetNLSVersionEx.argtypes = [ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(Version)]
kernel.GetNLSVersionEx.restype = ctypes.c_int
version = Version()
version.size = ctypes.sizeof(version)
assert kernel.GetNLSVersionEx(1, '', ctypes.byref(version)), ctypes.get_last_error()
inputs = json.loads(sys.stdin.buffer.read())
assert type(inputs) is list and all(type(value) is str for value in inputs)
outputs = [eval(expression, {'ntpath': ntpath, 'managed': {'state_dir': value}}) for value in inputs]
print(json.dumps({'source_sha256': hashlib.sha256(source).hexdigest(), 'cpython': sys.version.split()[0], 'unicode_data': unicodedata.unidata_version, 'nls': format(version.nls, '08x'), 'defined': format(version.defined, '08x'), 'effective': format(version.effective, '08x'), 'custom': bytes(version.custom).hex(), 'outputs': outputs}, ensure_ascii=True))
""";

    @Test void originalProducerCorpusIncludesNonFilesystemStringCases() throws Exception {
        JsonNode reference = reference();
        requireWindows();
        assertEquals("3.13.2", reference.path("cpython").asText());
        assertEquals("15.1.0", reference.path("unicode_data").asText());
        assertEquals("WINDOWS_NLS_UNICODE_VERSION_NOT_EXPOSED",
                LegacyWindowsPathCanonicalizer.casingVersion().casingUnicodeVersion());
        JsonNode signature = reference.path("nls_signature");
        var actual = LegacyWindowsPathCanonicalizer.casingVersion();
        assertEquals(signature.path("nls").asText(), actual.nlsVersionHex(), "reference machine NLS changed; recollect before claiming differential PASS");
        assertEquals(signature.path("defined").asText(), actual.definedVersionHex());
        assertEquals(signature.path("effective").asText(), actual.effectiveLocaleHex());
        assertEquals(signature.path("custom").asText(), actual.customVersionBytesHex());
        for (JsonNode example : reference.path("cases")) {
            assertEquals(example.path("output").asText(),
                    LegacyWindowsPathCanonicalizer.normalize(example.path("input").asText()),
                    example.path("case").asText());
        }
        assertThrows(NullPointerException.class, () -> LegacyWindowsPathCanonicalizer.normalize(null));
    }

    @Test void actualOriginalProducerMatchesInTwoIndependentProcesses(@TempDir Path temporary) throws Exception {
        requireWindows();
        JsonNode reference = reference();
        Path original = Path.of(requiredProperty("xar.legacy.windows.riteSource"));
        assertEquals(reference.path("rite_source_sha256").asText(),
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(original))));
        List<String> cases = new ArrayList<>();
        for (JsonNode example : reference.path("cases")) cases.add(example.path("input").asText());
        Random random = new Random(0x52544954454cL);
        String[] atoms = {"", ".", "..", "...", "A", "B ", "C:", "nul", "?", "UNC", "\u0130", "\u03a3\u039f\u03a3", "\u212a", "\u1e9e", "\u0000", "\ud801\udc00", "\ud800", "\udfff"};
        String[] separators = {"/", "\\", "//", "\\\\", "/\\"};
        for (int i = 0; i < 4000; i++) {
            StringBuilder input = new StringBuilder();
            int count = random.nextInt(12);
            for (int j = 0; j < count; j++) {
                input.append(atoms[random.nextInt(atoms.length)]);
                if (random.nextBoolean()) input.append(separators[random.nextInt(separators.length)]);
            }
            cases.add(input.toString());
        }
        cases.add("C:/" + "A/../".repeat(9000) + "END");
        JsonNode first = runOriginal(original, cases, temporary.resolve("first"));
        JsonNode second = runOriginal(original, cases, temporary.resolve("second"));
        assertEquals(first, second, "separate original Python processes must preserve string identities");
        var version = LegacyWindowsPathCanonicalizer.casingVersion();
        assertEquals(reference.path("rite_source_sha256").asText(), first.path("source_sha256").asText());
        assertTrue(first.path("cpython").asText().startsWith("3.13."));
        assertEquals(version.referenceUnicodeData(), first.path("unicode_data").asText());
        assertEquals(version.nlsVersionHex(), first.path("nls").asText());
        assertEquals(version.definedVersionHex(), first.path("defined").asText());
        assertEquals(version.effectiveLocaleHex(), first.path("effective").asText());
        assertEquals(version.customVersionBytesHex(), first.path("custom").asText());
        assertEquals(cases.size(), first.path("outputs").size());
        for (int i = 0; i < cases.size(); i++) {
            assertEquals(first.path("outputs").get(i).asText(),
                    LegacyWindowsPathCanonicalizer.normalize(cases.get(i)), "original producer input " + i);
        }
    }

    private static JsonNode runOriginal(Path original, List<String> cases, Path directory) throws Exception {
        Files.createDirectory(directory);
        Path input = directory.resolve("input.json");
        Path output = directory.resolve("output.json");
        Path error = directory.resolve("error.txt");
        // Force ASCII escapes so isolated UTF-16 surrogates survive the boundary.
        StringBuilder payload = new StringBuilder("[");
        for (int i = 0; i < cases.size(); i++) {
            if (i != 0) payload.append(',');
            payload.append('"');
            for (char value : cases.get(i).toCharArray()) payload.append(String.format(java.util.Locale.ROOT, "\\u%04x", (int)value));
            payload.append('"');
        }
        Files.writeString(input, payload.append(']').toString(), StandardCharsets.US_ASCII);
        Process process = new ProcessBuilder(requiredProperty("xar.legacy.windows.python"), "-I", "-c",
                ORIGINAL_PRODUCER, original.toString()).redirectInput(input.toFile())
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if (!process.waitFor(45, TimeUnit.SECONDS)) {
            process.destroyForcibly();
            throw new AssertionError("original Windows Python timed out");
        }
        assertEquals(0, process.exitValue(), Files.readString(error, StandardCharsets.UTF_8));
        return JSON.readTree(Files.readString(output, StandardCharsets.US_ASCII));
    }

    private static JsonNode reference() throws IOException {
        try (var stream = LegacyWindowsPathCanonicalizerTest.class.getResourceAsStream(RESOURCE)) {
            if (stream == null) throw new IOException("missing original reference corpus");
            return JSON.readTree(stream);
        }
    }

    private static String requiredProperty(String name) {
        String value = System.getProperty(name);
        if (value == null || value.isBlank()) throw new IllegalStateException("required original-producer test property: " + name);
        return value;
    }

    private static void requireWindows() {
        assertTrue(Platform.isWindows(), "Windows NLS differential UNAVAILABLE on this host; no fallback or skipped PASS");
    }
}
