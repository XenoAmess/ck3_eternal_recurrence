package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

final class RootReadContractCatalogEscrowTest {
    private record Selection(String id,Instant deadline) { }
    @Test void sameInstalledTypedFamilyResolvesTheUnchangedOriginalDecoderAndNeverRedatesItsReceipt() {
        var f=DriverCapabilityStateProducerTest.fresh();var replays=new AtomicInteger();
        ExactRef source=f.archive().preserveMaterial(new RawJson(new byte[]{'{','}'}));
        var family=family("actual-typed-family",source,source,replays,true);
        var catalog=new RootReadContractCatalog(List.of(),List.of(family));
        Instant oldDeadline=Instant.parse("2030-01-01T00:00:00Z");
        var original=catalog.issue(family,new Selection("original-cache-contract",oldDeadline));
        var current=catalog.issue(family,new Selection("later-contract",oldDeadline.plusSeconds(1)));
        assertSame(original,catalog.issue(family,new Selection("original-cache-contract",oldDeadline)));
        var receipt=DriverCapabilityStateProducerTest.receipt(f,"query-arrange-marriage-choices",
                new OpportunityJson.Obj(Map.of("step",new OpportunityJson.Text("query-arrange-marriage-choices"))));
        ReadContract<OpportunityJson.Obj> retained=catalog.originalContract(current,receipt.contractId()).orElseThrow();
        assertSame(original,retained);assertNotSame(current,retained);
        assertThrows(IllegalArgumentException.class,()->current.replay(receipt));
        var value=retained.replay(receipt);assertEquals(1,replays.get());
        var request=new PlanningReadRequest(receipt.request().origin(),receipt.request().source(),receipt.request().sessionId(),
                receipt.request().operation(),receipt.request().arguments(),oldDeadline.plusSeconds(1));
        retained.requireCanonicalReuse(receipt,value,request,new OpportunityJson.Obj(Map.of()));
        assertEquals(oldDeadline,receipt.request().deadline());assertEquals("original-cache-contract",receipt.contractId());
        assertTrue(catalog.originalContract(current,"missing-original").isEmpty());
    }
    @Test void AnotherFamilyOrUninstalledObjectCannotBorrowTheOriginalTypedEscrow() {
        var f=DriverCapabilityStateProducerTest.fresh();ExactRef source=f.archive().preserveMaterial(new RawJson(new byte[]{'{','}'}));
        var left=family("left",source,source,new AtomicInteger(),true);var right=family("right",source,source,new AtomicInteger(),true);
        var catalog=new RootReadContractCatalog(List.of(),List.of(left,right));Instant deadline=Instant.parse("2030-01-01T00:00:00Z");
        var original=catalog.issue(left,new Selection("left-original",deadline));var unrelated=catalog.issue(right,new Selection("right-current",deadline));
        assertTrue(catalog.originalContract(unrelated,original.contractId()).isEmpty());
        var outside=new RootReadContractCatalog(List.of(),List.of(family("outside",source,source,new AtomicInteger(),true)));
        assertThrows(IllegalArgumentException.class,()->outside.originalContract(original,original.contractId()));
    }
    @Test void AContractWithoutItsOwnPredicateCannotDiscardAChangedDeadline() {
        var f=DriverCapabilityStateProducerTest.fresh();ExactRef source=f.archive().preserveMaterial(new RawJson(new byte[]{'{','}'}));
        var family=family("strict",source,source,new AtomicInteger(),false);var catalog=new RootReadContractCatalog(List.of(),List.of(family));
        Instant deadline=Instant.parse("2030-01-01T00:00:00Z");var original=catalog.issue(family,new Selection("original-cache-contract",deadline));
        var receipt=DriverCapabilityStateProducerTest.receipt(f,"query-arrange-marriage-choices",new OpportunityJson.Obj(Map.of("step",new OpportunityJson.Text("query-arrange-marriage-choices"))));
        var value=original.replay(receipt);original.requireCanonicalReuse(receipt,value,receipt.request(),new OpportunityJson.Obj(Map.of()));
        var changed=new PlanningReadRequest(receipt.request().origin(),receipt.request().source(),receipt.request().sessionId(),receipt.request().operation(),receipt.request().arguments(),deadline.plusSeconds(1));
        assertThrows(IllegalArgumentException.class,()->original.requireCanonicalReuse(receipt,value,changed,new OpportunityJson.Obj(Map.of())));
    }
    private static RootReadContractCatalog.Family<Selection,OpportunityJson.Obj> family(String id,ExactRef definition,ExactRef decoder,AtomicInteger replays,boolean reuse) {
        return new RootReadContractCatalog.Family<>(id,Selection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of("game.command.query-arrange-marriage-choices"),definition,decoder,
                selection->new RawJson(DriverJson.encode(new OpportunityJson.Obj(Map.of("id",new OpportunityJson.Text(selection.id()),"deadline",new OpportunityJson.Text(selection.deadline().toString()))))),
                selection->new OperationKey("query-arrange-marriage-choices"),selection->{
                    java.util.function.Function<PlanningReadReceipt,OpportunityJson.Obj> pure=receipt->{
                        org.xar.ck3.control.contracts.StrictJson.require(receipt.request().deadline().equals(selection.deadline()),"original decoder retains its exact actual deadline");
                        replays.incrementAndGet();return DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),65536);
                    };
                    ReadContract.CanonicalReuse<OpportunityJson.Obj> predicate=(receipt,value,current,semantic)->{
                        org.xar.ck3.control.contracts.StrictJson.require(current.before().equals(receipt.request().before())&&current.source().equals(receipt.request().source())
                                &&current.sessionId().equals(receipt.request().sessionId())&&current.arguments().equals(receipt.request().arguments())
                                &&value.get("step").equals(new OpportunityJson.Text(current.operation().value())),"test source-owner native operands changed");
                    };
                    if(reuse)return new ReadContract<>(selection.id(),new OperationKey("query-arrange-marriage-choices"),Optional.of("game.command.query-arrange-marriage-choices"),
                            "game.command.query-arrange-marriage-choices",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                            definition,(request,requestId)->new NativeRequest(request.operation().value(),Optional.of("game.command.query-arrange-marriage-choices"),new RawJson(new byte[]{'{','}'})),pure,pure,predicate);
                    return new ReadContract<>(selection.id(),new OperationKey("query-arrange-marriage-choices"),Optional.of("game.command.query-arrange-marriage-choices"),
                            "game.command.query-arrange-marriage-choices",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                            definition,(request,requestId)->new NativeRequest(request.operation().value(),Optional.of("game.command.query-arrange-marriage-choices"),new RawJson(new byte[]{'{','}'})),pure,pure);
                });
    }
}
