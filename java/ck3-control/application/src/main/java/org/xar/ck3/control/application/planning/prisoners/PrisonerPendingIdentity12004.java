package org.xar.ck3.control.application.planning.prisoners;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;

/** Exact legacy identity projection. Parsing this object never imports an action or grants replay. */
public record PrisonerPendingIdentity12004(PrisonerPlanningPorts.Family family, RawJson original,
        long actor, long target, BigInteger nativeRevision, int dateRaw, Optional<BigInteger> publicRevision,
        Optional<String> actionId, Optional<String> requestId, Optional<RansomTerms> ransom, Optional<ReleaseTerms> release) {
    public PrisonerPendingIdentity12004 {
        Objects.requireNonNull(family); Objects.requireNonNull(original); NativeCharacterId.of(actor); validId(target);
        StrictJson.require(actor != target && nativeRevision != null && nativeRevision.signum() > 0
                && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0 && dateRaw > 0, "original prisoner pending pair/frame required");
        Objects.requireNonNull(publicRevision); Objects.requireNonNull(actionId); Objects.requireNonNull(requestId);
        Objects.requireNonNull(ransom); Objects.requireNonNull(release);
        StrictJson.require((family == PrisonerPlanningPorts.Family.RANSOM) == ransom.isPresent()
                && (family == PrisonerPlanningPorts.Family.RELEASE) == release.isPresent(), "exact pending family/terms required");
        actionId.ifPresent(StrictJson::text); requestId.ifPresent(StrictJson::text);
    }
    public record RansomTerms(long payer, String option, boolean acceptanceTime, long quotedGoldRaw, long playerGoldBefore) {
        public RansomTerms { validId(payer); StrictJson.require(option.equals("gold") || option.equals("current_gold"), "original ransom gold option required");
            StrictJson.require(quotedGoldRaw > 0 && acceptanceTime == option.equals("current_gold"), "original ransom quote timing differs"); }
    }
    public record ReleaseTerms(BigInteger querySequence, PrisonerOptionIntent options, int mask, RawJson costs, RawJson acceptance) {
        public ReleaseTerms { Objects.requireNonNull(querySequence); Objects.requireNonNull(options); Objects.requireNonNull(costs); Objects.requireNonNull(acceptance);
            StrictJson.require(querySequence.signum() > 0 && querySequence.compareTo(StrictJson.UINT64_MAX) <= 0
                    && mask == (options instanceof PrisonerOptionIntent.Negotiated value ? value.mask() : 0), "original release query/option mask differs"); }
    }
    public static PrisonerPendingIdentity12004 decode(PrisonerPlanningPorts.Family family, RawJson raw) {
        Objects.requireNonNull(family); JsonNode value = StrictJson.parse(raw.bytes(), 1_048_576);
        StrictJson.require(value instanceof ObjectNode, "original pending object required");
        String stage = StrictJson.text(value.get("stage"));
        StrictJson.require(stage.equals("submission_unresolved") || stage.equals("receipt_pending"), "supported retained prisoner pending stage required");
        long actor = NativeCharacterId.fromJson(value.get("player_character_id")).value(), target = id(value, "prisoner_character_id");
        BigInteger nativeRevision = uint(value, "pre_native_revision"); int date = (int) StrictJson.integer(value.get("pre_date_raw"), 1, Integer.MAX_VALUE);
        Optional<BigInteger> publicRevision = value.has("pre_public_revision") ? Optional.of(uint(value, "pre_public_revision")) : Optional.empty();
        Optional<String> actionId = value.has("action_id") ? Optional.of(StrictJson.text(value.get("action_id"))) : Optional.empty();
        Optional<String> requestId = Optional.empty();
        if (value.has("material_result")) no(value.get("material_result"));
        if (value.has("action_ack")) {
            JsonNode ack = value.get("action_ack"); StrictJson.require(ack != null && ack.isObject(), "present action_ack cannot be null");
            StrictJson.require("submitted_verification_pending".equals(StrictJson.text(ack.get("status"))), "old ACK must remain pending-only");
            no(ack.get("material_result")); requestId = Optional.of(StrictJson.text(ack.get("request_id")));
            equal(ack, "pre_native_revision", nativeRevision); equal(ack, "pre_date_raw", BigInteger.valueOf(date));
            equal(ack, "player_character_id", BigInteger.valueOf(actor)); equal(ack, "prisoner_character_id", BigInteger.valueOf(target));
        }
        Optional<RansomTerms> ransom = Optional.empty(); Optional<ReleaseTerms> release = Optional.empty();
        if (family == PrisonerPlanningPorts.Family.RANSOM) {
            RansomTerms terms = new RansomTerms(id(value, "payer_character_id"), StrictJson.text(value.get("selected_option")),
                    bool(value.get("amount_is_acceptance_time_quote")), StrictJson.integer(value.get("quoted_gold_raw"), 1, Long.MAX_VALUE),
                    StrictJson.integer(value.get("pre_player_gold_raw"), Long.MIN_VALUE, Long.MAX_VALUE));
            if (value.has("action_ack")) {
                JsonNode ack = value.get("action_ack"); equal(ack, "payer_character_id", BigInteger.valueOf(terms.payer()));
                equal(ack, "quoted_gold_raw", BigInteger.valueOf(terms.quotedGoldRaw()));
                StrictJson.require(terms.option().equals(StrictJson.text(ack.get("selected_option"))), "old ACK changed ransom option");
            }
            ransom = Optional.of(terms);
        } else {
            ObjectNode args = StrictJson.object(); JsonNode keys = value.get("release_option_keys");
            StrictJson.require(keys != null && keys.isArray(), "legacy pending must retain explicit option-key array");
            // The legacy persisted pending representation uses [] for an already-observed unconditional offer.
            // The native query entry still rejects an explicitly supplied empty option request.
            if (!keys.isEmpty()) args.set("release_option_keys", keys);
            var intent = PrisonerOptionIntent.decode(args).options();
            JsonNode costs = value.get("costs"), acceptance = value.get("acceptance");
            StrictJson.require(costs != null && costs.isObject() && acceptance != null && acceptance.isObject(), "original release costs and acceptance required");
            ReleaseTerms terms = new ReleaseTerms(uint(value, "release_query_sequence"), intent,
                    (int) StrictJson.integer(value.get("release_option_mask_bits"), 0, 8191),
                    new RawJson(StrictJson.canonical(costs)), new RawJson(StrictJson.canonical(acceptance)));
            if (value.has("action_ack")) {
                JsonNode ack = value.get("action_ack"); equal(ack, "release_query_sequence", terms.querySequence());
                equal(ack, "release_option_mask_bits", BigInteger.valueOf(terms.mask()));
            }
            release = Optional.of(terms);
        }
        return new PrisonerPendingIdentity12004(family, raw, actor, target, nativeRevision, date, publicRevision, actionId, requestId, ransom, release);
    }
    /** Necessary identity relation only. The runtime must additionally prove the original canonical lineage and Native packet. */
    public boolean matches(ActionReceipt receipt) {
        Objects.requireNonNull(receipt); var command = receipt.command();
        if (!(command.origin() instanceof CommandOrigin.Gameplay) || !command.operation().equals(operation())
                || command.before().frame().identity().player().longValueExact() != actor
                || !command.before().frame().identity().nativeRevision().equals(nativeRevision)
                || command.before().frame().identity().dateRaw().intValueExact() != dateRaw
                || publicRevision.filter(value -> !value.equals(command.before().frame().revision())).isPresent()
                || actionId.filter(value -> !value.equals(command.actionId())).isPresent()) return false;
        JsonNode arguments = StrictJson.parse(OpportunityJson.encode(command.arguments()), ActionCommand.MAX_ARGUMENT_BYTES);
        if (id(arguments, "prisoner_character_id") != target) return false;
        Optional<ActionState.Attempt> attempt = ActionTransitions.attempt(receipt.state());
        if (attempt.isEmpty() || requestId.filter(value -> !value.equals(attempt.orElseThrow().requestId())).isPresent()) return false;
        if (family == PrisonerPlanningPorts.Family.RANSOM) {
            RansomTerms terms = ransom.orElseThrow();
            return id(arguments, "payer_character_id") == terms.payer() && StrictJson.integer(arguments.get("quoted_gold_raw"), 1, Long.MAX_VALUE) == terms.quotedGoldRaw()
                    && StrictJson.text(arguments.get("selected_option")).equals(terms.option())
                    && bool(arguments.get("amount_is_acceptance_time_quote")) == terms.acceptanceTime()
                    && StrictJson.integer(arguments.get("pre_player_gold_raw"), Long.MIN_VALUE, Long.MAX_VALUE) == terms.playerGoldBefore();
        }
        ReleaseTerms terms = release.orElseThrow();
        return uint(arguments, "release_query_sequence").equals(terms.querySequence())
                && StrictJson.integer(arguments.get("release_option_mask_bits"), 0, 8191) == terms.mask();
    }
    public OperationKey operation() { return family == PrisonerPlanningPorts.Family.RELEASE ? PrisonerOrdinaryPolicy12004.RELEASE : PrisonerOrdinaryPolicy12004.RANSOM; }
    private static long id(JsonNode row, String key) { return StrictJson.integer(row.get(key), 1, 0xfffffffeL); }
    private static BigInteger uint(JsonNode row, String key) { return StrictJson.integer(row.get(key), BigInteger.ONE, StrictJson.UINT64_MAX); }
    private static boolean bool(JsonNode value) { StrictJson.require(value != null && value.isBoolean(), "actual pending boolean required"); return value.booleanValue(); }
    private static void no(JsonNode value) { StrictJson.require(!bool(value), "pending-only false required"); }
    private static void equal(JsonNode row, String key, BigInteger value) { StrictJson.integer(row.get(key), value, value); }
    private static void validId(long value) { StrictJson.require(value > 0 && value < 0xffffffffL, "valid full character identity required"); }
}
