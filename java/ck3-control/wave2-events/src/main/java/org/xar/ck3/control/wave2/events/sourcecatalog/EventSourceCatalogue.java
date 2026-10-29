package org.xar.ck3.control.wave2.events.sourcecatalog;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.TreeSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.interactionsourceblocks.InteractionSourceBlocks;

/** Finite source-text catalogue only: direct child blocks/scalars and authored option statements. */
public final class EventSourceCatalogue {
    private static final String SPACE = "[\\x{0009}-\\x{000d}\\x{001c}-\\x{0020}\\x{0085}\\x{00a0}\\x{1680}\\x{2000}-\\x{200a}\\x{2028}\\x{2029}\\x{202f}\\x{205f}\\x{3000}]";
    private static final Pattern CONDITIONAL_NAME = Pattern.compile("(?:text|desc)" + SPACE + "*=" + SPACE + "*(\"[^\"\\r\\n]+\"|[A-Za-z0-9_.]+)");
    private static final Pattern EFFECT = Pattern.compile("^" + SPACE + "*((?:(?:add_|remove_|set_|change_|trigger_|start_|end_|save_)[A-Za-z0-9_]+)|(?:[A-Za-z0-9_]+_effect))"
        + SPACE + "*=" + SPACE + "*([^\\r\\n]+)", Pattern.MULTILINE | Pattern.UNIX_LINES);
    private EventSourceCatalogue() { }

