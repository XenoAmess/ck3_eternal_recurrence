package com.xenoamess.kaishek.ir;

import com.xenoamess.kaishek.profile.GameProfile;
import com.xenoamess.kaishek.profile.InputType;
import com.xenoamess.kaishek.profile.OpcodeDescriptor;
import com.xenoamess.kaishek.profile.OpcodeKind;
import com.xenoamess.kaishek.profile.RandomnessClass;
import com.xenoamess.kaishek.profile.UnsupportedReason;
import com.xenoamess.kaishek.syntax.BlockNode;
import com.xenoamess.kaishek.syntax.CstNode;
import com.xenoamess.kaishek.syntax.Document;
import com.xenoamess.kaishek.syntax.EntryNode;
import com.xenoamess.kaishek.syntax.ParseResult;
import com.xenoamess.kaishek.syntax.Parser;
import com.xenoamess.kaishek.syntax.SyntaxKind;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/**
 * Conservative CST-to-IR lowering for a single exact {@link GameProfile}.
 *
 * <p>This compiler intentionally has a small surface.  It lowers registered
 * key/value entries and preserves source spans, but it does not guess control
 * flow or CK3 semantics.  A root block whose key is not registered is treated
 * as a file/declaration wrapper (the normal Paradox scripted-effect shape);
 * every unknown nested operation, malformed value, and uncertified opcode is
 * represented as an error/unsupported IR result.  Callers must check
 * {@link IrProgram#executable()} before invoking a runtime.</p>
 */
public final class StrictIrCompiler {
    private StrictIrCompiler() { }

    /** Compile using the canonical framework-neutral profile contract. */
    public static IrProgram compile(ParseResult parsed, String sourcePath,
                                    GameProfile profile) {
        Objects.requireNonNull(parsed, "parsed");
        Objects.requireNonNull(profile, "profile");
        if (sourcePath == null || sourcePath.isBlank())
            throw new IllegalArgumentException("sourcePath is blank");

        byte[] source = parsed.source();
        List<IrInstruction> instructions = new ArrayList<>();
        List<Diagnostic> diagnostics = new ArrayList<>();

        // Parser diagnostics are never discarded during lowering.  A parser
        // error also prevents any instruction from being emitted, which keeps
        // a malformed source from partially executing.
        parsed.diagnostics().forEach(d -> diagnostics.add(new Diagnostic(
                mapSeverity(d.severity().name()), d.code(), d.message(),
                SourceSpan.from(sourcePath, source, d.span()), null)));
        if (parsed.hasErrors()) {
            return new IrProgram(profile.id(), profile.gameVersion(), profile.fingerprint(),
                    List.of(), diagnostics);
        }

        CompilerState state = new CompilerState(sourcePath, source, profile,
                instructions, diagnostics);
        state.walk(parsed.document(), 0, "<file>");
        return new IrProgram(profile.id(), profile.gameVersion(), profile.fingerprint(),
                instructions, diagnostics);
    }

    /** Convenience overload for the short immutable profile record. */
    public static IrProgram compile(ParseResult parsed, String sourcePath,
                                    com.xenoamess.kaishek.profile.Profile profile) {
        Objects.requireNonNull(profile, "profile");
        return compile(parsed, sourcePath, profile.asGameProfile());
    }

    /** Parse bytes and lower them in one explicit, still lossless, operation. */
    public static IrProgram compile(byte[] source, String sourcePath,
                                    GameProfile profile) {
        return compile(Parser.parse(source), sourcePath, profile);
    }

    private static DiagnosticSeverity mapSeverity(String name) {
        try {
            return DiagnosticSeverity.valueOf(name);
        } catch (IllegalArgumentException ignored) {
            return DiagnosticSeverity.ERROR;
        }
    }

    private static final class CompilerState {
        private final String sourcePath;
        private final byte[] source;
        private final GameProfile profile;
        private final List<IrInstruction> instructions;
        private final List<Diagnostic> diagnostics;

        private CompilerState(String sourcePath, byte[] source, GameProfile profile,
                              List<IrInstruction> instructions,
                              List<Diagnostic> diagnostics) {
            this.sourcePath = sourcePath;
            this.source = source;
            this.profile = profile;
            this.instructions = instructions;
            this.diagnostics = diagnostics;
        }

