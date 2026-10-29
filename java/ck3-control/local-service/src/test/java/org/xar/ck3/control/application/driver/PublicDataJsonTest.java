package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.contracts.semantic.NativeOneLifeSettlement;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof;

/** Exercises the real Driver producer's full-token lane and the shared public DATA consumers. */
final class PublicDataJsonTest {
    private static RawJson raw(String json) { return new RawJson(json.getBytes(StandardCharsets.UTF_8)); }
    @Test void actualLargeDriverProducerRoundtripKeepsJsonTypesWithoutExpandingTheSmallContractLane() {
        RawJson original = raw("{\"payload\":\"" + "x".repeat(1100000)
                + "\",\"date_raw\":246,\"revision\":18446744073709551615,\"ratio\":1.25e0}");
        var produced = DriverJson.object(original.bytes(), RawJson.MAXIMUM_BYTES);
        var expected = OpportunityJson.toNode(produced);
        assertThrows(IllegalArgumentException.class, () -> StrictJson.parse(original.bytes(), RawJson.MAXIMUM_BYTES));
        var encoded = PublicDataJson.encode(expected); var decoded = PublicDataJson.object(encoded);
        assertEquals(expected, decoded); assertTrue(decoded.get("date_raw").isIntegralNumber());
        assertTrue(decoded.get("ratio").isFloatingPointNumber());
        assertEquals(new BigInteger("18446744073709551615"), decoded.get("revision").bigIntegerValue());
        assertEquals(1100000, decoded.get("payload").textValue().length());
    }
    @Test void actualDriverInspectionDataPreservesMissingNullAndNumericCountersThroughTheSoleCodec() {
        for (String json : List.of("{\"ready\":false,\"commit_serial\":null}",
                "{\"ready\":false,\"revision\":null,\"commit_serial\":7}",
                "{\"ready\":true,\"revision\":18446744073709551615,\"commit_serial\":7,\"date_raw\":246}")) {
            var produced = DriverJson.object(raw(json).bytes(), RawJson.MAXIMUM_BYTES);
            var original = PublicDataJson.encode(OpportunityJson.toNode(produced));
            var encoded = LifecyclePublicResultCodec.encodeSettlementInspection(original);
            assertEquals(PublicDataJson.object(original), PublicDataJson.object(
                    LifecyclePublicResultCodec.decodeSettlementInspection(encoded)));
            var result = PublicDataJson.object(encoded);
            if (result.hasNonNull("revision")) assertEquals("18446744073709551615", result.get("revision").textValue());
            if (result.hasNonNull("commit_serial")) assertTrue(result.get("commit_serial").isIntegralNumber());
            assertEquals(PublicDataJson.object(original).has("revision"), result.has("revision"));
        }
    }
    @Test void malformedTokensAndTheExistingDriverDepthLimitRemainRejected() {
        assertThrows(IllegalArgumentException.class, () -> PublicDataJson.object(raw("{\"a\":1,\"a\":2}")));
        RawJson deep = raw("{\"a\":".repeat(66) + "null" + "}".repeat(66));
        assertThrows(IllegalArgumentException.class, () -> PublicDataJson.object(deep));
        assertThrows(IllegalArgumentException.class, () -> PublicDataJson.object(raw("[]")));
    }
    /** This is a width boundary specimen; it does not claim that MAX rejected snapshots actually occurred. */
    @Test void twoProvedDiagnosticCountRolesDecodeExactlyWithoutReinterpretingRejectedRawRevision() {
        var wire = StrictJson.object().put("format_version", 1).put("snapshot_id", "fixture-snapshot")
                .put("revision", "2").put("native_revision", "9").put("date_raw", 246)
                .put("paused", true).put("map_ready", true).put("speed", 3).put("episode_run_id", "fixture-episode").put("episode_character_id", 73);
        wire.putObject("played_character").put("character_id", 73).put("alive", true);
        wire.putNull("active_event"); wire.putNull("pending_character_interaction"); wire.putNull("one_life_terminal_reason");
        wire.putArray("active_wars"); wire.putArray("player_armies");
        wire.putArray("native_command_history").add(-0.0).add("opaque").addArray().add(1.0);
        var diagnostics = wire.putObject("diagnostics").put("rejected_state_snapshot_count", "18446744073709551615")
                .put("snapshot_publish_diagnostic_count", "18446744073709551615");
        diagnostics.putObject("last_rejected_state_snapshot").put("revision", true);
        var original = PublicSnapshotCodec.decode(PublicDataJson.encode(wire));
        var observed = OpportunityJson.object(original.get("diagnostics"), "diagnostics");
        var opaqueHistory=OpportunityJson.array(original.get("native_command_history"),"history");
        assertEquals(new OpportunityJson.DecimalValue("-0.0"),opaqueHistory.getFirst());
        assertEquals(new OpportunityJson.DecimalValue("1.0"),OpportunityJson.array(opaqueHistory.get(2),"opaque nested history").getFirst());
        for (String name : List.of("rejected_state_snapshot_count", "snapshot_publish_diagnostic_count"))
            assertEquals(new BigInteger("18446744073709551615"), OpportunityJson.integer(observed.get(name), name));
        assertTrue(OpportunityJson.bool(OpportunityJson.object(observed.get("last_rejected_state_snapshot"), "raw rejected diagnostic").get("revision"), "raw revision"));
        var unsafe = wire.deepCopy(); var unsafeDiagnostics=(com.fasterxml.jackson.databind.node.ObjectNode)unsafe.get("diagnostics");
        ((com.fasterxml.jackson.databind.node.ObjectNode)unsafeDiagnostics.get("last_rejected_state_snapshot"))
                .put("revision", new BigInteger("18446744073709551615"));
        assertThrows(IllegalArgumentException.class, () -> PublicSnapshotCodec.decode(PublicDataJson.encode(unsafe)));
        var wrongCount = wire.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode)wrongCount.get("diagnostics")).put("rejected_state_snapshot_count", "18446744073709551616");
        assertThrows(IllegalArgumentException.class, () -> PublicSnapshotCodec.decode(PublicDataJson.encode(wrongCount)));
    }
    @Test void wideRejectedRevisionRoundTripsThroughFullAndSemanticOnlyDataWithExplicitRepresentation() {
        for(BigInteger revision:List.of(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER).add(BigInteger.ONE),StrictJson.UINT64_MAX)) {
            for(boolean semanticOnly:List.of(false,true)) {
                RawJson original=rejectedRevisionOriginal(java.util.Optional.of(new OpportunityJson.IntegerValue(revision)),semanticOnly);
                RawJson encoded=PublicSnapshotCodec.encodePlanningSnapshotData(original);
                var tree=PublicDataJson.object(encoded);
                var rejected=tree.get("diagnostics").get("last_rejected_state_snapshot");
                assertEquals(revision.toString(),rejected.get("revision").textValue());
                assertEquals(RejectedSnapshotPublicEncoding.ENCODING_SCHEMA,rejected.get(RejectedSnapshotPublicEncoding.ENCODING_FIELD).textValue());
                assertEquals(DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(
                        PublicSnapshotCodec.decodePlanningSnapshotData(encoded).bytes(),RawJson.MAXIMUM_BYTES));
                if(!semanticOnly)assertEquals(DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(
                        PublicSnapshotCodec.decodeSemanticData(PublicSnapshotCodec.encodeSemanticData(original)).bytes(),RawJson.MAXIMUM_BYTES));
            }
        }
    }

    @Test void rejectedRawTypesAndAbsenceSurviveWithoutBecomingIdentityRoles() {
        var cases=new java.util.ArrayList<java.util.Optional<OpportunityJson.Value>>();
        cases.add(java.util.Optional.empty());
        for(OpportunityJson.Value value:List.of(OpportunityJson.Nil.INSTANCE,new OpportunityJson.Bool(true),
                new OpportunityJson.Text(StrictJson.UINT64_MAX.toString()),new OpportunityJson.Text("01"),
                new OpportunityJson.IntegerValue(BigInteger.valueOf(-1)),
                new OpportunityJson.IntegerValue(BigInteger.ZERO),
                new OpportunityJson.IntegerValue(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)),
                new OpportunityJson.DecimalValue("-0.0"),new OpportunityJson.DecimalValue("1.2500e+2"),
                new OpportunityJson.Obj(java.util.Map.of()),new OpportunityJson.Arr(List.of())))cases.add(java.util.Optional.of(value));
        for(var revision:cases)for(boolean semanticOnly:List.of(false,true)) {
            RawJson original=rejectedRevisionOriginal(revision,semanticOnly);
            RawJson encoded=PublicSnapshotCodec.encodePlanningSnapshotData(original);
            var rejected=PublicDataJson.object(encoded).get("diagnostics").get("last_rejected_state_snapshot");
            assertFalse(rejected.has(RejectedSnapshotPublicEncoding.ENCODING_FIELD));
            assertEquals(revision.isPresent(),rejected.has("revision"));
            assertEquals(DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(
                    PublicSnapshotCodec.decodePlanningSnapshotData(encoded).bytes(),RawJson.MAXIMUM_BYTES));
        }
    }

    @Test void malformedRejectedRepresentationAndUnrelatedUnsafeNumbersRemainRejected() {
        assertThrows(NullPointerException.class,()->RejectedSnapshotPublicEncoding.toPublic(null));
        assertThrows(NullPointerException.class,()->RejectedSnapshotPublicEncoding.fromPublic(null));
        RawJson original=rejectedRevisionOriginal(java.util.Optional.of(new OpportunityJson.IntegerValue(StrictJson.UINT64_MAX)),false);
        var wire=PublicDataJson.object(PublicSnapshotCodec.encodePlanningSnapshotData(original));
        String field=RejectedSnapshotPublicEncoding.ENCODING_FIELD;
        for(OpportunityJson.Value marker:List.of(OpportunityJson.Nil.INSTANCE,new OpportunityJson.Bool(true),
                new OpportunityJson.Text("unknown/v1"),new OpportunityJson.Obj(java.util.Map.of()),
                new OpportunityJson.Arr(List.of()),new OpportunityJson.IntegerValue(StrictJson.UINT64_MAX))) {
            var invalid=wire.deepCopy();
            ((com.fasterxml.jackson.databind.node.ObjectNode)invalid.get("diagnostics").get("last_rejected_state_snapshot"))
                    .set(field,DriverJson.toNode(marker));
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decodePlanningSnapshotData(PublicDataJson.encodeFullMaterial(invalid)));
        }
        for(String revision:List.of("\"01\"","\"+1\"","\" 1\"","\"1.0\"","\"0\"","\"1\"","\"9007199254740991\"", "\"18446744073709551616\"","null","true","1","1.0","{}","[]")) {
            var invalid=wire.deepCopy();
            ((com.fasterxml.jackson.databind.node.ObjectNode)invalid.get("diagnostics").get("last_rejected_state_snapshot"))
                    .set("revision",PublicDataJson.object(raw("{\"value\":"+revision+"}")).get("value"));
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decodePlanningSnapshotData(PublicDataJson.encodeFullMaterial(invalid)),revision);
        }
        var missing=wire.deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode)missing.get("diagnostics").get("last_rejected_state_snapshot")).remove("revision");
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decodePlanningSnapshotData(PublicDataJson.encodeFullMaterial(missing)));
        for(OpportunityJson.Value marker:List.of(OpportunityJson.Nil.INSTANCE,new OpportunityJson.Bool(false),
                new OpportunityJson.Text(RejectedSnapshotPublicEncoding.ENCODING_SCHEMA))) {
            var collision=PublicDataJson.object(original);
            ((com.fasterxml.jackson.databind.node.ObjectNode)collision.get("diagnostics").get("last_rejected_state_snapshot"))
                    .set(field,DriverJson.toNode(marker));
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodePlanningSnapshotData(PublicDataJson.encodeFullMaterial(collision)));
        }
        var unrelated=PublicDataJson.object(original);unrelated.putObject("unrelated").put(field,StrictJson.UINT64_MAX);
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodePlanningSnapshotData(PublicDataJson.encodeFullMaterial(unrelated)));
        for(BigInteger outside:List.of(StrictJson.UINT64_MAX.add(BigInteger.ONE),BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER).negate().subtract(BigInteger.ONE))) {
            RawJson invalid=rejectedRevisionOriginal(java.util.Optional.of(new OpportunityJson.IntegerValue(outside)),false);
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodePlanningSnapshotData(invalid));
        }
    }

    private static RawJson rejectedRevisionOriginal(java.util.Optional<OpportunityJson.Value> revision,boolean semanticOnly) {
        var base=DriverJson.object(raw("""
                {"format_version":1,"snapshot_id":"diagnostic-data","revision":2,"native_revision":9,"date_raw":246,
                 "paused":true,"map_ready":true,"speed":3,"episode_run_id":"diagnostic-episode","episode_character_id":73,
                 "played_character":{"character_id":73,"alive":true},"active_event":null,"pending_character_interaction":null,
                 "one_life_terminal_reason":null,"active_wars":[],"player_armies":[],"diagnostics":{},"native_command_history":[]}
                """).bytes(),RawJson.MAXIMUM_BYTES);
        var rejected=new OpportunityJson.Obj(java.util.Map.of("snapshot_id",new OpportunityJson.Text("native-rejected"),
                "date_raw",new OpportunityJson.IntegerValue(BigInteger.valueOf(246)),"speed",new OpportunityJson.IntegerValue(BigInteger.valueOf(3)),
                "paused",new OpportunityJson.Bool(true),"map_ready",new OpportunityJson.Bool(true),
                "error_type",new OpportunityJson.Text("ValueError"),"error",new OpportunityJson.Text("played_character must be object")));
        if(revision.isPresent())rejected=rejected.with("revision",revision.orElseThrow());
        var diagnostics=new OpportunityJson.Obj(java.util.Map.of("last_rejected_state_snapshot",rejected,
                "rejected_state_snapshot_count",new OpportunityJson.IntegerValue(BigInteger.ONE),
                "snapshot_publish_diagnostic_count",new OpportunityJson.IntegerValue(BigInteger.ZERO)));
        var fields=new java.util.LinkedHashMap<>(base.with("diagnostics",diagnostics).members());
        if(semanticOnly)fields.remove("native_command_history");
        return RawJson.fullMaterial(DriverJson.encode(new OpportunityJson.Obj(fields)));
    }

    @Test void sourceDecimalTokensSurviveProjectionAcrossKnownAndOpaqueFieldsWithoutDoubleConversion() {
        var original=raw("{\"revision\":18446744073709551615,\"active_event\":{\"options\":[{\"strategy_score\":-0.0}]},"
                +"\"native_command_history\":[{\"opaque\":[1.0,-0.0,1.2500e+2]}],\"original_metric\":1.0}");
        var projected=PublicDataJson.object(original);projected.put("revision","18446744073709551615");
        var wire=PublicDataJson.encodePreservingDecimals(projected,original);
        var reverse=PublicDataJson.object(wire);reverse.put("revision",new BigInteger("18446744073709551615"));
        assertEquals(DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(
                PublicDataJson.encodePreservingDecimals(reverse,wire).bytes(),RawJson.MAXIMUM_BYTES));
        String emitted=new String(wire.bytes(),StandardCharsets.UTF_8);
        assertTrue(emitted.contains("-0.0"));assertTrue(emitted.contains("1.2500e+2"));
        var changed=projected.deepCopy();changed.put("original_metric",2.0);
        assertThrows(IllegalArgumentException.class,()->PublicDataJson.encodePreservingDecimals(changed,original));
        var changedCategory=projected.deepCopy();changedCategory.put("original_metric",1);
        assertThrows(IllegalArgumentException.class,()->PublicDataJson.encodePreservingDecimals(changedCategory,original));
        var removed=projected.deepCopy();removed.remove("native_command_history");
        assertThrows(IllegalArgumentException.class,()->PublicDataJson.encodePreservingDecimals(removed,original));
    }
    @Test void actualSoleSettlementNormalizerProducesRatioFloatThenInspectionAndDeathRetainBinary64() {
        var nativeSettlement=StrictJson.object().put("ready",true).put("commit_serial",1).put("source_character_id",73)
                .put("record_candidate",0).put("old_record",0).put("record_delta",0).put("blessing_count",0)
                .put("refusal_count",0).put("contract_progress",0).put("record_written",false);
        nativeSettlement.putObject("final_score").put("raw",-1).put("scale",BigInteger.TEN.pow(400));
        nativeSettlement.putObject("score_before_reject").put("raw",BigInteger.TEN.pow(100).add(BigInteger.ONE)).put("scale",BigInteger.TEN.pow(100));
        var actual=(NativeOneLifeSettlement.Ready)NativeOneLifeSettlement.decodeNative(nativeSettlement);
        assertEquals(Double.doubleToRawLongBits(-0.0),Double.doubleToRawLongBits(((NativeOneLifeSettlement.Fractional)actual.finalScore()).value()));
        assertEquals(1.0,((NativeOneLifeSettlement.Fractional)actual.scoreBeforeReject()).value());
        var inspection=StrictJson.object().put("revision",new BigInteger("18446744073709551615"));
        inspection.set("one_life_settlement",NativeOneLifeSettlement.encode(actual));
        var original=PublicDataJson.encode(inspection);var wire=LifecyclePublicResultCodec.encodeSettlementInspection(original);
        var back=LifecyclePublicResultCodec.decodeSettlementInspection(wire);
        assertEquals(DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(back.bytes(),RawJson.MAXIMUM_BYTES));
        var settlement=OpportunityJson.object(DriverJson.object(back.bytes(),RawJson.MAXIMUM_BYTES).get("one_life_settlement"),"settlement");
        var normalized=(NativeOneLifeSettlement.Ready)NativeOneLifeSettlement.decodeNormalized(DriverJson.encode(settlement),RawJson.MAXIMUM_BYTES);
        assertEquals(Double.doubleToRawLongBits(-0.0),Double.doubleToRawLongBits(((NativeOneLifeSettlement.Fractional)normalized.finalScore()).value()));
        assertEquals(1.0,((NativeOneLifeSettlement.Fractional)normalized.scoreBeforeReject()).value());
        var death=StrictJson.object().put("revision",1);death.set("score",NativeOneLifeSettlement.encodeScore(actual.finalScore()));
        var originalDeath=PublicDataJson.encode(death);var publicDeath=LifecyclePublicResultCodec.encode(LifecycleTransitionProof.Kind.DEATH,originalDeath);
        assertEquals(DriverJson.object(originalDeath.bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(
                LifecyclePublicResultCodec.decode(LifecycleTransitionProof.Kind.DEATH,publicDeath).bytes(),RawJson.MAXIMUM_BYTES));
    }
}
