package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.math.BigInteger;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.advance.AdvancePlan;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootOnlineDecisionSelector;
import org.xar.ck3.control.service.root.RootOrdinaryRuntimeConfiguration.DecisionProvider;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** New cases invoke the actual model payload builder; fixture DATA creates no private authority or HTTP. */
final class ModelHistoryByteIdentity104Test {
    private static final int MATERIAL=FullJsonTree.MAXIMUM_BYTES;
    private static final Claims EMPTY=new Claims(Set.of(),Set.of(),Set.of(),Set.of());
    private static final Obj EVIDENCE=obj("fixture",new Text("retained business evidence"));
    private static final String QUERY="ew0KICAic3RhdHVzIjogImF2YWlsYWJsZSIsDQogICJzdGVwIjogInByaXZhdGUtcXVlcnktY291bmNpbC1maW5hbC1nYXRlcy12MSIsDQogICJwcml2YXRlX2J1aWxkIjogdHJ1ZSwNCiAgInJlYWRfb25seSI6IHRydWUsDQogICJhZHZlcnRpc2VkIjogZmFsc2UsDQogICJxdWVyaWVkX3NuYXBzaG90X2lkIjogInNuYXBzaG90LTEiLA0KICAicXVlcmllZF9yZXZpc2lvbiI6IDEsDQogICJxdWVyaWVkX25hdGl2ZV9yZXZpc2lvbiI6IDEsDQogICJzb3VyY2VfZnJhbWUiOiB7DQogICAgInNuYXBzaG90X2lkIjogInNuYXBzaG90LTEiLA0KICAgICJyZXZpc2lvbiI6IDEsDQogICAgIm5hdGl2ZV9yZXZpc2lvbiI6IDEsDQogICAgImRhdGVfcmF3IjogMjQwMDAsDQogICAgInBsYXllcl9jaGFyYWN0ZXJfaWQiOiAyOTgyOSwNCiAgICAicGF1c2VkIjogdHJ1ZQ0KICB9LA0KICAiY291bmNpbF9jb21wb3NpdGlvbl9jYW5kaWRhdGVzIjogew0KICAgICJzbmFwc2hvdCI6IHsNCiAgICAgICJzbmFwc2hvdF9pZCI6ICJuYXRpdmU6MSIsDQogICAgICAicHVibGljX3JldmlzaW9uIjogMSwNCiAgICAgICJuYXRpdmVfcmV2aXNpb24iOiAxLA0KICAgICAgImRhdGVfcmF3IjogMjQwMDAsDQogICAgICAicGF1c2VkIjogdHJ1ZQ0KICAgIH0sDQogICAgIm93bmVyX2NoYXJhY3Rlcl9pZCI6IDI5ODI5LA0KICAgICJwb3NpdGlvbiI6IHsNCiAgICAgICJwb3NpdGlvbl9rZXkiOiAiY291bmNpbGxvcl9zdGV3YXJkIiwNCiAgICAgICJpbmN1bWJlbnRfY2hhcmFjdGVyX2lkIjogMTY3NzcyMTgsDQogICAgICAiaW5jdW1iZW50X21haW5fc2tpbGwiOiB7DQogICAgICAgICJrZXkiOiAic3Rld2FyZHNoaXAiLA0KICAgICAgICAidmFsdWUiOiA5DQogICAgICB9LA0KICAgICAgInZhY2FudCI6IGZhbHNlLA0KICAgICAgImFjdGlvbl9yb3V0ZSI6ICJyZXBsYWNlIg0KICAgIH0sDQogICAgImNhbmRpZGF0ZV9jb2xsZWN0aW9uX2NvbXBsZXRlIjogdHJ1ZSwNCiAgICAiY2FuZGlkYXRlcyI6IFsNCiAgICAgIHsNCiAgICAgICAgImNoYXJhY3Rlcl9pZCI6IDE2Nzc3MjMyLA0KICAgICAgICAibmF0aXZlX2NvbGxlY3Rpb25fb3JkaW5hbCI6IDEsDQogICAgICAgICJlbGlnaWJsZSI6IHRydWUsDQogICAgICAgICJlbGlnaWJpbGl0eV9yZWFzb24iOiAibmF0aXZlX2NhbmRpZGF0ZV9wcm92aWRlcl9hY2NlcHRlZCIsDQogICAgICAgICJtYWluX3NraWxsIjogew0KICAgICAgICAgICJrZXkiOiAic3Rld2FyZHNoaXAiLA0KICAgICAgICAgICJ2YWx1ZSI6IDIyDQogICAgICAgIH0sDQogICAgICAgICJhY3Rpb25fcm91dGUiOiAicmVwbGFjZSINCiAgICAgIH0sDQogICAgICB7DQogICAgICAgICJjaGFyYWN0ZXJfaWQiOiAxNjc3NzIzMywNCiAgICAgICAgIm5hdGl2ZV9jb2xsZWN0aW9uX29yZGluYWwiOiAwLA0KICAgICAgICAiZWxpZ2libGUiOiB0cnVlLA0KICAgICAgICAiZWxpZ2liaWxpdHlfcmVhc29uIjogIm5hdGl2ZV9jYW5kaWRhdGVfcHJvdmlkZXJfYWNjZXB0ZWQiLA0KICAgICAgICAibWFpbl9za2lsbCI6IHsNCiAgICAgICAgICAia2V5IjogInN0ZXdhcmRzaGlwIiwNCiAgICAgICAgICAidmFsdWUiOiAxNw0KICAgICAgICB9LA0KICAgICAgICAiYWN0aW9uX3JvdXRlIjogInJlcGxhY2UiDQogICAgICB9DQogICAgXSwNCiAgICAicmVhZGluZXNzIjogew0KICAgICAgImlkZW50aXR5X3JlYWR5IjogdHJ1ZSwNCiAgICAgICJjYW5kaWRhdGVfY29sbGVjdGlvbl9yZWFkeSI6IHRydWUsDQogICAgICAiaW5jdW1iZW50X3JlYWR5IjogdHJ1ZSwNCiAgICAgICJpbmN1bWJlbnRfbWFpbl9za2lsbF9yZWFkeSI6IHRydWUsDQogICAgICAiY2FuZGlkYXRlX2xlZ2FsaXR5X3JlYWR5IjogdHJ1ZSwNCiAgICAgICJtYWluX3NraWxsX3JlYWR5IjogdHJ1ZSwNCiAgICAgICJhY3Rpb25fcm91dGVfcmVhZHkiOiB0cnVlLA0KICAgICAgInNhbWVfZnJhbWVfcmVhZHkiOiB0cnVlLA0KICAgICAgInJlYWR5IjogdHJ1ZQ0KICAgIH0NCiAgfSwNCiAgImNvdW5jaWxfZmluYWxfZ2F0ZXMiOiB7DQogICAgInNjaGVtYSI6ICJ4YXIuY2szLnByaXZhdGUuY291bmNpbC1maW5hbC1nYXRlcy92MSIsDQogICAgInN0YXR1cyI6ICJhdmFpbGFibGUiLA0KICAgICJ1bmF2YWlsYWJsZV9yZWFzb24iOiAibm9uZSIsDQogICAgImNhbmRpZGF0ZV9jb3VudCI6IDIsDQogICAgInJvd3MiOiBbDQogICAgICB7DQogICAgICAgICJjaGFyYWN0ZXJfaWQiOiAxNjc3NzIzMiwNCiAgICAgICAgIm5hdGl2ZV9jb2xsZWN0aW9uX29yZGluYWwiOiAxLA0KICAgICAgICAiZmluYWxfZ2F0ZV9hdmFpbGFibGUiOiB0cnVlLA0KICAgICAgICAiY2FuZGlkYXRlX2FscmVhZHlfY291bmNpbGxvciI6IGZhbHNlLA0KICAgICAgICAiY2FuZGlkYXRlX2lzX2d1ZXN0IjogZmFsc2UsDQogICAgICAgICJwZW5kaW5nX2NoYXJhY3Rlcl9pbnRlcmFjdGlvbiI6IGZhbHNlLA0KICAgICAgICAiaW5jdW1iZW50X2ZpcmVhYmlsaXR5X2V2YWx1YXRlZCI6IHRydWUsDQogICAgICAgICJpbmN1bWJlbnRfY2FuX2JlX2ZpcmVkIjogdHJ1ZQ0KICAgICAgfSwNCiAgICAgIHsNCiAgICAgICAgImNoYXJhY3Rlcl9pZCI6IDE2Nzc3MjMzLA0KICAgICAgICAibmF0aXZlX2NvbGxlY3Rpb25fb3JkaW5hbCI6IDAsDQogICAgICAgICJmaW5hbF9nYXRlX2F2YWlsYWJsZSI6IHRydWUsDQogICAgICAgICJjYW5kaWRhdGVfYWxyZWFkeV9jb3VuY2lsbG9yIjogZmFsc2UsDQogICAgICAgICJjYW5kaWRhdGVfaXNfZ3Vlc3QiOiBmYWxzZSwNCiAgICAgICAgInBlbmRpbmdfY2hhcmFjdGVyX2ludGVyYWN0aW9uIjogZmFsc2UsDQogICAgICAgICJpbmN1bWJlbnRfZmlyZWFiaWxpdHlfZXZhbHVhdGVkIjogdHJ1ZSwNCiAgICAgICAgImluY3VtYmVudF9jYW5fYmVfZmlyZWQiOiB0cnVlDQogICAgICB9DQogICAgXSwNCiAgICAiY291bmNpbF9jb21wb3NpdGlvbl9jYW5kaWRhdGVzIjogew0KICAgICAgInNuYXBzaG90Ijogew0KICAgICAgICAic25hcHNob3RfaWQiOiAibmF0aXZlOjEiLA0KICAgICAgICAicHVibGljX3JldmlzaW9uIjogMSwNCiAgICAgICAgIm5hdGl2ZV9yZXZpc2lvbiI6IDEsDQogICAgICAgICJkYXRlX3JhdyI6IDI0MDAwLA0KICAgICAgICAicGF1c2VkIjogdHJ1ZQ0KICAgICAgfSwNCiAgICAgICJvd25lcl9jaGFyYWN0ZXJfaWQiOiAyOTgyOSwNCiAgICAgICJwb3NpdGlvbiI6IHsNCiAgICAgICAgInBvc2l0aW9uX2tleSI6ICJjb3VuY2lsbG9yX3N0ZXdhcmQiLA0KICAgICAgICAiaW5jdW1iZW50X2NoYXJhY3Rlcl9pZCI6IDE2Nzc3MjE4LA0KICAgICAgICAiaW5jdW1iZW50X21haW5fc2tpbGwiOiB7DQogICAgICAgICAgImtleSI6ICJzdGV3YXJkc2hpcCIsDQogICAgICAgICAgInZhbHVlIjogOQ0KICAgICAgICB9LA0KICAgICAgICAidmFjYW50IjogZmFsc2UsDQogICAgICAgICJhY3Rpb25fcm91dGUiOiAicmVwbGFjZSINCiAgICAgIH0sDQogICAgICAiY2FuZGlkYXRlX2NvbGxlY3Rpb25fY29tcGxldGUiOiB0cnVlLA0KICAgICAgImNhbmRpZGF0ZXMiOiBbDQogICAgICAgIHsNCiAgICAgICAgICAiY2hhcmFjdGVyX2lkIjogMTY3NzcyMzIsDQogICAgICAgICAgIm5hdGl2ZV9jb2xsZWN0aW9uX29yZGluYWwiOiAxLA0KICAgICAgICAgICJlbGlnaWJsZSI6IHRydWUsDQogICAgICAgICAgImVsaWdpYmlsaXR5X3JlYXNvbiI6ICJuYXRpdmVfY2FuZGlkYXRlX3Byb3ZpZGVyX2FjY2VwdGVkIiwNCiAgICAgICAgICAibWFpbl9za2lsbCI6IHsNCiAgICAgICAgICAgICJrZXkiOiAic3Rld2FyZHNoaXAiLA0KICAgICAgICAgICAgInZhbHVlIjogMjINCiAgICAgICAgICB9LA0KICAgICAgICAgICJhY3Rpb25fcm91dGUiOiAicmVwbGFjZSINCiAgICAgICAgfSwNCiAgICAgICAgew0KICAgICAgICAgICJjaGFyYWN0ZXJfaWQiOiAxNjc3NzIzMywNCiAgICAgICAgICAibmF0aXZlX2NvbGxlY3Rpb25fb3JkaW5hbCI6IDAsDQogICAgICAgICAgImVsaWdpYmxlIjogdHJ1ZSwNCiAgICAgICAgICAiZWxpZ2liaWxpdHlfcmVhc29uIjogIm5hdGl2ZV9jYW5kaWRhdGVfcHJvdmlkZXJfYWNjZXB0ZWQiLA0KICAgICAgICAgICJtYWluX3NraWxsIjogew0KICAgICAgICAgICAgImtleSI6ICJzdGV3YXJkc2hpcCIsDQogICAgICAgICAgICAidmFsdWUiOiAxNw0KICAgICAgICAgIH0sDQogICAgICAgICAgImFjdGlvbl9yb3V0ZSI6ICJyZXBsYWNlIg0KICAgICAgICB9DQogICAgICBdLA0KICAgICAgInJlYWRpbmVzcyI6IHsNCiAgICAgICAgImlkZW50aXR5X3JlYWR5IjogdHJ1ZSwNCiAgICAgICAgImNhbmRpZGF0ZV9jb2xsZWN0aW9uX3JlYWR5IjogdHJ1ZSwNCiAgICAgICAgImluY3VtYmVudF9yZWFkeSI6IHRydWUsDQogICAgICAgICJpbmN1bWJlbnRfbWFpbl9za2lsbF9yZWFkeSI6IHRydWUsDQogICAgICAgICJjYW5kaWRhdGVfbGVnYWxpdHlfcmVhZHkiOiB0cnVlLA0KICAgICAgICAibWFpbl9za2lsbF9yZWFkeSI6IHRydWUsDQogICAgICAgICJhY3Rpb25fcm91dGVfcmVhZHkiOiB0cnVlLA0KICAgICAgICAic2FtZV9mcmFtZV9yZWFkeSI6IHRydWUsDQogICAgICAgICJyZWFkeSI6IHRydWUNCiAgICAgIH0NCiAgICB9DQogIH0NCn0NCg==";
    private record Scene(PlanningRequest request,PlanningResult.ActionSelected proposal) { }

