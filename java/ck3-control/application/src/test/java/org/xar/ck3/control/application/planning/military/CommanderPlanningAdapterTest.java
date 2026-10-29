package org.xar.ck3.control.application.planning.military;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.commander.CommanderQuality;
import static org.junit.jupiter.api.Assertions.*;

/** Uses the retained real producer packets; mutations below are explicit negative test vectors. */
final class CommanderPlanningAdapterTest {
    private static final ExactRef REF = new ExactRef("unit-test-only-source", 1, "a".repeat(64));
    private static final Instant NOW = Instant.parse("2026-10-23T15:00:00Z");
    private static final int ARMY = 83886367;
    private static final int CHARACTER = 30001;

    @Test void realProducerQueryCollectorAndFormalContinuationSelectOneCommand() throws IOException {
        var request = request("absent-role");
        var collector = new CommanderObservationCollector(request, REF);
        var port = new Reads(request, packet("absent-role"));
        var policy = new CommanderQualityPolicy(REF, actual -> collector, port, CommanderPlanningAdapterTest::command);
        var decision = policy.evaluate(request, baseline());
        var replace = assertInstanceOf(OrdinaryPolicy.Replace.class, decision);
        assertEquals(1, port.calls.get());
        var selected = replace.draft().command().orElseThrow();
        assertEquals("assign-army-commander-v1-army-" + ARMY + "-to-character-" + CHARACTER, selected.operation().value());
        assertEquals(request.before(), selected.expected().before());
        assertEquals(request.source(), selected.expected().source());
        assertEquals(new OpportunityJson.DecimalValue("1.25"), replace.draft().detail()
                .members().get("opaque_decimal"));
        assertEquals(1, collector.registeredContracts().size());
        assertSame(collector.registeredContracts().get(0), port.lastContract);
        assertEquals(Set.of(BigInteger.valueOf(ARMY)), selected.claims().armyIds());
    }

