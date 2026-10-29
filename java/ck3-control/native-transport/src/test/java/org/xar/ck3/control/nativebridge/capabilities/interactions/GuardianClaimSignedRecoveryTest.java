package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Actual public command producer and durable claim DATA. No read, submission, Root or Game authority. */
final class GuardianClaimSignedRecoveryTest {
    private static final long ACTOR=-33_554_431L,CHILD=0xFE00_0002L,GUARDIAN=202;
    private static final String MACHINE="synthetic-guardian-claim",BIRTH="133700000000000001";
    private static final ExactRef SOURCE_REF=new ExactRef("synthetic/guardian-source",1,"a".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private record Produced(ActionCommand command,ActionCommand restored,OrdinaryInitiationIntent intent,Request request) { }
    private static final class Producer {
        private int reads,submissions,reconciliations;
        private final Context context;
        private final InteractionCapabilities facade;
        Producer(long actor) {
            var source=new G2Source(MACHINE,NOW.toString(),Build.CROZIER4.version(),SOURCE_REF);
            var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),BigInteger.valueOf(7),BigInteger.valueOf(53146848)),
                    "native:7",BigInteger.valueOf(56),"synthetic-guardian-episode");
            var before=new ObservationIdentity(MACHINE,new GameGeneration(991,new PythonOnlyUInt64(new BigInteger(BIRTH))),frame,1);
            context=new Context(before,source,"synthetic-guardian-session",BigInteger.TWO,Build.CROZIER4,NOW.plusSeconds(30),
                    new ControlFrame(true,true,true,1,19L,actor,"synthetic-guardian-episode",false,null,null,List.of()));
            var refs=new InteractionCapabilities.Sources(SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF);
            var installed=new InteractionCapabilities.Installation(refs,new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of()),new InteractionCapabilities.RootHeirSource(){
                @Override public PlanningReadResult<HeirSubject> read(Context ignored){throw new AssertionError("no heir read");}
                @Override public PlanningReadResult<HeirSubject> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session ignored,Context frameValue){throw new AssertionError("no heir read");}
            });
            facade=new InteractionCapabilities(installed,new PlanningReadPort(){
                @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){reads++;throw new AssertionError("pure command production cannot read");}
            },new ActionCoordinatorPort(){
                @Override public ActionReceipt execute(ActionCommand command){submissions++;throw new AssertionError("pure command production cannot submit");}
                @Override public ActionReceipt reconcile(String actionId){reconciliations++;throw new AssertionError("claim DATA cannot reconcile");}
            });
        }
        Produced prepare(List<String> keys) {
            var education=new EducationIntent(Optional.of(new CharacterId(CHILD)),Optional.of(new CharacterId(GUARDIAN)),
                    Optional.of(keys.stream().map(InteractionKey::new).toList()));
            var request=new OrdinaryRequest(new InteractionKey("educate_child_interaction"),new CharacterId(CHILD),Optional.of(education));
            var expected=new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION,context.before(),context.source(),GuardianOutgoingEffects.SCHEMA,
                    List.of(new ExpectedInteger(new FieldKey("child_full_id"),BigInteger.valueOf(CHILD)),
                            new ExpectedInteger(new FieldKey("guardian_full_id"),BigInteger.valueOf(GUARDIAN)),new ExpectedBoolean(new FieldKey("outbound_request_effect_observed"),true)));
            var action=new ActionContext(context,"synthetic-guardian-action",expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()));
            ActionCommand original=facade.prepareInitiateCharacterInteractionOrdinaryV1(action,request);
            ActionCommand restored=ActionCodec.decodeCommand(ActionCodec.encodeCommand(original));
            OrdinaryInitiationIntent intent=OrdinaryInitiationIntent.fromJson(restored.arguments());
            // The same extraction used by the actual OrdinaryInitiationPreparation, after the public producer/serde.
            var identity=new Identity(restored.before().machineId(),restored.before().game().pid(),restored.before().game().creationFiletime().value().toString(),
                    context.actor().longValueExact(),intent.interactionKey(),intent.recipientId());
            var binding=new Binding(context.before().frame().snapshotId(),context.before().frame().revision().toString(),context.revision().toString(),
                    context.date().toString(),context.connectionGeneration().toString(),context.before().frame().episodeRunId());
            return new Produced(original,restored,intent,new Request(identity,binding,"original-guardian-request"));
        }
        void requireUntouched(){assertEquals(0,reads);assertEquals(0,submissions);assertEquals(0,reconciliations);}
    }
    private static State empty(){return new State(MACHINE,List.of(),List.of(),List.of());}
    private static RetainedClaim retain(Claim claim){byte[] bytes=encodeClaim(claim);return new RetainedClaim(claim,new ExactRef("synthetic/original-guardian-claim.json",bytes.length,ActionCodec.sha256(bytes)));}
    private static State first(Request request){State before=empty();return append(before,retain(prepareClaim(before,request)));}
    private static byte[] bytes(JsonNode node){return node.toString().getBytes(StandardCharsets.UTF_8);}
    private static Request next(Request original,String requestId,String connection){
        Binding b=original.binding();return new Request(original.identity(),new Binding(b.snapshotId(),b.publicRevisionDecimal(),b.nativeRevisionDecimal(),b.dateRawDecimal(),connection,b.episodeRunId()),requestId);
    }
    @Test void actualPublicGuardianProducerAndColdClaimSerdeKeepSignedActorAndUnsignedRoles() {
        for(long actor:new long[]{Integer.MIN_VALUE,ACTOR,-2,0,1,Integer.MAX_VALUE})for(List<String> keys:List.of(List.<String>of(),List.of("send_language"))){
            Producer producer=new Producer(actor);Produced actual=producer.prepare(keys);
            assertEquals(actual.command(),actual.restored());assertEquals(ActionCodec.bodySha256(actual.command()),ActionCodec.bodySha256(actual.restored()));
            assertTrue(GuardianOutgoingEffects.accepts(actual.restored()));assertEquals(BigInteger.valueOf(actor),actual.restored().before().frame().identity().player());
            assertEquals(CHILD,actual.intent().recipientId());assertEquals(new OrdinaryInitiationIntent.Education(CHILD,GUARDIAN,keys),actual.intent().education().orElseThrow());
            State cold=decode(encode(first(actual.request())));RetainedClaim original=cold.latest(actual.request().identity()).orElseThrow();
            assertEquals(actual.request(),original.claim().request());assertEquals(actor,original.claim().request().identity().actorId());
            assertEquals(BIRTH,original.claim().request().identity().creationFiletimeDecimal());assertEquals(CHILD,original.claim().request().identity().recipientId());
            assertEquals(actual.request().identity().stableActionId(),original.claim().request().identity().stableActionId());
            assertEquals(actor,StrictJson.parse(encode(cold)).at("/claims/0/claim/identity/actor_id").longValue());
            assertEquals(cold,decode(encode(cold)));producer.requireUntouched();
        }
    }
    @Test void coldUnknownAndOriginalLegacyBlockerNeverReleaseTheSameGuardianPair() {
        Producer producer=new Producer(ACTOR);Request request=producer.prepare(List.of("send_language")).request();State cold=decode(encode(first(request)));
        assertThrows(IllegalArgumentException.class,()->prepareClaim(cold,request));
        assertThrows(IllegalArgumentException.class,()->prepareClaim(cold,next(request,"after-ack","2")));
        assertThrows(IllegalArgumentException.class,()->prepareClaim(cold,next(request,"after-reconnect","3")));
        Identity id=request.identity();Identity changedBirth=new Identity(id.machineId(),id.gamePid(),"133700000000000002",id.actorId(),id.interactionKey(),id.recipientId());
        assertThrows(IllegalArgumentException.class,()->prepareClaim(cold,new Request(changedBirth,request.binding(),"same-pid-new-birth")));
        var blocker=new LegacyBlocker(id.machineId(),id.gamePid(),id.actorId(),id.interactionKey(),id.recipientId(),SOURCE_REF,"original process birth unavailable");
        State blocked=decode(encode(new State(MACHINE,List.of(),List.of(),List.of(blocker))));
        assertEquals(blocker,blocked.legacyBlockers().getFirst());assertThrows(IllegalArgumentException.class,()->prepareClaim(blocked,next(request,"cannot-clear-original-blocker","4")));
        assertEquals("claimed_result_unknown_no_retry",StrictJson.parse(encode(cold)).at("/claims/0/claim/status").textValue());producer.requireUntouched();
    }
    @Test void modernAndLegacyActorSerdeRejectUnsignedAliasesMissingAndWrongJsonTypes() {
        Producer producer=new Producer(ACTOR);Request request=producer.prepare(List.of()).request();Identity id=request.identity();
        State blocked=new State(MACHINE,List.of(),List.of(),List.of(new LegacyBlocker(MACHINE,id.gamePid(),ACTOR,id.interactionKey(),CHILD,SOURCE_REF,"original blocker")));
        var f=JsonNodeFactory.instance;
        List<JsonNode> invalid=List.of(f.numberNode(-1),f.numberNode(2147483648L),f.numberNode(-2147483649L),f.numberNode(4261412865L),
                f.booleanNode(true),f.numberNode(1.0),f.textNode("1"),f.nullNode());
        for(JsonNode value:invalid){
            ObjectNode modern=OrdinaryOnceClaims.request(request).deepCopy();((ObjectNode)modern.get("identity")).set("actor_id",value);
            assertThrows(IllegalArgumentException.class,()->readRequest(StrictJson.parse(bytes(modern))));
            ObjectNode legacy=(ObjectNode)StrictJson.parse(encode(blocked));((ObjectNode)legacy.get("legacy_blockers").get(0)).set("actor_id",value);
            assertThrows(IllegalArgumentException.class,()->decode(bytes(legacy)));
        }
        ObjectNode missing=OrdinaryOnceClaims.request(request).deepCopy();((ObjectNode)missing.get("identity")).remove("actor_id");
        assertThrows(IllegalArgumentException.class,()->readRequest(missing));
        ObjectNode missingLegacy=(ObjectNode)StrictJson.parse(encode(blocked));((ObjectNode)missingLegacy.get("legacy_blockers").get(0)).remove("actor_id");
        assertThrows(IllegalArgumentException.class,()->decode(bytes(missingLegacy)));
        for(long actor:new long[]{-1,2147483648L,-2147483649L,4261412865L}){
            assertThrows(IllegalArgumentException.class,()->new Identity(MACHINE,991,BIRTH,actor,id.interactionKey(),CHILD));
            assertThrows(IllegalArgumentException.class,()->new LegacyBlocker(MACHINE,991,actor,id.interactionKey(),CHILD,SOURCE_REF,"old blocker"));
        }
        producer.requireUntouched();
    }
    @Test void recipientChildAndGuardianRetainTheirSeparateNativeFullIdDomain() {
        Identity identity=new Identity(MACHINE,991,BIRTH,ACTOR,"educate_child_interaction",CHILD);assertEquals(CHILD,identity.recipientId());
        var original=new OrdinaryInitiationIntent.Education(CHILD,GUARDIAN,List.of());assertEquals(CHILD,original.childId());
        for(long wrong:new long[]{0,-2,0xFFFF_FFFFL}){
            assertThrows(IllegalArgumentException.class,()->new Identity(MACHINE,991,BIRTH,ACTOR,"educate_child_interaction",wrong));
            assertThrows(IllegalArgumentException.class,()->new LegacyBlocker(MACHINE,991,ACTOR,"educate_child_interaction",wrong,SOURCE_REF,"old blocker"));
            assertThrows(IllegalArgumentException.class,()->new CharacterId(wrong));
            assertThrows(IllegalArgumentException.class,()->new OrdinaryInitiationIntent.Education(wrong,GUARDIAN,List.of()));
            assertThrows(IllegalArgumentException.class,()->new OrdinaryInitiationIntent.Education(CHILD,wrong,List.of()));
        }
    }
}
