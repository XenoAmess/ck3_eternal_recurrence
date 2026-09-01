package com.xenoamess.kaishek.syntax;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.stream.Stream;

/**
 * Dependency-free parser acceptance smoke test.
 *
 * <p>When invoked from the repository root, the default corpus is
 * {@code mod_zhongguo_style}.  A different root may be supplied as the first
 * argument or with {@code --root PATH}; {@code KAISHEK_CORPUS_ROOT} is also
 * honoured.  A missing default corpus is a skip (so a source-only checkout
 * remains testable); pass {@code --require-corpus} when a caller wants that
 * condition to fail.</p>
 *
 * <p>The test intentionally checks bytes rather than decoded text.  This is
 * the contract that permits a future formatter or semantic pass to preserve
 * comments, BOMs, duplicate keys, and newline style exactly.</p>
 */
public final class ParserCorpusRoundTripSelfTest {
    private static final Set<String> CORPUS_EXTENSIONS = Set.of(".txt", ".gui");

    private ParserCorpusRoundTripSelfTest() { }

    public static void main(String[] args) throws Exception {
        runGuiAndMalformedFixtures();

        Options options = Options.parse(args);
        Path root = options.root();
        if (!Files.isDirectory(root)) {
            if (options.requireCorpus()) {
                throw new AssertionError("corpus root does not exist: " + root.toAbsolutePath());
            }
            System.out.println("ParserCorpusRoundTripSelfTest: SKIP (corpus root absent: "
                    + root.toAbsolutePath() + ")");
            return;
        }

        List<Path> files;
        try (Stream<Path> walk = Files.walk(root)) {
            files = walk.filter(Files::isRegularFile)
                    .filter(ParserCorpusRoundTripSelfTest::isCorpusFile)
                    .sorted(Comparator.comparing(path -> relativePath(root, path)))
                    .toList();
        }
        if (files.isEmpty()) {
            if (options.requireCorpus()) {
                throw new AssertionError("corpus root contains no .txt/.gui files: "
                        + root.toAbsolutePath());
            }
            System.out.println("ParserCorpusRoundTripSelfTest: SKIP (no .txt/.gui files under "
                    + root.toAbsolutePath() + ")");
            return;
        }

        List<String> failures = new ArrayList<>();
        long bytes = 0;
        int parsed = 0;
        int warnings = 0;
        for (Path file : files) {
            byte[] source;
            try {
                source = Files.readAllBytes(file);
            } catch (IOException ex) {
                failures.add(relativePath(root, file) + ": read failed: " + ex);
                continue;
            }
            bytes += source.length;
            try {
                ParseResult result = Parser.parse(source);
                parsed++;
                if (!Arrays.equals(source, result.emit())) {
                    failures.add(relativePath(root, file) + ": emitted bytes differ");
                }
                if (result.hasErrors()) {
                    failures.add(relativePath(root, file) + ": unexpected diagnostics "
                            + result.diagnostics());
                } else {
                    warnings += result.diagnostics().size();
                }
            } catch (RuntimeException ex) {
                failures.add(relativePath(root, file) + ": parser threw " + ex);
            }
        }
        if (!failures.isEmpty()) {
            throw new AssertionError("corpus parser failures (" + failures.size() + "):\n"
                    + String.join("\n", failures));
        }
        System.out.printf(Locale.ROOT,
                "ParserCorpusRoundTripSelfTest: OK files=%d parsed=%d bytes=%d warnings=%d root=%s%n",
                files.size(), parsed, bytes, warnings, root.toAbsolutePath());
    }

