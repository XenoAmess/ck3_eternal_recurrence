package org.xar.ck3.markets.saveaudit;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonMappingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.deser.std.StdDeserializer;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.markets.saveaudit.FinancialSnapshot.*;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.SaveContracts;

/** Interpretation of the observed save variable envelope, not a second Clausewitz parser. */
public final class FinancialProjector {
    private FinancialProjector() { }
    public enum NumberIdentityEncoding { identityRequired, omittedZero }
    /** Scaling is an explicit hypothesis until verified against a real 1.21 financial physical save. */
    @JsonDeserialize(using = LayoutDeserializer.class)
    public record LayoutHypothesis(String gameVersion, String saveFormat, BigInteger numericScale,
                                   String storyReferenceType, String characterReferenceType,
                                   NumberIdentityEncoding numberIdentityEncoding) {
        /** Existing Java callers and the positional CLI retain strict identity semantics. */
        public LayoutHypothesis(String gameVersion, String saveFormat, BigInteger numericScale,
                                String storyReferenceType, String characterReferenceType) {
            this(gameVersion, saveFormat, numericScale, storyReferenceType, characterReferenceType,
                    NumberIdentityEncoding.identityRequired);
        }
        public LayoutHypothesis {
            if (gameVersion == null || gameVersion.isBlank() || saveFormat == null || saveFormat.isBlank()
                    || numericScale == null || numericScale.signum() <= 0
                    || storyReferenceType == null || storyReferenceType.isBlank()
                    || characterReferenceType == null || characterReferenceType.isBlank() || numberIdentityEncoding == null)
                throw new IllegalArgumentException("explicit layout hypothesis required");
            if (numberIdentityEncoding == NumberIdentityEncoding.omittedZero
                    && !(gameVersion.equals("1.21.0") && saveFormat.equals("19") && numericScale.equals(BigInteger.valueOf(100000))))
                throw new IllegalArgumentException("omittedZero is observed only for explicit 1.21.0 / format 19 / scale 100000");
        }
        /** Strict legacy five-field or explicit six-field JSON; no shared mapper guards are relaxed. */
        public static LayoutHypothesis fromJson(JsonNode node) {
            if (node == null || !node.isObject()) throw new IllegalArgumentException("layout object required");
            Set<String> allowed = Set.of("gameVersion", "saveFormat", "numericScale", "storyReferenceType",
                    "characterReferenceType", "numberIdentityEncoding");
            node.fieldNames().forEachRemaining(name -> {
                if (!allowed.contains(name)) throw new IllegalArgumentException("unknown layout field: " + name);
            });
            JsonNode scale = node.get("numericScale");
            if (scale == null || !scale.isIntegralNumber()) throw new IllegalArgumentException("numericScale must be an integer");
            NumberIdentityEncoding encoding = node.has("numberIdentityEncoding")
                    ? NumberIdentityEncoding.valueOf(text(node, "numberIdentityEncoding")) : NumberIdentityEncoding.identityRequired;
            return new LayoutHypothesis(text(node, "gameVersion"), text(node, "saveFormat"), scale.bigIntegerValue(),
                    text(node, "storyReferenceType"), text(node, "characterReferenceType"), encoding);
        }
        private static String text(JsonNode node, String name) {
            JsonNode value = node.get(name);
            if (value == null || !value.isTextual()) throw new IllegalArgumentException("layout field must be text: " + name);
            return value.textValue();
        }
    }
    /** Local codec prevents the record's implicit creator from making the optional sixth field mandatory. */
    public static final class LayoutDeserializer extends StdDeserializer<LayoutHypothesis> {
        private static final long serialVersionUID = 1L;
        public LayoutDeserializer() { super(LayoutHypothesis.class); }
        @Override public LayoutHypothesis deserialize(JsonParser parser, DeserializationContext context) throws IOException {
            // Read this nested value, not a new root with FAIL_ON_TRAILING_TOKENS.
            // SaveJson retains the complete request's duplicate/trailing-token guards.
            JsonNode node = context.readTree(parser);
            try { return LayoutHypothesis.fromJson(node); }
            catch (IllegalArgumentException malformed) { throw JsonMappingException.from(parser, malformed.getMessage(), malformed); }
        }
    }
    public static FinancialSnapshot project(FinancialSaveReader.Readback input, LayoutHypothesis layout) {
        List<Issue> issues = new ArrayList<>();
        issues.add(new Issue(Severity.UNQUALIFIED, "save", "layout",
                "External candidate only; no financial 1.21 source-layout qualification or live funds certification."));
        SaveContracts.Scope metadata = input.projection().scopes().stream()
                .filter(scope -> scope.kind() == SaveContracts.ScopeKind.METADATA).findFirst().orElseThrow();
        String version = atom(metadata.ast(), "version").map(FinancialProjector::unquote).orElse("");
        String format = atom(metadata.ast(), "save_game_version").orElse("");
        String date = atom(metadata.ast(), "meta_date").orElse("");
        if (!layout.gameVersion().equals(version) || !layout.saveFormat().equals(format))
            issues.add(new Issue(Severity.INCOMPLETE, "save", "metadata", "Version/format do not match the explicit layout hypothesis."));
        if (date.isEmpty()) issues.add(new Issue(Severity.INCOMPLETE, "save", "meta_date", "Missing metadata date."));
        List<Story> result = input.financialStories();
        issues.addAll(input.financialIssues());
        if (result.isEmpty()) issues.add(new Issue(Severity.INCOMPLETE, "save", "finance", "No recognized financial stories; an empty census is not a financial pass."));
        verifyGlobalExchange(input, layout, result, issues);
        return new FinancialSnapshot(input.machineId(), input.save().sha256(), version, format, date, result, issues);
    }
    public record RecordProjection(Optional<Story> story, List<Issue> issues) {
        public RecordProjection { issues = List.copyOf(issues); }
    }
    static RecordProjection projectRecord(SaveContracts.NativeId nativeId, Clausewitz.Block body, LayoutHypothesis layout) {
            List<Issue> issues = new ArrayList<>();
            Optional<String> wireType = atom(body, "story_cycle").map(FinancialProjector::unquote);
            Optional<Type> type = wireType.flatMap(Type::fromWire);
            if (type.isEmpty()) {
                if (wireType.orElse("").startsWith("xfm_"))
                    issues.add(new Issue(Severity.INCOMPLETE, nativeId.value(), "story_cycle", "Unrecognized finance story type."));
                return new RecordProjection(Optional.empty(), issues);
            }
            String identity = type.get() + ":native-" + nativeId.value();
            Map<String, Clausewitz.Block> variables = variables(body, identity, issues);
            EnumMap<NumberField, BigInteger> numbers = new EnumMap<>(NumberField.class);
            EnumMap<ReferenceField, Reference> references = new EnumMap<>(ReferenceField.class);
            for (NumberField field : NumberField.values()) {
                Clausewitz.Block data = variables.get(field.wire());
                if (data == null) continue;
                try {
                    if (!atom(data, "type").orElse("").equals("value")) throw new IllegalArgumentException("Expected type=value.");
                    String lexical = numericIdentity(data, layout);
                    if (!lexical.matches("-?(0|[1-9][0-9]*)")) throw new IllegalArgumentException("Canonical integer identity required.");
                    BigInteger[] division = new BigInteger(lexical).divideAndRemainder(layout.numericScale());
                    if (division[1].signum() != 0) throw new IllegalArgumentException("Fractional cent/unit/day/ID after exact scaling.");
                    numbers.put(field, division[0]);
                } catch (IllegalArgumentException error) { issues.add(new Issue(Severity.INCOMPLETE, identity, field.wire(), error.getMessage())); }
            }
            for (ReferenceField field : ReferenceField.values()) {
                Clausewitz.Block data = variables.get(field.wire());
                if (data == null) continue;
                try {
                    String kind = atom(data, "type").orElseThrow(() -> new IllegalArgumentException("Missing scope type."));
                    String expected = field.characterReference() ? layout.characterReferenceType() : layout.storyReferenceType();
                    if (!kind.equals(expected)) throw new IllegalArgumentException("Unrecognized reference type " + kind + "; expected explicit hypothesis " + expected + '.');
                    String lexical = atom(data, "identity").orElseThrow(() -> new IllegalArgumentException("Missing scope identity."));
                    references.put(field, new Reference(kind, new SaveContracts.NativeId(lexical)));
                } catch (IllegalArgumentException error) { issues.add(new Issue(Severity.INCOMPLETE, identity, field.wire(), error.getMessage())); }
            }
            Optional<SaveContracts.NativeId> permanent = Optional.empty();
            if (type.get().permanentField().isPresent()) {
                BigInteger number = numbers.get(type.get().permanentField().orElseThrow());
                if (number != null) {
                    try {
                        if (number.signum() <= 0) throw new IllegalArgumentException("Positive permanent ID required.");
                        permanent = Optional.of(new SaveContracts.NativeId(number.toString()));
                    } catch (IllegalArgumentException error) { issues.add(new Issue(Severity.VIOLATION, identity, "permanent_id", error.getMessage())); }
                } else issues.add(new Issue(Severity.INCOMPLETE, identity, "permanent_id", "Missing permanent financial ID."));
            }
            return new RecordProjection(Optional.of(new Story(type.get(), nativeId, permanent, numbers, references)), issues);
    }

