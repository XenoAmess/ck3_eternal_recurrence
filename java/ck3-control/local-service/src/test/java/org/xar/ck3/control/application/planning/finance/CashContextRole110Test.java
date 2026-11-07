package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import com.fasterxml.jackson.databind.JsonNode;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.warbudget.BudgetPoliticalStakesCodec;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashCodec;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashPolicy;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCash;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCodec;
import org.xar.ck3.control.wave3.planning.warpriorityfocus.WarCashFocusProjection;
import org.xar.ck3.control.wave3.planning.warpriorityfocus.WarCashFocusProjectionCodec;

/** Declared SDK role only. The Archive caller is source/typing reviewed; full archive orchestration is a separate P111 test.
 * Future Construction command representation changes are intentional; no issued command or original archive is rewritten.
 */
final class CashContextRole110Test {
    private static final int LIMIT=FullJsonTree.MAXIMUM_BYTES;
    private static JsonNode giftCases,cashCases,focusCases;
    private static Arr history;
    @BeforeAll static void load()throws Exception {
        callFixture("retainedInputs",new Class<?>[]{});
        Field field=FinancingSnapshotRole107Test.class.getDeclaredField("unrelatedHistory");field.setAccessible(true);history=(Arr)field.get(null);
        giftCases=FullJsonTree.parse(resource("/giftwarcash/original-producer-golden.json"),LIMIT).get("cases");
        cashCases=FullJsonTree.parse((byte[])callFixture("gzip",new Class<?>[]{String.class},"/wartimeconstructioncash/original-producer-golden.json.gz"),LIMIT).get("cases");
        focusCases=FullJsonTree.parse(resource("/warpriorityfocus/golden.json"),LIMIT).get("cases");
    }

    @Test void allGiftRequestsAndDecisionsRetainTypedValuesWithLargeUnconsumedHistory() {
        int count=0,max=0;
        for(JsonNode vector:giftCases) {
            Obj original=json(FullJsonTree.encode(vector.get("request"),LIMIT));Obj large=large(original);
            byte[] before=DriverJson.encode(large);Obj projected=OrdinaryFinanceCollector.projectCashContext(large);
            var reference=GiftWarCashCodec.decode(DriverJson.encode(original));var actual=GiftWarCashCodec.decode(DriverJson.encode(projected));
            assertEquals(reference,actual,vector.path("name").textValue());
            var expected=GiftWarCashPolicy.assess(reference);assertEquals(expected,GiftWarCashPolicy.assess(actual));
            byte[] wire=GiftWarCashCodec.encode(GiftWarCashPolicy.assess(actual));
            assertArrayEquals(GiftWarCashCodec.encode(expected),wire);assertEquals(vector.get("expected"),FullJsonTree.parse(wire,LIMIT));
            assertThrows(IllegalArgumentException.class,()->GiftWarCashCodec.decode(before));
            assertArrayEquals(before,DriverJson.encode(large));max=Math.max(max,DriverJson.encode(projected).length);count++;
        }
        assertEquals(32,count);assertTrue(max<65536);System.out.println("P110-gift32-max-role-bytes="+max);
    }

