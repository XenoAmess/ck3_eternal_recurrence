package org.xar.ck3.control.g2.m0;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m0.RaiktorRawJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import org.xar.ck3.control.g2.m0.RaiktorActualRecommendationFactory.Configuration;
import org.xar.ck3.control.g2.m0.RaiktorActualRecommendationFactory.ConfigurationSources;
import org.xar.ck3.control.g2.m0.RaiktorActualRecommendationFactory.FileRef;

/** Exact-byte configuration loading and original pure source rendering; no strategy default is fabricated. */
public final class RaiktorStrategyConfiguration {
    private static final Set<String> PAIR = Set.of("maximum_surrender_gold_transfer_raw",
            "maximum_surrender_prestige_loss_raw", "maximum_surrender_claims_removed", "allow_surrender_favor_hook",
            "maximum_surrender_truce_days", "maximum_continue_tail_loss_raw", "minimum_switch_margin_raw");
    private static final Set<String> WHITE = Set.of("maximum_gold_transfer_raw", "maximum_prestige_loss_raw",
            "maximum_claims_removed", "allow_favor_hook", "maximum_truce_days");
    private static final Set<String> COEFFICIENTS = Set.of("primary_gold_transfer_raw", "attacker_prestige_delta_raw",
            "declared_claim_removed_count", "favor_hook_applied", "truce_day_count", "pow_release_count",
            "title_holder_change_count", "hostage_transfer_count", "war_bound_soldier_loss_count");
    private static final Set<String> BUDGET2 = Set.of("schema_version", "contract", "profile_version", "activation",
            "profile_id", "profile_provenance", "pairwise_limits", "white_peace_limits");
    private static final Set<String> BUDGET1 = Set.of("schema_version", "contract", "approval", "profile_id",
            "profile_provenance", "pairwise_limits", "white_peace_limits");
    private static final Set<String> MODEL = Set.of("schema_version", "contract", "model_version", "activation",
            "model_id", "model_provenance", "utility_unit", "budget_profile_binding", "domain_coefficients_q100000",
            "nonlinear_policy", "uncertainty_policy", "tail_risk_policy");
    private RaiktorStrategyConfiguration() { }

    static Configuration load(ConfigurationSources sources) {
        Document baseBudget = repositoryBudget(sources.defaultBudget());
        Document baseModel = repositoryModel(sources.defaultModel());
        return new Configuration(ownerBudget(baseBudget, sources.budgetOverride()),
                exitModel(baseBudget, baseModel, sources.modelOverride()), sources);
    }

    /** Load only the original budget provider dependencies; a model file is not required. */
    public static ObjectNode provideOwnerBudget(FileRef defaultBudget, java.util.Optional<FileRef> override) {
        Objects.requireNonNull(override, "budget override");
        return ownerBudget(repositoryBudget(defaultBudget), override);
    }

    /** Load the model with its exact repository budget binding, independently of any budget override. */
    public static ObjectNode provideExitModel(FileRef defaultBudget, FileRef defaultModel,
            java.util.Optional<FileRef> override) {
        Objects.requireNonNull(override, "model override");
        return exitModel(repositoryBudget(defaultBudget), repositoryModel(defaultModel), override);
    }

    private static Document repositoryBudget(FileRef ref) {
        Document source = read(Objects.requireNonNull(ref, "default budget"));
        require(kind(source.json(), true).equals("repository_default"),
                "repository default budget activation differs");
        return source;
    }

    private static Document repositoryModel(FileRef ref) {
        Document source = read(Objects.requireNonNull(ref, "default model"));
        require(kind(source.json(), false).equals("repository_default"),
                "repository default model activation differs");
        return source;
    }

    private static ObjectNode ownerBudget(Document base, java.util.Optional<FileRef> override) {
        Document chosen = override.map(RaiktorStrategyConfiguration::read).orElse(base);
        if (override.isPresent()) {
            String sourceKind = kind(chosen.json(), true);
            require(!sourceKind.equals("repository_default"), "explicit versioned source must declare operator_override");
            if (sourceKind.equals("operator_override")) requireBase(chosen.json(), base.json(), true);
        }
        ObjectNode profile = renderBudget(chosen.json(), chosen.sha256(), base.json());
        return budgetProvider(chosen, profile, override.isEmpty());
    }

