package org.xar.ck3.control.g2.m1;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.campaigncadence.CampaignCadenceCodec;
import org.xar.ck3.control.planning.campaigncadence.CampaignCalendar;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifference;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmObservation;
import org.xar.ck3.control.wave2.planning.realmcompare.SubrealmCounties;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedCountyMembership;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipInput;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult;

/** Pure consumers of the existing complete membership producers. No reads or authority issuance. */
public final class M1RealmComparisons {
    private M1RealmComparisons() { }

    public enum CacheStatus {
        CURRENT, FRAME_CHANGED, PROVENANCE_CHANGED, QUERY_SEQUENCE_CHANGED, CONTENT_CHANGED,
        MONTH_CONFIGURATION_CHANGED, NOT_AN_EXACT_MONTH_SLOT
    }
    public enum SavedScope { REALM, DYNASTY }
    public enum Reason {
        PRODUCER_RESULT_CHANGED, OWNER_OR_FOUNDING_ANCHOR_CHANGED, GEOGRAPHY_RULES_CHANGED,
        INCOMPLETE_MEMBERSHIP, DATE_UNAVAILABLE, DATE_NOT_STRICTLY_EARLIER,
        FULL_COMPARISON_UNAVAILABLE, DELTA_DOES_NOT_MATCH_FULL_COMPARISON,
        DELTA_DOES_NOT_RECONSTRUCT_CURRENT_MEMBERSHIP
    }

    /** New cross-language delta identities serialize as decimal strings in the research entry. */
    public record Delta(List<BigInteger> lostTitleIds, List<BigInteger> gainedTitleIds) {
        public Delta {
            lostTitleIds = identities(lostTitleIds); gainedTitleIds = identities(gainedTitleIds);
            StrictJson.require(java.util.Collections.disjoint(lostTitleIds, gainedTitleIds),
                    "lost and gained identities must be disjoint");
        }
    }
    public sealed interface SavedComparison permits SavedChange, SavedUnavailable { }
    public record SavedChange(SavedScope scope, Delta delta, String beforeSourceRef, String afterSourceRef,
            String beforeDate, String afterDate) implements SavedComparison {
        public SavedChange {
            Objects.requireNonNull(scope); Objects.requireNonNull(delta);
            StrictJson.text(beforeSourceRef); StrictJson.text(afterSourceRef);
            CampaignCalendar.parse(beforeDate); CampaignCalendar.parse(afterDate);
        }
    }
    public record SavedUnavailable(Reason reason) implements SavedComparison {
        public SavedUnavailable { Objects.requireNonNull(reason); }
    }
    public sealed interface IncrementalVerification permits VerifiedIncremental, RejectedIncremental { }
    public record VerifiedIncremental(Delta fullDelta, List<BigInteger> reconstructedMembership)
            implements IncrementalVerification {
        public VerifiedIncremental {
            Objects.requireNonNull(fullDelta); reconstructedMembership = identities(reconstructedMembership);
        }
    }
    public record RejectedIncremental(Reason reason) implements IncrementalVerification {
        public RejectedIncremental { Objects.requireNonNull(reason); }
    }

    /** Reuses the production difference and its owner/provenance/frame/order checks. */
    public static RealmDifference compareNative(RealmObservation before, RealmObservation after) {
        Objects.requireNonNull(before); Objects.requireNonNull(after);
        return RealmDifference.compare(observationJson(before), observationJson(after));
    }

    /** Exact original frames include opaque extensions. A new snapshot never refreshes a cached source. */
    public static CacheStatus qualifyNativeCache(RealmObservation cached, RealmObservation current) {
        Objects.requireNonNull(cached); Objects.requireNonNull(current);
        if (!sameJsonDomain(cached.sourceFrame(), current.sourceFrame())) return CacheStatus.FRAME_CHANGED;
        if (!sameJsonDomain(cached.provenance(), current.provenance())) return CacheStatus.PROVENANCE_CHANGED;
        if (!cached.querySequence().equals(current.querySequence())) return CacheStatus.QUERY_SEQUENCE_CHANGED;
        if (!cached.component().equals(current.component())) return CacheStatus.CONTENT_CHANGED;
        return CacheStatus.CURRENT;
    }

