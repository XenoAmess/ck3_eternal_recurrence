package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.InteractionDirectPublicCodec;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.junit.jupiter.api.Assertions.*;

/** Actual framed Driver producer/loader + sole publication producer + original preflight/claim/dispatch + canonical serde. */
final class OrdinaryPendingPublicationArchiveTest {
    @TempDir Path directory;
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z"),DEADLINE=NOW.plusSeconds(60);
    private static final ExactRef SOURCE_REF=new ExactRef("software/ordinary-source",1,"a".repeat(64));
    private static final int FIXTURE_DATE_RAW=org.xar.ck3.control.planning.campaigncadence.CampaignCalendar.dateToRaw("1066.9.15");

    @Test void actualProducerArchiveAndPublicConsumerReplaySameQueueDataWithoutAppliedCredit()throws Exception {
        Fixture fixture=new Fixture();ActionReceipt receipt=fixture.produced();
        var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        var loaded=OrdinaryPendingPublication.load(receipt,fixture.archive,loader,Build.CROZIER3).orElseThrow();
        assertEquals(fixture.publication,loaded.value());assertEquals(fixture.before.actual(),loaded.before().actual());assertEquals(fixture.after.actual(),loaded.after().actual());
        ObjectNode wire=node(InteractionDirectPublicCodec.encode(InteractionDirectPublicCodec.initiation(receipt,fixture.archive,loaded.value())));
        assertFalse(wire.get("business_effects_verified").booleanValue());assertFalse(wire.get("full_product_acceptance_credit").booleanValue());
        assertTrue(wire.path("action_receipt").path("native_ack_received").booleanValue());assertFalse(wire.path("action_receipt").path("postcondition_verified").booleanValue());
        assertFalse(wire.get("replay_allowed").booleanValue());assertEquals("1",wire.get("after_revision").textValue());
        assertEquals(receipt,ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(receipt,fixture.archive),fixture.archive));
        assertEquals(fixture.publication,OrdinaryPendingPublication.load(receipt,fixture.archive,loader,Build.CROZIER3).orElseThrow().value());
    }

    @Test void signedActorOrdinaryPublicationReplaysWithoutAppliedCredit()throws Exception {
        Fixture fixture=new Fixture(-33554431L);
        ActionReceipt receipt=fixture.produced();
        var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        var loaded=OrdinaryPendingPublication.load(receipt,fixture.archive,loader,Build.CROZIER3).orElseThrow();
        
        // Assert signed actor preservation in loaded publication and original claim
        assertEquals(-33554431L,loaded.before().interaction().actor().longValueExact());
        assertEquals(-33554431L,loaded.after().interaction().actor().longValueExact());
        
        // Verify original retained claim actor
        ObjectNode claimBody=node(fixture.archive.loadMaterial(fixture.claim));
        assertEquals(-33554431L,StrictJson.integer(claimBody.get("identity").get("actor_id"),Integer.MIN_VALUE,Integer.MAX_VALUE));
        
        // Verify public codec output maintains no-credit semantics
        ObjectNode wire=node(InteractionDirectPublicCodec.encode(InteractionDirectPublicCodec.initiation(receipt,fixture.archive,loaded.value())));
        assertFalse(wire.get("business_effects_verified").booleanValue());
        assertFalse(wire.get("full_product_acceptance_credit").booleanValue());
        assertTrue(wire.path("action_receipt").path("native_ack_received").booleanValue());
        assertFalse(wire.path("action_receipt").path("postcondition_verified").booleanValue());
        assertFalse(wire.get("replay_allowed").booleanValue());
        
        // Verify roundtrip exactness
        assertEquals(receipt,ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(receipt,fixture.archive),fixture.archive));
        assertEquals(fixture.publication,OrdinaryPendingPublication.load(receipt,fixture.archive,loader,Build.CROZIER3).orElseThrow().value());
    }
    @Test void wrongStoredMaterialRequestOrFrameCannotBecomeNativePublication()throws Exception {
        Fixture fixture=new Fixture();ActionReceipt receipt=fixture.produced();var old=(ActionState.Unknown)receipt.state();
        var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        List<java.util.function.Consumer<ObjectNode>> mutations=List.of(
                row->row.put("request_id","another-request"),row->row.put("command_body_sha256","b".repeat(64)),
                row->row.put("schema","other-schema"),row->row.remove("before"),
                row->row.put("after",true));
        for(var mutate:mutations){ObjectNode body=node(fixture.archive.loadMaterial(old.evidence().getFirst()));mutate.accept(body);
            ExactRef bad=fixture.archive.preserveMaterial(raw(body));List<ExactRef> evidence=new ArrayList<>(old.evidence());evidence.set(0,bad);
            ActionReceipt changed=new ActionReceipt(1,2,receipt.command(),receipt.bodySha256(),new ActionState.Unknown(old.attempt(),old.dispatch(),old.reason(),evidence));
            assertThrows(IllegalArgumentException.class,()->OrdinaryPendingPublication.load(changed,fixture.archive,loader,Build.CROZIER3));}
        ExactRef material=old.evidence().getLast();byte[] original=fixture.archive.read(material);ObjectNode changed=node(new RawJson(original));changed.put("after_snapshot_id","not-the-original-first-after");
        fixture.archive.replaceBytes(material,DriverJson.encodeNode(changed));
        assertThrows(AssertionError.class,()->OrdinaryPendingPublication.load(receipt,fixture.archive,loader,Build.CROZIER3));
        fixture.archive.replaceBytes(material,original);
        assertTrue(OrdinaryPendingPublication.load(receipt,fixture.archive,loader,Build.CROZIER3).isPresent());
        assertThrows(IllegalArgumentException.class,()->OrdinaryPendingPublication.load(receipt,fixture.archive,loader,Build.CROZIER4));
    }
    @Test void laterReconciliationReplaysItsRecordedWindowWithoutExtendingOriginalRequest()throws Exception {
        Fixture fixture=new Fixture(true);ActionReceipt receipt=fixture.produced();
        assertTrue(fixture.after.actual().observedAt().isAfter(receipt.command().deadline()));
        var loaded=OrdinaryPendingPublication.load(receipt,fixture.archive,new DriverFrameEvidenceLoader(new DriverObservationAssembler()),Build.CROZIER3).orElseThrow();
        assertEquals(DEADLINE,receipt.command().deadline());assertEquals(DEADLINE.plusSeconds(30),loaded.after().interaction().deadline());
        assertEquals(fixture.publication,loaded.value());assertTrue(receipt.applied().isEmpty());assertFalse(receipt.settled());
        ObjectNode wire=node(InteractionDirectPublicCodec.encode(InteractionDirectPublicCodec.initiation(receipt,fixture.archive,loaded.value())));
        assertFalse(wire.get("business_effects_verified").booleanValue());assertFalse(wire.get("replay_allowed").booleanValue());
        var unknown=(ActionState.Unknown)receipt.state();ObjectNode basis=node(fixture.archive.loadMaterial(unknown.evidence().getFirst()));
        for(JsonNode wrong:List.of(com.fasterxml.jackson.databind.node.NullNode.getInstance(),com.fasterxml.jackson.databind.node.BooleanNode.TRUE,
                com.fasterxml.jackson.databind.node.TextNode.valueOf(DEADLINE.toString()))) {
            ObjectNode changed=basis.deepCopy();changed.set("after_projection_deadline",wrong);List<ExactRef> evidence=new ArrayList<>(unknown.evidence());evidence.set(0,fixture.archive.preserveMaterial(raw(changed)));
            var bad=new ActionReceipt(1,2,receipt.command(),receipt.bodySha256(),new ActionState.Unknown(unknown.attempt(),unknown.dispatch(),unknown.reason(),evidence));
            assertThrows(IllegalArgumentException.class,()->OrdinaryPendingPublication.load(bad,fixture.archive,new DriverFrameEvidenceLoader(new DriverObservationAssembler()),Build.CROZIER3));
        }
    }
    @Test void legacyV1KeepsOriginalDeadlineAndDoesNotBorrowCurrentWindow()throws Exception {
        Fixture fixture=new Fixture();ActionReceipt current=fixture.produced();var unknown=(ActionState.Unknown)current.state();
        ObjectNode old=node(fixture.archive.loadMaterial(unknown.evidence().getFirst()));old.put("schema",OrdinaryPendingPublication.LEGACY_SCHEMA);old.remove("after_projection_deadline");
        List<ExactRef> evidence=new ArrayList<>(unknown.evidence());evidence.set(0,fixture.archive.preserveMaterial(raw(old)));
        var legacy=new ActionReceipt(1,2,current.command(),current.bodySha256(),new ActionState.Unknown(unknown.attempt(),unknown.dispatch(),unknown.reason(),evidence));
        var loaded=OrdinaryPendingPublication.load(legacy,fixture.archive,new DriverFrameEvidenceLoader(new DriverObservationAssembler()),Build.CROZIER3).orElseThrow();
        assertEquals(fixture.publication,loaded.value());assertEquals(legacy.command().deadline(),loaded.after().interaction().deadline());
    }
    private final class Fixture {
        final Archive archive;final OrdinaryInitiationPreparation.ActualFrame before,after;final ActionCommand command;
        final ActionState.Attempt attempt;final NativeActionPort.AckReceived ack;final ExactRef claim;final RawJson publication;
        Fixture()throws Exception {this(false,7001L);}
        Fixture(boolean late)throws Exception {this(late,7001L);}
        Fixture(long signedActor)throws Exception {this(false,signedActor);}
        Fixture(boolean late,long signedActor)throws Exception {
            archive=new Archive(Files.createDirectory(directory.resolve(UUID.randomUUID().toString())));
            ObjectNode corpus=InteractionDirectPublicProductionTest.original();ObjectNode row=object(corpus.get("initiation"));
            
            // Derive signed actor fixture from unchanged Python corpus baseline
            ObjectNode signedFrame=object(row.get("frame")).deepCopy();
            signedFrame.put("episode_character_id",signedActor).put("date_raw",FIXTURE_DATE_RAW);
            ObjectNode player=object(signedFrame.get("played_character"));
            player.put("character_id",signedActor);
            
            before=actual(signedFrame,NOW,DEADLINE);after=actual(signedFrame,NOW.plusSeconds(late?70:1),late?DEADLINE.plusSeconds(30):DEADLINE);
            Context current=before.interaction();var request=new OrdinaryRequest(new InteractionKey("ordinary_fixture_interaction"),new CharacterId(2147483650L),Optional.empty());
            var intent=new org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent(request.interaction().value(),request.recipient().value(),Optional.empty(),Optional.empty());
            command=new ActionCommand("software-ordinary-pending-archive",current.before(),current.source(),current.sessionId(),new OperationKey(OrdinaryInteractionCodec.INITIATE_STEP),intent.toJson(),
                    OrdinaryPendingPublication.requestExpectation(current),new Claims(Set.of(),Set.of(),Set.of(),Set.of("foreground-window")),DEADLINE);
            String requestId="software-pending-original-request";
            var identity=new OrdinaryOnceClaims.Identity(current.before().machineId(),current.before().game().pid(),current.before().game().creationFiletime().value().toString(),current.actor().longValueExact(),request.interaction().value(),request.recipient().value());
            var binding=new OrdinaryOnceClaims.Binding(current.before().frame().snapshotId(),current.before().frame().revision().toString(),current.revision().toString(),current.date().toString(),current.connectionGeneration().toString(),current.before().frame().episodeRunId());
            var claimed=OrdinaryOnceClaims.prepareClaim(new OrdinaryOnceClaims.State(current.before().machineId(),List.of(),List.of(),List.of()),new OrdinaryOnceClaims.Request(identity,binding,requestId));
            claim=archive.preserveMaterial(new RawJson(OrdinaryOnceClaims.encodeClaim(claimed)));
            var query=new PlanningReadRequest(current.before(),current.source(),current.sessionId(),new OperationKey(OrdinaryInteractionCodec.QUERY_STEP),
                    InteractionArguments.app(InteractionArguments.body(current)),DEADLINE);
            
            // Derive signed query result from unchanged Python corpus baseline
            ObjectNode signedQuery=object(corpus.get("ordinary").get(0).get("native")).deepCopy();
            signedQuery.put("date_raw",FIXTURE_DATE_RAW);
            object(signedQuery.get("character_interaction_ordinary_context")).put("player_character_id",signedActor).put("date_raw",FIXTURE_DATE_RAW);
            RawJson queryResult=raw(signedQuery);
            var queryReceipt=InteractionDirectPublicProductionTest.receipt(ordinaryQuery(),query,queryResult);archive.preserveRead(queryReceipt);archive.preserve(queryReceipt.original());
            var nativeBase=new NativeRequest(OrdinaryInteractionCodec.INITIATE_STEP,OrdinaryInteractionCodec.INITIATE_CAPABILITY,OrdinaryInteractionCodec.request(current,request,true));
            List<ExactRef> prepared=GuardianOutgoingEffects.preservePreparation(command,requestId,queryReceipt,new OrdinaryOnceClaims.RetainedClaim(claimed,claim),nativeBase,Optional.empty(),archive);
            var nativeRequest=new NativeRequest(nativeBase.step(),nativeBase.requiredCapability(),nativeBase.additionalFields(),prepared);archive.preserveRequest(nativeRequest);
            var guard=new GuardEvidence(current.before(),current.source(),current.sessionId(),current.connectionGeneration(),command.operation(),before.actual().originalEvidence(),before.actual().originalEvidence(),"software-original-ordinary",NOW,DEADLINE);
            attempt=new ActionState.Attempt(requestId,NOW,guard,nativeRequest);
            
            // Derive signed initiation token from unchanged Python corpus baseline
            ObjectNode signedInitiation=object(row.get("native")).deepCopy();
            ObjectNode initiationBody=object(signedInitiation.get("character_interaction_ordinary_initiation"));
            signedInitiation.put("date_raw",FIXTURE_DATE_RAW);
            initiationBody.put("player_character_id",signedActor).put("date_raw",FIXTURE_DATE_RAW);
            object(initiationBody.get("preflight_context")).put("player_character_id",signedActor).put("date_raw",FIXTURE_DATE_RAW);
            RawJson token=raw(signedInitiation);
            ObjectNode envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",requestId).put("ok",true);envelope.set("result",node(token));
            byte[] outgoing=NativeWire.execute(requestId,nativeRequest.step(),current.revision(),nativeRequest.additionalFields().bytes());
            byte[] body=DriverJson.encodeNode(envelope);
            ack=new NativeActionPort.AckReceived(requestId,true,Optional.of(token),new RawJson(body),NativeWire.packet(body),Optional.of(new NativeActionPort.OutboundPacket(requestId,outgoing)));archive.preserve(ack);
            publication=OrdinaryInitiationPreparation.projectPending(token,current,after.actual(),requestId,claim);
        }
        ActionReceipt produced(){
            ExactRef basis=OrdinaryPendingPublication.preserve(command,attempt,ack,before,after,claim,publication,archive);
            var state=new ActionState.Unknown(Optional.of(attempt),Optional.of(ack),"queue DATA remains pending",List.of(basis,after.actual().originalEvidence(),archive.referenceOf(ack),archive.materialReferenceOf(publication)));
            var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),state);archive.preserveReceipt(receipt);return receipt;
        }
        OrdinaryInitiationPreparation.ActualFrame actual(ObjectNode original,Instant observed,Instant recordedDeadline)throws Exception {
            ObjectNode state=original.deepCopy();ObjectNode player=object(state.get("played_character"));player.putNull("betrothed_id").putNull("primary_spouse_id");player.putArray("spouse_ids");
            state.putArray("active_wars");state.putArray("player_armies");state.putNull("one_life_terminal_reason");
            ObjectNode packet=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id",original.get("snapshot_id").textValue()).put("revision",7);packet.set("state",state);
            byte[] body=DriverJson.encodeNode(packet),framed=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
            var game=new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001")));
            var nativeFrame=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("software-direct-public",game,BigInteger.TWO,"software-direct-session"),original.get("snapshot_id").textValue(),BigInteger.valueOf(7),raw(state),framed,observed);
            
            // The original Python corpus remains positive; this Java-derived frame keeps its public actor domain.
            byte[] originalDriver=DRIVER.getBytes(StandardCharsets.UTF_8);
            long actor=NativeCharacterId.fromJson(state.get("episode_character_id")).value();
            if(actor!=7001L) {
                ObjectNode driver=node(new RawJson(originalDriver));driver.put("episode_character_id",actor);
                originalDriver=DriverJson.encodeNode(driver);
            }
            ExactRef imported=archive.preserveMaterial(new RawJson(originalDriver));
            DriverSnapshotFacts.Known known=DriverFactsRepository.imported(imported,originalDriver,3,7,game,new OpportunityJson.Obj(Map.of()));
            RawJson full=new RawJson(known.driver().encode());ExactRef fullRef=archive.preserveMaterial(full);
            var source=new G2Source("software-direct-public",NOW.toString(),Build.CROZIER3.version(),SOURCE_REF);
            ObjectNode extras=StrictJson.object();extras.set("diagnostics",state.get("diagnostics"));extras.put("backend_id","native-headless");
            RawJson manifest=DriverObservationEvidenceReader.encode(known,nativeFrame,BigInteger.ONE,3,source,DriverJson.object(DriverJson.encodeNode(extras),65536),fullRef);
            ExactRef facts=archive.preserveMaterial(manifest);var actualFacts=DriverObservationEvidenceReader.decode(facts,manifest,full,nativeFrame);
            ExactRef nativeRef=archive.preserveNativeFrame(nativeFrame);var complete=new DriverObservationAssembler().assemble(nativeFrame,actualFacts,nativeRef);
            assertInstanceOf(DriverObservationAssembler.Complete.class,complete,complete.toString());var actual=(DriverObservationAssembler.Complete)complete;
            return new OrdinaryInitiationPreparation.ActualFrame(actual,new RootInteractionContextProjection(Build.CROZIER3).project(actual,recordedDeadline));
        }
    }
    private static ReadContract<OrdinaryContext> ordinaryQuery(){
        var refs=new InteractionCapabilities.Sources(SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF,SOURCE_REF);
        return new InteractionCapabilities.Installation(refs,new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of()),new InteractionCapabilities.RootHeirSource(){
            @Override public PlanningReadResult<HeirSubject> read(Context ignored){throw new AssertionError();}
            @Override public PlanningReadResult<HeirSubject> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,Context ignored){throw new AssertionError();}
        }).ordinaryQuery();
    }
    private static final String DRIVER="""
        {"format_version":2,"pipe_name":"software-ordinary","bridge_pid":991,"episode_character_id":7001,"episode_run_id":"synthetic-ordinary-episode",
         "last_checkpoint":null,"command_history":[],"rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,
         "succession_lifecycle":{},"campaign_goal":null,"rollback_war_failures":[]}
        """;
    private static ObjectNode object(JsonNode value){assertInstanceOf(ObjectNode.class,value);return (ObjectNode)value;}
    private static ObjectNode node(RawJson value){return object(DriverJson.toNode(DriverJson.object(value.bytes(),DriverJson.MAX_NATIVE_BYTES)));}
    private static RawJson raw(JsonNode value){return new RawJson(DriverJson.encodeNode(value));}

    private static final class Archive implements ActionPorts.OutcomeArchive {
        private final Path root;
        private final Map<ExactRef,ActionReceipt> receipts=new HashMap<>();
        private final Map<ExactRef,NativeActionPort.DispatchOutcome> dispatches=new HashMap<>();
        private final Map<ExactRef,NativeRequest> requests=new HashMap<>();
        private final Map<ExactRef,PlanningReadReceipt> reads=new HashMap<>();
        private Archive(Path root){this.root=root;}
        private ExactRef store(String kind,byte[] raw){
            try{Path file=root.resolve(kind+"-"+DriverJson.sha256(raw)+".bin");
                if(Files.exists(file))assertArrayEquals(raw,Files.readAllBytes(file));else Files.write(file,raw,StandardOpenOption.CREATE_NEW);
                return new ExactRef(file.toString(),raw.length,DriverJson.sha256(raw));
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        private void replaceBytes(ExactRef reference,byte[] bytes){try{Files.write(Path.of(reference.path()),bytes,StandardOpenOption.TRUNCATE_EXISTING);}catch(IOException failure){throw new UncheckedIOException(failure);}}
        private byte[] read(ExactRef reference){
            assertEquals(root,Path.of(reference.path()).getParent());
            try{byte[] raw=Files.readAllBytes(Path.of(reference.path()));assertEquals(reference.bytes(),raw.length);assertEquals(reference.sha256(),DriverJson.sha256(raw));return raw;}
            catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        @Override public ExactRef preserveMaterial(RawJson raw){return store("material",raw.bytes());}
        @Override public RawJson loadMaterial(ExactRef reference){return new RawJson(read(reference));}
        @Override public RawJson loadFullMaterial(ExactRef reference){return RawJson.fullMaterial(read(reference));}
        @Override public ExactRef materialReferenceOf(RawJson raw){ExactRef ref=store("material",raw.bytes());assertArrayEquals(raw.bytes(),read(ref));return ref;}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame raw){return store("native",raw.originalPacket());}
        @Override public byte[] loadNativeFrame(ExactRef reference){return read(reference);}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome raw){
            byte[] bytes=raw instanceof NativeActionPort.Unknown unknown?unknown.originalRequestPacket():assertInstanceOf(NativeActionPort.AckReceived.class,raw).originalPacket();
            ExactRef ref=store("dispatch",bytes);dispatches.putIfAbsent(ref,raw);assertEquals(raw,dispatches.get(ref));return ref;
        }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef reference){read(reference);return java.util.Objects.requireNonNull(dispatches.get(reference));}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome raw){return preserve(raw);}
        @Override public ExactRef preserveRequest(NativeRequest raw){
            ObjectNode body=StrictJson.object().put("step",raw.step()).put("capability",raw.requiredCapability().orElse(""));body.set("additional",StrictJson.parse(raw.additionalFields().bytes()));
            ExactRef ref=store("request",StrictJson.canonical(body));requests.putIfAbsent(ref,raw);assertEquals(raw,requests.get(ref));return ref;
        }
        @Override public NativeRequest loadRequest(ExactRef reference){read(reference);return java.util.Objects.requireNonNull(requests.get(reference));}
        @Override public ExactRef requestReferenceOf(NativeRequest raw){return preserveRequest(raw);}
        @Override public ExactRef preserveReceipt(ActionReceipt raw){ExactRef ref=store("receipt",ActionReceiptCodec.encodeReceipt(raw,this));receipts.putIfAbsent(ref,raw);return ref;}
        @Override public ActionReceipt loadReceipt(ExactRef reference){read(reference);return java.util.Objects.requireNonNull(receipts.get(reference));}
        @Override public ExactRef receiptReferenceOf(ActionReceipt raw){ExactRef ref=store("receipt",ActionReceiptCodec.encodeReceipt(raw,this));assertEquals(raw,receipts.get(ref));return ref;}
        @Override public ExactRef preserveRead(PlanningReadReceipt raw){ExactRef ref=store("read",DriverJson.encodeNode(StrictJson.object().put("contract_id",raw.contractId()).put("request_id",raw.requestId()).put("snapshot_id",raw.request().before().frame().snapshotId()).set("original",referenceOf(raw.original()).toJson())));reads.putIfAbsent(ref,raw);return ref;}
        @Override public PlanningReadReceipt loadRead(ExactRef reference){read(reference);return Objects.requireNonNull(reads.get(reference));}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt raw){return preserveRead(raw);}
        @Override public ExactRef preserveRecord(ActionRecord raw){throw new UnsupportedOperationException("no canonical writer in software fixture");}
        @Override public ActionRecord loadRecord(ExactRef reference){throw new UnsupportedOperationException("no canonical writer in software fixture");}
        @Override public ExactRef recordReferenceOf(ActionRecord raw){throw new UnsupportedOperationException("no canonical writer in software fixture");}
    }

}
