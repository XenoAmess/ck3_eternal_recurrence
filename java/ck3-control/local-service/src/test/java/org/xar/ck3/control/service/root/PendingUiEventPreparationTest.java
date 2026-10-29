package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.events.interactionfallback.InteractionFallback;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.events.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** Original Python/native software fixtures -> real Driver projections and installed codecs -> private DATA preparation.
 * This does not construct Ready or assert live Root/cause/once-token qualification. */
final class PendingUiEventPreparationTest {
    private static final Instant NOW=Instant.parse("2026-10-24T07:00:00Z"),DEADLINE=Instant.parse("2030-01-01T00:00:00Z");
    private static final BigInteger PUBLIC=new BigInteger("9007199254740993");
    private static final List<String> REPLIES=List.of("reject-pending-character-interaction","accept-pending-character-interaction","acknowledge-pending-character-interaction","block-pending-character-interaction");
    private static ObjectNode original;
    @TempDir Path temporary;
    @BeforeAll static void originalProducers()throws Exception{original=PendingUiEventOriginalTestInputs.load();}

    @Test void originalEventFirstDisplayUsesNativeFourNotDisplayOneAndRetainsBothReadAndParent()throws Exception{
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("event"),16*1024*1024)){
            disk.writer.locked(same->{var fixture=new Inputs(disk,disk.archive.withSession(same),same);var current=fixture.event(true);
                var prepared=fixture.eventPreparation(current,fixture.eventContext(true),1,"private-event");
                assertEquals("select-event-option-4",prepared.command().operation().value());
                var shown=assertInstanceOf(EventActionPreparation.EventPresentation.class,prepared.presentation());
                assertEquals(0,shown.selected().renderedIndex());assertEquals(3,shown.selected().nativeOptionIndex());
                assertEquals("xar_test.0001",shown.context().definition().key());assertEquals(2,shown.context().savedScopes().size());
                var nativeRequest=EventActionPreparation.prepare(prepared.command());
                var sent=NativeWire.decodeExecuteRequest(NativeWire.execute("event-native",nativeRequest.step(),current.frame().identity().frame().identity().nativeRevision(),nativeRequest.additionalFields().bytes()));
                assertEquals("select-event-option-4",sent.step());assertTrue(DriverJson.object(sent.normalizedAdditionalFields().value(),65536).members().isEmpty());
                assertTrue(prepared.sourceOriginals().contains(prepared.originalReadRef()));assertTrue(prepared.sourceOriginals().contains(current.canonicalPublication()));
                assertEquals(ActionCodec.bodySha256(current.originalParent()),OpportunityJson.text(OpportunityJson.object(prepared.command().arguments().get("pending_ui_event_source"),"source").get("original_parent_body_sha256"),"parent"));
                roundtrip(prepared.command());assertEquals(prepared.originalRead(),fixture.archive.loadRead(prepared.originalReadRef()));
                var disabled=assertThrows(EventActionPreparation.PendingSelectionRejected.class,()->fixture.eventPreparation(current,fixture.eventContext(false),2,"disabled"));
                assertFalse(disabled.diagnosis().get("selected_step") instanceof OpportunityJson.Text);assertTrue(disabled.originalRead().bytes()>0);
                return null;});
        }
    }

    @Test void originalNotificationAndUnknownInteractionKeepAckAndLegalLeftRejectDistinct()throws Exception{
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("replies"),16*1024*1024)){
            disk.writer.locked(same->{var fixture=new Inputs(disk,disk.archive.withSession(same),same);
                for(String name:List.of("normal","notification")){
                    var row=pending(name);var current=fixture.pending(row);var prepared=fixture.replyPreparation(current,row,1,"private-"+name);
                    var request=EventActionPreparation.prepare(prepared.command());String expected=name.equals("notification")?"acknowledge-pending-character-interaction":"reject-pending-character-interaction";
                    assertEquals(expected,request.step());assertEquals(-2130706399,prepared.presentation().instanceId());
                    var sent=NativeWire.decodeExecuteRequest(NativeWire.execute("reply-native-"+name,request.step(),BigInteger.valueOf(41),request.additionalFields().bytes()));
                    var args=DriverJson.object(sent.normalizedAdditionalFields().value(),65536);
                    assertEquals(Set.of("pending_interaction_id"),args.members().keySet());assertEquals(BigInteger.valueOf(-2130706399),OpportunityJson.integer(args.get("pending_interaction_id"),"full signed instance"));
                var actual=(ObjectNode)DriverJson.toNode(prepared.command().arguments());actual.remove("pending_ui_event_source");
                    var capture=(ObjectNode)actual.get("unhandled_interaction_fallback");assertTrue(((ObjectNode)capture.get("gui_binding")).remove("current_presentation").isObject());
                    var legacy=(ObjectNode)row.get("plan").deepCopy();
                    // The private installed producer additionally performs its actual persistent registry lookup.
                    // No matching entry is present in this software fixture; compare original semantics separately from that audit.
                    assertFalse(capture.path("registry_known").booleanValue());assertTrue(capture.path("offline_registry_audit").isObject());
                    capture.remove("offline_registry_audit");((ObjectNode)legacy.path("unhandled_interaction_fallback")).remove("offline_registry_audit");
                    assertEquals(RetainedJson.parse(DriverJson.encodeNode(legacy)),RetainedJson.parse(DriverJson.encodeNode(actual)));
                    var presentation=assertInstanceOf(EventActionPreparation.InteractionPresentation.class,prepared.presentation());
                    assertEquals(name.equals("notification")?1:2,presentation.current().buttons().size());roundtrip(prepared.command());
                }
                for(String name:List.of("disabled","no_native")){
                    var row=pending(name);var current=fixture.pending(row);
                    var rejected=assertThrows(EventActionPreparation.PendingSelectionRejected.class,()->fixture.replyPreparation(current,row,1,"blocked-"+name));
                    assertFalse(rejected.diagnosis().get("selected_step") instanceof OpportunityJson.Text);assertTrue(rejected.originalRead().bytes()>0);
                }
                return null;});
        }
    }

    @Test void privateBlockedKnownReplyUsesOnlyLegalLeftWhileSelectedAcceptAndMarriageRemainDedicated()throws Exception{
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("known-reply-boundary"),16*1024*1024)){
            disk.writer.locked(same->{var fixture=new Inputs(disk,disk.archive.withSession(same),same);
                for(String name:List.of("ransom_blocked","blocked_marriage","known_accept")){
                    var row=pending("normal").deepCopy();
                    var context=(ObjectNode)row.path("query").path("pending_character_interaction_context");
                    var definition=(ObjectNode)context.get("definition");
                    if(name.equals("ransom_blocked"))definition.put("canonical_key","pay_ransom_interaction");
                    else if(name.equals("blocked_marriage")){
                        definition.put("canonical_key","arrange_marriage_interaction").put("deterministic_key_hash",1298930137);
                        ((ObjectNode)context.get("terms")).put("special_data_present",true);
                        ((ObjectNode)context.path("terms").get("special_war_binding")).put("reason","special_interaction_subtype_opaque");
                        ((com.fasterxml.jackson.databind.node.ArrayNode)context.path("readiness").get("not_ready_reasons")).set(0,com.fasterxml.jackson.databind.node.TextNode.valueOf("special_interaction_subtype_opaque"));
                    }else{
                        definition.put("canonical_key","spar_with_knight_interaction");
                        for(String action:List.of("reject","block"))((ObjectNode)context.path("legality").get(action)).put("allowed",false).put("reason","native_reply_not_allowed");
                    }
                    var current=fixture.pending(row);
                    if(name.equals("ransom_blocked")){
                        var prepared=fixture.replyPreparation(current,row,1,name);
                        assertEquals("reject-pending-character-interaction",prepared.command().operation().value());
                        var capture=OpportunityJson.object(prepared.command().arguments().get("unhandled_interaction_fallback"),"actual private fallback");
                        var previous=OpportunityJson.object(capture.get("original_plan"),"original blocked known plan");
                        assertEquals(new OpportunityJson.Text("known_received_ransom"),OpportunityJson.object(previous.get("decision"),"known decision").get("classification"));
                        assertSame(OpportunityJson.Nil.INSTANCE,previous.get("selected_step"));
                        assertEquals("reject-pending-character-interaction",EventActionPreparation.prepare(prepared.command()).step());
                    }else{
                        var denied=assertThrows(EventActionPreparation.PendingSelectionRejected.class,()->fixture.replyPreparation(current,row,1,name));
                        assertEquals(new OpportunityJson.Bool(true),denied.diagnosis().get("known_policy_handled"));
                        assertFalse(denied.diagnosis().get("selected_step") instanceof OpportunityJson.Text);
                    }
                }
                return null;});
        }
    }

    @Test void freshReadRechecksExactDisplayAndOnlyMonotonicQueryIdentityMayChange()throws Exception{
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("fresh"),16*1024*1024)){
            disk.writer.locked(same->{var fixture=new Inputs(disk,disk.archive.withSession(same),same);var current=fixture.event(true);
                var old=fixture.eventPreparation(current,fixture.eventContext(true),1,"same-intent");
                var fresh=fixture.eventPreparation(current,fixture.eventContext(true),2,"same-intent");
                byte[] retained=ActionCodec.encodeCommand(old.command());assertNotEquals(old.originalReadRef(),fresh.originalReadRef());
                EventActionPreparation.requirePendingUiEventCurrent(old,fresh);assertArrayEquals(retained,ActionCodec.encodeCommand(old.command()));
                assertThrows(IllegalArgumentException.class,()->EventActionPreparation.requirePendingUiEventCurrent(old,old));
                var noLater=fixture.eventPreparation(current,fixture.eventContext(true),1,"same-intent");
                assertThrows(IllegalArgumentException.class,()->EventActionPreparation.requirePendingUiEventCurrent(old,noLater));
                List<java.util.function.Consumer<ObjectNode>> changes=List.of(
                    context->context.put("event_definition_key","different.actual.definition"),
                    context->((ObjectNode)context.path("options").get(0)).put("resolved_name","new original caption"),
                    context->((ObjectNode)context.path("saved_scopes").get(0).path("scope").path("typed_identity")).put("character_id",43));
                for(var mutate:changes){var context=fixture.eventContext(true);mutate.accept(context);var changed=fixture.eventPreparation(current,context,3,"same-intent");
                    assertThrows(IllegalArgumentException.class,()->EventActionPreparation.requirePendingUiEventCurrent(old,changed));}
                var replyCurrent=fixture.pending(pending("normal"));var reply=fixture.replyPreparation(replyCurrent,pending("normal"),1,"same-reply");var replyFresh=fixture.replyPreparation(replyCurrent,pending("normal"),2,"same-reply");
                EventActionPreparation.requirePendingUiEventCurrent(reply,replyFresh);
                assertThrows(IllegalArgumentException.class,()->EventActionPreparation.requirePendingUiEventCurrent(old,replyFresh));
                return null;});
        }
    }

    @Test void actualPrivateAfterFailureNeverFallsBackAndAbsentPrivateScopeUsesTheSameOrdinaryHeld()throws Exception{
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("after"),16*1024*1024)){
            disk.writer.locked(same->{var fixture=new Inputs(disk,disk.archive.withSession(same),same);var current=fixture.event(true);
                var command=fixture.eventPreparation(current,fixture.eventContext(true),1,"after-original").command();var after=fixture.next(current);
                AtomicInteger ordinary=new AtomicInteger();var held=new HeldDriverObservationPort(deadline->{ordinary.incrementAndGet();return after.full().actual();},
                    actual->new DriverObservationFacts.Known(after.full().facts()),fixture.archive::preserveNativeFrame,new DriverObservationAssembler(),4);
                var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
                var active=new NativeEffectSnapshots(()->held,fixture.archive,loader,(retained,deadline)->Optional.of(after.frame()));
                var observed=observe(active,command);assertEquals(after.frame().identity(),observed.after());assertEquals(0,ordinary.get());
                var broken=new NativeEffectSnapshots(()->held,fixture.archive,loader,(retained,deadline)->{throw new IOException("actual private cause/publication drift");});
                assertThrows(UncheckedIOException.class,()->broken.eventReads().read(command,DEADLINE));assertEquals(0,ordinary.get());
                var absent=new NativeEffectSnapshots(()->held,fixture.archive,loader,(retained,deadline)->Optional.empty());
                assertEquals(after.frame().identity(),observe(absent,command).after());assertEquals(1,ordinary.get());
                assertEquals(after.frame(),new NativeEffectSnapshots.Pair(current.frame(),after.frame()).after());
                assertThrows(IllegalArgumentException.class,()->new NativeEffectSnapshots.Pair(current.frame(),current.frame()));
                assertThrows(IllegalArgumentException.class,()->new NativeEffectSnapshots.Pair(after.frame(),current.frame()));
                return null;});
        }
    }

    @Test void privateDataAndOriginalReadRejectForeignFramesMalformedFieldsAndUnboundSource()throws Exception{
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("reject"),16*1024*1024)){
            disk.writer.locked(same->{var fixture=new Inputs(disk,disk.archive.withSession(same),same);var current=fixture.event(true);var next=fixture.next(current);
                assertThrows(IllegalArgumentException.class,()->new PendingUiEvent.Current(current.originalParent(),current.full(),current.known(),next.frame(),current.originalDriver(),current.originalHistoryBasis(),current.canonicalPublication(),current.canonicalDomain(),current.qualifiedCause(),current.bridgeCapabilities()));
                var context=fixture.eventContext(true);context.put("current_event_instance_id",17);
                assertThrows(IllegalArgumentException.class,()->fixture.eventPreparation(current,context,1,"wrong-instance"));
                for(String field:List.of("enabled","native_option_index","rendered_index")){
                    var wrong=fixture.eventContext(true);((ObjectNode)wrong.path("options").get(0)).put(field,field.equals("enabled")?"true":"0");
                    assertThrows(IllegalArgumentException.class,()->fixture.eventPreparation(current,wrong,2,"wrong-type"));}
                var row=pending("normal").deepCopy();((ObjectNode)row.path("query").path("pending_character_interaction_context")).put("pending_interaction_id",true);
                var replyCurrent=fixture.pending(pending("normal"));assertThrows(IllegalArgumentException.class,()->fixture.replyPreparation(replyCurrent,row,1,"wrong-reply-type"));
                return null;});
        }
    }

    @Test void privateActualAfterReachesExistingEffectReceiptArchiveAndPublic64WhileAckAloneStaysPending()throws Exception{
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("effect-chain"),24*1024*1024)){
            disk.writer.locked(same->{var fixture=new Inputs(disk,disk.archive.withSession(same),same);
                for(String kind:List.of("event","normal","notification"))for(boolean ack:List.of(true,false)){
                    var current=kind.equals("event")?fixture.event(true):fixture.pending(pending(kind));
                    var prepared=kind.equals("event")?fixture.eventPreparation(current,fixture.eventContext(true),1,"full-"+kind+ack):fixture.replyPreparation(current,pending(kind),1,"full-"+kind+ack);
                    var result=fixture.effect(prepared,current,fixture.next(current),ack);
                    assertTrue(result.applied().isPresent());assertFalse(result.eligibleAdvance());
                    assertEquals(result,ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(result,fixture.archive),fixture.archive));
                    var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());var empty=new NativeEventEffects.MaterialQueries(Optional.empty(),Optional.empty());
                    NativeEventEffects.archivedVerifier(prepared.command().operation(),disk.pin,loader,empty).verifier().verify(null,result,fixture.archive);
                    var verified=NativeEffectEvidence.load(result,fixture.archive,loader);
                    var publicResult=kind.equals("event")?EventSelectionPublicResult.encode(result,verified):PendingInteractionPublicCodec.result(result,fixture.archive,Optional.of(verified.compatibleResult()),
                        new InteractionModels.PendingSummary(new InteractionModels.PendingId(-2130706399),org.xar.ck3.control.contracts.NativeCharacterId.of(1001),kind.equals("notification")),
                        kind.equals("notification")?KnownPendingInteractionRules.Action.ACKNOWLEDGE:KnownPendingInteractionRules.Action.REJECT);
                    var wire=DriverJson.toNode(DriverJson.object(publicResult.bytes(),1<<20));assertEquals(PUBLIC.add(BigInteger.ONE).toString(),wire.path("revision").textValue());
                    assertEquals("xar.java-native-event-result/v3",wire.path("event_result_projection_schema").textValue());
                    if(!kind.equals("event")){assertEquals(kind.equals("notification")?"acknowledged":"rejected",wire.path("interaction_result").path("status").textValue());assertTrue(wire.path("remaining_pending_character_interaction").isNull());}
                    else assertTrue(wire.path("active_event").isNull());
                }
                var current=fixture.event(true);var retained=fixture.eventPreparation(current,fixture.eventContext(true),2,"ack-no-window-credit");
                var noAdvance=fixture.effect(retained,current,fixture.later(current,false),true);
                assertTrue(noAdvance.applied().isEmpty());assertFalse(noAdvance.settled());
                return null;});
        }
    }

    private static void roundtrip(ActionCommand command){var decoded=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));assertEquals(command,decoded);assertEquals(EventActionPreparation.prepare(command),EventActionPreparation.prepare(decoded));}
    private static NativeEventPostconditionPort.BoundSnapshot observe(NativeEffectSnapshots snapshots,ActionCommand command)throws IOException{
        try{return snapshots.eventReads().read(command,DEADLINE);}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("software private observation interrupted",interrupted);}
    }
    private static ObjectNode pending(String name){for(JsonNode row:original.path("pending"))if(name.equals(row.path("name").textValue()))return (ObjectNode)row;throw new AssertionError(name);}
    private static RawJson raw(JsonNode value){return new RawJson(DriverJson.encodeNode(value));}
    private static OpportunityJson.Obj obj(JsonNode value){return DriverJson.object(DriverJson.encodeNode(value),1<<20);}

    /** Shared real-original software fixture for the incident owner's mandatory same-producer regression. */
    static final class Inputs {
        final CoaSourceArchiveBoundaryTest.Fixture disk;final ActionPorts.OutcomeArchive archive;final Session same;final TrustedEventSourceContext trusted;final GameGeneration game;
        final Map<String,DriverSnapshotFacts.Known> known=new java.util.HashMap<>();final Map<String,ExactRef> drivers=new java.util.HashMap<>();int requests;
        Inputs(CoaSourceArchiveBoundaryTest.Fixture disk,ActionPorts.OutcomeArchive archive,Session same)throws IOException{
            this.disk=disk;this.archive=archive;this.same=same;game=disk.origin().game();
            var reviewed=RootBlockedPendingIncidentTest.offlineSources(disk.directory.resolve("pending-reviewed"),disk.source.machineId());
            Path stock=reviewed.stockGameRoot(),state=reviewed.stateRoot();
            byte[] gui;try(var input=PendingUiEventPreparationTest.class.getResourceAsStream("/unknownnotification/interaction_notification_window.gui")){assertNotNull(input);gui=input.readAllBytes();}
            assertEquals(InteractionFallback.GUI_SHA256,DriverJson.sha256(gui));Path destination=stock.resolve(InteractionFallback.GUI_SOURCE);Files.createDirectories(destination.getParent());Files.write(destination,gui);
            trusted=TrustedEventSourceContext.openEvidence(new EventSourceReadContext(disk.source.machineId(),state,stock));
        }
        PendingUiEvent.Current event(boolean enabled)throws IOException{
            var state=(ObjectNode)original.path("pending").get(0).path("packet").path("state").deepCopy();
            var snapshot=original.path("event_snapshot");state.put("date_raw",eventFixtureDateRaw()).put("paused",true).put("map_ready",true).put("local_player_id",42).putNull("pending_character_interaction");
            ((ObjectNode)state.get("played_character")).put("character_id",42).put("alive",true);state.set("active_event",snapshot.get("active_event").deepCopy());
            return frame(state,17,42,0);
        }
        PendingUiEvent.Current pending(ObjectNode row)throws IOException{return frame((ObjectNode)row.path("packet").path("state").deepCopy(),41,2001,0);}
        PendingUiEvent.Current next(PendingUiEvent.Current old)throws IOException{
            return later(old,true);
        }
        PendingUiEvent.Current later(PendingUiEvent.Current old,boolean cleared)throws IOException{
            var state=(ObjectNode)DriverJson.toNode(old.full().actual().state().bytes().length>0?DriverJson.object(old.full().actual().state().bytes(),1<<20):new OpportunityJson.Obj(Map.of()));
            if(cleared)state.putNull("active_event").putNull("pending_character_interaction");return frame(state,old.full().actual().nativeRevision().longValueExact()+1,old.frame().identity().frame().identity().player().intValueExact(),1);
        }
        PendingUiEvent.Current frame(ObjectNode state,long revision,int actor,int after)throws IOException{
            var driver=StrictJson.object().put("format_version",2).put("pipe_name","pending-ui-software").put("bridge_pid",4242).put("episode_character_id",actor).put("episode_run_id","actual-new-episode");
            for(String key:List.of("last_checkpoint","rollback_war_failure","managed_restore_transaction","succession_expectation","succession_lifecycle","campaign_goal"))driver.putNull(key);driver.putArray("command_history");driver.putArray("rollback_war_failures");
            byte[] driverBytes=DriverStateSnapshot.decodeComplete(DriverJson.encodeNode(driver)).encode();
            ExactRef driverRef=archive.preserveMaterial(new RawJson(driverBytes));var actualKnown=DriverFactsRepository.imported(driverRef,driverBytes,3,7,game,new OpportunityJson.Obj(Map.of()));
            var packet=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","native:"+revision).put("revision",revision);packet.set("state",state);
            var actual=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(disk.source.machineId(),game,BigInteger.valueOf(3),"pending-software-session"),"native:"+revision,BigInteger.valueOf(revision),raw(state),NativeWire.packet(DriverJson.encodeNode(packet)),NOW.plusSeconds(after));
            ExactRef nativeRef=archive.preserveNativeFrame(actual);var extras=StrictJson.object().put("backend_id","native-headless").put("source","injected-dll-named-pipe");var diagnostic=extras.putObject("diagnostics").put("bridge_pid",4242).put("connection_generation",3);diagnostic.putObject("hello").put("expected_ck3_version",EventWindowModels.Build.TOURS.version()).put("expected_ck3_sha256",EventWindowModels.Build.TOURS.sha256());
            var manifest=DriverObservationEvidenceReader.encode(actualKnown,actual,PUBLIC.add(BigInteger.valueOf(after)),3,disk.source,obj(extras),driverRef);ExactRef manifestRef=archive.preserveMaterial(manifest);
            var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,new RawJson(driverBytes),actual);var assembler=new DriverObservationAssembler();var joined=assembler.assemble(actual,facts,nativeRef);var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,joined,()->"actual Native/Driver join: "+joined);var full=assembler.projectFull(actual,facts,nativeRef);
            known.put(complete.identity().frame().snapshotId(),actualKnown);drivers.put(complete.identity().frame().snapshotId(),driverRef);
            var refs=new ArrayList<ExactRef>();for(int i=0;i<5;i++)refs.add(archive.preserveMaterial(new RawJson(("{\"software_original_role\":"+i+"}").getBytes(java.nio.charset.StandardCharsets.UTF_8))));
            var lifecycle=new LifecycleIdentity(disk.source.machineId(),game,complete.sessionId(),BigInteger.valueOf(3),new LifecycleIdentity.Subject(BigInteger.valueOf(actor+1L),"actual-old-episode",6,2),new LifecycleIdentity.Frame("terminal-before",PUBLIC.subtract(BigInteger.ONE),BigInteger.valueOf(16),complete.identity().frame().identity().dateRaw(),true,true),new LifecycleIdentity.Character(BigInteger.valueOf(actor),true),LifecycleIdentity.TerminalReason.CHANGED,new LifecycleIdentity.Evidence(refs.get(0),refs.get(1),refs.get(2),refs.get(3),refs.get(4)),NOW.minusSeconds(1));
            var expected=new LifecycleExpectedPostcondition(lifecycle,disk.source,LifecycleExpectedPostcondition.SCHEMA,LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR,List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),false),new ExpectedBoolean(new FieldKey("timeline.advance_verified"),false),new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),false)));
            var parent=new ActionCommand("actual-software-continue-"+actor,new CommandOrigin.LifecycleTerminal(lifecycle),disk.source,complete.sessionId(),LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR.key(),new OpportunityJson.Obj(Map.of()),new CommandExpectation.LifecycleTerminal(expected),new Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
            Set<String> caps=new java.util.HashSet<>();caps.add(EventActionPreparation.EVENT_CAPABILITY);REPLIES.forEach(step->caps.add("game.command."+step));
            return new PendingUiEvent.Current(parent,full,actualKnown,complete,driverRef,actualKnown.originalHistoryBasis(),refs.get(1),refs.get(2),refs.get(4),caps);
        }
        // The event codec unit fixture uses an arbitrary raw date; join both software fields on the original pending fixture's whole CK3 day.
        private static int eventFixtureDateRaw(){return original.path("pending").get(0).path("packet").path("state").path("date_raw").intValue();}
        ObjectNode eventContext(boolean enabled){var context=(ObjectNode)original.get("event").deepCopy();context.put("date_raw",eventFixtureDateRaw());if(enabled){((ObjectNode)context.path("options").get(0)).put("enabled",true).put("unavailable_reason","");}return context;}
        EventActionPreparation.PendingPrepared eventPreparation(PendingUiEvent.Current current,ObjectNode context,long sequence,String id)throws IOException{
            var contract=EventWindowRead.contract(disk.pin,request->{assertEquals(current.frame().identity(),request.before());});
            var result=StrictJson.object().put("step",EventWindowRead.STEP).put("accepted",true).put("status","available").put("query_sequence",sequence).put("snapshot_revision",17).put("backend_id","native-headless");result.set("current_event_window_context",context);
            var request=new PlanningReadRequest(current.frame().identity(),disk.source,current.frame().sessionId(),contract.operation(),current.frame().semantic(),DEADLINE);
            var read=read(current,contract,request,result);Set<OperationKey> steps=Set.of(new OperationKey("select-event-option-1"),new OperationKey("select-event-option-2"),new OperationKey("select-event-option-3"),new OperationKey("select-event-option-4"));
            return PendingUiEventPreparation.event(current,read,EventWindowModels.Build.TOURS,steps,id,DEADLINE,RegisteredEventKnowledge.load(),trusted);
        }
        EventActionPreparation.PendingPrepared replyPreparation(PendingUiEvent.Current current,ObjectNode row,long sequence,String id)throws IOException{
            var controls=new RootInteractionContextProjection(InteractionModels.Build.WANDERER6).project(current.frame(),DEADLINE);var contract=PendingInteractionContracts.pending(disk.pin);
            var request=new PlanningReadRequest(current.frame().identity(),disk.source,current.frame().sessionId(),contract.operation(),PendingInteractionReadArguments.current(controls),DEADLINE);
            var result=(ObjectNode)row.get("query").deepCopy();result.put("query_sequence",sequence);var read=read(current,contract,request,result);
            Set<OperationKey> steps=new java.util.HashSet<>();row.path("steps").forEach(step->steps.add(new OperationKey(step.textValue())));
            return PendingUiEventPreparation.interaction(current,read,controls,Set.copyOf(steps),id,DEADLINE,trusted);
        }
        <T>PlanningReadResult.Known<T> read(PendingUiEvent.Current current,ReadContract<T> contract,PlanningReadRequest request,ObjectNode result)throws IOException{
            String id="actual-software-read-"+(++requests);NativeRequest nativeRequest=contract.prepare(request,id);
            byte[] outbound=NativeWire.execute(id,nativeRequest.step(),request.before().frame().identity().nativeRevision(),nativeRequest.additionalFields().bytes());
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",4242).put("connection_generation",3).put("bridge_version","original-wire-fixture").put("expected_ck3_sha256",EventWindowModels.Build.TOURS.sha256()).put("game_adapter_id","ck3-1.19.0.6-msvc-x64").put("game_adapter_status","ready").put("ck3_build_match",true);hello.putArray("capabilities").add(EventWindowRead.CAPABILITY);
            byte[] helloPacket=NativeWire.packet(DriverJson.encodeNode(hello));ExactRef helloRef=disk.archive.preserveArtifact(same,helloPacket,NativeWire.MAXIMUM_FRAME_BYTES+4);
            var guard=new GuardEvidence(current.frame().identity(),disk.source,current.frame().sessionId(),BigInteger.valueOf(3),contract.operation(),current.frame().originalEvidence(),helloRef,"explicit-pending-software-read",NOW,DEADLINE);
            var bound=new PlanningReadGuard(guard,true,true,true,current.frame().fullBindingSha256());
            var token=raw(result);var returned=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);returned.set("result",result);
            var ack=new NativeActionPort.AckReceived(id,true,Optional.of(token),raw(returned),NativeWire.packet(DriverJson.encodeNode(returned)),Optional.of(new NativeActionPort.OutboundPacket(id,outbound)));
            var receipt=new PlanningReadReceipt(request,contract.contractId(),id,bound,bound,ack);ExactRef ref=archive.preserveRead(receipt);
            return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,ref);
        }
        ActionReceipt effect(EventActionPreparation.PendingPrepared prepared,PendingUiEvent.Current current,PendingUiEvent.Current after,boolean ack)throws IOException{
            var command=prepared.command();var nativeRequest=EventActionPreparation.prepare(command);
            var observedKnown=new DriverSnapshotFacts.Known(current.known().driver(),current.known().stamp(),current.known().originalHistoryBasis(),current.known().actionRows(),current.known().auxiliary(),current.known().loop(),Optional.of(current.full().facts()));
            ExactRef semantic=archive.preserveMaterial(new RawJson(DriverJson.encode(current.frame().semantic()))),stamp=archive.preserveMaterial(new RawJson(NativeDriverStamp.encode(current.frame(),observedKnown)));
            var actualSemantic=new SemanticEvidence(current.frame().identity(),semantic,current.frame().originalEvidence(),stamp,current.originalDriver(),current.frame().observedAt());
            ExactRef hello=prepared.originalRead().before().binding().capabilityEvidence(),capabilities=archive.preserveMaterial(new RawJson(DriverJson.encodeNode(StrictJson.object().put("software_only",true))));
            String authority="explicit-software-private-event";
            var originals=new RootGuardEvidence.PhysicalReadOriginals(current.frame(),actualSemantic,hello,hello,current.qualifiedCause(),capabilities);
            ExactRef basis=RootGuardEvidence.preservePhysicalRead(originals,command.operation(),authority,archive,same.head());
            var guard=new GuardEvidence(command.before(),command.source(),command.sessionId(),current.frame().connectionGeneration(),command.operation(),current.frame().originalEvidence(),hello,authority,current.frame().observedAt(),DEADLINE,List.of(basis));
            var attempt=new ActionState.Attempt("dispatch-"+command.actionId(),NOW,guard,nativeRequest);byte[] outbound=NativeWire.execute(attempt.requestId(),nativeRequest.step(),command.before().frame().identity().nativeRevision(),nativeRequest.additionalFields().bytes());
            NativeActionPort.DispatchOutcome dispatch;
            if(ack){var token=StrictJson.object().put("step",nativeRequest.step()).put("accepted",true).put("status","submitted");var returned=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",attempt.requestId()).put("ok",true);returned.set("result",token);
                dispatch=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.of(raw(token)),raw(returned),NativeWire.packet(DriverJson.encodeNode(returned)),Optional.of(new NativeActionPort.OutboundPacket(attempt.requestId(),outbound)));
            }else dispatch=new NativeActionPort.Unknown(attempt.requestId(),"software lost return packet",outbound,Optional.empty());
            archive.preserve(dispatch);var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
            var snapshots=new NativeEffectSnapshots(()->{throw new AssertionError("private source must not resolve ordinary held observer");},archive,loader,(retained,deadline)->{assertEquals(command,retained);return Optional.of(after.frame());});
            PlanningReadPort noMaterialReads=new PlanningReadPort(){@Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("private event has no installed extra-material reader");}};
            var actual=new NativeEventEffects(snapshots,noMaterialReads,(NativeEventEffects.MaterialQuerySelection)retained->new NativeEventEffects.MaterialQueries(Optional.empty(),Optional.empty()),NativeEventEffects.ObservedAfter.none()).observe(command,attempt,dispatch);
            ActionState state=actual.result() instanceof ActionPorts.EffectObserved observed?new ActionState.Settled(attempt,dispatch,new ActionState.Applied(observed.observation())):
                dispatch instanceof NativeActionPort.AckReceived received?new ActionState.AckReceived(attempt,received):new ActionState.Unknown(Optional.of(attempt),Optional.of(dispatch),"actual original window still present",List.of(after.frame().originalEvidence()));
            var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),state);archive.preserveReceipt(receipt);return receipt;
        }
    }
}
