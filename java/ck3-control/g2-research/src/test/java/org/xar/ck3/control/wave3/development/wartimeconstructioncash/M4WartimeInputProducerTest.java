package org.xar.ck3.control.wave3.development.wartimeconstructioncash;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer.Context;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer.CopiedObject;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer.Outlay;
import static org.junit.jupiter.api.Assertions.*;

public final class M4WartimeInputProducerTest {
    @Test public void actualOriginalAllThirtyOneVectorsPassThroughTypedProducerAndPolicy() throws IOException {
        JsonNode corpus = M4OriginalCorpus.wartime();
        assertEquals("xar.wartime-construction-original-producer-golden.v1", corpus.path("schema").textValue());
        assertEquals(31, corpus.path("cases").size());
        assertEquals(2, corpus.path("original_consumer_regressions").size());
        assertFalse(corpus.path("machine_id").textValue().isEmpty());
        for (JsonNode vector : corpus.path("cases")) {
            JsonNode request = vector.get("request");
            var produced = M4WartimeInputProducer.produce(M4OriginalCorpus.context(request), M4OriginalCorpus.outlay(request));
            assertEquals(request, StrictJson.parse(produced.utf8()), vector.path("name").textValue());
            assertEquals(vector.get("expected"), StrictJson.parse(
                    WartimeConstructionCodec.encode(WartimeConstructionCash.observe(produced.input()))),
                    vector.path("name").textValue());
        }
    }

    @Test public void originalObjectBytesAndExtensionsSurviveAndCopiesCannotMutateFutureRequest() throws IOException {
        JsonNode request = M4OriginalCorpus.wartimeCase("exact_ample_threshold").get("request");
        Context original = M4OriginalCorpus.context(request);
        String snapshot = new String(original.snapshot().originalUtf8(), StandardCharsets.UTF_8);
        byte[] raw = ("{\"extension_float\":1.0,\"extension_null\":null,\"extension_empty\":[],"
                + snapshot.substring(1)).getBytes(StandardCharsets.UTF_8);
        CopiedObject copied = new CopiedObject(raw);
        byte[] expected = raw.clone(); raw[0] = '[';
        assertArrayEquals(expected, copied.originalUtf8());
        Context changed = new Context(copied, original.root(), original.spending(), original.market(),
                original.marketSourceFrame(), original.mercenaryLedger(), original.procurementDecision());
        var first = M4WartimeInputProducer.produce(changed, M4OriginalCorpus.outlay(request));
        String produced = new String(first.utf8(), StandardCharsets.UTF_8);
        assertTrue(produced.contains("\"extension_float\":1.0"));
        assertTrue(produced.contains("\"extension_null\":null"));
        assertTrue(produced.contains("\"extension_empty\":[]"));
        byte[] resultCopy = first.utf8(); resultCopy[0] = '[';
        byte[] sourceCopy = copied.originalUtf8(); sourceCopy[0] = '[';
        assertArrayEquals(first.utf8(), M4WartimeInputProducer.produce(changed, M4OriginalCorpus.outlay(request)).utf8());
    }

    @Test public void wrongNativeTokensReachOriginalValidationWithoutIntegerLaundering() throws IOException {
        JsonNode request = M4OriginalCorpus.wartimeCase("exact_ample_threshold").get("request");
        Context source = M4OriginalCorpus.context(request);
        String raw = new String(source.snapshot().originalUtf8(), StandardCharsets.UTF_8);
        for (String token : List.of("1.0", "true", "\"1\"")) {
            String malformed = raw.replaceFirst("\"native_revision\":[0-9]+", "\"native_revision\":" + token);
            assertNotEquals(raw, malformed);
            Context bad = new Context(new CopiedObject(malformed.getBytes(StandardCharsets.UTF_8)), source.root(),
                    source.spending(), source.market(), source.marketSourceFrame(), source.mercenaryLedger(), source.procurementDecision());
            assertThrows(IllegalArgumentException.class,
                    () -> M4WartimeInputProducer.produce(bad, M4OriginalCorpus.outlay(request)), token);
        }
        assertThrows(IllegalArgumentException.class, () -> new CopiedObject("[]".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> new CopiedObject("{\"a\":1,\"a\":2}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> new CopiedObject("{} {}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> new CopiedObject(new byte[] {(byte) 0xc3, 0x28}));
    }

    @Test public void unknownPendingAndEmptyMarketRemainDistinctAndNeverCreditProspectiveFunding() throws IOException {
        for (String name : List.of("market_unavailable", "complete_empty_market", "mercenary_pending_unknown")) {
            JsonNode request = M4OriginalCorpus.wartimeCase(name).get("request");
            var produced = M4WartimeInputProducer.produce(M4OriginalCorpus.context(request), M4OriginalCorpus.outlay(request));
            var decision = WartimeConstructionCash.observe(produced.input());
            assertFalse(decision.newSpendAllowed(), name);
            JsonNode output = StrictJson.parse(WartimeConstructionCodec.encode(decision));
            assertEquals(BigInteger.ZERO, output.path("loan_or_refund_credited_raw").bigIntegerValue());
            assertEquals(BigInteger.ZERO, output.path("future_income_credited_raw").bigIntegerValue());
            assertTrue(output.path("does_not_open_or_refresh_mercenary_procurement_epoch").booleanValue());
        }
        JsonNode base = M4OriginalCorpus.wartimeCase("exact_ample_threshold").get("request");
        Context context = M4OriginalCorpus.context(base);
        Context noMarket = new Context(context.snapshot(), context.root(), context.spending(), Optional.empty(),
                context.marketSourceFrame(), context.mercenaryLedger(), context.procurementDecision());
        JsonNode generated = StrictJson.parse(M4WartimeInputProducer.produce(noMarket, new Outlay("new_building", Optional.empty())).utf8());
        assertTrue(generated.get("market").isNull()); assertTrue(generated.get("construction_gold_raw").isNull());
        StrictJson.object(generated, Set.of("schema", "snapshot", "kind", "construction_gold_raw", "root", "spending",
                "market", "market_source_frame", "mercenary_ledger", "procurement_decision"));
    }
}
