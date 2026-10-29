package org.xar.ck3.control.g2.m1;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.planning.campaigncadence.CampaignCalendar;
import org.xar.ck3.control.planning.campaigncadence.MonthlyObservation;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifference;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmObservation;
import org.xar.ck3.control.wave2.planning.realmcompare.SubrealmCounties;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipCodec;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult;
import org.xar.ck3.control.wave2.planning.scoreinputs.ScoreInputFrame;
import org.xar.ck3.control.wave2.planning.scoreinputs.UnknownScoreMetric;
import org.xar.ck3.control.wave3.planning.datedsummary.DatedRealmSummary;

/** Typed response consumers. Decoding preserves supplied evidence and grants no transport qualification. */
public final class M1ResultConsumers {
    public static final int MAX_BYTES = 1_048_576;
    private M1ResultConsumers() { }

    public sealed interface DecodedFeedback permits AvailableFeedback, UnavailableFeedback { }
    public record AvailableFeedback(RealmObservation observation, RealmDifference difference)
            implements DecodedFeedback {
        public AvailableFeedback { require(observation != null && difference != null, "supplied feedback required"); }
    }
    public record UnavailableFeedback(String reason) implements DecodedFeedback {
        public UnavailableFeedback { StrictJson.text(reason); }
    }
    public sealed interface DecodedSummary permits NoQualifiedSummary, RetainedSummary { }
    public enum NoQualifiedSummary implements DecodedSummary { INSTANCE }
    public record SummaryLoss(boolean lossObserved, int lostCount, int gainedCount, List<Integer> firstEightLost,
            boolean truncated, ObjectNode beforeSourceFrame) {
        public SummaryLoss {
            firstEightLost = List.copyOf(firstEightLost); beforeSourceFrame = beforeSourceFrame.deepCopy();
        }
        @Override public ObjectNode beforeSourceFrame() { return beforeSourceFrame.deepCopy(); }
    }
    public record RetainedSummary(DatedRealmSummary.Status status, int lastObservedCount, ScoreInputFrame frame,
            ObjectNode sourceFrame, BigInteger querySequence, Optional<SummaryLoss> loss) implements DecodedSummary {
        public RetainedSummary { sourceFrame = sourceFrame.deepCopy(); }
        @Override public ObjectNode sourceFrame() { return sourceFrame.deepCopy(); }
    }

    public static SavedMembershipResult savedMembership(byte[] raw) {
        ObjectNode input = object(parse(raw), Set.of("schema", "source_ref", "date", "actor_id",
                "founding_house_id", "founding_dynasty_id", "title_census_complete", "geography_complete",
                "realm", "dynasty", "states"));
        text(input.get("schema"), "xar.ck3.saved-county-membership-audit/v1");
        Map<BigInteger, SavedMembershipResult.CountyState> states = new LinkedHashMap<>();
        ObjectNode rows = arbitraryObject(input.get("states"));
        rows.properties().forEach(entry -> {
            require(entry.getKey().matches("0|[1-9][0-9]*"), "canonical saved title identity key required");
            BigInteger identity = new BigInteger(entry.getKey());
            ObjectNode row = object(entry.getValue(), Set.of("key", "geographic", "geography_reason",
                    "in_player_realm", "realm_reason", "realm_terminal_title_id", "family_factor", "family_reason"));
            JsonNode geographic = row.get("geographic");
            require(geographic.isNull() || geographic.isBoolean() && geographic.booleanValue(),
                    "observed geographic county or explicit unknown required");
            SavedMembershipResult.Geography geography = geographic.isNull()
                    ? SavedMembershipResult.Geography.UNKNOWN : SavedMembershipResult.Geography.KNOWN_COUNTY;
            JsonNode member = row.get("in_player_realm");
            require(member.isNull() || member.isBoolean(), "realm membership Boolean or explicit unknown required");
            SavedMembershipResult.Truth truth = member.isNull() ? SavedMembershipResult.Truth.UNKNOWN
                    : member.booleanValue() ? SavedMembershipResult.Truth.YES : SavedMembershipResult.Truth.NO;
            states.put(identity, new SavedMembershipResult.CountyState(optionalText(row.get("key")), geography,
                    new SavedMembershipResult.Realm(truth, reason(row.get("realm_reason")),
                            integer(row.get("realm_terminal_title_id"))),
                    new SavedMembershipResult.Family(factor(row.get("family_factor")), reason(row.get("family_reason")))));
        });
        SavedMembershipResult result = new SavedMembershipResult(StrictJson.text(input.get("source_ref")),
                optionalText(input.get("date")), integer(input.get("actor_id")), optionalInteger(input.get("founding_house_id")),
                optionalInteger(input.get("founding_dynasty_id")), bool(input.get("title_census_complete")),
                bool(input.get("geography_complete")), scope(input.get("realm")), scope(input.get("dynasty")), states);
        require(parse(SavedMembershipCodec.encode(result)).equals(input), "saved response must round trip without losing fields or JSON types");
        return result;
    }

