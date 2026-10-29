package org.xar.ck3.control.wave2.military.declarationcontract;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Pattern;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Real native declaration catalogue projection and literal command grammar, without action submission. */
public final class DeclarationContract {
    public static final String QUERY_DECLARABLE_WARS_STEP = "query-declarable-wars";
    public static final String DECLARE_WAR_CAPABILITY = "game.command.declare-war-N";
    private static final BigInteger ABSENT = BigInteger.valueOf(-1);
    // Python's re \d is Unicode decimal digits. Literal parsing is deliberately distinct from catalogue canonical IDs.
    private static final Pattern LITERAL_ID = Pattern.compile("\\p{Nd}+-\\p{Nd}+-(-1|\\p{Nd}+)");
    private static final String PREFIX = "declare-war-";

    private DeclarationContract() { }

    public record Choice(String declarationId, BigInteger targetCharacterId, BigInteger casusBelliIndex,
                         String casusBelliKey, BigInteger configurationIndex, BigInteger claimantCharacterId,
                         List<BigInteger> targetTitleIds) {
        public Choice {
            nonnegative(targetCharacterId); nonnegative(casusBelliIndex);
            minimum(configurationIndex, ABSENT); minimum(claimantCharacterId, ABSENT);
            require(casusBelliKey != null && !casusBelliKey.isEmpty(), "nonempty semantic CB key required");
            targetTitleIds = List.copyOf(targetTitleIds);
            targetTitleIds.forEach(DeclarationContract::nonnegative);
            require(Objects.equals(declarationId, identity(targetCharacterId, casusBelliIndex, configurationIndex)), "declaration ID changed tuple meaning");
        }
        public String source() { return "native"; }
        public LiteralStep step() { return buildStep(declarationId); }
    }

    /** A syntax match preserves raw leading zeros/Unicode digits; it does not qualify a current catalogue choice. */
    public record LiteralStep(String declarationId) {
        public LiteralStep { require(declarationId != null && LITERAL_ID.matcher(declarationId).matches(), "malformed declaration literal"); }
        public String wire() { return PREFIX + declarationId; }
    }

    /** Existing catalogue containers accept extra native metadata and emit only the original declared projection. */
    public static List<Choice> normalize(JsonNode value) {
        inputRequire(value != null && value.isArray(), "native declarable_wars must be an array");
        List<Choice> result = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        for (JsonNode raw : value) {
            inputRequire(raw instanceof ObjectNode, "native declaration row must be an object");
            BigInteger target = integer(raw.get("target_character_id"), BigInteger.ZERO);
            BigInteger cb = integer(raw.get("casus_belli_index"), BigInteger.ZERO);
            BigInteger configuration = integer(raw.get("configuration_index"), ABSENT);
            BigInteger claimant = integer(raw.get("claimant_character_id"), ABSENT);
            JsonNode rawKey = raw.get("casus_belli_key");
            inputRequire(rawKey != null && rawKey.isTextual() && !rawKey.textValue().isEmpty(), "nonempty semantic CB key required");
            JsonNode titles = raw.get("target_title_ids");
            inputRequire(titles != null && titles.isArray(), "ordered target_title_ids array required");
            List<BigInteger> normalizedTitles = new ArrayList<>();
            for (JsonNode title : titles) normalizedTitles.add(integer(title, BigInteger.ZERO));
            String identity = identity(target, cb, configuration);
            JsonNode rawIdentity = raw.get("declaration_id");
            inputRequire(rawIdentity != null && rawIdentity.isTextual() && rawIdentity.textValue().equals(identity), "declaration ID is malformed or changed meaning");
            inputRequire(seen.add(identity), "native declarations repeat a catalogue choice");
            result.add(new Choice(identity, target, cb, rawKey.textValue(), configuration, claimant, normalizedTitles));
        }
        return List.copyOf(result);
    }

    public static LiteralStep buildStep(String declarationId) { return new LiteralStep(declarationId); }

    public static Optional<LiteralStep> parseStep(JsonNode step) {
        if (step == null || !step.isTextual()) return Optional.empty();
        return parseStep(step.textValue());
    }

    public static Optional<LiteralStep> parseStep(String step) {
        if (step == null || !step.startsWith(PREFIX)) return Optional.empty();
        String declarationId = step.substring(PREFIX.length());
        return LITERAL_ID.matcher(declarationId).matches() ? Optional.of(new LiteralStep(declarationId)) : Optional.empty();
    }

    public static boolean isNativeDeclarationStep(JsonNode step) {
        return step != null && step.isTextual() && isNativeDeclarationStep(step.textValue());
    }

    public static boolean isNativeDeclarationStep(String step) {
        return QUERY_DECLARABLE_WARS_STEP.equals(step) || parseStep(step).isPresent();
    }

    public static ArrayNode encode(List<Choice> choices) {
        ArrayNode result = StrictJson.object().putArray("choices");
        for (Choice choice : List.copyOf(choices)) result.add(encodeChoice(choice));
        return result;
    }

    public static ObjectNode encodeChoice(Choice choice) {
        ObjectNode result = StrictJson.object().put("declaration_id", choice.declarationId())
                .put("target_character_id", choice.targetCharacterId()).put("casus_belli_index", choice.casusBelliIndex())
                .put("casus_belli_key", choice.casusBelliKey()).put("configuration_index", choice.configurationIndex())
                .put("claimant_character_id", choice.claimantCharacterId()).put("source", choice.source());
        ArrayNode titles = result.putArray("target_title_ids"); choice.targetTitleIds().forEach(titles::add);
        return result;
    }

    private static BigInteger integer(JsonNode value, BigInteger minimum) {
        inputRequire(value != null && value.isIntegralNumber(), "actual JSON integer required; bool/float/string rejected");
        BigInteger result = value.bigIntegerValue();
        inputRequire(result.compareTo(minimum) >= 0, "integer is below declaration contract minimum"); return result;
    }
    private static String identity(BigInteger target, BigInteger cb, BigInteger configuration) {
        return target + "-" + cb + "-" + configuration;
    }
    private static void nonnegative(BigInteger value) { minimum(value, BigInteger.ZERO); }
    private static void minimum(BigInteger value, BigInteger minimum) {
        require(value != null && value.compareTo(minimum) >= 0, "integer is below declaration contract minimum");
    }
    private static void inputRequire(boolean condition, String reason) {
        if (!condition) throw new ProjectionDomainRejection("declaration contract " + reason);
    }
    private static void require(boolean condition, String reason) { StrictJson.require(condition, "declaration contract " + reason); }
}