    private static ObjectNode exitModel(Document baseBudget, Document baseModel,
            java.util.Optional<FileRef> override) {
        Document chosen = override.map(RaiktorStrategyConfiguration::read).orElse(baseModel);
        if (override.isPresent()) {
            require(kind(chosen.json(), false).equals("operator_override"), "explicit source must declare operator_override");
            requireBase(chosen.json(), baseModel.json(), false);
        }
        ObjectNode model = renderModel(chosen.json(), chosen.sha256());
        ObjectNode binding = object(model.get("budget_profile_binding"), "budget binding");
        require(same(binding.get("profile_id"), baseBudget.json().get("profile_id"))
                && same(binding.get("profile_version"), baseBudget.json().get("profile_version"))
                && text(binding.get("profile_source_sha256"), "budget SHA").equals(baseBudget.sha256()),
                "repository budget profile binding drifted");
        return modelProvider(chosen, model, override.isEmpty());
    }

    /** The original renderer accepts explicit source hash; file loading above establishes its provenance. */
    public static ObjectNode renderBudget(JsonNode raw, String sourceSha256, JsonNode repositoryDefault) {
        ObjectNode source = object(raw, "source"); boolean versioned = version(source.get("schema_version"), 2)
                && "raiktor-strategy-budget-profile-source-v2".equals(text(source.get("contract"), "contract"));
        boolean eligible;
        if (versioned) {
            exact(source, BUDGET2, "source"); semantic(source.get("profile_version"), "profile_version");
            ObjectNode activation = activation(source.get("activation"), true);
            if (text(activation.get("kind"), "activation kind").equals("operator_override")) {
                require(repositoryDefault != null, "repository budget identity required for override");
                requireBase(source, object(repositoryDefault, "repository default"), true);
            }
            eligible = true;
        } else {
            exact(source, BUDGET1, "source"); require(version(source.get("schema_version"), 1)
                    && text(source.get("contract"), "contract").equals("raiktor-owner-budget-profile-source-v1"),
                    "source identity drifted");
            eligible = approval(source.get("approval"));
        }
        String id = text(source.get("profile_id"), "profile_id");
        String provenance = text(source.get("profile_provenance"), "profile_provenance");
        require(sourceSha256 != null && sourceSha256.matches("[0-9A-F]{64}"), "source_sha256 malformed");
        ObjectNode pair = exact(source.get("pairwise_limits"), PAIR, "pairwise_limits").deepCopy();
        for (String key : List.of("maximum_surrender_gold_transfer_raw", "maximum_surrender_prestige_loss_raw",
                "maximum_continue_tail_loss_raw")) nonnegative(pair.get(key), key);
        positive64(pair.get("minimum_switch_margin_raw"), "minimum_switch_margin_raw");
        number(pair.get("maximum_surrender_claims_removed"), 0, Integer.MAX_VALUE, "maximum_surrender_claims_removed");
        number(pair.get("maximum_surrender_truce_days"), 0, Integer.MAX_VALUE, "maximum_surrender_truce_days");
        bool(pair.get("allow_surrender_favor_hook"), "allow_surrender_favor_hook");
        pair.put("schema_version", 1); pair.put("profile_id", id); pair.put("profile_provenance", provenance);
        pair.put("profile_production_eligible", eligible);
        ObjectNode white = exact(source.get("white_peace_limits"), WHITE, "white_peace_limits").deepCopy();
        nonnegative(white.get("maximum_gold_transfer_raw"), "maximum_gold_transfer_raw");
        nonnegative(white.get("maximum_prestige_loss_raw"), "maximum_prestige_loss_raw");
        number(white.get("maximum_claims_removed"), 0, Integer.MAX_VALUE, "maximum_claims_removed");
        number(white.get("maximum_truce_days"), 0, Integer.MAX_VALUE, "maximum_truce_days");
        bool(white.get("allow_favor_hook"), "allow_favor_hook");
        ObjectNode result = StrictJson.object(); result.put("schema_version", 1);
        result.put("contract", "raiktor-owner-budget-profile-v1"); result.put("status", eligible ? "complete" : "incomplete");
        result.put("profile_id", id); result.put("profile_provenance", provenance); result.put("profile_source_sha256", sourceSha256);
        result.put("profile_production_eligible", eligible); result.set("pairwise_limits", pair); result.set("white_peace_limits", white);
        return result;
    }

