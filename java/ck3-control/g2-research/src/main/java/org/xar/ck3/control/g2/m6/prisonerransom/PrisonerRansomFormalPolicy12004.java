package org.xar.ck3.control.g2.m6.prisonerransom;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.AvailableQuote;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Candidate;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Catalog;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Explanation;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003.MeasuredChildRelation;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003.MeasuredLineage;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003.MeasuredTitleTier;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

/** Read-only Java continuation of the existing formal offer selection and final refresh. */
public final class PrisonerRansomFormalPolicy12004 {
    private PrisonerRansomFormalPolicy12004() { }

    public record Frame(BigInteger publicRevision, BigInteger nativeRevision, int dateRaw,
                        long playerCharacterId, List<Long> activeWarIds) {
        public Frame {
            ReleasePreviewValues12003.unsigned64(publicRevision, "public revision");
            ReleasePreviewValues12003.unsigned64(nativeRevision, "native revision");
            StrictJson.require(dateRaw > 0, "formal paused frame date must be positive");
            id(playerCharacterId); activeWarIds = List.copyOf(activeWarIds);
            StrictJson.require(activeWarIds.size() <= 64, "bounded active wars required");
            Set<Long> seen = new HashSet<>();
            for (long war : activeWarIds) { id(war); StrictJson.require(seen.add(war), "duplicate active war"); }
        }
        public FrameBinding binding(long prisonerId) {
            return new FrameBinding(nativeRevision, dateRaw, playerCharacterId, prisonerId);
        }
    }

    public record CollectionRead(Frame frame, int selectedOrdinal, Explanation explanation) {
        public CollectionRead {
            Objects.requireNonNull(frame); Objects.requireNonNull(explanation);
            StrictJson.require(explanation.nativeWireRevision().equals(frame.nativeRevision())
                    && explanation.publicPlanningRevision().equals(frame.publicRevision()), "collection frame differs");
            StrictJson.require(selectedOrdinal >= 0 && selectedOrdinal < explanation.candidates().size(),
                    "selected prisoner must exist");
            for (int index = 0; index < explanation.candidates().size(); index++) {
                Candidate candidate = explanation.candidates().get(index);
                StrictJson.require((candidate.ransomGate() == PrisonerVanillaResearch.Gate.NOT_EVALUATED)
                        != (index == selectedOrdinal), "only selected quote may be evaluated");
                if (candidate.ransomQuote() instanceof AvailableQuote quote) {
                    StrictJson.require(quote.frame().equals(frame.binding(candidate.prisonerCharacterId())),
                            "quote frame differs from formal observation");
                }
            }
        }
    }

    public sealed interface WarRetention permits KnownWarRetention, UnavailableWarRetention { long warId(); }
    public record KnownWarRetention(long warId, Frame frame, List<Long> retainedPrisonerIds,
                                    String originalSha256) implements WarRetention {
        public KnownWarRetention {
            id(warId); Objects.requireNonNull(frame); retainedPrisonerIds = List.copyOf(retainedPrisonerIds);
            retainedPrisonerIds.forEach(PrisonerRansomFormalPolicy12004::id); digest(originalSha256);
        }
    }
    public record UnavailableWarRetention(long warId, String reason, String originalSha256) implements WarRetention {
        public UnavailableWarRetention { id(warId); StrictJson.text(reason); digest(originalSha256); }
    }

