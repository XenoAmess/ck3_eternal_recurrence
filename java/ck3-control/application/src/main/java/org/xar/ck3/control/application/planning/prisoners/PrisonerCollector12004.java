package org.xar.ck3.control.application.planning.prisoners;

import static org.xar.ck3.control.application.planning.prisoners.PrisonerPlanningPorts.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.*;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.*;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003.*;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.*;

/** Ransom gathers every ordinal. Release preserves actual latest-per-ordinal history and authored terms. */
public final class PrisonerCollector12004 {
    public record Entry(RawJson original, CollectionQuery query, Observation collection, Optional<ExactRef> archivedRead) {
        public Entry { Objects.requireNonNull(original); Objects.requireNonNull(query); Objects.requireNonNull(collection); Objects.requireNonNull(archivedRead);
            archivedRead.ifPresent(reference -> StrictJson.require(reference.bytes() > 0, "actual archived read reference required")); }
    }
    public sealed interface Result permits Collected, Empty, Unavailable { }
    public record Collected(Frame frame, List<Entry> entries, List<WarRetention> wars, List<ExactRef> originalReads) implements Result {
        public Collected { Objects.requireNonNull(frame); entries = List.copyOf(entries); wars = List.copyOf(wars); originalReads = List.copyOf(originalReads);
            StrictJson.require(!entries.isEmpty() && entries.size() <= 64, "bounded actual selected collection reads required");
            StrictJson.require(entries.stream().map(value -> value.collection().selectedOrdinal()).distinct().count() == entries.size(), "distinct selected ordinals required"); }
    }
    public record Empty() implements Result { }
    public record Unavailable(String reason) implements Result { public Unavailable { StrictJson.text(reason); } }
    private final Bindings bindings;
    public PrisonerCollector12004(Bindings bindings) { this.bindings = Objects.requireNonNull(bindings); }

