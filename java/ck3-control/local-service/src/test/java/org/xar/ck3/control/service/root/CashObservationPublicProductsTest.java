package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.mcp.PublicMcpNativeAdapter;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.CashObservationPublicCodec.*;

/** Actual public registration/strict argument producer. Callbacks are DATA and grant no current Root or read authority. */
final class CashObservationPublicProductsTest {
    private static final ExactRef SOURCE=new ExactRef("controlled-public-cash-no-authority",1,"a".repeat(64));
    @Test void actualTypedPublicBinderDefersCallsAndPreservesNullMissingAndSelectors()throws Exception {
        var registry=new PublicBindings();var calls=new AtomicInteger();
        RootCashObservationPublicProducts.register(registry,SOURCE,current->{calls.incrementAndGet();assertEquals(Presence.NULL,current.sampling().presence());assertEquals(Presence.MISSING,current.window().presence());return response("current");},
            construction->{calls.incrementAndGet();assertEquals(new BigInteger("18446744073709551615"),construction.reserve());return response("construction");},
            termination->{calls.incrementAndGet();assertEquals(Integer.MAX_VALUE,termination.warId());assertEquals(Outcome.SURRENDER,termination.outcome());return response("termination");});
        var current=registry.lookup(method("query_war_cash_current_resources_private_v1")).orElseThrow();
        var construction=registry.lookup(method("query_construction_cash_outcome_private_v1")).orElseThrow();var termination=registry.lookup(method("query_war_cash_termination_send_costs_private_v1")).orElseThrow();
        assertEquals(Current.class,current.requestType());assertEquals(Construction.class,construction.requestType());assertEquals(Termination.class,termination.requestType());
        assertThrows(IllegalArgumentException.class,()->current.invoke(args("{\"expected_revision\":1}")));assertEquals(0,calls.get());
        registry.freeze(Set.of(method("query_war_cash_current_resources_private_v1"),method("query_construction_cash_outcome_private_v1"),method("query_war_cash_termination_send_costs_private_v1")));
        current.invoke(args("{\"expected_revision\":\"1\",\"payment_sampling\":null}"));
        construction.invoke(args("{\"expected_revision\":1,\"reserve_gold_raw\":\"18446744073709551615\",\"existing_commitment_gold_raw\":0,\"horizon_months\":24}"));
        termination.invoke(args("{\"expected_revision\":1,\"war_id\":2147483647,\"outcome\":\"surrender\"}"));assertEquals(3,calls.get());
        assertThrows(IllegalArgumentException.class,()->current.invoke(args("{\"expected_revision\":true}")));assertEquals(3,calls.get());
        assertOriginalDeclarations();
    }
    @Test void malformedMoneyRevisionModeAndOutcomeCannotReachARead() {
        for(String revision:new String[]{"true","1.0","null","9007199254740992","\"01\"","0"})assertThrows(IllegalArgumentException.class,()->CashObservationPublicCodec.current(args("{\"expected_revision\":"+revision+"}")));
        for(String option:new String[]{"\"enable\"","\"unknown\"","true"})assertThrows(IllegalArgumentException.class,()->CashObservationPublicCodec.current(args("{\"expected_revision\":1,\"payment_sampling\":"+option+"}")));
        assertThrows(IllegalArgumentException.class,()->CashObservationPublicCodec.current(args("{\"expected_revision\":1,\"payment_window_contract\":\"same_owned_process_no_load_v1\"}")));
        var enable=CashObservationPublicCodec.current(args("{\"expected_revision\":1,\"payment_sampling\":\"enable\",\"payment_window_contract\":\"same_owned_process_no_load_v1\"}"));assertEquals(Sampling.ENABLE,enable.sampling().value().orElseThrow());
        for(String raw:new String[]{"true","1.0","-1","null","9007199254740992"})assertThrows(IllegalArgumentException.class,()->CashObservationPublicCodec.construction(args("{\"expected_revision\":1,\"reserve_gold_raw\":"+raw+",\"existing_commitment_gold_raw\":0,\"horizon_months\":1}")));
        assertThrows(IllegalArgumentException.class,()->CashObservationPublicCodec.termination(args("{\"expected_revision\":1,\"war_id\":true,\"outcome\":\"surrender\"}")));
        assertThrows(IllegalArgumentException.class,()->CashObservationPublicCodec.termination(args("{\"expected_revision\":1,\"war_id\":1,\"outcome\":\"total_free\"}")));
    }
    @Test void declaredWideMoneyAndUint64RoundTripButUnknownUnsafeFieldFails() {
        var raw=new RawJson("{\"snapshot_revision\":18446744073709551615,\"current_treasury\":{\"raw\":-9223372036854775808,\"scale\":100000},\"resource_raw_native\":[9223372036854775807],\"missing\":null}".getBytes(StandardCharsets.UTF_8));
        var wire=CashObservationCodec.publicWire(raw);var n=PublicDataJson.object(wire);assertEquals("18446744073709551615",n.path("snapshot_revision").textValue());assertEquals("-9223372036854775808",n.path("current_treasury").path("raw").textValue());assertTrue(n.path("missing").isNull());
        assertEquals(PublicDataJson.encode(PublicDataJson.object(raw)),CashObservationCodec.nativeWire(wire));
        assertThrows(IllegalArgumentException.class,()->CashObservationCodec.publicWire(new RawJson("{\"unknown_counter\":18446744073709551615}".getBytes(StandardCharsets.UTF_8))));
        assertThrows(IllegalArgumentException.class,()->CashObservationCodec.nativeWire(new RawJson("{\"snapshot_revision\":18446744073709551615}".getBytes(StandardCharsets.UTF_8))));
    }
    private static Response response(String route){return new Response(new RawJson(("{\"schema\":\"controlled-data-only\",\"route\":\""+route+"\"}").getBytes(StandardCharsets.UTF_8)));}
    private static PublicMethod method(String name){return java.util.Arrays.stream(PublicMethod.values()).filter(m->m.pythonName().equals(name)).findFirst().orElseThrow();}
    private static PublicBindings.Arguments args(String value){return PublicBindings.present(new RawJson(value.getBytes(StandardCharsets.UTF_8)));}
    private static void assertOriginalDeclarations() throws java.io.IOException {
        try (var input=CashObservationPublicProductsTest.class.getResourceAsStream("/mcp/original-tool-catalog.json")) {
            assertNotNull(input,"actual original declarations resource required");
            byte[] bytes=input.readNBytes(65537);
            assertTrue(bytes.length<=65536,"original declarations exceed bounded resource read");
            var catalog=PublicDataJson.object(new RawJson(bytes));
            assertEquals("xar.original-mcp-declarations/v2",catalog.path("schema").textValue());
            var declarations=catalog.path("declarations");assertTrue(declarations.isArray());
            for (var expected:Set.of(PublicMethod.QUERY_WAR_CASH_CURRENT_RESOURCES_PRIVATE_V1,
                    PublicMethod.QUERY_CONSTRUCTION_CASH_OUTCOME_PRIVATE_V1,
                    PublicMethod.QUERY_WAR_CASH_TERMINATION_SEND_COSTS_PRIVATE_V1)) {
                String name="ck3_"+expected.pythonName();
                assertSame(expected,PublicMcpNativeAdapter.expectedServiceMethod(name));
                long count=0;
                for (var declaration:declarations) if(name.equals(declaration.path("name").textValue()))count++;
                assertEquals(1L,count,name+" must have exactly one actual original declaration");
            }
        }
    }
}
