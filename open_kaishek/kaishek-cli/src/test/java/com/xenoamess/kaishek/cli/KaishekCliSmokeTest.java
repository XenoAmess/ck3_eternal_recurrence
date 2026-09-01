package com.xenoamess.kaishek.cli;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** No framework dependency: invoke this {@code main} as an explicit CLI smoke test. */
public final class KaishekCliSmokeTest {
  public static void main(String[] args) {
    ByteArrayOutputStream b = new ByteArrayOutputStream();
    int ok = KaishekCli.run(new String[]{"parse"}, new PrintStream(b), System.err);
    check(ok == 0 && b.toString(StandardCharsets.UTF_8).contains("\"status\":\"PARSED\""), b);
    b.reset();
    int unsupported = KaishekCli.run(new String[]{"profile", "--id", "future"}, new PrintStream(b), System.err);
    check(unsupported == 4 && b.toString(StandardCharsets.UTF_8).contains("UNSUPPORTED"), b);

    // Diagnostic offsets are numeric JSON fields (and byte offsets), not
    // quoted decimal strings.
    b.reset();
    int syntaxError = KaishekCli.run(new String[]{"parse", "x"}, new PrintStream(b), System.err);
    String syntaxJson = b.toString(StandardCharsets.UTF_8);
    check(syntaxError == 1 && syntaxJson.contains("\"offset\":0")
        && !syntaxJson.contains("\"offset\":\"0\""), syntaxJson);

    b.reset();
    int inlineSyntaxError = KaishekCli.run(new String[]{"validate", "x"},
        new PrintStream(b), System.err);
    // An inline syntax error must not be reported as an unsupported semantic
    // layer merely because no file path was supplied.
    check(inlineSyntaxError == 1 && b.toString(StandardCharsets.UTF_8)
        .contains("\"status\":\"INVALID\""), b);

    // A semantic diagnostic must make validate fail.  Put the fixture under a
    // recognised directory so the static CK3 profile is actually selected,
    // and put --profile before --file to exercise option-order handling.
    Path root = null;
    try {
      root = Files.createTempDirectory("kaishek-cli-smoke-");
      Path effects = Files.createDirectories(root.resolve("common/scripted_effects"));
      Path invalid = effects.resolve("invalid.txt");
      Files.writeString(invalid, "mystery_opcode = yes\n", StandardCharsets.UTF_8);
      b.reset();
      int semanticError = KaishekCli.run(new String[]{"validate", "--profile", "ck3-1.19.0.6",
          "--file", invalid.toString()}, new PrintStream(b), System.err);
      String semanticJson = b.toString(StandardCharsets.UTF_8);
      check(semanticError == 1 && semanticJson.contains("\"status\":\"INVALID\"")
          && semanticJson.contains("\"semanticDiagnostics\":1"), semanticJson);

      b.reset();
      int missing = KaishekCli.run(new String[]{"parse", "--file"}, new PrintStream(b), System.err);
      check(missing == 2 && b.toString(StandardCharsets.UTF_8).contains("\"status\":\"ERROR\""), b);

      b.reset();
      int trailingUnknown = KaishekCli.run(new String[]{"parse", "x = 1", "--unknown"},
          new PrintStream(b), System.err);
      check(trailingUnknown == 2 && b.toString(StandardCharsets.UTF_8).contains("\"status\":\"ERROR\""), b);
    } catch (IOException ex) {
      throw new AssertionError("CLI smoke fixture setup failed", ex);
    } finally {
      if (root != null) {
        try (var walk = Files.walk(root)) {
          walk.sorted(java.util.Comparator.reverseOrder()).forEach(path -> {
            try { Files.deleteIfExists(path); }
            catch (IOException ex) { throw new UncheckedIOException(ex); }
          });
        } catch (IOException | UncheckedIOException ex) {
          throw new AssertionError("CLI smoke fixture cleanup failed", ex);
        }
      }
    }
  }

  private static void check(boolean condition, Object detail) {
    if (!condition) throw new AssertionError(String.valueOf(detail));
  }
}