    @Test void reorderedAndDistinctCurrentHistorySurvivesAllActualPayloadPaths() throws Exception {
        Obj first=row(obj("x",integer(1),"y",integer(2)));
        Obj reordered=row(obj("y",integer(2),"x",integer(1)));
        assertEquals(toNode(first),toNode(reordered),"the original tree predicate misses member order");
        assertEquals(first,reordered,"the original typed Map predicate also misses member order");
        assertFalse(java.util.Arrays.equals(bytes(toNode(first)),bytes(toNode(reordered))));
        List<Obj[]> cases=List.of(
                new Obj[]{first,reordered},
                new Obj[]{row(obj("nested",obj("a",integer(1),"b",integer(2)))),
                        row(obj("nested",obj("b",integer(2),"a",integer(1))))},
                new Obj[]{first,row(obj("x",integer(1),"y",integer(2),"unknown",Nil.INSTANCE))},
                new Obj[]{row(obj("items",new Arr(List.of(integer(1),integer(2))))),
                        row(obj("items",new Arr(List.of(integer(2),integer(1)))))},
                new Obj[]{row(obj("decimal",new DecimalValue("1.0"))),row(obj("decimal",new DecimalValue("1.00")))},
                new Obj[]{row(obj("decimal",new DecimalValue("-0.000"))),row(obj("decimal",new DecimalValue("0.000")))},
                new Obj[]{row(obj("id",new IntegerValue(new BigInteger("18446744073709551614")))),
                        row(obj("id",new IntegerValue(new BigInteger("18446744073709551615"))))});
        for(Obj[] pair:cases)for(String route:List.of("generic","life","council"))
            exercise(route,List.of(pair[0]),new Arr(List.of(pair[1])),false);
    }