    public enum Reason { INCOMPLETE_COLLECTION_READS, COLLECTION_IDENTITY_DRIFT, WAR_RETENTION_UNAVAILABLE,
        QUOTE_CHANGED_BEFORE_SUBMIT, SOURCE_PROVIDER_UNAVAILABLE }
    public sealed interface Decision permits Selected, NoEligibleOffer, Unavailable { }
    public record Choice(int sourceOrdinal, long prisonerCharacterId, long payerCharacterId,
                         PrisonerVanillaResearch.Option option, long quotedGoldRaw,
                         boolean amountIsAcceptanceTimeQuote, String collectionSha256,
                         BigInteger proofEpoch) {
        public Choice {
            StrictJson.require(sourceOrdinal >= 0 && sourceOrdinal <= 63, "bounded ordinal required");
            id(prisonerCharacterId); id(payerCharacterId); Objects.requireNonNull(option); digest(collectionSha256);
            StrictJson.require(quotedGoldRaw > 0 && amountIsAcceptanceTimeQuote
                    == (option == PrisonerVanillaResearch.Option.CURRENT_GOLD), "quote timing differs");
            ReleasePreviewValues12003.unsigned64(proofEpoch, "quote epoch");
        }
    }
    public record Selected(Frame frame, Choice choice) implements Decision {
        public Selected { Objects.requireNonNull(frame); Objects.requireNonNull(choice); }
    }
    public record NoEligibleOffer() implements Decision { }
    public record Unavailable(Reason reason) implements Decision { public Unavailable { Objects.requireNonNull(reason); } }

    /** The shared strict collection and ordinary quote reader validates original bytes before policy. */
    public static CollectionRead read(byte[] original, Frame frame, long selectedPrisonerId, Catalog catalog) {
        Objects.requireNonNull(frame); id(selectedPrisonerId);
        JsonNode collection = StrictJson.parse(original, ReleaseCollectionProjection12003.MAX_BYTES).path("player_prisoner_collection");
        StrictJson.integer(collection.get("played_dynasty_id"), BigInteger.ONE, StrictJson.UINT64_MAX);
        Explanation explanation = PrisonerVanillaResearch.explain(original,
                ReleaseCollectionProjection12003.SupportedBuild.CK3_12004,
                frame.binding(selectedPrisonerId), frame.publicRevision(), catalog);
        for (Candidate candidate : explanation.candidates()) {
            if (candidate.ransomGate() != PrisonerVanillaResearch.Gate.NOT_EVALUATED) {
                return new CollectionRead(frame, candidate.sourceOrdinal(), explanation);
            }
        }
        throw new IllegalArgumentException("complete empty collection has no formal quote read");
    }