    @Test void currentObservedQualityAndUnavailableInputRetainOriginalAction() throws IOException {
        var request = request("legacy-quality-missing");
        var collector = new CommanderObservationCollector(request, REF);
        var port = new Reads(request, packet("legacy-quality-missing"));
        var policy = new CommanderQualityPolicy(REF, actual -> collector, port, CommanderPlanningAdapterTest::command);
        var annotate = assertInstanceOf(OrdinaryPolicy.Annotate.class, policy.evaluate(request, baseline()));
        assertEquals(baseline().command(), annotate.retained().command());
        assertEquals("native_war_counterpolicy_hold", annotate.retained().phase());
        assertEquals(1, port.calls.get());
        PlanningReadPort unavailable = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest read) {
                return new PlanningReadResult.Unavailable<>("actual native read unavailable", Optional.empty());
            }
        };
        var missing = new CommanderQualityPolicy(REF, actual -> collector, unavailable, CommanderPlanningAdapterTest::command);
        assertInstanceOf(OrdinaryPolicy.Annotate.class, missing.evaluate(request, baseline()));
    }
    @Test void oneLongLivedPolicyRebuildsTheExactCollectorCatalogForEveryActualCapture() throws IOException {
        PlanningRequest first=request("absent-role");var old=first.observations();
        var before=new ProposalLifecycle.ObservationIdentity(first.before().machineId(),first.before().game(),
                new ProposalFrame(first.before().frame().identity(),first.before().frame().snapshotId(),BigInteger.valueOf(5),first.before().frame().episodeRunId()),1);
        var second=new PlanningRequest(before,first.source(),first.sessionId(),first.deadline(),new PlanningObservation(old.snapshot().with("revision",integer(5)),old.history(),old.actionSteps(),old.bridgeCapabilities(),old.battleSpeedReadiness(),old.actionFacts(),old.campaignGoal(),old.crossRunPlan(),old.initialLifestyleFocusRequired()));
        Map<ProposalLifecycle.ObservationIdentity,Reads> installed=new LinkedHashMap<>();AtomicInteger captures=new AtomicInteger();
        CommanderQualityPolicy.CollectorFactory factory=actual->{captures.incrementAndGet();try{installed.put(actual.before(),new Reads(actual,packet("absent-role")));}catch(IOException failure){throw new IllegalStateException(failure);}return new CommanderObservationCollector(actual,REF);};
        PlanningReadPort port=new PlanningReadPort(){@Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest read){return installed.get(read.before()).read(contract,read);}};
        var policy=new CommanderQualityPolicy(REF,factory,port,CommanderPlanningAdapterTest::command);
        assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluate(first,baseline()));assertInstanceOf(OrdinaryPolicy.Replace.class,policy.evaluate(second,baseline()));
        assertEquals(2,captures.get());assertEquals(2,installed.size());assertEquals(1,installed.get(first.before()).calls.get());assertEquals(1,installed.get(second.before()).calls.get());
        assertNotSame(installed.get(first.before()).lastContract,installed.get(second.before()).lastContract);
    }

    @Test void decimalBooleanDuplicateAndWrongSourceTokensNeverBecomeIntegerIds() throws IOException {
        var request = request("absent-role");
        var collector = new CommanderObservationCollector(request, REF);
        var good = packet("absent-role");
        var candidates = object(good.get("army_commander_candidates"));
        for (OpportunityJson.Value bad : List.of(new OpportunityJson.DecimalValue("83886367.0"),
                new OpportunityJson.DecimalValue("83886367e0"), new OpportunityJson.Bool(true))) {
            var mutated = good.with("army_commander_candidates", candidates.with("army_id", bad));
            assertThrows(IllegalArgumentException.class, () -> collector.collect(new Reads(request, mutated), request, ARMY));
        }
        var wrong = good.with("snapshot_revision", integer(12));
        assertThrows(IllegalArgumentException.class, () -> collector.collect(new Reads(request, wrong), request, ARMY));
        byte[] duplicate = ("{\"step\":\"duplicate\"," + new String(OpportunityJson.encode(good), StandardCharsets.UTF_8).substring(1))
                .getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> collector.collect(new Reads(request, duplicate), request, ARMY));
    }

    @Test void sameFrameGenerationAndSubjectGuardRemainIndependentOfTypedValue() throws IOException {
        var request = request("absent-role");
        var collector = new CommanderObservationCollector(request, REF);
        Reads drift = new Reads(request, packet("absent-role")); drift.afterGeneration = BigInteger.TWO;
        assertThrows(IllegalArgumentException.class, () -> collector.collect(drift, request, ARMY));
        Reads unpaused = new Reads(request, packet("absent-role")); unpaused.afterPaused = false;
        assertThrows(IllegalArgumentException.class, () -> collector.collect(unpaused, request, ARMY));
        Reads digest = new Reads(request, packet("absent-role")); digest.afterDigest = "b".repeat(64);
        assertThrows(IllegalArgumentException.class, () -> collector.collect(digest, request, ARMY));
        assertInstanceOf(PlanningReadResult.Unavailable.class, collector.collect(digest, request, ARMY + 1));
    }

    @Test void actualAssignmentAckRequiresIndependentCurrentCommanderObservation() throws IOException {
        var request = request("absent-role"); var command = assignment(request);
        var outcome = assigned(command, "submitted");
        AtomicInteger independent = new AtomicInteger();
        var observer = new CommanderAssignmentPostcondition(original -> new CommanderAssignmentPostcondition.Current(request),
                (now, army) -> { independent.incrementAndGet(); return currentRead(request, CHARACTER, "independent-read"); }, archive());
        var effect = assertInstanceOf(ActionPorts.EffectObserved.class, observer.observe(command, attempt(command), outcome));
        assertEquals(1, independent.get());
        assertEquals("independent-read", assertInstanceOf(ObservationProvenance.Query.class, effect.observation().provenance()).requestId());
        assertEquals(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("verified"), true),
                effect.observation().actual().get(0));
        var noFrame = new CommanderAssignmentPostcondition(original -> new CommanderAssignmentPostcondition.FrameUnavailable("frame unavailable"),
                (now, army) -> { throw new AssertionError("must not read without a current frame"); }, archive());
        assertInstanceOf(ActionPorts.Pending.class, noFrame.observe(command, attempt(command), outcome));
    }

    @Test void unknownSubmissionCannotBorrowOrdinaryReadiness() throws IOException {
        var request = request("absent-role"); var command = assignment(request);
        AtomicInteger reads = new AtomicInteger();
        var observer = new CommanderAssignmentPostcondition(original -> new CommanderAssignmentPostcondition.Current(request),
                (now, army) -> { reads.incrementAndGet(); return currentRead(request, CHARACTER, "fresh-read"); }, archive());
        var unknown = new NativeActionPort.Unknown("write-request", "write result unknown", new byte[]{1}, Optional.empty());
        assertInstanceOf(ActionPorts.Pending.class, observer.observe(command, attempt(command), unknown));
        assertEquals(0, reads.get());
        var mismatch = new CommanderAssignmentPostcondition(original -> new CommanderAssignmentPostcondition.Current(request),
                (now, army) -> currentRead(request, CHARACTER + 1, "other-read"), archive());
        assertInstanceOf(ActionPorts.Pending.class,mismatch.observe(command, attempt(command), unknown));
    }

    @Test void sameWriteRequestCannotMasqueradeAsIndependentReadAndAckAloneCannotVerify() throws IOException {
        var request = request("absent-role"); var command = assignment(request);
        var observer = new CommanderAssignmentPostcondition(original -> new CommanderAssignmentPostcondition.Current(request),
                (now, army) -> currentRead(request, CHARACTER, "write-request"), archive());
        assertInstanceOf(ActionPorts.Pending.class, observer.observe(command, attempt(command), assigned(command, "submitted")));
        var ackOnly = new NativeActionPort.AckReceived("write-request", true, Optional.empty(), new RawJson(new byte[]{'{','}'}), new byte[]{1});
        assertInstanceOf(ActionPorts.Pending.class, observer.observe(command, attempt(command), ackOnly));
    }

    @Test void assignmentExpectedDomainAndNativeZeroIdentityAreCheckedBeforePrepare() throws IOException {
        var request = request("absent-role");
        assertThrows(IllegalArgumentException.class,()->new CommanderAssignmentPostcondition.Arguments(BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO,BigInteger.ONE,BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class,()->new CommanderAssignmentPostcondition.Arguments(BigInteger.ZERO,BigInteger.ZERO,BigInteger.ONE,BigInteger.ZERO,BigInteger.ZERO));
        var args = arguments(request).with("commander_character_id", integer(0));
        var expected = CommanderAssignmentPostcondition.expected(request, args);
        assertTrue(CommanderAssignmentPostcondition.claims(args).characterIds().isEmpty());
        assertEquals(Set.of("commander-character:0"), CommanderAssignmentPostcondition.claims(args).commitmentKeys());
        var good = new ActionCommand("zero-id", request.before(), request.source(), request.sessionId(),
                new OperationKey("assign-army-commander-v1-army-" + ARMY + "-to-character-0"), args, expected,
                CommanderAssignmentPostcondition.claims(args), request.deadline());
        assertEquals(good.operation().value(), CommanderAssignmentPostcondition.prepare(good).step());
        var badExpected = new ProposalLifecycle.ExpectedPostcondition(1, request.before(), request.source(),
                CommanderAssignmentPostcondition.OBSERVER_SCHEMA,
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("verified"), false)));
        var bad = new ActionCommand("wrong-expected", good.before(), good.source(), good.sessionId(), good.operation(),
                args, badExpected, good.claims(), good.deadline());
        assertThrows(IllegalArgumentException.class, () -> CommanderAssignmentPostcondition.prepare(bad));
        for (var token : List.<OpportunityJson.Value>of(new OpportunityJson.DecimalValue("0.0"), new OpportunityJson.Bool(false)))
            assertThrows(IllegalArgumentException.class, () -> CommanderAssignmentPostcondition.arguments(args.with("commander_character_id", token)));
    }
    @Test void availableAckWithoutNativeOwnerIdentityStaysPendingInsteadOfThrowingNullPointer() throws IOException {
        var request=request("absent-role");var command=assignment(request);var original=assigned(command,"already_assigned");
        var root=object(OpportunityJson.parse(original.originalResultToken().orElseThrow().bytes()));var inner=object(root.get("army_commander_assignment")).with("native_carmy_id",OpportunityJson.Nil.INSTANCE);
        var malformed=ack("write-request",OpportunityJson.encode(root.with("army_commander_assignment",inner)));
        var observer=new CommanderAssignmentPostcondition(c->new CommanderAssignmentPostcondition.Current(request),(now,army)->{throw new AssertionError("malformed assignment must not start an independent read");},archive());
        assertInstanceOf(ActionPorts.Pending.class,observer.observe(command,attempt(command),malformed));
    }
    @Test void sameInstalledCommanderFamilyServesALaterDateWithoutRegisteringTheOperationTwice() throws IOException {
        var first=request("absent-role");var observed=first.observations();var before=first.before();var old=before.frame();
        BigInteger date=old.identity().dateRaw().add(BigInteger.valueOf(24)),nativeRevision=old.identity().nativeRevision().add(BigInteger.ONE),revision=old.revision().add(BigInteger.ONE);
        var fresh=new ProposalLifecycle.ObservationIdentity(before.machineId(),before.game(),new ProposalFrame(new Frame(old.identity().player(),nativeRevision,date),"retained-native:12",revision,old.episodeRunId()),before.observationVersion());
        var snapshot=observed.snapshot().with("snapshot_id",text("retained-native:12")).with("revision",new OpportunityJson.IntegerValue(revision)).with("native_revision",new OpportunityJson.IntegerValue(nativeRevision)).with("date_raw",new OpportunityJson.IntegerValue(date));
        var second=new PlanningRequest(fresh,first.source(),first.sessionId(),first.deadline(),new PlanningObservation(snapshot,observed.history(),observed.actionSteps(),observed.bridgeCapabilities(),observed.battleSpeedReadiness(),observed.actionFacts(),observed.campaignGoal(),observed.crossRunPlan(),observed.initialLifestyleFocusRequired()));
        var observer=new CommanderAssignmentPostcondition(c->new CommanderAssignmentPostcondition.FrameUnavailable("not used while registering"),(now,army)->{throw new AssertionError();},archive());
        var binding=new CommanderBindings(new CommanderBindings.Sources(REF,REF,REF,REF,REF,REF),new Reads(first,packet("absent-role")),observer,(basis,archive)->{throw new AssertionError("family registration cannot read archived frames");});
        var reads=new RootReadContractCatalog(List.of(),List.of(binding.readFamily()));var catalog=RootExecutableBindings.freeze(List.of(),reads,List.of(),List.of(),List.of(binding.actionFamily()),8);
        var a=CommanderAssignmentPostcondition.arguments(arguments(first));var b=CommanderAssignmentPostcondition.arguments(arguments(second));
        assertEquals(binding.assignment(first,a,catalog,"first-date").operation(),binding.assignment(second,b,catalog,"later-date").operation());
        assertEquals(1,catalog.actionBindings().size());assertEquals(1,catalog.archivedBindings().size());catalog.requireCompleteArchiveCoverage();
    }
    @Test void registeredTargetFamilyCannotAdoptTheRealUntargetedProducerReceipt()throws IOException {
        var request=request("absent-role");var reads=new Reads(request,packet("absent-role"));
        var observer=new CommanderAssignmentPostcondition(c->new CommanderAssignmentPostcondition.FrameUnavailable("registration only"),(now,army)->{throw new AssertionError();},archive());
        var binding=new CommanderBindings(new CommanderBindings.Sources(REF,REF,REF,REF,REF,REF),reads,observer,(basis,original)->{throw new AssertionError();});
        var catalog=new RootReadContractCatalog(List.of(),binding.readFamilies());
        var base=assertInstanceOf(PlanningReadResult.Known.class,binding.collector(request,catalog).collect(reads,request,ARMY));
        var normalized=assertInstanceOf(CommanderObservationCollector.Observation.class,base.value());
        assertEquals(normalized,reads.lastContract.replay(base.receipt()));
        var input=CommanderObservationCollector.ObservedInput.of(request);var caps=new java.util.HashSet<>(input.capabilities());caps.add(CommanderObservationCollector.TARGET_CAPABILITY);
        var targeted=new CommanderObservationCollector.ObservedInput(input.before(),input.source(),input.sessionId(),input.deadline(),input.snapshot(),caps);
        var targetCollector=binding.collector(targeted,Optional.of(12004),catalog);
        assertEquals(3,binding.readFamilies().size());
        assertEquals("query-army-commander-candidates-v1-for-army-"+ARMY+"-at-province-12004",targetCollector.registeredContracts().getFirst().operation().value());
        assertThrows(IllegalArgumentException.class,()->targetCollector.collect(reads,targeted,ARMY),"a real untargeted receipt cannot qualify a target-at-province query");
    }
    @Test void originalServiceDerivedTargetPacketReachesTheSameRegisteredFamilyAndPureReplay()throws Exception {
        var corpus=CommanderTargetOriginalProducerTest.originalCorpus();int checked=0;
        for(var chosen:corpus.get("good")) {if(!chosen.get("target").isIntegralNumber())continue;checked++;
        var wrapper=chosen.get("wrapper");var original=org.xar.ck3.control.application.driver.DriverJson.object(org.xar.ck3.control.wave2.military.commander.ArmyCommanderCandidatesCodec.encodeJson(wrapper.get("snapshot_before")),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
        var snapshot=original.with("episode_run_id",text("derived-target-episode")).with("map_ready",new OpportunityJson.Bool(true));
        BigInteger player=OpportunityJson.integer(object(snapshot.get("played_character")).get("character_id"),"actual fixture actor");
        var before=new ProposalLifecycle.ObservationIdentity("unit-machine",new GameGeneration(10,new PythonOnlyUInt64(BigInteger.ONE)),new ProposalFrame(new Frame(player,OpportunityJson.integer(snapshot.get("native_revision"),"native revision"),OpportunityJson.integer(snapshot.get("date_raw"),"date")),OpportunityJson.text(snapshot.get("snapshot_id"),"snapshot ID"),OpportunityJson.integer(snapshot.get("revision"),"revision"),"derived-target-episode"),1);
        var caps=new java.util.HashSet<String>();wrapper.get("bridge_capabilities").forEach(value->caps.add(value.textValue()));
        var request=new PlanningRequest(before,new G2Source("unit-machine",NOW.toString(),"derived-original-target-test",REF),"unit-session",NOW.plusSeconds(60),new PlanningObservation(snapshot,List.of(),Set.of(),caps,Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        int army=wrapper.get("army_id").intValue(),target=chosen.get("target").intValue();
        var nativeResult=org.xar.ck3.control.application.driver.DriverJson.object(org.xar.ck3.control.wave2.military.commander.ArmyCommanderCandidatesCodec.encodeJson(wrapper.get("native_result")),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);var reads=new Reads(request,nativeResult);
        var observer=new CommanderAssignmentPostcondition(c->new CommanderAssignmentPostcondition.FrameUnavailable("read-only fixture"),(now,unit)->{throw new AssertionError();},archive());
        var binding=new CommanderBindings(new CommanderBindings.Sources(REF,REF,REF,REF,REF,REF),reads,observer,(basis,archive)->{throw new AssertionError();});var catalog=new RootReadContractCatalog(List.of(),binding.readFamilies());
        var collector=binding.collector(CommanderObservationCollector.ObservedInput.of(request),Optional.of(target),catalog);
        var result=assertInstanceOf(PlanningReadResult.Known.class,collector.collect(reads,request,army));var value=assertInstanceOf(CommanderObservationCollector.Observation.class,result.value());
        assertEquals(chosen.get("normalized"),value.observed().normalizedJson());assertEquals(value,reads.lastContract.replay(result.receipt()));assertEquals(1,reads.calls.get());
        }
        assertTrue(checked>0,"original producer target-derived fixtures are mandatory; they do not prove live target availability");
    }

    @Test void canonicalUnknownUsesSeparateRegisteredObservationOriginAndOriginalNativeNormalizer() throws IOException {
        var request=request("absent-role");var command=assignment(request);var attempt=attempt(command);
        var unknown=new NativeActionPort.Unknown(attempt.requestId(),"actual result is unknown",new byte[]{1},Optional.empty());
        var identity=reconciliationIdentity(command,attempt,unknown);var input=new CommanderReconciliationCollector.Input(identity,request.observations().snapshot());
        var current=object(packet("absent-role").get("army_commander_candidates")).with("current_commander",empty().with("status",text("available"))
                .with("character_id",integer(CHARACTER)).with("unavailable_reason",OpportunityJson.Nil.INSTANCE));
        var actualReads=new ReconReads(identity,packet("absent-role").with("army_commander_candidates",current));
        var unused=new CommanderAssignmentPostcondition(c->new CommanderAssignmentPostcondition.FrameUnavailable("registration only"),(now,army)->{throw new AssertionError();},archive());
        var bindings=new CommanderBindings(new CommanderBindings.Sources(REF,REF,REF,REF,REF,REF),actualReads,unused,(basis,archive)->{throw new AssertionError();});
        var catalog=new RootReadContractCatalog(List.of(),bindings.readFamilies());
        var observer=new CommanderAssignmentPostcondition(c->new CommanderAssignmentPostcondition.ReconciliationCurrent(input,NOW.plusSeconds(120)),
                (now,army)->{throw new AssertionError("UNKNOWN cannot use ordinary collector");},archive(),
                (now,army,deadline)->bindings.readReconciliation(now,army,deadline,catalog,null));
        var applied=assertInstanceOf(ActionPorts.EffectObserved.class,observer.observe(command,attempt,unknown));
        assertEquals(1,actualReads.calls);assertEquals(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("verified"),true),applied.observation().actual().getFirst());
        assertEquals(ReadContract.GuardMode.RECONCILIATION_OBSERVATION,actualReads.last.guardMode());
        assertThrows(IllegalStateException.class,()->actualReads.receipt.request().before());
        assertEquals(NOW.plusSeconds(120),actualReads.receipt.request().deadline());
        assertEquals(actualReads.last.decode(actualReads.receipt),actualReads.last.replay(actualReads.receipt));
        var selected=new CommanderReconciliationCollector.Selection(input,ARMY);
        assertThrows(IllegalArgumentException.class,()->actualReads.last.prepare(new PlanningReadRequest(request.before(),request.source(),request.sessionId(),
                CommanderReconciliationCollector.operation(ARMY),CommanderReconciliationCollector.arguments(ARMY),request.deadline()),"wrong-ordinary"));
        assertThrows(IllegalArgumentException.class,()->CommanderReconciliationCollector.admit(selected,assertInstanceOf(PlanningReadResult.Known.class,currentRead(request,CHARACTER,"ordinary-only")).receipt()));
    }
    @Test void reconciliationRejectsUnrelatedPendingBodyAndNeverStartsItsRead()throws IOException {
        var request=request("absent-role");var command=assignment(request);var attempt=attempt(command);
        var unknown=new NativeActionPort.Unknown(attempt.requestId(),"unknown",new byte[]{1},Optional.empty());
        var actual=reconciliationIdentity(command,attempt,unknown);var p=actual.pending();
        var other=new ReconciliationIdentity(actual.factual(),actual.source(),actual.sessionId(),actual.connectionGeneration(),
                new ReconciliationIdentity.Pending("other-action",p.bodySha256(),p.requestId(),p.originalBefore(),p.originalReceipt(),p.originalBeforeDriver()),actual.evidence(),actual.observedAt());
        var input=new CommanderReconciliationCollector.Input(other,request.observations().snapshot());
        var observer=new CommanderAssignmentPostcondition(c->new CommanderAssignmentPostcondition.ReconciliationCurrent(input,NOW.plusSeconds(120)),
                (now,army)->{throw new AssertionError();},archive(),(now,army,deadline)->{throw new AssertionError("unrelated pending body cannot query");});
        assertInstanceOf(ActionPorts.Pending.class,observer.observe(command,attempt,unknown));
        assertThrows(IllegalArgumentException.class,()->new CommanderReconciliationCollector.Input(actual,request.observations().snapshot().with("date_raw",integer(1))));
        assertThrows(IllegalArgumentException.class,()->new CommanderReconciliationCollector.Selection(input,ARMY+1));
    }
    /** Explicit domain fixture DATA; Root's independent scope tests prove physical/canonical authority. */
    private static ReconciliationIdentity reconciliationIdentity(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.Unknown unknown) {
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.of(attempt),Optional.of(unknown),"unknown",List.of()));
        var evidence=new ReconciliationIdentity.Evidence(role("native"),role("hello"),role("heartbeat"),role("manifest"),role("driver"),role("qualification"));
        return ReconciliationIdentity.fromCanonical(receipt,command.before(),command.source(),command.sessionId(),BigInteger.ONE,role("pending-receipt"),role("driver"),evidence,NOW.plusSeconds(1));
    }
    private static ExactRef role(String name){return new ExactRef("explicit-unit-"+name,1,"b".repeat(64));}
    private static final class ReconReads implements PlanningReadPort {
        final ReconciliationIdentity identity;final OpportunityJson.Obj packet;int calls;ReadContract<?> last;PlanningReadReceipt receipt;
        ReconReads(ReconciliationIdentity identity,OpportunityJson.Obj packet){this.identity=identity;this.packet=packet;}
        @Override public <T> PlanningReadResult<T> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ReadContract<T> contract,PlanningReadRequest actual){return read(contract,actual);}
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest actual) {
            calls++;last=contract;contract.prepare(actual,"reconciliation-query");
            var guard=new GuardEvidence(new CommandOrigin.Reconciliation(identity),identity.source(),identity.sessionId(),identity.connectionGeneration(),contract.operation(),
                    identity.nativeEvidence(),identity.capabilityEvidence(),"explicit-domain-fixture",NOW.plusSeconds(1),actual.deadline(),identity.supportingEvidence());
            var basis=new PlanningReadGuard(guard,new PlanningReadGuard.Reconciliation(),"c".repeat(64));
            receipt=new PlanningReadReceipt(actual,contract.contractId(),"reconciliation-query",basis,basis,ack("reconciliation-query",org.xar.ck3.control.application.driver.DriverJson.encode(packet)));
            return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,REF);
        }
    }

    private static OrdinaryPolicy.Draft baseline() {
        var detail = empty().with("policy", text("one-life-turn-v1")).with("phase", text("native_war_counterpolicy_hold"))
                .with("reason", text("original military hold")).with("selected_step", OpportunityJson.Nil.INSTANCE)
                .with("opaque_decimal", new OpportunityJson.DecimalValue("1.25"));
        return new OrdinaryPolicy.Draft("one-life-turn-v1", "native_war_counterpolicy_hold", "original military hold",
                OrdinaryPolicy.Kind.ORDINARY, Optional.empty(), OrdinaryPolicy.Purpose.WORLD_ACTION, Optional.empty(), detail);
    }
    private static ActionCommand command(PlanningRequest request, MilitaryPlanningDecision.Select select) {
        return new ActionCommand("unit-commander", request.before(), request.source(), request.sessionId(),
                select.operation(), select.arguments(), CommanderAssignmentPostcondition.expected(request, select.arguments()),
                CommanderAssignmentPostcondition.claims(select.arguments()), request.deadline());
    }
    private static ActionCommand assignment(PlanningRequest request) {
        var args = arguments(request);
        return new ActionCommand("unit-assignment", request.before(), request.source(), request.sessionId(),
                new OperationKey("assign-army-commander-v1-army-" + ARMY + "-to-character-" + CHARACTER), args,
                CommanderAssignmentPostcondition.expected(request, args), CommanderAssignmentPostcondition.claims(args), request.deadline());
    }
    private static OpportunityJson.Obj arguments(PlanningRequest request) {
        return empty().with("army_id", integer(ARMY)).with("commander_character_id", integer(CHARACTER))
                .with("native_carmy_id", integer(50331794)).with("owner_character_id", integer(29829))
                .with("date_raw", new OpportunityJson.IntegerValue(request.before().frame().identity().dateRaw()));
    }
    private static PlanningRequest request(String caseName) throws IOException {
        var original = object(input(caseName).get("snapshot"));
        var snapshot = original.with("map_ready", new OpportunityJson.Bool(true)).with("episode_run_id", text("unit-episode"))
                .with("played_character", empty().with("character_id", integer(29829))).with("active_wars", new OpportunityJson.Arr(List.of()));
        var identity = new ProposalLifecycle.ObservationIdentity("unit-machine", new GameGeneration(10, new PythonOnlyUInt64(BigInteger.ONE)),
                new ProposalFrame(new Frame(BigInteger.valueOf(29829), BigInteger.valueOf(11), BigInteger.valueOf(53288448)),
                        "retained-native:11", BigInteger.valueOf(4), "unit-episode"), 1);
        return new PlanningRequest(identity, new G2Source("unit-machine", NOW.toString(), "unit-build", REF), "unit-session",
                NOW.plusSeconds(60), new PlanningObservation(snapshot, List.of(), Set.of(),
                        Set.of(CommanderQuality.QUERY_CAPABILITY, CommanderQuality.ASSIGN_CAPABILITY), Optional.empty(),
                        List.of(), Optional.empty(), Optional.empty(), false));
    }
    private static OpportunityJson.Obj input(String name) throws IOException {
        try (InputStream stream = CommanderPlanningAdapterTest.class.getResourceAsStream("/commander/legacy-golden.json")) {
            assertNotNull(stream, "requires the unchanged actual legacy producer resource");
            var golden = object(OpportunityJson.parse(stream.readAllBytes()));
            for (var item : OpportunityJson.array(golden.get("cases"), "cases")) {
                var row = object(item);
                if (new OpportunityJson.Text(name).equals(row.get("name"))) return object(row.get("input"));
            }
            throw new AssertionError("real producer case missing: " + name);
        }
    }
    private static OpportunityJson.Obj packet(String name) throws IOException {
        var input = input(name);
        return empty().with("step", text("query-army-commander-candidates-v1-for-army-" + ARMY))
                .with("accepted", new OpportunityJson.Bool(true)).with("status", text("completed"))
                .with("read_only", new OpportunityJson.Bool(true)).with("query_sequence", input.get("query_sequence"))
                .with("snapshot_revision", integer(11)).with("date_raw", integer(53288448))
                .with("army_commander_candidates", input.get("candidates"));
    }
    private static PlanningReadResult<CommanderObservationCollector.Observation> currentRead(PlanningRequest now, int current, String id) {
        try {
            var packet = packet("absent-role");
            var candidates = object(packet.get("army_commander_candidates")).with("current_commander",
                    empty().with("status", text("available")).with("character_id", integer(current)).with("unavailable_reason", OpportunityJson.Nil.INSTANCE));
            var reads = new Reads(now, packet.with("army_commander_candidates", candidates)); reads.requestId = id;
            return new CommanderObservationCollector(now, REF).collect(reads, now, ARMY);
        } catch (IOException error) { throw new IllegalStateException(error); }
    }
    private static NativeActionPort.AckReceived assigned(ActionCommand command, String status) {
        var value = empty().with("schema", text("ck3_12004_army_commander_assignment_v1")).with("status", text(status))
                .with("army_id", integer(ARMY)).with("requested_commander_character_id", integer(CHARACTER))
                .with("native_carmy_id", integer(50331794)).with("owner_character_id", integer(29829))
                .with("prior_commander_character_id", OpportunityJson.Nil.INSTANCE)
                .with("final_eligibility_observable", new OpportunityJson.Bool(true)).with("can_assign", new OpportunityJson.Bool(true))
                .with("native_command_validation_observable", new OpportunityJson.Bool(true)).with("native_command_valid", new OpportunityJson.Bool(true))
                .with("command_submitted", new OpportunityJson.Bool(status.equals("submitted")))
                .with("verification_pending", new OpportunityJson.Bool(status.equals("submitted"))).with("unavailable_reason", OpportunityJson.Nil.INSTANCE);
        var root = empty().with("step", text(command.operation().value())).with("accepted", new OpportunityJson.Bool(true))
                .with("snapshot_revision", integer(11)).with("date_raw", integer(53288448)).with("army_commander_assignment", value);
        return ack("write-request", OpportunityJson.encode(root));
    }
    private static GuardEvidence guard(PlanningRequest request, OperationKey operation, BigInteger generation) {
        return new GuardEvidence(request.before(), request.source(), request.sessionId(), generation, operation, REF, REF,
                "unit-guard", NOW, NOW.plusSeconds(60));
    }
    private static ActionState.Attempt attempt(ActionCommand command) {
        return new ActionState.Attempt("write-request", NOW, new GuardEvidence(command.before(), command.source(), command.sessionId(),
                BigInteger.ONE, command.operation(), REF, REF, "unit-guard", NOW, NOW.plusSeconds(60)),
                CommanderAssignmentPostcondition.prepare(command));
    }
    private static NativeActionPort.AckReceived ack(String id, byte[] result) {
        return new NativeActionPort.AckReceived(id, true, Optional.of(new RawJson(result)), new RawJson(new byte[]{'{','}'}), new byte[]{1});
    }
    private static ActionPorts.OutcomeArchive archive() {
        return new ActionPorts.OutcomeArchive() {
            @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original) { return REF; }
            @Override public NativeActionPort.DispatchOutcome load(ExactRef ref) { throw new UnsupportedOperationException(); }
            @Override public ExactRef preserveRequest(NativeRequest original) { return REF; }
            @Override public NativeRequest loadRequest(ExactRef ref) { throw new UnsupportedOperationException(); }
            @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) { return REF; }
            @Override public ExactRef requestReferenceOf(NativeRequest original) { throw new UnsupportedOperationException(); }
            @Override public ExactRef preserveRead(PlanningReadReceipt original) { return REF; }
            @Override public PlanningReadReceipt loadRead(ExactRef original) { throw new UnsupportedOperationException(); }
            @Override public ExactRef readReferenceOf(PlanningReadReceipt original) { return REF; }
            @Override public ExactRef preserveRecord(ActionRecord original) { throw new UnsupportedOperationException(); }
            @Override public ActionRecord loadRecord(ExactRef original) { throw new UnsupportedOperationException(); }
            @Override public ExactRef recordReferenceOf(ActionRecord original) { throw new UnsupportedOperationException(); }
            @Override public ExactRef preserveReceipt(ActionReceipt original) { throw new UnsupportedOperationException(); }
            @Override public ActionReceipt loadReceipt(ExactRef original) { throw new UnsupportedOperationException(); }
            @Override public ExactRef receiptReferenceOf(ActionReceipt original) { throw new UnsupportedOperationException(); }
            @Override public ExactRef preserveMaterial(RawJson original) { throw new UnsupportedOperationException(); }
            @Override public RawJson loadMaterial(ExactRef original) { throw new UnsupportedOperationException(); }
            @Override public ExactRef materialReferenceOf(RawJson original) { throw new UnsupportedOperationException(); }
            @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) { throw new UnsupportedOperationException(); }
            @Override public byte[] loadNativeFrame(ExactRef original) { throw new UnsupportedOperationException(); }
        };
    }
    private static final class Reads implements PlanningReadPort {
        final PlanningRequest request; final byte[] packet; final AtomicInteger calls = new AtomicInteger();
        BigInteger afterGeneration = BigInteger.ONE; boolean afterPaused = true;
        String afterDigest = "a".repeat(64), requestId = "independent-read"; ReadContract<?> lastContract;
        Reads(PlanningRequest request, OpportunityJson.Obj result) { this(request, org.xar.ck3.control.application.driver.DriverJson.encode(result)); }
        Reads(PlanningRequest request, byte[] packet) { this.request = request; this.packet = packet.clone(); }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest read) {
            calls.incrementAndGet(); lastContract = contract; contract.prepare(read, requestId);
            var before = new PlanningReadGuard(guard(request, contract.operation(), BigInteger.ONE), true, true, true, "a".repeat(64));
            var after = new PlanningReadGuard(guard(request, contract.operation(), afterGeneration), afterPaused, true, true, afterDigest);
            var receipt = new PlanningReadReceipt(read, contract.contractId(), requestId, before, after, ack(requestId, packet));
            return new PlanningReadResult.Known<>(contract.decode(receipt), receipt,REF);
        }
    }
    private static OpportunityJson.Obj empty() { return new OpportunityJson.Obj(Map.of()); }
    private static OpportunityJson.Obj object(OpportunityJson.Value value) { return OpportunityJson.object(value, "object"); }
    private static OpportunityJson.Text text(String value) { return new OpportunityJson.Text(value); }
    private static OpportunityJson.IntegerValue integer(long value) { return new OpportunityJson.IntegerValue(BigInteger.valueOf(value)); }
}