        private void walk(CstNode node, int depth, String path) {
            if (node instanceof Document document) {
                walkChildren(document.children(), depth, path);
            } else if (node instanceof BlockNode block) {
                walkChildren(block.children(), depth, path);
            }
        }

        private void walkChildren(List<CstNode> nodes, int depth, String path) {
            for (CstNode node : nodes) {
                if (!(node instanceof EntryNode entry)) {
                    // Trivia and the brace tokens are structural CST data;
                    // a list item or recovery/error node is not.  Ignoring
                    // the latter would turn a malformed/unsupported block
                    // into a successful no-op, which is forbidden by the
                    // strict IR contract.
                    if (node.kind() == SyntaxKind.LIST_ITEM) {
                        error("UNSUPPORTED_LIST_ITEM", "bare list item is not lowered",
                                node.span(), UnsupportedReason.UNSUPPORTED_NATIVE_OPERATION);
                    } else if (node.kind() == SyntaxKind.ERROR) {
                        error("INVALID_INPUT", "syntax recovery node cannot be lowered",
                                node.span(), UnsupportedReason.INVALID_INPUT);
                    }
                    continue;
                }
                String key = entry.key() == null ? "" : entry.key().text().trim();
                String entryPath = path + "." + (key.isEmpty() ? "<blank>" : key);

                // A top-level declaration (`effect_id = { ... }`) is a
                // container, not an executable instruction.  This is the one
                // intentionally permissive structural recovery rule; unknown
                // operations at any nested depth remain hard errors.
                Optional<OpcodeDescriptor> descriptor = profile.opcodes().find(key);
                if (depth == 0 && descriptor.isEmpty() && entry.value() instanceof BlockNode block) {
                    if (entry.operator() == null) {
                        error("INVALID_INPUT", "declaration wrapper has no '=' operator",
                                entry.span(), null);
                    }
                    int instructionCount = instructions.size();
                    int diagnosticCount = diagnostics.size();
                    walkChildren(block.children(), depth + 1, entryPath);
                    // Do not turn an empty/metadata-only unknown root block
                    // into a successful no-op.  Real Paradox declarations
                    // must contain at least one lowered child; otherwise the
                    // caller receives an explicit unsupported result.
                    if (instructions.size() == instructionCount
                            && diagnostics.size() == diagnosticCount) {
                        error("UNSUPPORTED_EMPTY_DECLARATION",
                                "root declaration contains no executable children",
                                entry.span(), UnsupportedReason.UNSUPPORTED_NATIVE_OPERATION);
                    }
                    continue;
                }

                if (entry.operator() == null || entry.value() == null) {
                    error("INVALID_INPUT", "entry must contain an operator and value",
                            entry.span(), UnsupportedReason.INVALID_INPUT);
                    continue;
                }
                if (descriptor.isEmpty()) {
                    error("UNSUPPORTED_UNKNOWN_OPCODE", "unregistered opcode: " + key,
                            entry.key().span(), UnsupportedReason.UNKNOWN_OPCODE);
                    continue;
                }
                lower(entry, descriptor.get(), entryPath);
            }
        }

