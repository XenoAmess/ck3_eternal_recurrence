package org.xar.ck3.control.governance.crownauthority;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Balance;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Candidate;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Choice;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Cost;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Currency;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.CurrencyAmount;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.HeldTitle;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Readback;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.SourceFrame;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.TitleSuccessors;

/** Strict JSON adapter; no Jackson coercion or dynamic JSON reaches the policy. */
public final class CrownAuthorityCodec {
    private static final Set<String> READBACK_FIELDS = Set.of("schema", "available", "paused", "group_key",
            "active_law_key", "candidates", "resources", "title_successors", "snapshot_revision",
            "native_snapshot_revision", "proof_epoch", "date_raw", "player_character_id", "exact_ck3_build",
            "exe_sha256", "read_only", "advertised", "queried_snapshot_id", "queried_revision", "queried_native_revision");
    private CrownAuthorityCodec() { }

    public record Request(Readback readback, Map<Currency, BigInteger> reservesRaw) {
        public Request { java.util.Objects.requireNonNull(readback); reservesRaw = Map.copyOf(reservesRaw); }
    }

    public static Request decodeRequest(byte[] body) {
        ObjectNode row = StrictJson.object(StrictJson.parse(body), Set.of("readback", "reserves_raw"));
        return new Request(decodeReadbackNode(row.get("readback")),decodeReserves(StrictJson.canonical(row.get("reserves_raw"))));
    }

    /** One reserve field contract shared by the domain JSON request and the native query argument producer. */
    public static Map<Currency,BigInteger> decodeReserves(byte[] encoded) {
        ObjectNode reserves=object(StrictJson.parse(encoded));EnumMap<Currency,BigInteger> values=new EnumMap<>(Currency.class);
        for(var entry:reserves.properties()){
            BigInteger amount=integer(entry.getValue());CrownAuthorityPolicy.nonnegative(amount);
            values.put(Currency.fromWire(entry.getKey()),amount);
        }
        return Map.copyOf(values);
    }
    public static byte[] encodeReserves(Map<Currency,BigInteger> reserves) {
        ObjectNode row=StrictJson.object();
        for(var entry:Map.copyOf(reserves).entrySet()){
            CrownAuthorityPolicy.nonnegative(entry.getValue());row.put(entry.getKey().wire(),entry.getValue());
        }
        return StrictJson.canonical(row);
    }

    public static byte[] encodeRequest(Request request) {
        ObjectNode row=StrictJson.object();row.set("readback",StrictJson.parse(encodeReadback(request.readback())));
        row.set("reserves_raw",StrictJson.parse(encodeReserves(request.reservesRaw())));return StrictJson.canonical(row);
    }

    public static Readback decodeReadback(byte[] body) { return decodeReadbackNode(StrictJson.parse(body)); }

    public static byte[] choose(byte[] body) {
        Request request = decodeRequest(body);
        return encodeChoice(CrownAuthorityPolicy.choose(request.readback(), request.reservesRaw()));
    }

    public static byte[] encodeChoice(Choice choice) {
        ObjectNode result = StrictJson.object();
        result.put("status", choice.status().wire()); result.put("reason", choice.reason());
        nullableText(result, "active_law_key", choice.activeLawKey());
        nullableText(result, "law_key", choice.lawKey());
        writePairs(result.putArray("budgets_raw"), choice.budgetsRaw());
        writePairs(result.putArray("quoted_post_balances_raw"), choice.quotedPostBalancesRaw());
        return StrictJson.canonical(result);
    }

    public static byte[] encodeReadback(Readback readback) {
        ObjectNode row = StrictJson.object();
        row.put("schema", readback.schema()); row.put("available", readback.available()); row.put("paused", readback.paused());
        row.put("group_key", readback.groupKey()); row.put("active_law_key", readback.activeLawKey());
        row.put("read_only", readback.readOnly()); row.put("advertised", readback.advertised());
        SourceFrame source = readback.sourceFrame();
        row.put("snapshot_revision", source.snapshotRevision()); row.put("native_snapshot_revision", source.nativeSnapshotRevision());
        row.put("proof_epoch", source.proofEpoch()); row.put("date_raw", source.dateRaw());
        row.put("player_character_id", source.playerCharacterId()); row.put("exact_ck3_build", source.exactCk3Build());
        row.put("exe_sha256", source.exeSha256()); nullableText(row, "queried_snapshot_id", source.queriedSnapshotId());
        row.put("queried_revision", source.queriedRevision()); row.put("queried_native_revision", source.queriedNativeRevision());
        writeCollections(row, readback.resources(), readback.candidates(), readback.titleSuccessors());
        return StrictJson.canonical(row);
    }

