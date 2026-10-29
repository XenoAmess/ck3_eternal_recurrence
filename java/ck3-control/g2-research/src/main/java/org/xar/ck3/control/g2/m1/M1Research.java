package org.xar.ck3.control.g2.m1;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifferenceCodec;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmObservation;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipCodec;
import org.xar.ck3.control.wave3.planning.datedsummary.DatedSummaryCodec;

/** G2 M1 composition in the single research host. Original producer bytes remain original leaf inputs. */
public final class M1Research implements G2Domain {
    // Two complete 1 MiB native inputs plus their wrapper fit without changing a leaf's own profile.
    public static final int MAX_BYTES = 4 * 1024 * 1024;
    private static final JsonFactory JSON = new JsonFactory();
    @Override public Milestone milestone() { return Milestone.M1; }
    @Override public G2Response evaluate(G2Request request) {
        Objects.requireNonNull(request);
        StrictJson.require(request.milestone() == milestone(), "M1 request milestone required");
        RawFields wrapper = fields(request.payload().bytes(), Set.of("operation", "input"));
        M1Operation operation = M1Operation.parse(StrictJson.text(StrictJson.parse(wrapper.get("operation"))));
        byte[] input = wrapper.get("input");
        byte[] output = switch (operation) {
            case SAVED_MEMBERSHIP -> SavedMembershipCodec.encode(M1ProducerApi.savedMembership(input).result());
            case REALM_FEEDBACK -> M1ProducerApi.realmFeedback(input).wireJson();
            case MONTHLY_OBSERVATION -> M1ProducerApi.monthlyObservation(input).wireJson();
            case NATIVE_DIFFERENCE -> RealmDifferenceCodec.evaluate(input);
            case DATED_SUMMARY -> DatedSummaryCodec.evaluate(input);
            case NATIVE_CACHE -> nativeCache(input);
            case MONTHLY_CACHE -> monthlyCache(input);
            case SAVED_DIFFERENCE -> savedDifference(input);
        };
        return new G2Response(request.requestId(), milestone(), request.source(), ProjectionJson.value(output, MAX_BYTES));
    }

    private static byte[] nativeCache(byte[] input) {
        RawFields values = fields(input, Set.of("cached", "current"));
        RealmObservation cached = RealmObservation.parse(StrictJson.parse(values.get("cached"), StrictJson.EXPLICIT_MAX_BYTES));
        RealmObservation current = RealmObservation.parse(StrictJson.parse(values.get("current"), StrictJson.EXPLICIT_MAX_BYTES));
        return cacheJson(M1RealmComparisons.qualifyNativeCache(cached, current));
    }
    private static byte[] monthlyCache(byte[] input) {
        RawFields values = fields(input, Set.of("cached", "current"));
        var cached = M1ProducerApi.monthlyObservation(values.get("cached"));
        var current = M1ProducerApi.monthlyObservation(values.get("current"));
        return cacheJson(M1RealmComparisons.qualifyMonthlyCache(cached.request(), current.request()));
    }
    private static byte[] cacheJson(M1RealmComparisons.CacheStatus status) {
        ObjectNode result = StrictJson.object();
        boolean current = status == M1RealmComparisons.CacheStatus.CURRENT;
        result.put("status", current ? "current" : "invalidated");
        if (current) result.putNull("reason"); else result.put("reason", status.name());
        return StrictJson.canonical(result);
    }
    private static byte[] savedDifference(byte[] input) {
        RawFields values = fields(input, Set.of("previous", "current", "scope"));
        var before = M1ProducerApi.savedMembership(values.get("previous"));
        var after = M1ProducerApi.savedMembership(values.get("current"));
        String scopeWire = StrictJson.text(StrictJson.parse(values.get("scope")));
        M1RealmComparisons.SavedScope scope = switch (scopeWire) {
            case "realm" -> M1RealmComparisons.SavedScope.REALM;
            case "dynasty" -> M1RealmComparisons.SavedScope.DYNASTY;
            default -> throw new ContractViolationException("M1 saved scope must be realm or dynasty");
        };
        var comparison = M1RealmComparisons.compareSaved(before.input(), before.result(), after.input(), after.result(), scope);
        ObjectNode result = StrictJson.object(); result.put("scope", scopeWire); result.putNull("cause");
        if (comparison instanceof M1RealmComparisons.SavedChange change) {
            result.put("status", "available"); result.putNull("unavailable_reason");
            var lost = result.putArray("lost_title_ids"); change.delta().lostTitleIds().forEach(value -> lost.add(value.toString()));
            var gained = result.putArray("gained_title_ids"); change.delta().gainedTitleIds().forEach(value -> gained.add(value.toString()));
            result.put("before_source_ref", change.beforeSourceRef()); result.put("after_source_ref", change.afterSourceRef());
            result.put("before_date", change.beforeDate()); result.put("after_date", change.afterDate());
        } else {
            var unavailable = (M1RealmComparisons.SavedUnavailable) comparison;
            result.put("status", "unavailable"); result.put("unavailable_reason", unavailable.reason().name());
            result.putNull("lost_title_ids"); result.putNull("gained_title_ids");
        }
        return StrictJson.canonical(result, StrictJson.EXPLICIT_MAX_BYTES);
    }

    /** Dynamic JSON boundary only: all fields are declared, values retain their exact original byte slices. */
    private record RawFields(Map<String, byte[]> values) {
        byte[] get(String field) { return values.get(field).clone(); }
    }
    private static RawFields fields(byte[] raw, Set<String> expected) {
        ProjectionJson.object(raw, MAX_BYTES);
        Map<String, byte[]> values = new HashMap<>();
        try (JsonParser parser = JSON.createParser(raw)) {
            StrictJson.require(parser.nextToken() == JsonToken.START_OBJECT, "M1 object required");
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                StrictJson.require(parser.currentToken() == JsonToken.FIELD_NAME, "M1 field name required");
                String key = parser.currentName();
                StrictJson.require(expected.contains(key) && !values.containsKey(key), "unknown or repeated M1 field");
                StrictJson.require(parser.nextToken() != null, "M1 field value required");
                int start = Math.toIntExact(parser.currentTokenLocation().getByteOffset());
                parser.skipChildren();
                parser.finishToken();
                int end = Math.toIntExact(parser.currentLocation().getByteOffset());
                values.put(key, Arrays.copyOfRange(raw, start, end));
            }
            StrictJson.require(values.keySet().equals(expected) && parser.nextToken() == null, "complete exact M1 fields required");
            return new RawFields(Map.copyOf(values));
        } catch (IOException error) {
            throw new ContractViolationException("invalid M1 input JSON", error);
        }
    }
}
