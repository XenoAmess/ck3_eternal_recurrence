package org.xar.ck3.control.application.planning.finance;

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
final class FinanceStateBoundaryTest {
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
    @Test void missingOrUnqualifiedFamilyBodyNeverBecomesClear() {
        var request=request();var doc=document(FinanceStatePort.Domain.CHILD_MARRIAGE,"{\"schema\":\"unqualified\",\"pending\":null}");
        var snapshot=known(state(request,List.of(doc),List.of()),request);
        assertTrue(snapshot.ledger(FinanceStatePort.Domain.CHILD_MARRIAGE).isEmpty());
        assertTrue(snapshot.unavailableReason(FinanceStatePort.Domain.CHILD_MARRIAGE).isPresent());
        assertFalse(snapshot.spendingLedgersKnownClear());
    }
    @Test void invalidUnrelatedBodyDoesNotEraseStrictKnownGiftBody() {
        var request=request();
        var gift=document(FinanceStatePort.Domain.FACTION_GIFT,"{\"schema\":\"xar.ck3.faction_gift_pending_v1\",\"format_version\":1,\"pending\":null,\"resolved_request_outcomes\":{}}");
        var crown=document(FinanceStatePort.Domain.CROWN,"{\"pending\":true}");
        var snapshot=known(state(request,List.of(gift,crown),List.of(FinanceStatePort.giftReader(SOURCE_REF))),request);
        assertEquals(FinanceStatePort.Pending.CLEAR,snapshot.ledger(FinanceStatePort.Domain.FACTION_GIFT).orElseThrow().pending());
        assertTrue(snapshot.ledger(FinanceStatePort.Domain.CROWN).isEmpty());
    }
    @Test void missingPendingAndBooleanPendingCannotAcquireClearEvenFromPermissiveProvider() {
        var request=request();
        var permissive=new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.MERCENARY,SOURCE_REF,ignored->FinanceStatePort.Pending.CLEAR);
        for(String body:List.of("{}", "{\"pending\":true}", "{\"pending\":[]}")) {
            var snapshot=known(state(request,List.of(document(FinanceStatePort.Domain.MERCENARY,body)),List.of(permissive)),request);
            assertTrue(snapshot.ledger(FinanceStatePort.Domain.MERCENARY).isEmpty());
        }
    }
    @Test void duplicateDomainOrDecoderRejectedAndArchiveBytesCannotDrift() {
        var request=request();var doc=document(FinanceStatePort.Domain.MERCENARY,"{\"pending\":null}");
        assertInstanceOf(FinanceStatePort.Missing.class,state(request,List.of(doc,doc),List.of()).read(request));
        var reader=new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.MERCENARY,SOURCE_REF,ignored->FinanceStatePort.Pending.CLEAR);
        assertThrows(IllegalArgumentException.class,()->state(request,List.of(doc),List.of(reader,reader)));
        assertThrows(IllegalArgumentException.class,()->new FinanceStatePort.Document(FinanceStatePort.Domain.MERCENARY,SOURCE_REF,new byte[]{'{','}'}));
    }
    @Test void exactOwningCodecHandlesLegacyBomWithoutChangingOriginalEvidence() {
        var request=request();String json="\ufeff{\"schema\":\"xar.ck3.faction_gift_pending_v1\",\"format_version\":1,\"pending\":null,\"resolved_request_outcomes\":{}}";
        var document=document(FinanceStatePort.Domain.FACTION_GIFT,json);
        var snapshot=known(state(request,List.of(document),List.of(FinanceStatePort.giftReader(SOURCE_REF))),request);
        assertEquals(FinanceStatePort.Pending.CLEAR,snapshot.ledger(FinanceStatePort.Domain.FACTION_GIFT).orElseThrow().pending());
        assertArrayEquals(json.getBytes(StandardCharsets.UTF_8),snapshot.ledger(FinanceStatePort.Domain.FACTION_GIFT).orElseThrow().document().bytes());
    }
    @Test void factoryStagesDoNotCompeteWithConstructionOrFeastAndPendingContributorCannotCreateNewSpend() {
        var request=request();
        var definitions=new FinanceReadContracts(query->new FinanceReadContracts.Registration(SOURCE_REF,new FinanceReadContracts.Permission(
                Optional.empty(),query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
        PlanningReadPort noRead=new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) { throw new AssertionError("unexpected native read"); }
        };
        var collector=new OrdinaryFinanceCollector(definitions,noRead,state(request,List.of(),List.of()));
        var policies=new OrdinaryFinancePolicies(SOURCE_REF,collector,(op,req,args)->Optional.empty(),List.of());
        assertEquals(List.of(PlanningStage.PENDING_MATERIAL_PUBLICATION,PlanningStage.WAR_MERCENARY_CURRENT_CASH,PlanningStage.FACTION_GIFT),
                policies.stages().stream().map(OrdinaryPolicy::stage).toList());
        var malformed=new OrdinaryFinancePolicies(SOURCE_REF,collector,(op,req,args)->Optional.empty(),
                List.of((req,draft)->Optional.of(new OrdinaryPolicy.Replace(OrdinaryPolicy.Draft.empty(),"must not grant a new action"))));
        assertInstanceOf(OrdinaryPolicy.Defer.class,malformed.stages().getFirst().evaluate(request,OrdinaryPolicy.Draft.empty()));
    }
    @Test void borrowedStateCannotFallBackToOpeningAnUnborrowedTransaction() {
        var request=request();
        Session held=(Session)java.lang.reflect.Proxy.newProxyInstance(Session.class.getClassLoader(),new Class<?>[]{Session.class},
                (proxy,method,args)->{throw new AssertionError("this boundary must not dereference or replace the writer");});
        var original=new FinanceStatePort(ignored->{throw new AssertionError("borrowed call reopened original transaction");},List.of());
        assertThrows(IllegalStateException.class,()->original.read(held,request));
        FinanceStatePort.SourcePort actual=new FinanceStatePort.SourcePort() {
            @Override public FinanceStatePort.Read readUnderOriginalLock(PlanningRequest ignored) { throw new AssertionError("unexpected second writer transaction"); }
            @Override public FinanceStatePort.Read readUnderOriginalLock(Session borrowed,PlanningRequest current) {
                assertSame(held,borrowed);assertEquals(request,current);return new FinanceStatePort.Head(current.before(),SOURCE_REF,List.of(),List.of(),Optional.empty());
            }
        };
        assertInstanceOf(FinanceStatePort.Known.class,new FinanceStatePort(actual,List.of()).read(held,request));
    }
    @Test void strictActivityOwnsOneInputContractAndBorrowedBudgetCannotMintAnotherRoute() {
        var request=request();var called=new java.util.ArrayList<String>();
        Session held=(Session)java.lang.reflect.Proxy.newProxyInstance(Session.class.getClassLoader(),new Class<?>[]{Session.class},
                (proxy,method,args)->{throw new AssertionError("budget adapter replaced its borrowed writer");});
        var definitions=new FinanceReadContracts(query->new FinanceReadContracts.Registration(SOURCE_REF,new FinanceReadContracts.Permission(
                Optional.empty(),query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)),
                new FinanceReadContracts.ExternalFeastInputs() {
                    @Override public PlanningReadResult<PlanningReadReceipt> read(PlanningRequest current) { assertEquals(request,current);called.add("normal");return new PlanningReadResult.Unavailable<>("native unavailable",Optional.empty()); }
                    @Override public PlanningReadResult<PlanningReadReceipt> read(Session borrowed,PlanningRequest current) { assertSame(held,borrowed);assertEquals(request,current);called.add("borrowed");return new PlanningReadResult.Unavailable<>("native unavailable",Optional.empty()); }
                });
        assertFalse(definitions.registeredContracts().stream().anyMatch(c->List.of(FinanceReadContracts.Query.FEAST_INPUTS.operation(),
                FinanceReadContracts.Query.FEAST_DIAGNOSTIC.operation(),FinanceReadContracts.Query.FEAST_HOSTED.operation()).contains(c.operation())));
        PlanningReadPort unregistered=new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> ignored,PlanningReadRequest current) { throw new AssertionError("second generic Activity contract was invoked"); }
        };
        assertInstanceOf(PlanningReadResult.Unavailable.class,definitions.read(FinanceReadContracts.Query.FEAST_INPUTS,unregistered,request));
        assertInstanceOf(PlanningReadResult.Unavailable.class,definitions.read(held,FinanceReadContracts.Query.FEAST_INPUTS,unregistered,request));
        assertEquals(List.of("normal","borrowed"),called);
    }
    @Test void clearMatrilinealBodyDoesNotEraseAnUnknownOrPendingDefaultMarriageProducer() {
        var request=request();var domains=List.of(FinanceStatePort.Domain.CONSTRUCTION,FinanceStatePort.Domain.FACTION_GIFT,
                FinanceStatePort.Domain.FEAST,FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE,FinanceStatePort.Domain.CHILD_MARRIAGE);
        var documents=domains.stream().map(domain->document(domain,"{\"pending\":null}")).toList();
        var readers=java.util.stream.Stream.concat(domains.stream(),java.util.stream.Stream.of(FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE))
                .map(domain->new FinanceStatePort.ReaderBinding(domain,SOURCE_REF,body->
                        object(parse(body.bytes()),"actual test body").get("pending")==Nil.INSTANCE?FinanceStatePort.Pending.CLEAR:FinanceStatePort.Pending.PENDING)).toList();
        assertFalse(known(state(request,documents,readers),request).spendingLedgersKnownClear());
        var pending=new java.util.ArrayList<>(documents);pending.add(document(FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE,"{\"pending\":{\"request_id\":\"unknown-default-1\"}}"));
        assertFalse(known(state(request,pending,readers),request).spendingLedgersKnownClear());
        var clear=new java.util.ArrayList<>(documents);clear.add(document(FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE,"{\"pending\":null}"));
        assertTrue(known(state(request,clear,readers),request).spendingLedgersKnownClear());
    }
    @Test void actualCanonicalProducerRejectsWrongWriterBeforeReadingDomainsOrOpeningAnotherLock() {
        var request=request();var lock=java.nio.file.Path.of("target","original-writer.lock").toAbsolutePath().normalize();
        Session wrong=(Session)java.lang.reflect.Proxy.newProxyInstance(Session.class.getClassLoader(),new Class<?>[]{Session.class},(proxy,method,args)->{
            assertEquals("requireWriter",method.getName());assertEquals(lock,args[0]);throw new java.io.IOException("not the original writer");
        });
        var store=(org.xar.ck3.control.continuity.writer.ContinuityStorePort)java.lang.reflect.Proxy.newProxyInstance(
                Session.class.getClassLoader(),new Class<?>[]{org.xar.ck3.control.continuity.writer.ContinuityStorePort.class},
                (proxy,method,args)->{throw new AssertionError("borrowed producer attempted to open a writer");});
        var actions=(ActionJournal)java.lang.reflect.Proxy.newProxyInstance(ActionJournal.class.getClassLoader(),new Class<?>[]{ActionJournal.class},
                (proxy,method,args)->{throw new AssertionError("wrong-writer path reached action facts");});
        var source=new CanonicalFinanceStateSource(lock,store,actions,session->{throw new AssertionError("wrong writer reached Driver");},
                session->{throw new AssertionError("wrong writer reached SAVE");},List.of());
        var result=assertInstanceOf(FinanceStatePort.Unavailable.class,source.readUnderOriginalLock(wrong,request));
        assertTrue(result.reason().contains("not the original writer"));
    }
    @Test void nativeCashRequestAddsOnlyItsActualNonreservedNativeRevisionField() {
        var request=request();var definitions=new FinanceReadContracts(query->new FinanceReadContracts.Registration(SOURCE_REF,new FinanceReadContracts.Permission(
                Optional.empty(),query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
        var query=FinanceReadContracts.Query.CASH;var before=request.before();
        var nativeRequest=definitions.contract(query).prepare(new PlanningReadRequest(before,request.source(),request.sessionId(),query.operation(),new Obj(java.util.Map.of()),request.deadline()),"actual-cash-read");
        Obj fields=object(parse(nativeRequest.additionalFields().bytes()),"actual cash producer fields");
        assertEquals(Set.of("expected_snapshot_revision"),fields.members().keySet());
        assertEquals(new IntegerValue(before.frame().identity().nativeRevision()),fields.get("expected_snapshot_revision"));
    }
    @Test void externalM1OwnsTheSingleFactionReadAndPreservesTheActualBorrowedSession() {
        var request=request();var calls=new java.util.ArrayList<String>();
        Session held=(Session)java.lang.reflect.Proxy.newProxyInstance(Session.class.getClassLoader(),new Class<?>[]{Session.class},(proxy,method,args)->{throw new AssertionError("external faction adapter replaced the actual writer");});
        var definitions=new FinanceReadContracts(query->new FinanceReadContracts.Registration(SOURCE_REF,new FinanceReadContracts.Permission(
                Optional.empty(),query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)),
                new FinanceReadContracts.ExternalFeastInputs() {
                    public PlanningReadResult<PlanningReadReceipt> read(PlanningRequest input){throw new AssertionError("unrelated Activity read");}
                    public PlanningReadResult<PlanningReadReceipt> read(Session same,PlanningRequest input){throw new AssertionError("unrelated Activity read");}
                },new FinanceReadContracts.ExternalFactionAlerts() {
                    public ExactRef definitionSource(){return SOURCE_REF;}
                    public PlanningReadResult<PlanningReadReceipt> read(PlanningRequest input){assertEquals(request,input);calls.add("normal");return new PlanningReadResult.Unavailable<>("actual native gap",Optional.empty());}
                    public PlanningReadResult<PlanningReadReceipt> read(Session same,PlanningRequest input){assertSame(held,same);assertEquals(request,input);calls.add("borrowed");return new PlanningReadResult.Unavailable<>("actual native gap",Optional.empty());}
                    public void verifyOriginal(PlanningReadReceipt original,Obj snapshot){throw new AssertionError("an unavailable read cannot create original evidence");}
                });
        assertFalse(definitions.registeredContracts().stream().anyMatch(contract->contract.operation().equals(FinanceReadContracts.Query.FACTION_ALERTS.operation())));
        PlanningReadPort unregistered=new PlanningReadPort(){public <T> PlanningReadResult<T> read(ReadContract<T> ignored,PlanningReadRequest input){throw new AssertionError("generic same-operation faction contract must not exist");}};
        assertInstanceOf(PlanningReadResult.Unavailable.class,definitions.read(FinanceReadContracts.Query.FACTION_ALERTS,unregistered,request));
        assertInstanceOf(PlanningReadResult.Unavailable.class,definitions.read(held,FinanceReadContracts.Query.FACTION_ALERTS,unregistered,request));
        assertEquals(List.of("normal","borrowed"),calls);
    }
    @Test void fullMercenaryProducerBodyAboveProposalLimitReachesActualStateConsumerWithoutLosingUnknown() {
        var request=request();Obj claim=OrdinaryFinanceCollector.obj("action_request_id",new Text("large-original-request"),"company_id",new IntegerValue(BigInteger.ZERO),
                "status",new Text("submission_unresolved"),"pre_capture_epoch",new IntegerValue(BigInteger.ONE),"pre_player_army_ids",new Arr(List.of()),
                "source_frame",OrdinaryFinanceCollector.sourceFrame(request),"decision",new Obj(java.util.Map.of()),"original_extension",new Text("x".repeat(200000)));
        byte[] original=org.xar.ck3.control.application.driver.DriverJson.encode(OrdinaryFinanceCollector.obj("schema",new Text(MercenaryProcurement.SCHEMA),"pending",claim,"observed",new Arr(List.of())));
        var produced=MercenaryProcurement.decode(original);assertTrue(produced.pending().isPresent());assertArrayEquals(original,MercenaryProcurement.encode(produced));
        var document=new FinanceStatePort.Document(FinanceStatePort.Domain.MERCENARY,new ExactRef("D:/fixture/large-native-body.json",original.length,ActionCodec.sha256(original)),original);
        var reader=new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.MERCENARY,SOURCE_REF,body->MercenaryProcurement.decode(body.bytes()).pending().isPresent()?FinanceStatePort.Pending.PENDING:FinanceStatePort.Pending.CLEAR);
        var consumed=known(state(request,List.of(document),List.of(reader)),request).ledger(FinanceStatePort.Domain.MERCENARY).orElseThrow();
        assertEquals(FinanceStatePort.Pending.PENDING,consumed.pending());assertEquals(claim,consumed.original().get("pending"));
        assertFalse(known(state(request,List.of(document),List.of(reader)),request).spendingLedgersKnownClear());
    }
}

