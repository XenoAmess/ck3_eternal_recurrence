package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import org.xar.ck3.control.application.driver.DriverPendingEpisodeSource;
import org.xar.ck3.control.application.driver.DriverPendingEpisodeProjection;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Frame;

/** Single domain body. It records actual artifacts and never grants natural succession by construction. */
public final class NaturalClockOriginals {
    public static final String SCHEMA=DriverPendingEpisodeSource.DOMAIN_SCHEMA;
    public static final int MAX_BYTES=65_536;
    private NaturalClockOriginals() { }
    public record Capture(String parentActionId,String parentBodySha256,ExactRef parentCommand,
            String clockActionId,String clockBodySha256,ExactRef clockCommand,
            String machineId,String sessionId,long gamePid,String gameBirthFiletime,String connectionGeneration,
            String episodeRunId,G2Source source,Frame predecessorFrame,ExactRef executable,String executableFileId,String executableMtimeNs,
            ExactRef rootRead,ExactRef rootResult,ExactRef nativePacket,ExactRef semantic,
            ExactRef driverStamp,ExactRef driver,ExactRef hello,Optional<ExactRef> sourceQualification,
            String headBeforeCapture,long ledgerSequenceBeforeCapture,Optional<ExactRef> replacementProof) {
        public Capture {
            for(String value:List.of(parentActionId,clockActionId,machineId,sessionId,episodeRunId))StrictJson.text(value);
            digest(parentBodySha256);digest(clockBodySha256);digest(headBeforeCapture);
            StrictJson.require(gamePid>0 && gamePid<=0xffff_ffffL,"actual Game PID"); decimal(gameBirthFiletime,true);decimal(connectionGeneration,true);
            StrictJson.safe(ledgerSequenceBeforeCapture,0); Objects.requireNonNull(source); Objects.requireNonNull(predecessorFrame);
            Objects.requireNonNull(executable);StrictJson.require(executableFileId!=null && executableFileId.matches("0|[1-9][0-9]{0,38}") && new BigInteger(executableFileId).bitLength()<=128,"canonical executable FileID128");decimal(executableMtimeNs,false);
            StrictJson.require(source.machineId().equals(machineId),"capture source machine");
            for(ExactRef ref:List.of(parentCommand,clockCommand,rootRead,rootResult,nativePacket,semantic,driverStamp,driver,hello))StrictJson.require(ref!=null && ref.bytes()>0,"actual preclock original artifact");
            Objects.requireNonNull(sourceQualification);sourceQualification.ifPresent(ref->StrictJson.require(ref.bytes()>0,"actual source qualification required"));
            Objects.requireNonNull(replacementProof);replacementProof.ifPresent(ref->StrictJson.require(ref.bytes()>0,"actual new-Game source admission"));
        }
        public Capture(String parentActionId,String parentBodySha256,ExactRef parentCommand,
                String clockActionId,String clockBodySha256,ExactRef clockCommand,
                String machineId,String sessionId,long gamePid,String gameBirthFiletime,String connectionGeneration,
                String episodeRunId,G2Source source,Frame predecessorFrame,ExactRef executable,String executableFileId,String executableMtimeNs,
                ExactRef rootRead,ExactRef rootResult,ExactRef nativePacket,ExactRef semantic,
                ExactRef driverStamp,ExactRef driver,ExactRef hello,ExactRef sourceQualification,
                String headBeforeCapture,long ledgerSequenceBeforeCapture,Optional<ExactRef> replacementProof) {
            this(parentActionId,parentBodySha256,parentCommand,clockActionId,clockBodySha256,clockCommand,machineId,sessionId,gamePid,gameBirthFiletime,connectionGeneration,episodeRunId,source,predecessorFrame,executable,executableFileId,executableMtimeNs,rootRead,rootResult,nativePacket,semantic,driverStamp,driver,hello,Optional.of(sourceQualification),headBeforeCapture,ledgerSequenceBeforeCapture,replacementProof);
        }
        public List<ExactRef> artifacts() { var refs=new ArrayList<>(List.of(parentCommand,clockCommand,rootRead,rootResult,nativePacket,semantic,driverStamp,driver,hello));sourceQualification.ifPresent(refs::add);replacementProof.ifPresent(refs::add);return List.copyOf(refs); }
    }
    public record ReadArtifact(ExactRef receipt,ExactRef frame,String requestId,Frame actualFrame,ExactRef semantic) {
        public ReadArtifact { Objects.requireNonNull(receipt);Objects.requireNonNull(frame);StrictJson.text(requestId);Objects.requireNonNull(actualFrame);Objects.requireNonNull(semantic); }
    }
    public record Ready(String parentActionId,String parentBodySha256,ExactRef parentCommand,
            ExactRef predecessorDeath,ReadArtifact initialTimeline,Optional<ExactRef> closeReceipt,
            List<ReadArtifact> subsequentTimeline,ExactRef finalNativePacket,ExactRef finalSemantic,
            ExactRef finalDriver,Optional<ExactRef> finalSourceQualification) {
        public Ready {
            StrictJson.text(parentActionId);digest(parentBodySha256);Objects.requireNonNull(parentCommand);Objects.requireNonNull(predecessorDeath);Objects.requireNonNull(initialTimeline);Objects.requireNonNull(closeReceipt);subsequentTimeline=List.copyOf(subsequentTimeline);
            Objects.requireNonNull(finalNativePacket);Objects.requireNonNull(finalSemantic);Objects.requireNonNull(finalDriver);Objects.requireNonNull(finalSourceQualification);
            finalSourceQualification.ifPresent(ref->StrictJson.require(ref.bytes()>0,"actual final source qualification required"));
            StrictJson.require(closeReceipt.isPresent()? !subsequentTimeline.isEmpty() && subsequentTimeline.size()<=8 : subsequentTimeline.isEmpty(),"one actual Close has one to eight independent later reads");
        }
        public Ready(String parentActionId,String parentBodySha256,ExactRef parentCommand,
                ExactRef predecessorDeath,ReadArtifact initialTimeline,Optional<ExactRef> closeReceipt,
                List<ReadArtifact> subsequentTimeline,ExactRef finalNativePacket,ExactRef finalSemantic,
                ExactRef finalDriver,ExactRef finalSourceQualification) {
            this(parentActionId,parentBodySha256,parentCommand,predecessorDeath,initialTimeline,closeReceipt,subsequentTimeline,finalNativePacket,finalSemantic,finalDriver,Optional.of(finalSourceQualification));
        }
        public List<ExactRef> artifacts() {
            List<ExactRef> values=new ArrayList<>(List.of(parentCommand,predecessorDeath,initialTimeline.receipt(),initialTimeline.frame(),initialTimeline.semantic(),finalNativePacket,finalSemantic,finalDriver));
            finalSourceQualification.ifPresent(values::add);
            closeReceipt.ifPresent(values::add);for(ReadArtifact read:subsequentTimeline)values.addAll(List.of(read.receipt(),read.frame(),read.semantic()));return List.copyOf(values);
        }
    }
    public record MutationArtifact(long sequence,ExactRef beforeDriver,ExactRef afterDriver,ExactRef afterAuxiliary,
            ExactRef beforeObligation,ExactRef afterObligation,Optional<ExactRef> result,Optional<ExactRef> m3Finalization) {
        public MutationArtifact {StrictJson.safe(sequence,1);for(ExactRef ref:List.of(beforeDriver,afterDriver,afterAuxiliary,beforeObligation,afterObligation))StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"nonempty actual pending mutation original required");Objects.requireNonNull(result);Objects.requireNonNull(m3Finalization);result.ifPresent(ref->StrictJson.require(ref.bytes()>0,"actual pending result required"));m3Finalization.ifPresent(ref->StrictJson.require(ref.bytes()>0,"actual M3 finalization required"));}
        public List<ExactRef> artifacts(){var refs=new ArrayList<>(List.of(beforeDriver,afterDriver,afterAuxiliary,beforeObligation,afterObligation));result.ifPresent(refs::add);m3Finalization.ifPresent(refs::add);return List.copyOf(refs);}
    }
    /** Durable once-date intent; records an exact already-issued Life child and material Close originals. */
    public record DateIntent(String actionId,String bodySha256,ExactRef command,ExactRef closeReceipt,ExactRef materialClearance,Instant observedAtUtc,
            Optional<ExactRef> previousDocument,Optional<ExactRef> previousReceipt) {
        public DateIntent(String actionId,String bodySha256,ExactRef command,ExactRef closeReceipt,ExactRef materialClearance,Instant observedAtUtc){this(actionId,bodySha256,command,closeReceipt,materialClearance,observedAtUtc,Optional.empty(),Optional.empty());}
        public DateIntent {StrictJson.text(actionId);digest(bodySha256);for(var ref:List.of(command,closeReceipt,materialClearance))StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"actual once-date originals required");Objects.requireNonNull(observedAtUtc);Objects.requireNonNull(previousDocument);Objects.requireNonNull(previousReceipt);previousDocument.ifPresent(ref->StrictJson.require(ref.bytes()>0,"actual previous date document required"));previousReceipt.ifPresent(ref->StrictJson.require(ref.bytes()>0,"actual previous date receipt required"));StrictJson.require(previousDocument.isPresent()==previousReceipt.isPresent(),"a later date child must retain its actual settled predecessor and canonical document");StrictJson.require(command.sha256().equals(bodySha256),"once-date command digest differs");}
        public List<ExactRef> artifacts(){var refs=new ArrayList<>(List.of(command,closeReceipt,materialClearance));previousDocument.ifPresent(refs::add);previousReceipt.ifPresent(refs::add);return List.copyOf(refs);}
    }
    /** One immutable selected UI action; earlier actions remain in an exact archived chain and canonical parent. */
    public record EventIntent(String machineId,long ordinal,String actionId,String bodySha256,ExactRef command,ExactRef originalRead,
            int instanceId,boolean interaction,List<ExactRef> sourceOriginals,Optional<ExactRef> previous,
            Optional<ExactRef> originalReceipt,Optional<ExactRef> confirmedReceipt,Instant observedAtUtc) {
        public EventIntent {StrictJson.text(machineId);StrictJson.safe(ordinal,1);StrictJson.text(actionId);digest(bodySha256);Objects.requireNonNull(command);Objects.requireNonNull(originalRead);Objects.requireNonNull(observedAtUtc);sourceOriginals=List.copyOf(sourceOriginals);Objects.requireNonNull(previous);Objects.requireNonNull(originalReceipt);Objects.requireNonNull(confirmedReceipt);StrictJson.require(command.bytes()>0&&originalRead.bytes()>0&&sourceOriginals.stream().allMatch(ref->ref.bytes()>0),"nonempty actual event originals required");previous.ifPresent(ref->StrictJson.require(ref.bytes()>0,"actual previous event original required"));originalReceipt.ifPresent(ref->StrictJson.require(ref.bytes()>0,"actual event receipt required"));confirmedReceipt.ifPresent(ref->StrictJson.require(ref.bytes()>0,"actual confirmed event receipt required"));StrictJson.require(instanceId!=-1&&!sourceOriginals.isEmpty()&&sourceOriginals.size()<=32&&command.sha256().equals(bodySha256),"actual finite once-event originals required");StrictJson.require(confirmedReceipt.isEmpty()||originalReceipt.isPresent(),"confirmed event result must retain its original result");}
        public List<ExactRef> artifacts(){var refs=new ArrayList<>(List.of(command,originalRead));refs.addAll(sourceOriginals);previous.ifPresent(refs::add);originalReceipt.ifPresent(refs::add);confirmedReceipt.ifPresent(refs::add);return List.copyOf(refs);}
    }
    /** Exact immutable initial child plus the latest canonical finite UI mutation. No parsed field grants authority. */
    public record PendingProjection(DriverPendingEpisodeProjection value,ExactRef original,Optional<MutationArtifact> latestMutation,Optional<DateIntent> dateIntent,Optional<EventIntent> eventIntent,Optional<ExactRef> eventDiagnosis) {
        public PendingProjection {
            Objects.requireNonNull(value);Objects.requireNonNull(original);Objects.requireNonNull(latestMutation);Objects.requireNonNull(dateIntent);Objects.requireNonNull(eventIntent);Objects.requireNonNull(eventDiagnosis);eventDiagnosis.ifPresent(ref->StrictJson.require(ref.bytes()>0,"actual pending event diagnosis required"));byte[] bytes=value.encode();
            StrictJson.require(original.bytes()==bytes.length&&original.sha256().equals(DriverJson.sha256(bytes)),"canonical pending projection reference differs from its sole child codec");
        }
        public PendingProjection(DriverPendingEpisodeProjection value,ExactRef original){this(value,original,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());}
        public PendingProjection(DriverPendingEpisodeProjection value,ExactRef original,Optional<MutationArtifact> mutation){this(value,original,mutation,Optional.empty(),Optional.empty(),Optional.empty());}
        public PendingProjection(DriverPendingEpisodeProjection value,ExactRef original,Optional<MutationArtifact> mutation,Optional<DateIntent> date){this(value,original,mutation,date,Optional.empty(),Optional.empty());}
        public PendingProjection(DriverPendingEpisodeProjection value,ExactRef original,Optional<MutationArtifact> mutation,Optional<DateIntent> date,Optional<EventIntent> event){this(value,original,mutation,date,event,Optional.empty());}
        public ExactRef currentObligation(){return latestMutation.map(MutationArtifact::afterObligation).orElse(value.obligation());}
        public long mutationSequence(){return latestMutation.map(MutationArtifact::sequence).orElse(0L);}
        public List<ExactRef> artifacts(){var refs=new ArrayList<>(List.of(original,value.beforeDriver(),value.afterDriver(),value.auxiliary(),value.obligation(),value.qualifiedCause()));latestMutation.ifPresent(actual->refs.addAll(actual.artifacts()));dateIntent.ifPresent(actual->refs.addAll(actual.artifacts()));eventIntent.ifPresent(actual->refs.addAll(actual.artifacts()));eventDiagnosis.ifPresent(refs::add);return List.copyOf(refs);}
    }
    public record Document(Capture capture,Optional<Ready> ready,Optional<PendingProjection> pendingProjection,Instant observedAtUtc) {
        public Document {
            Objects.requireNonNull(capture);Objects.requireNonNull(ready);Objects.requireNonNull(pendingProjection);Objects.requireNonNull(observedAtUtc);
            pendingProjection.flatMap(PendingProjection::eventIntent).ifPresent(event->StrictJson.require(event.machineId().equals(capture.machineId()),"event original crossed actual machine"));
            if(pendingProjection.isPresent()) {
                StrictJson.require(ready.isPresent(),"pending projection requires the actual retained causal originals");var actual=pendingProjection.orElseThrow().value();
                StrictJson.require(actual.game().pid()==capture.gamePid()&&actual.game().creationFiletime().value().toString().equals(capture.gameBirthFiletime())
                        &&actual.oldEpisodeRunId().equals(capture.episodeRunId())&&actual.oldActor().intValueExact()==capture.predecessorFrame().actorCharacterId()
                        &&actual.newActor().intValueExact()==ready.orElseThrow().initialTimeline().actualFrame().actorCharacterId(),"pending child crosses its original physical Game/predecessor/actual successor");
            }
        }
        /** Explicit DATA construction for original non-pending callers. Actual native producers pass their actual frame time. */
        public Document(Capture capture,Optional<Ready> ready){this(capture,ready,Optional.empty(),Instant.parse(capture.source().observedAtUtc()));}
        public List<ExactRef> artifacts() { List<ExactRef> refs=new ArrayList<>(capture.artifacts());ready.ifPresent(value->refs.addAll(value.artifacts()));pendingProjection.ifPresent(value->refs.addAll(value.artifacts()));return refs.stream().distinct().toList(); }
    }
    public static byte[] encode(Document document) {
        ObjectNode root=StrictJson.object().put("schema",SCHEMA).put("machine_id",document.capture().machineId()).put("observed_at_utc",document.observedAtUtc().toString());root.set("capture",capture(document.capture()));
        if(document.ready().isEmpty())root.putNull("ready");else root.set("ready",ready(document.ready().orElseThrow()));
        if(document.pendingProjection().isEmpty())root.putNull("pending_projection");else {var value=document.pendingProjection().orElseThrow();var row=root.putObject("pending_projection");row.set("value",OpportunityJson.toNode(value.value().toJson()));row.set("original",value.original().toJson());if(value.latestMutation().isPresent())row.set("latest_mutation",mutation(value.latestMutation().orElseThrow()));else row.putNull("latest_mutation");if(value.dateIntent().isPresent())row.set("date_intent",dateIntent(value.dateIntent().orElseThrow()));else row.putNull("date_intent");if(value.eventIntent().isPresent())row.set("event_intent",eventIntent(value.eventIntent().orElseThrow()));else row.putNull("event_intent");if(value.eventDiagnosis().isPresent())row.set("event_diagnosis",value.eventDiagnosis().orElseThrow().toJson());else row.putNull("event_diagnosis");}
        return StrictJson.canonical(root,MAX_BYTES);
    }
    public static Document decode(byte[] bytes) {
        ObjectNode root=StrictJson.object(StrictJson.parse(bytes,MAX_BYTES),Set.of("schema","machine_id","observed_at_utc","capture","ready","pending_projection"));StrictJson.require(SCHEMA.equals(text(root,"schema")),"natural original v2 schema required; v1 originals are never aliased/upgraded");
        Capture capture=capture(root.get("capture"));StrictJson.require(text(root,"machine_id").equals(capture.machineId()),"actual natural original machine differs");
        Optional<PendingProjection> pending=Optional.empty();
        if(!root.get("pending_projection").isNull()){var row=StrictJson.object(root.get("pending_projection"),Set.of("value","original","latest_mutation","date_intent","event_intent","event_diagnosis"));pending=Optional.of(new PendingProjection(DriverPendingEpisodeProjection.fromJson(OpportunityJson.object(DriverJson.fromNode(row.get("value")),"canonical pending child")),ref(row,"original"),row.get("latest_mutation").isNull()?Optional.empty():Optional.of(mutation(row.get("latest_mutation"))),row.get("date_intent").isNull()?Optional.empty():Optional.of(dateIntent(row.get("date_intent"))),row.get("event_intent").isNull()?Optional.empty():Optional.of(eventIntent(row.get("event_intent"))),row.get("event_diagnosis").isNull()?Optional.empty():Optional.of(ref(row,"event_diagnosis"))));}
        return new Document(capture,root.get("ready").isNull()?Optional.empty():Optional.of(ready(root.get("ready"))),pending,Instant.parse(text(root,"observed_at_utc")));
    }
    private static ObjectNode dateIntent(DateIntent v){var row=StrictJson.object().put("action_id",v.actionId()).put("body_sha256",v.bodySha256()).put("observed_at_utc",v.observedAtUtc().toString());row.set("command",v.command().toJson());row.set("close_receipt",v.closeReceipt().toJson());row.set("material_clearance",v.materialClearance().toJson());if(v.previousDocument().isPresent())row.set("previous_document",v.previousDocument().orElseThrow().toJson());else row.putNull("previous_document");if(v.previousReceipt().isPresent())row.set("previous_receipt",v.previousReceipt().orElseThrow().toJson());else row.putNull("previous_receipt");return row;}
    public static byte[] encodeEventIntent(EventIntent actual){return StrictJson.canonical(eventIntent(actual),MAX_BYTES);}
    public static EventIntent decodeEventIntent(byte[] original){return eventIntent(StrictJson.parse(original,MAX_BYTES));}
    private static ObjectNode eventIntent(EventIntent v){var row=StrictJson.object().put("machine_id",v.machineId()).put("ordinal",v.ordinal()).put("action_id",v.actionId()).put("body_sha256",v.bodySha256()).put("instance_id",v.instanceId()).put("interaction",v.interaction()).put("observed_at_utc",v.observedAtUtc().toString());row.set("command",v.command().toJson());row.set("original_read",v.originalRead().toJson());var refs=row.putArray("source_originals");v.sourceOriginals().forEach(ref->refs.add(ref.toJson()));if(v.previous().isPresent())row.set("previous",v.previous().orElseThrow().toJson());else row.putNull("previous");if(v.originalReceipt().isPresent())row.set("original_receipt",v.originalReceipt().orElseThrow().toJson());else row.putNull("original_receipt");if(v.confirmedReceipt().isPresent())row.set("confirmed_receipt",v.confirmedReceipt().orElseThrow().toJson());else row.putNull("confirmed_receipt");return row;}
    private static EventIntent eventIntent(JsonNode node){var row=StrictJson.object(node,Set.of("machine_id","ordinal","action_id","body_sha256","instance_id","interaction","observed_at_utc","command","original_read","source_originals","previous","original_receipt","confirmed_receipt"));var refs=new ArrayList<ExactRef>();var source=row.get("source_originals");StrictJson.require(source.isArray()&&source.size()<=32,"actual finite event source originals required");source.forEach(ref->refs.add(ExactRef.fromJson(ref)));StrictJson.require(row.get("interaction").isBoolean(),"exact interaction boolean required");return new EventIntent(text(row,"machine_id"),StrictJson.integer(row.get("ordinal"),1,StrictJson.MAX_SAFE_INTEGER),text(row,"action_id"),text(row,"body_sha256"),ref(row,"command"),ref(row,"original_read"),(int)StrictJson.integer(row.get("instance_id"),Integer.MIN_VALUE,Integer.MAX_VALUE),row.get("interaction").booleanValue(),refs,row.get("previous").isNull()?Optional.empty():Optional.of(ref(row,"previous")),row.get("original_receipt").isNull()?Optional.empty():Optional.of(ref(row,"original_receipt")),row.get("confirmed_receipt").isNull()?Optional.empty():Optional.of(ref(row,"confirmed_receipt")),Instant.parse(text(row,"observed_at_utc")));}
    private static DateIntent dateIntent(JsonNode node){var row=StrictJson.object(node,Set.of("action_id","body_sha256","observed_at_utc","command","close_receipt","material_clearance","previous_document","previous_receipt"));return new DateIntent(text(row,"action_id"),text(row,"body_sha256"),ref(row,"command"),ref(row,"close_receipt"),ref(row,"material_clearance"),Instant.parse(text(row,"observed_at_utc")),row.get("previous_document").isNull()?Optional.empty():Optional.of(ref(row,"previous_document")),row.get("previous_receipt").isNull()?Optional.empty():Optional.of(ref(row,"previous_receipt")));}
    private static ObjectNode mutation(MutationArtifact value){var row=StrictJson.object().put("sequence",value.sequence());row.set("before_driver",value.beforeDriver().toJson());row.set("after_driver",value.afterDriver().toJson());row.set("after_auxiliary",value.afterAuxiliary().toJson());row.set("before_obligation",value.beforeObligation().toJson());row.set("after_obligation",value.afterObligation().toJson());if(value.result().isPresent())row.set("result",value.result().orElseThrow().toJson());else row.putNull("result");if(value.m3Finalization().isPresent())row.set("m3_finalization",value.m3Finalization().orElseThrow().toJson());else row.putNull("m3_finalization");return row;}
    private static MutationArtifact mutation(JsonNode node){var row=StrictJson.object(node,Set.of("sequence","before_driver","after_driver","after_auxiliary","before_obligation","after_obligation","result","m3_finalization"));return new MutationArtifact(StrictJson.safe(StrictJson.integer(row.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER),1),ref(row,"before_driver"),ref(row,"after_driver"),ref(row,"after_auxiliary"),ref(row,"before_obligation"),ref(row,"after_obligation"),row.get("result").isNull()?Optional.empty():Optional.of(ref(row,"result")),row.get("m3_finalization").isNull()?Optional.empty():Optional.of(ref(row,"m3_finalization")));}
    /** Identity projection of proofs already minted/replayed by the sole Root source authority. No bytes grant current custody. */
    public static void requireSameSourceEpoch(byte[] predecessorProof,byte[] currentProof) {
        RootSourceProofContinuity.requireSameSourceEpoch(predecessorProof,currentProof);
    }
    private static ObjectNode capture(Capture value) {
        ObjectNode row=StrictJson.object().put("parent_action_id",value.parentActionId()).put("parent_body_sha256",value.parentBodySha256()).put("clock_action_id",value.clockActionId()).put("clock_body_sha256",value.clockBodySha256()).put("machine_id",value.machineId()).put("session_id",value.sessionId()).put("game_pid",value.gamePid()).put("game_birth_filetime",value.gameBirthFiletime()).put("connection_generation",value.connectionGeneration()).put("episode_run_id",value.episodeRunId()).put("head_before_capture",value.headBeforeCapture()).put("ledger_sequence_before_capture",value.ledgerSequenceBeforeCapture());
        row.set("parent_command",value.parentCommand().toJson());row.set("clock_command",value.clockCommand().toJson());row.set("source",ProposalLifecycleCodec.source(value.source()));row.set("predecessor_frame",frame(value.predecessorFrame()));
        row.set("executable",value.executable().toJson());row.put("executable_file_id",value.executableFileId()).put("executable_mtime_ns",value.executableMtimeNs());
        row.set("root_read",value.rootRead().toJson());row.set("root_result",value.rootResult().toJson());row.set("native_packet",value.nativePacket().toJson());row.set("semantic",value.semantic().toJson());row.set("driver_stamp",value.driverStamp().toJson());row.set("driver",value.driver().toJson());row.set("hello",value.hello().toJson());row.set("source_qualification",ExactRef.optionalToJson(value.sourceQualification()));if(value.replacementProof().isPresent())row.set("replacement_proof",value.replacementProof().orElseThrow().toJson());else row.putNull("replacement_proof");return row;
    }
    private static Capture capture(JsonNode node) {
        ObjectNode row=StrictJson.object(node,Set.of("parent_action_id","parent_body_sha256","parent_command","clock_action_id","clock_body_sha256","clock_command","machine_id","session_id","game_pid","game_birth_filetime","connection_generation","episode_run_id","source","predecessor_frame","executable","executable_file_id","executable_mtime_ns","root_read","root_result","native_packet","semantic","driver_stamp","driver","hello","head_before_capture","ledger_sequence_before_capture","replacement_proof"),Set.of("source_qualification"));
        return new Capture(text(row,"parent_action_id"),text(row,"parent_body_sha256"),ref(row,"parent_command"),text(row,"clock_action_id"),text(row,"clock_body_sha256"),ref(row,"clock_command"),text(row,"machine_id"),text(row,"session_id"),StrictJson.integer(row.get("game_pid"),1,0xffff_ffffL),text(row,"game_birth_filetime"),text(row,"connection_generation"),text(row,"episode_run_id"),G2Wire.source(row.get("source")),frame(row.get("predecessor_frame")),ref(row,"executable"),text(row,"executable_file_id"),text(row,"executable_mtime_ns"),ref(row,"root_read"),ref(row,"root_result"),ref(row,"native_packet"),ref(row,"semantic"),ref(row,"driver_stamp"),ref(row,"driver"),ref(row,"hello"),ExactRef.optionalFromJson(row.get("source_qualification")),text(row,"head_before_capture"),StrictJson.integer(row.get("ledger_sequence_before_capture"),0,StrictJson.MAX_SAFE_INTEGER),row.get("replacement_proof").isNull()?Optional.empty():Optional.of(ref(row,"replacement_proof")));
    }
    private static ObjectNode ready(Ready value) {
        ObjectNode row=StrictJson.object().put("parent_action_id",value.parentActionId()).put("parent_body_sha256",value.parentBodySha256());row.set("parent_command",value.parentCommand().toJson());row.set("predecessor_death",value.predecessorDeath().toJson());row.set("initial_timeline",read(value.initialTimeline()));if(value.closeReceipt().isPresent())row.set("close_receipt",value.closeReceipt().orElseThrow().toJson());else row.putNull("close_receipt");var subsequent=row.putArray("subsequent_timeline");value.subsequentTimeline().forEach(item->subsequent.add(read(item)));row.set("final_native_packet",value.finalNativePacket().toJson());row.set("final_semantic",value.finalSemantic().toJson());row.set("final_driver",value.finalDriver().toJson());row.set("final_source_qualification",ExactRef.optionalToJson(value.finalSourceQualification()));return row;
    }
    private static Ready ready(JsonNode node) {
        ObjectNode row=StrictJson.object(node,Set.of("parent_action_id","parent_body_sha256","parent_command","predecessor_death","initial_timeline","close_receipt","subsequent_timeline","final_native_packet","final_semantic","final_driver"),Set.of("final_source_qualification"));JsonNode entries=row.get("subsequent_timeline");StrictJson.require(entries.isArray() && entries.size()<=8,"bounded independent Timeline reads");List<ReadArtifact> reads=new ArrayList<>();entries.forEach(item->reads.add(read(item)));
        return new Ready(text(row,"parent_action_id"),text(row,"parent_body_sha256"),ref(row,"parent_command"),ref(row,"predecessor_death"),read(row.get("initial_timeline")),row.get("close_receipt").isNull()?Optional.empty():Optional.of(ref(row,"close_receipt")),reads,ref(row,"final_native_packet"),ref(row,"final_semantic"),ref(row,"final_driver"),ExactRef.optionalFromJson(row.get("final_source_qualification")));
    }
    private static ObjectNode read(ReadArtifact value) { ObjectNode row=StrictJson.object().put("request_id",value.requestId());row.set("receipt",value.receipt().toJson());row.set("frame",value.frame().toJson());row.set("actual_frame",frame(value.actualFrame()));row.set("semantic",value.semantic().toJson());return row; }
    private static ReadArtifact read(JsonNode node) { ObjectNode row=StrictJson.object(node,Set.of("request_id","receipt","frame","actual_frame","semantic"));return new ReadArtifact(ref(row,"receipt"),ref(row,"frame"),text(row,"request_id"),frame(row.get("actual_frame")),ref(row,"semantic")); }
    public static ObjectNode frame(Frame value) { return StrictJson.object().put("snapshot_id",value.snapshotId()).put("public_revision",value.publicRevision()).put("native_revision",value.nativeRevision()).put("date_raw",value.dateRaw()).put("actor_character_id",value.actorCharacterId()).put("local_player_id",value.localPlayerId()); }
    public static Frame frame(JsonNode node) { ObjectNode row=StrictJson.object(node,Set.of("snapshot_id","public_revision","native_revision","date_raw","actor_character_id","local_player_id"));return new Frame(text(row,"snapshot_id"),StrictJson.integer(row.get("public_revision"),BigInteger.ZERO,StrictJson.UINT64_MAX),StrictJson.integer(row.get("native_revision"),BigInteger.ONE,StrictJson.UINT64_MAX),(int)StrictJson.integer(row.get("date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE),(int)StrictJson.integer(row.get("actor_character_id"),Integer.MIN_VALUE,Integer.MAX_VALUE),(int)StrictJson.integer(row.get("local_player_id"),0,Integer.MAX_VALUE)); }
    private static ExactRef ref(JsonNode row,String key) { return ExactRef.fromJson(row.get(key)); }
    private static String text(JsonNode row,String key) { return StrictJson.text(row.get(key)); }
    private static void digest(String value) { StrictJson.require(value!=null && value.matches("[0-9a-f]{64}"),"SHA256"); }
    private static void decimal(String value,boolean positive) { StrictJson.require(value!=null && value.matches(positive?"[1-9][0-9]{0,19}":"0|[1-9][0-9]{0,19}"),"canonical decimal identity");StrictJson.require(new BigInteger(value).compareTo(StrictJson.UINT64_MAX)<=0,"uint64 identity"); }
}