    private static Readback decodeReadbackNode(JsonNode value) {
        ObjectNode row = StrictJson.object(value, READBACK_FIELDS);
        ObservationFields fields = readObservationFields(row);
        JsonNode snapshotId = row.get("queried_snapshot_id");
        SourceFrame frame = new SourceFrame(integer(row.get("snapshot_revision")), integer(row.get("native_snapshot_revision")),
                integer(row.get("proof_epoch")), integer(row.get("date_raw")), integer(row.get("player_character_id")),
                StrictJson.text(row.get("exact_ck3_build")), StrictJson.text(row.get("exe_sha256")),
                snapshotId.isNull() ? null : StrictJson.text(snapshotId), integer(row.get("queried_revision")),
                integer(row.get("queried_native_revision")));
        return new Readback(StrictJson.text(row.get("schema")), fields.available(), fields.paused(),
                fields.groupKey(), fields.activeLawKey(), fields.candidates(), fields.resources(), fields.titleSuccessors(), frame,
                bool(row.get("read_only")), bool(row.get("advertised")));
    }

    private static Currency currency(ObjectNode row) { return Currency.fromWire(StrictJson.text(row.get("currency_key"))); }
    private static ObjectNode object(JsonNode node) {
        StrictJson.require(node instanceof ObjectNode, "JSON object required");
        return (ObjectNode) node;
    }
    private static ArrayNode array(JsonNode node) {
        StrictJson.require(node instanceof ArrayNode, "JSON array required");
        return (ArrayNode) node;
    }
    private static BigInteger integer(JsonNode node) {
        StrictJson.require(node != null && node.isIntegralNumber(), "actual integer token required");
        return node.bigIntegerValue();
    }
    private static boolean bool(JsonNode node) {
        StrictJson.require(node != null && node.isBoolean(), "actual boolean token required");
        return node.booleanValue();
    }
    private static String emptyText(JsonNode node) {
        StrictJson.require(node != null && node.isTextual(), "actual string token required");
        return node.textValue().isEmpty() ? "" : StrictJson.text(node);
    }
    private static void nullableText(ObjectNode row, String field, String value) {
        if (value == null) { row.putNull(field); } else { row.put(field, value); }
    }
    private static void writePairs(ArrayNode array, List<CurrencyAmount> values) {
        for (CurrencyAmount value : values) { array.addArray().add(value.currency().wire()).add(value.amountRaw()); }
    }

