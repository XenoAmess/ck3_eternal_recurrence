package org.xar.ck3.control.nativebridge.capabilities.family;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.AvailableQuote;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.RansomQuote;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.*;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.*;

/** One fixed registered contract for each actual ordinal. Options/retained target are checked arguments, not new routes. */
public final class PrisonerNativeQueries {
    public static final String STEP = "query-player-prisoner-collection-private-v1";
    public static final String PERMISSION = "allow_private_prisoner_collection_query";
    private static final Set<String> ENVELOPE = Set.of("step", "accepted", "status", "query_sequence", "observation_revision",
            "snapshot_revision", "player_prisoner_collection", "private_build", "read_only", "advertised", "backend_id");
    private static final Set<String> VALUE = Set.of("schema", "schema_version", "snapshot_revision", "status", "unavailable_reason",
            "date_raw", "played_character_id", "total_count", "returned_count", "collection_complete", "prisoners");
    private static final Set<String> ROW = Set.of("source_ordinal", "prisoner_character_id", "collection_owner_character_id", "jailer_character_id", "custody_relation_verified");
    @FunctionalInterface public interface Admission { void verify(int ordinal, PlanningReadRequest request, PrisonerOptionIntent.Arguments arguments); }
    public enum CollectionStatus { AVAILABLE, UNAVAILABLE }
    public record Decoded(RawJson normalized, CollectionStatus status, Optional<String> unavailableReason, int schemaVersion, List<Long> prisonerIds,
            Optional<ReleaseCollectionProjection12003.Observation> releaseProjection, List<RansomQuote> ransomQuotes,
            List<NegotiatedPreview12003> negotiatedPreviews, Optional<PrisonerMaterial12004.ReleaseMaterial> releaseMaterial,
            Optional<PrisonerMaterial12004.KeeperOpinion> keeperOpinion, Optional<PrisonerMaterial12004.Custody> retainedCustody) {
        public Decoded { Objects.requireNonNull(normalized); Objects.requireNonNull(status); Objects.requireNonNull(unavailableReason);
            StrictJson.require((status == CollectionStatus.UNAVAILABLE) == unavailableReason.isPresent(), "collection availability/reason mismatch");
            prisonerIds = List.copyOf(prisonerIds); Objects.requireNonNull(releaseProjection);
            ransomQuotes = List.copyOf(ransomQuotes); negotiatedPreviews = List.copyOf(negotiatedPreviews);
            Objects.requireNonNull(releaseMaterial); Objects.requireNonNull(keeperOpinion); Objects.requireNonNull(retainedCustody); }
    }
    private final List<ReadContract<RawJson>> contracts;
    public PrisonerNativeQueries(ExactRef source, Admission admission) {
        Objects.requireNonNull(source); Objects.requireNonNull(admission); List<ReadContract<RawJson>> all = new ArrayList<>();
        for (int ordinal = 0; ordinal < 64; ordinal++) {
            int fixedOrdinal = ordinal; String step = step(ordinal);
            all.add(new ReadContract<>("family/prisoner-collection12004/" + ordinal, new OperationKey(step), Optional.empty(), PERMISSION,
                    ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, source,
                    (request, requestId) -> {
                        PrisonerOptionIntent.Arguments arguments = arguments(request); admission.verify(fixedOrdinal, request, arguments);
                        long actor = request.before().frame().identity().player().longValueExact();
                        arguments.materialTarget().ifPresent(target -> StrictJson.require(target != actor, "material target must differ from current player"));
                        ObjectNode fields = StrictJson.object();
                        if (arguments.options() instanceof PrisonerOptionIntent.Negotiated negotiated) fields.put("release_option_mask_bits", negotiated.mask());
                        arguments.materialTarget().ifPresent(target -> fields.put("release_material_target_character_id", target));
                        return new NativeRequest(step, Optional.empty(), new RawJson(StrictJson.canonical(fields)));
                    }, receipt -> decode(receipt, fixedOrdinal).normalized(),
                    receipt -> decode(receipt, fixedOrdinal).normalized()));
        }
        contracts = List.copyOf(all);
    }
    public List<ReadContract<RawJson>> contracts() { return contracts; }
    public ReadContract<RawJson> contract(int ordinal) { ordinal(ordinal); return contracts.get(ordinal); }
    public static String step(int ordinal) { ordinal(ordinal); return ordinal == 0 ? STEP : STEP + "-ransom-ordinal-" + ordinal; }
    public static OpportunityJson.Obj arguments(PrisonerOptionIntent options, OptionalLong materialTarget) {
        return (OpportunityJson.Obj) OpportunityJson.parse(PrisonerOptionIntent.encode(new PrisonerOptionIntent.Arguments(options, materialTarget)));
    }
    public static Decoded decode(PlanningReadReceipt receipt, int ordinal) {
        ordinal(ordinal); Objects.requireNonNull(receipt); var request = receipt.request(); var identity = request.before().frame().identity();
        for (var g : List.of(receipt.before(), receipt.after())) StrictJson.require(g.paused() && g.mapReady() && g.playerAlive()
                && g.binding().source().equals(request.source()) && g.binding().sessionId().equals(request.sessionId()), "actual prisoner read guard required");
        StrictJson.require(request.operation().value().equals(step(ordinal)) && receipt.original().nativeOk()
                && receipt.original().originalResultToken().isPresent(), "original successful prisoner collection ACK/token required");
        StrictJson.require(receipt.before().binding().observed().equals(request.before()) && receipt.after().binding().observed().equals(request.before())
                && receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()), "prisoner query crossed its actual paused frame");
        StrictJson.require(request.source().exactBuild().equals("1.20.0.4@sha256:" + CachedSuccession12004.EXE_SHA256), "actual current exact .4 source required");
        return decodeNative(receipt.original().originalResultToken().orElseThrow(), ordinal, arguments(request), request.before().frame().snapshotId(),
                request.before().frame().revision(), identity.nativeRevision(), identity.dateRaw().intValueExact(), identity.player().longValueExact());
    }
    public static Decoded decodeNative(RawJson original, int ordinal, PrisonerOptionIntent.Arguments arguments, String snapshotId,
            BigInteger publicRevision, BigInteger nativeRevision, int date, long actor) {
        ordinal(ordinal); Objects.requireNonNull(arguments); StrictJson.text(snapshotId);
        StrictJson.require(actor > 0 && actor < 0xffff_ffffL, "valid player full ID required");
        ObjectNode root = object(StrictJson.parse(original.bytes(), 1_048_576));
        Set<String> envelope = new HashSet<>(ENVELOPE);
        for (String key : List.of("prisoner_selected_quote_source_12004", "prisoner_negotiated_quote_source_12004")) if (root.has(key)) envelope.add(key);
        if (arguments.materialTarget().isPresent()) {
            envelope.add("prisoner_release_material_opinion");
            if (root.has("prisoner_keeper_opinion")) envelope.add("prisoner_keeper_opinion");
            if (root.has("prisoner_retained_target_state")) envelope.add("prisoner_retained_target_state");
        }
        StrictJson.object(root, envelope); text(root, "step", step(ordinal)); yes(root, "accepted"); yes(root, "private_build"); yes(root, "read_only"); no(root, "advertised");
        text(root, "backend_id", "native-headless"); equal(root, "snapshot_revision", nativeRevision);
        BigInteger sequence = u64(root.get("query_sequence")), epoch = u64(root.get("observation_revision"));
        ObjectNode value = object(root.get("player_prisoner_collection")); int schema = (int) StrictJson.integer(value.get("schema_version"), 1, 7);
        Set<String> valueFields = new HashSet<>(VALUE);
        if (schema >= 3) valueFields.addAll(Set.of("played_house_id", "played_dynasty_id"));
        if (schema >= 6) valueFields.add("played_dread_raw");
        StrictJson.object(value, valueFields); text(value, "schema", "player-prisoner-collection-private-v1"); equal(value, "snapshot_revision", nativeRevision);
        String status = StrictJson.text(value.get("status")); text(root, "status", status);
        List<Long> ids = new ArrayList<>(); List<RansomQuote> quotes = new ArrayList<>(); List<NegotiatedPreview12003> negotiated = new ArrayList<>();
        Optional<ReleaseCollectionProjection12003.Observation> projection = Optional.empty();
        boolean requestedOptions = arguments.options() instanceof PrisonerOptionIntent.Negotiated;
        int mask = requestedOptions ? ((PrisonerOptionIntent.Negotiated) arguments.options()).mask() : 0;
        JsonNode rows = value.get("prisoners"); StrictJson.require(rows != null && rows.isArray(), "complete prisoner array required");
        if (status.equals("unavailable")) {
            StrictJson.text(value.get("unavailable_reason")); no(value, "collection_complete");
            nil(value, "date_raw", "played_character_id", "total_count", "returned_count");
            if (schema >= 3) nil(value, "played_house_id", "played_dynasty_id"); if (schema >= 6) nil(value, "played_dread_raw");
            StrictJson.require(rows.isEmpty(), "unavailable collection requires explicit empty rows");
        } else {
            StrictJson.require(status.equals("available"), "unsupported prisoner collection status"); nil(value, "unavailable_reason");
            equal(value, "date_raw", BigInteger.valueOf(date)); equal(value, "played_character_id", BigInteger.valueOf(actor));
            int count = (int) StrictJson.integer(value.get("total_count"), 0, 64); StrictJson.integer(value.get("returned_count"), count, count); yes(value, "collection_complete");
            StrictJson.require(rows.size() == count && (ordinal == 0 || schema >= 4 && ordinal < count)
                    && (!requestedOptions || ordinal < count), "complete rows or requested ordinal absent");
            if (schema >= 3) lineage(value.get("played_house_id"), value.get("played_dynasty_id"));
            if (schema >= 6) StrictJson.integer(value.get("played_dread_raw"), BigInteger.ZERO, StrictJson.UINT64_MAX);
            Set<Long> seen = new HashSet<>();
            for (int index = 0; index < count; index++) {
                JsonNode row = rows.get(index); Set<String> fields = new HashSet<>(ROW);
                if (schema >= 2) fields.add("unconditional_release_preview"); if (schema >= 3) fields.addAll(Set.of("house_id", "dynasty_id", "same_house", "same_dynasty"));
                if (schema >= 4) fields.add("ransom_quote_preview"); if (schema >= 5) fields.add("is_child_of_played_character");
                if (schema >= 6) fields.add("primary_title_tier_raw"); if (schema == 7) fields.add("native_kinship");
                if (requestedOptions) fields.add("negotiated_release_preview"); StrictJson.object(row, fields);
                StrictJson.integer(row.get("source_ordinal"), index, index);
                long prisoner = StrictJson.integer(row.get("prisoner_character_id"), 1, 0xffff_ffffL);
                StrictJson.require(prisoner != actor && seen.add(prisoner), "duplicate/player prisoner identity refused"); ids.add(prisoner);
                StrictJson.integer(row.get("collection_owner_character_id"), actor, actor); StrictJson.integer(row.get("jailer_character_id"), actor, actor); yes(row, "custody_relation_verified");
                FrameBinding frame = new FrameBinding(nativeRevision, date, actor, prisoner);
                if (schema >= 4) {
                    RansomQuote quote = PrisonerVanillaResearch.readQuote(row.get("ransom_quote_preview"), frame, epoch); quotes.add(quote);
                    if (ordinal > 0) StrictJson.require(notEvaluated(quote) != (index == ordinal), "ordinary ransom evaluated another ordinal");
                }
                if (requestedOptions) {
                    NegotiatedPreview12003 preview = NegotiatedPreviewCodec.decode(row.get("negotiated_release_preview"), frame, mask);
                    if (preview instanceof NegotiatedPreview12003.Available available) StrictJson.require(available.proofEpoch().equals(epoch), "negotiated epoch mismatch");
                    boolean notEvaluated = preview instanceof NegotiatedPreview12003.Unavailable unavailable && unavailable.unavailableReason().equals("not_evaluated");
                    StrictJson.require(notEvaluated != (index == ordinal), "negotiated preview evaluated another ordinal"); negotiated.add(preview);
                }
            }
            if (schema >= 2 && count > 0) {
                long selected = ids.get(ordinal);
                projection = Optional.of(ReleaseCollectionProjection12003.decode(original.bytes(), ReleaseCollectionProjection12003.SupportedBuild.CK3_12004,
                        new FrameBinding(nativeRevision, date, actor, selected)));
            }
        }
        ObjectNode normalized = root.deepCopy();
        normalized.put("exact_ck3_build", "1.20.0.4").put("exe_sha256", CachedSuccession12004.EXE_SHA256.toUpperCase(java.util.Locale.ROOT))
                .put("queried_snapshot_id", snapshotId).put("queried_revision", publicRevision).put("queried_native_revision", nativeRevision);
        Optional<PrisonerMaterial12004.ReleaseMaterial> material = Optional.empty(); Optional<PrisonerMaterial12004.KeeperOpinion> keeper = Optional.empty();
        Optional<PrisonerMaterial12004.Custody> custody = Optional.empty();
        if (arguments.materialTarget().isPresent()) {
            long target = arguments.materialTarget().getAsLong(); var frame = new PrisonerMaterial12004.Frame(nativeRevision, date, actor, target);
            material = Optional.of(PrisonerMaterial12004.decodeReleaseMaterial(root.get("prisoner_release_material_opinion"), frame));
            if (root.has("prisoner_keeper_opinion")) keeper = Optional.of(PrisonerMaterial12004.decodeKeeperOpinion(root.get("prisoner_keeper_opinion"), frame));
            if (root.has("prisoner_retained_target_state")) custody = Optional.of(PrisonerMaterial12004.decodeCustody(root.get("prisoner_retained_target_state"), frame));
            normalized.put("queried_release_material_target_character_id", target);
        }
        Optional<NegotiatedSourceCopy12004> negotiatedSource = Optional.empty();
        if (root.has("prisoner_selected_quote_source_12004") || root.has("prisoner_negotiated_quote_source_12004")) {
            StrictJson.require(status.equals("available") && ordinal < ids.size(), "copied quote source lacks a current selected row");
            FrameBinding frame = new FrameBinding(nativeRevision, date, actor, ids.get(ordinal));
            if (root.has("prisoner_selected_quote_source_12004")) {
                StrictJson.require(schema >= 4, "ordinary source lacks its quote"); RansomQuote quote = quotes.get(ordinal);
                Optional<NegotiatedSourceCodec12004.OrdinaryQuoteJoin> join = quote instanceof AvailableQuote available
                        ? Optional.of(new NegotiatedSourceCodec12004.OrdinaryQuoteJoin(available.payerCharacterId(), available.answerStatusRaw(), available.recipientAcceptanceRaw())) : Optional.empty();
                NegotiatedSourceCodec12004.decodeOrdinary(root.get("prisoner_selected_quote_source_12004"),
                        new NegotiatedSourceCodec12004.OrdinaryQuoteBinding(frame, sequence, epoch, ordinal), join);
            }
            if (root.has("prisoner_negotiated_quote_source_12004")) {
                StrictJson.require(requestedOptions, "negotiated copied source has no requested options");
                negotiatedSource = Optional.of(NegotiatedSourceCodec12004.decode(root.get("prisoner_negotiated_quote_source_12004"),
                        new NegotiatedSourceCopy12004.QuoteBinding(frame, sequence, epoch, ordinal, mask)));
            }
        }
        if (requestedOptions) {
            var intent = (PrisonerOptionIntent.Negotiated) arguments.options(); var keys = normalized.putArray("queried_release_option_keys");
            intent.options().forEach(option -> keys.add(option.key())); normalized.put("queried_release_option_mask_bits", mask);
            if (status.equals("available")) {
                var binding = new NegotiatedSourceCopy12004.QuoteBinding(new FrameBinding(nativeRevision, date, actor, ids.get(ordinal)), sequence, epoch, ordinal, mask);
                normalized.set("prisoner_negotiated_quote_result_12004", StrictJson.parse(NegotiatedQuoteResult12004.encode(
                        NegotiatedQuoteResult12004.consume(negotiated.get(ordinal), negotiatedSource, binding)), 1_048_576));
            }
        }
        return new Decoded(new RawJson(StrictJson.canonical(normalized, 1_048_576)), CollectionStatus.valueOf(status.toUpperCase(java.util.Locale.ROOT)),
                status.equals("unavailable") ? Optional.of(StrictJson.text(value.get("unavailable_reason"))) : Optional.empty(),
                schema, ids, projection, quotes, negotiated, material, keeper, custody);
    }
    private static PrisonerOptionIntent.Arguments arguments(PlanningReadRequest request) { return PrisonerOptionIntent.decode(OpportunityJson.encode(request.arguments())); }
    private static boolean notEvaluated(RansomQuote quote) { return quote instanceof PrisonerVanillaResearch.UnavailableQuote unavailable && unavailable.reason().equals("not_evaluated"); }
    private static void ordinal(int value) { StrictJson.require(value >= 0 && value < 64, "ordinal must be 0..63"); }
    private static ObjectNode object(JsonNode value) { StrictJson.require(value instanceof ObjectNode, "actual prisoner JSON object required"); return (ObjectNode) value; }
    private static void text(JsonNode value, String field, String expected) { StrictJson.require(expected.equals(StrictJson.text(value.get(field))), "prisoner native field mismatch: " + field); }
    private static void equal(JsonNode value, String field, BigInteger expected) { StrictJson.integer(value.get(field), expected, expected); }
    private static void yes(JsonNode value, String field) { StrictJson.trueValue(value.get(field)); }
    private static void no(JsonNode value, String field) { JsonNode node = value.get(field); StrictJson.require(node != null && node.isBoolean() && !node.booleanValue(), "actual JSON false required: " + field); }
    private static void nil(JsonNode value, String... fields) { for (String field : fields) StrictJson.require(value.has(field) && value.get(field).isNull(), "explicit null required: " + field); }
    private static BigInteger u64(JsonNode node) { return StrictJson.integer(node, BigInteger.ONE, StrictJson.UINT64_MAX); }
    private static void lineage(JsonNode house, JsonNode dynasty) { StrictJson.require(house != null && dynasty != null, "explicit lineage fields required"); if (!house.isNull()) StrictJson.integer(house, BigInteger.ZERO, StrictJson.UINT64_MAX); if (!dynasty.isNull()) StrictJson.integer(dynasty, BigInteger.ZERO, StrictJson.UINT64_MAX); StrictJson.require(!house.isNull() || dynasty.isNull(), "dynasty requires observed house"); }
}
