package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.lifecycle.SeedAdoption;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.root.RootCheckpointPublicCalls;
import static org.xar.ck3.control.service.root.RootCheckpointPublicCalls.*;

/** The only public SAVE / restore JSON conversion. Durable source records are never rewritten. */
public final class CheckpointPublicCodec {
    public static final String SCHEMA="xar.ck3.public-checkpoint-result/v1";
    private CheckpointPublicCodec(){ }
    public static Request decode(PublicBindings.Arguments arguments){
        Objects.requireNonNull(arguments);
        if(arguments instanceof PublicBindings.Missing)return new Request(new MissingRevision());
        if(!(arguments instanceof PublicBindings.Value value))throw new IllegalArgumentException("checkpoint arguments must be omitted or an object, not JSON null");
        var parsed=StrictJson.parse(value.original().bytes(),65536);
        StrictJson.require(parsed instanceof ObjectNode,"checkpoint arguments object required");
        var row=StrictJson.object(parsed,parsed.has("expected_revision")?Set.of("expected_revision"):Set.of());
        if(!row.has("expected_revision"))return new Request(new MissingRevision());
        var revision=row.get("expected_revision");
        return new Request(revision.isNull()?new NullRevision():new ExactRevision(publicRevision(revision)));
    }
    public static RawJson encodeRequest(Request request){
        Objects.requireNonNull(request);var row=StrictJson.object();
        if(request.expectedRevision() instanceof NullRevision)row.putNull("expected_revision");
        else if(request.expectedRevision() instanceof ExactRevision exact)row.put("expected_revision",exact.value().toString());
        return raw(row);
    }
    private static BigInteger publicRevision(JsonNode value){
        if(value.isTextual())return new BigInteger(new CrossJsDecimalUInt64(value.textValue()).decimal());
        return StrictJson.integer(value,BigInteger.ZERO,BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER));
    }
    public static RawJson save(SaveCall call){
        Objects.requireNonNull(call);var actual=call.actual();var row=base("save-checkpoint");
        var action=RootCheckpointPublicCalls.action(actual);row.put("accepted",action.flatMap(ActionReceipt::ack).map(ack->ack.nativeOk()).orElse(false));
        action.ifPresent(receipt->row.set("canonical_save",canonicalSave(receipt,call.canonicalReceipt().orElseThrow())));
        if(actual instanceof CheckpointResult.Confirmed confirmed){
            row.put("status","saved");row.put("accepted",true);
            var checkpoint=PublicDataJson.object(new RawJson(((DriverStateSnapshot.Value)call.savedDriver().orElseThrow().lastCheckpoint()).json()));
            requireCheckpoint(checkpoint,confirmed.pair());row.set("checkpoint",checkpoint);
            row.set("checkpoint_pair",pair(confirmed.pair()));
            var material=row.putObject("materialization");material.put("available",true);
            material.put("save_dir",Path.of(confirmed.pair().save().reference().path()).getParent().toString());
            material.put("mtime_ns",confirmed.pair().save().identity().mtimeNs());
            material.set("save_witness",CheckpointPairCodec.fileWitnessToJson(confirmed.pair().save()));
            material.set("driver_witness",CheckpointPairCodec.fileWitnessToJson(confirmed.pair().driver()));
            var frame=confirmed.poststate().frame();row.put("snapshot_id",frame.snapshotId());
            row.put("revision",frame.revision().toString());row.put("native_revision",frame.identity().nativeRevision().toString());
            row.put("map_ready",true);row.put("paused",true);
            seed(row,confirmed.seedAdoption());
        }else{
            String reason;
            if(actual instanceof CheckpointResult.Rejected rejected){row.put("status","rejected");row.put("action_id",rejected.actionId());reason=rejected.reason();}
            else{var unknown=(CheckpointResult.Unknown)actual;row.put("status","unknown");row.put("action_id",unknown.actionId());reason=unknown.reason();}
            row.put("reason",reason);var material=row.putObject("materialization");material.put("available",false);material.put("reason",reason);
        }
        return raw(row);
    }
    public static RawJson restore(RestoreCall call){
        Objects.requireNonNull(call);var actual=call.actual();
        if(actual instanceof RestoreCheckpointService.Restored restored){
            // The real cold producer appends its actual completed restore row. Never reconstruct it from ACK fields.
            var history=restored.binding().driver().commandHistory();StrictJson.require(!history.isEmpty(),"published restore full Driver history is empty");
            var original=PublicDataJson.object(new RawJson(history.getLast().originalRow().json()));
            StrictJson.require("restore-checkpoint".equals(StrictJson.text(original.get("command")))
                    &&original.path("ok").isBoolean()&&original.get("ok").booleanValue(),"published full Driver lacks its genuine completed restore row");
            var row=object(original.get("result"),"actual persisted restore result").deepCopy();
            StrictJson.require("restore-checkpoint".equals(StrictJson.text(row.get("step")))
                    &&row.path("accepted").isBoolean()&&row.get("accepted").booleanValue()
                    &&"restored".equals(StrictJson.text(row.get("status"))),"actual original restore result is not confirmed");
            var after=restored.nativePoststate();var frame=after.observed().frame();
            StrictJson.require(StrictJson.integer(row.get("restored_date_raw"),0,StrictJson.MAX_SAFE_INTEGER)==frame.identity().dateRaw().longValueExact()
                    &&StrictJson.integer(row.get("native_revision"),BigInteger.ZERO,StrictJson.UINT64_MAX).equals(frame.identity().nativeRevision()),
                    "persisted restore result differs from the original actual native poststate");
            requireCheckpoint(object(row.get("checkpoint"),"actual restored saved anchor"),restored.pair());
            var persisted=row.deepCopy();decimalRole(persisted,"native_revision");
            if(persisted.has("revision"))decimalRole(persisted,"revision");
            if(persisted.get("lifecycle") instanceof ObjectNode originalLifecycle)decimalRole(originalLifecycle,"connection_generation");
            else throw new IllegalArgumentException("actual restore lifecycle original required");
            row.set("persistent_restore_result",persisted);
            row.put("schema",SCHEMA);decimalRole(row,"native_revision");
            row.put("snapshot_id",frame.snapshotId());row.put("revision",frame.revision().toString());
            if(row.get("lifecycle") instanceof ObjectNode lifecycle)decimalRole(lifecycle,"connection_generation");
            else throw new IllegalArgumentException("actual restore lifecycle original required");
            date(row,"starting_date_raw","starting_date",call.starting().observed().frame().identity().dateRaw());
            date(row,"restored_date_raw","restored_date",frame.identity().dateRaw());
            row.set("checkpoint_pair",pair(restored.pair()));row.set("published_game",call.published().orElseThrow().identity().game().toJson());
            return raw(row);
        }
        var row=base("restore-checkpoint");row.put("accepted",false);
        if(actual instanceof RestoreCheckpointService.Rejected rejected){row.put("status","rejected");row.put("reason",rejected.reason());}
        else{var unknown=(RestoreCheckpointService.Unknown)actual;row.put("status","unknown");row.put("request_id",unknown.requestId());row.put("reason",unknown.reason());}
        return raw(row);
    }
    /** Pair schema already defines exact decimal identity/revision strings; it is kept unchanged. */
    public static ObjectNode pair(CheckpointPair pair){
        var row=object(StrictJson.parse(CheckpointPairCodec.encode(Objects.requireNonNull(pair))),"actual checkpoint pair");
        StrictJson.require(pair.equals(CheckpointPairCodec.decode(StrictJson.canonical(row))),"public checkpoint pair changed its original JSON domain");return row;
    }
    private static ObjectNode canonicalSave(ActionReceipt receipt,ExactRef reference){
        var row=StrictJson.object();row.put("action_id",receipt.command().actionId());row.put("outcome",receipt.outcome().name());
        row.put("sequence",receipt.sequence());row.put("body_sha256",receipt.bodySha256());row.set("receipt_ref",reference.toJson());return row;
    }
    private static void requireCheckpoint(ObjectNode checkpoint,CheckpointPair pair){
        StrictJson.require(pair.save().reference().path().equals(StrictJson.text(checkpoint.get("path")))
                &&pair.save().reference().bytes()==StrictJson.integer(checkpoint.get("size"),1,StrictJson.MAX_SAFE_INTEGER)
                &&pair.save().reference().sha256().equals(StrictJson.text(checkpoint.get("sha256")))
                &&pair.frame().frame().identity().dateRaw().longValueExact()==StrictJson.integer(checkpoint.get("date_raw"),0,StrictJson.MAX_SAFE_INTEGER),
                "public checkpoint must retain the actual saved anchor bytes/date");
    }
    private static void seed(ObjectNode row,SeedAdoption adoption){
        var state=row.putObject("seed_adoption");
        if(adoption instanceof SeedAdoption.Available available){
            state.put("status","available");state.put("origin",available.origin().name());var artifact=available.artifact();
            var seed=row.putObject("episode_seed");seed.put("format_version",1);seed.put("name",org.xar.ck3.control.application.lifecycle.SeedArtifact.NAME);
            seed.put("path",artifact.save().reference().path());seed.put("size",artifact.save().reference().bytes());seed.put("sha256",artifact.save().reference().sha256());
            seed.put("date_raw",artifact.dateRaw());seed.put("character_id",artifact.characterId());seed.put("source_run_id",artifact.sourceRunId());
            seed.put("source_checkpoint_name","xar_checkpoint.ck3");seed.put("immutable",true);
            state.set("save_witness",CheckpointPairCodec.fileWitnessToJson(artifact.save()));state.set("metadata_witness",CheckpointPairCodec.fileWitnessToJson(artifact.metadata()));
        }else{
            row.putNull("episode_seed");var evidence=state.putArray("evidence");
            if(adoption instanceof SeedAdoption.Unavailable absent){state.put("status","unavailable");state.put("reason",absent.reason().name());absent.evidence().forEach(ref->evidence.add(ref.toJson()));}
            else{var unknown=(SeedAdoption.Unknown)adoption;state.put("status","unknown");state.put("reason",unknown.reason());unknown.evidence().forEach(ref->evidence.add(ref.toJson()));}
        }
    }
    private static void decimalRole(ObjectNode row,String field){
        var value=row.get(field);StrictJson.require(value!=null&&value.isIntegralNumber()&&value.bigIntegerValue().signum()>=0
                &&value.bigIntegerValue().compareTo(StrictJson.UINT64_MAX)<=0,"actual original uint64 checkpoint role required: "+field);
        row.put(field,value.bigIntegerValue().toString());
    }
    private static void date(ObjectNode row,String scalar,String object,BigInteger actual){
        if(row.has(scalar))StrictJson.require(StrictJson.integer(row.get(scalar),0,StrictJson.MAX_SAFE_INTEGER)==actual.longValueExact(),"actual checkpoint date field differs");
        else row.put(scalar,actual);
        if(row.has(object))StrictJson.require(row.get(object).equals(StrictJson.object().put("date_raw",actual)),"actual checkpoint date object differs");
        else row.putObject(object).put("date_raw",actual);
    }
    private static ObjectNode base(String step){var row=StrictJson.object();row.put("schema",SCHEMA);row.put("step",step);return row;}
    private static ObjectNode object(JsonNode value,String name){StrictJson.require(value instanceof ObjectNode,name+" object required");return (ObjectNode)value;}
    private static RawJson raw(ObjectNode row){PublicSnapshotCodec.publicNumbers(row,"");return PublicDataJson.encode(row);}
}
