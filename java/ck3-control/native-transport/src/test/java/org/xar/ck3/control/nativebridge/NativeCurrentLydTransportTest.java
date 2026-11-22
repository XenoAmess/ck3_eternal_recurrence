package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** NoGame port consumes retained C++ tokens. Changed envelopes and explicitly named mutations below are Java DATA, not new Native frames. */
class NativeCurrentLydTransportTest {
    static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    static final CurrentLyd.PersonalKey PERSONAL=CurrentLyd.PersonalKey.REVERENT_HEAVEN;
    static ObjectNode envelope(String name)throws IOException{
        try(var in=NativeCurrentLydTransportTest.class.getResourceAsStream("/current267-lyd-cpp-a749/"+name+".json")){
            if(in==null)throw new IOException("Retained actual LYD resource missing: "+name);return NativeWire.object(NativeWire.parse(in.readAllBytes()));
        }
    }
    static ObjectNode token(String name)throws IOException{return NativeWire.object(envelope(name).get("result"));}
    static ObjectNode branch(ObjectNode token){var s=token.get("source");return (ObjectNode)s.get(s.get("kind").textValue());}
    static CoreFrame.Partial actualCore()throws IOException{return new CoreFrame.Partial(BUILD,CurrentLydResult.decode(new RawJson(StrictJson.canonical(token("personal-query")))).factsBefore().orElseThrow());}
    static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\lyd-data","lyd-data",GAME,"lyd-session","lyd-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),1024,32);}
    static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(30)));}
    static NativeGameTransport.LydReceived query(NativeGameTransport t,CurrentLyd.Action action,CurrentLyd.Target target)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.LydReceived.class,t.readCurrentLyd(c,action,target,c.validUntil()));}
    static NativeGameTransport.LydReceived personal(NativeGameTransport t)throws Exception{return query(t,CurrentLyd.Action.QUERY_PERSONAL,CurrentLyd.Target.personal(PERSONAL));}
    static NativeGameTransport.LydPrepared select(NativeGameTransport t)throws Exception{return t.prepareCurrentLydCandidate(personal(t),PERSONAL);}

    @Test void candidateUsesPrivateActualRowTokenAndOriginalOncePacket()throws Exception{
        var r=new Replay("capture");try(var t=transport(r)){var q=personal(t);var p=t.prepareCurrentLydCandidate(q,PERSONAL);assertSame(p,t.prepareCurrentLydCandidate(q,PERSONAL));
            var req=NativeWire.decodeExecuteRequest(p.originalPacket().value());var fields=NativeWire.parse(req.normalizedAdditionalFields().value());var claim=fields.get("lyd");
            assertEquals(14,claim.size());assertEquals("lyd.native.row.a",claim.get("choice_token").textValue());assertEquals(PERSONAL.wire(),claim.get("personal_key").textValue());assertEquals(q.validUntil(),p.deadline());assertEquals(p.deadline().toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());
            var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLyd(p));assertSame(out,t.submitCurrentLyd(p));assertEquals(CurrentLydResult.decodeOutcome(out),p.latestFrame().orElseThrow());assertEquals(1,r.effectWrites);assertFalse(p.latestFrame().orElseThrow().nativeHandled());}
    }
    @Test void personalAddUsesSameReceiverFreshCoreAndOriginalSelectionDeadlineAcrossSixSubmissions()throws Exception{
        var r=new Replay("capture");try(var t=transport(r)){var p=select(t);assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLyd(p));var after=core(t);
            var add=assertInstanceOf(NativeGameTransport.LydReceived.class,t.readCurrentLydAddConfirmation(after,p));assertEquals(p.deadline(),add.validUntil());
            var confirm=t.prepareCurrentLydPersonalAdd(add,p);assertEquals(p.target().personalKey(),confirm.target().personalKey());assertEquals(p.deadline(),confirm.deadline());
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLyd(confirm));assertEquals(CurrentLydResult.Status.CONFIRMATION_DISPATCHED,CurrentLydResult.decodeOutcome(ack).status());assertSame(ack,t.submitCurrentLyd(confirm));assertEquals(6,r.writes);assertEquals(2,r.effectWrites);
            assertEquals(p.deadline().toEpochMilli(),r.selectDeadline);assertEquals(r.selectDeadline,r.addDeadline);assertEquals(r.addDeadline,r.confirmDeadline);assertFalse(CurrentLydResult.decodeOutcome(ack).nativeHandled());}
    }
    @Test void callerCannotRecoverSelectionAcrossConnectionOrUseStandaloneAddQuery()throws Exception{
        var a=new Replay("known");var b=new Replay("known");try(var t=transport(a);var other=transport(b)){var p=select(t);assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLyd(p));var fresh=core(t);var foreign=core(other);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.readCurrentLydAddConfirmation(foreign,p).original());
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentLydAddConfirmation(foreign,p).original());
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentLyd(fresh,CurrentLyd.Action.QUERY_ADD_CONFIRMATION,CurrentLyd.Target.personal(PERSONAL),p.deadline()).original());assertEquals(0,a.addQueries);assertEquals(0,b.addQueries);}
    }
    @Test void addRequiresCoreObservedAfterSelectionAndSameFullPrefix()throws Exception{
        for(String mode:List.of("known","changed-after-core")){var r=new Replay(mode);try(var t=transport(r)){var before=core(t);var q=assertInstanceOf(NativeGameTransport.LydReceived.class,t.readCurrentLyd(before,CurrentLyd.Action.QUERY_PERSONAL,CurrentLyd.Target.personal(PERSONAL),before.validUntil()));var p=t.prepareCurrentLydCandidate(q,PERSONAL);assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLyd(p));
            var after=mode.equals("known")?before:core(t);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentLydAddConfirmation(after,p).original());assertEquals(0,r.addQueries);assertEquals(1,r.effectWrites);
        }}
    }
    @Test void foreignQueriesAndChangedTargetsCannotBorrowAnActualLease()throws Exception{
        var a=new Replay("known");var b=new Replay("known");try(var t=transport(a);var other=transport(b)){var q=personal(t);assertThrows(IOException.class,()->other.prepareCurrentLydCandidate(q,PERSONAL));assertThrows(IOException.class,()->t.prepareCurrentLydCandidate(q,CurrentLyd.PersonalKey.KNOWING_ACTING_SUPPORT));
            var p=t.prepareCurrentLydCandidate(q,PERSONAL);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentLyd(p));assertEquals(0,a.effectWrites);assertEquals(0,b.effectWrites);}
    }
    @Test void actualCanFalseEmptyEventOrMissingCandidateCannotMintEffects()throws Exception{
        for(String mode:List.of("can-false","unmaterialized")){var r=new Replay(mode);try(var t=transport(r)){var q=personal(t);assertThrows(IOException.class,()->t.prepareCurrentLydCandidate(q,PERSONAL));assertEquals(0,r.effectWrites);}}
        var r=new Replay("empty-events");try(var t=transport(r)){var q=query(t,CurrentLyd.Action.QUERY_EVENTS,CurrentLyd.Target.none());assertTrue(q.frame().source().orElseThrow().events().orElseThrow().events().isEmpty());assertThrows(IOException.class,()->t.prepareCurrentLydEvent(q,CurrentLyd.EventRole.RITUAL_MUSIC_PAY));}
    }
    @Test void completeEventsChooseOneActualSemanticRoleAndNeverAnOrdinal()throws Exception{
        var r=new Replay("capture");try(var t=transport(r)){var q=query(t,CurrentLyd.Action.QUERY_EVENTS,CurrentLyd.Target.none());var p=t.prepareCurrentLydEvent(q,CurrentLyd.EventRole.RITUAL_MUSIC_PAY);assertEquals(7,p.target().instanceId().orElseThrow());assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLyd(p));assertEquals(1,r.effectWrites);}
        for(String mode:List.of("duplicate-event-role","wrong-event-actor","event-can-false")){var x=new Replay(mode);try(var t=transport(x)){var q=query(t,CurrentLyd.Action.QUERY_EVENTS,CurrentLyd.Target.none());assertThrows(IOException.class,()->t.prepareCurrentLydEvent(q,CurrentLyd.EventRole.RITUAL_MUSIC_PAY));assertEquals(0,x.effectWrites);}}
    }
    @Test void beginDecisionRemainsReadonlyAndDetailConfirmUseTheirActualStates()throws Exception{
        var r=new Replay("capture");try(var t=transport(r)){var q=query(t,CurrentLyd.Action.QUERY_DECISIONS,CurrentLyd.Target.none());assertThrows(IOException.class,()->t.prepareCurrentLydDecision(q,CurrentLyd.Action.CONFIRM_DECISION,CurrentLyd.DecisionKey.BEGIN_READONLY));var p=t.prepareCurrentLydDecision(q,CurrentLyd.Action.OPEN_DETAIL,CurrentLyd.DecisionKey.ENTRY);assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLyd(p));}
        var x=new Replay("selected-decision");try(var t=transport(x)){var q=query(t,CurrentLyd.Action.QUERY_DECISIONS,CurrentLyd.Target.none());var p=t.prepareCurrentLydDecision(q,CurrentLyd.Action.CONFIRM_DECISION,CurrentLyd.DecisionKey.ENTRY);assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLyd(p));}
    }
    @Test void realToggleHandledTrueAndFalseBothRemainKnownDispatchedWithoutAutomaticReopen()throws Exception{
        for(String mode:List.of("toggle-true","toggle-false")){var r=new Replay(mode);try(var t=transport(r)){var q=query(t,CurrentLyd.Action.QUERY_DECISIONS,CurrentLyd.Target.none());var p=t.prepareCurrentLyd(q,CurrentLyd.Action.OPEN_LIST);var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLyd(p));assertTrue(CurrentLydResult.decodeOutcome(ack).successful());assertEquals(!mode.equals("toggle-false"),p.latestFrame().orElseThrow().nativeHandled());assertSame(ack,t.submitCurrentLyd(p));assertEquals(1,r.effectWrites);}}
        for(String mode:List.of("hidden-personal","start-add")){var r=new Replay(mode);try(var t=transport(r)){var q=personal(t);var p=t.prepareCurrentLyd(q,mode.equals("hidden-personal")?CurrentLyd.Action.OPEN_PERSONAL:CurrentLyd.Action.START_ADD_PERSONAL);assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLyd(p));assertEquals(1,r.effectWrites);}}
    }
    @Test void leaseCapabilityDeadlineAndLatestActualQueryAreRequiredBeforeWrite()throws Exception{
        var r=new Replay("missing-effects");try(var t=transport(r)){var q=personal(t);assertThrows(IOException.class,()->t.prepareCurrentLydCandidate(q,PERSONAL));}
        var x=new Replay("known");try(var t=transport(x)){var c=core(t);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentLyd(c,CurrentLyd.Action.QUERY_PERSONAL,CurrentLyd.Target.personal(PERSONAL),c.validUntil().plusMillis(1)).original());assertEquals(0,x.queries);
            var q=assertInstanceOf(NativeGameTransport.LydReceived.class,t.readCurrentLyd(c,CurrentLyd.Action.QUERY_PERSONAL,CurrentLyd.Target.personal(PERSONAL),c.validUntil()));var p=t.prepareCurrentLydCandidate(q,PERSONAL);
            assertInstanceOf(NativeGameTransport.LydReceived.class,t.readCurrentLyd(c,CurrentLyd.Action.QUERY_PERSONAL,CurrentLyd.Target.personal(PERSONAL),c.validUntil()));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitCurrentLyd(p));assertEquals(0,x.effectWrites);}
    }
    @Test void knownSpentClaimRefusalRemainsZeroEffectAndOriginalPreparationCannotReplay()throws Exception{
        var r=new Replay("refused");try(var t=transport(r)){var p=select(t);var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentLyd(p));var f=CurrentLydResult.decodeOutcome(ack);assertFalse(f.successful());assertFalse(f.effectAttempted());assertTrue(f.claimSequence().signum()>0);assertSame(ack,t.submitCurrentLyd(p));assertEquals(1,r.effectWrites);var after=core(t);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentLydAddConfirmation(after,p).original());assertEquals(0,r.addQueries);}
    }
    @Test void lostOrChangedActionReceiptPreservesUnknownAndNeverReplays()throws Exception{
        for(String mode:List.of("lost","wrong-lease","wrong-target","changed-source","wrong-owner","indeterminate")){var r=new Replay(mode);try(var t=transport(r)){var p=select(t);var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentLyd(p));assertSame(unknown,t.submitCurrentLyd(p));assertEquals(1,r.effectWrites);assertFalse(p.latestFrame().isPresent());if(!mode.equals("lost"))assertTrue(t.originalIndeterminateCoreAcknowledgement(unknown.requestId()).isPresent());}}
    }
    @Test void queryReadbackPreservesFourActualResourcesAndUnqualifiedNulls()throws Exception{
        var r=new Replay("capture");try(var t=transport(r)){var q=query(t,CurrentLyd.Action.QUERY_READBACK,CurrentLyd.Target.none());var s=q.frame().source().orElseThrow().readback().orElseThrow();assertEquals(-9223372036854775807L,s.resources().orElseThrow().personalGoldRaw());assertEquals(Long.MAX_VALUE,s.resources().orElseThrow().prestigeRaw());assertTrue(s.legitimacyRaw().isEmpty());assertFalse(s.originalCaseReadbackComplete());assertEquals(0,r.effectWrites);}
    }

    static final class Replay implements NativePacketPort {
        final String mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed;int writes,queries,effectWrites,coreWrites,addQueries;long selectDeadline,addDeadline,confirmDeadline;ObjectNode lastPersonalQuery;
        Replay(String mode)throws IOException{
            this.mode=mode;var f=CurrentLydResult.decode(new RawJson(StrictJson.canonical(token("personal-query"))));var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",f.owner().orElseThrow().connectionGeneration()).put("bridge_version","lyd-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY);for(var a:CurrentLyd.Action.values())if(a.isQuery()||!mode.equals("missing-effects"))caps.add(a.capability());packets.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("LYD DATA port closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("LYD DATA response missing");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException{
            verify();writes++;var req=NativeWire.decodeExecuteRequest(packet);ObjectNode result;boolean ok=true;
            if(req.step().equals(CoreFrame.STEP)){coreWrites++;result=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(actualCore()).bytes()));if(mode.equals("changed-after-core")&&coreWrites>1)result.put("date_raw",actualCore().prefix().dateRaw()+24);}
            else{
                var fields=NativeWire.parse(req.normalizedAdditionalFields().value());var claim=fields.get("lyd");var a=CurrentLyd.Action.parse(claim.get("action").textValue());retain(a,packet);
                if(a.isQuery()){queries++;assertEquals("0",claim.get("provider_generation").textValue());String file=switch(a){case QUERY_DECISIONS->mode.equals("hidden-list")||mode.equals("toggle-true")||mode.equals("toggle-false")?"decisions-hidden":"decisions-query";case QUERY_EVENTS->mode.equals("empty-events")?"events-empty":"events-query";case QUERY_PERSONAL->mode.equals("can-false")?"personal-can-false":"personal-query";case QUERY_ADD_CONFIRMATION->"add-modal-query";case QUERY_READBACK->"readback-resources";default->throw new IOException("Unexpected query");};result=token(file);
                    if(a==CurrentLyd.Action.QUERY_ADD_CONFIRMATION){addQueries++;addDeadline=fields.get("core_control_deadline_unix_ms").longValue();}
                    if(a==CurrentLyd.Action.QUERY_DECISIONS&&mode.equals("selected-decision")){result=token("decision-confirm");queryResult(result,a);}
                    if(a==CurrentLyd.Action.QUERY_EVENTS){if(mode.equals("duplicate-event-role")){var rows=(com.fasterxml.jackson.databind.node.ArrayNode)branch(result).get("events");var copy=(ObjectNode)rows.get(0).deepCopy();copy.put("instance_id",8);rows.add(copy);branch(result).put("named_root_count",2);}if(mode.equals("wrong-event-actor"))((ObjectNode)branch(result).get("events").get(0)).put("recipient_character_id",123);if(mode.equals("event-can-false"))((ObjectNode)branch(result).get("events").get(0).get("options").get(0)).put("native_can_select",false);}
                    if(a==CurrentLyd.Action.QUERY_PERSONAL){var s=branch(result);if(mode.equals("unmaterialized")){s.put("window_visible",false).put("model_materialized",false).put("slots_complete",false).put("groups_complete",false).put("empty_slot_found",false).putNull("slot_count").putNull("group_count");s.putArray("slots");s.putArray("rows");}
                        if(mode.equals("hidden-personal")||mode.equals("start-add")){s.put("is_adding",false);for(var row:s.get("rows"))((ObjectNode)row).put("select_admissible",false);if(mode.equals("hidden-personal"))s.put("window_visible",false).put("native_window_visible",false).put("open_admissible",true);else s.put("start_add_admissible",true);}lastPersonalQuery=result.deepCopy();}
                }else{effectWrites++;if(mode.equals("lost"))return;String file=switch(a){case OPEN_LIST->"decisions-open-list";case OPEN_DETAIL->"decision-detail";case CONFIRM_DECISION->"decision-confirm";case CHOOSE_KNOWN_EVENT_OPTION->"event-choose-pay";case SELECT_PERSONAL_CANDIDATE->mode.equals("refused")?"select-refused-spent-claim":mode.equals("indeterminate")?"select-indeterminate":"personal-select";case CONFIRM_PERSONAL_ADD->"add-modal-confirm";case OPEN_PERSONAL,START_ADD_PERSONAL->"personal-query";default->throw new IOException("Unexpected effect");};result=token(file);
                    if(a==CurrentLyd.Action.SELECT_PERSONAL_CANDIDATE)selectDeadline=fields.get("core_control_deadline_unix_ms").longValue();if(a==CurrentLyd.Action.CONFIRM_PERSONAL_ADD)confirmDeadline=fields.get("core_control_deadline_unix_ms").longValue();
                    if(a==CurrentLyd.Action.OPEN_PERSONAL||a==CurrentLyd.Action.START_ADD_PERSONAL){result=lastPersonalQuery.deepCopy();result.put("action",a.wire()).put("status",CurrentLydResult.dispatchedStatus(a).wire()).put("claim_sequence","1").put("effect_attempted",true).put("native_returned",true).put("native_handled",a==CurrentLyd.Action.OPEN_PERSONAL);}
                    if(mode.equals("toggle-true"))result.put("native_handled",true);if(mode.equals("toggle-false"))result.put("native_handled",false);if(mode.equals("wrong-lease"))result.put("query_sequence","1");if(mode.equals("wrong-target"))result.put("personal_key",CurrentLyd.PersonalKey.KNOWING_ACTING_SUPPORT.wire());if(mode.equals("changed-source"))branch(result).put("spiritual_fulfillment_raw","123");if(mode.equals("wrong-owner"))((ObjectNode)result.get("owner")).put("connection_generation","8");
                    ok=CurrentLydResult.decode(new RawJson(StrictJson.canonical(result))).successful();
                }
            }
            var e=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",req.requestId()).put("ok",ok);e.set("result",result);packets.add(NativeWire.packet(StrictJson.canonical(e)));
        }
        static void queryResult(ObjectNode r,CurrentLyd.Action a){r.put("action",a.wire()).put("status","available").put("claim_sequence","0").put("effect_attempted",false).put("native_returned",false).put("native_handled",false);r.putNull("decision_key");}
        static void retain(CurrentLyd.Action action,byte[] packet)throws IOException{String dir=System.getProperty("xar.current267.lyd.java.requests");if(dir==null)return;var root=java.nio.file.Path.of(dir).toAbsolutePath().normalize();if(!root.getRoot().toString().equalsIgnoreCase("D:\\"))throw new IOException("D request evidence required");java.nio.file.Files.createDirectories(root);var p=root.resolve(action.wire()+".request.json");if(!java.nio.file.Files.exists(p))java.nio.file.Files.write(p,Arrays.copyOfRange(packet,4,packet.length),java.nio.file.StandardOpenOption.CREATE_NEW);}
        public void close(){closed=true;}
    }
}