    public static RealmDifference nativeDifference(byte[] raw) {
        JsonNode input = parse(raw);
        require(input instanceof ObjectNode, "native difference object required");
        String status = StrictJson.text(input.get("status"));
        RealmDifference result;
        if (status.equals("available")) {
            ObjectNode row = object(input, Set.of("status", "lost_county_title_ids", "gained_county_title_ids",
                    "unavailable_reason", "before_source_frame", "after_source_frame", "cause"));
            require(row.get("unavailable_reason").isNull() && row.get("cause").isNull(), "explicit unavailable reason and cause null required");
            ScoreInputFrame before = sourceFrame(row.get("before_source_frame"));
            ScoreInputFrame after = sourceFrame(row.get("after_source_frame"));
            require(before.actorCharacterId().equals(after.actorCharacterId())
                    && before.episodeRunId().equals(after.episodeRunId()) && before.bridgePid() == after.bridgePid()
                    && before.connectionGeneration().equals(after.connectionGeneration())
                    && before.dateRaw() <= after.dateRaw() && before.revision().compareTo(after.revision()) < 0
                    && before.nativeRevision().compareTo(after.nativeRevision()) < 0,
                    "native difference must retain comparable original owner and strictly earlier source");
            result = new RealmDifference.Available(countyIds(row.get("lost_county_title_ids")),
                    countyIds(row.get("gained_county_title_ids")), arbitraryObject(row.get("before_source_frame")),
                    arbitraryObject(row.get("after_source_frame")));
        } else {
            text(input.get("status"), "unavailable");
            ObjectNode row = object(input, Set.of("status", "lost_county_title_ids", "gained_county_title_ids", "unavailable_reason"));
            require(row.get("lost_county_title_ids").isNull() && row.get("gained_county_title_ids").isNull(),
                    "unknown membership is not an empty difference");
            result = new RealmDifference.Unavailable(StrictJson.text(row.get("unavailable_reason")));
        }
        require(sameWire(input, result.toJson()), "native difference must retain exact source JSON");
        return result;
    }

