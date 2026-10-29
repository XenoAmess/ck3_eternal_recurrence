package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.OptionalLong;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.family.FamilyMarriageSendExpectation;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Complete wire DATA regression. It supplies neither Root qualification nor actual native role-arity authority. */
final class FamilyMarriageSendReadsTest {
    private static final long HASH=0xF1234567L;
    private static final Frame FRAME=new Frame(BigInteger.valueOf(9),BigInteger.valueOf(100),BigInteger.valueOf(7),Build.CROZIER4,BigInteger.ONE);
    private static final FamilyOutgoingCodec.Roles ROLES=new FamilyOutgoingCodec.Roles(31L,null,7L,9L,null);
    private static final List<FamilyOutgoingCodec.OptionRow> BANK=List.of(
            new FamilyOutgoingCodec.OptionRow(0,0xF0000001L,1),new FamilyOutgoingCodec.OptionRow(1,0xF0000001L,0));

    private static ObjectNode prepared() {
        ObjectNode n=StrictJson.object().put("schema",PREPARED_SCHEMA)
                .put("status","available").put("source","original_native_marriage_context_builder")
                .put("read_only",true).put("send_invoked",false).put("command_constructed",false)
                .put("role_arity",5).put("definition_stable_hash",HASH).put("interaction_key","arrange_marriage_interaction")
                .put("complete_can_send",true).put("matrilineal_option_selected",false)
                .put("grand_wedding_option_selected",false).put("copy_passes",2);
        n.putNull("sixth_role_id").putNull("unavailable_reason").putNull("effective_matrilineal_if_accepted");
        n.set("effective_roles",FamilyOutgoingCodec.encodeRoles(ROLES));n.set("selected_option_rows",FamilyOutgoingCodec.encodeOptions(BANK));return n;
    }
    private static ObjectNode packet(Scope scope) {
        var frame=new Frame(FRAME.revision(),FRAME.date(),FRAME.actor(),FRAME.build(),BigInteger.valueOf(20));
        var storage=new FamilyOutgoingCodec.Snapshot(frame,FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE,true,
                OptionalLong.of(HASH),OptionalInt.of(4),OptionalLong.of(31),List.of(),List.of(),Optional.empty());
        ObjectNode n=StrictJson.object().put("schema",WIRE_SCHEMA).put("step",STEP).put("accepted",true)
                .put("status","available").put("private_build",true).put("read_only",true).put("advertised",false)
                .put("backend_id","native-headless").put("query_sequence",20).put("snapshot_revision",9)
                .put("date_raw",100).put("played_character_id",7).put("read_scope",scope.name());
        if(scope==Scope.ACTION_PREPARATION)n.set("prepared_context",prepared());else n.putNull("prepared_context");
        n.set(FamilyOutgoingCodec.GROUP,FamilyOutgoingCodec.encodeGroup(storage));return n;
    }
    private static Observation decode(ObjectNode n,Scope scope) {
        return decodePayload(StrictJson.parse(StrictJson.canonical(n,DriverJson.MAX_NATIVE_BYTES),DriverJson.MAX_NATIVE_BYTES),scope,
                FRAME,scope==Scope.POST_SUBMISSION?OptionalLong.of(31):OptionalLong.empty(),Route.RULER);
    }

