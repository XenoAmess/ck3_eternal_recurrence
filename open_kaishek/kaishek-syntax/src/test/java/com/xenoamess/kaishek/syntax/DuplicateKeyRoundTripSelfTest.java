package com.xenoamess.kaishek.syntax;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;

/** Regression fixture: duplicate keys are source data, never a map overwrite. */
public final class DuplicateKeyRoundTripSelfTest {
    private DuplicateKeyRoundTripSelfTest() { }

    public static void main(String[] args) {
        byte[] input = ("# duplicate-key fixture\r\n" +
                "case = {\r\n" +
                "  reward = 1\r\n" +
                "  reward = 2\r\n" +
                "  reward = { gold = 3 gold = 4 }\r\n" +
                "}\r\n").getBytes(StandardCharsets.UTF_8);
        ParseResult parsed = Parser.parse(input);
        check(!parsed.hasErrors(), "duplicate-key fixture produced diagnostics: " + parsed.diagnostics());
        check(Arrays.equals(input, parsed.emit()), "duplicate-key source was not byte-preserved");
        check(parsed.document().entries().size() == 1, "top-level entry count changed");
        check(parsed.document().children().stream().filter(n -> n.kind() == SyntaxKind.ENTRY).count() == 1,
                "entry structure was collapsed");
        BlockNode block = (BlockNode) parsed.document().entries().get(0).value();
        check(block.entries().size() == 3, "duplicate nested keys were overwritten");
        check(((BlockNode) block.entries().get(2).value()).entries().size() == 2,
                "duplicate keys in nested block were overwritten");
        System.out.println("DuplicateKeyRoundTripSelfTest: OK");
    }

    private static void check(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }
}