    public static DecodedFeedback realmFeedback(byte[] raw) {
        ObjectNode input = object(parse(raw), Set.of("schema", "status", "observation", "difference", "unavailable_reason",
                "raw_metrics", "new_RPC_calls", "new_SAVE_exports", "same_native_capture_with_MET", "native_capture_epoch"));
        text(input.get("schema"), "xar.ck3.realm-membership-feedback/v1");
        require(integer(input.get("new_RPC_calls")).equals(BigInteger.ZERO)
                && integer(input.get("new_SAVE_exports")).equals(BigInteger.ZERO)
                && !bool(input.get("same_native_capture_with_MET")) && input.get("native_capture_epoch").isNull(),
                "response must preserve the pure producer evidence limits");
        ObjectNode metrics = object(input.get("raw_metrics"), Set.of("realm_county_count"));
        if (StrictJson.text(input.get("status")).equals("unavailable")) {
            require(input.get("observation").isNull() && input.get("difference").isNull(),
                    "unavailable feedback cannot contain a promoted observation");
            String reason = StrictJson.text(input.get("unavailable_reason"));
            require(sameWire(metrics.get("realm_county_count"),
                    new UnknownScoreMetric(UnknownScoreMetric.nameFromWire("realm_county_count"), reason).toJson()),
                    "unavailable feedback must retain its unknown metric");
            return new UnavailableFeedback(reason);
        }
        text(input.get("status"), "available");
        require(input.get("unavailable_reason").isNull(), "available feedback reason must be null");
        object(input.get("observation"), Set.of("schema", "status", "scope", "component", "source_frame", "query_sequence", "provenance"));
        RealmObservation observation = RealmObservation.parse(input.get("observation"));
        RealmDifference difference = nativeDifference(write(input.get("difference")));
        ObjectNode expected = StrictJson.object();
        expected.put("value", Integer.toString(observation.component().countyTitleIds().size()));
        expected.put("unit", "county"); expected.put("availability", "observed");
        expected.put("scope", SubrealmCounties.SCOPE);
        expected.put("source_ref", "existing_player_faction_alerts");
        expected.put("locator", SubrealmCounties.COMPONENT);
        require(sameWire(metrics.get("realm_county_count"), expected), "observed count must use the complete realm component");
        return new AvailableFeedback(observation, difference);
    }

    public static Optional<MonthlyObservation> monthlyObservation(byte[] raw) {
        JsonNode parsed = parse(raw);
        if (parsed.isNull()) { return Optional.empty(); }
        ObjectNode input = arbitraryObject(parsed);
        ObjectNode anchor = arbitraryObject(input.get("campaign_anchor"));
        ObjectNode frame = arbitraryObject(input.get("frame"));
        MonthlyObservation.CampaignAnchor campaign = new MonthlyObservation.CampaignAnchor(
                StrictJson.text(anchor.get("campaign_id")), integer(anchor.get("founder_character_id")),
                nullableInteger(anchor.get("founding_house_id")), nullableInteger(anchor.get("founding_dynasty_id")));
        MonthlyObservation.Frame identity = new MonthlyObservation.Frame(StrictJson.text(frame.get("snapshot_id")),
                integer(frame.get("revision")), integer(frame.get("native_revision")), signedInt(frame.get("date_raw")),
                optionalText(frame.get("episode_run_id")).orElse(null), nullableInteger(frame.get("episode_character_id")),
                nullableBoolean(frame.get("one_life_terminal")), optionalText(frame.get("one_life_terminal_reason")).orElse(null),
                nullableInteger(frame.get("actor_character_id")), nullableBoolean(frame.get("actor_alive")));
        ObjectNode metrics = arbitraryObject(input.get("raw_metrics"));
        ObjectNode gold = arbitraryObject(metrics.get("gold"));
        JsonNode warsNode = input.get("observed_player_wars");
        require(warsNode != null, "explicit observed player wars null or array required");
        List<MonthlyObservation.WarRow> wars = null;
        if (!warsNode.isNull()) {
            require(warsNode.isArray(), "player wars must be an array or null");
            wars = new ArrayList<>();
            for (JsonNode row : warsNode) {
                wars.add(new MonthlyObservation.WarRow(nullableInteger(row.get("war_id")),
                        optionalText(row.get("player_side")).orElse(null), nullableInteger(row.get("primary_opponent_character_id")),
                        row.get("player_relative_war_score") != null && row.get("player_relative_war_score").isNull()
                                ? null : signedInt(row.get("player_relative_war_score"))));
            }
        }
        MonthlyObservation result = new MonthlyObservation(StrictJson.text(input.get("machine_id")),
                StrictJson.text(input.get("observed_at_utc")), signedInt(input.get("month_index")),
                new CampaignCalendar.Boundary(StrictJson.text(input.get("date")), signedInt(input.get("date_raw"))),
                campaign, new CampaignCalendar.Boundary(StrictJson.text(input.get("baseline_date")), signedInt(input.get("baseline_date_raw"))),
                new CampaignCalendar.Boundary(StrictJson.text(input.get("endpoint_date")), signedInt(input.get("endpoint_date_raw"))),
                identity, optionalText(gold.get("value")).orElse(null), wars);
        require(sameWire(input, result.toJson()), "monthly response must retain missing, null, empty, sources and metric availability");
        return Optional.of(result);
    }

