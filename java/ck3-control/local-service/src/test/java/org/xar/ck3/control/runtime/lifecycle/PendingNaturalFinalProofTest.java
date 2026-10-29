package org.xar.ck3.control.runtime.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification.FinalClearance;
import org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification.FinalProofDocument;

/** Sole actual final-proof codec and its typed producer closure. All fixtures are DATA, not Root/CK3 evidence. */
final class PendingNaturalFinalProofTest {
    private static final Instant OBSERVED=Instant.parse("2026-10-24T11:00:00.123456789Z");
    private static ExactRef ref(int n){return new ExactRef("D:/software-final-originals/"+n+".json",n+1,String.format("%064x",n+1));}
    private static FinalProofDocument document(boolean closed) {
        return new FinalProofDocument("xenoamess-full-tower-eb9d2c1186",OBSERVED,"a".repeat(64),"b".repeat(64),
                StrictJson.MAX_SAFE_INTEGER,"successor-run",74,closed?FinalClearance.CLOSED_AND_DATE_ADVANCED:FinalClearance.ALREADY_CLEAR,
                Integer.MAX_VALUE,ref(1),ref(2),ref(3),ref(4),
                new ExactRef("D:/software-final-originals/full-known.json",2_000_000,"c".repeat(64)),
                new ExactRef("D:/software-final-originals/full-sem.json",6_000_000,"d".repeat(64)),
                ref(7),ref(8),ref(9),Optional.of(ref(10)),ref(11),closed?List.of(ref(12),ref(13)):List.of(),
                closed?Optional.of(ref(14)):Optional.empty(),closed?Optional.of(ref(15)):Optional.empty(),closed?Optional.of(ref(16)):Optional.empty());
    }
    private static byte[] encode(FinalProofDocument value){return RootPendingNaturalSuccessionQualification.encodeFinalProof(value);}
    private static FinalProofDocument decode(byte[] value){return RootPendingNaturalSuccessionQualification.decodeFinalProof(value);}
    private static ObjectNode row(boolean close){var value=StrictJson.parse(encode(document(close)));if(value instanceof ObjectNode object)return object;throw new AssertionError("actual proof producer must encode an object");}
    private static void rejected(ObjectNode value){assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(value)));}

    @Test void producerCodecAndFiniteMaterialClosureRetainBothExactUiBranches() {
        for(boolean closed:List.of(false,true)) {
            var original=document(closed);byte[] bytes=encode(original);var decoded=decode(bytes);
            assertEquals(original,decoded);assertArrayEquals(bytes,encode(decoded));
            assertEquals(OBSERVED,decoded.observedAtUtc());assertEquals(StrictJson.MAX_SAFE_INTEGER,decoded.writerHeadSequence());
            assertEquals(2_000_000,decoded.originalKnown().bytes());assertEquals(6_000_000,decoded.originalSemantic().bytes());
            assertNotEquals(decoded.actualObservation(),decoded.originalKnown());
            var refs=decoded.materialReferences();assertEquals(closed?16:11,refs.size());
            assertTrue(refs.containsAll(List.of(decoded.actualOrdinarySnapshot(),decoded.actualObservation(),decoded.currentRoot(),
                    decoded.currentRootRead(),decoded.originalKnown(),decoded.originalSemantic(),decoded.pendingContinueReceipt(),
                    decoded.pendingContinueDriver(),decoded.canonicalPublication(),decoded.sourceQualification().orElseThrow(),decoded.initialTimeline())));
            decoded.close().ifPresent(value->assertTrue(refs.contains(value)));decoded.verifiedDateAdvance().ifPresent(value->assertTrue(refs.contains(value)));
            decoded.finalTimelineAfterDateAdvance().ifPresent(value->assertTrue(refs.contains(value)));assertTrue(refs.containsAll(decoded.postqueries()));
            assertThrows(UnsupportedOperationException.class,()->refs.add(ref(99)));
            var wire=StrictJson.parse(bytes);assertFalse(wire.get("replay_authorized").booleanValue());assertFalse(wire.get("business_reapply_authorized").booleanValue());
            if(!closed){assertTrue(wire.get("close").isNull());assertTrue(wire.get("verified_date_advance").isNull());assertTrue(wire.get("final_timeline_after_date_advance").isNull());}
        }
    }
    @Test void oldSchemaMissingNullAliasesAndMalformedReferencesDoNotSupplyHistoricalMaterials() {
        for(String field:List.of("writer_head_sequence","current_root_read","original_known","original_semantic","actual_observation",
                "actual_ordinary_snapshot","postqueries","close","verified_date_advance","final_timeline_after_date_advance")) {
            var missing=row(false);missing.remove(field);rejected(missing);
        }
        for(String field:List.of("current_root_read","original_known","original_semantic","actual_observation","actual_ordinary_snapshot","postqueries")) {
            var explicitNull=row(false);explicitNull.putNull(field);rejected(explicitNull);
        }
        for(boolean closed:List.of(false,true)) {
            var missingSource=row(closed);missingSource.remove("source_qualification");
            var withoutSource=decode(StrictJson.canonical(missingSource));
            assertTrue(withoutSource.sourceQualification().isEmpty());
            assertEquals(closed?15:10,withoutSource.materialReferences().size());
            missingSource.putNull("source_qualification");assertEquals(withoutSource,decode(StrictJson.canonical(missingSource)));
            assertEquals(withoutSource,decode(encode(withoutSource)));
            var malformedSource=row(closed);malformedSource.put("source_qualification",true);rejected(malformedSource);
            var emptySource=row(closed);assertInstanceOf(ObjectNode.class,emptySource.get("source_qualification")).put("bytes",0);rejected(emptySource);
        }
        var legacy=row(false);legacy.put("schema","xar.java.post-continue-natural-finalization/v1");rejected(legacy);
        var alias=row(false);alias.set("root_read",alias.remove("current_root_read"));rejected(alias);
        var extra=row(false);extra.put("ui_clearance_qualified",true);rejected(extra);
        for(String field:List.of("current_root_read","original_known","actual_observation")) {
            var empty=row(false);((ObjectNode)empty.get(field)).put("bytes",0);rejected(empty);
            var badSha=row(false);((ObjectNode)badSha.get(field)).put("sha256","rounded-or-unbound");rejected(badSha);
        }
        var badUtc=row(false);badUtc.put("observed_at_utc","2026-10-24T11:00:00");rejected(badUtc);
    }
    @Test void integerDomainAndAuthorityFlagsRejectJsonEqualityAndRoleAliases() {
        for(String field:List.of("writer_head_sequence","successor_character_id","date_raw")) {
            for(JsonNode bad:List.of(JsonNodeFactory.instance.booleanNode(true),JsonNodeFactory.instance.numberNode(1.0),JsonNodeFactory.instance.textNode("1"))) {
                var wire=row(false);wire.set(field,bad);rejected(wire);
            }
        }
        var unsafe=row(false);unsafe.put("writer_head_sequence",StrictJson.MAX_SAFE_INTEGER+1);rejected(unsafe);
        var negative=row(false);negative.put("writer_head_sequence",-1);rejected(negative);
        var noActor=row(false);noActor.put("successor_character_id",0);rejected(noActor);
        var dateOverflow=row(false);dateOverflow.put("date_raw",(long)Integer.MAX_VALUE+1);rejected(dateOverflow);
        for(String field:List.of("replay_authorized","business_reapply_authorized")) {
            var yes=row(false);yes.put(field,true);rejected(yes);
            var number=row(false);number.put(field,0);rejected(number);
            var missing=row(false);missing.remove(field);rejected(missing);
        }
        var badModal=row(false);badModal.put("modal","CLEARED_FROM_ACK");rejected(badModal);
    }
    @Test void closeDateAndIndependentQueryMaterialsAreOneContractWithoutAnInventedFallback() {
        var noDate=row(true);noDate.putNull("verified_date_advance");rejected(noDate);
        var noLaterQuery=row(true);noLaterQuery.putNull("final_timeline_after_date_advance");rejected(noLaterQuery);
        var noQueries=row(true);noQueries.putArray("postqueries");rejected(noQueries);
        var duplicate=row(true);duplicate.withArray("postqueries").add(duplicate.withArray("postqueries").get(0));rejected(duplicate);
        var invented=row(false);invented.putArray("postqueries").add(ref(12).toJson());rejected(invented);
        var modalMismatch=row(true);modalMismatch.put("modal","already_clear");rejected(modalMismatch);
        var tooMany=row(true);var array=tooMany.putArray("postqueries");for(int i=0;i<9;i++)array.add(ref(20+i).toJson());rejected(tooMany);
        var mutable=new ArrayList<>(List.of(ref(12),ref(13)));var value=document(true);
        var copied=new FinalProofDocument(value.machineId(),value.observedAtUtc(),value.pendingCauseSha256(),value.writerHeadSha256(),value.writerHeadSequence(),
                value.newEpisodeRunId(),value.successorCharacterId(),value.modal(),value.dateRaw(),value.actualOrdinarySnapshot(),value.actualObservation(),value.currentRoot(),
                value.currentRootRead(),value.originalKnown(),value.originalSemantic(),value.pendingContinueReceipt(),value.pendingContinueDriver(),value.canonicalPublication(),
                value.sourceQualification(),value.initialTimeline(),mutable,value.close(),value.verifiedDateAdvance(),value.finalTimelineAfterDateAdvance());
        mutable.clear();assertEquals(2,decode(encode(copied)).postqueries().size());
        String original=new String(encode(document(false)),java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->decode((original+"{}").getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class,()->decode(original.replaceFirst("\\{","{\"schema\":\"duplicate\",").getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
}
