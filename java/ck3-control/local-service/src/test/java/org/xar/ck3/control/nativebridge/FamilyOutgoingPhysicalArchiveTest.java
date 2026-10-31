package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.*;

/**
 * Actual transport/coordinator/archive software regression for complete outgoing DATA.
 * The before probe is deliberately a software-only raw boundary, not the missing RootFamilyBridge
 * preparation qualification. No test constructs Ready, Applied, GuardEvidence, chronology or custody.
 * These observations grant no Family5 send/relationship/fee/advance credit.
 */
final class FamilyOutgoingPhysicalArchiveTest {
    @TempDir Path temporary;
    private static final OpportunityJson.Obj EMPTY=new OpportunityJson.Obj(Map.of());
    private static final String BEFORE_STEP="query-software-complete-family-before";
    private static final String BEFORE_CAP="software.query.complete-family-before";
    private static final long HASH=0xF1234567L;
    private static final OperationKey ACTION=new OperationKey("arrange-marriage-73-75");
    private enum Mode { LATER_UNIQUE,SAME_SEM,AMBIGUOUS,MISSING_ROLE,NULL_RECIPIENT,CHANGED_ACTOR,MISSING_PREPARATION,REDIRECTED_SENDER,MISMATCHED_SENDER }

    private final class Harness implements AutoCloseable {
        final ActionWriterIntegrationFixture fixture;
        final ReadContract<FamilyOutgoingCodec.Snapshot> beforeContract,afterContract;
        final RootLifecycleAuthority physical;
        final RootReconciliationAuthority reconciliation;
        final AtomicReference<PlanningReadResult<FamilyOutgoingCodec.Snapshot>> after=new AtomicReference<>();
        final AtomicReference<GuardEvidence> actualPush=new AtomicReference<>();
        final AtomicReference<PlanningReadResult.Known<FamilyOutgoingCodec.Snapshot>> before=new AtomicReference<>();
        final AtomicInteger scopes=new AtomicInteger(),rawReads=new AtomicInteger();
        final AtomicInteger refusedSourceCalls=new AtomicInteger(),missingPreparationChecks=new AtomicInteger();
        final MarriageSendEffects actualMarriageEffects;
        final Mode mode;
        ActionCommand command;
        ActionReceipt unknown;
        Harness(Path root,Mode selected,boolean lostAck)throws Exception{
            mode=selected;var self=new AtomicReference<Harness>();var beforeRef=new AtomicReference<ReadContract<FamilyOutgoingCodec.Snapshot>>();var afterRef=new AtomicReference<ReadContract<FamilyOutgoingCodec.Snapshot>>();
            var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario(InteractionModels.Build.CROZIER4.sha256().toLowerCase(java.util.Locale.ROOT),"family-storage-software",source->{
                // This raw probe tests the exact generic storage wire only; it grants no actual preparation authority.
                ReadContract<FamilyOutgoingCodec.Snapshot> initial=new ReadContract<>("software-family-before-data/v1",new OperationKey(BEFORE_STEP),Optional.of(BEFORE_CAP),BEFORE_CAP,
                        ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                        (request,id)->new NativeRequest(BEFORE_STEP,Optional.of(BEFORE_CAP),raw(StrictJson.object())),FamilyOutgoingPhysicalArchiveTest::decodeStorage,FamilyOutgoingPhysicalArchiveTest::decodeStorage);
                ReadContract<FamilyOutgoingCodec.Snapshot> last=new ReadContract<>("software-family-after-data/v1",new OperationKey(FamilyMarriageSendReads.STEP),Optional.empty(),FamilyMarriageSendReads.PERMISSION,
                        ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.RECONCILIATION_OBSERVATION,source,
                        (request,id)->new NativeRequest(FamilyMarriageSendReads.STEP,Optional.empty(),FamilyMarriageSendReads.nativeFields(FamilyMarriageSendReads.arguments(request.arguments()))),
                        FamilyOutgoingPhysicalArchiveTest::decodeStorage,FamilyOutgoingPhysicalArchiveTest::decodeStorage);
                beforeRef.set(initial);afterRef.set(last);return List.of(initial,last);
            },request->{
                rawReads.incrementAndGet();boolean initial=request.step().equals(BEFORE_STEP);
                return raw(storagePacket(initial,mode));
            },Optional.of(InteractionModels.Build.CROZIER4.version()),java.util.Set.of());
            var action=new ActionWriterIntegrationFixture.SoftwareActionScenario(ACTION,"software.command.family-probe",
                    (original,attempt,dispatch)->{
                        if(!ActionReconciliationScope.activeFor(original))return new ActionPorts.Pending("raw ACK does not prove a family send",List.of(attempt.guard().nativeEvidence()));
                        Harness h=self.get();try{
                            var same=h.fixture.journal.borrowedWriterSession();var identity=ActionReconciliationScope.requireIdentity(original,attempt);var factual=ActionReconciliationScope.requireFrame(original,attempt);
                            h.actualPush.set(ActionReconciliationScope.requireObservationGuard(original,attempt));h.scopes.incrementAndGet();
                            h.reconciliation.currentForCommand(same,original,lease->{
                                assertSame(factual,lease.complete());assertEquals(identity,lease.identity());String head=same.head().digest();
                                var request=PlanningReadRequest.newReconciliation(identity,h.afterContract.operation(),FamilyMarriageSendReads.observationArguments(original,attempt,h.before.get().originalReceipt(),h.before.get().value().senderCharacterId().orElseThrow()),lease.validUntil());
                                h.after.set(h.fixture.reads.read(same,h.afterContract,request));
                                assertEquals(head,same.head().digest(),"read-only observation cannot append history or settle a domain");return null;
                            });
                            if(mode==Mode.MISSING_PREPARATION){
                                var failure=assertThrows(IllegalArgumentException.class,()->h.actualMarriageEffects.observe(same,original,attempt,dispatch,h.fixture.archive.withSession(same)));
                                assertTrue(failure.getMessage().contains("preparation")||failure.getMessage().contains("baseline"),failure.getMessage());
                                assertEquals(0,h.refusedSourceCalls.get(),"missing original manifest fails before an authority could be consulted");h.missingPreparationChecks.incrementAndGet();
                            }
                            return new ActionPorts.Pending("complete raw family DATA has no actual RootFamilyBridge preparation proof",List.of(factual.originalEvidence()));
                        }catch(IOException failure){throw new UncheckedIOException(failure);}
                    },()->{});
            fixture=new ActionWriterIntegrationFixture(root,lostAck,reads,List.of(action));beforeContract=beforeRef.get();afterContract=afterRef.get();self.set(this);
            var denied=new FamilyMarriageSendReads(fixture.observationSource().sourceRef(),new FamilyMarriageSendReads.Authority(){
                public void verifyCurrent(PlanningReadRequest request,FamilyMarriageSendReads.Arguments args){refusedSourceCalls.incrementAndGet();throw new IllegalArgumentException("no actual RootFamilyBridge source installed in this DATA fixture");}
                public void verifyOriginal(PlanningReadReceipt receipt,FamilyMarriageSendReads.Arguments args){refusedSourceCalls.incrementAndGet();throw new IllegalArgumentException("no actual archived RootFamilyBridge source installed in this DATA fixture");}
            });
            java.util.function.Supplier<org.xar.ck3.control.application.driver.HeldDriverObservationPort> noReplacementHeld=()->{throw new AssertionError("canonical reconciliation must use its exact held frame, never create a replacement Held");};
            actualMarriageEffects=new MarriageSendEffects(denied,fixture.reads,new NativeEffectSnapshots(noReplacementHeld,fixture.archive,fixture.frameLoader()),fixture.frameLoader());
            var inputs=fixture.physicalInputs();
            physical=new RootLifecycleAuthority(fixture.writer,fixture.archive,inputs.transport(),inputs.driverAssembler(),inputs.observationAssembler(),inputs.source(),
                    (same,session,source,packet,diagnostics,deadline)->{
                        fixture.writer.requireSession(same);assertEquals(inputs.source(),source);assertEquals(session,diagnostics.session().orElseThrow());fixture.archive.readArtifact(same,packet,WriterContracts.MAX_PIN_BYTES);
                        var pin=same.capturePin(source.sourceRef(),65536);same.verifyPin(pin);ObjectNode proof=StrictJson.object().put("schema","xar.java-root-native-source-proof/v2").put("machine_id",source.machineId()).put("session_id",session.sessionId()).put("scope","software-packet-edge-no-live-family-source-grant");proof.set("source",source.sourceRef().toJson());
                        var ref=fixture.archive.preserveArtifact(same,StrictJson.canonical(proof,65536),65536);
                        return new NativeReadinessCollector.SourceQualification(ref,borrowed->{fixture.writer.requireSession(borrowed);assertSame(same,borrowed);borrowed.verifyPin(pin);});
                    },Clock.systemUTC(),Duration.ofSeconds(30));
            var pending=new ReconciliationPendingBinding(fixture.writer,fixture.archive,inputs.originals());
            reconciliation=new RootReconciliationAuthority(fixture.writer,fixture.archive,physical,pending,inputs.originals(),inputs.frameLoader(),fixture.actualReadCatalog(),
                    (original,identity,data,deadline)->{
                        var retained=RootFamilyMarriageSendRuntime.requireArchivedPendingOriginal(original,identity,data,fixture.archive.withSession(fixture.journal.borrowedWriterSession()));
                        return List.of(new RootReconciliationAuthority.AllowedRead(afterContract,FamilyMarriageSendReads.observationArguments(retained.command(),ActionTransitions.attempt(retained.state()).orElseThrow(),before.get().originalReceipt(),before.get().value().senderCharacterId().orElseThrow()),RootReconciliationAuthority.QueryKind.FAMILY_MARRIAGE_SEND));
                    },Clock.systemUTC());
            reconciliation.requireOwner(fixture.writer,fixture.archive,fixture.actualReadCatalog(),physical);
            var guards=new RootReconciliationReadGuard(reconciliation,()->{try{return fixture.writer.borrowedSession();}catch(IOException failure){throw new UncheckedIOException(failure);}},fixture.archive,inputs.source(),Clock.systemUTC(),"software-family-data-query",inputs.originals(),fixture.actualReadCatalog());
            fixture.bindReconciliationReadGuard(guards);fixture.coordinator.bindReconciliationObservation((same,pendingReceipt,deadline,work)->reconciliation.observe(same,pendingReceipt,deadline,lease->work.apply(lease.complete(),lease.provenance(),lease.identity(),lease.observationGuard())));
        }
        void original()throws Exception{
            var ready=fixture.ready();var planning=ready.request();var request=new PlanningReadRequest(planning.before(),planning.source(),planning.sessionId(),beforeContract.operation(),EMPTY,planning.deadline());
            var result=fixture.reads.read(beforeContract,request);if(result instanceof PlanningReadResult.Known<FamilyOutgoingCodec.Snapshot> known)before.set(known);else fail("actual raw before query unavailable: "+result);
            assertTrue(before.get().value().complete());assertTrue(before.get().value().occupiedPendingIds().isEmpty());
            var basis=fixture.command("software-family-original");var intent=new RulerMarriageIntent("73-75",73,75,Optional.empty());
            command=new ActionCommand(basis.actionId(),basis.before(),basis.source(),basis.sessionId(),ACTION,intent.toJson(),MarriageSendEffects.expected(basis.before(),basis.source(),FamilyMarriageSendReads.sender(intent.toJson(),ACTION.value())),basis.claims(),basis.deadline());
            unknown=fixture.coordinator.execute(command);assertInstanceOf(ActionState.Unknown.class,unknown.state());assertEquals(1,fixture.nativeActionWrites());
            var actual=ActionTransitions.dispatch(unknown.state()).orElseThrow();assertTrue(actual instanceof NativeActionPort.Unknown||actual instanceof NativeActionPort.AckReceived);
            if(actual instanceof NativeActionPort.AckReceived ack){assertTrue(ack.outbound().isPresent());ack.custody().orElseThrow().verify(ack,ActionTransitions.attempt(unknown.state()).orElseThrow().guard());NativeRequestChronology.requireBeforeSubmission(before.get().receipt(),ActionTransitions.attempt(unknown.state()).orElseThrow(),ack);}
            else assertTrue(((NativeActionPort.Unknown)actual).originalRequestPacket().length>4);
            if(mode!=Mode.SAME_SEM)publishLater(mode==Mode.CHANGED_ACTOR);
        }
        void publishLater(boolean actorChanged)throws Exception{
            var previous=fixture.physicalInputs().transport().latestObservedSnapshot().orElseThrow();ObjectNode frame=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","family-original-after").put("revision",previous.nativeRevision().add(BigInteger.ONE));
            var state=fullObject(previous.state().bytes());if(actorChanged)state.set("played_character",StrictJson.object().put("character_id",74).put("alive",true));frame.set("state",state);fixture.enqueueSoftwareNativePacket(NativeWire.packet(raw(frame).bytes()));
        }
        ActionReceipt reconcile()throws Exception{return fixture.coordinator.reconcile(command.actionId());}
        @Override public void close()throws IOException{fixture.close();}
    }