    public static M1RealmComparisons.CacheStatus cache(byte[] raw) {
        ObjectNode input = object(parse(raw), Set.of("status", "reason"));
        if (StrictJson.text(input.get("status")).equals("current")) {
            require(input.get("reason").isNull(), "current cache reason must be explicit null");
            return M1RealmComparisons.CacheStatus.CURRENT;
        }
        text(input.get("status"), "invalidated");
        M1RealmComparisons.CacheStatus reason = M1RealmComparisons.CacheStatus.valueOf(StrictJson.text(input.get("reason")));
        require(reason != M1RealmComparisons.CacheStatus.CURRENT, "invalidated cache requires an invalidation reason");
        return reason;
    }

    public static DecodedSummary datedSummary(byte[] raw) {
        JsonNode input = parse(raw);
        require(input instanceof ObjectNode, "dated summary object required");
        if (StrictJson.text(input.get("status")).equals("unavailable")) {
            ObjectNode row = object(input, Set.of("status", "current_realm_county_count", "loss_observed", "unavailable_reason"));
            require(row.get("current_realm_county_count").isNull() && row.get("loss_observed").isNull(), "unavailable summary is not a zero count");
            text(row.get("unavailable_reason"), "no_qualified_realm_observation");
            return NoQualifiedSummary.INSTANCE;
        }
        ObjectNode row = object(input, Set.of("status", "current_realm_county_count", "last_observed_realm_county_count",
                "source_frame", "query_sequence", "loss_observed", "lost_county_count", "gained_county_count",
                "lost_county_title_ids_first8", "loss_list_truncated", "before_source_frame", "cause", "new_RPC_calls"));
        DatedRealmSummary.Status status = switch (StrictJson.text(row.get("status"))) {
            case "current" -> DatedRealmSummary.Status.CURRENT;
            case "historical" -> DatedRealmSummary.Status.HISTORICAL;
            default -> throw new IllegalArgumentException("dated summary status required");
        };
        int count = boundedCountyCount(row.get("last_observed_realm_county_count"));
        require(status == DatedRealmSummary.Status.CURRENT
                ? boundedCountyCount(row.get("current_realm_county_count")) == count : row.get("current_realm_county_count").isNull(),
                "historical summary cannot relabel its last count as current");
        ObjectNode source = arbitraryObject(row.get("source_frame"));
        ScoreInputFrame frame = sourceFrame(source);
        BigInteger sequence = StrictJson.integer(row.get("query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX);
        require(row.get("cause").isNull() && integer(row.get("new_RPC_calls")).equals(BigInteger.ZERO), "dated summary evidence limits required");
        Optional<SummaryLoss> loss = Optional.empty();
        if (row.get("loss_observed").isNull()) {
            require(row.get("lost_county_count").isNull() && row.get("gained_county_count").isNull()
                    && row.get("lost_county_title_ids_first8").isNull() && !bool(row.get("loss_list_truncated"))
                    && row.get("before_source_frame").isNull(), "unknown loss must remain null rather than false or empty");
        } else {
            boolean observed = bool(row.get("loss_observed"));
            int lost = boundedCountyCount(row.get("lost_county_count"));
            int gained = boundedCountyCount(row.get("gained_county_count"));
            List<Integer> first = countyIds(row.get("lost_county_title_ids_first8"));
            int prior = 0;
            for (int identity : first) { require(identity > prior, "sorted unique first loss identities required"); prior = identity; }
            boolean truncated = bool(row.get("loss_list_truncated"));
            require(observed == (lost > 0) && first.size() == Math.min(8, lost) && truncated == (lost > 8), "dated loss counts and bounded preview disagree");
            ObjectNode beforeSource = arbitraryObject(row.get("before_source_frame"));
            ScoreInputFrame before = sourceFrame(beforeSource);
            require(before.actorCharacterId().equals(frame.actorCharacterId()) && before.episodeRunId().equals(frame.episodeRunId())
                    && before.bridgePid() == frame.bridgePid() && before.connectionGeneration().equals(frame.connectionGeneration())
                    && before.dateRaw() <= frame.dateRaw() && before.revision().compareTo(frame.revision()) < 0
                    && before.nativeRevision().compareTo(frame.nativeRevision()) < 0, "dated loss must retain comparable prior source");
            loss = Optional.of(new SummaryLoss(observed, lost, gained, first, truncated, beforeSource));
        }
        return new RetainedSummary(status, count, frame, source, sequence, loss);
    }

    private static int boundedCountyCount(JsonNode value) {
        return (int) StrictJson.integer(value, 0, 16_384);
    }

    public static M1RealmComparisons.SavedComparison savedDifference(byte[] raw) {
        JsonNode input = parse(raw);
        require(input instanceof ObjectNode, "saved difference object required");
        String scopeWire = StrictJson.text(input.get("scope"));
        M1RealmComparisons.SavedScope scope = switch (scopeWire) {
            case "realm" -> M1RealmComparisons.SavedScope.REALM;
            case "dynasty" -> M1RealmComparisons.SavedScope.DYNASTY;
            default -> throw new IllegalArgumentException("saved difference scope required");
        };
        require(input.has("cause") && input.get("cause").isNull(), "saved difference cannot invent a cause");
        if (StrictJson.text(input.get("status")).equals("available")) {
            ObjectNode row = object(input, Set.of("scope", "cause", "status", "unavailable_reason", "lost_title_ids",
                    "gained_title_ids", "before_source_ref", "after_source_ref", "before_date", "after_date"));
            require(row.get("unavailable_reason").isNull(), "available saved difference reason must be null");
            String beforeDate = StrictJson.text(row.get("before_date"));
            String afterDate = StrictJson.text(row.get("after_date"));
            require(CampaignCalendar.dateToRaw(beforeDate) < CampaignCalendar.dateToRaw(afterDate),
                    "saved difference dates must be strictly ordered");
            return new M1RealmComparisons.SavedChange(scope,
                    new M1RealmComparisons.Delta(decimalStringIds(row.get("lost_title_ids")), decimalStringIds(row.get("gained_title_ids"))),
                    StrictJson.text(row.get("before_source_ref")), StrictJson.text(row.get("after_source_ref")), beforeDate, afterDate);
        }
        ObjectNode row = object(input, Set.of("scope", "cause", "status", "unavailable_reason", "lost_title_ids", "gained_title_ids"));
        text(row.get("status"), "unavailable");
        require(row.get("lost_title_ids").isNull() && row.get("gained_title_ids").isNull(), "unknown saved difference is not an empty set");
        return new M1RealmComparisons.SavedUnavailable(M1RealmComparisons.Reason.valueOf(StrictJson.text(row.get("unavailable_reason"))));
    }

    private static List<BigInteger> decimalStringIds(JsonNode node) {
        require(node != null && node.isArray(), "canonical decimal string identity array required");
        List<BigInteger> values = new ArrayList<>();
        for (JsonNode value : node) {
            String text = StrictJson.text(value);
            require(text.matches("[1-9][0-9]*"), "canonical positive decimal string identity required");
            values.add(new BigInteger(text));
        }
        return List.copyOf(values);
    }

    private static SavedMembershipResult.Scope scope(JsonNode node) {
        ObjectNode row = object(node, Set.of("complete", "known_member_title_ids", "unknown_title_ids", "count_lower", "count_upper"));
        JsonNode upper = row.get("count_upper");
        boolean complete = bool(row.get("complete"));
        List<BigInteger> known = identities(row.get("known_member_title_ids"));
        List<BigInteger> unknown = identities(row.get("unknown_title_ids"));
        int lower = signedInt(row.get("count_lower"));
        OptionalInt maximum = upper.isNull() ? OptionalInt.empty() : OptionalInt.of(signedInt(upper));
        require(Set.copyOf(known).size() == known.size() && Set.copyOf(unknown).size() == unknown.size()
                && java.util.Collections.disjoint(known, unknown) && lower == known.size()
                && (maximum.isEmpty() || maximum.getAsInt() >= lower)
                && (!complete || unknown.isEmpty() && maximum.isPresent() && maximum.getAsInt() == lower),
                "membership completeness and count bounds must retain the supplied set semantics");
        return new SavedMembershipResult.Scope(complete, known, unknown, lower, maximum);
    }
    private static ScoreInputFrame sourceFrame(JsonNode node) {
        ObjectNode source = arbitraryObject(node);
        text(source.get("schema"), "xar.ck3.planning-source-frame/v1");
        text(source.get("status"), "complete");
        ObjectNode frame = StrictJson.object();
        for (String key : Set.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id",
                "actor_character_id", "bridge_pid", "connection_generation")) {
            require(source.has(key), "complete original difference source frame required");
            frame.set(key, source.get(key));
        }
        ScoreInputFrame result = ScoreInputFrame.fromJson(frame);
        require(result.nativeRevision().signum() > 0 && result.actorCharacterId().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0,
                "native realm frame requires observed positive revision and full int32 actor");
        return result;
    }
    private static SavedMembershipResult.Reason reason(JsonNode node) {
        String wire = StrictJson.text(node);
        for (SavedMembershipResult.Reason reason : SavedMembershipResult.Reason.values()) {
            if (reason.wire().equals(wire)) { return reason; }
        }
        throw new IllegalArgumentException("unknown membership reason");
    }
    private static Optional<SavedMembershipResult.Factor> factor(JsonNode node) {
        require(node != null, "explicit family factor required");
        if (node.isNull()) { return Optional.empty(); }
        String wire = StrictJson.text(node);
        for (SavedMembershipResult.Factor factor : SavedMembershipResult.Factor.values()) {
            if (factor.lexical().equals(wire)) { return Optional.of(factor); }
        }
        throw new IllegalArgumentException("unknown family factor");
    }
    private static List<Integer> countyIds(JsonNode node) {
        return identities(node).stream().map(BigInteger::intValueExact).toList();
    }
    private static List<BigInteger> identities(JsonNode node) {
        require(node != null && node.isArray(), "explicit exact integer array required");
        List<BigInteger> values = new ArrayList<>();
        for (JsonNode value : node) { values.add(integer(value)); }
        return List.copyOf(values);
    }
    private static BigInteger integer(JsonNode node) {
        require(node != null && node.isIntegralNumber(), "exact JSON integer required; Boolean, fractional and string tokens are distinct");
        return node.bigIntegerValue();
    }
    private static Optional<BigInteger> optionalInteger(JsonNode node) {
        require(node != null, "explicit integer or null required");
        return node.isNull() ? Optional.empty() : Optional.of(integer(node));
    }
    private static BigInteger nullableInteger(JsonNode node) { return optionalInteger(node).orElse(null); }
    private static int signedInt(JsonNode node) { return integer(node).intValueExact(); }
    private static Optional<String> optionalText(JsonNode node) {
        require(node != null, "explicit text or null required");
        return node.isNull() ? Optional.empty() : Optional.of(StrictJson.text(node));
    }
    private static Boolean nullableBoolean(JsonNode node) {
        require(node != null, "explicit Boolean or null required");
        return node.isNull() ? null : bool(node);
    }
    private static boolean bool(JsonNode node) {
        require(node != null && node.isBoolean(), "exact JSON Boolean required");
        return node.booleanValue();
    }
    private static void text(JsonNode node, String expected) { require(expected.equals(StrictJson.text(node)), "unexpected response discriminator"); }
    private static ObjectNode object(JsonNode node, Set<String> fields) { return StrictJson.object(node, fields); }
    private static ObjectNode arbitraryObject(JsonNode node) {
        require(node instanceof ObjectNode, "response object required");
        return (ObjectNode) node;
    }
    private static JsonNode parse(byte[] raw) { return StrictJson.parse(raw, MAX_BYTES); }
    private static byte[] write(JsonNode value) { return SdkProjectionJson.encode(value, MAX_BYTES); }
    private static boolean sameWire(JsonNode input, JsonNode projected) { return input != null && parse(write(projected)).equals(input); }
}