    private static void runGuiAndMalformedFixtures() {
        // These three forms occur in the CK3 GUI corpus and exercise the
        // declaration productions that differ from ordinary key = value data.
        String gui = "types ZG361ScoreboardTypes\r\n"
                + "{\r\n"
                + "  type zg361_columns = hbox {\r\n"
                + "    layoutpolicy_horizontal = expanding\r\n"
                + "  }\r\n"
                + "  header_pattern = {\r\n"
                + "    blockoverride \"header_text\" { text = \"title\" }\r\n"
                + "  }\r\n"
                + "}\r\n";
        assertRoundTripAndNoErrors("GUI declaration forms", gui);
        ParseResult guiResult = Parser.parse(gui.getBytes(StandardCharsets.UTF_8));
        check(guiResult.document().entries().size() == 1,
                "GUI declaration fixture lost top-level entry: " + guiResult.document().entries());
        EntryNode types = guiResult.document().entries().get(0);
        check(types.operator() == null, "types header unexpectedly acquired an operator");
        check(types.value() instanceof BlockNode, "types header was not represented as a block");
        BlockNode typesBlock = (BlockNode) types.value();
        check(typesBlock.entries().size() == 2,
                "GUI declaration fixture lost nested entries: " + typesBlock.entries().size());
        EntryNode typed = typesBlock.entries().get(0);
        check(typed.operator() != null && "=".equals(typed.operator().text()),
                "typed GUI declaration did not retain its operator");
        check(typed.value() != null && typed.value().text().contains("hbox"),
                "typed GUI declaration did not retain the widget type");
        EntryNode header = ((BlockNode) typesBlock.entries().get(1).value()).entries().get(0);
        check(header.operator() == null && header.key().text().equals("blockoverride"),
                "blockoverride header was not retained as a no-equals declaration");

        // Each malformed fixture has a deliberately narrow, stable diagnostic
        // contract.  Byte preservation is required even while recovering.
        assertDiagnosticCodes("stray closing brace", "}", Set.of("UNEXPECTED_RBRACE"));
        assertDiagnosticCodes("stray opening brace", "{", Set.of("UNEXPECTED_LBRACE"));
        assertDiagnosticCodes("missing operator", "x", Set.of("MISSING_OPERATOR"));
        assertDiagnosticCodes("unknown no-equals declaration", "foo bar { x = 1 }",
                Set.of("MISSING_OPERATOR", "UNEXPECTED_LBRACE", "UNEXPECTED_RBRACE"));
        assertDiagnosticCodes("unclosed block", "x = { y = 1", Set.of("UNCLOSED_BLOCK"));
        assertDiagnosticCodes("unterminated string", "x = \"unterminated",
                Set.of("UNTERMINATED_STRING", "MALFORMED_VALUE"));
    }

    private static void assertRoundTripAndNoErrors(String label, String text) {
        byte[] source = text.getBytes(StandardCharsets.UTF_8);
        ParseResult result = Parser.parse(source);
        check(Arrays.equals(source, result.emit()), label + " changed source bytes");
        check(!result.hasErrors(), label + " produced diagnostics: " + result.diagnostics());
    }

    private static void assertDiagnosticCodes(String label, String text, Set<String> expected) {
        byte[] source = text.getBytes(StandardCharsets.UTF_8);
        ParseResult result = Parser.parse(source);
        check(Arrays.equals(source, result.emit()), label + " changed source bytes");
        Set<String> actual = new LinkedHashSet<>();
        for (Diagnostic diagnostic : result.diagnostics()) {
            if (diagnostic.severity() == Diagnostic.Severity.ERROR) {
                actual.add(diagnostic.code());
            }
        }
        check(actual.equals(expected), label + " diagnostics expected " + expected + " but got " + actual
                + " (all=" + result.diagnostics() + ")");
    }

    private static boolean isCorpusFile(Path path) {
        return CORPUS_EXTENSIONS.contains(extension(path));
    }

    private static String extension(Path path) {
        String name = path.getFileName().toString().toLowerCase(Locale.ROOT);
        int dot = name.lastIndexOf('.');
        return dot < 0 ? "" : name.substring(dot);
    }

    private static String relativePath(Path root, Path path) {
        return root.relativize(path).toString().replace('\\', '/');
    }

    private static void check(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    private record Options(Path root, boolean requireCorpus) {
        static Options parse(String[] args) {
            Path explicit = null;
            boolean require = false;
            for (int i = 0; i < args.length; i++) {
                String arg = args[i];
                if ("--require-corpus".equals(arg)) {
                    require = true;
                } else if ("--root".equals(arg)) {
                    if (++i >= args.length) {
                        throw new IllegalArgumentException("--root requires a path");
                    }
                    explicit = Path.of(args[i]);
                } else if (arg.startsWith("--root=")) {
                    explicit = Path.of(arg.substring("--root=".length()));
                } else if (arg.startsWith("--")) {
                    throw new IllegalArgumentException("unknown option: " + arg);
                } else if (explicit == null) {
                    explicit = Path.of(arg);
                } else {
                    throw new IllegalArgumentException("unexpected argument: " + arg);
                }
            }
            if (explicit != null) {
                return new Options(explicit, require);
            }
            String fromEnvironment = System.getenv("KAISHEK_CORPUS_ROOT");
            if (fromEnvironment != null && !fromEnvironment.isBlank()) {
                return new Options(Path.of(fromEnvironment), require);
            }
            return new Options(Path.of("mod_zhongguo_style"), require);
        }
    }
}
