package org.xar.ck3.control.nativebridge.capabilities.army;

import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Actual catalog caching and pure preparation with physical originals; no native submit or Game claim. */
final class ArmyReadDeadlineIdentityTest {
    @TempDir Path temporary;
    @Test void allFiveReadFamiliesReuseTheirExactContractAcrossTransportBudgetsAndStillRejectChangedSource()throws Exception{
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("actual"),false)){
            fixture.ready();var actual=RootGuardEvidence.loadFrame(fixture.lastNestedRead.get().before().binding(),fixture.archive,fixture.frameLoader());
            var first=new Context(actual.identity(),actual.source(),actual.sessionId(),Instant.now().plusSeconds(10));
            var next=new Context(first.before(),first.source(),first.sessionId(),first.deadline().plusSeconds(5));
            var source=actual.source().sourceRef();var closed=new ArmyClosedReadContracts(source,source);var battle=new ArmyBattleReads(source,source,fixture.reads);
            var route=new ArmyRouteReads(source,source,fixture.reads);var windows=new ArmyWindowReads(source,source,fixture.reads,fixture.archive);var reinforcement=new ArmyReinforcementReads(source,source,fixture.reads);
            List<RootReadContractCatalog.Family<?,?>> families=new ArrayList<>();families.addAll(closed.families());families.addAll(battle.families());families.add(route.family());families.addAll(windows.families());families.addAll(reinforcement.families());
            var catalog=new RootReadContractCatalog(List.of(),families);var revision=new ArmyCalls.Revision(new Present<>(first.before().frame().revision()));
            var closedInput=new ArmyCalls.Frame(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1,revision);
            var c1=new ArmyClosedReadContracts.Selection(closedInput,first);var c2=new ArmyClosedReadContracts.Selection(closedInput,next);
            var battleInput=new ArmyCalls.Unit(PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1,revision,new PublicUnitId(0));
            var b1=new ArmyBattleReads.Selection(battleInput,first,ArmyBattleReads.Capture.PUBLIC_QUERY);var b2=new ArmyBattleReads.Selection(battleInput,next,ArmyBattleReads.Capture.PUBLIC_QUERY);
            var r1=new ArmyRouteReads.Selection(first,new PublicUnitId(0),new PositiveId(1),new PositiveId(2));var r2=new ArmyRouteReads.Selection(next,r1.army(),r1.origin(),r1.target());
            var windowInput=new ArmyCalls.Frame(PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1,revision);
            var w1=new ArmyWindowReads.Selection(windowInput,first,actual.connectionGeneration(),ArmyWindowReads.driverGeneration(actual));var w2=new ArmyWindowReads.Selection(windowInput,next,actual.connectionGeneration(),ArmyWindowReads.driverGeneration(actual));
            var reinforcementInput=new ArmyCalls.Unit(PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1,revision,new PublicUnitId(0));
            var f1=new ArmyReinforcementReads.Selection(reinforcementInput,first);var f2=new ArmyReinforcementReads.Selection(reinforcementInput,next);
            assertEquals(ArmyReadKey.key(battleInput,first),ArmyReadKey.key(battleInput,next));
            fixture.writer.locked(same->{
                check(closed.issue(catalog,c1),closed.issue(catalog,c2),closed.request(c2));
                check(battle.issue(catalog,b1),battle.issue(catalog,b2),battle.request(b2));
                var routeFirst=catalog.issue(route.family(),r1);var routeNext=catalog.issue(route.family(),r2);
                var routeArgs=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(org.xar.ck3.control.planning.opportunity.OpportunityJson.parse("{\"army_id\":0,\"origin_province_id\":1,\"target_province_id\":2}".getBytes(java.nio.charset.StandardCharsets.UTF_8)),"route arguments");
                check(routeFirst,routeNext,new PlanningReadRequest(next.before(),next.source(),next.sessionId(),routeNext.operation(),routeArgs,next.deadline()));
                check(windows.issue(catalog,w1),windows.issue(catalog,w2),windows.request(w2));
                check(reinforcement.issue(catalog,f1),reinforcement.issue(catalog,f2),reinforcement.request(f2));return null;
            });
            var invocation=closed.request(c2);var rebound=ArmyNativeReadEvidence.contextForRequest(first,invocation);
            assertEquals(next.deadline(),rebound.deadline());assertEquals(first.before(),rebound.before());assertEquals(first.source(),rebound.source());
            var wrong=new PlanningReadRequest(invocation.before(),invocation.source(),invocation.sessionId()+"-changed",invocation.operation(),invocation.arguments(),invocation.deadline());
            assertThrows(IllegalArgumentException.class,()->ArmyNativeReadEvidence.contextForRequest(first,wrong));
            assertThrows(IllegalArgumentException.class,()->closed.issue(catalog,c1).prepare(wrong,"pure-negative-source-test"));
            assertTrue(routeFirstHasReplay(catalog,route,r1));
        }
    }
    private static <T> void check(ReadContract<T> first,ReadContract<T> next,PlanningReadRequest request){assertSame(first,next);assertTrue(first.hasPureReplay());assertEquals(request.operation().value(),first.prepare(request,"pure-software-budget-test").step());}
    private static boolean routeFirstHasReplay(RootReadContractCatalog catalog,ArmyRouteReads route,ArmyRouteReads.Selection selection){return catalog.issue(route.family(),selection).hasPureReplay();}
    @Test void canonicalPredicateReusesTheGenuineOldContractAndReceiptWithoutRelabellingItsDeadline()throws Exception{
        var installed=new AtomicReference<ReadContract<RawJson>>();var operation=new OperationKey("query-fixture-army-canonical-budget");String capability="game.command."+operation.value();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"fixture-army-canonical-budget",source->{
            var contract=new ReadContract<RawJson>("army-budget-original-software-contract",operation,Optional.of(capability),capability,
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->new NativeRequest(operation.value(),Optional.of(capability),new RawJson(new byte[]{'{','}'})),
                    receipt->receipt.original().originalResultToken().orElseThrow(),receipt->receipt.original().originalResultToken().orElseThrow(),
                    (original,value,current,semantic)->ArmyNativeReadEvidence.requireCanonicalEquivalent(original,current));
            installed.set(contract);return List.of(contract);
        },request->new RawJson("{\"actual_status\":\"retained\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("canonical"),false,scenario)){
            fixture.ready();var actual=RootGuardEvidence.loadFrame(fixture.lastNestedRead.get().before().binding(),fixture.archive,fixture.frameLoader());
            var original=new PlanningReadRequest(actual.identity(),actual.source(),actual.sessionId(),operation,new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()),Instant.now().plusSeconds(20));
            fixture.writer.locked(same->{
                var result=fixture.reads.read(same,installed.get(),original);if(!(result instanceof PlanningReadResult.Known<RawJson> known))throw new AssertionError(result);
                var current=new PlanningReadRequest(original.before(),original.source(),original.sessionId(),operation,original.arguments(),original.deadline().plusSeconds(5));
                installed.get().requireCanonicalReuse(known.receipt(),installed.get().replay(known.receipt()),current,actual.semantic());
                assertEquals(original,known.receipt().request());assertNotEquals(current.deadline(),known.receipt().request().deadline());
                assertEquals(known.receipt(),fixture.archive.loadRead(known.originalReceipt()));
                var differentArgs=new PlanningReadRequest(current.before(),current.source(),current.sessionId(),operation,new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of("changed",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true))),current.deadline());
                assertThrows(IllegalArgumentException.class,()->installed.get().requireCanonicalReuse(known.receipt(),known.value(),differentArgs,actual.semantic()));
                var differentSession=new PlanningReadRequest(current.before(),current.source(),current.sessionId()+"-other",operation,current.arguments(),current.deadline());
                assertThrows(IllegalArgumentException.class,()->installed.get().requireCanonicalReuse(known.receipt(),known.value(),differentSession,actual.semantic()));return null;
            });
        }
    }
}
