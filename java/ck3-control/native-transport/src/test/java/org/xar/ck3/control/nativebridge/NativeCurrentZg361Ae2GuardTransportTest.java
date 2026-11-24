package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Generated Java DATA only: tests real transport authority, never C++/Game/fee evidence. */
final class NativeCurrentZg361Ae2GuardTransportTest {
    private static final BigInteger Z=BigInteger.ZERO,O=BigInteger.ONE,T=BigInteger.TWO;
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static NativeGameTransport transport(DataPort p){return new NativeGameTransport(p,new NativePipeEndpoint.Config("\\\\.\\pipe\\zg361-ae2-generated-DATA","zg361-ae2-data",GAME,"zg361-ae2-DATA-session","zg361-ae2-DATA",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),128,512);}
    private static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(30)));}
    private static void begin(NativeGameTransport t)throws Exception{t.beginCurrentZg361Ae2Case(core(t));}
    private static NativeGameTransport.Zg361Ae2Received query(NativeGameTransport t,CurrentZg361Ae2.Action a)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.Zg361Ae2Received.class,t.readCurrentZg361Ae2(c,a,c.validUntil()));}
    private static NativeGameTransport.Zg361Ae2Prepared action(NativeGameTransport t,CurrentZg361Ae2.Action a)throws Exception{
        var q=query(t,a.sourceKind()==CurrentZg361Ae2Source.Kind.CONTROLS?CurrentZg361Ae2.Action.QUERY_CONTROLS:CurrentZg361Ae2.Action.QUERY_AE2);
        var p=t.prepareCurrentZg361Ae2(q,a);assertSame(p,t.prepareCurrentZg361Ae2(q,a));var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentZg361Ae2(p));assertSame(out,t.submitCurrentZg361Ae2(p));return p;
    }
    private static void present(NativeGameTransport t)throws Exception{
        action(t,CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST);action(t,CurrentZg361Ae2.Action.OPEN_PRESENT_DETAIL);action(t,CurrentZg361Ae2.Action.CONFIRM_PRESENT);
    }
    @Test void foreignReceiverExtendedDeadlineAndOldCoreCannotMintTheOriginalAction()throws Exception{
        var a=new DataPort("normal");var b=new DataPort("normal");try(var t=transport(a);var foreign=transport(b)){
            begin(t);begin(foreign);var q=query(t,CurrentZg361Ae2.Action.QUERY_CONTROLS);
            assertThrows(IOException.class,()->q.requireOriginal(t,q.validUntil().plusMillis(1)));
            assertThrows(IOException.class,()->foreign.prepareCurrentZg361Ae2(q,CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST));
            var p=t.prepareCurrentZg361Ae2(q,CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST);var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentZg361Ae2(p));assertSame(out,t.submitCurrentZg361Ae2(p));
            assertThrows(IOException.class,()->q.requireOriginal(t,q.validUntil()));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,foreign.submitCurrentZg361Ae2(p));
            assertEquals(1,a.effectWrites);assertEquals(0,b.effectWrites);
        }
    }
    @Test void secondListPhaseRequiresOriginalPayAckAndIndependentCompleteAbsence()throws Exception{
        var port=new DataPort("normal");try(var t=transport(port)){
            begin(t);present(t);var pay=action(t,CurrentZg361Ae2.Action.CHOOSE_PAY_NOW);assertEquals(15,port.selectedAuthored);
            var after=query(t,CurrentZg361Ae2.Action.QUERY_AE2);assertTrue(t.currentZg361Ae2EventAbsent(pay,after));
            action(t,CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST);assertEquals(2,port.listOpens);
            action(t,CurrentZg361Ae2.Action.OPEN_VERIFY_DETAIL);action(t,CurrentZg361Ae2.Action.CONFIRM_VERIFY);t.requireCurrentZg361Ae2ZeroDay(core(t));
            assertEquals(7,port.effectWrites);assertEquals(1,port.pays);assertEquals(1,port.verifies);
        }
        var port2=new DataPort("normal");try(var t=transport(port2)){
            begin(t);present(t);action(t,CurrentZg361Ae2.Action.CHOOSE_PAY_NOW);
            var q=query(t,CurrentZg361Ae2.Action.QUERY_CONTROLS);
            assertThrows(IOException.class,()->t.prepareCurrentZg361Ae2(q,CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST));
            assertThrows(IOException.class,()->t.prepareCurrentZg361Ae2(q,CurrentZg361Ae2.Action.OPEN_VERIFY_DETAIL));assertEquals(4,port2.effectWrites);
        }
    }
    @Test void foreignCompleteQueryRemainsDataButCannotAuthorizePayAndChangedCoreStopsBeforeWrite()throws Exception{
        var port=new DataPort("foreign-event");try(var t=transport(port)){
            begin(t);present(t);var q=query(t,CurrentZg361Ae2.Action.QUERY_AE2);var ae=q.frame().source().orElseThrow().events().orElseThrow().ae2().orElseThrow();
            assertEquals(0,ae.recipientCharacterId());assertTrue(ae.tooltipsComplete());assertTrue(ae.options().getFirst().tooltip().contains("\u0000"));
            assertThrows(IOException.class,()->t.prepareCurrentZg361Ae2(q,CurrentZg361Ae2.Action.CHOOSE_PAY_NOW));assertEquals(0,port.pays);
            int before=port.familyWrites;port.actor=42;var changed=core(t);assertInstanceOf(NativeGameTransport.Zg361Ae2Unavailable.class,t.readCurrentZg361Ae2(changed,CurrentZg361Ae2.Action.QUERY_AE2,changed.validUntil()));assertEquals(before,port.familyWrites);
        }
    }
    @Test void knownZeroEffectStaleAckKeepsActualFactsAndOnceWithoutBecomingUnknown()throws Exception{
        var port=new DataPort("known-stale");try(var t=transport(port)){
            begin(t);var q=query(t,CurrentZg361Ae2.Action.QUERY_CONTROLS);var p=t.prepareCurrentZg361Ae2(q,CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST);
            var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentZg361Ae2(p));assertSame(out,t.submitCurrentZg361Ae2(p));
            var frame=p.latestFrame().orElseThrow();assertEquals(CurrentZg361Ae2Result.Status.STALE_SOURCE,frame.status());assertFalse(frame.effectAttempted());assertTrue(frame.cleanupKnown());assertTrue(frame.source().isEmpty());assertEquals(42,frame.factsBefore().orElseThrow().playedCharacterId());
            var fresh=query(t,CurrentZg361Ae2.Action.QUERY_CONTROLS);assertThrows(IOException.class,()->t.prepareCurrentZg361Ae2(fresh,CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST));assertEquals(1,port.effectWrites);
        }
    }
    @Test void lostResultAndValidWholeSourceDriftRemainStickyWithoutAnotherActionWrite()throws Exception{
        for(String mode:List.of("lost-result","changed-before-source")){
            var port=new DataPort(mode);try(var t=transport(port)){
                begin(t);var p=t.prepareCurrentZg361Ae2(query(t,CurrentZg361Ae2.Action.QUERY_CONTROLS),CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST);
                var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentZg361Ae2(p));assertSame(out,t.submitCurrentZg361Ae2(p));
                var c=core(t);var read=assertInstanceOf(NativeGameTransport.Zg361Ae2Unavailable.class,t.readCurrentZg361Ae2(c,CurrentZg361Ae2.Action.QUERY_CONTROLS,c.validUntil()));assertSame(out,read.original());assertEquals(1,port.effectWrites);
            }
        }
    }
    /** Explicit Java DATA native-observation substitute, never a C++ frame. */
    private static CurrentZg361Ae2Source reviewSource(DataPort port) {
        boolean row=!port.mode.equals("review-metadata-only");
        boolean complete=port.reviewOpened&&!port.mode.equals("review-incomplete");
        boolean open=row&&port.list&&!port.reviewOpened&&!port.mode.equals("review-no-open");
        var review=new CurrentZg361Ae2Source.Review(CurrentZg361Ae2.REVIEW_DEFINITION,true,port.list,port.reviewOpened,true,
                true,true,false,row,port.reviewOpened,open,complete,
                port.reviewOpened?Optional.of(CurrentZg361Ae2.REVIEW_DEFINITION):Optional.empty(),
                complete?Optional.of(port.reviewHasRequirements):Optional.empty(),complete?Optional.of(port.reviewDescription):Optional.empty());
        return new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.REVIEW,Optional.empty(),Optional.empty(),Optional.of(review));
    }
    private static CurrentZg361Ae2Source changedReviewSource(CurrentZg361Ae2Source before) {
        var r=before.review().orElseThrow();
        var changed=new CurrentZg361Ae2Source.Review(r.definitionKey(),r.residentAvailable(),r.listVisible(),r.detailVisible(),!r.detailEnabled(),
                r.actorBound(),r.modelComplete(),r.blockedByVisibleModal(),r.rowPresent(),r.selectedReview(),r.openDetailAdmissible(),
                r.requirementsComplete(),r.selectedDefinitionKey(),r.hasRequirements(),r.requirementsDescription());
        return new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.REVIEW,Optional.empty(),Optional.empty(),Optional.of(changed));
    }
    @Test void reviewPrivateQueryOpensOnceAndKeepsIndependentFalseEmptyAndRichTextData()throws Exception {
        var port=new DataPort("review-normal",true);try(var t=transport(port)) {
            begin(t);var q=query(t,CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS);
            assertFalse(q.frame().source().orElseThrow().review().orElseThrow().requirementsComplete());
            var p=t.prepareCurrentZg361Ae2(q,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL);
            assertSame(p,t.prepareCurrentZg361Ae2(q,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL));
            var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentZg361Ae2(p));assertSame(out,t.submitCurrentZg361Ae2(p));
            assertEquals(CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED,p.latestFrame().orElseThrow().status());
            var after=query(t,CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS);var r=after.frame().source().orElseThrow().review().orElseThrow();
            assertTrue(r.requirementsComplete());assertEquals(Optional.of(false),r.hasRequirements());assertEquals(Optional.of(""),r.requirementsDescription());
            assertThrows(IOException.class,()->t.prepareCurrentZg361Ae2(after,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL));
            port.reviewDescription=String.valueOf((char)0)+(char)0x15+"actual Java DATA description\n";
            var rich=query(t,CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS);
            assertEquals(Optional.of(port.reviewDescription),rich.frame().source().orElseThrow().review().orElseThrow().requirementsDescription());
            t.requireCurrentZg361Ae2ZeroDay(core(t));
            assertEquals(1,port.effectWrites);assertEquals(1,port.reviewOpens);assertEquals(0,port.pays);assertEquals(0,port.verifies);assertFalse(port.present);
        }
    }
    @Test void reviewWrongKindCapabilitiesAndIncompleteMetadataCannotAuthorizeAWrite()throws Exception {
        var wrong=new DataPort("review-normal",true);try(var t=transport(wrong)) {
            begin(t);var q=query(t,CurrentZg361Ae2.Action.QUERY_CONTROLS);
            assertThrows(IOException.class,()->t.prepareCurrentZg361Ae2(q,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL));assertEquals(0,wrong.effectWrites);
        }
        var missing=new DataPort("review-no-caps",true);try(var t=transport(missing)) {
            begin(t);var c=core(t);assertInstanceOf(NativeGameTransport.Zg361Ae2Unavailable.class,t.readCurrentZg361Ae2(c,CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS,c.validUntil()));
            assertEquals(0,missing.familyWrites);assertEquals(0,missing.effectWrites);
        }
        var queryOnly=new DataPort("review-query-only",true);try(var t=transport(queryOnly)) {
            begin(t);var q=query(t,CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS);
            assertThrows(IOException.class,()->t.prepareCurrentZg361Ae2(q,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL));assertEquals(0,queryOnly.effectWrites);
        }
        for(String mode:List.of("review-no-open","review-metadata-only")) {
            var port=new DataPort(mode,true);try(var t=transport(port)) {
                begin(t);var q=query(t,CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS);var r=q.frame().source().orElseThrow().review().orElseThrow();
                assertEquals(CurrentZg361Ae2.REVIEW_DEFINITION,r.definitionKey());assertFalse(r.requirementsComplete());assertTrue(r.hasRequirements().isEmpty());assertTrue(r.requirementsDescription().isEmpty());
                assertThrows(IOException.class,()->q.requireOriginal(t,q.validUntil().plusMillis(1)));
                assertThrows(IOException.class,()->t.prepareCurrentZg361Ae2(q,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL));assertEquals(0,port.effectWrites);
            }
        }
    }
    @Test void reviewLostResultAndWholeSourceCoreLeaseDriftStayStickyWithoutReplay()throws Exception {
        for(String mode:List.of("review-lost-result","review-changed-source","review-changed-core","review-changed-lease")) {
            var port=new DataPort(mode,true);try(var t=transport(port)) {
                begin(t);var q=query(t,CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS);
                var p=t.prepareCurrentZg361Ae2(q,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL);
                var original=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentZg361Ae2(p));assertSame(original,t.submitCurrentZg361Ae2(p));
                int familyWrites=port.familyWrites;var c=core(t);
                var blocked=assertInstanceOf(NativeGameTransport.Zg361Ae2Unavailable.class,t.readCurrentZg361Ae2(c,CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS,c.validUntil()));
                assertSame(original,blocked.original());assertEquals(familyWrites,port.familyWrites);assertEquals(1,port.effectWrites);assertEquals(0,port.pays);assertEquals(0,port.verifies);
            }
        }
    }

    /** Same existing self-owned Java DATA port; no genuine C++/Game frames. */
    private static NativeGameTransport.Zg361Ae2Received reviewCombinedThroughSevenEffects(NativeGameTransport t,DataPort port)throws Exception {
        action(t,CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST);
        var review=query(t,CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS);
        var detail=t.prepareCurrentZg361Ae2(review,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL);
        assertSame(detail,t.prepareCurrentZg361Ae2(review,CurrentZg361Ae2.Action.OPEN_REVIEW_DETAIL));
        var detailAck=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentZg361Ae2(detail));
        assertSame(detailAck,t.submitCurrentZg361Ae2(detail));
        assertEquals(CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED,detail.latestFrame().orElseThrow().status());
        var actualReview=query(t,CurrentZg361Ae2.Action.QUERY_REVIEW_REQUIREMENTS).frame().source().orElseThrow().review().orElseThrow();
        assertTrue(actualReview.requirementsComplete());assertEquals(Optional.of(false),actualReview.hasRequirements());
        assertEquals(Optional.of(""),actualReview.requirementsDescription());assertEquals(0,port.pays);
        // Review leaves the same actual controls list visible. There is no
        // generic Close or second phase-0 list action between review/present.
        assertTrue(port.list);action(t,CurrentZg361Ae2.Action.OPEN_PRESENT_DETAIL);
        action(t,CurrentZg361Ae2.Action.CONFIRM_PRESENT);
        var pay=action(t,CurrentZg361Ae2.Action.CHOOSE_PAY_NOW);
        var after=query(t,CurrentZg361Ae2.Action.QUERY_AE2);
        assertTrue(t.currentZg361Ae2EventAbsent(pay,after));
        action(t,CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST);
        action(t,CurrentZg361Ae2.Action.OPEN_VERIFY_DETAIL);
        assertEquals(7,port.effectWrites);assertEquals(1,port.reviewOpens);assertEquals(1,port.pays);
        return query(t,CurrentZg361Ae2.Action.QUERY_CONTROLS);
    }
    @Test void reviewCombinedPrivateBeginPermitsEightOnceEffectsAndIndependentActualAbsence()throws Exception {
        var port=new DataPort("review-combined",true);port.list=false;
        try(var t=transport(port)) {
            t.beginCurrentZg361Ae2CombinedCase(core(t));
            int before=port.familyWrites;
            assertThrows(IOException.class,()->t.beginCurrentZg361Ae2CombinedCase(core(t)));
            assertThrows(IOException.class,()->t.beginCurrentZg361Ae2Case(core(t)));
            assertEquals(before,port.familyWrites);
            var verify=reviewCombinedThroughSevenEffects(t,port);
            var eighth=t.prepareCurrentZg361Ae2(verify,CurrentZg361Ae2.Action.CONFIRM_VERIFY);
            assertSame(eighth,t.prepareCurrentZg361Ae2(verify,CurrentZg361Ae2.Action.CONFIRM_VERIFY));
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentZg361Ae2(eighth));
            assertSame(ack,t.submitCurrentZg361Ae2(eighth));
            assertEquals(CurrentZg361Ae2Result.Status.CONFIRMATION_DISPATCHED,eighth.latestFrame().orElseThrow().status());
            t.requireCurrentZg361Ae2ZeroDay(core(t));
            assertEquals(8,port.effectWrites);assertEquals(2,port.listOpens);assertEquals(1,port.reviewOpens);
            assertEquals(1,port.pays);assertEquals(1,port.verifies);assertEquals(15,port.selectedAuthored);
        }
    }
    @Test void reviewCombinedCapacityCannotBeBorrowedByOriginalBeginOrAnUpgrade()throws Exception {
        var port=new DataPort("review-original-seven",true);port.list=false;
        try(var t=transport(port)) {
            begin(t);int before=port.familyWrites;
            // All five capabilities and complete DATA are present. The old
            // private begin still owns seven; no later call may upgrade it.
            assertThrows(IOException.class,()->t.beginCurrentZg361Ae2CombinedCase(core(t)));
            assertThrows(IOException.class,()->t.beginCurrentZg361Ae2Case(core(t)));
            assertEquals(before,port.familyWrites);
            var verify=reviewCombinedThroughSevenEffects(t,port);
            assertThrows(IOException.class,()->t.prepareCurrentZg361Ae2(verify,CurrentZg361Ae2.Action.CONFIRM_VERIFY));
            assertEquals(7,port.effectWrites);assertEquals(0,port.verifies);
            before=port.familyWrites;
            assertThrows(IOException.class,()->t.beginCurrentZg361Ae2CombinedCase(core(t)));
            assertEquals(before,port.familyWrites);assertEquals(7,port.effectWrites);
        }
    }

    private static final class DataPort implements NativePacketPort {
        final String mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed,list,detail,present,event,paid;
        int actor=-2,sequence,effectWrites,familyWrites,listOpens,pays,verifies,selectedAuthored=-1;
        CurrentZg361Ae2Source.Control selected;CurrentZg361Ae2Source before;
        final boolean reviewData;boolean reviewOpened,reviewHasRequirements;String reviewDescription="";int reviewOpens;
        DataPort(String mode)throws IOException{this(mode,false);}
        DataPort(String mode,boolean reviewData)throws IOException{
            this.reviewData=reviewData;if(reviewData)list=true;
            this.mode=mode;var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",T)
                    .put("bridge_version","zg361-ae2-DATA").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                    .put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities");caps.add(CoreFrame.CAPABILITY);caps.add(CurrentZg361Ae2.QUERY_CAPABILITY);caps.add(CurrentZg361Ae2.CONTROLS_CAPABILITY);caps.add(CurrentZg361Ae2.PAY_CAPABILITY);
            if(reviewData&&!mode.equals("review-no-caps")){caps.add(CurrentZg361Ae2.REVIEW_QUERY_CAPABILITY);if(!mode.equals("review-query-only"))caps.add(CurrentZg361Ae2.REVIEW_DETAIL_CAPABILITY);}
            packets.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        CoreFrame.Prefix prefix(){return new CoreFrame.Prefix(-240,3,true,1,true,true,actor,true);}
        CurrentZg361Ae2Source source(CurrentZg361Ae2.Action action){
            if(action.sourceKind()==CurrentZg361Ae2Source.Kind.REVIEW)return reviewSource(this);
            if(action.sourceKind()==CurrentZg361Ae2Source.Kind.CONTROLS){
                var rows=new ArrayList<CurrentZg361Ae2Source.ControlRow>();
                for(var c:CurrentZg361Ae2Source.Control.values()){
                    boolean allowed=c==CurrentZg361Ae2Source.Control.PRESENT?!present:paid;
                    boolean isSelected=detail&&selected==c;rows.add(new CurrentZg361Ae2Source.ControlRow(c,c.definitionKey(),allowed,list&&allowed,isSelected?Optional.of(allowed):Optional.empty(),isSelected&&allowed));
                }
                return new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.CONTROLS,Optional.of(new CurrentZg361Ae2Source.Controls(true,list,detail,true,true,false,!list,Optional.ofNullable(selected),rows)),Optional.empty());
            }
            Optional<CurrentZg361Ae2Source.Ae2> snapshot=Optional.empty();List<CurrentZg361Ae2Source.EventIdentity> census=List.of();
            if(event){
                long recipient=mode.equals("foreign-event")?0:Integer.toUnsignedLong(actor);var options=new ArrayList<CurrentZg361Ae2Source.Option>();
                for(int index:new int[]{17,15,16})options.add(new CurrentZg361Ae2Source.Option(index,"zg361comp.1.ae2.r"+(index-14),index==15,"Java DATA authored"+index,"","Java DATA full\u0000tooltip\n"+index));
                snapshot=Optional.of(new CurrentZg361Ae2Source.Ae2(19,recipient,"zg361comp.1",42,true,true,true,true,true,options,true));census=List.of(new CurrentZg361Ae2Source.EventIdentity(19,recipient,"zg361comp.1"));
            }
            return new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.EVENTS,Optional.empty(),Optional.of(new CurrentZg361Ae2Source.Events(true,census,snapshot)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Java DATA port closed");}
        public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant deadline)throws IOException{verify();}
        public byte[] readPacket(Instant deadline)throws IOException{verify();if(packets.isEmpty())throw new IOException("Java DATA intentionally lost original result");return packets.removeFirst();}
        public void writePacket(byte[] bytes,Instant deadline)throws IOException{
            verify();var request=NativeWire.decodeExecuteRequest(bytes);ObjectNode result;
            if(request.step().equals(CoreFrame.STEP))result=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD,prefix())).bytes()));
            else {
                familyWrites++;var claim=NativeWire.parse(request.normalizedAdditionalFields().value()).get("arguments").get("zg361_ae2");var action=CurrentZg361Ae2.Action.parse(claim.get("action").textValue());boolean query=action.queryOnly();var source=query?source(action):before;
                var provider=query?O:new BigInteger(claim.get("provider_generation").textValue());var seq=query?BigInteger.valueOf(++sequence):new BigInteger(claim.get("query_sequence").textValue());var status=CurrentZg361Ae2Result.Status.AVAILABLE;Optional<String> why=Optional.empty();Optional<CurrentZg361Ae2Source> observed=Optional.of(source);var facts=prefix();boolean attempted=!query,returned=!query;BigInteger consumed=Z;
                if(query)before=source;
                else {
                    effectWrites++;consumed=BigInteger.valueOf(effectWrites);
                    if(mode.equals("lost-result"))return;
                    if(reviewData&&mode.equals("review-lost-result"))return;
                    if(mode.equals("known-stale")){status=CurrentZg361Ae2Result.Status.STALE_SOURCE;attempted=returned=false;consumed=Z;observed=Optional.empty();why=Optional.of("Java DATA original known prewrite stale");facts=new CoreFrame.Prefix(-240,3,true,1,true,true,42,true);}
                    else {
                        switch(action){
                            case OPEN_CONTROLS_LIST->{list=true;listOpens++;status=CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED;}
                            case OPEN_PRESENT_DETAIL->{selected=CurrentZg361Ae2Source.Control.PRESENT;detail=true;status=CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED;}
                            case CONFIRM_PRESENT->{present=true;event=true;list=false;detail=false;selected=null;status=CurrentZg361Ae2Result.Status.CONFIRMATION_DISPATCHED;}
                            case CHOOSE_PAY_NOW->{selectedAuthored=source.events().orElseThrow().ae2().orElseThrow().payNowOption().authoredOptionIndex();paid=true;event=false;pays++;status=CurrentZg361Ae2Result.Status.SELECTION_DISPATCHED;}
                            case OPEN_VERIFY_DETAIL->{selected=CurrentZg361Ae2Source.Control.VERIFY;detail=true;status=CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED;}
                            case CONFIRM_VERIFY->{verifies++;status=CurrentZg361Ae2Result.Status.CONFIRMATION_DISPATCHED;}
                            case OPEN_REVIEW_DETAIL->{reviewOpened=true;detail=true;reviewOpens++;status=CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED;}
                            default->throw new IOException("No arbitrary action in generated Java DATA");
                        }
                        if(mode.equals("changed-before-source")){
                            var c=source.controls().orElseThrow();var reversed=new ArrayList<>(c.rows());java.util.Collections.reverse(reversed);
                            observed=Optional.of(new CurrentZg361Ae2Source(source.kind(),Optional.of(new CurrentZg361Ae2Source.Controls(c.residentAvailable(),c.listVisible(),c.detailVisible(),c.actorBound(),c.modelComplete(),c.blockedByVisibleModal(),c.openListAdmissible(),c.selectedControl(),reversed)),Optional.empty()));
                        }
                    }
                }
                if(!query&&reviewData){
                    if(mode.equals("review-changed-source"))observed=Optional.of(changedReviewSource(source));
                    if(mode.equals("review-changed-core"))facts=new CoreFrame.Prefix(-240,3,true,1,true,true,42,true);
                    if(mode.equals("review-changed-lease"))seq=seq.add(O);
                }
                var owner=new CurrentLetterResult.OwnerWitness(T,BigInteger.valueOf(20),BigInteger.valueOf(30),7);
                var frame=new CurrentZg361Ae2Result(action,status,attempted,returned,true,provider,seq,consumed,Optional.of(facts),Optional.of(owner),observed,why);result=NativeWire.object(NativeWire.parse(frame.encode().bytes()));
            }
            var envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",request.step().equals(CoreFrame.STEP)||result.path("source_available").asBoolean());envelope.set("result",result);packets.add(NativeWire.packet(StrictJson.canonical(envelope)));
        }
        public void close(){closed=true;}
    }
}