    /** Existing native war proof projection; incomplete coverage is unavailable, never an empty retention set. */
    public static WarRetention readWar(byte[] original, Frame frame, long expectedWarId) {
        Objects.requireNonNull(frame); id(expectedWarId);
        String sha = PrisonerVanillaResearch.sha256(original);
        JsonNode envelope = StrictJson.parse(original, ReleaseCollectionProjection12003.MAX_BYTES);
        StrictJson.require(envelope.isObject(), "war read object required");
        JsonNode proof = envelope.get("war_prisoner_release_pairs_v1");
        if (proof == null || !proof.isObject()) return new UnavailableWarRetention(expectedWarId, "missing_original_native_observation", sha);
        if (!textEqual(envelope.get("step"), "query-war-prisoner-release-pairs-v1-" + expectedWarId)
                || !textEqual(envelope.get("status"), "available") || !actualTrue(envelope.get("accepted"))
                || !actualTrue(envelope.get("read_only")) || !textEqual(envelope.get("backend_id"), "native-headless")
                || !integerEqual(envelope.get("snapshot_revision"), frame.nativeRevision())
                || !integerEqual(proof.get("war_id"), BigInteger.valueOf(expectedWarId))
                || !integerEqual(proof.get("date_raw"), BigInteger.valueOf(frame.dateRaw()))
                || !actualTrue(proof.get("same_frame_stable")) || !actualTrue(proof.get("full_participant_scan"))
                || !actualTrue(proof.get("primary_and_first_three_successors_scanned"))) {
            return new UnavailableWarRetention(expectedWarId, "incomplete_or_different_native_frame", sha);
        }
        StrictJson.integer(envelope.get("query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX);
        StrictJson.integer(proof.get("active_casus_belli_database_index"), 0, Integer.MAX_VALUE);
        String cb = StrictJson.text(proof.get("active_casus_belli_key"));
        if (cb.equals("fp3_free_house_member_cb")) return new UnavailableWarRetention(expectedWarId, "free_house_member_retention", sha);
        long attacker = nativeId(proof.get("primary_attacker_character_id"));
        long defender = nativeId(proof.get("primary_defender_character_id"));
        List<Long> attackers = ids(proof.get("attacker_participant_ids"));
        List<Long> defenders = ids(proof.get("defender_participant_ids"));
        List<Long> attackerCandidates = ids(proof.get("attacker_release_candidate_ids"));
        List<Long> defenderCandidates = ids(proof.get("defender_release_candidate_ids"));
        StrictJson.require(attackers.contains(attacker) && defenders.contains(defender)
                && !attackerCandidates.isEmpty() && attackerCandidates.getFirst() == attacker
                && !defenderCandidates.isEmpty() && defenderCandidates.getFirst() == defender
                && attackerCandidates.size() <= 4 && defenderCandidates.size() <= 4
                && java.util.Collections.disjoint(attackers, defenders), "native participant/successor scan contradicts source");
        List<Long> retained = new ArrayList<>(attackerCandidates); retained.addAll(defenderCandidates);
        JsonNode pairs = proof.get("release_pairs");
        StrictJson.require(pairs != null && pairs.isArray() && pairs.size() <= 4096, "bounded native release pairs required");
        Set<String> seenPairs = new HashSet<>();
        for (JsonNode pair : pairs) {
            StrictJson.require(pair.isObject(), "native release pair object required");
            long jailer = nativeId(pair.get("jailer_character_id"));
            long prisoner = nativeId(pair.get("prisoner_character_id"));
            StrictJson.require(seenPairs.add(jailer + ":" + prisoner)
                    && (attackers.contains(jailer) && defenderCandidates.contains(prisoner)
                    || defenders.contains(jailer) && attackerCandidates.contains(prisoner))
                    && pair.get("reason") != null && pair.get("reason").isTextual(), "native release pair contradicts complete scan");
            retained.add(prisoner);
        }
        if (envelope.has("war_prisoner_release_pairs_proof")) StrictJson.require(
                proof.equals(envelope.get("war_prisoner_release_pairs_proof")), "normalized proof differs from original native observation");
        return new KnownWarRetention(expectedWarId, frame, retained, sha);
    }

    public static Decision select(Frame frame, List<CollectionRead> reads, List<WarRetention> warReads) {
        Objects.requireNonNull(frame); reads = List.copyOf(reads); warReads = List.copyOf(warReads);
        if (reads.isEmpty()) return new Unavailable(Reason.INCOMPLETE_COLLECTION_READS);
        List<Candidate> baseline = reads.getFirst().explanation().candidates();
        if (reads.size() != baseline.size()) return new Unavailable(Reason.INCOMPLETE_COLLECTION_READS);
        for (int index = 0; index < reads.size(); index++) {
            CollectionRead read = reads.get(index);
            if (!read.frame().equals(frame) || read.selectedOrdinal() != index
                    || read.explanation().candidates().size() != baseline.size()
                    || !read.explanation().source().equals(reads.getFirst().explanation().source())) {
                return new Unavailable(Reason.COLLECTION_IDENTITY_DRIFT);
            }
            for (int ordinal = 0; ordinal < baseline.size(); ordinal++) {
                if (read.explanation().candidates().get(ordinal).prisonerCharacterId()
                        != baseline.get(ordinal).prisonerCharacterId()) return new Unavailable(Reason.COLLECTION_IDENTITY_DRIFT);
            }
        }
        Set<Long> retained = new HashSet<>();
        if (frame.activeWarIds().size() != warReads.size()) return new Unavailable(Reason.WAR_RETENTION_UNAVAILABLE);
        for (int index = 0; index < warReads.size(); index++) {
            WarRetention read = warReads.get(index);
            if (!(read instanceof KnownWarRetention known) || read.warId() != frame.activeWarIds().get(index)
                    || !known.frame().equals(frame)) return new Unavailable(Reason.WAR_RETENTION_UNAVAILABLE);
            retained.addAll(known.retainedPrisonerIds());
        }
        Choice best = null;
        for (CollectionRead read : reads) {
            Candidate candidate = read.explanation().candidates().get(read.selectedOrdinal());
            var row = candidate.originalProjection();
            if (!(candidate.ransomQuote() instanceof AvailableQuote quote) || !quote.wouldAcceptNow()
                    || !(row.lineage() instanceof MeasuredLineage lineage) || lineage.sameDynasty()
                    || !(row.childRelation() instanceof MeasuredChildRelation child) || child.childOfPlayedCharacter()
                    || !(row.primaryTitleTier() instanceof MeasuredTitleTier tier) || tier.raw() != null && tier.raw() != 1
                    || retained.contains(candidate.prisonerCharacterId())) continue;
            Choice choice = new Choice(candidate.sourceOrdinal(), candidate.prisonerCharacterId(), quote.payerCharacterId(),
                    quote.option(), quote.quotedGoldRaw(), quote.amountIsAcceptanceTimeQuote(),
                    read.explanation().originalCollectionSha256(), quote.proofEpoch());
            if (best == null || choice.quotedGoldRaw() > best.quotedGoldRaw()
                    || choice.quotedGoldRaw() == best.quotedGoldRaw() && choice.prisonerCharacterId() < best.prisonerCharacterId()) best = choice;
        }
        return best == null ? new NoEligibleOffer() : new Selected(frame, best);
    }

    /** A changed offer never becomes a replacement submit request. Caller retains the original pending fence. */
    public static Decision refresh(Selected planned, List<CollectionRead> originalReads, CollectionRead latest,
                                   List<WarRetention> warReads) {
        Objects.requireNonNull(planned); Objects.requireNonNull(latest);
        List<CollectionRead> updated = new ArrayList<>(originalReads);
        if (!latest.frame().equals(planned.frame()) || latest.selectedOrdinal() != planned.choice().sourceOrdinal()
                || latest.selectedOrdinal() >= updated.size()) return new Unavailable(Reason.QUOTE_CHANGED_BEFORE_SUBMIT);
        updated.set(latest.selectedOrdinal(), latest);
        Decision current = select(planned.frame(), updated, warReads);
        if (!(current instanceof Selected selected) || !sameOffer(planned.choice(), selected.choice())) {
            return new Unavailable(Reason.QUOTE_CHANGED_BEFORE_SUBMIT);
        }
        return selected;
    }

    private static boolean sameOffer(Choice left, Choice right) {
        return left.sourceOrdinal() == right.sourceOrdinal() && left.prisonerCharacterId() == right.prisonerCharacterId()
                && left.payerCharacterId() == right.payerCharacterId() && left.option() == right.option()
                && left.quotedGoldRaw() == right.quotedGoldRaw()
                && left.amountIsAcceptanceTimeQuote() == right.amountIsAcceptanceTimeQuote();
    }
    private static boolean integerEqual(JsonNode value, BigInteger expected) {
        return value != null && value.isIntegralNumber() && value.bigIntegerValue().equals(expected);
    }
    private static boolean actualTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static boolean textEqual(JsonNode value, String expected) { return value != null && value.isTextual() && expected.equals(value.textValue()); }
    private static List<Long> ids(JsonNode rows) {
        StrictJson.require(rows != null && rows.isArray() && rows.size() <= 4096, "bounded native retention IDs required");
        List<Long> result = new ArrayList<>(); Set<Long> seen = new HashSet<>();
        for (JsonNode value : rows) {
            long id = nativeId(value); StrictJson.require(seen.add(id), "native retention full ID duplicated"); result.add(id);
        }
        return List.copyOf(result);
    }
    private static long nativeId(JsonNode value) { return StrictJson.integer(value, 1, 0xffff_fffeL); }
    private static void id(long value) { StrictJson.require(value > 0 && value < ReleasePreviewValues12003.UINT32_MAX, "valid full uint32 ID required"); }
    private static void digest(String value) { StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "canonical SHA required"); }
}