    private static String numericIdentity(Clausewitz.Block data, LayoutHypothesis layout) {
        // atom() rejects duplicates, blocks and non-assignment identities before any omission policy is considered.
        Optional<String> identity = atom(data, "identity");
        if (identity.isPresent()) return identity.get();
        if (layout.numberIdentityEncoding() == NumberIdentityEncoding.omittedZero && data.entries().size() == 1)
            return "0"; // Caller already required the sole assigned atom to be type=value.
        throw new IllegalArgumentException("Missing numeric identity; strict encoding or noncanonical omitted-zero data.");
    }

    private static void verifyGlobalExchange(FinancialSaveReader.Readback input, LayoutHypothesis layout,
                                            List<Story> stories, List<Issue> issues) {
        // Globals are the same variables envelope but without a parent "variables" block.
        Map<String, Clausewitz.Block> globals = variableData(projection(input, "globals"), "globals", issues);
        Clausewitz.Block exchange = globals.get("xfm_exchange");
        if (exchange == null) { issues.add(new Issue(Severity.INCOMPLETE, "globals", "xfm_exchange", "Missing singleton pointer.")); return; }
        try {
            if (!atom(exchange, "type").orElse("").equals(layout.storyReferenceType())) throw new IllegalArgumentException("Unrecognized exchange reference type.");
            String id = atom(exchange, "identity").orElseThrow(() -> new IllegalArgumentException("Missing exchange identity."));
            long count = stories.stream().filter(s -> s.type() == Type.EXCHANGE).count();
            if (count != 1 || stories.stream().noneMatch(s -> s.type() == Type.EXCHANGE && s.nativeId().value().equals(id)))
                throw new IllegalArgumentException("Singleton pointer does not resolve to exactly one exchange.");
        } catch (IllegalArgumentException error) { issues.add(new Issue(Severity.INCOMPLETE, "globals", "xfm_exchange", error.getMessage())); }
    }

