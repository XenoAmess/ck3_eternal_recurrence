package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment;

/** Actual same-writer import/state/action reader pipeline. Source fixture custody is not a Core/private Game qualification. */
final class CanonicalFundingPendingRuntimeTest {
    @TempDir Path root;
    private static PlanningRequest request() {
        var source=new G2Source("xenoamess-full-tower-eb9d2c1186","2026-10-24T00:00:00Z","1.20.0.4",new ExactRef("D:/fixture/complete-runtime-source.json",1,"a".repeat(64)));
        var identity=new ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(32904),BigInteger.valueOf(3),BigInteger.valueOf(53288472)),"native-funding-fixture",BigInteger.valueOf(3),"episode-funding-fixture"),1);
        Obj snapshot=OrdinaryFinanceCollector.obj("paused",new Bool(true),"map_ready",new Bool(true),"snapshot_id",new Text(identity.frame().snapshotId()),"revision",new IntegerValue(identity.frame().revision()),
                "native_revision",new IntegerValue(identity.frame().identity().nativeRevision()),"date_raw",new IntegerValue(identity.frame().identity().dateRaw()),"episode_run_id",new Text(identity.frame().episodeRunId()),
                "played_character",OrdinaryFinanceCollector.obj("character_id",new IntegerValue(identity.frame().identity().player()),"alive",new Bool(true)),"active_wars",new Arr(List.of()),"player_armies",new Arr(List.of()),"active_event",Nil.INSTANCE,"pending_character_interaction",Nil.INSTANCE);
        return new PlanningRequest(identity,source,"session-funding-fixture",Instant.parse("2099-01-01T00:00:00Z"),new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }

    @Test void currentRuntimeDecodesImportedBodiesAfterProducerRecompileWithoutReauditingSourceFiles()throws Exception {
        var input=request();Path current=root.resolve("recompiled-current-runtime.class");
        byte[] loadedBytes="current runtime decoder already loaded".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        java.nio.file.Files.write(current,loadedBytes);
        var currentRef=new ExactRef(current.toAbsolutePath().normalize().toString(),loadedBytes.length,ActionCodec.sha256(loadedBytes));
        var fixture=CanonicalFundingFixture.create(root.resolve("historical-producer"),input,CanonicalFundingFixture.Variant.CLEAR,Optional.empty(),
                originals->originals.stream().map(binding->new CanonicalFinanceStateSource.Binding(
                        new FinanceStatePort.ReaderBinding(binding.decoder().domain(),currentRef,binding.decoder().reader()),
                        binding.slot(),binding.contractSchema(),binding.maximumBodyBytes(),List.of(currentRef))).toList());
        java.nio.file.Files.delete(current); // Source files are not a prerequisite for an already loaded decoder.
        fixture.withSession(same->{
            var head=same.head();var persisted=same.persistedHead();
            var actual=assertInstanceOf(org.xar.ck3.control.continuity.writer.DomainBodies.Available.class,
                    same.readDomain(org.xar.ck3.control.continuity.writer.DomainBodies.Slot.CONSTRUCTION));
            assertNotEquals(List.of(currentRef),actual.reference().producerSources());
            var observed=assertInstanceOf(FinanceStatePort.Known.class,fixture.state().read(same,input));
            assertTrue(observed.snapshot().spendingLedgersKnownClear());
            assertEquals(head.digest(),same.head().digest());assertEquals(persisted,same.persistedHead());
            assertEquals(actual.reference(),org.xar.ck3.control.continuity.writer.DomainBodies.reference(
                    same.head().state(),org.xar.ck3.control.continuity.writer.DomainBodies.Slot.CONSTRUCTION).orElseThrow());
            java.nio.file.Files.writeString(Path.of(actual.reference().payload().path()),"changed actual payload");
            var tampered=assertInstanceOf(FinanceStatePort.Known.class,fixture.state().read(same,input));
            assertTrue(tampered.snapshot().ledger(FinanceStatePort.Domain.CONSTRUCTION).isEmpty());
            assertFalse(tampered.snapshot().spendingLedgersKnownClear(),"a changed payload must never become clear");
            assertEquals(head.digest(),same.head().digest());assertEquals(persisted,same.persistedHead());
            return null;
        });
    }
    @Test void ordinaryFinanceUsesTheCurrentHeldWriterForEachStateAndQueryWithoutNestedSessions()throws Exception {
        var input=request();var fixture=CanonicalFundingFixture.create(root.resolve("ordinary-current-session"),input,CanonicalFundingFixture.Variant.CLEAR);
        var active=new java.util.concurrent.atomic.AtomicReference<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session>();
        var resolutions=new java.util.concurrent.atomic.AtomicInteger();var queries=new java.util.concurrent.atomic.AtomicInteger();
        var definitions=new FinanceReadContracts(query->new FinanceReadContracts.Registration(input.source().sourceRef(),new FinanceReadContracts.Permission(
                Optional.empty(),query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
        PlanningReadPort reads=new PlanningReadPort(){
            public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("ordinary finance reopened an unborrowed native read");}
            public <T> PlanningReadResult<T> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ReadContract<T> contract,PlanningReadRequest request){
                assertSame(active.get(),same);queries.incrementAndGet();return new PlanningReadResult.Unavailable<>("controlled native gap",Optional.empty());
            }
        };
        var collector=new OrdinaryFinanceCollector(definitions,reads,fixture.state(),()->{resolutions.incrementAndGet();return active.get();});
        assertEquals(0,resolutions.get(),"installation must not capture a soon-closed writer Session");
        var policies=new OrdinaryFinancePolicies(input.source().sourceRef(),collector,(operation,request,args)->Optional.empty(),List.of());
        org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session previous=null;
        for(int iteration=0;iteration<2;iteration++){
            var prior=previous;
            previous=fixture.withSession(same->{
                assertNotSame(prior,same);active.set(same);var head=same.head().digest();
                try {
                    var original=assertInstanceOf(FinanceStatePort.Missing.class,fixture.state().read(input));
                    assertTrue(original.reason().contains("nested original writer sessions"),original.reason());
                    assertInstanceOf(FinanceStatePort.Known.class,collector.state(input));
                    assertInstanceOf(OrdinaryPolicy.Keep.class,policies.stages().getFirst().evaluate(input,OrdinaryPolicy.Draft.empty()));
                    assertInstanceOf(OrdinaryFinanceCollector.Unavailable.class,collector.query(FinanceReadContracts.Query.CASH,input));
                    var foreign=(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session)java.lang.reflect.Proxy.newProxyInstance(
                            getClass().getClassLoader(),new Class<?>[]{org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session.class},
                            (proxy,method,args)->{throw new AssertionError("foreign session must not be used");});
                    assertThrows(IllegalArgumentException.class,()->collector.state(foreign,input));
                    assertEquals(head,same.head().digest());return same;
                } finally {active.set(null);}
            });
        }
        assertEquals(2,queries.get());
        assertThrows(NullPointerException.class,()->collector.state(input),"missing active session must not silently reopen the original writer");
    }

    @Test void realRegisteredImportsAndFullCanonicalInventoryCanProveOwnedSubmissionsClearWithoutNativeDebtQualification()throws Exception {
        var input=request();var fixture=CanonicalFundingFixture.create(root.resolve("clear"),input,CanonicalFundingFixture.Variant.CLEAR);
        fixture.withSession(same->{
            var before=same.head();var observed=assertInstanceOf(CanonicalFundingPending.Observed.class,fixture.service().read(same,input));
            assertInstanceOf(EmergencyFinancingAssessment.NoPendingAction.class,observed.pending());assertEquals(before.digest(),same.head().digest());
            var evidence=observed.sourceEvidence();assertEquals(7,evidence.bodies().size());assertEquals(same.persistedHead(),evidence.canonicalHead());assertEquals(before.state().sequence(),evidence.ledgerSequence());
            assertEquals(CanonicalFundingPending.Scope.OWNED_SUBMISSION_INVENTORY,evidence.scope());assertEquals(CanonicalFundingPending.NativeFundingCoverage.COMPLETE_DEBT_LOAN_REFUND_UNQUALIFIED,evidence.nativeFundingCoverage());assertEquals(0,evidence.unreceivedFundingCreditedRaw());
            var restored=CanonicalFundingPending.decodeEvidence(CanonicalFundingPending.encodeEvidence(evidence));assertEquals(evidence,restored);assertEquals(observed.pending(),CanonicalFundingPending.pending(restored));
            assertEquals(new Text("xar.java.canonical-owned-funding-inventory/v2"),CanonicalFundingPending.evidenceJson(restored).get("schema"));
            assertEquals(0,evidence.canonicalActionCount());assertTrue(evidence.unresolvedActions().isEmpty());return null;
        });
    }
    @Test void missingRegisteredBodyAndActualMercenaryUnknownCannotBecomeClear()throws Exception {
        var input=request();
        for(var variant:List.of(CanonicalFundingFixture.Variant.MISSING_MERCENARY,CanonicalFundingFixture.Variant.PENDING_MERCENARY)) {
            var fixture=CanonicalFundingFixture.create(root.resolve(variant.name()),input,variant);
            fixture.withSession(same->{var actual=fixture.service().read(same,input);
                if(variant==CanonicalFundingFixture.Variant.MISSING_MERCENARY)assertInstanceOf(CanonicalFundingPending.Unavailable.class,actual);
                else {var observed=assertInstanceOf(CanonicalFundingPending.Observed.class,actual);assertInstanceOf(EmergencyFinancingAssessment.PendingUnavailable.class,observed.pending());
                    assertEquals(FinanceStatePort.Pending.PENDING,observed.sourceEvidence().bodies().stream().filter(body->body.domain()==FinanceStatePort.Domain.MERCENARY).findFirst().orElseThrow().pending());}
                return null;});
        }
    }
    @Test void originalGenericUnknownAndAckFactsSurviveSerdeAndNeverGrantClearOrCredit()throws Exception {
        var input=request();var fixture=CanonicalFundingFixture.create(root.resolve("generic-originals"),input,CanonicalFundingFixture.Variant.CLEAR);
        fixture.withSession(same->{var original=assertInstanceOf(CanonicalFundingPending.Observed.class,fixture.service().read(same,input)).sourceEvidence();
            for(var phase:List.of(CanonicalFundingPending.Phase.INTENT_DURABLE,CanonicalFundingPending.Phase.ACKNOWLEDGED,CanonicalFundingPending.Phase.UNKNOWN,CanonicalFundingPending.Phase.COMPOSITE_UNKNOWN,
                    CanonicalFundingPending.Phase.PHYSICAL_SUBMITTING,CanonicalFundingPending.Phase.PHYSICAL_UNKNOWN)) {
                var action=new CanonicalFundingPending.ActionFact("original-generic-decision-event",new OperationKey("generic-original-decision-event"),"b".repeat(64),phase,new ExactRef("D:/fixture/original-generic-receipt.json",1,"c".repeat(64)));
                var data=new CanonicalFundingPending.SourceEvidence(original.current(),original.source(),original.sessionId(),original.canonicalHead(),original.ledgerSequence(),original.headSha256(),original.bodies(),original.installed(),original.families(),1,"d".repeat(64),List.of(action));
                var restored=CanonicalFundingPending.decodeEvidence(CanonicalFundingPending.encodeEvidence(data));assertEquals(List.of(action),restored.unresolvedActions());
                assertInstanceOf(EmergencyFinancingAssessment.PendingUnavailable.class,CanonicalFundingPending.pending(restored));assertEquals(0,restored.unreceivedFundingCreditedRaw());
            }
            for(var terminal:List.of(CanonicalFundingPending.Phase.PHYSICAL_COMPLETED,CanonicalFundingPending.Phase.PHYSICAL_NOT_POSTED)) {
                assertTrue(terminal.settled());
                var invalid=new CanonicalFundingPending.ActionFact("physical-terminal-data",new OperationKey("software-camera-presentation"),"b".repeat(64),terminal,original.canonicalHead());
                assertThrows(IllegalArgumentException.class,()->new CanonicalFundingPending.SourceEvidence(original.current(),original.source(),original.sessionId(),original.canonicalHead(),original.ledgerSequence(),original.headSha256(),
                        original.bodies(),original.installed(),original.families(),1,"d".repeat(64),List.of(invalid)));
            }
            return null;});
    }
    @Test void foreignWriterSessionAndWrongTypedEvidenceCannotAcquireLiveOrHistoricalClear()throws Exception {
        var input=request();var first=CanonicalFundingFixture.create(root.resolve("original"),input,CanonicalFundingFixture.Variant.CLEAR);var foreign=CanonicalFundingFixture.create(root.resolve("foreign"),input,CanonicalFundingFixture.Variant.CLEAR);
        foreign.withSession(same->{
            String beforeDigest=same.head().digest();ExactRef beforePersisted=same.persistedHead();
            var rejected=assertThrowsExactly(ContractViolationException.class,()->first.service().read(same,input));
            assertEquals("borrowed session belongs to another canonical writer",rejected.getMessage());
            assertEquals(beforeDigest,same.head().digest());assertEquals(beforePersisted,same.persistedHead());return null;
        });
        first.withSession(same->{var evidence=assertInstanceOf(CanonicalFundingPending.Observed.class,first.service().read(same,input)).sourceEvidence();Obj json=CanonicalFundingPending.evidenceJson(evidence);
            for(Obj bad:List.of(json.with("schema",new Text("xar.java.canonical-owned-funding-inventory/v1")),json.with("ledger_sequence",new Bool(true)),json.with("canonical_action_count",new Bool(true)),json.with("bodies",new Arr(List.of())),json.with("families",Nil.INSTANCE),json.with("unreceived_funding_credited_raw",new IntegerValue(BigInteger.ONE)),json.with("scope",new Text("COMPLETE_NATIVE_DEBT")),json.with("extra",new Bool(true))))
                assertThrows(IllegalArgumentException.class,()->CanonicalFundingPending.decodeEvidence(encode(bad)));
            var changed=new PlanningRequest(input.before(),input.source(),"another-session",input.deadline(),input.observations());assertInstanceOf(CanonicalFundingPending.Unavailable.class,first.service().read(same,changed));return null;});
    }
    @Test void settledHistorySummaryStaysBoundedAndOversizedInventoryCannotWidenTheCommandLimit()throws Exception {
        var input=request();var fixture=CanonicalFundingFixture.create(root.resolve("bounded-evidence"),input,CanonicalFundingFixture.Variant.CLEAR);
        fixture.withSession(same->{var original=assertInstanceOf(CanonicalFundingPending.Observed.class,fixture.service().read(same,input)).sourceEvidence();
            var summary=new CanonicalFundingPending.SourceEvidence(original.current(),original.source(),original.sessionId(),original.canonicalHead(),original.ledgerSequence(),original.headSha256(),original.bodies(),original.installed(),original.families(),1000000,"e".repeat(64),List.of());
            assertTrue(CanonicalFundingPending.encodeEvidence(summary).length<=CanonicalFundingPending.encodeEvidence(original).length+16,"settled source count/digest must not copy the complete settled receipt list");
            var installed=new java.util.ArrayList<>(original.installed());var first=installed.getFirst();
            for(int i=0;i<4096;i++)installed.add(new ExecutableStepBindings.InstalledStep(new OperationKey("large-actual-inventory-shape-"+i+"-"+"x".repeat(100)),first.kind(),first.guardMode(),first.requiredCapability(),first.implementationSource(),first.decoderSource()));
            var oversized=new CanonicalFundingPending.SourceEvidence(original.current(),original.source(),original.sessionId(),original.canonicalHead(),original.ledgerSequence(),original.headSha256(),original.bodies(),installed,original.families(),original.canonicalActionCount(),original.canonicalActionInventorySha256(),original.unresolvedActions());
            assertThrows(IllegalArgumentException.class,()->CanonicalFundingPending.encodeEvidence(oversized));return null;});
    }
}