    public static ObjectNode renderModel(JsonNode raw, String sourceSha256) {
        ObjectNode source = exact(raw, MODEL, "source");
        require(version(source.get("schema_version"), 2)
                && text(source.get("contract"), "contract").equals("raiktor-strategy-exit-utility-model-source-v2"),
                "source identity drifted");
        require(text(source.get("utility_unit"), "utility_unit").equals("strategy_utility_q100000"), "utility unit drifted");
        require(sourceSha256 != null && sourceSha256.matches("[0-9A-F]{64}"), "source_sha256 malformed");
        ObjectNode activation = activation(source.get("activation"), false);
        ObjectNode binding = exact(source.get("budget_profile_binding"),
                Set.of("profile_id", "profile_version", "profile_source_sha256"), "budget_profile_binding").deepCopy();
        text(binding.get("profile_id"), "profile_id"); semantic(binding.get("profile_version"), "profile_version");
        sha(binding.get("profile_source_sha256"), "profile_source_sha256");
        ObjectNode coefficients = exact(source.get("domain_coefficients_q100000"), COEFFICIENTS, "coefficients").deepCopy();
        for (String key : COEFFICIENTS) number(coefficients.get(key), Long.MIN_VALUE, Long.MAX_VALUE, key);
        ObjectNode result = StrictJson.object(); result.put("schema_version", 2);
        result.put("contract", "raiktor-strategy-exit-utility-model-v2"); result.put("status", "complete");
        result.put("model_id", text(source.get("model_id"), "model_id"));
        result.put("model_version", semantic(source.get("model_version"), "model_version"));
        result.put("model_provenance", text(source.get("model_provenance"), "model_provenance"));
        result.put("utility_unit", "strategy_utility_q100000"); result.put("model_source_sha256", sourceSha256);
        result.set("activation", activation); result.set("budget_profile_binding", binding);
        result.set("domain_coefficients_q100000", coefficients);
        for (String key : List.of("nonlinear_policy", "uncertainty_policy", "tail_risk_policy")) {
            ObjectNode policy = exact(source.get(key), Set.of("rule_id", "parameters_raw"), key).deepCopy();
            text(policy.get("rule_id"), key + ".rule_id");
            ObjectNode parameters = object(policy.get("parameters_raw"), key + ".parameters_raw");
            parameters.fields().forEachRemaining(entry -> {
                require(!entry.getKey().strip().isEmpty(), "policy parameter key must be nonempty");
                number(entry.getValue(), Long.MIN_VALUE, Long.MAX_VALUE, key + "." + entry.getKey());
            });
            result.set(key, policy);
        }
        result.put("model_production_eligible", true); return result;
    }

