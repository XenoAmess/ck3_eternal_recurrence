package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Closed DATA/role transport only. These objects are not private Captured material, actual membership or a current Driver. */
final class DriverGiftHistorySourceTest {
    @Test void pairSourceRoundTripsBothOriginalReturnedRolesWithoutInventingASecondAction() {
        var pair=pair();var source=new DriverActionHistoryCodec.Source("gift", "a".repeat(64),3,ref("receipt"),ref("record"),ActionReceipt.Outcome.APPLIED_CONFIRMED,pair);
        RawJson encoded=DriverActionHistoryCodec.encode(source);assertEquals(source,DriverActionHistoryCodec.decode(encoded));
        Obj submit=row(source,false);Obj receipt=row(source,true);
        var submitRoles=DriverActionHistoryCodec.giftPublicNumbers(submit).orElseThrow();
        var receiptRoles=DriverActionHistoryCodec.giftPublicNumbers(receipt).orElseThrow();
        assertEquals(original(),submitRoles.fromPublic(submitRoles.toPublic(original())));
        assertEquals(original(),receiptRoles.fromPublic(receiptRoles.toPublic(original())));
        assertEquals(new Text(StrictJson.UINT64_MAX.toString()),submitRoles.toPublic(original()).get("query_sequence"));
        assertFalse(submit.members().containsKey(DriverActionHistoryCodec.PART_FIELD));
    }
    @Test void publicationEvidenceUsesActualBusinessRolesInStableOrderWithoutImplementationOnlyRefs() {
        var material=pair();
        var evidence=DriverActionHistoryPublisher.publicationEvidence(List.of(ref("originals"),ref("archive"),ref("archive")),material);
        assertEquals(List.of(ref("originals"),ref("archive"),ref("submit"),ref("returned"),ref("read")),evidence);
        assertFalse(evidence.contains(ref("producer")));
        assertThrows(UnsupportedOperationException.class,()->evidence.add(ref("another")));
    }
    @Test void recordedImplementationMetadataSurvivesItsFileDisappearingWithoutBecomingBusinessEvidence(@TempDir Path temporary)throws Exception {
        // A real temporary implementation file is measured, then removed. This is historical DATA, never Game authority.
        Path implementation=temporary.resolve("implementation.jar");byte[] bytes="recorded implementation".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Files.write(implementation,bytes);
        var metadata=new ExactRef(implementation.toString(),bytes.length,ActionCodec.sha256(bytes));Files.delete(implementation);
        var material=new DriverActionHistoryCodec.CanonicalOnly(DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,
                List.of(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.READ,ref("actual-read"))),List.of(metadata));
        var source=new DriverActionHistoryCodec.Source("software-action","a".repeat(64),3,ref("receipt"),ref("record"),ActionReceipt.Outcome.APPLIED_CONFIRMED,material);
        var decoded=DriverActionHistoryCodec.decode(DriverActionHistoryCodec.encode(source));
        assertEquals(source,decoded);assertEquals(List.of(metadata),decoded.material().producers());
        var archived=List.of(ref("before-driver"),ref("after-driver"),ref("original-source"),ref("record"),ref("receipt"));
        var evidence=DriverActionHistoryPublisher.publicationEvidence(archived,decoded.material());
        assertEquals(List.of(ref("before-driver"),ref("after-driver"),ref("original-source"),ref("record"),ref("receipt"),ref("actual-read")),evidence);
        assertFalse(evidence.contains(metadata));assertFalse(Files.exists(implementation));
    }
    @Test void aProducerReferenceWithAnExplicitBusinessReadRoleIsStillEvidenceAndInvalidMetadataShapeStillFails() {
        var shared=ref("read-and-implementation");
        var material=new DriverActionHistoryCodec.CanonicalOnly(DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,
                List.of(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME,shared),
                        new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.READ,shared)),List.of(shared));
        assertEquals(List.of(ref("original-source"),shared),DriverActionHistoryPublisher.publicationEvidence(List.of(ref("original-source"),shared),material));
        assertThrows(IllegalArgumentException.class,()->new DriverActionHistoryCodec.CanonicalOnly(
                DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,material.evidence(),List.of()));
    }
    @Test void closedPairAndPartRulesRejectAliasesWrongRecordingAndWrongScalarTypes() {
        var source=new DriverActionHistoryCodec.Source("gift", "a".repeat(64),3,ref("receipt"),ref("record"),ActionReceipt.Outcome.APPLIED_CONFIRMED,pair());
        Obj raw=DriverJson.object(DriverActionHistoryCodec.encode(source).bytes(),262144);
        for(Value invalid:List.of(new Bool(true),new Text("ACCEPTED_RETURN"))) {
            var values=new LinkedHashMap<>(raw.members());values.put("recording",invalid);
            assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.decode(json(new Obj(values))));
        }
        var extra=new LinkedHashMap<>(raw.members());extra.put("legacy_ok",new Bool(true));
        assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.decode(json(new Obj(extra))));
        var receipt=new LinkedHashMap<>(row(source,true).members());receipt.put(DriverActionHistoryCodec.PART_FIELD,new Bool(true));
        assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.giftPublicNumbers(new Obj(receipt)));
        receipt.put(DriverActionHistoryCodec.PART_FIELD,new Text("GIFT_RECEIPT"));receipt.put("ok",new Text("true"));
        assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.giftPublicNumbers(new Obj(receipt)));
        var missing=new LinkedHashMap<>(row(source,true).members());missing.remove(DriverActionHistoryCodec.SOURCE_FIELD);
        assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.giftPublicNumbers(new Obj(missing)));
    }
    private static DriverActionHistoryCodec.GiftLegacyPair pair() {
        var roles=PublicNumbers.fromResults(json(original()),json(new Obj(Map.of("query_sequence",new Text(StrictJson.UINT64_MAX.toString())))));
        var evidence=List.of(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,ref("originals")),
                new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,ref("submit")),
                new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,ref("returned")),
                new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.READ,ref("read")));
        return new DriverActionHistoryCodec.GiftLegacyPair(ref("originals"),ref("submit"),ref("returned"),roles,roles,evidence,List.of(ref("producer")));
    }
    private static Obj row(DriverActionHistoryCodec.Source source,boolean receipt) {
        var values=new LinkedHashMap<String,Value>();values.put("index",new IntegerValue(BigInteger.valueOf(receipt?2:1)));
        values.put("command",new Text(receipt?DriverActionHistoryCodec.GIFT_RECEIPT_OPERATION:DriverActionHistoryCodec.GIFT_SUBMIT_OPERATION));
        values.put("ok",new Bool(true));values.put("result",original());values.put(DriverActionHistoryCodec.SOURCE_FIELD,DriverJson.object(DriverActionHistoryCodec.encode(source).bytes(),262144));
        if(receipt)values.put(DriverActionHistoryCodec.PART_FIELD,new Text("GIFT_RECEIPT"));return new Obj(values);
    }
    private static Obj original(){return new Obj(Map.of("query_sequence",new IntegerValue(StrictJson.UINT64_MAX)));}
    private static RawJson json(Value value){return new RawJson(DriverJson.encode(value));}
    private static ExactRef ref(String name){return new ExactRef("D:/source-only-gift-data/"+name,1,"b".repeat(64));}
}
