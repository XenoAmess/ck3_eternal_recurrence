package org.xar.ck3.control.build;

import java.nio.file.Files;
import java.nio.file.Path;

/** Actual compiled test child for the production owned-Job/custody consumer. No build or Game authority. */
public final class ControlCiUtf8JobFixture {
    private ControlCiUtf8JobFixture() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3 || !(arguments[0].equals("PASS") || arguments[0].equals("FAIL42")))
            throw new IllegalArgumentException("Exact software fixture arguments required");
        Files.writeString(Path.of(arguments[1]), arguments[2], java.nio.charset.StandardCharsets.UTF_8);
        if (arguments[0].equals("FAIL42")) System.exit(42);
    }
}