        private void lower(EntryNode entry, OpcodeDescriptor descriptor, String path) {
            com.xenoamess.kaishek.syntax.SourceSpan syntaxSpan = entry.span();
            com.xenoamess.kaishek.ir.SourceSpan span =
                    com.xenoamess.kaishek.ir.SourceSpan.from(sourcePath, source, syntaxSpan);
            List<IrValue> positional = new ArrayList<>();
            Map<String, IrValue> named = new LinkedHashMap<>();

            if (entry.value() instanceof BlockNode block) {
                Set<String> declared = new HashSet<>(descriptor.parameterNames());
                for (CstNode child : block.children()) {
                    if (!(child instanceof EntryNode parameter)) {
                        if (child.kind() == SyntaxKind.LIST_ITEM) {
                            error("UNSUPPORTED_LIST_ITEM", "bare list item is not lowered",
                                    child.span(), UnsupportedReason.UNSUPPORTED_NATIVE_OPERATION);
                        } else if (child.kind() != SyntaxKind.LBRACE
                                && child.kind() != SyntaxKind.RBRACE
                                && child.kind() != SyntaxKind.BOM
                                && child.kind() != SyntaxKind.COMMENT
                                && child.kind() != SyntaxKind.WHITESPACE
                                && child.kind() != SyntaxKind.NEWLINE) {
                            error("UNSUPPORTED_BLOCK_NODE", "block contains a node that is not a named parameter",
                                    child.span(), UnsupportedReason.UNSUPPORTED_NATIVE_OPERATION);
                        }
                        continue;
                    }
                    String name = parameter.key().text().trim();
                    if (parameter.operator() == null || parameter.value() == null) {
                        error("INVALID_INPUT", "parameter must contain an operator and value",
                                parameter.span(), UnsupportedReason.INVALID_INPUT);
                        continue;
                    }
                    if (!declared.isEmpty() && !declared.contains(name)) {
                        error("INVALID_PARAMETER", "parameter is not declared by opcode "
                                        + descriptor.id() + ": " + name,
                                parameter.key().span(), UnsupportedReason.INVALID_INPUT);
                        continue;
                    }
                    if (named.containsKey(name)) {
                        error("DUPLICATE_PARAMETER", "duplicate parameter: " + name,
                                parameter.key().span(), UnsupportedReason.INVALID_INPUT);
                        continue;
                    }
                    parseValue(parameter.value()).ifPresent(value -> named.put(name, value));
                }
                int count = named.size();
                if (count < descriptor.minParameters() || count > descriptor.maxParameters()) {
                    String range = descriptor.minParameters() + ".."
                            + (descriptor.maxParameters() == Integer.MAX_VALUE
                            ? "*" : descriptor.maxParameters());
                    error("INVALID_PARAMETERS", "opcode " + descriptor.id() + " expects "
                                    + range + " named parameters, got " + count,
                            block.span(), UnsupportedReason.INVALID_INPUT);
                }
                if (descriptor.inputType() != InputType.BLOCK
                        && descriptor.inputType() != InputType.ANY
                        && descriptor.inputType() != InputType.NONE) {
                    error("INVALID_INPUT", "opcode " + descriptor.id()
                                    + " does not accept a block value",
                            block.span(), UnsupportedReason.INVALID_INPUT);
                }
            } else {
                Optional<IrValue> value = parseValue(entry.value());
                value.ifPresent(positional::add);
                if (descriptor.inputType() == InputType.BLOCK
                        || descriptor.inputType() == InputType.LIST
                        || descriptor.inputType() == InputType.SCOPE) {
                    error("INVALID_INPUT", "opcode " + descriptor.id()
                                    + " requires a structured value",
                            entry.value().span(), UnsupportedReason.INVALID_INPUT);
                }
                if (descriptor.parameterNames().size() > 1) {
                    error("INVALID_PARAMETERS", "scalar opcode " + descriptor.id()
                                    + " declares multiple parameters",
                            entry.value().span(), UnsupportedReason.INVALID_INPUT);
                }
            }

            // Do not emit an instruction when its shape is invalid.  For a
            // valid but uncertified descriptor we do emit an explicit
            // non-executable instruction, retaining the source and profile
            // identity for diagnostics and later certification.
            if (hasErrorForSpan(span)) return;
            RandomnessClass randomness = descriptor.certified()
                    ? descriptor.randomness() : RandomnessClass.UNSUPPORTED;
            UnsupportedReason unsupported = descriptor.certified()
                    ? null : UnsupportedReason.NOT_CERTIFIED;
            Set<String> reads = descriptor.readsState() ? Set.of(descriptor.id()) : Set.of();
            Set<String> writes = descriptor.writesState() ? Set.of(descriptor.id()) : Set.of();
            instructions.add(new IrInstruction(descriptor.id(), descriptor.profileVersion(),
                    descriptor.kind(), descriptor.inputType(), descriptor.requiredScope(),
                    positional, named, span, reads, writes, randomness, unsupported));
            if (!descriptor.certified()) {
                error("UNSUPPORTED_NOT_CERTIFIED", "opcode is not certified for profile: "
                                + descriptor.id(), syntaxSpan, UnsupportedReason.NOT_CERTIFIED);
            }
        }