    @Test void completeProductionWireRetainsPlayedActorAndRedirectedSenderThroughJsonRoundTrip() {
        var observation=decode(packet(Scope.ACTION_PREPARATION),Scope.ACTION_PREPARATION);
        var context=assertInstanceOf(Prepared.class,observation.prepared().orElseThrow());
        assertEquals(BigInteger.valueOf(7),observation.frame().actor());assertEquals(BigInteger.valueOf(20),observation.frame().querySequence());
        assertEquals(Long.valueOf(31),context.roles().actor());assertNull(context.roles().recipient());assertNull(context.roles().intermediary());
        assertEquals(BANK,context.options());assertTrue(observation.outgoing().complete());
        assertEquals(OptionalLong.of(31),observation.outgoing().senderCharacterId());
        assertEquals(observation,decode(packet(Scope.ACTION_PREPARATION),Scope.ACTION_PREPARATION));
        assertEquals(observation.outgoing(),decode(packet(Scope.POST_SUBMISSION),Scope.POST_SUBMISSION).outgoing());
    }
    @Test void validPreparedSubtreeCannotHideWrongCompleteOuterPacket() {
        List<Consumer<ObjectNode>> changes=List.of(
                n->n.put("schema","old-schema"),n->n.put("step","another-query"),n->n.put("status","unavailable"),
                n->n.put("accepted",false),n->n.put("read_only",false),n->n.put("private_build",false),n->n.put("advertised",true),
                n->n.put("read_scope",Scope.POST_SUBMISSION.name()),n->n.put("backend_id","other-backend"),
                n->n.put("snapshot_revision",10),n->n.put("date_raw",101),n->n.put("played_character_id",31),
                n->n.put("query_sequence",0),n->n.put("query_sequence",true),n->n.put("query_sequence",20.0),
                n->n.put("snapshot_revision",9.0),n->n.remove(FamilyOutgoingCodec.GROUP),n->n.remove("prepared_context"),
                n->n.put("legacy_alias",true));
        for(var change:changes){var n=packet(Scope.ACTION_PREPARATION);change.accept(n);
            assertThrows(IllegalArgumentException.class,()->decode(n,Scope.ACTION_PREPARATION),n.toString());}
    }
    @Test void originalPreparedSenderAndDefinitionMustMatchEntireStorageBaseline() {
        for(String key:List.of("sender_character_id","definition_stable_hash")){
            var n=packet(Scope.ACTION_PREPARATION);((ObjectNode)n.get(FamilyOutgoingCodec.GROUP)).put(key,32);
            assertThrows(IllegalArgumentException.class,()->decode(n,Scope.ACTION_PREPARATION));
        }
        var n=packet(Scope.ACTION_PREPARATION);((ObjectNode)n.get("prepared_context")).put("sixth_role_id",31);
        assertThrows(IllegalArgumentException.class,()->decode(n,Scope.ACTION_PREPARATION));
    }
    @Test void legacyBarePredicateScanCannotAliasSourceBoundV4() {
        var n=packet(Scope.ACTION_PREPARATION);((ObjectNode)n.get(FamilyOutgoingCodec.GROUP)).put("schema","ck3-family-outgoing-storage-12004-v3");
        assertThrows(IllegalArgumentException.class,()->decode(n,Scope.ACTION_PREPARATION));
        assertEquals("ck3-family-outgoing-storage-12004-v4",FamilyOutgoingCodec.SCHEMA);
    }
    @Test void postReadCannotBuildFreshPreparationOrChangeOriginalSenderFilter() {
        var fresh=packet(Scope.POST_SUBMISSION);fresh.set("prepared_context",prepared());
        assertThrows(IllegalArgumentException.class,()->decode(fresh,Scope.POST_SUBMISSION));
        assertThrows(IllegalArgumentException.class,()->decodePayload(packet(Scope.POST_SUBMISSION),Scope.POST_SUBMISSION,FRAME,OptionalLong.of(7),Route.RULER));
        assertThrows(IllegalArgumentException.class,()->decodePayload(packet(Scope.POST_SUBMISSION),Scope.POST_SUBMISSION,FRAME,OptionalLong.empty(),Route.RULER));
        assertThrows(IllegalArgumentException.class,()->decodePayload(packet(Scope.ACTION_PREPARATION),Scope.ACTION_PREPARATION,FRAME,OptionalLong.of(31),Route.RULER));
    }
    @Test void unavailableArityOrStorageIsPreservedWithoutNegativeOrPartialFacts() {
        var n=packet(Scope.ACTION_PREPARATION);n.put("status","unavailable");
        var unavailable=new FamilyOutgoingCodec.Snapshot(FRAME,FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE,false,
                OptionalLong.empty(),OptionalInt.empty(),OptionalLong.empty(),List.of(),List.of(),Optional.of("actual_pending_role_arity_source_unqualified"));
        n.set(FamilyOutgoingCodec.GROUP,FamilyOutgoingCodec.encodeGroup(unavailable));
        var result=decode(n,Scope.ACTION_PREPARATION);assertFalse(result.outgoing().complete());
        assertEquals(Optional.of("actual_pending_role_arity_source_unqualified"),result.outgoing().unavailableReason());
        assertTrue(result.outgoing().candidates().isEmpty());assertTrue(result.outgoing().senderCharacterId().isEmpty());
        var partial=n.deepCopy();((ObjectNode)partial.get(FamilyOutgoingCodec.GROUP)).put("sender_character_id",31);
        assertThrows(IllegalArgumentException.class,()->decode(partial,Scope.ACTION_PREPARATION));
    }
    @Test void argumentRoundTripPreservesExplicitNullsAndRejectsMissingWrongTypedOrCrossScopeFields() {
        var intent=new RulerMarriageIntent("7-9",7,9,Optional.empty()).toJson();
        var ref=new ExactRef("fixture-original",1,"a".repeat(64));
        var basis=new FreshBasis(ref,new ExactRef("fixture-bridge",2,"b".repeat(64)),List.of(new ExactRef("fixture-read",3,"c".repeat(64))));
        var before=new Arguments(Scope.ACTION_PREPARATION,"action-original","d".repeat(64),"request-original",intent,
                Optional.of(basis),Optional.empty(),OptionalLong.empty());
        assertEquals(before,arguments(encode(before)));assertTrue(DriverJson.toNode(encode(before)).get("sender_character_id").isNull());
        var after=new Arguments(Scope.POST_SUBMISSION,"action-original","d".repeat(64),"request-original",intent,
                Optional.empty(),Optional.of(ref),OptionalLong.of(31));
        assertEquals(after,arguments(encode(after)));assertEquals(31,StrictJson.parse(nativeFields(after).bytes()).get("sender_character_id").longValue());
        List<Consumer<ObjectNode>> changes=List.of(n->n.remove("sender_character_id"),n->n.putNull("sender_character_id"),
                n->n.put("sender_character_id",true),n->n.put("sender_character_id",31.0),n->n.remove("fresh_basis"),
                n->n.putNull("before_read"),n->n.put("scope",Scope.ACTION_PREPARATION.name()));
        for(var change:changes){var n=(ObjectNode)DriverJson.toNode(encode(after));change.accept(n);
            assertThrows(IllegalArgumentException.class,()->arguments(DriverJson.object(StrictJson.canonical(n),DriverJson.MAX_NATIVE_BYTES)));}
    }
    @Test void expectedPreSubmissionFieldsHaveNoInventedPendingIdentityOrGameCredit() {
        var values=FamilyMarriageSendExpectation.values(7,9);assertEquals(6,values.size());
        assertFalse(values.stream().anyMatch(value->value.field().value().equals("native_pending_full_id")));
        assertFalse(values.stream().anyMatch(value->value.field().value().startsWith("timeline.")));
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageSendExpectation.values(7,7));
    }
    @Test void originalFirstHeirAndFulfillmentDoNotInvokeTheChildOnlyOptionSetter() {
        var ref=new ExactRef("fixture-original",1,"a".repeat(64));
        var basis=new FreshBasis(ref,new ExactRef("fixture-bridge",2,"b".repeat(64)),List.of(new ExactRef("fixture-read",3,"c".repeat(64))));
        for(var route:FamilyMarriageIntent.Route.values())for(boolean matrilineal:List.of(false,true)){
            if(route==FamilyMarriageIntent.Route.CHILD_MATRILINEAL&&!matrilineal||route==FamilyMarriageIntent.Route.CHILD_DEFAULT&&matrilineal)continue;
            var intent=new FamilyMarriageIntent(route,7,8,9,17,matrilineal,
                    route==FamilyMarriageIntent.Route.FIRST_HEIR?List.of(9,13,14,15,16):List.of(),Optional.empty());
            var args=new Arguments(Scope.ACTION_PREPARATION,"action-original","d".repeat(64),"request-original",intent.toJson(),
                    Optional.of(basis),Optional.empty(),OptionalLong.empty());
            var actual=StrictJson.parse(nativeFields(arguments(encode(args))).bytes());
            assertEquals(intent.step(),actual.get("source_action_step").textValue());
            assertEquals(route==FamilyMarriageIntent.Route.CHILD_MATRILINEAL,actual.get("request_matrilineal_option").booleanValue());
            assertEquals(route==FamilyMarriageIntent.Route.CHILD_DEFAULT,actual.get("require_matrilineal_option_off").booleanValue());
            assertEquals(matrilineal,FamilyMarriageIntent.fromJson(arguments(encode(args)).senderIntent()).matrilineal(),"expected native option is retained independently of setter invocation");
        }
    }
    @Test void selectedOptionAndEffectiveLinealityAreDistinctRequiredPrivateMaterial() {
        for(var route:List.of(Route.FIRST_HEIR,Route.FULFILL_BETROTHAL,Route.CHILD_MATRILINEAL,Route.CHILD_DEFAULT))for(boolean effective:List.of(false,true)){
            var n=packet(Scope.ACTION_PREPARATION);((ObjectNode)n.get("prepared_context")).put("effective_matrilineal_if_accepted",effective)
                    .put("matrilineal_option_selected",route==Route.CHILD_MATRILINEAL);
            var value=decodePayload(n,Scope.ACTION_PREPARATION,FRAME,OptionalLong.empty(),route);
            var context=assertInstanceOf(Prepared.class,value.prepared().orElseThrow());
            assertEquals(route==Route.CHILD_MATRILINEAL,context.matrilineal());assertEquals(Optional.of(effective),context.effectiveMatrilineal());
            assertThrows(IllegalArgumentException.class,()->decodePayload(n,Scope.ACTION_PREPARATION,FRAME,OptionalLong.empty(),Route.RULER));
        }
        assertThrows(IllegalArgumentException.class,()->decodePayload(packet(Scope.ACTION_PREPARATION),Scope.ACTION_PREPARATION,FRAME,OptionalLong.empty(),Route.FULFILL_BETROTHAL));
        var legacy=prepared().put("schema","ck3-marriage-materialized-send-context-12004-v1");legacy.remove("effective_matrilineal_if_accepted");
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageSendReads.prepared(legacy));
        var missing=prepared();missing.remove("effective_matrilineal_if_accepted");assertThrows(IllegalArgumentException.class,()->FamilyMarriageSendReads.prepared(missing));
        var wrong=prepared().put("effective_matrilineal_if_accepted",1);assertThrows(IllegalArgumentException.class,()->FamilyMarriageSendReads.prepared(wrong));
        var wrongFloat=prepared().put("effective_matrilineal_if_accepted",1.0);assertThrows(IllegalArgumentException.class,()->FamilyMarriageSendReads.prepared(wrongFloat));
    }
    @Test void unavailablePreparationCannotInventAnEffectiveOutcome() {
        var n=prepared().put("status","unavailable").put("copy_passes",0).put("unavailable_reason","actual finalized terms unavailable");
        for(String field:List.of("role_arity","definition_stable_hash","complete_can_send","matrilineal_option_selected","grand_wedding_option_selected","effective_roles"))n.putNull(field);
        n.putArray("selected_option_rows");
        assertInstanceOf(NotPrepared.class,FamilyMarriageSendReads.prepared(n));
        n.put("effective_matrilineal_if_accepted",false);
        assertThrows(IllegalArgumentException.class,()->FamilyMarriageSendReads.prepared(n));
    }
}