    public static final class UnbalancedSourceException extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        public UnbalancedSourceException() { super("unbalanced event source"); }
    }
    public static final class UnterminatedChildBlockException extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        public UnterminatedChildBlockException() { super("unterminated event source block"); }
    }
    public record DirectEffectStatement(String effect, String sourceValue) {
        public DirectEffectStatement { Objects.requireNonNull(effect); Objects.requireNonNull(sourceValue); }
    }
    public record Option(int nativeOptionIndex, List<String> sourceNameKeys, List<String> conditionalNameSource,
                          String sourceOption, String trigger, List<DirectEffectStatement> directEffectStatements) {
        public Option {
            StrictJson.require(nativeOptionIndex >= 0, "native option index");
            sourceNameKeys = List.copyOf(sourceNameKeys); conditionalNameSource = List.copyOf(conditionalNameSource);
            Objects.requireNonNull(sourceOption); directEffectStatements = List.copyOf(directEffectStatements);
        }
    }
    public record Catalogue(List<String> sourceEventTypes, List<Option> options, String immediate, String after) {
        public Catalogue { sourceEventTypes = List.copyOf(sourceEventTypes); options = List.copyOf(options); }
        public boolean materialEffectsVerified() { return false; }
        public boolean registryContractAccepted() { return false; }
    }
    private record Token(String value, int start, int end) { }

    /** The exact _blocks behavior: every matching direct child at token depth one, including same-line children. */
    public static List<String> blocks(String text, String wanted) {
        Objects.requireNonNull(text, "text"); Objects.requireNonNull(wanted, "wanted");
        List<Token> tokens = tokens(text);
        int depth = 0;
        List<String> found = new ArrayList<>();
        for (int index = 0; index < tokens.size(); index++) {
            Token token = tokens.get(index);
            if (token.value().equals("{")) depth++;
            else if (token.value().equals("}")) {
                depth--; if (depth < 0) throw new UnbalancedSourceException();
            } else if (depth == 1 && token.value().equals(wanted) && index + 2 < tokens.size()
                    && tokens.get(index + 1).value().equals("=") && tokens.get(index + 2).value().equals("{")) {
                int level = 1; boolean closed = false;
                for (int closing = index + 3; closing < tokens.size(); closing++) {
                    if (tokens.get(closing).value().equals("{")) level++;
                    if (tokens.get(closing).value().equals("}")) level--;
                    if (level == 0) { found.add(text.substring(token.start(), tokens.get(closing).end())); closed = true; break; }
                }
                if (!closed) throw new UnterminatedChildBlockException();
            }
        }
        if (depth != 0) throw new UnbalancedSourceException();
        return List.copyOf(found);
    }

    /** Like the original _scalars, this helper alone does not reject unbalanced braces. */
    public static List<String> scalars(String text, String wanted) {
        Objects.requireNonNull(text, "text"); Objects.requireNonNull(wanted, "wanted");
        List<Token> tokens = tokens(text);
        int depth = 0;
        List<String> found = new ArrayList<>();
        for (int index = 0; index < tokens.size(); index++) {
            String value = tokens.get(index).value();
            if (value.equals("{")) depth++;
            else if (value.equals("}")) depth--;
            else if (depth == 1 && value.equals(wanted) && index + 2 < tokens.size()
                    && tokens.get(index + 1).value().equals("=") && !tokens.get(index + 2).value().equals("{")) {
                found.add(stripQuotes(tokens.get(index + 2).value()));
            }
        }
        return List.copyOf(found);
    }

    /** Pure post-load part of _source; file/EXE/index/hash admission stays with the original loader. */
    public static Catalogue catalogue(String definition, int nativeOptionCount) {
        Objects.requireNonNull(definition, "definition");
        StrictJson.require(nativeOptionCount > 0, "positive native option count");
        List<String> authored = blocks(definition, "option");
        if (authored.size() != nativeOptionCount) throw new IllegalArgumentException("source/native option-count mapping not established");
        List<Option> options = new ArrayList<>();
        for (int index = 0; index < authored.size(); index++) {
            String option = authored.get(index);
            TreeSet<String> names = new TreeSet<>(CODE_POINT_ORDER);
            names.addAll(scalars(option, "name"));
            List<String> nameBlocks = blocks(option, "name");
            for (String block : nameBlocks) {
                Matcher matcher = CONDITIONAL_NAME.matcher(block);
                while (matcher.find()) {
                    if (matcher.start() == 0 || !pythonWord(block.codePointBefore(matcher.start()))) names.add(stripQuotes(matcher.group(1)));
                }
            }
            if (names.isEmpty()) throw new IllegalArgumentException("source option name identity cannot be parsed");
            List<DirectEffectStatement> effects = new ArrayList<>();
            Matcher matcher = EFFECT.matcher(option);
            while (matcher.find()) effects.add(new DirectEffectStatement(matcher.group(1), matcher.group(2)));
            options.add(new Option(index, List.copyOf(names), nameBlocks, option, namedBlock(option, "trigger"), effects));
        }
        return new Catalogue(scalars(definition, "type"), options, namedBlock(definition, "immediate"), namedBlock(definition, "after"));
    }

    private static String namedBlock(String text, String key) {
        InteractionSourceBlocks.Block block = InteractionSourceBlocks.extract(text, key);
        return block instanceof InteractionSourceBlocks.Found found ? found.text() : null;
    }
    private static List<Token> tokens(String text) {
        List<Token> result = new ArrayList<>();
        for (int cursor = 0; cursor < text.length();) {
            char current = text.charAt(cursor);
            if (pythonSpace(current)) { cursor++; continue; }
            if (current == '#') {
                while (cursor < text.length() && text.charAt(cursor) != '\r' && text.charAt(cursor) != '\n') cursor++;
                continue;
            }
            int start = cursor;
            if (current == '"') {
                int end = quotedEnd(text, cursor);
                cursor = end >= 0 ? end : cursor + 1;
            } else if (current == '=' || current == '{' || current == '}') cursor++;
            else {
                do { cursor++; } while (cursor < text.length() && !separator(text.charAt(cursor)));
            }
            result.add(new Token(text.substring(start, cursor), start, cursor));
        }
        return result;
    }
    /** Failed quoted regex matches fall back to a single quote token, exactly as the original tokenizer. */
    private static int quotedEnd(String text, int start) {
        for (int cursor = start + 1; cursor < text.length(); cursor++) {
            char current = text.charAt(cursor);
            if (current == '"') return cursor + 1;
            if (current == '\\') {
                if (cursor + 1 >= text.length() || text.charAt(cursor + 1) == '\n') return -1;
                cursor++;
            }
        }
        return -1;
    }
    private static boolean separator(char value) { return pythonSpace(value) || value == '=' || value == '{' || value == '}' || value == '#' || value == '"'; }
    private static boolean pythonWord(int value) {
        int type = Character.getType(value);
        return value == '_' || Character.isLetterOrDigit(value) || type == Character.LETTER_NUMBER || type == Character.OTHER_NUMBER;
    }
    private static boolean pythonSpace(char value) {
        return value >= 0x09 && value <= 0x0d || value >= 0x1c && value <= 0x20 || value == 0x85 || value == 0xa0
            || value == 0x1680 || value >= 0x2000 && value <= 0x200a || value == 0x2028 || value == 0x2029
            || value == 0x202f || value == 0x205f || value == 0x3000;
    }
    private static String stripQuotes(String value) {
        int start = 0, end = value.length();
        while (start < end && value.charAt(start) == '"') start++;
        while (end > start && value.charAt(end - 1) == '"') end--;
        return value.substring(start, end);
    }
    private static final Comparator<String> CODE_POINT_ORDER = (left, right) -> {
        int first = 0, second = 0;
        while (first < left.length() && second < right.length()) {
            int a = left.codePointAt(first), b = right.codePointAt(second);
            if (a != b) return Integer.compare(a, b);
            first += Character.charCount(a); second += Character.charCount(b);
        }
        return Integer.compare(left.length() - first, right.length() - second);
    };
}
