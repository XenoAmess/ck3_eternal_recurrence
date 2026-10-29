package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Captured original data -> actual family/receipt producer -> generic and dedicated public DATA consumers. */
final class ContactScopeOriginalCodecTest {
    @Test void bothOriginalResultsRoundtripAndDedicatedMcpAddsOnlyItsActualReceipt()throws Exception {
        for(boolean projected:List.of(true,false)) {
            var known=ContactScopeReadProducerTest.producedOriginalRead(projected);
            var generic=ContactScopePublicCodec.encodeOriginal(known.value());ObjectNode original=parse(generic.bytes());
            assertFalse(original.has("original_read_receipt"));
            assertEquals(projected,original.has("backend_id"));
            assertEquals(known.value(),ContactScopePublicCodec.decodeOriginal(generic));
            assertEquals(original,parse(ContactScopePublicCodec.encodeOriginal(ContactScopePublicCodec.decodeOriginal(generic)).bytes()));
            for(String role:List.of("query_sequence","snapshot_revision","queried_revision","queried_native_revision","queried_connection_generation"))
                assertTrue(original.get(role).isTextual(),role);
            String payload=projected?"projected_contact_scope":"actual_contact_scope";
            assertTrue(original.get(payload).get("snapshot_revision").isTextual());
            assertTrue(original.get(payload).get("subject_army_id").isIntegralNumber());
            var response=ContactScopePublicCodec.capture(known.value().query(),known);
            RawJson dedicated=ContactScopePublicCodec.encode(response);ObjectNode envelope=parse(dedicated.bytes());
            assertEquals(parse(bytes(known.originalReceipt().toJson())),envelope.remove("original_read_receipt"));
            assertEquals(original,envelope);assertEquals(response,ContactScopePublicCodec.decode(dedicated));
            assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(dedicated));
            assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decode(generic));
        }
    }

    @Test void allPublicUint64RolesRejectWrongTokenDomainsMissingAndNoncanonicalStrings()throws Exception {
        for(boolean projected:List.of(true,false)) {
            ObjectNode original=parse(ContactScopePublicCodec.encodeOriginal(ContactScopeReadProducerTest.producedOriginalRead(projected).value()).bytes());
            for(String role:List.of("query_sequence","snapshot_revision","queried_revision","queried_native_revision","queried_connection_generation")) {
                for(String token:List.of("true","null","1","1.0","9007199254740993","\"01\"","\"+1\"","\"18446744073709551616\"")) {
                    ObjectNode bad=original.deepCopy();bad.set(role,value(token));
                    assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(new RawJson(bytes(bad))),role+"="+token);
                }
                ObjectNode missing=original.deepCopy();missing.remove(role);
                assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(new RawJson(bytes(missing))),role);
            }
            String payload=projected?"projected_contact_scope":"actual_contact_scope";
            for(String token:List.of("true","null","1","1.0","\"01\"","\"0\"")) {
                ObjectNode bad=original.deepCopy();object(bad.get(payload)).set("snapshot_revision",value(token));
                assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(new RawJson(bytes(bad))));
            }
            ObjectNode missing=original.deepCopy();object(missing.get(payload)).remove("snapshot_revision");
            assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(new RawJson(bytes(missing))));
        }
    }

    @Test void sourceMirrorsTypedIdsAndClosedEnvelopeStayStrictForBothConsumers()throws Exception {
        for(boolean projected:List.of(true,false)) {
            var known=ContactScopeReadProducerTest.producedOriginalRead(projected);
            ObjectNode original=parse(ContactScopePublicCodec.encodeOriginal(known.value()).bytes());
            ObjectNode mismatch=original.deepCopy();mismatch.put("queried_native_revision","18446744073709551615");
            if(original.path("queried_native_revision").textValue().equals("18446744073709551615"))mismatch.put("queried_native_revision","1");
            assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(new RawJson(bytes(mismatch))));
            ObjectNode unknown=original.deepCopy();unknown.put("invented",1);
            assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(new RawJson(bytes(unknown))));
            String payload=projected?"projected_contact_scope":"actual_contact_scope";
            ObjectNode history=parse(DriverJson.encode(known.value().normalizedResult()));
            int historyDate=i32(object(history.get(payload)).get("date_raw"));
            List<String> invalidBackends=projected?List.of("null","true","1","1.0","\"\"","\"   \"")
                    :List.of("null","true","1","1.0","\"\"","\"   \"","\"native-headless\"","\"unexpected-backend\"");
            for(String token:invalidBackends) {
                ObjectNode badBackend=original.deepCopy();badBackend.set("backend_id",value(token));
                assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(new RawJson(bytes(badBackend))),token);
                ObjectNode dedicatedBackend=badBackend.deepCopy();dedicatedBackend.set("original_read_receipt",known.originalReceipt().toJson());
                assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decode(new RawJson(bytes(dedicatedBackend))),token);
                ObjectNode badHistory=history.deepCopy();badHistory.set("backend_id",value(token));
                assertThrows(IllegalArgumentException.class,()->ContactScopeObservation.decodeHistoryResult(
                        DriverJson.object(bytes(badHistory),DriverJson.MAX_NATIVE_BYTES),historyDate),token);
            }
            if(projected) {
                ObjectNode missingBackend=original.deepCopy();missingBackend.remove("backend_id");
                assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(new RawJson(bytes(missingBackend))));
                ObjectNode dedicatedMissing=missingBackend.deepCopy();dedicatedMissing.set("original_read_receipt",known.originalReceipt().toJson());
                assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decode(new RawJson(bytes(dedicatedMissing))));
                ObjectNode missingHistory=history.deepCopy();missingHistory.remove("backend_id");
                assertThrows(IllegalArgumentException.class,()->ContactScopeObservation.decodeHistoryResult(
                        DriverJson.object(bytes(missingHistory),DriverJson.MAX_NATIVE_BYTES),historyDate));
            }
            for(String token:List.of("true","1.0","\"1\"")) {
                ObjectNode bad=original.deepCopy();object(bad.get(payload)).set("subject_army_id",value(token));
                assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(new RawJson(bytes(bad))));
                bad.set("original_read_receipt",known.originalReceipt().toJson());
                assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decode(new RawJson(bytes(bad))));
            }
            ObjectNode unavailable=empty().put("step",known.value().query().step()).put("status","unavailable").put("reason","actual provider unavailable");
            assertInstanceOf(ContactScopePublicCodec.Unavailable.class,ContactScopePublicCodec.decode(new RawJson(bytes(unavailable))));
            assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(new RawJson(bytes(unavailable))));
        }
    }

    @Test void genericDecoderRejectsDuplicateTrailingAndMalformedUtf8Transport()throws Exception {
        var observation=ContactScopeReadProducerTest.producedOriginalRead(true).value();
        String original=new String(ContactScopePublicCodec.encodeOriginal(observation).bytes(),StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(new RawJson((original+" false").getBytes(StandardCharsets.UTF_8))));
        assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(new RawJson(("{\"step\":\"wrong\","+original.substring(1)).getBytes(StandardCharsets.UTF_8))));
        assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decodeOriginal(new RawJson(new byte[]{'{','"',(byte)0xc3,'"',':','0','}'})));
    }
    private static JsonNode value(String token){return parse(("{\"value\":"+token+"}").getBytes(StandardCharsets.UTF_8)).get("value");}
}
