package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual native fixture producer -> complete Java query decoder. Synthetic memory, zero Game credit. */
final class GuardianOutgoingCodecTest {
    private static final String PREFIX="FIXTURE_QUERY_GUARDIAN_AVAILABLE ";
    private static ObjectNode original;
    private static final long ACTOR=0x01000001L, RECIPIENT=0xFE000002L;
    private static Context context() {
        Instant now=Instant.parse("2026-10-24T00:00:00Z");
        G2Source source=new G2Source("synthetic-guardian-machine",now.toString(),Build.CROZIER4.version(),
                new ExactRef("synthetic/source",1,"a".repeat(64)));
        var game=new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001")));
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(ACTOR),
                BigInteger.valueOf(7),BigInteger.valueOf(53146848)),"native:7",BigInteger.valueOf(56),"synthetic-text");
        return new Context(new ObservationIdentity(source.machineId(),game,frame,1),source,"synthetic-guardian-session",
                BigInteger.TWO,Build.CROZIER4,now.plusSeconds(30),new ControlFrame(true,true,true,1,19L,
                ACTOR,"synthetic-guardian-episode",false,null,null,List.of()));
    }
    private static OrdinaryRequest request() {
        return new OrdinaryRequest(new InteractionKey("educate_child_interaction"),new CharacterId(RECIPIENT),
                Optional.of(new EducationIntent(Optional.of(new CharacterId(303)),Optional.of(new CharacterId(202)),
                        Optional.of(List.of(new InteractionKey("fixture_flag"))))));
    }
    @BeforeAll static void originalNativeProductionSerializer() throws Exception {
        verifyPins();
        Path executable=verifiedFixtureExecutable();
        Process process=new ProcessBuilder(executable.toString()).redirectErrorStream(true).start();
        if(!process.waitFor(30,TimeUnit.SECONDS)) { process.destroyForcibly(); throw new AssertionError("native production fixture timeout"); }
        byte[] bytes=process.getInputStream().readNBytes(1_048_577);
        String output=new String(bytes,StandardCharsets.UTF_8);
        assertEquals(0,process.exitValue(),output); assertTrue(bytes.length<=1_048_576,"native fixture output bound");
        List<String> packets=output.lines().filter(line->line.startsWith(PREFIX)).toList();
        assertEquals(1,packets.size(),"fixture must emit one actual serializer guardian packet");
        original=(ObjectNode)NativeWire.parse(packets.getFirst().substring(PREFIX.length()).getBytes(StandardCharsets.UTF_8));
        assertEquals(executable,verifiedFixtureExecutable(),"fixture path/pin must remain exact after execution");
        verifyPins();
    }
    @Test void nativeStoragePacketToFullQueryAndTypedObserverPreservesGenerationAndDuplicateBanks() {
        var query=OrdinaryInteractionCodec.query(raw(original),context(),request());
        assertTrue(query.availability().available()); assertTrue(query.readyToInitiate());
        var snapshot=GuardianOutgoingCodec.decode(raw(original),context(),request());
        assertTrue(snapshot.complete()); assertEquals(2,snapshot.scannedSlots().orElseThrow());
        assertEquals(FamilyOutgoingCodec.Profile.EDUCATE_CHILD,snapshot.profile());
        assertEquals(List.of(0L,0xFE000001L),snapshot.occupiedPendingIds(),"inactive native ID zero remains occupied");
        assertEquals(1,snapshot.candidates().size()); var candidate=snapshot.candidates().getFirst();
        assertEquals(0xFE000001L,candidate.pendingFullId()); assertTrue(candidate.knownActiveRoute());
        assertEquals(303L,candidate.roles().secondaryRecipient().longValue()); assertEquals(202L,candidate.roles().secondaryActor().longValue());
        assertNull(candidate.roles().intermediary()); assertEquals(19,candidate.options().get(0).flag());
        assertEquals(19,candidate.options().get(1).flag()); assertEquals(1,candidate.options().get(0).bankByte());
        assertEquals(0,candidate.options().get(1).bankByte());
        assertTrue(query.educationOptions().orElseThrow().rows().get(1).selected(),"getter uses first equal flag, raw ordinal bank remains independent");
        assertArrayEquals(raw(original).bytes(),GuardianOutgoingCodec.encodeOriginal(raw(original),snapshot,context(),request()).bytes());
    }
    @Test void incompleteCompleteAbsentAndAmbiguousRemainDistinctObservations() {
        ObjectNode absent=original.deepCopy(); group(absent).putArray("candidates");
        var negative=GuardianOutgoingCodec.decode(raw(absent),context(),request());
        assertTrue(negative.complete()); assertTrue(negative.candidates().isEmpty());
        ObjectNode unavailable=original.deepCopy(); group(unavailable).put("status","unavailable").put("complete",false)
                .put("passes",0).putNull("scanned_slots").putNull("definition_stable_hash").putNull("sender_character_id").put("unavailable_reason","storage_changed");
        group(unavailable).putArray("candidates"); group(unavailable).putArray("occupied_pending_full_ids");
        var unknown=GuardianOutgoingCodec.decode(raw(unavailable),context(),request());
        assertFalse(unknown.complete()); assertEquals(Optional.of("storage_changed"),unknown.unavailableReason());
        ObjectNode ambiguous=original.deepCopy(); ObjectNode second=candidate(ambiguous).deepCopy().put("pending_full_id",0xFD000000L);
        ((com.fasterxml.jackson.databind.node.ArrayNode)group(ambiguous).get("candidates")).insert(0,second);
        group(ambiguous).putArray("occupied_pending_full_ids").add(0xFD000000L).add(0xFE000001L);
        var multiple=GuardianOutgoingCodec.decode(raw(ambiguous),context(),request());
        assertTrue(multiple.complete()); assertEquals(2,multiple.candidates().size());
        ObjectNode unknownRoute=original.deepCopy(); candidate(unknownRoute).put("route_kind",1);
        assertFalse(GuardianOutgoingCodec.decode(raw(unknownRoute),context(),request()).candidates().getFirst().knownActiveRoute());
    }
    @Test void queryRequiresVersionedGroupAndInitiationPreflightExplicitlyForbidsIt() {
        ObjectNode old=original.deepCopy(); payload(old).remove(FamilyOutgoingCodec.GROUP);
        assertThrows(IllegalArgumentException.class,()->OrdinaryInteractionCodec.query(raw(old),context(),request()));
        assertTrue(OrdinaryInteractionCodec.context(payload(old),context(),request(),BigInteger.valueOf(47)).availability().available());
        assertThrows(IllegalArgumentException.class,()->OrdinaryInteractionCodec.context(payload(original),context(),request(),BigInteger.valueOf(47)));
    }
    @Test void familyArgumentsUseTheSameTypedProducerAndPreserveAbsentVersusExplicitEmptyOptions() {
        ObjectNode args=InteractionJson.F.objectNode().put("interaction_key","educate_child_interaction")
                .put("recipient_id",RECIPIENT).put("expected_revision",56);
        var absent=FamilyEducationNativeProjection.intent(context(),app(args));
        assertTrue(absent.education().orElseThrow().options().isEmpty());
        args.put("child_full_id",303).put("guardian_full_id",202).putArray("requested_option_keys");
        var empty=FamilyEducationNativeProjection.intent(context(),app(args));
        assertEquals(Optional.of(List.of()),empty.education().orElseThrow().options());
        var actual=FamilyEducationNativeProjection.applicationArguments(context(),app(args));
        assertEquals(empty,InteractionArguments.ordinary(InteractionArguments.parseApp(actual)));
        ObjectNode missing=args.deepCopy(); missing.remove("guardian_full_id");
        assertThrows(IllegalArgumentException.class,()->FamilyEducationNativeProjection.intent(context(),app(missing)));
        ObjectNode wrong=args.deepCopy().put("expected_revision",7);
        assertThrows(IllegalArgumentException.class,()->FamilyEducationNativeProjection.intent(context(),app(wrong)));
        ObjectNode bool=args.deepCopy().put("child_full_id",true);
        assertThrows(IllegalArgumentException.class,()->FamilyEducationNativeProjection.intent(context(),app(bool)));
        ObjectNode nullOptions=args.deepCopy().putNull("requested_option_keys");
        assertThrows(IllegalArgumentException.class,()->FamilyEducationNativeProjection.intent(context(),app(nullOptions)));
    }
    @Test void closedFieldsExactIntegersSenderAndCompleteDoubleReadAreEnforced() {
        ObjectNode bool=original.deepCopy(); candidate(bool).put("pending_full_id",true); reject(bool);
        ObjectNode floating=original.deepCopy(); candidate(floating).put("pending_full_id",4261412865.0); reject(floating);
        ObjectNode missing=original.deepCopy(); candidate(missing).remove("selected_option_rows"); reject(missing);
        ObjectNode truncated=original.deepCopy(); group(truncated).put("passes",1); reject(truncated);
        ObjectNode sender=original.deepCopy(); ((ObjectNode)candidate(sender).get("effective_roles")).put("actor_id",999); reject(sender);
        ObjectNode scope=original.deepCopy(); group(scope).put("producer_scope","received_only"); reject(scope);
        ObjectNode extra=original.deepCopy(); group(extra).put("linked_to_host_request",true); reject(extra);
        ObjectNode partial=original.deepCopy(); group(partial).put("status","unavailable").put("complete",false)
                .put("passes",0).putNull("scanned_slots").put("unavailable_reason","not_complete"); reject(partial);
        ObjectNode missingOccupied=original.deepCopy(); group(missingOccupied).remove("occupied_pending_full_ids"); reject(missingOccupied);
        ObjectNode foreignCandidate=original.deepCopy(); group(foreignCandidate).putArray("occupied_pending_full_ids").add(0); reject(foreignCandidate);
        ObjectNode duplicateSlot=original.deepCopy(); group(duplicateSlot).putArray("occupied_pending_full_ids").add(0xFD000001L).add(0xFE000001L); reject(duplicateSlot);
        ObjectNode unknownSixth=original.deepCopy(); ((ObjectNode)payload(unknownSixth).get("effective_roles")).put("sixth_role_id",404); reject(unknownSixth);
        ObjectNode oldAlias=original.deepCopy(); payload(oldAlias).set("guardian_outgoing_requests",payload(oldAlias).remove(FamilyOutgoingCodec.GROUP)); reject(oldAlias);
        ObjectNode wrongPair=original.deepCopy(); ((ObjectNode)payload(wrongPair).get("education_request_materialization")).put("child_full_id",999); reject(wrongPair);
    }
    @Test void reconciliationContextIsExplicitAndDoesNotAuthorizeGameplayBefore() {
        var context=context(); var args=InteractionArguments.body(context); InteractionArguments.ordinary(args,request());
        var pending=new org.xar.ck3.control.application.action.ReconciliationIdentity.Pending("synthetic-action","1".repeat(64),"original-submission",
                context.before(),ref("original-receipt",1),ref("original-driver",2));
        var evidence=new org.xar.ck3.control.application.action.ReconciliationIdentity.Evidence(ref("current-native",3),ref("current-hello",4),
                ref("original-heartbeat",5),ref("current-observation",6),ref("current-driver",2),ref("current-source",7));
        var identity=new org.xar.ck3.control.application.action.ReconciliationIdentity(context.before(),context.source(),context.sessionId(),
                context.connectionGeneration(),pending,evidence,Instant.parse("2026-10-24T00:00:00Z"));
        var request=org.xar.ck3.control.application.action.PlanningReadRequest.newReconciliation(identity,
                new org.xar.ck3.control.application.action.OperationKey(OrdinaryInteractionCodec.QUERY_STEP),InteractionArguments.app(args),context.deadline());
        assertThrows(IllegalStateException.class,request::before);
        assertEquals(context,InteractionArguments.context(request));
    }
    @Test void originalPythonNormalizerAcceptsPriorPacketAndExplicitlyRejectsVersionedExtension() throws Exception {
        String script="""
                import copy,json,pathlib,sys
                root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                from xar_autoplayer.bridge.ordinary_interaction_contract import normalize_native_query
                value=json.loads(sys.argv[2]);binding={'native_revision':7,'date_raw':53146848,'game_pid':991,'connection_generation':2,'played_character_id':16777217,'active_event_present':False,'incoming_interaction_present':False}
                old=copy.deepcopy(value);del old['character_interaction_ordinary_context']['family_outgoing_requests']
                parsed=normalize_native_query(old,binding,'educate_child_interaction',4261412866)
                try:normalize_native_query(value,binding,'educate_child_interaction',4261412866)
                except ValueError:rejected=True
                else:rejected=False
                print(json.dumps({'original_accepted':parsed==old,'new_group_rejected':rejected},sort_keys=True))
                """;
        var builder=new ProcessBuilder(required("xar.python"),"-B","-c",script,required("xar.repository.root"),original.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1"); builder.redirectErrorStream(true);
        Process process=builder.start();
        if(!process.waitFor(30,TimeUnit.SECONDS)) { process.destroyForcibly(); throw new AssertionError("original Python parser timeout"); }
        byte[] output=process.getInputStream().readNBytes(65_537); assertEquals(0,process.exitValue(),new String(output,StandardCharsets.UTF_8));
        assertTrue(output.length<=65_536); JsonNode result=NativeWire.parse(output);
        assertTrue(result.get("original_accepted").booleanValue()); assertTrue(result.get("new_group_rejected").booleanValue()); verifyPins();
    }
    private static void reject(ObjectNode value) { assertThrows(IllegalArgumentException.class,()->GuardianOutgoingCodec.decode(raw(value),context(),request())); }
    private static ObjectNode payload(ObjectNode value) { return (ObjectNode)value.get("character_interaction_ordinary_context"); }
    private static ObjectNode group(ObjectNode value) { return (ObjectNode)payload(value).get(FamilyOutgoingCodec.GROUP); }
    private static ObjectNode candidate(ObjectNode value) { return (ObjectNode)group(value).get("candidates").get(0); }
    private static RawJson raw(JsonNode value) { return new RawJson(value.toString().getBytes(StandardCharsets.UTF_8)); }
    private static OpportunityJson.Obj app(JsonNode value) { return OpportunityJson.object(OpportunityJson.parse(raw(value).bytes()),"family arguments"); }
    private static String required(String key) { String value=System.getProperty(key); assertNotNull(value,"required CI property: "+key); assertFalse(value.isBlank()); return value; }
    private static ExactRef ref(String path,int digit) { return new ExactRef("synthetic/"+path,1,Integer.toHexString(digit).repeat(64)); }
    private static Path verifiedFixtureExecutable() throws Exception {
        Path path=Path.of(required("xar.guardian.outgoing.native.fixture")).toAbsolutePath().normalize();
        String expected=required("xar.guardian.outgoing.native.fixture.sha256");assertTrue(expected.matches("[0-9a-f]{64}"),"canonical lowerhex fixture SHA256 required");
        long bytes=Files.size(path);assertTrue(bytes>0 && bytes<=67_108_864,"bounded actual fixture executable required");
        var digest=MessageDigest.getInstance("SHA-256");try(var stream=Files.newInputStream(path)) {byte[] chunk=new byte[8192];int count;while((count=stream.read(chunk))>=0)if(count>0)digest.update(chunk,0,count);}
        assertEquals(expected,HexFormat.of().formatHex(digest.digest()),"exact measured fixture executable changed");return path;
    }
    private static void verifyPins() throws Exception {
        pin("ck3_autonomous_player/src/xar_autoplayer/bridge/ordinary_interaction_contract.py",31161,"ba0c169f6eef192f5494da4b553d3782d5d89eb15e091c2658f7171af1695ee1");
        pin("ck3_autonomous_player/native_bridge/src/pending_character_interaction_context_v1.cpp",64872,"268da0a9d77771fffca4ccc9f3db4d90dfcc3f182d96e547fa8ee8a7d1db9b23");
        pin("ck3_autonomous_player/native_bridge/src/ck3_12004_family_actions.cpp",2963,"e8518eb8227f16590d30cb61dfda77f89baa6cf5380cfc44378ce979be321588");
    }
    private static void pin(String relative,long length,String sha) throws Exception {
        byte[] body=Files.readAllBytes(Path.of(required("xar.repository.root")).resolve(relative));
        assertEquals(length,body.length,relative); assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)),relative);
    }
}