    /** Compatibility name continues to mean the original complete ordinary-ransom collection. */
    public Result collect(PlanningRequest request) { return collectRansom(request); }
    public Result collectRansom(PlanningRequest request) {
        try {
            Frame frame = frame(request); List<ExactRef> originals = new ArrayList<>();
            List<WarRetention> wars = wars(request, frame, originals);
            Entry first = collection(request, frame, bindings.queries().collection(0, new PrisonerOptionIntent.Unconditional()));
            if (first == null) return new Empty();
            List<Entry> entries = new ArrayList<>(); entries.add(first); originals.add(first.archivedRead().orElseThrow());
            for (int ordinal = 1; ordinal < first.collection().rows().size(); ordinal++) {
                Entry next = collection(request, frame, bindings.queries().collection(ordinal, new PrisonerOptionIntent.Unconditional()));
                StrictJson.require(next != null && sameRows(first, next), "collection identities changed during complete reads");
                entries.add(next); originals.add(next.archivedRead().orElseThrow());
            }
            return new Collected(frame, entries, wars, originals);
        } catch (IllegalArgumentException | ArithmeticException rejected) { return new Unavailable(diagnostic(rejected)); }
    }
    /** The producer history is chronological; pop/reinsert gives the same distinct-ordinal order as Python. */
    public Result collectRelease(PlanningRequest request) {
        try {
            Frame frame = frame(request); List<Entry> entries = retainedReleaseEntries(request, frame);
            if (entries.isEmpty()) return new Empty();
            List<ExactRef> originals = new ArrayList<>();
            return new Collected(frame, entries, wars(request, frame, originals), originals);
        } catch (IllegalArgumentException | ArithmeticException rejected) { return new Unavailable(diagnostic(rejected)); }
    }
    public Entry refresh(PlanningRequest request, Collected collected, int ordinal) {
        Entry selected = collected.entries().stream().filter(entry -> entry.collection().selectedOrdinal() == ordinal).findFirst().orElseThrow();
        Entry latest = collection(request, collected.frame(), selected.query());
        StrictJson.require(latest != null && sameRows(selected, latest), "selected prisoner identity/intent changed");
        return latest;
    }
    public List<CollectionRead> ransomReads(Collected collected) {
        var catalog = bindings.catalog().orElseThrow(() -> new IllegalArgumentException("exact stock Catalog unavailable"));
        List<CollectionRead> result = new ArrayList<>();
        for (Entry entry : collected.entries()) result.add(PrisonerRansomFormalPolicy12004.read(entry.original().bytes(),
                collected.frame(), selected(entry).prisonerCharacterId(), catalog));
        return List.copyOf(result);
    }
    public CollectionRead ransomRead(Frame frame, Entry entry) {
        return PrisonerRansomFormalPolicy12004.read(entry.original().bytes(), frame, selected(entry).prisonerCharacterId(),
                bindings.catalog().orElseThrow(() -> new IllegalArgumentException("exact stock Catalog unavailable")));
    }
    public static Row selected(Entry entry) { return entry.collection().rows().get(entry.collection().selectedOrdinal()); }
    public static boolean retained(Collected all, long prisoner) {
        if (all.frame().activeWarIds().size() != all.wars().size()) return true;
        for (int index = 0; index < all.wars().size(); index++) {
            WarRetention war = all.wars().get(index);
            if (!(war instanceof KnownWarRetention known) || known.warId() != all.frame().activeWarIds().get(index)
                    || !known.frame().equals(all.frame()) || known.retainedPrisonerIds().contains(prisoner)) return true;
        }
        return false;
    }
    public static boolean acceptedRelease(Entry entry, Frame frame) {
        Row row = selected(entry);
        if (entry.query().mask() == 0) return row.preview() instanceof ReleasePreview12003.Available value && value.canSend();
        JsonNode wire = StrictJson.parse(entry.original().bytes(), ReleaseCollectionProjection12003.MAX_BYTES)
                .path("player_prisoner_collection").path("prisoners").get(entry.collection().selectedOrdinal()).get("negotiated_release_preview");
        var preview = NegotiatedPreviewCodec.decode(wire, frame.binding(row.prisonerCharacterId()), entry.query().mask());
        if (!(preview instanceof NegotiatedPreview12003.Available value) || !value.proofEpoch().equals(entry.collection().proofEpoch()) || !value.canSend()) return false;
        return value.acceptance() instanceof NegotiatedPreview12003.AutoAccept
                || value.acceptance() instanceof NegotiatedPreview12003.NativeAnswer answer && answer.wouldAcceptNow();
    }
    public static boolean positiveRansomPriority(Entry entry, Frame frame) {
        Row row = selected(entry);
        if (!(row.lineage() instanceof MeasuredLineage lineage) || lineage.sameDynasty()
                || !(row.childRelation() instanceof MeasuredChildRelation child) || child.childOfPlayedCharacter()
                || !(row.primaryTitleTier() instanceof MeasuredTitleTier tier) || tier.raw() != null && tier.raw() != 1) return false;
        JsonNode quote = StrictJson.parse(entry.original().bytes(), ReleaseCollectionProjection12003.MAX_BYTES)
                .path("player_prisoner_collection").path("prisoners").get(row.sourceOrdinal()).get("ransom_quote_preview");
        return PrisonerVanillaResearch.readQuote(quote, frame.binding(row.prisonerCharacterId()), entry.collection().proofEpoch())
                instanceof PrisonerVanillaResearch.AvailableQuote value && value.wouldAcceptNow();
    }
    /** New release selection must distinguish an unreadable ransom from an observed absence of an offer.
     * The legacy predicate remains unchanged for preparation/reconciliation of already submitted commands. */
    public static boolean positiveRansomPriorityForRelease(Entry entry, Frame frame) {
        Row row = selected(entry);
        if (!(row.lineage() instanceof MeasuredLineage lineage) || lineage.sameDynasty()
                || !(row.childRelation() instanceof MeasuredChildRelation child) || child.childOfPlayedCharacter()
                || !(row.primaryTitleTier() instanceof MeasuredTitleTier tier) || tier.raw() != null && tier.raw() != 1) return false;
        JsonNode quote = StrictJson.parse(entry.original().bytes(), ReleaseCollectionProjection12003.MAX_BYTES)
                .path("player_prisoner_collection").path("prisoners").get(row.sourceOrdinal()).get("ransom_quote_preview");
        var result = PrisonerVanillaResearch.readQuote(quote, frame.binding(row.prisonerCharacterId()), entry.collection().proofEpoch());
        if (result instanceof PrisonerVanillaResearch.AvailableQuote value) return value.wouldAcceptNow();
        String reason = ((PrisonerVanillaResearch.UnavailableQuote) result).reason();
        if (reason.equals("final_can_send_false") || reason.equals("extortionate_final_can_send_false")
                || reason.equals("payer_below_one_gold")) return false;
        throw new IllegalArgumentException("ransom priority is unobserved: " + reason);
    }
    public boolean retainedReleaseReady(PlanningRequest request) {
        if (request.observations().warInProgress()) return false;
        try {
            Frame frame = frame(request);
            for (Entry entry : retainedReleaseEntries(request, frame))
                if (acceptedRelease(entry, frame) && !positiveRansomPriorityForRelease(entry, frame)) return true;
            return false;
        } catch (IllegalArgumentException | ArithmeticException rejected) { return false; }
    }
    /** Exposes the exact retained selection order for consumers and real regression cases. */
    public List<Entry> retainedReleaseEntries(PlanningRequest request, Frame frame) {
        var selected = new LinkedHashMap<Integer, Entry>();
        for (OpportunityJson.Obj history : request.observations().history()) {
            if (!(history.get("ok") instanceof OpportunityJson.Bool ok) || !ok.value()
                    || !(history.get("command") instanceof OpportunityJson.Text command)
                    || !(history.get("result") instanceof OpportunityJson.Obj result)) continue;
            int ordinal = ordinal(command.value()); if (ordinal < 0) continue;
            JsonNode wire = StrictJson.parse(OpportunityJson.encode(result), ReleaseCollectionProjection12003.MAX_BYTES);
            if (!current(wire, request, frame)) continue;
            // The latest current original supersedes an earlier original even when its offer is unavailable/malformed.
            selected.remove(ordinal);
            JsonNode rows = wire.path("player_prisoner_collection").get("prisoners");
            StrictJson.require(rows != null && rows.isArray(), "retained current prisoner rows absent");
            if (rows.isEmpty()) { StrictJson.require(ordinal == 0, "retained selected ordinal absent"); continue; }
            StrictJson.require(ordinal < rows.size(), "retained selected ordinal absent");
            long prisoner = StrictJson.integer(rows.get(ordinal).get("prisoner_character_id"), 1, 0xfffffffeL);
            StrictJson.require(collectionStep(ordinal).equals(StrictJson.text(wire.get("step"))), "history command differs from returned selected ordinal");
            ObjectNode args = StrictJson.object();
            boolean keys = wire.has("queried_release_option_keys"), mask = wire.has("queried_release_option_mask_bits");
            StrictJson.require(keys == mask, "retained release intent fields must appear together");
            if (keys) args.set("release_option_keys", wire.get("queried_release_option_keys"));
            if (wire.has("queried_release_material_target_character_id"))
                args.set("release_material_target_character_id", wire.get("queried_release_material_target_character_id"));
            PrisonerOptionIntent.Arguments intent = PrisonerOptionIntent.decode(args);
            CollectionQuery query = bindings.queries().collection(ordinal, intent);
            if (keys) StrictJson.integer(wire.get("queried_release_option_mask_bits"), query.mask(), query.mask());
            RawJson original = new RawJson(OpportunityJson.encode(result));
            selected.put(ordinal, new Entry(original, query, ReleaseCollectionProjection12003.decode(original.bytes(),
                    SupportedBuild.CK3_12004, frame.binding(prisoner)), Optional.empty()));
        }
        return List.copyOf(selected.values());
    }
    private List<WarRetention> wars(PlanningRequest request, Frame frame, List<ExactRef> originals) {
        List<WarRetention> result = new ArrayList<>();
        for (long war : frame.activeWarIds()) {
            ReadContract<RawJson> contract = bindings.queries().wars().get(war);
            StrictJson.require(contract != null, "active war exact read contract absent");
            var original = read(request, contract, EMPTY); originals.add(original.originalReceipt());
            result.add(PrisonerRansomFormalPolicy12004.readWar(original.value().bytes(), frame, war));
        }
        return List.copyOf(result);
    }
    private Entry collection(PlanningRequest request, Frame frame, CollectionQuery query) {
        var known = read(request, query.contract(), query.arguments()); RawJson original = known.value();
        JsonNode wire = StrictJson.parse(original.bytes(), ReleaseCollectionProjection12003.MAX_BYTES);
        JsonNode rows = wire.path("player_prisoner_collection").get("prisoners");
        StrictJson.require(rows != null && rows.isArray() && rows.size() <= 64, "bounded current prisoner rows required");
        int ordinal = ordinal(query.contract().operation().value());
        if (rows.isEmpty()) {
            JsonNode empty = wire.get("player_prisoner_collection");
            StrictJson.require(ordinal == 0 && "available".equals(wire.path("status").textValue())
                    && "available".equals(empty.path("status").textValue()), "collection is unavailable, not empty");
            for (String key : List.of("accepted", "private_build", "read_only")) StrictJson.trueValue(wire.get(key));
            StrictJson.require(wire.path("advertised").isBoolean() && !wire.path("advertised").booleanValue()
                    && "native-headless".equals(wire.path("backend_id").textValue()), "empty native collection flags differ");
            StrictJson.trueValue(empty.get("collection_complete"));
            StrictJson.integer(empty.get("total_count"), 0, 0); StrictJson.integer(empty.get("returned_count"), 0, 0);
            StrictJson.integer(wire.get("snapshot_revision"), frame.nativeRevision(), frame.nativeRevision());
            StrictJson.integer(empty.get("snapshot_revision"), frame.nativeRevision(), frame.nativeRevision());
            StrictJson.integer(empty.get("date_raw"), frame.dateRaw(), frame.dateRaw());
            StrictJson.integer(empty.get("played_character_id"), frame.playerCharacterId(), frame.playerCharacterId());
            return null;
        }
        StrictJson.require(ordinal >= 0 && ordinal < rows.size(), "queried ordinal absent");
        long prisoner = StrictJson.integer(rows.get(ordinal).get("prisoner_character_id"), 1, 0xfffffffeL);
        Observation projection = ReleaseCollectionProjection12003.decode(original.bytes(), SupportedBuild.CK3_12004, frame.binding(prisoner));
        StrictJson.require(projection.selectedOrdinal() == ordinal, "query selected another ordinal");
        return new Entry(original, query, projection, Optional.of(known.originalReceipt()));
    }
    private PlanningReadResult.Known<RawJson> read(PlanningRequest request, ReadContract<RawJson> contract, OpportunityJson.Obj arguments) {
        PlanningReadResult<RawJson> result = bindings.reads().read(contract, request(request, contract, arguments));
        if (!(result instanceof PlanningReadResult.Known<RawJson> known)) throw new IllegalArgumentException(((PlanningReadResult.Unavailable<RawJson>) result).reason());
        StrictJson.require(known.receipt().request().equals(request(request, contract, arguments))
                && known.receipt().contractId().equals(contract.contractId()) && known.originalReceipt().bytes() > 0,
                "shared read crossed its exact planner request or lacks durable original");
        return known;
    }
    public static Frame frame(PlanningRequest request) {
        var nativeFrame = request.before().frame().identity(); List<Long> wars = new ArrayList<>();
        for (var item : OpportunityJson.array(request.observations().snapshot().get("active_wars"), "active_wars"))
            wars.add(OpportunityJson.integer(OpportunityJson.object(item, "war").get("war_id"), "war_id").longValueExact());
        StrictJson.require(request.source().exactBuild().equals("1.20.0.4@sha256:" + PrisonerVanillaResearch.EXE_SHA256), "current exact .4 source required");
        return new Frame(request.before().frame().revision(), nativeFrame.nativeRevision(), nativeFrame.dateRaw().intValueExact(), nativeFrame.player().longValueExact(), wars);
    }
    private static boolean sameRows(Entry before, Entry after) {
        if (before.collection().rows().size() != after.collection().rows().size()) return false;
        for (int index = 0; index < before.collection().rows().size(); index++)
            if (before.collection().rows().get(index).prisonerCharacterId() != after.collection().rows().get(index).prisonerCharacterId()) return false;
        return before.query().intent().equals(after.query().intent());
    }
    private static boolean current(JsonNode wire, PlanningRequest request, Frame frame) {
        return wire.path("queried_snapshot_id").isTextual() && wire.path("queried_snapshot_id").textValue().equals(request.before().frame().snapshotId())
                && equalInteger(wire.get("queried_revision"), frame.publicRevision()) && equalInteger(wire.get("snapshot_revision"), frame.nativeRevision());
    }
    private static boolean equalInteger(JsonNode value, BigInteger expected) { return value != null && value.isIntegralNumber() && value.bigIntegerValue().equals(expected); }
    private static int ordinal(String step) {
        for (int index = 0; index < 64; index++) if (collectionStep(index).equals(step)) return index;
        return -1;
    }
    private static String diagnostic(RuntimeException failure) {
        String reason = failure.getMessage() == null ? failure.getClass().getSimpleName() : failure.getMessage();
        return reason.substring(0, Math.min(reason.length(), 1024));
    }
}