    private static Clausewitz.Block projection(FinancialSaveReader.Readback input, String name) {
        List<SaveContracts.ProjectionScope> found = input.projection().projections().stream().filter(p -> p.name().equals(name)).toList();
        if (found.size() != 1) throw new IllegalArgumentException("Exactly one complete projection required: " + name);
        return found.getFirst().ast();
    }
    private static Map<String, Clausewitz.Block> variables(Clausewitz.Block story, String identity, List<Issue> issues) {
        Optional<Clausewitz.Block> block = block(story, "variables");
        if (block.isEmpty()) { issues.add(new Issue(Severity.INCOMPLETE, identity, "variables", "Missing variables block.")); return Map.of(); }
        return variableData(block.get(), identity, issues);
    }
    private static Map<String, Clausewitz.Block> variableData(Clausewitz.Block variables, String identity, List<Issue> issues) {
        Map<String, Clausewitz.Block> result = new HashMap<>();
        Optional<Clausewitz.Block> list = block(variables, "data");
        if (list.isEmpty()) { issues.add(new Issue(Severity.INCOMPLETE, identity, "variables.data", "Missing variable list.")); return Map.of(); }
        for (Clausewitz.Entry element : list.get().entries()) {
            if (!element.key().isEmpty() || !(element.value() instanceof Clausewitz.Block variable)) {
                issues.add(new Issue(Severity.INCOMPLETE, identity, "variables.data", "Unexpected variable envelope.")); continue;
            }
            try {
                String name = atom(variable, "flag").map(FinancialProjector::unquote).orElseThrow(() -> new IllegalArgumentException("Variable flag missing."));
                Clausewitz.Block data = block(variable, "data").orElseThrow(() -> new IllegalArgumentException("Variable data missing."));
                if (name.startsWith("xfm_") && result.putIfAbsent(name, data) != null)
                    issues.add(new Issue(Severity.VIOLATION, identity, name, "Duplicate financial variable."));
            } catch (IllegalArgumentException error) { issues.add(new Issue(Severity.INCOMPLETE, identity, "variables.data", error.getMessage())); }
        }
        return result;
    }
    static Optional<String> atom(Clausewitz.Block body, String key) {
        List<Clausewitz.Entry> found = body.named(key);
        if (found.isEmpty()) return Optional.empty();
        if (found.size() != 1 || !found.getFirst().operator().equals("=") || !(found.getFirst().value() instanceof Clausewitz.Atom atom))
            throw new IllegalArgumentException("Expected one assigned atom: " + key);
        return Optional.of(atom.token());
    }
    private static Optional<Clausewitz.Block> block(Clausewitz.Block body, String key) {
        List<Clausewitz.Entry> found = body.named(key);
        if (found.isEmpty()) return Optional.empty();
        if (found.size() != 1 || !found.getFirst().operator().equals("=") || !(found.getFirst().value() instanceof Clausewitz.Block block))
            throw new IllegalArgumentException("Expected one assigned block: " + key);
        return Optional.of(block);
    }
    static String unquote(String lexical) {
        if (lexical.length() >= 2 && lexical.charAt(0) == '"' && lexical.charAt(lexical.length() - 1) == '"') {
            String interior = lexical.substring(1, lexical.length() - 1);
            if (interior.indexOf('\\') >= 0 || interior.indexOf('"') >= 0) throw new IllegalArgumentException("Escaped financial key/version unsupported.");
            return interior;
        }
        return lexical;
    }
}