    @Test void onlyExactCompleteHistoryDuplicatesAreOmitted() throws Exception {
        Obj row=row(obj("unknown",Nil.INSTANCE,"id",new IntegerValue(new BigInteger("18446744073709551615")),
                "precise",new DecimalValue("1.230000000000000000000000000000e-23")));
        for(String route:List.of("generic","life","council")) {
            exercise(route,List.of(row),new Arr(List.of(row)),true);
            exercise(route,List.of(),new Arr(List.of()),true);
            exercise(route,List.of(row),Nil.INSTANCE,false);
            exercise(route,List.of(row),new Text("not-an-array"),false);
        }
    }

    @Test void wireLegalDeepTypedHistoryDoesNotAcquireTheNarrowerOpportunityEncoderLimit() throws Exception {
        Value left=integer(1),right=integer(1);
        for(int depth=0;depth<35;depth++) {
            left=obj("first",left,"second",Nil.INSTANCE);
            right=obj("second",Nil.INSTANCE,"first",right);
        }
        Obj original=row(obj("deep",left)),reordered=row(obj("deep",right));
        assertEquals(toNode(original),toNode(reordered));
        assertThrows(IllegalArgumentException.class,()->OpportunityJson.encode(original),
                "typed DATA exceeds only the narrower legacy OpportunityJson.write depth");
        for(String route:List.of("generic","life","council")) {
            exercise(route,List.of(original),new Arr(List.of(original)),true);
            exercise(route,List.of(original),new Arr(List.of(reordered)),false);
        }
    }