    @Test void allConstructionCashDecisionsRetainContextAndReachTheRealPositiveFocusBranch() {
        int count=0,max=0,explicitFocus=0;
        for(JsonNode vector:cashCases) {
            Obj original=json(FullJsonTree.encode(vector.get("request"),LIMIT));Obj large=large(original);
            byte[] before=DriverJson.encode(large);Obj projected=OrdinaryFinanceCollector.projectCashContext(large);
            var reference=WartimeConstructionCodec.decode(DriverJson.encode(original));var actual=WartimeConstructionCodec.decode(DriverJson.encode(projected));
            assertEquals(reference.kindWire(),actual.kindWire());assertEquals(reference.cost(),actual.cost());assertEquals(reference.context(),actual.context());
            assertEquals(reference.quotes(),actual.quotes());assertEquals(reference.marketShape(),actual.marketShape());assertEquals(reference.procurement(),actual.procurement());
            var expected=WartimeConstructionCash.observe(reference);var observed=WartimeConstructionCash.observe(actual);
            assertEquals(expected,observed);assertArrayEquals(WartimeConstructionCodec.encode(expected),WartimeConstructionCodec.encode(observed));
            assertEquals(vector.get("expected"),FullJsonTree.parse(WartimeConstructionCodec.encode(observed),LIMIT));
            if(List.of("exact_ample_threshold","cheapest_adequate_quote","current_assessed_suitable_quote").contains(vector.path("name").textValue())) {
                assertEquals(WarCashFocusProjection.observe(reference.focusRequest().decodeRequired()),WarCashFocusProjection.observe(actual.focusRequest().decodeRequired()));explicitFocus++;
            }
            assertThrows(IllegalArgumentException.class,()->WartimeConstructionCodec.decode(before));
            assertArrayEquals(before,DriverJson.encode(large));max=Math.max(max,DriverJson.encode(projected).length);count++;
        }
        assertEquals(31,count);assertEquals(3,explicitFocus);assertTrue(max<65536);System.out.println("P110-construction31-max-role-bytes="+max);
    }

    @Test void allFocusOutcomesAndOpaquePoliticalProfilesRemainExactWithoutClaimingRawEchoIdentity()throws Exception {
        int count=0,max=0,profiles=0;
        for(JsonNode vector:focusCases) {
            byte[] original=vector.path("request_json").textValue().getBytes(java.nio.charset.StandardCharsets.UTF_8);
            Obj request=json(original),snapshot=object(request.get("snapshot"),"snapshot");
            Obj outer=obj("snapshot",snapshot.with("native_command_history",history),"root",request.get("campaign_root"));
            Obj view=OrdinaryFinanceCollector.projectCashContext(outer);
            Obj projected=request.with("snapshot",view.get("snapshot")).with("campaign_root",view.get("root"));
            byte[] role=DriverJson.encode(projected);
            var reference=WarCashFocusProjectionCodec.decode(original);var actual=WarCashFocusProjectionCodec.decode(role);
            var expected=WarCashFocusProjection.observe(reference);assertEquals(expected,WarCashFocusProjection.observe(actual));
            byte[] wire=WarCashFocusProjectionCodec.encode(WarCashFocusProjection.observe(actual));
            assertArrayEquals(WarCashFocusProjectionCodec.encode(expected),wire);assertEquals(vector.get("expected_result"),FullJsonTree.parse(wire,LIMIT));
            // This API echoes the supplied role exactly, not the omitted full historical snapshot.
            assertArrayEquals(role,WarCashFocusProjectionCodec.encodeRequest(actual));
            var oldContext=political(reference);
            var newContext=political(actual);
            assertEquals(oldContext.activeWarCount(),newContext.activeWarCount());
            for(int ordinal=0;ordinal<oldContext.activeWarCount();ordinal++) {
                var a=BudgetPoliticalStakesCodec.observe(oldContext,ordinal);var b=BudgetPoliticalStakesCodec.observe(newContext,ordinal);
                assertEquals(a.status(),b.status());assertEquals(a.reason(),b.reason());assertEquals(BudgetPoliticalStakesCodec.qualified(a),BudgetPoliticalStakesCodec.qualified(b));
                assertArrayEquals(a.toJsonBytes(),b.toJsonBytes());profiles++;
            }
            Obj full=request.with("snapshot",snapshot.with("native_command_history",history));
            assertThrows(IllegalArgumentException.class,()->WarCashFocusProjectionCodec.decode(DriverJson.encode(full)));
            max=Math.max(max,role.length);count++;
        }
        assertEquals(18,count);assertTrue(profiles>0);assertTrue(max<65536);System.out.println("P110-focus18-max-role-bytes="+max+" political-profiles="+profiles);
    }

