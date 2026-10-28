package org.xar.ck3.save;

import java.io.IOException;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Objects;

/** Existing SAVE-lexer canonical encoding: exact token lexeme UTF-8, then one ASCII space. */
final class CanonicalTokens {
    private CanonicalTokens() { }

    /** A complete sequence signature; the caller defines its prefix/body domain explicitly. */
    record Signature(long tokens, long bytes, String sha256) {
        Signature {
            if (tokens < 0 || bytes < 0) throw new IllegalArgumentException("nonnegative canonical counters required");
            SaveContracts.digest(sha256);
        }
    }

    /** Incremental hashing only; does not parse, reorder fields, or retain a record body. */
    static final class Accumulator {
        private final MessageDigest digest = FilePins.digest();
        private long tokens;
        private long bytes;
        private boolean finished;
        void add(String token) {
            Objects.requireNonNull(token);
            if (finished) throw new IllegalStateException("canonical digest already finished");
            byte[] utf8 = token.getBytes(StandardCharsets.UTF_8);
            digest.update(utf8); digest.update((byte) ' ');
            tokens = Math.addExact(tokens, 1L);
            bytes = Math.addExact(bytes, utf8.length + 1L);
        }
        Signature finish() {
            if (finished) throw new IllegalStateException("canonical digest already finished");
            finished = true;
            return new Signature(tokens, bytes, HexFormat.of().formatHex(digest.digest()));
        }
    }

    /** Retains historical selected-record domain, including its 'record = ' wrapper. */
    static String selectedRecordHash(Clausewitz.Block ast) {
        Objects.requireNonNull(ast);
        try {
            Clausewitz.Lexer lexer = new Clausewitz.Lexer(new StringReader("record = " + ast.render()),
                    Clausewitz.Syntax.SAVE, 2 * 1024 * 1024);
            Accumulator digest = new Accumulator();
            for (String token; (token = lexer.next()) != null;) digest.add(token);
            return digest.finish().sha256();
        } catch (IOException invalid) { throw new IllegalArgumentException("invalid selected AST", invalid); }
    }

    /** Already canonical producer capture text; no new normalization or parser. */
    static String capturedRecordHash(String canonicalText) {
        return FilePins.sha256(Objects.requireNonNull(canonicalText).getBytes(StandardCharsets.UTF_8));
    }
}