    @Test void physicalWireFiveRolesAndDuplicateRawBankRoundTripThroughRealQueryAndColdSoleArchive()throws Exception{
        for(Mode mode:List.of(Mode.LATER_UNIQUE,Mode.REDIRECTED_SENDER))try(var h=new Harness(temporary.resolve(mode.name()),mode,false)){
            h.original();var result=h.reconcile();assertInstanceOf(ActionState.Unknown.class,result.state());assertEquals(1,h.scopes.get());
            PlanningReadResult.Known<?> known=assertInstanceOf(PlanningReadResult.Known.class,h.after.get());var after=assertInstanceOf(FamilyOutgoingCodec.Snapshot.class,known.value());assertEquals(1,after.candidates().size());assertEquals(0,after.candidates().getFirst().pendingFullId());
            assertEquals(List.of(0xF0000001L,0xF0000001L,0x80000000L),after.candidates().getFirst().options().stream().map(FamilyOutgoingCodec.OptionRow::flag).toList());
            assertEquals(java.util.OptionalLong.of(0),MarriageSendEffects.match(FamilyMarriageSendReads.prepared(storagePacket(true,mode).get("prepared_context")) instanceof FamilyMarriageSendReads.Prepared prepared?prepared:fail("actual native context missing"),h.before.get().value(),after));
            long sender=mode==Mode.REDIRECTED_SENDER?79:73;assertEquals(BigInteger.valueOf(73),after.frame().actor());assertEquals(sender,after.senderCharacterId().orElseThrow());assertEquals(Long.valueOf(sender),after.candidates().getFirst().roles().actor());
            var outgoing=NativeWire.decodeExecuteRequest(known.receipt().original().outbound().orElseThrow().originalPacket());assertEquals(sender,StrictJson.parse(outgoing.normalizedAdditionalFields().value()).get("sender_character_id").longValue());
            assertNotEquals(h.before.get().receipt().requestId(),known.receipt().requestId());var first=h.before.get().receipt().original().custody().orElseThrow();var last=known.receipt().original().custody().orElseThrow();first.verify(h.before.get().receipt());last.verify(known.receipt());assertEquals(first.session(),last.session());assertEquals(first.custodyEpoch(),last.custodyEpoch());assertTrue(first.responseReceived().order().compareTo(last.writeEntered().order())<0);
            int reads=h.fixture.nativeReadWrites(),writes=h.fixture.nativeActionWrites();coldReplay(h,known.receipt(),known.originalReceipt(),after);assertEquals(reads,h.fixture.nativeReadWrites());assertEquals(writes,h.fixture.nativeActionWrites());
            assertEquals(result,h.fixture.coordinator.execute(h.command));assertEquals(result,h.fixture.reopenAndReturnExisting(h.command));assertEquals(1,h.fixture.nativeActionWrites());assertFalse(ActionReconciliationScope.activeFor(h.command));
        }
    }
    @Test void ambiguousExactRowsRemainUnknownAndMissingRoleRetainsOriginalRawFailure()throws Exception{
        for(Mode mode:List.of(Mode.AMBIGUOUS,Mode.MISSING_ROLE,Mode.NULL_RECIPIENT,Mode.MISMATCHED_SENDER))try(var h=new Harness(temporary.resolve(mode.name()),mode,false)){
            h.original();assertInstanceOf(ActionState.Unknown.class,h.reconcile().state());assertEquals(1,h.fixture.nativeActionWrites());
            if(mode==Mode.AMBIGUOUS||mode==Mode.NULL_RECIPIENT){PlanningReadResult.Known<?> known=assertInstanceOf(PlanningReadResult.Known.class,h.after.get());var after=assertInstanceOf(FamilyOutgoingCodec.Snapshot.class,known.value());assertEquals(mode==Mode.AMBIGUOUS?2:1,after.candidates().size());if(mode==Mode.NULL_RECIPIENT)assertNull(after.candidates().getFirst().roles().recipient());var prepared=assertInstanceOf(FamilyMarriageSendReads.Prepared.class,FamilyMarriageSendReads.prepared(storagePacket(true,mode).get("prepared_context")));assertTrue(MarriageSendEffects.match(prepared,h.before.get().value(),after).isEmpty());}
            else{PlanningReadResult.Unavailable<?> unavailable=assertInstanceOf(PlanningReadResult.Unavailable.class,h.after.get());assertTrue(unavailable.original().isPresent());var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original().orElseThrow());assertTrue(ack.custody().isPresent());assertTrue(ack.outbound().isPresent());assertTrue(unavailable.reason().contains("field")||unavailable.reason().contains("role")||unavailable.reason().contains("key")||unavailable.reason().contains("actor"));}
            assertEquals(1,h.fixture.nativeActionWrites());
        }
    }
    @Test void changedActorCannotEnterFamilyObserverAndLostAckDoesNotResubmit()throws Exception{
        try(var changed=new Harness(temporary.resolve("actor"),Mode.CHANGED_ACTOR,false)){
            changed.original();var result=changed.reconcile();var unknown=assertInstanceOf(ActionState.Unknown.class,result.state());assertEquals(0,changed.scopes.get());assertNull(changed.after.get());assertTrue(unknown.evidence().size()>=7);assertEquals(1,changed.fixture.nativeActionWrites());
        }
        try(var lost=new Harness(temporary.resolve("lost"),Mode.LATER_UNIQUE,true)){
            lost.original();assertInstanceOf(NativeActionPort.Unknown.class,ActionTransitions.dispatch(lost.unknown.state()).orElseThrow());var result=lost.reconcile();assertInstanceOf(ActionState.Unknown.class,result.state());assertEquals(1,lost.fixture.nativeActionWrites());assertEquals(result,lost.fixture.coordinator.execute(lost.command));assertEquals(result,lost.fixture.reopenAndReturnExisting(lost.command));assertEquals(1,lost.fixture.nativeActionWrites());
        }
    }
    @Test void unchangedNativeFrameCannotBeUpgradedToAQualifiedLaterEffect()throws Exception{
        try(var h=new Harness(temporary.resolve("same-sem"),Mode.SAME_SEM,false)){
            h.original();var result=h.reconcile();assertInstanceOf(ActionState.Unknown.class,result.state());assertEquals(1,h.fixture.nativeActionWrites());
            if(h.after.get() instanceof PlanningReadResult.Known<?> known){var after=assertInstanceOf(FamilyOutgoingCodec.Snapshot.class,known.value());assertEquals(h.before.get().value().frame().revision(),after.frame().revision(),"a query must not invent a newer native SEM");}
            assertEquals(result,h.fixture.coordinator.execute(h.command));assertEquals(1,h.fixture.nativeActionWrites());
        }
    }
    @Test void completeLaterWireCannotInventTheMissingActualFamilyPreparationOrUpgradeUnknown()throws Exception{
        try(var h=new Harness(temporary.resolve("missing-preparation"),Mode.MISSING_PREPARATION,false)){
            h.original();var result=h.reconcile();assertInstanceOf(ActionState.Unknown.class,result.state());assertEquals(1,h.missingPreparationChecks.get());assertEquals(0,h.refusedSourceCalls.get());assertEquals(1,h.fixture.nativeActionWrites());
            assertTrue(MarriageSendEffects.accepts(h.command));var prepared=ActionTransitions.attempt(result.state()).orElseThrow().preparedRequest();assertTrue(prepared.preparationEvidence().isEmpty(),"existing action12 fixture has the actual missing preparation seam");
            assertEquals(result,h.fixture.coordinator.execute(h.command));assertEquals(1,h.fixture.nativeActionWrites());
        }
    }
    @Test void fullFixturePacketsUseTheExistingDriverLaneAndKeepDuplicateUtf8AndTrailingGuards(){
        var large=StrictJson.object().put("padding","x".repeat(StrictJson.EXPLICIT_MAX_BYTES+1));
        byte[] original=raw(large).bytes();
        assertTrue(original.length>StrictJson.EXPLICIT_MAX_BYTES);
        assertEquals(large,fullObject(original),"the existing full Driver boundary accepts a real body above the general JSON cap");
        assertThrows(IllegalArgumentException.class,()->StrictJson.parse(original,DriverJson.MAX_NATIVE_BYTES),
                "the general StrictJson contract remains capped; it is not widened for this fixture");
        byte[] duplicate=("{\"padding\":\"first\","+new String(original,StandardCharsets.UTF_8).substring(1)).getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->fullObject(duplicate));
        byte[] trailing=java.util.Arrays.copyOf(original,original.length+1);trailing[trailing.length-1]='x';
        assertThrows(IllegalArgumentException.class,()->fullObject(trailing));
        assertThrows(IllegalArgumentException.class,()->fullObject(new byte[]{'{','"',(byte)0xFF,'"',':','0','}'}));
    }
    private static FamilyOutgoingCodec.Snapshot decodeStorage(PlanningReadReceipt receipt){
        JsonNode n=fullObject(receipt.original().originalResultToken().orElseThrow().bytes());var identity=receipt.request().origin() instanceof CommandOrigin.Reconciliation?receipt.request().reconciliationBefore():receipt.request().before();
        var frame=new InteractionModels.Frame(identity.frame().identity().nativeRevision(),identity.frame().identity().dateRaw(),identity.frame().identity().player(),InteractionModels.Build.CROZIER4,StrictJson.integer(n.get("query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX));
        return FamilyOutgoingCodec.decodeGroup(n.get(FamilyOutgoingCodec.GROUP),frame,FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE);
    }
    private static ObjectNode storagePacket(boolean initial,Mode mode){
        long sender=mode==Mode.REDIRECTED_SENDER||mode==Mode.MISMATCHED_SENDER?79:73;ObjectNode n=StrictJson.object().put("query_sequence",initial?20:21);ObjectNode group=StrictJson.object().put("schema",FamilyOutgoingCodec.SCHEMA).put("status","available").put("source","native_complete_outgoing_pending_storage_1.20.0.4").put("producer_scope","complete_outgoing_storage").put("read_only",true).put("complete",true).put("passes",2).put("scanned_slots",4).put("actor_id",73).put("sender_character_id",sender).put("interaction_key","arrange_marriage_interaction").put("definition_stable_hash",HASH);group.putNull("unavailable_reason");var occupied=group.putArray("occupied_pending_full_ids");var candidates=group.putArray("candidates");
        if(!initial)for(int index=0;index<(mode==Mode.AMBIGUOUS?2:1);index++){occupied.add(index);ObjectNode row=candidates.addObject().put("pending_full_id",index).put("definition_stable_hash",HASH).put("interaction_key","arrange_marriage_interaction").put("route_kind",index==0?0:2).put("age_days",0).put("ai_reply_cutoff_days",30);row.set("effective_roles",roles(mode==Mode.MISMATCHED_SENDER?73:sender));row.set("selected_option_rows",options());if(mode==Mode.MISSING_ROLE)((ObjectNode)row.get("effective_roles")).remove("secondary_recipient_id");if(mode==Mode.NULL_RECIPIENT)((ObjectNode)row.get("effective_roles")).putNull("recipient_id");}
        n.set(FamilyOutgoingCodec.GROUP,group);ObjectNode p=StrictJson.object().put("schema","ck3-marriage-materialized-send-context-12004-v2").put("status","available").put("source","original_native_marriage_context_builder").put("read_only",true).put("send_invoked",false).put("command_constructed",false).put("role_arity",5).put("definition_stable_hash",HASH).put("interaction_key","arrange_marriage_interaction").put("complete_can_send",true).put("matrilineal_option_selected",true).put("grand_wedding_option_selected",false).put("copy_passes",2);p.putNull("effective_matrilineal_if_accepted").putNull("sixth_role_id").putNull("unavailable_reason");p.set("effective_roles",roles(sender));p.set("selected_option_rows",options());n.set("prepared_context",p);return n;
    }
    private static ObjectNode roles(long sender){return StrictJson.object().put("actor_id",sender).put("recipient_id",81).put("secondary_actor_id",73).put("secondary_recipient_id",75).putNull("intermediary_id");}
    private static com.fasterxml.jackson.databind.node.ArrayNode options(){var rows=StrictJson.object().putArray("rows");long[] flags={0xF0000001L,0xF0000001L,0x80000000L};for(int index=0;index<flags.length;index++)rows.add(StrictJson.object().put("declared_ordinal",index).put("flag_full_u32",flags[index]).put("bank_value_u8",index==1?0:1));return rows;}
    private static ObjectNode fullObject(byte[] original){
        return assertInstanceOf(ObjectNode.class,OpportunityJson.toNode(DriverJson.object(original,DriverJson.MAX_NATIVE_BYTES)));
    }
    /** Test trees are serialized, then accepted by the existing full-domain parser/encoder before becoming wire DATA. */
    private static RawJson raw(JsonNode node){
        var exact=DriverJson.object(node.toString().getBytes(StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);
        return new RawJson(DriverJson.encode(exact));
    }
    private static void coldReplay(Harness h,PlanningReadReceipt receipt,ExactRef reference,FamilyOutgoingCodec.Snapshot expected)throws Exception{
        byte[] anchor=Files.readAllBytes(h.fixture.root.resolve("anchor.json"));var anchorRef=new ExactRef(h.fixture.root.resolve("anchor.json").toAbsolutePath().normalize().toString(),anchor.length,ActionCodec.sha256(anchor));var layout=new WriterContracts.Layout(h.fixture.root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchorRef,h.fixture.observationSource().machineId());
        var storage=h.fixture.writer.storageGuard();var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(h.fixture.root.resolve("artifacts"),layout.lock(),16*1024*1024),storage);
        var writer=new ContinuityWriter(layout,List.of(h.fixture.observationSource().sourceRef()),new WriterContracts.TransitionAuthority(){public String revalidate(ContinuityState state,WriterContracts.Request request){throw new AssertionError("cold raw replay must append no transition");}public ContinuityState reduce(ContinuityState state,WriterContracts.Request request){throw new AssertionError("cold raw replay must reduce no action");}},Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(),Optional.of(artifacts),Optional.empty()),storage);
        var archive=new NativeOutcomeArchive(artifacts,writer);writer.locked(same->{var bound=archive.withSession(same);PlanningReadReceipt loaded=bound.loadRead(reference);assertEquals(receipt,loaded);assertEquals(reference,bound.readReferenceOf(loaded));NativeRecordedEvidenceVerifier.requireRead(loaded,bound);loaded.original().custody().orElseThrow().verify(loaded);assertEquals(expected,h.afterContract.replay(loaded));return null;});
        h.fixture.writer.locked(same->{
            var bound=h.fixture.archive.withSession(same);var identity=receipt.request().origin().requireReconciliation();
            var retained=bound.loadReceipt(identity.pending().originalReceipt());
            var later=ContinuityActionJournal.lookup(same.head().state(),h.command.actionId(),bound).orElseThrow();
            assertNotEquals(retained,later,"actual reconciliation appended a later UNKNOWN; archive policy must reopen the retained original instead of requiring today's Head equality");
            String head=same.head().digest();int reads=h.fixture.nativeReadWrites(),writes=h.fixture.nativeActionWrites();
            for(var guard:List.of(receipt.before().binding(),receipt.after().binding())){
                var factual=h.reconciliation.verifyArchived(guard,bound,same,h.fixture.physicalInputs().originals());
                assertEquals(receipt.request().reconciliationBefore(),factual.identity());
                assertEquals(retained,RootFamilyMarriageSendRuntime.requireArchivedPendingOriginal(retained,identity,factual,bound));
                assertThrows(IllegalArgumentException.class,()->RootFamilyMarriageSendRuntime.requireArchivedPendingOriginal(later,identity,factual,bound),
                        "a newer canonical receipt cannot replace the archived original bytes");
            }
            assertEquals(head,same.head().digest());assertEquals(reads,h.fixture.nativeReadWrites());assertEquals(writes,h.fixture.nativeActionWrites());return null;
        });
    }
}