    private static String kind(ObjectNode source, boolean budget) {
        if (budget && version(source.get("schema_version"), 1)
                && text(source.get("contract"), "contract").equals("raiktor-owner-budget-profile-source-v1")) return "legacy_owner_artifact";
        return text(activation(source.get("activation"), budget).get("kind"), "activation kind");
    }
    private static boolean version(JsonNode value, int expected) {
        return value != null && value.isIntegralNumber() && value.bigIntegerValue().equals(java.math.BigInteger.valueOf(expected));
    }
    private static String semantic(JsonNode value, String name) {
        String version = text(value, name); require(version.matches("[1-9]\\d*\\.\\d+\\.\\d+"), name + " semantic version required");
        return version;
    }
    private static ObjectNode activation(JsonNode raw, boolean budget) {
        String name = budget ? "profile" : "model";
        ObjectNode activation = exact(raw, Set.of("kind", "source", "base_" + name + "_id", "base_" + name + "_version"), "activation").deepCopy();
        String kind = text(activation.get("kind"), "activation.kind");
        require(Set.of("repository_default", "operator_override").contains(kind), "activation kind unsupported");
        text(activation.get("source"), "activation.source");
        JsonNode id = activation.get("base_" + name + "_id"); JsonNode version = activation.get("base_" + name + "_version");
        if (kind.equals("repository_default")) require(id.isNull() && version.isNull(), "repository default cannot declare a base");
        else { text(id, "base ID"); semantic(version, "base version"); }
        return activation;
    }
    private static void requireBase(ObjectNode source, ObjectNode base, boolean budget) {
        String name = budget ? "profile" : "model";
        ObjectNode activation = activation(source.get("activation"), budget);
        require(same(activation.get("base_" + name + "_id"), base.get(name + "_id"))
                && same(activation.get("base_" + name + "_version"), base.get(name + "_version")),
                "operator override base " + name + " identity drifted");
    }
    private static boolean approval(JsonNode raw) {
        ObjectNode approval = exact(raw, Set.of("status", "approved_by", "approved_at_utc"), "approval");
        String status = text(approval.get("status"), "approval.status");
        require(Set.of("draft", "approved").contains(status), "approval status unsupported");
        JsonNode actor = approval.get("approved_by"); JsonNode timestamp = approval.get("approved_at_utc");
        if (!actor.isNull()) text(actor, "approval.approved_by");
        if (!timestamp.isNull()) {
            String utc = text(timestamp, "approval.approved_at_utc");
            require(utc.matches("\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z"), "approval UTC timestamp required");
            Instant.parse(utc);
        }
        if (status.equals("approved")) require(!actor.isNull() && !timestamp.isNull(), "approved source requires actor and timestamp");
        else require(actor.isNull() && timestamp.isNull(), "draft approval actor and timestamp must be null");
        return status.equals("approved");
    }
    private static Document read(FileRef ref) {
        try {
            Path path = ref.path();
            BasicFileAttributes before = IdentityBearingFileAttributes.read(path);
            require(before.isRegularFile() && before.size() == ref.bytes(), "configuration source bytes differ");
            byte[] bytes = Files.readAllBytes(path);
            BasicFileAttributes after = IdentityBearingFileAttributes.read(path);
            require(bytes.length == ref.bytes() && before.size() == after.size()
                    && before.lastModifiedTime().equals(after.lastModifiedTime())
                    && Objects.equals(before.fileKey(), after.fileKey()), "configuration source changed while reading");
            String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)).toUpperCase(Locale.ROOT);
            require(sha.equalsIgnoreCase(ref.sha256()), "configuration source SHA differs");
            byte[] json = bytes.length >= 3 && bytes[0] == (byte)0xef && bytes[1] == (byte)0xbb && bytes[2] == (byte)0xbf
                    ? java.util.Arrays.copyOfRange(bytes, 3, bytes.length) : bytes;
            return new Document(path.toString(), sha, object(StrictJson.parse(json, StrictJson.EXPLICIT_MAX_BYTES), "configuration source"));
        } catch (IOException | NoSuchAlgorithmException failure) {
            throw new IllegalArgumentException("cannot read exact configuration source: " + ref.path(), failure);
        }
    }
    private record Document(String path, String sha256, ObjectNode raw) {
        private Document { raw = raw.deepCopy(); }
        ObjectNode json() { return raw.deepCopy(); }
    }
    private static ObjectNode budgetProvider(Document doc, ObjectNode profile, boolean defaultUsed) {
        boolean eligible = bool(profile.get("profile_production_eligible"), "profile eligible");
        ObjectNode result = StrictJson.object(); result.put("schema", "xar.ck3.raiktor_owner_budget_profile_provider.v1");
        result.put("provider", "raiktor-owner-budget-profile-provider-v1"); result.put("status", eligible ? "available" : "incomplete");
        ObjectNode source = result.putObject("source"); source.put("path", doc.path()); source.put("sha256", doc.sha256());
        result.put("source_kind", kind(doc.json(), true)); result.set("source_profile_version", doc.json().get("profile_version"));
        if (!result.has("source_profile_version")) result.putNull("source_profile_version");
        result.put("default_source_used", defaultUsed); result.put("profile_available", true);
        result.put("profile_production_eligible", eligible); result.set("owner_budget_profile", profile);
        strings(result, "blockers", eligible ? List.of() : List.of("owner_budget_profile_not_owner_approved"));
        strings(result, "boundaries", List.of("versioned_repository_default_is_active", "explicit_versioned_operator_override_binds_default_profile_identity",
                "source_sha256_binds_exact_file_bytes", "profile_is_policy_input_not_campaign_evidence",
                "profile_is_policy_input_not_white_peace_evidence", "profile_does_not_authorize_an_action"));
        return result;
    }
    private static ObjectNode modelProvider(Document doc, ObjectNode model, boolean defaultUsed) {
        ObjectNode result = StrictJson.object(); result.put("schema", "xar.ck3.raiktor_exit_utility_model_provider.v1");
        result.put("provider", "raiktor-exit-utility-model-file-provider-v1"); result.put("status", "available");
        ObjectNode source = result.putObject("source"); source.put("path", doc.path()); source.put("sha256", doc.sha256());
        result.put("source_kind", kind(doc.json(), false)); result.set("source_model_version", model.get("model_version"));
        result.put("default_source_used", defaultUsed); result.put("model_available", true); result.put("model_production_eligible", true);
        result.set("exit_utility_model", model); result.putArray("provider_blockers");
        ObjectNode readiness = result.putObject("downstream_readiness");
        for (String name : List.of("same_frame_utility_evaluation_ready", "white_peace_comparison_ready", "decision_ready",
                "automatic_surrender_ready", "gen034_closed")) readiness.put(name, false);
        strings(result, "boundaries", List.of("versioned_repository_default_is_active", "operator_override_must_bind_default_model_identity",
                "model_binds_exact_repository_budget_bytes", "source_sha256_binds_exact_model_bytes",
                "model_is_strategy_configuration_not_ck3_observation", "model_is_not_native_ai_semantics",
                "model_alone_does_not_authorize_an_action"));
        return result;
    }
}

