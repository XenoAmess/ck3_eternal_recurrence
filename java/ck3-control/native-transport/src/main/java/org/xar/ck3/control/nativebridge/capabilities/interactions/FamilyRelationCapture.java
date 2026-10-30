package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.continuity.writer.StorageWriteGuard.*;

/** Same native query originals exported under the actual finite Root storage guard. No new CAS or Game authority. */
public final class FamilyRelationCapture {
    public static final String RECEIPT="ROOT-NATIVE71-GUARDIAN-CAPTURE-RESULT.json";
    private static final String FAMILY="family-result.json",COMMAND="guardian-family-command-result.json",SIDECAR="guardian-two-factory-source.json";
    private static final long MAX_FILE=64L*1024*1024;
    public record Request(Path outputDirectory,long ownedGamePid){
        public Request {outputDirectory=Objects.requireNonNull(outputDirectory).toAbsolutePath().normalize();need(ownedGamePid>0&&ownedGamePid<=0xffff_ffffL,"owned Game PID required");}
    }
    public record Original(FamilyCurrentRelationQueries queries,PlanningReadResult.Known<OpportunityJson.Obj> read,FamilyCurrentRelation.Observation observation,ActionPorts.OutcomeArchive archive){
        public Original {Objects.requireNonNull(queries);Objects.requireNonNull(read);Objects.requireNonNull(observation);Objects.requireNonNull(archive);need(observation.original().equals(read.value())&&observation.root().binding().context().before().equals(read.receipt().request().before()),"capture source DATA differs from the exact original typed read");}
    }
    /** Actual coordinator failure retains its original outcome separately from any successful typed read. */
    public static final class QueryUnavailable extends IOException {
        private static final long serialVersionUID = 1L;
        // Retained native outcomes use the existing archive codec for export.
        @SuppressWarnings("serial")
        private final java.util.Optional<NativeActionPort.DispatchOutcome> original;
        public QueryUnavailable(String reason,java.util.Optional<NativeActionPort.DispatchOutcome> original){super(reason);this.original=Objects.requireNonNull(original);}
        public java.util.Optional<NativeActionPort.DispatchOutcome> original(){return original;}
    }
    @FunctionalInterface public interface Query {Original read()throws IOException;}
    public static final class Result {
        private final OpportunityJson.Obj body;
        private Result(ObjectNode actual){body=OpportunityJson.object(DriverJson.fromNode(actual),"actual guardian capture");}
        public OpportunityJson.Obj body(){return body;}
    }
    private FamilyRelationCapture(){ }
    public static Result capture(Request requested,Clock clock,StorageWriteGuard actualGuard,Path originalLock,Query actualQuery)throws IOException {
        Objects.requireNonNull(requested);Objects.requireNonNull(clock);Objects.requireNonNull(actualGuard);Objects.requireNonNull(actualQuery);
        Path output=requested.outputDirectory();List<Mutation> mutations=new ArrayList<>();List<Path> parents=new ArrayList<>();
        need(!Files.exists(output,LinkOption.NOFOLLOW_LINKS),"capture requires a fresh output directory");
        Path cursor=output;while(cursor!=null&&!Files.exists(cursor,LinkOption.NOFOLLOW_LINKS)){parents.add(cursor);cursor=cursor.getParent();need(parents.size()<=128,"bounded capture parent path required");}
        need(cursor!=null&&Files.isDirectory(cursor,LinkOption.NOFOLLOW_LINKS)&&cursor.equals(cursor.toRealPath()),"capture parent must be a real ordinary directory");
        for(int i=parents.size()-1;i>=0;i--)mutations.add(new DirectoryCreate(parents.get(i)));
        for(String file:List.of(FAMILY,COMMAND,RECEIPT))mutations.add(new FileCreate(output.resolve(file),MAX_FILE));
        mutations.add(new FileCreate(output.resolve(SIDECAR),FamilyRelationMaterialExports.MAX_BYTES));
        return actualGuard.write(new WritePlan(originalLock.toAbsolutePath().normalize(),mutations),()->{
            for(int i=parents.size()-1;i>=0;i--)Files.createDirectory(parents.get(i));
            ObjectNode receipt=F.objectNode().put("schema","xar.guardian.private-current-capture-result.v1")
                    .put("started_at_utc",clock.instant().toString()).put("status","RED").put("owned_game_pid",requested.ownedGamePid())
                    .put("new_driver_constructions",0).put("new_listeners",0).put("Game_launch_injection_pause_focus_close",0)
                    .put("guardian_membership_observed",false).put("guardian_pair_ready",false).put("G2_outcome_credit",0);
            try {
                Original original=Objects.requireNonNull(actualQuery.read());var read=original.read();var typed=original.observation();
                need(typed.original().equals(read.value()),"capture typed body differs from the sole original relationship decoder");
                var context=typed.root().binding().context();need(context.before().game().pid()==requested.ownedGamePid(),"capture owned PID differs from the actual Root Game");
                JsonNode family=OpportunityJson.toNode(typed.original());ExactRef material=ExactRef.fromJson(family.path("guardian_factory_materials_v2").get("original_sidecar"));
                var retained=original.queries().originalMaterials(read.receipt());need(retained.reference().equals(material),"capture mixed another query sidecar reference");
                FamilyRelationMaterialExports.requireCaptured(read.receipt(),retained);RawJson sidecar=retained.original();need(sidecar.bytes().length==material.bytes()&&DriverJson.sha256(sidecar.bytes()).equals(material.sha256()),"capture CAS original changed its exact bytes");
                // Decode reopened this READ-attached original and checked its fixed keys and material versions.
                JsonNode raw=DriverJson.toNode(DriverJson.object(sidecar.bytes(),FamilyRelationMaterialExports.MAX_BYTES));
                need(raw.path("schema").asText().equals("xar.ck3.guardian-factory-discovery.v1")&&raw.path("factories").isArray()&&raw.path("factories").size()==2
                        &&raw.path("factories").get(0).path("key").asText().equals("has_relation_guardian")&&raw.path("factories").get(1).path("key").asText().equals("has_relation_ward"),"capture lacks the two original fixed factory records");
                write(output,FAMILY,DriverJson.encode(FamilyCurrentRelationPublic.captureFamily(typed)));
                write(output,COMMAND,read.receipt().original().originalFrame().bytes());write(output,SIDECAR,sidecar.bytes());
                JsonNode publicFamily=OpportunityJson.toNode(FamilyCurrentRelationPublic.encode(typed));
                JsonNode owned=publicFamily.path("guardian_factory_materials_v2").get("observation");
                receipt.set("guardian_family_decision_inputs_v1",OpportunityJson.toNode(FamilyCurrentRelationPublic.guardianDecision(typed)));
                if(owned!=null&&!owned.isNull()){
                    receipt.set("native_factory_discovery_v1",owned);
                    for(String field:List.of(FamilyRelationGuardianMaterials.RELATION,FamilyRelationGuardianMaterials.CHILD_MATERIALS))if(owned.has(field))receipt.set(field,owned.get(field));
                }
                boolean qualified=raw.path("qualified").isBoolean()&&raw.path("qualified").booleanValue();
                receipt.put("status",qualified?"FRAME_QUALIFIED_DISCOVERY_WRITTEN":"DISCOVERY_UNAVAILABLE")
                        .put("family_result_path",output.resolve(FAMILY).toString()).put("native_command_result_path",output.resolve(COMMAND).toString())
                        .put("native_sidecar_path",output.resolve(SIDECAR).toString()).put("actual_native_revision_before",context.revision().toString())
                        .put("actual_public_revision_before",context.before().frame().revision().toString()).put("actual_date_raw_before",context.date())
                        .put("actual_played_character_id_before",context.actor()).put("sidecar_request_id",read.receipt().requestId())
                        .put("sidecar_native_revision",context.revision().toString()).put("sidecar_frame_qualified",qualified)
                        .put("public_family_result_changed",false).put("registered_MCP_consumer_count",0)
                        .put("guardian_pair_ready",owned!=null&&!owned.isNull()&&owned.path(FamilyRelationGuardianMaterials.RELATION).path("ready").asBoolean(false))
                        .put("public_numeric_schema",FamilyCurrentRelationPublic.SCHEMA);
                int found=0;var statuses=receipt.putArray("fixed_record_statuses");for(JsonNode row:raw.path("factories")){
                    if(row.path("status").asText().equals("found"))found++;
                    ObjectNode status=statuses.addObject().put("key",row.get("key").textValue());for(String field:List.of("status","unavailable_reason")){JsonNode value=row.get(field);status.set(field,value==null?F.nullNode():value);}
                }
                receipt.put("actual_factory_found_count",found);receipt.set("original_sidecar",material.toJson());
                receipt.put("sidecar_export_basis","same_query_archived_READ_sidecar_original_copy");
            }catch(IOException|RuntimeException failure){
                String message=failure.getClass().getSimpleName()+": "+failure.getMessage();receipt.put("failure",message.substring(0,Math.min(message.length(),8192)));
                if(failure instanceof QueryUnavailable unavailable&&unavailable.original().orElse(null) instanceof NativeActionPort.AckReceived ack){
                    try {write(output,COMMAND,ack.originalFrame().bytes());receipt.put("native_command_result_path",output.resolve(COMMAND).toString());
                        JsonNode frame=DriverJson.toNode(DriverJson.object(ack.originalFrame().bytes(),64*1024*1024));JsonNode proof=frame.get("guardian_factory_discovery_v1");
                        if(proof!=null){safeDiagnostic(proof,0);receipt.set("native_factory_export",proof);}
                    }catch(IOException|RuntimeException retainFailure){failure.addSuppressed(retainFailure);receipt.put("failed_original_export_diagnostic",retainFailure.getClass().getSimpleName());}
                }
                throw failure;
            }
            finally{receipt.put("ended_at_utc",clock.instant().toString());write(output,RECEIPT,DriverJson.encodeNode(receipt));}
            return new Result(receipt);
        });
    }
    /** Failed diagnostic fields have no declared wide-number role; preserve unsafe values only in original file bytes. */
    private static void safeDiagnostic(JsonNode value,int depth){
        need(depth<=32,"failed native diagnostic depth exceeds its source bound");
        if(value.isIntegralNumber())need(value.bigIntegerValue().abs().compareTo(java.math.BigInteger.valueOf(9007199254740991L))<=0,"unknown unsafe native diagnostic integer");
        need(!value.isFloatingPointNumber(),"native failure diagnostic floating token is unqualified");
        if(value.isContainerNode())for(JsonNode child:value)safeDiagnostic(child,depth+1);
    }
    private static void write(Path directory,String name,byte[] bytes)throws IOException {
        need(bytes.length<=MAX_FILE,"capture output exceeds finite quote");
        Path target=directory.resolve(name);
        try(var channel=java.nio.channels.FileChannel.open(target,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){
            var buffer=java.nio.ByteBuffer.wrap(bytes);while(buffer.hasRemaining())need(channel.write(buffer)>0,"capture file write made no bounded progress");channel.force(true);
        }
    }
}