    private static void exercise(String route,List<Obj> history,Value nativeHistory,boolean omitted) throws Exception {
        Obj snapshot=lifeSnapshot().with("native_command_history",nativeHistory);
        Scene scene=scene(route,snapshot,history);
        byte[] originalSnapshot=bytes(toNode(snapshot));
        byte[] originalHistory=bytes(toNode(new Arr(new ArrayList<Value>(history))));
        byte[] command=ActionCodec.encodeCommand(scene.proposal().command());
        String digest=ActionCodec.bodySha256(scene.proposal().command());
        JsonNode data=wire(scene);
        assertEquals(scene.proposal().command().actionId(),data.path("proposal_id").textValue());
        assertEquals(digest,data.path("body_sha256").textValue());
        assertArrayEquals(command,bytes(data.get("proposal")));
        if(route.equals("life"))assertEquals("xar.model-peaceful-life-decision/v1",data.path("decision_context_schema").textValue());
        else if(route.equals("council"))assertEquals("xar.model-private-council-admission/v1",data.path("decision_context_schema").textValue());
        else assertFalse(data.has("decision_context_schema"));
        ObjectNode expected=(ObjectNode)toNode(snapshot);
        if(omitted)expected.remove("native_command_history");
        assertArrayEquals(bytes(expected),bytes(data.get("snapshot")),route+" must preserve ordered current facts");
        if(!omitted)assertArrayEquals(bytes(toNode(nativeHistory)),bytes(data.get("snapshot").get("native_command_history")));
        if(route.equals("council"))assertEquals(omitted,data.has("duplicate_snapshot_history_omitted"));
        if(route.equals("generic"))assertArrayEquals(originalHistory,bytes(data.get("history")));
        assertArrayEquals(originalSnapshot,bytes(toNode(scene.request().observations().snapshot())));
        assertArrayEquals(originalHistory,bytes(toNode(new Arr(new ArrayList<Value>(scene.request().observations().history())))));
        assertArrayEquals(command,ActionCodec.encodeCommand(scene.proposal().command()));
        assertEquals(digest,ActionCodec.bodySha256(scene.proposal().command()));
    }