    /** Original native observation DATA. Missing request provenance is not synthesized. */
    public record ObservationFields(boolean available, boolean paused, String groupKey, String activeLawKey,
            List<Candidate> candidates, List<Balance> resources, TitleSuccessors titleSuccessors) {
        public ObservationFields {
            StrictJson.text(groupKey); StrictJson.text(activeLawKey);
            candidates=List.copyOf(candidates); resources=List.copyOf(resources);
            java.util.Objects.requireNonNull(titleSuccessors);
            StrictJson.require(!candidates.isEmpty()&&candidates.size()<=24,"bounded native candidates required");
            StrictJson.require(resources.size()==Currency.values().length&&resources.stream().map(Balance::currency)
                    .distinct().count()==resources.size(),"all five native balances once required");
            StrictJson.require(candidates.stream().filter(Candidate::active).map(Candidate::lawKey).toList()
                    .equals(List.of(activeLawKey)),"native active law differs");
        }
    }
    public record ObservedFrame(BigInteger snapshotRevision, BigInteger nativeSnapshotRevision,
            BigInteger proofEpoch, BigInteger dateRaw, BigInteger playerCharacterId) {
        public ObservedFrame {
            for (BigInteger value:List.of(snapshotRevision,nativeSnapshotRevision,proofEpoch,playerCharacterId))
                StrictJson.require(value.signum()>0,"positive original native frame field required");
            java.util.Objects.requireNonNull(dateRaw);
        }
    }
    public record NativeObservation(ObservationFields fields, ObservedFrame frame) {
        public NativeObservation { java.util.Objects.requireNonNull(fields); java.util.Objects.requireNonNull(frame); }
    }
    private static final Set<String> NATIVE_OBSERVATION_FIELDS=Set.of("available","paused","group_key",
            "active_law_key","candidates","resources","title_successors","snapshot_revision",
            "native_snapshot_revision","proof_epoch","date_raw","player_character_id");
    public static NativeObservation decodeNativeObservation(byte[] original) {
        ObjectNode row=StrictJson.object(StrictJson.parse(original),NATIVE_OBSERVATION_FIELDS);
        return new NativeObservation(readObservationFields(row),new ObservedFrame(integer(row.get("snapshot_revision")),
                integer(row.get("native_snapshot_revision")),integer(row.get("proof_epoch")),
                integer(row.get("date_raw")),integer(row.get("player_character_id"))));
    }
    public static byte[] encodeNativeObservation(NativeObservation original) {
        var value=original.fields();var frame=original.frame();ObjectNode row=StrictJson.object();
        row.put("available",value.available());row.put("paused",value.paused());row.put("group_key",value.groupKey());
        row.put("active_law_key",value.activeLawKey());row.put("snapshot_revision",frame.snapshotRevision());
        row.put("native_snapshot_revision",frame.nativeSnapshotRevision());row.put("proof_epoch",frame.proofEpoch());
        row.put("date_raw",frame.dateRaw());row.put("player_character_id",frame.playerCharacterId());
        writeCollections(row,value.resources(),value.candidates(),value.titleSuccessors());return StrictJson.canonical(row);
    }
    public static TitleSuccessors decodeTitleSuccessors(byte[] original) {
        return readTitleSuccessors(StrictJson.parse(original));
    }
    public static byte[] encodeTitleSuccessors(TitleSuccessors original) {
        ObjectNode row=StrictJson.object();writeTitleSuccessors(row,original);return StrictJson.canonical(row);
    }
    private static ObservationFields readObservationFields(ObjectNode row) {
        List<Candidate> candidates = new ArrayList<>();
        for (JsonNode item : array(row.get("candidates"))) {
            ObjectNode candidate = StrictJson.object(item, Set.of("law_key", "is_active", "engine_final_only", "can_enact", "blocked_reason", "costs"));
            List<Cost> costs = new ArrayList<>();
            for (JsonNode quoted : array(candidate.get("costs"))) {
                ObjectNode cost = StrictJson.object(quoted, Set.of("currency_key", "cost_raw"));
                costs.add(new Cost(currency(cost), integer(cost.get("cost_raw"))));
            }
            candidates.add(new Candidate(StrictJson.text(candidate.get("law_key")), bool(candidate.get("is_active")),
                    bool(candidate.get("engine_final_only")), bool(candidate.get("can_enact")),
                    emptyText(candidate.get("blocked_reason")), costs));
        }
        List<Balance> balances = new ArrayList<>();
        for (JsonNode item : array(row.get("resources"))) {
            ObjectNode balance = StrictJson.object(item, Set.of("currency_key", "amount_raw"));
            balances.add(new Balance(currency(balance), integer(balance.get("amount_raw"))));
        }
        TitleSuccessors titles = readTitleSuccessors(row.get("title_successors"));
        return new ObservationFields(bool(row.get("available")),bool(row.get("paused")),
                StrictJson.text(row.get("group_key")),StrictJson.text(row.get("active_law_key")),candidates,balances,titles);
    }
    private static TitleSuccessors readTitleSuccessors(JsonNode value) {
        ObjectNode titles = StrictJson.object(value, Set.of("primary_title_id", "held_titles"));
        List<HeldTitle> held = new ArrayList<>();
        for (JsonNode item : array(titles.get("held_titles"))) {
            ObjectNode title = StrictJson.object(item, Set.of("title_id", "primary", "successor_character_ids"));
            List<BigInteger> successors = new ArrayList<>();
            for (JsonNode successor : array(title.get("successor_character_ids"))) { successors.add(integer(successor)); }
            held.add(new HeldTitle(integer(title.get("title_id")), bool(title.get("primary")), successors));
        }
        return new TitleSuccessors(integer(titles.get("primary_title_id")),held);
    }
    private static void writeCollections(ObjectNode row,List<Balance> balances,List<Candidate> candidates,
            TitleSuccessors titleSuccessors) {
        ArrayNode resources = row.putArray("resources");
        for (Balance balance : balances) {
            resources.addObject().put("currency_key", balance.currency().wire()).put("amount_raw", balance.amountRaw());
        }
        ArrayNode candidateRows = row.putArray("candidates");
        for (Candidate candidate : candidates) {
            ObjectNode item = candidateRows.addObject().put("law_key", candidate.lawKey()).put("is_active", candidate.active())
                    .put("engine_final_only", candidate.engineFinalOnly()).put("can_enact", candidate.canEnact())
                    .put("blocked_reason", candidate.blockedReason());
            ArrayNode costs = item.putArray("costs");
            for (Cost cost : candidate.costs()) {
                costs.addObject().put("currency_key", cost.currency().wire()).put("cost_raw", cost.costRaw());
            }
        }
        writeTitleSuccessors(row.putObject("title_successors"), titleSuccessors);
    }
    private static void writeTitleSuccessors(ObjectNode titles,TitleSuccessors value) {
        titles.put("primary_title_id", value.primaryTitleId());
        ArrayNode held = titles.putArray("held_titles");
        for (HeldTitle title : value.heldTitles()) {
            ObjectNode item = held.addObject().put("title_id", title.titleId()).put("primary", title.primary());
            ArrayNode successors = item.putArray("successor_character_ids");
            title.successorCharacterIds().forEach(successors::add);
        }
    }
}
