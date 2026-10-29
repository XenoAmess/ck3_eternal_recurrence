package org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.Nonce;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.Family;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract.*;

/** Source grammar/typed constructor regression. Actual Native report parity is the shared
 * original-Python/corpus + sole-coordinator consumer's job; this test fabricates no receipt. */
final class ChinaCasesExecutionCodecTest {
    private static final BigInteger GENERATION=new BigInteger("18446744073709551615");
    private static String hex(String nonce){return HexFormat.of().formatHex(nonce.getBytes(StandardCharsets.US_ASCII));}
    private static OperationKey step(Method method,String tail){return new OperationKey(method.family().step()+"-"+tail);}
    @Test void allTenOriginalEncodedGrammarsReachTheSameTypedSelectorAndNativeArguments() {
        String h=hex("source-0");
        Map<Method,String> tails=Map.of(Method.B1,h,Method.CASE,"b1-12-0-"+h,
            Method.AI_OWNED,"11-12-"+h,Method.RESULT,"11-"+h,Method.PIP,"11-"+h,
            Method.PROMOTION,"11-"+h,Method.AF5,"11-"+h,Method.PROJECTS,"11-12-"+h,
            Method.INCIDENT,"11-z-"+h,Method.SCOREBOARD,"source-0");
        for(var row:tails.entrySet()){
            OperationKey original=step(row.getKey(),row.getValue());
            assertEquals(Optional.of(row.getKey()),ChinaCasesCodec.executionMethod(original));
            var args=ChinaCasesCodec.executionArguments(original,GENERATION);
            assertEquals(new OpportunityJson.Text("source-0"),args.get("request_nonce"));
            assertEquals(args,OpportunityJson.parse(OpportunityJson.encode(args)));
            if(row.getKey()==Method.SCOREBOARD)
                assertEquals(new OpportunityJson.IntegerValue(GENERATION),args.get("expected_connection_generation"));
            else assertFalse(args.members().containsKey("expected_connection_generation"));
        }
        var caseArgs=ChinaCasesCodec.executionArguments(step(Method.CASE,"b1-12-0-"+h),GENERATION);
        assertEquals(new OpportunityJson.IntegerValue(BigInteger.ZERO),caseArgs.get("owner_character_id"));
        assertEquals(new OpportunityJson.IntegerValue(BigInteger.valueOf(12)),caseArgs.get("subject_character_id"));
        assertEquals(new OpportunityJson.Text("zhongguo.b1.performance"),caseArgs.get("case_kind"));
    }
    @Test void noncanonicalNonceIdsProfileAndOwnerSubjectAliasesNeverSelectARead() {
        String h=hex("n");
        List<OperationKey> bad=List.of(
            step(Method.B1,"6"),step(Method.B1,"6E"),step(Method.B1,"ff"),step(Method.B1,"00"),
            step(Method.CASE,"b2-12-0-"+h),step(Method.CASE,"b1-0-0-"+h),
            step(Method.CASE,"b1-12-00-"+h),step(Method.CASE,"b1-2147483648-0-"+h),
            step(Method.AI_OWNED,"11-11-"+h),step(Method.AI_OWNED,"0-12-"+h),
            step(Method.PIP,"00-"+h),step(Method.PIP,"2147483648-"+h),
            step(Method.PROMOTION,"01-"+h),step(Method.PROJECTS,"11-11-"+h),
            step(Method.INCIDENT,"11-X-"+h),step(Method.INCIDENT,"11-z-"+h+"-extra"),
            new OperationKey(Method.B1.family().step()),new OperationKey("query-unregistered-source-n"));
        for(OperationKey encoded:bad){
            assertTrue(ChinaCasesCodec.executionMethod(encoded).isEmpty(),encoded.value());
            assertThrows(IllegalArgumentException.class,()->ChinaCasesCodec.executionArguments(encoded,GENERATION),encoded.value());
        }
        assertThrows(IllegalArgumentException.class,()->ChinaCasesCodec.executionArguments(step(Method.B1,h),BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class,()->ChinaCasesCodec.executionArguments(step(Method.B1,h),GENERATION.add(BigInteger.ONE)));
    }
    @Test void originalWidePositivePromotionAf5AndProjectsIdsAreNeverNarrowedToInt32OrDouble() {
        String first="9".repeat(4300),second="8".repeat(4300),h=hex("n");
        for(Method method:List.of(Method.PROMOTION,Method.AF5,Method.PROJECTS)){
            String tail=method==Method.PROJECTS?first+"-"+second+"-"+h:first+"-"+h;
            OperationKey encoded=step(method,tail);
            assertEquals(Optional.of(method),ChinaCasesCodec.executionMethod(encoded));
            var args=ChinaCasesCodec.executionArguments(encoded,GENERATION);
            assertEquals(new BigInteger(first),OpportunityJson.integer(args.get("owner_character_id"),"owner"));
            if(method==Method.PROJECTS)assertEquals(new BigInteger(second),
                OpportunityJson.integer(args.get("subject_character_id"),"subject"));
            assertEquals(args,OpportunityJson.parse(OpportunityJson.encode(args)));
        }
        assertTrue(ChinaCasesCodec.executionMethod(step(Method.PROMOTION,"9".repeat(4301)+"-"+h)).isEmpty());
    }
    @Test void scoreboardKeepsRawNonceAndActualGenerationRatherThanHexOrDefaultGeneration() {
        var original=step(Method.SCOREBOARD,"N.0:_-source");
        var args=ChinaCasesCodec.executionArguments(original,GENERATION);
        assertEquals(new OpportunityJson.Text("N.0:_-source"),args.get("request_nonce"));
        assertEquals(new OpportunityJson.IntegerValue(GENERATION),args.get("expected_connection_generation"));
        assertEquals(Optional.of(Method.SCOREBOARD),ChinaCasesCodec.executionMethod(step(Method.SCOREBOARD,hex("n"))),
            "raw ASCII hex-looking nonce is still the original raw nonce, not decoded to n");
        assertEquals(new OpportunityJson.Text(hex("n")),
            ChinaCasesCodec.executionArguments(step(Method.SCOREBOARD,hex("n")),GENERATION).get("request_nonce"));
    }
    @Test void exactDecoratedInstancesAreUsedForBothCatalogAndActualFacadeReads() {
        var observed=new AtomicReference<ReadContract<?>>();
        PlanningReadPort port=new PlanningReadPort(){
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){
                observed.set(contract);return new PlanningReadResult.Unavailable<>("software unavailable; no Native packet",Optional.empty());
            }
        };
        var factory=new ChinaCasesFacade.HistoryProjectionFactory(){
            @Override public DriverReadHistoryRichMaterial.Kind kind(){return DriverReadHistoryRichMaterial.Kind.PUBLIC_EXECUTE_QUERY;}
            @Override public <T> Optional<ReadContract.OriginalHistoryProjection<T>> forFamily(Family family){
                if(family==Family.PROGRESS)return Optional.empty();
                return Optional.of((receipt,replayed)->{throw new AssertionError("no positive receipt manufactured");});
            }
        };
        var facade=new ChinaCasesFacade(port,noMutation(),factory);
        List<ReadContract<?>> installed=facade.readContracts();
        assertEquals(11,installed.size());
        for(int index=0;index<10;index++)assertEquals(Optional.of(DriverReadHistoryRichMaterial.Kind.PUBLIC_EXECUTE_QUERY),installed.get(index).originalHistoryKind());
        assertTrue(installed.get(10).originalHistoryKind().isEmpty(),"PROGRESS is outside Cases10 registry");
        var context=context();
        assertInstanceOf(PlanningReadResult.Unavailable.class,facade.query_zhongguo_b1_cycle_snapshot_v1(context,new Nonce("n")));
        assertSame(installed.get(0),observed.get());
        assertInstanceOf(PlanningReadResult.Unavailable.class,facade.query_zhongguo_scoreboard_state_v1(context,new Nonce("n")));
        assertSame(installed.get(9),observed.get());
    }
    @Test void formalFactoryCannotSilentlyOmitAnyCasesProjectorOrDecorateProgress() {
        PlanningReadPort unused=new PlanningReadPort(){
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> c,PlanningReadRequest r){throw new AssertionError();}
        };
        for(boolean all:List.of(false,true)){
            var invalid=new ChinaCasesFacade.HistoryProjectionFactory(){
                @Override public DriverReadHistoryRichMaterial.Kind kind(){return DriverReadHistoryRichMaterial.Kind.PUBLIC_EXECUTE_QUERY;}
                @Override public <T> Optional<ReadContract.OriginalHistoryProjection<T>> forFamily(Family f){
                    return all?Optional.of((receipt,value)->{throw new AssertionError();}):Optional.empty();
                }
            };
            assertThrows(IllegalArgumentException.class,()->new ChinaCasesFacade(unused,
                noMutation(),invalid));
        }
    }
    private static ActionCoordinatorPort noMutation(){
        return new ActionCoordinatorPort(){
            @Override public ActionReceipt execute(ActionCommand command){throw new AssertionError("no mutation");}
            @Override public ActionReceipt reconcile(String actionId){throw new AssertionError("no mutation");}
        };
    }
    private static ChinaCasesFacade.Context context(){
        var game=new GameGeneration(123,new PythonOnlyUInt64(BigInteger.valueOf(100)));
        var before=new ObservationIdentity("software-cases-execution",game,new JointBudgetSelector.ProposalFrame(
            new JointBudgetSelector.Frame(BigInteger.valueOf(12),BigInteger.ONE,BigInteger.valueOf(53217264)),
            "native:1",BigInteger.ONE,"software-episode"),1);
        var source=new G2Source(before.machineId(),"2026-10-24T00:00:00Z","software-only",
            new ExactRef("software-source",1,"a".repeat(64)));
        return new ChinaCasesFacade.Context(before,source,"software-session",GENERATION,Instant.parse("2026-10-24T01:00:00Z"));
    }
}