    private static Scene scene(String route,Obj snapshot,List<Obj> history) {
        if(route.equals("life")) {
            PlanningRequest request=request(snapshot,history,List.of());
            return new Scene(request,selected(request));
        }
        OperationKey operation=new OperationKey(route.equals("council")?"private-assign-councillor-v1":"fixture-read-model-history");
        PlanningRequest request=PlanningFixtures.request(snapshot,history,Set.of(operation));
        Obj args=route.equals("council")?new Obj(Map.of("position_key",new Text("councillor_steward"),
                "candidate_character_id",integer(16777232),"original_query",parse(Base64.getDecoder().decode(QUERY)),
                "expected_has_incumbent",new Bool(true),"expected_incumbent_character_id",integer(16777218))):obj();
        ActionCommand command=PlanningFixtures.command(request,operation,args);
        OrdinaryPolicy.Draft draft=new OrdinaryPolicy.Draft("fixture-history-policy","fixture-history-phase","fixture history reason",
                OrdinaryPolicy.Kind.ORDINARY,Optional.of(command),
                route.equals("council")?OrdinaryPolicy.Purpose.WORLD_ACTION:OrdinaryPolicy.Purpose.READ_ONLY,
                route.equals("council")?Optional.of(Domain.council):Optional.empty(),obj());
        return new Scene(request,new PlanningResult.ActionSelected(command,new PlanTrace(request.before(),List.of(),Optional.of(draft))));
    }
    private static JsonNode wire(Scene scene)throws Exception {
        var config=new DecisionProvider(URI.create("http://127.0.0.1:1/v1"),"fixture-model",Duration.ofSeconds(10),1,Duration.ZERO);
        var selector=new RootOnlineDecisionSelector(config,Clock.fixed(PlanningFixtures.NOW,ZoneOffset.UTC),raw->{throw new AssertionError("no material or HTTP I/O");});
        Method method=RootOnlineDecisionSelector.class.getDeclaredMethod("requestPayload",PlanningRequest.class,PlanningResult.ActionSelected.class,String.class);
        method.setAccessible(true);
        try {
            byte[] raw=(byte[])method.invoke(selector,scene.request(),scene.proposal(),ActionCodec.bodySha256(scene.proposal().command()));
            JsonNode envelope=FullJsonTree.parse(raw,MATERIAL);
            return FullJsonTree.parse(envelope.get("messages").get(1).get("content").textValue().getBytes(StandardCharsets.UTF_8),MATERIAL);
        }catch(InvocationTargetException failure){
            if(failure.getCause() instanceof Exception exception)throw exception;
            if(failure.getCause() instanceof Error error)throw error;
            throw failure;
        }
    }
    private static Obj row(Obj result){return obj("index",integer(1),"command",new Text("fixture-history-opaque"),"ok",new Bool(true),"result",result);}
    private static byte[] bytes(JsonNode tree){return FullJsonTree.encode(tree,MATERIAL);}
    private static Obj jsonObject(String json){return object(OpportunityJson.parseComplete(json.getBytes(StandardCharsets.UTF_8),MATERIAL),"fixture");}
    private static IntegerValue integer(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static Obj obj(Object... pairs){
        Map<String,Value> fields=new LinkedHashMap<>();
        for(int index=0;index<pairs.length;index+=2)fields.put((String)pairs[index],(Value)pairs[index+1]);
        return new Obj(fields);
    }
    private static Obj lifeSnapshot() {
        Obj root = jsonObject("""
                {"schema_version":1,"status":"available","snapshot_revision":1,"date_raw":24000,
                 "local_player_id":0,"player_character_id":29829,"player_character_alive":true,
                 "primary_title":null,"capital_province_id":null,"immediate_liege_character_id":null,
                 "top_liege_character_id":29829,"independent":true,"government":null,
                 "selected_game_rule_tokens":[],"native_selected_game_rule_token_count":0,
                 "readiness":{"capital_ready":true,"government_ready":true,"lieges_ready":true,
                   "player_identity_ready":true,"primary_title_ready":true,"ready":true,
                   "same_frame_ready":true,"selected_game_rule_tokens_ready":true},
                 "unavailable_reason":null,
                 "provenance":{"game_version":"1.20.0.4",
                   "executable_sha256":"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
                   "backend_id":"ck3-1.20.0.4-native-campaign-root-context-v1",
                   "primary_title_rva":"0x289DA10","capital_province_rva":"0x28B1CB0",
                   "immediate_liege_rva":"0x28BFC50","top_liege_rva":"0x28BFD80",
                   "government_rva":"0x28C2DF0","selected_game_rule_service_slot_rva":"0x5CB3D78"}}
                """);
        assertEquals(root, CampaignRootContextJson.normalize(root, BigInteger.valueOf(24000), BigInteger.ONE),
                "fixture must itself satisfy the real current ROOT normalizer");
        Obj binding = obj("snapshot_id", new Text("snapshot-1"), "revision", integer(1), "native_revision", integer(1),
                "date_raw", integer(24000), "actor_character_id", integer(29829), "bridge_pid", integer(123),
                "connection_generation", integer(1));
        return PlanningFixtures.snapshot()
                .with("one_life_terminal", new Bool(false)).with("episode_identity_pending", new Bool(false))
                .with("active_event", Nil.INSTANCE).with("pending_character_interaction", Nil.INSTANCE)
                .with("one_life_terminal_reason", Nil.INSTANCE).with("episode_transition", Nil.INSTANCE)
                .with("episode_transition_error", Nil.INSTANCE).with("driver_state_error", Nil.INSTANCE)
                .with("cold_candidate_rejection", Nil.INSTANCE)
                .with("top_exclusive_modal_choice_hint", Nil.INSTANCE)
                .with("campaign_root_context_query", obj("query_sequence", integer(1), "campaign_root_context", root,
                        "cache_binding", binding))
                .with("unknown_current_fields", obj("not_a_success_claim", new Text("retain-me"),
                        "large_integer", new IntegerValue(new BigInteger("18446744073709551615")),
                        "signed_zero", new DecimalValue("-0.000"),
                        "precise_decimal", new DecimalValue("1.23456789012345678901234567890e-17")));
    }

    private static PlanningRequest request(Obj snapshot, List<Obj> history, List<ExternalFact> facts) {
        PlanningRequest baseline = PlanningFixtures.request(PlanningFixtures.snapshot(), List.of(), Set.of());
        PlanningObservation observations = new PlanningObservation(snapshot, history,
                Set.of(new OperationKey("life-advance"), new OperationKey("pause-map"),
                        new OperationKey("query-campaign-root-context-v1"), new OperationKey(ClockStatusRead.STEP),
                        new OperationKey("resume-map"), new OperationKey("set-speed-5")),
                Set.of("zeta-capability", "alpha-capability", "game.command.pause-map", "game.command.resume-map",
                        "game.command.set-speed-5", ClockStatusRead.ARM_CAP, ClockStatusRead.STATUS_CAP,
                        ClockStatusRead.CANCEL_CAP), Optional.empty(), facts, Optional.empty(), Optional.empty(), false);
        assertTrue(ClockStatusRead.available(observations.bridgeCapabilities()), "fixture advertises actual clock ports");
        return new PlanningRequest(baseline.before(), baseline.source(), baseline.sessionId(), baseline.deadline(), observations);
    }

    private static AdvancePlan plan(int days, boolean exact, AdvancePlan.ClockMode mode, boolean capped) {
        BigInteger start = BigInteger.valueOf(24000), end = start.add(AdvancePlan.DAY.multiply(BigInteger.valueOf(days)));
        Optional<CampaignDeadline.Cap> cap = capped ? Optional.of(new CampaignDeadline.Cap("fixture-campaign",
                CampaignDeadline.CALENDAR_PROFILE, start, end, start.add(BigInteger.valueOf(720)),
                start.add(BigInteger.valueOf(1440)), end, CampaignDeadline.Status.ADVANCE)) : Optional.empty();
        return new AdvancePlan(start, end, days, 5, "bounded_non_tactical", exact, mode, cap);
    }

    private static PlanningResult.ActionSelected selected(PlanningRequest request) {
        return selected(request, arguments(plan(8, false, AdvancePlan.ClockMode.CAMPAIGN_SENTINEL, true)), "life-advance", false, EMPTY);
    }

    private static PlanningResult.ActionSelected selected(PlanningRequest request, Obj args, String operation,
            boolean wrongExpected, Claims claims) {
        AdvancePlan expectedPlan = plan(8, false, AdvancePlan.ClockMode.CAMPAIGN_SENTINEL, true);
        try { expectedPlan = AdvancePlan.decode(object(args.get(AdvancePlan.KEY), "advance")); }
        catch (IllegalArgumentException malformedUnsupportedFixture) { /* malformed plans test legacy fallback */ }
        ExpectedPostcondition expected = new ExpectedPostcondition(1, request.before(), request.source(),
                wrongExpected ? "fixture-wrong-observer/v1" : AdvancePlan.OBSERVER, expectedPlan.expected());
        ActionCommand command = new ActionCommand("compact-fixture-action", request.before(), request.source(), request.sessionId(),
                new OperationKey(operation), args, expected, claims, request.deadline());
        OrdinaryPolicy.Draft draft = new OrdinaryPolicy.Draft("business-policy", "business-phase", "business reason retained",
                OrdinaryPolicy.Kind.ORDINARY, Optional.of(command), OrdinaryPolicy.Purpose.DATE_ADVANCE,
                Optional.of(Domain.lifestyle), args.get("plan") instanceof Obj detail ? detail : selectedDetail(operation));
        List<PlanTrace.StageVisit> visits = List.of(
                new PlanTrace.StageVisit(PlanningStage.CROWN_AUTHORITY, PlanTrace.Outcome.KEPT, "first business visit",
                        Optional.of(PlanningFixtures.SOURCE), Optional.of(EVIDENCE)),
                new PlanTrace.StageVisit(PlanningStage.CAMPAIGN_ADVANCE_CAP, PlanTrace.Outcome.REPLACED, "campaign bound retained",
                        Optional.empty(), Optional.of(obj("unknown_business", new Text("second-evidence")))));
        return new PlanningResult.ActionSelected(command, new PlanTrace(request.before(), visits, Optional.of(draft)));
    }

    private static Obj arguments(AdvancePlan plan) {
        return obj(AdvancePlan.KEY, plan.json(), "plan", selectedDetail("life-advance"),
                "original_unknown_argument", obj("text", new Text("retain-original-proposal")));
    }

    private static Obj selectedDetail(String operation) {
        return obj("selected_step", new Text(operation), "policy", new Text("business-policy"),
                "phase", new Text("business-phase"), "reason", new Text("business reason retained"),
                "complete_business_detail", EVIDENCE);
    }
}