    @Test void publicProducerPreservesHeldObjectsAndTheIncomeSubtreeConsumedByIntent()throws Exception {
        PlanningRequest request=(PlanningRequest)callFixture("request",new Class<?>[]{});
        JsonNode loan=(JsonNode)fixtureField("loanOriginal");Class<?> readsType=Class.forName(FinancingSnapshotRole107Test.class.getName()+"$OriginalReads");
        Constructor<?> constructor=readsType.getDeclaredConstructor(Obj.class);constructor.setAccessible(true);Object reads=constructor.newInstance(json(FullJsonTree.encode(loan.get("cash_resources"),LIMIT)));
        var collector=(OrdinaryFinanceCollector)callFixture("collector",new Class<?>[]{readsType,PlanningRequest.class},reads,request);
        var held=(OrdinaryFinanceCollector.Current)callFixture("current",new Class<?>[]{OrdinaryFinanceCollector.class,PlanningRequest.class},collector,request);
        Obj mercenary=object(json(FullJsonTree.encode(giftCases.get(0).get("request"),LIMIT)).get("mercenary_ledger"),"actual software domain");
        byte[] body=DriverJson.encode(mercenary);var ref=new ExactRef("p110-original-software-mercenary-body",body.length,ActionCodec.sha256(body));
        var document=new FinanceStatePort.Document(FinanceStatePort.Domain.MERCENARY,ref,body);
        var state=new FinanceStatePort(input->new FinanceStatePort.Head(input.before(),ref,List.of(document),List.of(),Optional.empty()),
                List.of(new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.MERCENARY,ref,original->FinanceStatePort.Pending.CLEAR)));
        var snapshot=assertInstanceOf(FinanceStatePort.Known.class,state.read(request)).snapshot();
        var current=new OrdinaryFinanceCollector.Current(held.root(),held.spending(),held.spendingJson(),held.market(),held.priority(),snapshot,held.originalReads());
        Obj candidate=object(json(FullJsonTree.encode(giftCases.get(0).get("request"),LIMIT)).get("candidate"),"candidate");
        Obj small=OrdinaryFinanceCollector.cashContext(request,current,GiftWarCashCodec.SCHEMA,candidate);
        var large=(PlanningRequest)callFixture("withSnapshot",new Class<?>[]{PlanningRequest.class,Obj.class},request,request.observations().snapshot().with("native_command_history",history));
        byte[] before=DriverJson.encode(large.observations().snapshot()),rootBefore=DriverJson.encode(current.root()),marketBefore=DriverJson.encode(current.market().original());
        Obj actual=OrdinaryFinanceCollector.cashContext(large,current,GiftWarCashCodec.SCHEMA,candidate);
        assertEquals(GiftWarCashCodec.decode(DriverJson.encode(small)),GiftWarCashCodec.decode(DriverJson.encode(actual)));
        assertSame(candidate,actual.get("candidate"));assertSame(current.spendingJson(),actual.get("spending"));assertSame(current.market().original(),actual.get("market"));
        assertEquals(mercenary,actual.get("mercenary_ledger"));assertArrayEquals(body,snapshot.ledger(FinanceStatePort.Domain.MERCENARY).orElseThrow().document().bytes());
        assertArrayEquals(before,DriverJson.encode(large.observations().snapshot()));assertArrayEquals(rootBefore,DriverJson.encode(current.root()));assertArrayEquals(marketBefore,DriverJson.encode(current.market().original()));
        Obj last=object(history.items().get(138),"last original row");Obj incomeRoot=object(object(last.get("result"),"result").get("campaign_root_context"),"source income root");
        byte[] originalRoot=DriverJson.encode(incomeRoot);Obj incomeView=object(OrdinaryFinanceCollector.projectCashContext(obj("root",incomeRoot)).get("root"),"income role");
        assertArrayEquals(DriverJson.encode(incomeRoot.get("player_monthly_gold_income")),DriverJson.encode(incomeView.get("player_monthly_gold_income")));
        Obj income=object(incomeView.get("player_monthly_gold_income"),"complete lifecycle income material");
        assertEquals(n(584686),income.get("raw"));assertEquals(n(100000),income.get("scale"));
        for(String key:List.of("player_character_id","snapshot_revision","date_raw"))assertEquals(incomeRoot.get(key),incomeView.get(key));
        assertArrayEquals(originalRoot,DriverJson.encode(incomeRoot));
        // These are the exact inputs consumed by ConstructionDomainLifecycle.intent's income rule, not an issued intent.
    }

    @Test void sharedSdkEntryClosesBoundedOverflowAndPreservesMalformedOrUnknownInputs() {
        Obj original=json(FullJsonTree.encode(giftCases.get(0).get("request"),LIMIT));Obj snapshot=object(original.get("snapshot"),"snapshot");
        Obj padded=snapshot.with("unconsumed_extension",new Text("x".repeat(64000)));
        assertTrue(DriverJson.encode(padded).length<65536);
        Obj full=original.with("snapshot",padded);assertTrue(DriverJson.encode(full).length>65536);
        byte[] before=DriverJson.encode(full);assertThrows(IllegalArgumentException.class,()->GiftWarCashCodec.decode(before));
        var role=OrdinaryFinanceCollector.projectCashContext(full);
        assertTrue(GiftWarCashPolicy.assess(GiftWarCashCodec.decode(DriverJson.encode(role))).newGiftSpendingAllowed());
        assertEquals(GiftWarCashPolicy.assess(GiftWarCashCodec.decode(DriverJson.encode(original))),GiftWarCashPolicy.assess(GiftWarCashCodec.decode(DriverJson.encode(role))));
        assertArrayEquals(before,DriverJson.encode(full));
        for(Value malformed:List.of(Nil.INSTANCE,new Bool(false),new Text("unknown"),new Arr(List.of()))) {
            Obj value=obj("snapshot",malformed,"root",malformed,"unknown_outer",new Text("must remain"));
            assertSame(value.get("snapshot"),OrdinaryFinanceCollector.projectCashContext(value).get("snapshot"));
            assertSame(value.get("root"),OrdinaryFinanceCollector.projectCashContext(value).get("root"));
            assertSame(value.get("unknown_outer"),OrdinaryFinanceCollector.projectCashContext(value).get("unknown_outer"));
        }
        assertFalse(OrdinaryFinanceCollector.projectCashContext(obj()).members().containsKey("snapshot"));
    }

    private static Obj large(Obj original){return original.with("snapshot",object(original.get("snapshot"),"snapshot").with("native_command_history",history));}
    private static BudgetPoliticalStakesCodec.Context political(WarCashFocusProjectionCodec.Request request)throws Exception {Method method=request.getClass().getDeclaredMethod("politicalContext");method.setAccessible(true);return (BudgetPoliticalStakesCodec.Context)method.invoke(request);}
    private static Object fixtureField(String name)throws Exception {Field field=FinancingSnapshotRole107Test.class.getDeclaredField(name);field.setAccessible(true);return field.get(null);}
    private static Object callFixture(String name,Class<?>[] signature,Object...args)throws Exception {Method method=FinancingSnapshotRole107Test.class.getDeclaredMethod(name,signature);method.setAccessible(true);try{return method.invoke(null,args);}catch(InvocationTargetException error){if(error.getCause() instanceof Exception cause)throw cause;if(error.getCause() instanceof Error cause)throw cause;throw error;}}
    private static byte[] resource(String path)throws Exception {return (byte[])callFixture("resource",new Class<?>[]{String.class},path);}
    private static Obj json(byte[] bytes){return DriverJson.object(bytes,LIMIT);}
    private static IntegerValue n(long value){return new IntegerValue(BigInteger.valueOf(value));}
}
