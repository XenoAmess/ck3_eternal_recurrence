package org.xar.ck3.control.application.driver;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationReducer.PendingEpisode;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Canonical natural-domain child DATA. The installed private Root issuer and original writer still own publication. */
public record DriverPendingEpisodeProjection(long beforeVersion,long beforeEpoch,String beforeDriverSha256,
        long afterVersion,long afterEpoch,GameGeneration game,String machineId,Instant observedAtUtc,String oldEpisodeRunId,BigInteger oldActor,
        String newEpisodeRunId,BigInteger newActor,ExactRef beforeDriver,ExactRef afterDriver,
        ExactRef auxiliary,ExactRef obligation,ExactRef qualifiedCause) {
    public static final String SCHEMA="xar.java.pending-episode-driver-projection/v1";
    private static final Set<String> KEYS=Set.of("schema","before_version","before_epoch","before_driver_sha256",
            "after_version","after_epoch","game","machine_id","observed_at_utc","old_episode_run_id","old_actor","new_episode_run_id","new_actor",
            "before_driver","after_driver","auxiliary","obligation","qualified_cause");
    public DriverPendingEpisodeProjection {
        StrictJson.safe(beforeVersion,0);StrictJson.safe(beforeEpoch,0);StrictJson.safe(afterVersion,1);StrictJson.safe(afterEpoch,1);
        StrictJson.require(afterVersion==Math.addExact(beforeVersion,1)&&afterEpoch==Math.addExact(beforeEpoch,1),
                "pending episode must advance the same actual Driver version and episode epoch once");
        Objects.requireNonNull(game);StrictJson.text(machineId);Objects.requireNonNull(observedAtUtc);StrictJson.text(oldEpisodeRunId);StrictJson.text(newEpisodeRunId);
        NativeCharacterId.of(oldActor);NativeCharacterId.of(newActor);
        StrictJson.require(!oldActor.equals(newActor)&&!oldEpisodeRunId.equals(newEpisodeRunId),
                "pending rebind needs the real changed player and a distinct new episode");
        StrictJson.require(beforeDriverSha256!=null&&beforeDriverSha256.matches("[0-9a-f]{64}"),"original complete Driver digest required");
        for(ExactRef ref:java.util.List.of(beforeDriver,afterDriver,auxiliary,obligation,qualifiedCause))
            StrictJson.require(ref.bytes()>0,"actual pending projection original required");
        StrictJson.require(beforeDriver.sha256().equals(beforeDriverSha256),"pending original Driver reference differs from its stamp");
    }
    public record Prepared(DriverPendingEpisodeProjection projection,ExactRef originalRef) {
        public Prepared {Objects.requireNonNull(projection);Objects.requireNonNull(originalRef);
            byte[] bytes=projection.encode();StrictJson.require(originalRef.bytes()==bytes.length&&originalRef.sha256().equals(DriverJson.sha256(bytes)),
                    "pending child original differs from its complete typed body");}
    }
    /** Retains deterministic DATA only, before the Root domain commit. This method supplies no transition authority. */
    public static Prepared prepare(DriverSnapshotFacts.Known before,PendingEpisode pending,OutcomeArchive originals) {
        Objects.requireNonNull(before);Objects.requireNonNull(pending);Objects.requireNonNull(originals);
        var binding=pending.obligation().binding();var old=before.driver();
        StrictJson.require(binding.predecessor().subject().driverVersion()==before.stamp().driverVersion()
                &&binding.predecessor().subject().episodeEpoch()==before.stamp().episodeEpoch()
                &&binding.predecessor().game().equals(before.stamp().game())
                &&binding.predecessor().subject().characterId().equals(old.session().actorId())
                &&binding.predecessor().subject().episodeRunId().equals(old.session().episodeRunId()),"pending child lost its actual original subject");
        StrictJson.require(pending.obligation().blocksOrdinaryActionsAndSave()&&pending.driver().commandHistory().isEmpty()
                &&pending.driver().session().actorId().equals(binding.successorCharacterId())
                &&pending.driver().session().episodeRunId().equals(binding.successorEpisodeRunId())
                &&Objects.equals(old.campaignGoal(),pending.driver().campaignGoal()),
                "pending projection cannot finalize a goal or retain old episode history");
        ExactRef beforeRef=originals.materialReferenceOf(new RawJson(old.encode()));
        ExactRef afterRef=retain(originals,new RawJson(pending.driver().encode()));
        ExactRef auxiliary=retain(originals,new RawJson(DriverJson.encode(pending.auxiliary())));
        ExactRef obligation=retain(originals,new RawJson(SuccessorUiObligationCodec.encode(pending.obligation())));
        var value=new DriverPendingEpisodeProjection(before.stamp().driverVersion(),before.stamp().episodeEpoch(),before.stamp().driverSha256(),
                Math.addExact(before.stamp().driverVersion(),1),Math.addExact(before.stamp().episodeEpoch(),1),before.stamp().game(),
                binding.predecessor().machineId(),binding.qualifiedAtUtc(),
                old.session().episodeRunId(),old.session().actorId(),pending.driver().session().episodeRunId(),pending.driver().session().actorId(),
                beforeRef,afterRef,auxiliary,obligation,binding.qualifiedCause());
        return new Prepared(value,retain(originals,new RawJson(value.encode())));
    }
    private static ExactRef retain(OutcomeArchive originals,RawJson body) {
        ExactRef actual=originals.preserveMaterial(body);
        StrictJson.require(actual.equals(originals.materialReferenceOf(body))&&Arrays.equals(originals.loadMaterial(actual).bytes(),body.bytes()),
                "pending projection original archive differs");return actual;
    }
    public byte[] encode(){return DriverJson.encode(toJson());}
    public Obj toJson() {
        var values=new LinkedHashMap<String,Value>();values.put("schema",new Text(SCHEMA));
        values.put("before_version",number(beforeVersion));values.put("before_epoch",number(beforeEpoch));values.put("before_driver_sha256",new Text(beforeDriverSha256));
        values.put("after_version",number(afterVersion));values.put("after_epoch",number(afterEpoch));
        values.put("game",DriverJson.fromNode(game.toJson()));values.put("machine_id",new Text(machineId));values.put("observed_at_utc",new Text(observedAtUtc.toString()));
        values.put("old_episode_run_id",new Text(oldEpisodeRunId));values.put("old_actor",new IntegerValue(oldActor));
        values.put("new_episode_run_id",new Text(newEpisodeRunId));values.put("new_actor",new IntegerValue(newActor));
        values.put("before_driver",DriverObservationEvidenceReader.reference(beforeDriver));values.put("after_driver",DriverObservationEvidenceReader.reference(afterDriver));
        values.put("auxiliary",DriverObservationEvidenceReader.reference(auxiliary));values.put("obligation",DriverObservationEvidenceReader.reference(obligation));
        values.put("qualified_cause",DriverObservationEvidenceReader.reference(qualifiedCause));return new Obj(values);
    }
    public static DriverPendingEpisodeProjection decode(byte[] original){return fromJson(DriverJson.object(original,262144));}
    public static DriverPendingEpisodeProjection fromJson(Obj value) {
        StrictJson.require(value.members().keySet().equals(KEYS)&&new Text(SCHEMA).equals(value.get("schema")),"closed pending Driver child schema required");
        return new DriverPendingEpisodeProjection(integer(value,"before_version"),integer(value,"before_epoch"),OpportunityJson.text(value.get("before_driver_sha256"),"before digest"),
                integer(value,"after_version"),integer(value,"after_epoch"),GameGeneration.fromJson(OpportunityJson.toNode(value.get("game"))),
                OpportunityJson.text(value.get("machine_id"),"machine"),Instant.parse(OpportunityJson.text(value.get("observed_at_utc"),"observed time")),
                OpportunityJson.text(value.get("old_episode_run_id"),"old episode"),OpportunityJson.integer(value.get("old_actor"),"old actor"),
                OpportunityJson.text(value.get("new_episode_run_id"),"new episode"),OpportunityJson.integer(value.get("new_actor"),"new actor"),
                ref(value,"before_driver"),ref(value,"after_driver"),ref(value,"auxiliary"),ref(value,"obligation"),ref(value,"qualified_cause"));
    }
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static long integer(Obj value,String field){return OpportunityJson.integer(value.get(field),field).longValueExact();}
    private static ExactRef ref(Obj value,String field){return DriverObservationEvidenceReader.reference(value.get(field));}
}
