package org.xar.ck3.control.service.root;
import org.xar.ck3.control.application.planning.finance.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;

/** Application boundaries, not a substitute for the original producer or a writer-lock integration qualification. */
final class FeastCommitmentBudgetTest {
    private static final ExactRef SOURCE_REF=new ExactRef("D:/fixture/finance.java",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("xenoamess-full-tower-eb9d2c1186","2026-10-23T17:00:00Z","1.20.0.4",SOURCE_REF);
    private static PlanningRequest request() {
        var identity=new ProposalLifecycle.ObservationIdentity(SOURCE.machineId(),
                new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.ONE,BigInteger.valueOf(100)),
                        "native:1",BigInteger.ONE,"episode-finance-fixture"),1);
        Obj snapshot=object(parse(("{\"paused\":true,\"map_ready\":true,\"snapshot_id\":\"native:1\",\"revision\":1,\"native_revision\":1,"
                +"\"date_raw\":100,\"episode_run_id\":\"episode-finance-fixture\",\"played_character\":{\"character_id\":1,\"alive\":true},"
                +"\"active_wars\":[],\"player_armies\":[],\"active_event\":null,\"pending_character_interaction\":null}").getBytes(StandardCharsets.UTF_8)),"fixture");
        var observed=new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        return new PlanningRequest(identity,SOURCE,"session-finance-fixture",Instant.parse("2026-10-23T18:00:00Z"),observed);
    }
    private static FinanceStatePort.Document document(FinanceStatePort.Domain domain,String json) {
        byte[] raw=json.getBytes(StandardCharsets.UTF_8);
        return new FinanceStatePort.Document(domain,new ExactRef("D:/fixture/"+domain+".json",raw.length,ActionCodec.sha256(raw)),raw);
    }
    private static FinanceStatePort state(PlanningRequest request,List<FinanceStatePort.Document> documents,List<FinanceStatePort.ReaderBinding> readers) {
        return new FinanceStatePort(ignored->new FinanceStatePort.Head(request.before(),SOURCE_REF,documents,List.of(),Optional.empty()),readers);
    }
    private static FinanceStatePort.Snapshot known(FinanceStatePort port,PlanningRequest request) {
        return assertInstanceOf(FinanceStatePort.Known.class,port.read(request)).snapshot();
    }

    private final FeastDomainRuntime runtime = new FeastDomainRuntime(java.nio.file.Path.of("synthetic-writer.lock"),
            new FeastDomainRuntime.Sources(SOURCE_REF,List.of(SOURCE_REF)));
    private byte[] encoded(boolean pending) {
        var claim = new FeastDomainRuntime.Pending(request().before().frame().episodeRunId(),SOURCE_REF,"c".repeat(64));
        return FeastDomainRuntime.encode(new FeastDomainRuntime.Ledger(pending?Optional.of(claim):Optional.empty(),Optional.empty()));
    }
    private FinanceStatePort fixture(Optional<byte[]> feast,boolean installOwner) {
        var request=request();
        var domains=List.of(FinanceStatePort.Domain.CONSTRUCTION,FinanceStatePort.Domain.FACTION_GIFT,
                FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE,FinanceStatePort.Domain.CHILD_MARRIAGE,FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE);
        var docs=new java.util.ArrayList<FinanceStatePort.Document>();
        var readers=new java.util.ArrayList<FinanceStatePort.ReaderBinding>();
        for(var domain:domains) {
            docs.add(document(domain,"{\"pending\":null}"));
            readers.add(new FinanceStatePort.ReaderBinding(domain,SOURCE_REF,body->{
                require(object(parse(body.bytes()),"explicit clear fixture").get("pending")==Nil.INSTANCE,"other owner pending");
                return FinanceStatePort.Pending.CLEAR;
            }));
        }
        feast.ifPresent(body->docs.add(new FinanceStatePort.Document(FinanceStatePort.Domain.FEAST,
                new ExactRef("synthetic-feast-body",body.length,ActionCodec.sha256(body)),body)));
        if(installOwner)readers.add(runtime.financeBinding().decoder());
        return state(request,docs,readers);
    }
    private void blocked(Optional<byte[]> body,boolean owner) {
        var port=fixture(body,owner);var request=request();
        var snapshot=known(port,request);
        assertFalse(snapshot.spendingLedgersKnownClear());
        var definitions=new FinanceReadContracts(query->new FinanceReadContracts.Registration(SOURCE_REF,
                new FinanceReadContracts.Permission(Optional.empty(),query.operation().value(),
                        ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
        PlanningReadPort failOnRead=new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest current) {
                throw new AssertionError("blocked Feast commitment reached a Native read");
            }
        };
        assertInstanceOf(OrdinaryFinanceCollector.Unavailable.class,
                new OrdinaryFinanceCollector(definitions,failOnRead,port).spending(request));
        body.ifPresent(raw->assertArrayEquals(raw,port.read(request) instanceof FinanceStatePort.Known value
                ? value.snapshot().head().bodies().stream().filter(d->d.domain()==FinanceStatePort.Domain.FEAST).findFirst().orElseThrow().bytes()
                : new byte[0]));
    }
    @Test void actualPendingProducerCannotBecomeZeroCommitments() {
        byte[] body=encoded(true);
        assertTrue(FeastDomainRuntime.decode(body).pending().isPresent());
        blocked(Optional.of(body),true);
        assertArrayEquals(body,FeastDomainRuntime.encode(FeastDomainRuntime.decode(body)));
    }
    @Test void missingFeastIsUnknownRatherThanClear() {blocked(Optional.empty(),true);}
    @Test void malformedOriginalCannotAcquireClear() {
        blocked(Optional.of(("{\"schema\":\""+FeastDomainRuntime.SCHEMA+"\",\"pending\":{\"episode_run_id\":\"unknown\"},\"resolved\":null}")
                .getBytes(StandardCharsets.UTF_8)),true);
    }
    @Test void absentOwningDecoderCannotAcquireClear() {blocked(Optional.of(encoded(false)),false);}
    @Test void actualExplicitClearProducerRemainsEligible() {
        byte[] body=encoded(false);
        assertEquals(FinanceStatePort.Pending.CLEAR,runtime.financeBinding().decoder().reader().decode(
                new FinanceStatePort.Document(FinanceStatePort.Domain.FEAST,new ExactRef("clear",body.length,ActionCodec.sha256(body)),body)));
        assertTrue(known(fixture(Optional.of(body),true),request()).spendingLedgersKnownClear());
    }
}