    /** The original candidate retains its full source snapshot; metadata is never stamped onto an old cache. */
    public static CacheStatus qualifyMonthlyCache(CampaignCadenceCodec.Candidate cached,
            CampaignCadenceCodec.Candidate current) {
        Objects.requireNonNull(cached); Objects.requireNonNull(current);
        if (!sameJsonDomain(cached.snapshot(), current.snapshot())) return CacheStatus.FRAME_CHANGED;
        if (!cached.startDate().equals(current.startDate()) || cached.months() != current.months()
                || !cached.machineId().equals(current.machineId())
                || !cached.observedAtUtc().equals(current.observedAtUtc())
                || !sameJsonDomain(cached.campaignAnchor(), current.campaignAnchor())) {
            return CacheStatus.MONTH_CONFIGURATION_CHANGED;
        }
        if (cached.evaluate().isNull() || current.evaluate().isNull()) return CacheStatus.NOT_AN_EXACT_MONTH_SLOT;
        return CacheStatus.CURRENT;
    }

    /** A result alone does not carry its geography rules; retain and revalidate both original inputs. */
    public static SavedComparison compareSaved(SavedMembershipInput beforeInput, SavedMembershipResult before,
            SavedMembershipInput afterInput, SavedMembershipResult after, SavedScope scope) {
        Objects.requireNonNull(beforeInput); Objects.requireNonNull(before);
        Objects.requireNonNull(afterInput); Objects.requireNonNull(after); Objects.requireNonNull(scope);
        if (!SavedCountyMembership.audit(beforeInput).equals(before)
                || !SavedCountyMembership.audit(afterInput).equals(after)) {
            return new SavedUnavailable(Reason.PRODUCER_RESULT_CHANGED);
        }
        if (!before.actor().equals(after.actor()) || !before.house().equals(after.house())
                || !before.dynasty().equals(after.dynasty())) {
            return new SavedUnavailable(Reason.OWNER_OR_FOUNDING_ANCHOR_CHANGED);
        }
        if (!beforeInput.mapping().equals(afterInput.mapping())) {
            return new SavedUnavailable(Reason.GEOGRAPHY_RULES_CHANGED);
        }
        SavedMembershipResult.Scope oldScope = scope(before, scope), newScope = scope(after, scope);
        if (!oldScope.complete() || !newScope.complete()) return new SavedUnavailable(Reason.INCOMPLETE_MEMBERSHIP);
        if (before.date().isEmpty() || after.date().isEmpty()) return new SavedUnavailable(Reason.DATE_UNAVAILABLE);
        int beforeRaw;
        int afterRaw;
        try {
            beforeRaw = CampaignCalendar.dateToRaw(before.date().orElseThrow());
            afterRaw = CampaignCalendar.dateToRaw(after.date().orElseThrow());
        } catch (IllegalArgumentException refusal) {
            return new SavedUnavailable(Reason.DATE_UNAVAILABLE);
        }
        if (beforeRaw >= afterRaw) return new SavedUnavailable(Reason.DATE_NOT_STRICTLY_EARLIER);
        return new SavedChange(scope, difference(oldScope.known(), newScope.known()), before.sourceRef(),
                after.sourceRef(), before.date().orElseThrow(), after.date().orElseThrow());
    }

    /** Incremental application is checked against the same complete, source-qualified full comparison. */
    public static IncrementalVerification verifyNativeIncremental(RealmObservation before,
            RealmObservation after, Delta proposed) {
        Objects.requireNonNull(proposed);
        RealmDifference comparison = compareNative(before, after);
        if (!(comparison instanceof RealmDifference.Available available)) {
            return new RejectedIncremental(Reason.FULL_COMPARISON_UNAVAILABLE);
        }
        Delta full = new Delta(big(available.lostCountyTitleIds()), big(available.gainedCountyTitleIds()));
        return verify(big(before.component().countyTitleIds()), big(after.component().countyTitleIds()), full, proposed);
    }

