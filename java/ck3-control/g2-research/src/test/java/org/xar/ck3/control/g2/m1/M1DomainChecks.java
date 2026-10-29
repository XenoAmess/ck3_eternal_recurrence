package org.xar.ck3.control.g2.m1;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.campaigncadence.CampaignCadenceCodec;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifference;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmObservation;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedCountyMembership;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipCodec;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipInput;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult;
import org.xar.ck3.control.wave2.planning.scoretarget.ScalarField;

/** Executable regression over the immutable original producer corpora; no SAVE or Driver input. */
public final class M1DomainChecks {
    private static int checks;
    private M1DomainChecks() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 4) throw new IllegalArgumentException("realm golden, saved JSONL, monthly golden and machine ID required");
        int total = run(Files.readAllBytes(Path.of(arguments[0])), Files.readAllLines(Path.of(arguments[1])),
                Files.readAllBytes(Path.of(arguments[2])));
        ObjectNode receipt = StrictJson.object(); receipt.put("schema", "xar.g2.m1.domain-regression/v1");
        receipt.put("machine_id", arguments[3]); receipt.put("observed_at_utc", Instant.now().toString());
        receipt.put("status", "PASS"); receipt.put("checks", total); receipt.put("native_rpc_calls", 0);
        receipt.put("save_reads", 0); receipt.put("driver_reads", 0); receipt.put("canonical_writes", 0);
        System.out.println(new String(StrictJson.canonical(receipt), java.nio.charset.StandardCharsets.UTF_8));
    }
    public static synchronized int run(byte[] realmGolden, List<String> savedLines, byte[] monthlyGolden) {
        checks = 0;
        nativeCases(StrictJson.parse(realmGolden, StrictJson.EXPLICIT_MAX_BYTES));
        savedCases(savedLines);
        monthlyCases(StrictJson.parse(monthlyGolden, StrictJson.EXPLICIT_MAX_BYTES));
        return checks;
    }

    private static void nativeCases(JsonNode corpus) {
        int valid = 0;
        for (JsonNode row : corpus.path("cases")) {
            JsonNode request = row.path("request");
            if (!row.path("expected").path("status").asText().equals("returned")) continue;
            RealmObservation before;
            RealmObservation after;
            try {
                before = RealmObservation.parse(request.get("previous"));
                after = RealmObservation.parse(request.get("observation"));
            } catch (IllegalArgumentException malformedOriginalVector) { continue; }
            RealmDifference full = M1RealmComparisons.compareNative(before, after);
            check(M1RealmComparisons.sameJsonDomain(row.path("expected").get("value"), full.toJson()),
                    "typed full comparison differs from unchanged original producer: " + row.path("id"));
            if (full instanceof RealmDifference.Available available) {
                var delta = new M1RealmComparisons.Delta(big(available.lostCountyTitleIds()), big(available.gainedCountyTitleIds()));
                check(M1RealmComparisons.verifyNativeIncremental(before, after, delta)
                        instanceof M1RealmComparisons.VerifiedIncremental, "actual full delta failed incremental reconstruction");
            }
            valid++;
        }
        check(valid > 0, "actual complete native original cases required");
        JsonNode realLoss = corpus.path("cases").get(0).path("request");
        RealmObservation before = RealmObservation.parse(realLoss.get("previous"));
        RealmObservation after = RealmObservation.parse(realLoss.get("observation"));
        check(M1RealmComparisons.qualifyNativeCache(before, before) == M1RealmComparisons.CacheStatus.CURRENT,
                "unchanged complete original frame must remain eligible");
        check(M1RealmComparisons.qualifyNativeCache(before, after) == M1RealmComparisons.CacheStatus.FRAME_CHANGED,
                "later frame must invalidate the retained observation cache");
        var wrong = new M1RealmComparisons.Delta(List.of(), List.of());
        check(M1RealmComparisons.verifyNativeIncremental(before, after, wrong)
                instanceof M1RealmComparisons.RejectedIncremental, "empty delta concealed the actual vassal-inclusive loss");
        ObjectNode decimalFrame = before.sourceFrame(); decimalFrame.set("sdk_extension", new DecimalNode(new BigDecimal("1.0")));
        ObjectNode integerFrame = before.sourceFrame(); integerFrame.put("sdk_extension", 1);
        RealmObservation decimal = new RealmObservation(before.frame(), decimalFrame, before.querySequence(), before.provenance(), before.component());
        RealmObservation integer = new RealmObservation(before.frame(), integerFrame, before.querySequence(), before.provenance(), before.component());
        check(M1RealmComparisons.qualifyNativeCache(decimal, integer) == M1RealmComparisons.CacheStatus.FRAME_CHANGED,
                "opaque decimal must not alias an integer source frame");
        ObjectNode changedSource = before.provenance(); changedSource.put("backend_id", "different-source");
        var otherSource = new RealmObservation(before.frame(), before.sourceFrame(), before.querySequence(), changedSource, before.component());
        check(M1RealmComparisons.qualifyNativeCache(before, otherSource) == M1RealmComparisons.CacheStatus.PROVENANCE_CHANGED,
                "source changes must invalidate cache");
        ObjectNode reconnected = ((ObjectNode) realLoss.get("observation")).deepCopy();
        ((ObjectNode) reconnected.get("source_frame")).put("connection_generation", 4);
        check(M1RealmComparisons.compareNative(before, RealmObservation.parse(reconnected)) instanceof RealmDifference.Unavailable,
                "a cold connection change cannot infer M3 continuity");
        var unsafeSequence = new RealmObservation(before.frame(), before.sourceFrame(), new BigInteger("9007199254740993"),
                before.provenance(), before.component());
        check(unsafeSequence.querySequence().toString().equals("9007199254740993"), "uint64 query sequence lost precision");
        check(M1RealmComparisons.qualifyNativeCache(before, unsafeSequence) == M1RealmComparisons.CacheStatus.QUERY_SEQUENCE_CHANGED,
                "query identity changes must invalidate cache");
        check(M1RealmComparisons.sameJsonDomain(StrictJson.parse("1".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                com.fasterxml.jackson.databind.node.IntNode.valueOf(1)), "integer node representation is not JSON identity");
        check(!M1RealmComparisons.sameJsonDomain(StrictJson.parse("true".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                com.fasterxml.jackson.databind.node.IntNode.valueOf(1)), "boolean must not alias an integer");
    }

    private static void savedCases(List<String> lines) {
        SavedMembershipInput complete = null;
        SavedMembershipInput incomplete = null;
        int originals = 0;
        for (int index = 1; index < lines.size(); index++) {
            JsonNode row = StrictJson.parse(lines.get(index).getBytes(java.nio.charset.StandardCharsets.UTF_8));
            SavedMembershipInput input = SavedMembershipCodec.decode(row.path("input_json").textValue().getBytes(java.nio.charset.StandardCharsets.UTF_8));
            SavedMembershipResult result = SavedCountyMembership.audit(input);
            check(M1RealmComparisons.sameJsonDomain(row.get("expected"), StrictJson.parse(SavedMembershipCodec.encode(result))),
                    "saved original producer differential failed at ordinal " + row.path("ordinal"));
            if (complete == null && result.realm().complete() && result.realm().known().size() > 1) complete = input;
            if (incomplete == null && !result.realm().complete()) incomplete = input;
            originals++;
        }
        check(originals == 34 && complete != null && incomplete != null, "all34 real saved vectors including unknown/complete required");
        SavedMembershipResult before = SavedCountyMembership.audit(complete);
        SavedMembershipInput afterInput = later(complete);
        SavedMembershipResult after = SavedCountyMembership.audit(afterInput);
        check(before.realm().known().size() > 1, "full realm must include the original vassal county");
        var unchanged = M1RealmComparisons.compareSaved(complete, before, afterInput, after, M1RealmComparisons.SavedScope.REALM);
        check(unchanged instanceof M1RealmComparisons.SavedChange, "complete comparable saved scope must compare");
        check(M1RealmComparisons.verifySavedIncremental(complete, before, afterInput, after,
                M1RealmComparisons.SavedScope.REALM, new M1RealmComparisons.Delta(List.of(), List.of()))
                instanceof M1RealmComparisons.VerifiedIncremental, "incremental empty update failed against unchanged full realm");
        BigInteger vassalCounty = before.realm().known().stream()
                .filter(id -> !before.states().get(id).realm().terminal().equals(id)).findFirst().orElseThrow();
        var changedTitles = new LinkedHashMap<>(afterInput.projection().titles());
        var vassal = changedTitles.get(vassalCounty);
        changedTitles.put(vassalCounty, new SavedMembershipInput.Title(vassal.key(), new ScalarField.Text("3"),
                new ScalarField.Missing(), false, false));
        var originalProjection = afterInput.projection();
        var lossProjection = new SavedMembershipInput.SavedProjection(changedTitles, originalProjection.houses(),
                originalProjection.characterHouses(), originalProjection.characterHouseUnknown(), originalProjection.characterSources(),
                originalProjection.streamComplete(), originalProjection.unknownKeyFields(), originalProjection.rootKeys(), originalProjection.date());
        var lossInput = new SavedMembershipInput(afterInput.actor(), afterInput.house(), afterInput.dynasty(),
                afterInput.sourceRef() + ":vassal-transfer", lossProjection, afterInput.mapping());
        var lossResult = SavedCountyMembership.audit(lossInput);
        var expectedLoss = new M1RealmComparisons.Delta(List.of(vassalCounty), List.of());
        check(lossResult.realm().complete(), "legal foreign root must preserve complete full-realm census");
        check(M1RealmComparisons.verifySavedIncremental(complete, before, lossInput, lossResult,
                M1RealmComparisons.SavedScope.REALM, expectedLoss) instanceof M1RealmComparisons.VerifiedIncremental,
                "full audit and incremental replay disagreed on the vassal county transfer");
        check(M1RealmComparisons.verifySavedIncremental(complete, before, lossInput, lossResult,
                M1RealmComparisons.SavedScope.REALM, new M1RealmComparisons.Delta(List.of(), List.of()))
                instanceof M1RealmComparisons.RejectedIncremental, "direct-only cache hid a vassal county loss");
        SavedMembershipInput oldUnknown = incomplete;
        SavedMembershipInput newUnknown = later(incomplete);
        check(M1RealmComparisons.compareSaved(oldUnknown, SavedCountyMembership.audit(oldUnknown), newUnknown,
                SavedCountyMembership.audit(newUnknown), M1RealmComparisons.SavedScope.REALM)
                instanceof M1RealmComparisons.SavedUnavailable, "unknown members became precise empty loss");
        check(M1RealmComparisons.compareSaved(complete, before, complete, before, M1RealmComparisons.SavedScope.REALM)
                instanceof M1RealmComparisons.SavedUnavailable, "same-date SAVE has no independent ordering proof");
        SavedMembershipInput changedRules = new SavedMembershipInput(afterInput.actor(), afterInput.house(), afterInput.dynasty(),
                afterInput.sourceRef(), afterInput.projection(), new SavedMembershipInput.UnavailableMapping(SavedMembershipInput.UnavailableKind.NULL));
        check(M1RealmComparisons.compareSaved(complete, before, changedRules, SavedCountyMembership.audit(changedRules),
                M1RealmComparisons.SavedScope.REALM) instanceof M1RealmComparisons.SavedUnavailable,
                "mapping/source rules changed without invalidating comparison");
        var successorInput = new SavedMembershipInput(BigInteger.valueOf(2), afterInput.house(), afterInput.dynasty(),
                afterInput.sourceRef() + ":successor", afterInput.projection(), afterInput.mapping());
        var successorComparison = M1RealmComparisons.compareSaved(complete, before, successorInput,
                SavedCountyMembership.audit(successorInput), M1RealmComparisons.SavedScope.REALM);
        check(successorComparison instanceof M1RealmComparisons.SavedUnavailable unavailable
                && unavailable.reason() == M1RealmComparisons.Reason.OWNER_OR_FOUNDING_ANCHOR_CHANGED,
                "actor succession cannot invent a comparability/M3 proof");
        SavedMembershipResult forged = new SavedMembershipResult(after.sourceRef(), after.date(), BigInteger.valueOf(999),
                after.house(), after.dynasty(), after.titleCensusComplete(), after.geographyComplete(), after.realm(), after.family(), after.states());
        check(M1RealmComparisons.compareSaved(complete, before, afterInput, forged, M1RealmComparisons.SavedScope.REALM)
                instanceof M1RealmComparisons.SavedUnavailable, "reconstructed result bypassed the original input/audit");
    }

    private static SavedMembershipInput later(SavedMembershipInput input) {
        var projection = input.projection();
        var updated = new SavedMembershipInput.SavedProjection(projection.titles(), projection.houses(), projection.characterHouses(),
                projection.characterHouseUnknown(), projection.characterSources(), projection.streamComplete(), projection.unknownKeyFields(),
                projection.rootKeys(), new ScalarField.Text("1066.11.15"));
        return new SavedMembershipInput(input.actor(), input.house(), input.dynasty(), input.sourceRef() + ":later", updated, input.mapping());
    }

    private static void monthlyCases(JsonNode corpus) {
        CampaignCadenceCodec.Candidate exact = null;
        CampaignCadenceCodec.Candidate absent = null;
        for (JsonNode row : corpus.path("cases")) {
            if (!row.path("request").path("operation").asText().equals("ordinary_sample_candidate")
                    || !row.path("expected").path("status").asText().equals("returned")) continue;
            var request = (CampaignCadenceCodec.Candidate) CampaignCadenceCodec.decode(row.get("request"));
            if (request.evaluate().isNull()) absent = request; else exact = request;
        }
        check(exact != null && absent != null, "actual monthly producer must include exact and nonboundary frames");
        check(M1RealmComparisons.qualifyMonthlyCache(exact, exact) == M1RealmComparisons.CacheStatus.CURRENT,
                "original exact monthly slot was not retained");
        check(M1RealmComparisons.qualifyMonthlyCache(absent, absent) == M1RealmComparisons.CacheStatus.NOT_AN_EXACT_MONTH_SLOT,
                "nonboundary null became a cached observed month");
        ObjectNode changed = exact.snapshot(); changed.put("revision", new BigInteger("9007199254740993"));
        var revised = new CampaignCadenceCodec.Candidate(changed, exact.startDate(), exact.machineId(), exact.observedAtUtc(),
                exact.campaignAnchor(), exact.months());
        check(M1RealmComparisons.qualifyMonthlyCache(exact, revised) == M1RealmComparisons.CacheStatus.FRAME_CHANGED,
                "monthly cache accepted a restamped uint64 revision");
        ObjectNode restamped = exact.snapshot(); restamped.put("source_extension", true);
        var sourceChange = new CampaignCadenceCodec.Candidate(restamped, exact.startDate(), exact.machineId(), exact.observedAtUtc(),
                exact.campaignAnchor(), exact.months());
        check(M1RealmComparisons.qualifyMonthlyCache(exact, sourceChange) == M1RealmComparisons.CacheStatus.FRAME_CHANGED,
                "monthly opaque source change did not invalidate cache");
    }
    private static List<BigInteger> big(List<Integer> input) {
        List<BigInteger> result = new ArrayList<>(); for (int value : input) result.add(BigInteger.valueOf(value)); return List.copyOf(result);
    }
    private static void check(boolean condition, String message) { checks++; if (!condition) throw new AssertionError(message); }
}
