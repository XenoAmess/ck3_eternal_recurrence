package com.xenoamess.kaishek.zg361;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Objects;

/**
 * Generator for the tiny, reviewable 014 appeal-case script used by the
 * offline vertical-slice test.  The returned bytes include the UTF-8 BOM so
 * the fixture follows the same source-file contract as the mod corpus.
 */
public final class Synthetic361Fixture {
    public static final String SOURCE_PATH =
            "common/scripted_effects/zg361_synthetic_014.txt";
    private static final byte[] BOM = {(byte) 0xef, (byte) 0xbb, (byte) 0xbf};

    private Synthetic361Fixture() { }

    /** Render a complete generated `.txt` source file, byte-for-byte stable. */
    public static byte[] render() {
        String body = "# synthetic-only 361 mechanism 014 vertical slice\n"
                + "zg361_synthetic_014 = {\n"
                + "    " + Synthetic361Profile.OPEN_CASE + " = {\n"
                + "        case_id = \"case-014\"\n"
                + "    }\n"
                + "    " + Synthetic361Profile.CHOOSE + " = {\n"
                + "        choice = \"a\"\n"
                + "    }\n"
                + "    " + Synthetic361Profile.CLOSE_CASE + " = { }\n"
                + "}\n";
        byte[] encoded = body.getBytes(StandardCharsets.UTF_8);
        byte[] result = new byte[BOM.length + encoded.length];
        System.arraycopy(BOM, 0, result, 0, BOM.length);
        System.arraycopy(encoded, 0, result, BOM.length, encoded.length);
        return result;
    }

    /** Materialize the generated source as a file for file-boundary tests. */
    public static Path writeTo(Path directory) throws java.io.IOException {
        Objects.requireNonNull(directory, "directory");
        Files.createDirectories(directory);
        Path file = directory.resolve("zg361_synthetic_014.txt");
        Files.write(file, render());
        return file;
    }
}