    public static IncrementalVerification verifySavedIncremental(SavedMembershipInput beforeInput,
            SavedMembershipResult before, SavedMembershipInput afterInput, SavedMembershipResult after,
            SavedScope scope, Delta proposed) {
        Objects.requireNonNull(proposed);
        SavedComparison comparison = compareSaved(beforeInput, before, afterInput, after, scope);
        if (!(comparison instanceof SavedChange available)) {
            return new RejectedIncremental(Reason.FULL_COMPARISON_UNAVAILABLE);
        }
        return verify(scope(before, scope).known(), scope(after, scope).known(), available.delta(), proposed);
    }

    /** Equality in the declared JSON type domain; integer node storage does not change an integer's value. */
    public static boolean sameJsonDomain(JsonNode left, JsonNode right) {
        if (left == null || right == null) return left == right;
        if (left.isIntegralNumber() && right.isIntegralNumber()) return left.bigIntegerValue().equals(right.bigIntegerValue());
        if (left.isFloatingPointNumber() && right.isFloatingPointNumber()) return left.decimalValue().compareTo(right.decimalValue()) == 0;
        if (left.getNodeType() != right.getNodeType()) return false;
        if (left.isObject()) {
            if (left.size() != right.size()) return false;
            for (var field : left.properties()) {
                if (!right.has(field.getKey()) || !sameJsonDomain(field.getValue(), right.get(field.getKey()))) return false;
            }
            return true;
        }
        if (left.isArray()) {
            if (left.size() != right.size()) return false;
            for (int i = 0; i < left.size(); i++) if (!sameJsonDomain(left.get(i), right.get(i))) return false;
            return true;
        }
        return left.equals(right);
    }

    private static IncrementalVerification verify(List<BigInteger> before, List<BigInteger> after,
            Delta full, Delta proposed) {
        if (!full.equals(proposed)) return new RejectedIncremental(Reason.DELTA_DOES_NOT_MATCH_FULL_COMPARISON);
        TreeSet<BigInteger> replayed = new TreeSet<>(before);
        if (!replayed.containsAll(proposed.lostTitleIds())
                || proposed.gainedTitleIds().stream().anyMatch(replayed::contains)) {
            return new RejectedIncremental(Reason.DELTA_DOES_NOT_RECONSTRUCT_CURRENT_MEMBERSHIP);
        }
        replayed.removeAll(proposed.lostTitleIds()); replayed.addAll(proposed.gainedTitleIds());
        if (!replayed.equals(new TreeSet<>(after))) {
            return new RejectedIncremental(Reason.DELTA_DOES_NOT_RECONSTRUCT_CURRENT_MEMBERSHIP);
        }
        return new VerifiedIncremental(full, List.copyOf(replayed));
    }
    private static SavedMembershipResult.Scope scope(SavedMembershipResult value, SavedScope scope) {
        return scope == SavedScope.REALM ? value.realm() : value.family();
    }
    private static Delta difference(List<BigInteger> before, List<BigInteger> after) {
        TreeSet<BigInteger> lost = new TreeSet<>(before); lost.removeAll(after);
        TreeSet<BigInteger> gained = new TreeSet<>(after); gained.removeAll(before);
        return new Delta(List.copyOf(lost), List.copyOf(gained));
    }
    private static List<BigInteger> identities(List<BigInteger> source) {
        List<BigInteger> values = List.copyOf(source); BigInteger previous = BigInteger.ZERO;
        for (BigInteger value : values) {
            StrictJson.require(value.signum() > 0 && value.compareTo(previous) > 0,
                    "sorted unique positive full identities required");
            previous = value;
        }
        return values;
    }
    private static List<BigInteger> big(List<Integer> values) {
        List<BigInteger> result = new ArrayList<>(values.size());
        for (int value : values) result.add(BigInteger.valueOf(value));
        return List.copyOf(result);
    }
    private static ObjectNode observationJson(RealmObservation value) {
        ObjectNode result = StrictJson.object();
        result.put("schema", RealmObservation.SCHEMA); result.put("status", "available");
        result.put("scope", SubrealmCounties.SCOPE); result.set("component", value.component().toJson());
        result.set("source_frame", value.sourceFrame()); result.put("query_sequence", value.querySequence());
        result.set("provenance", value.provenance()); return result;
    }
}
