package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyCodec;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel;

/** Original construction body boundary. Missing body is handled by the one writer, never initialized here. */
public final class ConstructionLedgerCodec {
    public static final int MAX_BYTES = org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES;
    public static final String SCHEMA = "xar.ck3.construction_formal_pending_v1";
    private ConstructionLedgerCodec() { }
    public record Tuple(BigInteger barony, BigInteger province, BigInteger building, BigInteger slot) {
        public Tuple { positive(barony); positive(province); positive(building); nonnegative(slot); }
    }
    /** Legacy creation token is compared verbatim; it is never promoted to a 100 ns FILETIME. */
    public record Process(BigInteger pid, String legacyCreationToken) {
        public Process { positive(pid); require(legacyCreationToken != null && !legacyCreationToken.isEmpty(), "actual creation token required"); }
    }
    public record Scope(Process process, BigInteger nativeRevision, BigInteger dateRaw) {
        public Scope { Objects.requireNonNull(process); positive(nativeRevision); nonnegative(dateRaw); }
    }
    public record Identity(String actionRequestId, String episode, BigInteger actor, Tuple candidate) {
        public Identity { require(actionRequestId != null && !actionRequestId.isEmpty(), "original action identity required");
            require(episode != null && !episode.isEmpty(), "original episode required"); positive(actor); Objects.requireNonNull(candidate); }
    }
    public record Intent(Obj original, Identity identity, Scope source, BigInteger proofEpoch) {
        public Intent { Objects.requireNonNull(original); Objects.requireNonNull(identity); Objects.requireNonNull(source); positive(proofEpoch); }
        public Optional<String> coordinatorActionId() {
            return original.get("coordinator_action_id") instanceof Text value ? Optional.of(value.value()) : Optional.empty();
        }
    }
    public record Receipt(Obj original, Identity identity, Scope observed, ConstructionEconomyModel.Receipt economy) {
        public Receipt { Objects.requireNonNull(original); Objects.requireNonNull(identity); Objects.requireNonNull(observed); Objects.requireNonNull(economy); }
        public boolean completed() { return economy.completion() == ConstructionEconomyModel.CompletionStatus.COMPLETED; }
        public Optional<BigInteger> lastCheck() { return original.members().containsKey("completion_last_check_date_raw")
                ? optionalInteger(original, "completion_last_check_date_raw") : optionalInteger(original, "post_date_raw"); }
    }
    public record Ledger(Obj original, Optional<Intent> pending, Optional<Receipt> applied, List<Receipt> prior) {
        public Ledger { Objects.requireNonNull(original); Objects.requireNonNull(pending); Objects.requireNonNull(applied); prior = List.copyOf(prior); }
        public List<Receipt> receipts(String episode) {
            List<Receipt> rows = new ArrayList<>(prior); applied.ifPresent(rows::add);
            return rows.stream().filter(row -> row.identity().episode().equals(episode)).toList();
        }
    }
    public static void validateLedger(byte[] original) { decodeLedger(original); }
    public static Ledger decodeLedger(byte[] original) {
        Objects.requireNonNull(original); require(original.length > 0 && original.length <= MAX_BYTES, "bounded original construction body required");
        Obj body = DriverJson.object(original, MAX_BYTES);
        require(new Text(SCHEMA).equals(body.get("schema")), "original construction schema required");
        if (body.members().containsKey(ConstructionMaterialSource.BODY_FIELD))
            ConstructionMaterialSource.decode(object(body.get(ConstructionMaterialSource.BODY_FIELD), "original complete material source"));
        Optional<Intent> pending = nullableObject(body, "pending").map(ConstructionLedgerCodec::intent);
        Optional<Receipt> applied = nullableObject(body, "applied").map(ConstructionLedgerCodec::receipt);
        Value previous = body.get("applied_prior"); List<Receipt> prior = new ArrayList<>();
        // Missing applied_prior is the original pre-history format; explicit null is not an empty collection.
        if (previous != null) for (Value row : array(previous, "applied_prior")) prior.add(receipt(object(row, "prior receipt")));
        HashSet<String> ids = new HashSet<>();
        for (Receipt row : prior) require(ids.add(row.identity().actionRequestId()), "duplicate original applied action identity");
        applied.ifPresent(row -> require(ids.add(row.identity().actionRequestId()), "duplicate newest applied action identity"));
        return new Ledger(body, pending, applied, prior);
    }
    public static Intent intent(Obj row) {
        Identity identity = identity(row);
        validateFundingEvidence(row, identity);
        boolean hasCoordinator = row.members().containsKey("coordinator_action_id") || row.members().containsKey("coordinator_body_sha256");
        if (hasCoordinator) {
            String action = text(row.get("coordinator_action_id"), "actual coordinator action identity");
            String digest = text(row.get("coordinator_body_sha256"), "actual coordinator body digest");
            require(action.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}") && digest.matches("[0-9a-f]{64}")
                    && identity.actionRequestId().equals(org.xar.ck3.control.application.action.RequestIds.forActionBody(digest)),
                    "actual coordinator and native request identities differ");
        }
        require(!new Text("java_intent_prepared").equals(row.get("status")) || hasCoordinator, "prepared Java intent requires its distinct coordinator identity");
        BigInteger wallet = requiredInteger(object(row.get("candidate"), "candidate"), "gold_before_raw");
        BigInteger cost = requiredInteger(object(row.get("candidate"), "candidate"), "stock_gold_cost_raw");
        nonnegative(wallet); positive(cost); require(wallet.compareTo(cost) >= 0, "original native quote exceeds its observed wallet");
        return new Intent(row, identity, new Scope(new Process(requiredInteger(row, "source_bridge_pid"),
                text(row.get("source_bridge_creation_date"), "source process creation")), requiredInteger(row, "pre_native_revision"),
                requiredInteger(row, "pre_date_raw")), requiredInteger(row, "pre_proof_epoch"));
    }
    public static Receipt receipt(Obj row) {
        Identity identity = identity(row);
        validateFundingEvidence(row, identity);
        Scope originalScope = new Scope(new Process(requiredInteger(row, "post_bridge_pid"),
                text(row.get("post_bridge_creation_date"), "post process creation")), requiredInteger(row, "post_native_revision"),
                requiredInteger(row, "post_date_raw"));
        Scope actual = unavailableObservationScope(row, identity).orElse(originalScope);
        ConstructionEconomyModel.Receipt economy = ConstructionEconomyCodec.decodeReceipt(encode(row));
        optionalInteger(row, "completion_last_check_date_raw").ifPresent(ConstructionLedgerCodec::nonnegative);
        return new Receipt(row, identity, actual, economy);
    }
    public static Identity identity(Obj row) {
        Obj candidate = object(row.get("candidate"), "complete original construction tuple");
        return new Identity(text(row.get("action_request_id"), "action_request_id"), text(row.get("episode_run_id"), "episode_run_id"),
                requiredInteger(row, "actor_character_id"), new Tuple(requiredInteger(candidate, "barony_title_id"),
                requiredInteger(candidate, "province_id"), requiredInteger(candidate, "building_type_id"), requiredInteger(candidate, "slot_index")));
    }
    private static void validateFundingEvidence(Obj row, Identity identity) {
        if (!row.members().containsKey(ConstructionFundingEvidence.FIELD)) return;
        var evidence = ConstructionFundingEvidence.decode(object(row.get(ConstructionFundingEvidence.FIELD), "original owned-submission source evidence"));
        var frame = evidence.current().frame();
        require(frame.episodeRunId().equals(identity.episode()) && frame.identity().player().equals(identity.actor())
                && frame.identity().nativeRevision().equals(requiredInteger(row, "pre_native_revision"))
                && frame.identity().dateRaw().equals(requiredInteger(row, "pre_date_raw")),
                "retained construction funding evidence crossed its original actor/episode/action frame");
    }
    private static Optional<Scope> unavailableObservationScope(Obj receipt, Identity identity) {
        Value raw = receipt.get("material_observation_unavailable_v1");
        if (!(raw instanceof Obj observation)) return Optional.empty();
        // Malformed historical diagnostics cannot lend their source lease to a prior material receipt.
        try {
            require(new Text("xar.construction-material-observation-unavailable.v1").equals(observation.get("schema"))
                    && new Bool(true).equals(observation.get("read_only")) && new Bool(false).equals(observation.get("business_submission"))
                    && new IntegerValue(BigInteger.ZERO).equals(observation.get("native_submit_calls"))
                    && new Text(identity.actionRequestId()).equals(observation.get("action_request_id")), "unavailable observation is not a read-only receipt");
            Obj source = object(observation.get("source_frame"), "unavailable observation source");
            BigInteger revision = requiredInteger(source, "native_revision"); positive(revision); positive(requiredInteger(source, "revision"));
            require(new Text(identity.episode()).equals(source.get("episode_run_id")) && new IntegerValue(identity.actor()).equals(source.get("actor_character_id"))
                    && new Text("native:" + revision).equals(source.get("snapshot_id"))
                    && Objects.equals(source.get("date_raw"), receipt.get("completion_last_check_date_raw")), "unavailable observation crossed the original action");
            return Optional.of(new Scope(new Process(requiredInteger(source, "bridge_pid"), text(source.get("bridge_creation_date"), "source creation")),
                    revision, requiredInteger(source, "date_raw")));
        } catch (IllegalArgumentException rejected) { return Optional.empty(); }
    }
    public static Optional<Obj> nullableObject(Obj row, String field) {
        Value value = row.get(field); require(value != null, "required nullable field absent: " + field);
        return value == Nil.INSTANCE ? Optional.empty() : Optional.of(object(value, field));
    }
    public static Optional<BigInteger> optionalInteger(Obj row, String field) {
        Value value = row.get(field); return value == null || value == Nil.INSTANCE ? Optional.empty() : Optional.of(integer(value, field));
    }
    public static BigInteger requiredInteger(Obj row, String field) { return integer(row.get(field), field); }
    private static void positive(BigInteger value) { require(value != null && value.signum() > 0, "positive exact native integer required"); }
    private static void nonnegative(BigInteger value) { require(value != null && value.signum() >= 0, "nonnegative exact native integer required"); }
}