        private boolean hasErrorForSpan(com.xenoamess.kaishek.ir.SourceSpan span) {
            return diagnostics.stream().anyMatch(d -> d.severity() == DiagnosticSeverity.ERROR
                    && d.span().startOffset() >= span.startOffset()
                    && d.span().endOffset() <= span.endOffset());
        }

        private Optional<IrValue> parseValue(CstNode value) {
            if (value instanceof BlockNode) {
                error("INVALID_INPUT", "nested blocks are not scalar IR values",
                        value.span(), UnsupportedReason.INVALID_INPUT);
                return Optional.empty();
            }
            if (value.kind() == SyntaxKind.VALUE || value.kind() == SyntaxKind.LIST_ITEM) {
                // Inline expressions and list items are deliberately not
                // guessed in Phase 0.  A single child is safe to unwrap;
                // multiple children require a future typed expression node.
                if (value.children().size() != 1) {
                    error("UNSUPPORTED_VALUE_EXPRESSION", "compound value is not lowered",
                            value.span(), UnsupportedReason.UNSUPPORTED_NATIVE_OPERATION);
                    return Optional.empty();
                }
                return parseValue(value.children().get(0));
            }
            String raw = value.text().trim();
            try {
                return switch (value.kind()) {
                    case STRING -> Optional.of(new IrValue.LiteralValue(unquote(raw)));
                    case NUMBER -> Optional.of(new IrValue.LiteralValue(parseNumber(raw)));
                    case VARIABLE -> Optional.of(new IrValue.VariableRef(raw));
                    case BARE_VALUE -> Optional.of(new IrValue.LiteralValue(parseBare(raw)));
                    default -> {
                        error("INVALID_INPUT", "unsupported value node: " + value.kind(),
                                value.span(), UnsupportedReason.INVALID_INPUT);
                        yield Optional.empty();
                    }
                };
            } catch (RuntimeException ex) {
                error("INVALID_INPUT", "cannot parse value: " + raw,
                        value.span(), UnsupportedReason.INVALID_INPUT);
                return Optional.empty();
            }
        }

        private static Object parseBare(String raw) {
            return switch (raw.toLowerCase(Locale.ROOT)) {
                case "yes", "true" -> Boolean.TRUE;
                case "no", "false" -> Boolean.FALSE;
                case "none", "null" -> null;
                default -> raw;
            };
        }

        private static Number parseNumber(String raw) {
            if (raw.matches("[+-]?\\d+")) {
                try {
                    return Long.valueOf(raw);
                } catch (NumberFormatException ignored) {
                    // BigDecimal preserves a large integer without silently
                    // wrapping it; runtime handlers may still reject it.
                }
            }
            BigDecimal decimal = new BigDecimal(raw);
            if (!decimal.toString().equalsIgnoreCase("nan")
                    && !decimal.toString().equalsIgnoreCase("infinity")) return decimal;
            throw new IllegalArgumentException("non-finite number");
        }

        private static String unquote(String raw) {
            if (raw.length() < 2 || raw.charAt(0) != '"' || raw.charAt(raw.length() - 1) != '"')
                throw new IllegalArgumentException("unterminated string");
            StringBuilder out = new StringBuilder(raw.length() - 2);
            boolean escaped = false;
            for (int i = 1; i < raw.length() - 1; i++) {
                char c = raw.charAt(i);
                if (escaped) {
                    out.append(switch (c) {
                        case 'n' -> '\n';
                        case 'r' -> '\r';
                        case 't' -> '\t';
                        case '"' -> '"';
                        case '\\' -> '\\';
                        default -> throw new IllegalArgumentException("unknown escape: " + c);
                    });
                    escaped = false;
                } else if (c == '\\') {
                    escaped = true;
                } else {
                    out.append(c);
                }
            }
            if (escaped) throw new IllegalArgumentException("trailing escape");
            return out.toString();
        }

        private void error(String code, String message,
                           com.xenoamess.kaishek.syntax.SourceSpan span,
                           UnsupportedReason reason) {
            diagnostics.add(new Diagnostic(DiagnosticSeverity.ERROR, code, message,
                    com.xenoamess.kaishek.ir.SourceSpan.from(sourcePath, source, span), reason));
        }
    }
}
