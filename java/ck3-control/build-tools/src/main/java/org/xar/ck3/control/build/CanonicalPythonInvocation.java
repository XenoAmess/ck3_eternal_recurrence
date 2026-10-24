package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/** Bounded argv interpretation for the original canonical workflow, before a shared explicit fixture bootstrap. */
public final class CanonicalPythonInvocation {
    private CanonicalPythonInvocation() { }
    public enum Mode { MODULE, INLINE_SOURCE, SCRIPT_FILE }
    public record Invocation(String originalCommand, List<String> interpreterArguments, Mode mode,
            String moduleName, String inlineSource, String relativeScript, List<String> arguments) {
        public Invocation {
            interpreterArguments = List.copyOf(interpreterArguments); arguments = List.copyOf(arguments);
            if (originalCommand == null || !originalCommand.startsWith("python ") || originalCommand.contains("\n") || originalCommand.contains("\r")
                    || !(interpreterArguments.equals(List.of("-B")) || interpreterArguments.equals(List.of("-B", "-X", "utf8"))) || mode == null)
                throw new IllegalArgumentException("Original finite canonical interpreter invocation required");
            switch (mode) {
                case MODULE -> {
                    if (moduleName == null || !moduleName.matches("[A-Za-z_][A-Za-z0-9_.]*") || inlineSource != null || relativeScript != null)
                        throw new IllegalArgumentException("Exact module invocation required");
                }
                case INLINE_SOURCE -> {
                    if (inlineSource == null || inlineSource.isBlank() || moduleName != null || relativeScript != null)
                        throw new IllegalArgumentException("Exact original inline body required");
                }
                case SCRIPT_FILE -> {
                    if (relativeScript == null || inlineSource != null || moduleName != null || Path.of(relativeScript).isAbsolute()
                            || !Path.of(relativeScript).equals(Path.of(relativeScript).normalize()) || relativeScript.contains("..")
                            || !(relativeScript.startsWith("tools/") || relativeScript.startsWith("ck3_autonomous_player/")) || !relativeScript.endsWith(".py"))
                        throw new IllegalArgumentException("Exact canonical relative script source required");
                }
            }
        }
    }
    public static Invocation parse(String command, Path runnerTemporary) throws IOException {
        if (runnerTemporary == null || !runnerTemporary.isAbsolute()) throw new IOException("Owned absolute runner temporary root required");
        List<String> tokens = words(command); if (tokens.size() < 3 || !tokens.getFirst().equals("python")) throw new IOException("Exact canonical Python command required");
        int cursor = 1; List<String> flags = new ArrayList<>();
        if (tokens.get(cursor).equals("-B")) { flags.add(tokens.get(cursor)); cursor++; }
        if (cursor < tokens.size() && tokens.get(cursor).equals("-X")) {
            if (++cursor >= tokens.size() || !tokens.get(cursor).equals("utf8")) throw new IOException("Only the original utf8 interpreter option is declared");
            flags.add("-X"); flags.add(tokens.get(cursor++));
        }
        if (cursor >= tokens.size()) throw new IOException("Original Python execution entry missing");
        Mode mode; String module = null, inline = null, script = null; String entry = tokens.get(cursor++);
        if (entry.equals("-m") || entry.equals("-c")) {
            if (cursor >= tokens.size()) throw new IOException("Original Python execution body missing");
            if (entry.equals("-m")) { mode = Mode.MODULE; module = tokens.get(cursor++); }
            else { mode = Mode.INLINE_SOURCE; inline = tokens.get(cursor++); }
        } else { mode = Mode.SCRIPT_FILE; script = entry; }
        List<String> arguments = new ArrayList<>();
        for (String value : tokens.subList(cursor, tokens.size())) {
            String expanded = value.replace("%RUNNER_TEMP%", runnerTemporary.toString());
            if (expanded.matches(".*%[A-Za-z_][A-Za-z0-9_]*%.*")) throw new IOException("Undeclared CMD environment expansion in original arguments");
            arguments.add(expanded);
        }
        try { return new Invocation(command, flags, mode, module, inline, script, arguments); }
        catch (IllegalArgumentException invalid) { throw new IOException("Unsupported canonical invocation", invalid); }
    }
    /** The current fixed step has ordinary words and complete double-quoted Python bodies; no CMD programs are interpreted here. */
    static List<String> words(String command) throws IOException {
        if (command == null || command.length() > 16384 || command.contains("\n") || command.contains("\r")) throw new IOException("One bounded original command line required");
        List<String> words = new ArrayList<>(); StringBuilder current = new StringBuilder(); boolean quoted = false, present = false;
        for (int index = 0; index < command.length(); index++) {
            char value = command.charAt(index);
            if (value == '"') { quoted = !quoted; present = true; continue; }
            if (!quoted && Character.isWhitespace(value)) {
                if (present) { words.add(current.toString()); current.setLength(0); present = false; }
            } else {
                if (!quoted && "&|<>^".indexOf(value) >= 0) throw new IOException("Unquoted shell operation is outside the fixed original Python argv subset");
                if (value == '\\' && index + 1 < command.length() && command.charAt(index + 1) == '"')
                    throw new IOException("Escaped quotes need an explicit original workflow contract, never guessed decoding");
                current.append(value); present = true;
            }
        }
        if (quoted) throw new IOException("Original command quote is incomplete"); if (present) words.add(current.toString());
        return List.copyOf(words);
    }
}
