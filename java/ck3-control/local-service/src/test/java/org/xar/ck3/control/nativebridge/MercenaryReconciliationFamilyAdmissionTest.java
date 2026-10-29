package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeFinanceEffects;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinancePolicies;
import org.xar.ck3.control.application.planning.finance.MercenaryProcurement;
import org.xar.ck3.control.application.planning.finance.NativeMercenaryMarket;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.service.root.RootReconciliationAuthority;

/** Actual sole-writer UNKNOWN fixture and pure read-family binding.
 * This test grants no physical Root lease, native employer/payment/army result or live business credit.
 */
final class MercenaryReconciliationFamilyAdmissionTest {
    @TempDir Path temporary;
    private static final long COMPANY=0x81000003L;
    private static final OperationKey HIRE=OrdinaryFinancePolicies.MERCENARY;
    private static final String EXE="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final Obj EMPTY=new Obj(Map.of());
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static FinanceReadContracts producer(ExactRef source){
        return new FinanceReadContracts(query->new FinanceReadContracts.Registration(source,
                new FinanceReadContracts.Permission(Optional.of("game.command."+query.operation().value()),
                        "game.command."+query.operation().value(),ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                        ReadContract.WireProfile.EXECUTE_STEP)));
    }
    private static RootReconciliationAuthority.AllowedRead allowed(ReadContract<?> contract){
        return new RootReconciliationAuthority.AllowedRead(contract,EMPTY,RootReconciliationAuthority.QueryKind.MERCENARY_EMPLOYER);
    }
    private static ReadContract<FinanceReadContracts.Packet> copy(ReadContract<FinanceReadContracts.Packet> actual,
            String id,String permission,ReadContract.GuardMode mode){
        return new ReadContract<>(id,actual.operation(),actual.requiredCapability(),permission,actual.permissionMode(),
                actual.wireProfile(),mode,actual.sourceRef(),actual::prepare,actual::decode,actual::replay);
    }
    private static ExpectedPostcondition expected(ActionCommand template,long company){
        return new ExpectedPostcondition(1,template.before(),template.source(),NativeFinanceEffects.HIRE_SCHEMA,
                List.of(new ExpectedInteger(new FieldKey("company_id"),BigInteger.valueOf(company)),
                        new ExpectedInteger(new FieldKey("actor_id"),template.before().frame().identity().player()),
                        new ExpectedText(new FieldKey("status"),"employment_observed")));
    }
    private record Material(PlanningReadReceipt read,Obj snapshot) { }
    /** Constructed DATA exercises the owning codecs and reducers; it never obtains a Root read permit. */
    private static Material material(ReconciliationIdentity identity,ReadContract<?> profile,boolean employed){
        var factual=identity.factual();var frame=factual.frame();var nativeFrame=frame.identity();
        var snapshot=obj("played_character",obj("character_id",new IntegerValue(nativeFrame.player()),"alive",new Bool(true)),
                "native_revision",new IntegerValue(nativeFrame.nativeRevision()),"date_raw",new IntegerValue(nativeFrame.dateRaw()),
                "snapshot_id",new Text(frame.snapshotId()),"revision",new IntegerValue(frame.revision()),"episode_run_id",new Text(frame.episodeRunId()),
                "paused",new Bool(true),"map_ready",new Bool(true),"active_wars",new Arr(List.of()),"player_armies",new Arr(List.of()),
                "played_character_gold",obj("raw",new IntegerValue(BigInteger.valueOf(50000000)),"scale",new IntegerValue(BigInteger.valueOf(100000))),
                "diagnostics",obj("hello",obj("expected_ck3_version",new Text("1.20.0.4"),"expected_ck3_sha256",new Text(EXE))));
        var terms=object(parse(raw("""
                {"available":true,"unavailable_reason":null,"can_hire":false,"can_afford":true,"payment_status":2,
                "resource_scale":100000,"resource_costs_raw":[1000000,0,0,0,0,0,0,0,0,0],"hire_duration_months":36,
                "can_hire_reasons_available":true,"can_hire_reason_literal":"already employed","can_afford_reasons_available":true,"can_afford_reason_literal":""}
                """).bytes()),"software terms");
        var location=object(parse(raw("""
                {"company_home_title_id":null,"company_home_province_id":null,"hire_auto_raise_province_id":null,
                "actor_active_war_count":0,"hire_auto_raise_attempted_in_active_war":false,"company_home_ready":false,
                "company_home_failure":"not observed","company_home_source":"software DATA","hire_auto_raise_position_ready":false,
                "hire_auto_raise_position_failure":"not observed","hire_auto_raise_position_source":"software DATA"}
                """).bytes()),"software location");
        var company=obj("company_id",new IntegerValue(BigInteger.valueOf(COMPANY)),"employer_id",employed?new IntegerValue(nativeFrame.player()):Nil.INSTANCE,
                "manager_slot_index",new IntegerValue(BigInteger.ZERO),"troop_strength",obj("available",new Bool(false),
                "unavailable_reason",new Text("not observed"),"current_soldiers",Nil.INSTANCE),"final_terms",terms,"location",location);
        var market=obj("schema",new Text("ck3_12004_player_mercenary_context_v1"),"game_version",new Text("1.20.0.4"),
                "executable_sha256",new Text(EXE),"actor_character_id",new IntegerValue(nativeFrame.player()),
                "date_raw",new IntegerValue(nativeFrame.dateRaw()),"capture_epoch",new IntegerValue(BigInteger.TWO),
                "read_only",new Bool(true),"native_hire_mode",new IntegerValue(BigInteger.ONE),"available",new Bool(true),
                "unavailable_reason",Nil.INSTANCE,"rows",new Arr(List.of(company)));
        var result=obj("step",new Text(FinanceReadContracts.Query.MERCENARIES.operation().value()),"accepted",new Bool(true),
                "snapshot_revision",new IntegerValue(nativeFrame.nativeRevision()),"player_mercenary_context",market);
        String requestId=employed?"software-independent-employer":"software-no-employer";
        var full=new RawJson(encode(obj("type",new Text("command_result"),"protocol_version",new IntegerValue(BigInteger.ONE),
                "request_id",new Text(requestId),"ok",new Bool(true),"result",result)));
        var packet=ByteBuffer.allocate(full.bytes().length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(full.bytes().length).put(full.bytes()).array();
        var ack=new NativeActionPort.AckReceived(requestId,true,Optional.of(new RawJson(encode(result))),full,packet);
        var query=PlanningReadRequest.newReconciliation(identity,FinanceReadContracts.Query.MERCENARIES.operation(),EMPTY,Instant.now().plusSeconds(30));
        var binding=new GuardEvidence(query.origin(),identity.source(),identity.sessionId(),identity.connectionGeneration(),query.operation(),
                identity.nativeEvidence(),identity.capabilityEvidence(),"constructed-reconciliation-DATA",identity.observedAt(),query.deadline(),identity.supportingEvidence());
        var guard=new PlanningReadGuard(binding,new PlanningReadGuard.Reconciliation(),"b".repeat(64));
        return new Material(new PlanningReadReceipt(query,profile.contractId(),requestId,guard,guard,ack),snapshot);
    }
    @Test void actualUnknownAdmitsOnlyItsOriginalMercenaryEmployerReadWithoutAnotherHire() throws Exception {
        var dispatches=new AtomicInteger();
        var preparation=new ActionPorts.PreparationPort(){
            @Override public NativeRequest prepare(ActionCommand command){
                return new NativeRequest(HIRE.value(),Optional.of("game.command.hire-mercenary-v1"),
                        new RawJson(StrictJson.canonical(StrictJson.object().put("company_id",COMPANY))));
            }
        };
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(HIRE,"game.command.hire-mercenary-v1",
                (command,attempt,original)->new ActionPorts.Pending("independent employer material unavailable",List.of(attempt.guard().nativeEvidence())),
                dispatches::incrementAndGet,Optional.empty(),Optional.empty(),false,Optional.of(preparation));
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("canonical"),true,scenario)){
            var template=fixture.command("mercenary-original");
            var selected=obj("company_id",new IntegerValue(BigInteger.valueOf(COMPANY)),"gold_cost_raw",new IntegerValue(BigInteger.valueOf(1000000)),
                    "predicted_auto_raise_province_id",Nil.INSTANCE,"purpose_war_ids",new Arr(List.of()),
                    "finance",obj("observed_treasury_raw",new IntegerValue(BigInteger.valueOf(50000000))));
            var arguments=obj("company_id",new IntegerValue(BigInteger.valueOf(COMPANY)),
                    "source_frame",org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.sourceFrame(template.before()),
                    "pre_capture_epoch",new IntegerValue(BigInteger.ONE),"pre_player_army_ids",new Arr(List.of()),
                    "decision",obj("selected_candidate",selected));
            var command=new ActionCommand(template.actionId(),template.before(),template.source(),template.sessionId(),HIRE,
                    arguments,expected(template,COMPANY),template.claims(),template.deadline());
            var pending=fixture.coordinator.execute(command);assertInstanceOf(ActionState.Unknown.class,pending.state());
            var attempt=ActionTransitions.attempt(pending.state()).orElseThrow();
            var identity=fixture.writer.locked(same->fixture.archive.inSession(same,archive->{
                try{
                    assertTrue(ContinuityActionJournal.receipts(same.head().state(),archive).contains(pending));
                    var receipt=archive.receiptReferenceOf(pending);assertEquals(pending,archive.loadReceipt(receipt));
                    var driver=archive.preserveMaterial(raw("{\"role\":\"unqualified-same-driver-data\"}"));
                    var evidence=new ReconciliationIdentity.Evidence(attempt.guard().nativeEvidence(),attempt.guard().capabilityEvidence(),
                            archive.preserveMaterial(raw("{\"role\":\"heartbeat-data\"}")),archive.preserveMaterial(raw("{\"role\":\"manifest-data\"}")),
                            driver,archive.preserveMaterial(raw("{\"role\":\"source-data\"}")));
                    return ReconciliationIdentity.fromCanonical(pending,command.before(),command.source(),command.sessionId(),
                            attempt.guard().connectionGeneration(),receipt,driver,evidence,Instant.now());
                }catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
            }));
            var definitions=producer(command.source().sourceRef());var profile=definitions.mercenaryEmployerContract();
            var catalog=new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(profile,command.source().sourceRef()),
                    new RootReadContractCatalog.InstalledRead(definitions.contract(FinanceReadContracts.Query.MERCENARIES),command.source().sourceRef())),List.of());
            assertTrue(catalog.containsIdentity(profile));assertSame(profile,allowed(profile).contract());
            assertTrue(definitions.registeredContracts().stream().anyMatch(value->value==profile));
            var query=PlanningReadRequest.newReconciliation(identity,FinanceReadContracts.Query.MERCENARIES.operation(),EMPTY,Instant.now().plusSeconds(30));
            NativeFinanceEffects.requireCanonicalMercenaryReconciliation(pending,attempt,identity,profile,query);
            var restored=ReconciliationIdentityCodec.decode(ReconciliationIdentityCodec.encode(identity));assertEquals(identity,restored);
            NativeFinanceEffects.requireCanonicalMercenaryReconciliation(pending,attempt,restored,profile,
                    PlanningReadRequest.newReconciliation(restored,query.operation(),EMPTY,query.deadline()));
            assertEquals(identity.factual(),FinanceReadContracts.mercenaryFrame(query));
            assertThrows(IllegalStateException.class,query::before);
            var prepared=profile.prepare(query,"independent-employer-query");
            assertEquals("query-player-mercenary-context-v1",prepared.step());
            assertEquals(Optional.of("game.command.query-player-mercenary-context-v1"),prepared.requiredCapability());
            assertArrayEquals(new byte[]{'{','}'},prepared.additionalFields().bytes());
            var ledger=MercenaryProcurement.begin(MercenaryProcurement.emptyFreshEpisode(),command);
            assertEquals(attempt.requestId(),ledger.pending().orElseThrow().requestId());
            var missing=material(identity,profile,false);
            var missingPacket=profile.replay(missing.read());
            var missingMarket=NativeMercenaryMarket.decode(missingPacket,identity.factual(),identity.source(),identity.sessionId(),missing.snapshot());
            var unresolved=MercenaryProcurement.observeEmployment(ledger,attempt.requestId(),missing.snapshot(),missingMarket);
            assertTrue(unresolved.pending().isPresent());assertTrue(unresolved.observed().isEmpty());
            assertEquals(MercenaryProcurement.NewHireBarrier.UNKNOWN_PENDING,MercenaryProcurement.barrier(missing.snapshot(),unresolved));
            var employer=material(identity,profile,true);
            var originalPacket=definitions.decodeOriginal(FinanceReadContracts.Query.MERCENARIES,employer.read(),employer.snapshot());
            var employerMarket=NativeMercenaryMarket.decode(originalPacket,identity.factual(),identity.source(),identity.sessionId(),employer.snapshot());
            var employment=MercenaryProcurement.observeEmployment(unresolved,attempt.requestId(),employer.snapshot(),employerMarket);
            assertTrue(employment.pending().isEmpty());assertEquals(MercenaryProcurement.Status.EMPLOYMENT_OBSERVED,employment.observed().getFirst().status());
            assertEquals(employment.original(),MercenaryProcurement.decode(MercenaryProcurement.encode(employment)).original());
            assertEquals(new Bool(false),employment.observed().getFirst().original().get("payment_verified"));
            assertEquals(new Bool(false),employment.observed().getFirst().original().get("army_creation_verified"));
            assertFalse(employerMarket.receivedFundsVerified());
            var drift=employer.snapshot().with("revision",new IntegerValue(identity.factual().frame().revision().add(BigInteger.ONE)));
            assertThrows(IllegalArgumentException.class,()->MercenaryProcurement.observeEmployment(unresolved,attempt.requestId(),drift,employerMarket));
            assertThrows(IllegalArgumentException.class,()->allowed(definitions.contract(FinanceReadContracts.Query.MERCENARIES)));
            assertThrows(IllegalArgumentException.class,()->allowed(copy(profile,profile.contractId(),"game.command.hire-mercenary-v1",profile.guardMode())));
            var clone=copy(profile,profile.contractId(),profile.permissionKey(),profile.guardMode());
            assertFalse(catalog.containsIdentity(clone));
            var extra=new Obj(Map.of("company_id",new IntegerValue(BigInteger.ONE)));
            assertThrows(IllegalArgumentException.class,()->new RootReconciliationAuthority.AllowedRead(profile,extra,RootReconciliationAuthority.QueryKind.MERCENARY_EMPLOYER));
            assertThrows(IllegalArgumentException.class,()->NativeFinanceEffects.requireCanonicalMercenaryReconciliation(pending,attempt,identity,profile,
                    PlanningReadRequest.newReconciliation(identity,query.operation(),extra,query.deadline())));
            assertThrows(IllegalArgumentException.class,()->NativeFinanceEffects.requireCanonicalMercenaryReconciliation(pending,attempt,identity,profile,
                    new PlanningReadRequest(identity.factual(),identity.source(),identity.sessionId(),query.operation(),EMPTY,query.deadline())));
            var otherAttempt=new ActionState.Attempt(attempt.requestId()+"-foreign",attempt.submittedAt(),attempt.guard(),attempt.preparedRequest());
            assertThrows(IllegalArgumentException.class,()->NativeFinanceEffects.requireCanonicalMercenaryReconciliation(pending,otherAttempt,identity,profile,query));
            var wrongPrepared=new NativeRequest(HIRE.value(),Optional.of("game.command.hire-mercenary-v1"),raw("{\"company_id\":1}"));
            var changedAttempt=new ActionState.Attempt(attempt.requestId(),attempt.submittedAt(),attempt.guard(),wrongPrepared);
            var changed=new ActionReceipt(pending.version(),pending.sequence(),command,pending.bodySha256(),
                    new ActionState.Unknown(Optional.of(changedAttempt),Optional.empty(),"wrong prepared full company",List.of()));
            assertThrows(IllegalArgumentException.class,()->NativeFinanceEffects.requireCanonicalMercenaryReconciliation(changed,changedAttempt,identity,profile,query));
            int reads=fixture.nativeReadWrites();assertEquals(pending,fixture.coordinator.execute(command));
            assertEquals(reads,fixture.nativeReadWrites());assertEquals(1,fixture.nativeActionWrites());assertEquals(1,dispatches.get());
            assertFalse(pending.settled());assertFalse(pending.eligibleAdvance());
        }
    }
}

