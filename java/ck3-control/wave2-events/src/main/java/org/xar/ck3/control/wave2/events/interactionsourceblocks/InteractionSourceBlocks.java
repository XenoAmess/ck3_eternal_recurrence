package org.xar.ck3.control.wave2.events.interactionsourceblocks;

import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Source-text extraction only. Authored effects are never reported as executed effects. */
public final class InteractionSourceBlocks {
    public static final int MAX_SOURCE_BYTES = 2 * 1024 * 1024;
    private InteractionSourceBlocks() { }

    public sealed interface Block permits Found, Absent { }
    public record Found(String text) implements Block { public Found { validText(text); StrictJson.require(!text.isEmpty(), "found block cannot be empty"); } }
    public record Absent() implements Block { }
    public record AuthoredEffects(String canonicalKey, String definition, List<String> category, String onAccept, String onDecline) {
        public AuthoredEffects {
            key(canonicalKey); validText(definition); category = List.copyOf(category); StrictJson.require(category.size() <= 64, "bounded category count required");
            category.forEach(InteractionSourceBlocks::key); if (onAccept != null) { validText(onAccept); } if (onDecline != null) { validText(onDecline); }
        }
        public boolean materialEffectsVerified() { return false; }
        public boolean semanticOptimal() { return false; }
        public boolean nativeAiEquivalent() { return false; }
    }
    public static final class UnterminatedBlockException extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        UnterminatedBlockException() { super("unterminated original interaction definition"); }
    }

    public static Block extract(String text, String key) {
        validText(text); key(key);
        return extractNamed(text, key);
    }

    /** Uses the same original scanner with the existing native event definition-key grammar. */
    public static Block extractEventDefinition(String text, String eventKey) {
        validText(text);
        StrictJson.require(eventKey != null && eventKey.matches("[A-Za-z0-9_]+\\.[0-9]+"), "native event definition key required");
        return extractNamed(text, eventKey);
    }

    private static Block extractNamed(String text, String key) {
        Match match = assignment(text, key, 0, true);
        if (match == null) { return new Absent(); }
        int depth = 1; boolean quoted = false; boolean comment = false; boolean escaped = false;
        for (int index = match.valueStart() + 1; index < text.length(); index++) {
            char current = text.charAt(index);
            if (comment) { if (current == '\r' || current == '\n') { comment = false; } }
            else if (quoted) {
                if (escaped) { escaped = false; }
                else if (current == '\\') { escaped = true; }
                else if (current == '"') { quoted = false; }
            } else if (current == '#') { comment = true; }
            else if (current == '"') { quoted = true; }
            else if (current == '{') { depth++; }
            else if (current == '}') { if (--depth == 0) { return new Found(text.substring(match.start(), index + 1)); } }
        }
        throw new UnterminatedBlockException();
    }

    public static Optional<AuthoredEffects> catalogue(String source, String canonicalKey) {
        Block block = extract(source, canonicalKey);
        if (block instanceof Absent) { return Optional.empty(); }
        String definition = ((Found) block).text();
        List<String> categories = new ArrayList<>(); int from = 0;
        while (from < definition.length()) {
            Match match = assignment(definition, "category", from, false); if (match == null) { break; }
            int end = match.valueStart(); while (end < definition.length() && word(definition.charAt(end))) { end++; }
            StrictJson.require(categories.size() < 64, "bounded category count required"); categories.add(definition.substring(match.valueStart(), end)); from = end;
        }
        return Optional.of(new AuthoredEffects(canonicalKey, definition, categories, optional(extract(definition, "on_accept")), optional(extract(definition, "on_decline"))));
    }

    /** Mirrors the original producer's UTF-8-sig decoding before source extraction. */
    public static Optional<AuthoredEffects> catalogueUtf8(byte[] source, String canonicalKey) {
        StrictJson.require(source != null && source.length <= MAX_SOURCE_BYTES, "bounded original UTF-8 source required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(source)).toString();
            if (text.startsWith("\ufeff")) { text = text.substring(1); }
            return catalogue(text, canonicalKey);
        } catch (CharacterCodingException error) { throw new ContractViolationException("invalid original UTF-8 source", error); }
    }

    /** Equivalent to Python's LF-only multiline anchor and Unicode \s, without rescanning blank-line suffixes. */
    private static Match assignment(String text, String key, int from, boolean brace) {
        int start = from == 0 || text.charAt(from - 1) == '\n' ? from : nextLine(text, from);
        while (start >= 0 && start < text.length()) {
            int cursor = whitespace(text, start);
            if (text.startsWith(key, cursor)) {
                int equals = whitespace(text, cursor + key.length());
                if (equals < text.length() && text.charAt(equals) == '=') {
                    int value = whitespace(text, equals + 1);
                    if (value < text.length() && (brace ? text.charAt(value) == '{' : word(text.charAt(value)))) { return new Match(start, value); }
                }
            }
            start = nextLine(text, cursor);
        }
        return null;
    }
    private static int nextLine(String text, int from) { int newline = text.indexOf('\n', from); return newline < 0 ? -1 : newline + 1; }
    private static int whitespace(String text, int from) { int cursor = from; while (cursor < text.length() && pythonSpace(text.charAt(cursor))) { cursor++; } return cursor; }
    private static boolean pythonSpace(char value) {
        return value >= 0x09 && value <= 0x0d || value >= 0x1c && value <= 0x20 || value == 0x85 || value == 0xa0
                || value == 0x1680 || value >= 0x2000 && value <= 0x200a || value == 0x2028 || value == 0x2029
                || value == 0x202f || value == 0x205f || value == 0x3000;
    }
    private static boolean word(char value) { return value >= 'A' && value <= 'Z' || value >= 'a' && value <= 'z' || value >= '0' && value <= '9' || value == '_'; }
    private record Match(int start, int valueStart) { }

    private static String optional(Block block) { return block instanceof Found found ? found.text() : null; }
    static void key(String value) { StrictJson.require(value != null && value.matches("[A-Za-z0-9_]{1,1024}"), "canonical source key required"); }
    static void validText(String value) {
        Objects.requireNonNull(value, "source text");
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            if (Character.isHighSurrogate(current)) {
                StrictJson.require(index + 1 < value.length() && Character.isLowSurrogate(value.charAt(index + 1)), "unpaired source surrogate"); index++;
            } else { StrictJson.require(!Character.isLowSurrogate(current), "unpaired source surrogate"); }
        }
        StrictJson.require(value.getBytes(StandardCharsets.UTF_8).length <= MAX_SOURCE_BYTES, "bounded original source required");
    }
}
