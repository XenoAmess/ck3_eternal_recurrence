package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Production typed profile/binder boundaries. These software DATA objects mint no Root, source, writer or native qualification. */
final class GuardianReconciliationQueriesTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final G2Source SOURCE=new G2Source("synthetic-guardian-machine",NOW.toString(),"1.20.0.4",ref("source",1));
    @TempDir Path directory;
    private static ExactRef ref(String name,int digit){return new ExactRef("synthetic/"+name,1,Integer.toHexString(digit%15+1).repeat(64));}
    private static ObservationIdentity frame(int revision,int publicRevision,int date) {
        var game=new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001")));
        var image=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(19),BigInteger.valueOf(revision),BigInteger.valueOf(date)),
                "native:"+revision,BigInteger.valueOf(publicRevision),"synthetic-guardian-episode");
        return new ObservationIdentity(SOURCE.machineId(),game,image,1);
    }
    private static OrdinaryInitiationIntent intent(long child) {
        return new OrdinaryInitiationIntent("educate_child_interaction",17,Optional.of(new OrdinaryInitiationIntent.Education(child,18,List.of("selected_option"))),Optional.empty());
    }
    private static ActionCommand command(long child) {
        var before=frame(53,55,100);var intent=intent(child);
        var expected=new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION,before,SOURCE,GuardianOutgoingEffects.SCHEMA,
                List.of(new ExpectedInteger(new FieldKey("child_full_id"),BigInteger.valueOf(child)),
                        new ExpectedInteger(new FieldKey("guardian_full_id"),BigInteger.valueOf(18)),new ExpectedBoolean(new FieldKey("outbound_request_effect_observed"),true)));
        return new ActionCommand("synthetic-guardian-action",before,SOURCE,"synthetic-guardian-session",
                new OperationKey(OrdinaryInteractionCodec.INITIATE_STEP),intent.toJson(),expected,
                new JointBudgetSelector.Claims(java.util.Set.of(),java.util.Set.of(),java.util.Set.of(),java.util.Set.of()),NOW.plusSeconds(30));
    }
    private static ActionState.Attempt attempt(ActionCommand command) {
        var guard=new GuardEvidence(command.before(),SOURCE,command.sessionId(),BigInteger.TWO,command.operation(),ref("native-before",2),ref("hello",3),"synthetic-guardian-authority",NOW,NOW.plusSeconds(30));
        return new ActionState.Attempt("guardian-attempt-1",NOW,guard,new NativeRequest(command.operation().value(),OrdinaryInteractionCodec.INITIATE_CAPABILITY,new RawJson(new byte[]{'{','}'})));
    }
    private static ReconciliationIdentity identity(ActionCommand original,int revision,int publicRevision,int date,String requestId) {
        var pending=new ReconciliationIdentity.Pending(original.actionId(),ActionCodec.bodySha256(original),requestId,original.before(),ref("original-receipt",4),ref("original-driver",5));
        var evidence=new ReconciliationIdentity.Evidence(ref("current-native",6),ref("hello",3),ref("heartbeat",7),ref("current-driver",8),ref("current-observation",9),ref("current-source",10));
        return new ReconciliationIdentity(frame(revision,publicRevision,date),SOURCE,original.sessionId(),BigInteger.TWO,pending,evidence,NOW);
    }
    private static PlanningReadRequest request(ActionCommand original,ReconciliationIdentity identity) {
        var controls=new ControlFrame(true,true,true,1,19L,19,"synthetic-guardian-episode",false,null,null,List.of());
        var context=new Context(identity.factual(),SOURCE,original.sessionId(),BigInteger.TWO,Build.CROZIER4,NOW.plusSeconds(30),controls);
        var args=InteractionArguments.body(context);InteractionArguments.ordinary(args,GuardianOutgoingEffects.nativeIntent(OrdinaryInitiationIntent.fromJson(original.arguments())));
        return PlanningReadRequest.newReconciliation(identity,new OperationKey(OrdinaryInteractionCodec.QUERY_STEP),InteractionArguments.app(args),NOW.plusSeconds(30));
    }
    private static PlanningReadRequest request(){var c=command(17);return request(c,identity(c,53,55,100,"guardian-attempt-1"));}
    private ExactRef profile()throws Exception {
        Path path=directory.resolve("guardian-profile.java");byte[] bytes="software profile witness only".getBytes(java.nio.charset.StandardCharsets.UTF_8);Files.write(path,bytes);
        return new ExactRef(path.toString(),bytes.length,ActionCodec.sha256(bytes));
    }
    private static ReadContract<OrdinaryContext> ordinary(String id,String capability,String permission,ReadContract.PermissionMode mode,ReadContract.WireProfile wire) {
        Optional<String> advertised=mode==ReadContract.PermissionMode.ADVERTISED_CAPABILITY?Optional.of(capability):Optional.empty();
        return new ReadContract<>(id,new OperationKey(OrdinaryInteractionCodec.QUERY_STEP),advertised,permission,mode,wire,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,ref("actual-native-producer",11),(r,request)->new NativeRequest(r.operation().value(),advertised,new RawJson(new byte[]{'{','}'})),
                receipt->{throw new IllegalStateException("software ordinary decoder is not invoked by canonical profile");},
                receipt->{throw new IllegalStateException("software ordinary replay is not invoked by canonical profile");});
    }
    private static ReadContract<OrdinaryContext> ordinary(){
        var source=ref("actual-native-producer",11);
        var sources=new InteractionCapabilities.Sources(source,source,source,source,source,source,source,source,source,source);
        var root=new InteractionCapabilities.RootHeirSource(){
            @Override public PlanningReadResult<HeirSubject> read(Context ignored){throw new IllegalStateException("software ordinary test has no Root heir authority");}
            @Override public PlanningReadResult<HeirSubject> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session ignored,Context context){throw new IllegalStateException("software ordinary test has no Root heir authority");}
        };
        return new InteractionCapabilities.Installation(sources,new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of()),root).ordinaryQuery();
    }
    private static GuardianReconciliationQueries.CanonicalAdmission admission(AtomicInteger current,AtomicInteger replay) {
        return new GuardianReconciliationQueries.CanonicalAdmission(){
            @Override public void verifyCurrent(PlanningReadRequest request){current.incrementAndGet();GuardianReconciliationQueries.requireOriginalRequest(request,command(17),attempt(command(17)));}
            @Override public void verifyOriginal(PlanningReadReceipt receipt){replay.incrementAndGet();throw new IllegalStateException("no actual Root archive authority in software test");}
        };
    }
    @Test void canonicalProfileKeepsTheSameNativeProducerAndAdvertisedPurePermission()throws Exception {
        var ordinary=ordinary();var factory=new GuardianReconciliationQueries(ordinary,Build.CROZIER4,profile(),admission(new AtomicInteger(),new AtomicInteger()));
        assertSame(ordinary.sourceRef(),factory.contract().sourceRef());factory.requireOrdinary(ordinary);
        assertTrue(ordinary.hasPureReplay(),"the selected actual ordinary production factory supplies its explicit original replay");
        assertEquals(GuardianReconciliationQueries.CONTRACT_ID,factory.contract().contractId());assertTrue(factory.contract().hasPureReplay());
        assertEquals(ReadContract.GuardMode.RECONCILIATION_OBSERVATION,factory.contract().guardMode());
        assertEquals(ordinary.requiredCapability(),factory.contract().requiredCapability());assertEquals(ordinary.permissionKey(),factory.contract().permissionKey());
        assertThrows(IllegalArgumentException.class,()->factory.requireOrdinary(ordinary()));
    }
    @Test void actualCanonicalPreparationUsesOnlyItsCurrentCallbackAndOriginalNativeFieldProducer()throws Exception {
        var current=new AtomicInteger();var replay=new AtomicInteger();var factory=new GuardianReconciliationQueries(ordinary(),Build.CROZIER4,profile(),admission(current,replay));
        var request=request();var prepared=factory.contract().prepare(request,"independent-guardian-read");
        assertEquals(1,current.get());assertEquals(0,replay.get());assertEquals(OrdinaryInteractionCodec.QUERY_STEP,prepared.step());
        assertEquals(OrdinaryInteractionCodec.request(InteractionArguments.context(request),GuardianOutgoingEffects.nativeIntent(intent(17)),false),prepared.additionalFields());
        assertTrue(prepared.preparationEvidence().isEmpty());
    }
    @Test void closedArgumentAndCommandSerializationPreserveTheOriginalEducationIntent() {
        var command=command(0x7E000001L);var decoded=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));assertEquals(command,decoded);
        var request=request(decoded,identity(decoded,53,55,100,"guardian-attempt-1"));
        GuardianReconciliationQueries.requireOriginalRequest(request,decoded,attempt(decoded));
        assertEquals(InteractionArguments.ordinary(InteractionArguments.parseApp(request.arguments())),GuardianOutgoingEffects.nativeIntent(intent(0x7E000001L)));
    }
    @Test void anotherOriginalPairBodyOrRequestCannotBorrowGuardianReadPermission() {
        var c=command(17);var request=request();
        assertThrows(IllegalArgumentException.class,()->GuardianReconciliationQueries.requireOriginalRequest(request,command(18),attempt(command(18))));
        var wrong=request(c,identity(c,53,55,100,"another-original"));
        assertThrows(IllegalArgumentException.class,()->GuardianReconciliationQueries.requireOriginalRequest(wrong,c,attempt(c)));
    }
    @Test void sameSemDataIsAllowedButAnotherDayOrRegressedNativeFrameIsNotAnOriginalSend() {
        var c=command(17);GuardianReconciliationQueries.requireOriginalRequest(request(),c,attempt(c));
        for(var identity:List.of(identity(c,53,55,101,"guardian-attempt-1"),identity(c,52,55,100,"guardian-attempt-1"),identity(c,53,54,100,"guardian-attempt-1")))
            assertThrows(IllegalArgumentException.class,()->GuardianReconciliationQueries.requireOriginalRequest(request(c,identity),c,attempt(c)));
    }
    @Test void unknownArgumentsAliasesAndScalarTypesAreRefusedBeforeCurrentAdmission()throws Exception {
        var calls=new AtomicInteger();var factory=new GuardianReconciliationQueries(ordinary(),Build.CROZIER4,profile(),admission(calls,new AtomicInteger()));
        var request=request();var body=InteractionArguments.parseApp(request.arguments());
        for(var changed:List.of(body.deepCopy().put("guardian_history",true),body.deepCopy().put("recipient_id",true),body.deepCopy().put("recipient_id",17.0))){
            var invalid=PlanningReadRequest.newReconciliation(request.origin().requireReconciliation(),request.operation(),InteractionArguments.app(changed),request.deadline());
            assertThrows(IllegalArgumentException.class,()->factory.contract().prepare(invalid,"independent-guardian-read"));
        }
        assertEquals(0,calls.get());
    }
    @Test void changedProfileWitnessRefusesBeforeAnyCurrentOrArchiveCallback()throws Exception {
        var calls=new AtomicInteger();var replay=new AtomicInteger();var source=profile();
        var factory=new GuardianReconciliationQueries(ordinary(),Build.CROZIER4,source,admission(calls,replay));
        Files.writeString(Path.of(source.path()),"changed-source");
        assertThrows(IllegalArgumentException.class,()->factory.contract().prepare(request(),"independent-guardian-read"));assertEquals(0,calls.get());assertEquals(0,replay.get());
    }
    @Test void ordinaryGameplayCannotAcquireCanonicalGuardianReadPermission()throws Exception {
        var calls=new AtomicInteger();var factory=new GuardianReconciliationQueries(ordinary(),Build.CROZIER4,profile(),admission(calls,new AtomicInteger()));var c=command(17);
        var actual=request();var gameplay=new PlanningReadRequest(c.before(),SOURCE,c.sessionId(),actual.operation(),actual.arguments(),c.deadline());
        assertThrows(IllegalArgumentException.class,()->factory.contract().prepare(gameplay,"independent-guardian-read"));assertEquals(0,calls.get());
    }
    @Test void foreignQueryProfilePermissionOrWireCannotBeInstalledAsGuardianSource()throws Exception {
        var source=profile();var admission=admission(new AtomicInteger(),new AtomicInteger());
        for(var wrong:List.of(ordinary("foreign",OrdinaryInteractionCodec.QUERY_CAPABILITY,OrdinaryInteractionCodec.QUERY_CAPABILITY,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP),
                ordinary("interactions:ordinary-query","game.query.foreign",OrdinaryInteractionCodec.QUERY_CAPABILITY,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP),
                ordinary("interactions:ordinary-query",OrdinaryInteractionCodec.QUERY_CAPABILITY,"foreign",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)))
            assertThrows(IllegalArgumentException.class,()->new GuardianReconciliationQueries(wrong,Build.CROZIER4,source,admission));
        assertThrows(IllegalArgumentException.class,()->new GuardianReconciliationQueries(ordinary(),Build.CROZIER3,source,admission));
    }
}

