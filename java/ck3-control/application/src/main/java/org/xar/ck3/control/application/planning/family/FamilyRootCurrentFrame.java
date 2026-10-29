package org.xar.ck3.control.application.planning.family;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** DATA projection of an independently qualified ROOT target. This record cannot mint a lineage proof or an action. */
public record FamilyRootCurrentFrame(ExactRef originalRootReceipt,BigInteger originalRevision,String snapshotId,
        BigInteger publicRevision,BigInteger nativeRevision,BigInteger dateRaw,String episodeRunId,BigInteger player) {
    public static final String FIELD="family_root_current_frame";
    public static final String SCHEMA="xar.java.family-root-current-frame/v1";
    public FamilyRootCurrentFrame {
        Objects.requireNonNull(originalRootReceipt);StrictJson.require(originalRootReceipt.bytes()>0,"actual original ROOT reference required");
        StrictJson.text(snapshotId);StrictJson.text(episodeRunId);
        for(var number:new BigInteger[]{originalRevision,publicRevision,nativeRevision})StrictJson.require(number!=null&&number.signum()>0&&number.bitLength()<=64,"positive uint64 ROOT revision required");
        StrictJson.require(originalRevision.compareTo(publicRevision)<=0&&dateRaw!=null&&dateRaw.signum()>=0&&dateRaw.bitLength()<=32,
                "ROOT current frame identities or revision order changed");
        NativeCharacterId.of(player);
    }
    public static FamilyRootCurrentFrame observed(ExactRef original,ObservationIdentity originalFrame,ObservationIdentity actualTarget) {
        var target=actualTarget.frame();return new FamilyRootCurrentFrame(original,originalFrame.frame().revision(),target.snapshotId(),target.revision(),
                target.identity().nativeRevision(),target.identity().dateRaw(),target.episodeRunId(),target.identity().player());
    }
    public Obj toJson() {
        var row=StrictJson.object().put("schema",SCHEMA).put("original_revision",originalRevision.toString()).put("snapshot_id",snapshotId)
                .put("public_revision",publicRevision.toString()).put("native_revision",nativeRevision.toString()).put("date_raw",dateRaw)
                .put("episode_run_id",episodeRunId);row.set("played_character_id",NativeCharacterId.of(player).toJson());row.set("original_root_receipt",originalRootReceipt.toJson());
        return DriverJson.object(StrictJson.canonical(row),DriverJson.MAX_NATIVE_BYTES);
    }
    public static FamilyRootCurrentFrame fromJson(Obj value) {
        var row=StrictJson.object(DriverJson.toNode(value),Set.of("schema","original_root_receipt","original_revision","snapshot_id","public_revision","native_revision","date_raw","episode_run_id","played_character_id"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact current ROOT DATA schema required");
        return new FamilyRootCurrentFrame(ExactRef.fromJson(row.get("original_root_receipt")),decimal(row.get("original_revision")),StrictJson.text(row.get("snapshot_id")),
                decimal(row.get("public_revision")),decimal(row.get("native_revision")),StrictJson.integer(row.get("date_raw"),BigInteger.ZERO,new BigInteger("4294967295")),
                StrictJson.text(row.get("episode_run_id")),NativeCharacterId.fromJson(row.get("played_character_id")).asBigInteger());
    }
    /** Pure consumer check only. Root's actual producer/replay must separately reopen the private publisher proof. */
    public static void requireSame(Obj root,Obj actualSnapshot) {
        JsonNode value=DriverJson.toNode(root),snapshot=DriverJson.toNode(actualSnapshot);
        String snapshotId=StrictJson.text(snapshot.get("snapshot_id"));BigInteger nativeRevision=number(snapshot.get("native_revision")),revision=number(snapshot.get("revision"));
        BigInteger snapshotPlayer=NativeCharacterId.fromJson(snapshot.path("played_character").get("character_id")).asBigInteger();
        BigInteger queriedRevision=number(value.get("queried_revision"));
        StrictJson.require(StrictJson.text(value.get("queried_snapshot_id")).equals(snapshotId)&&number(value.get("queried_native_revision")).equals(nativeRevision),"ROOT original native identity differs from actual snapshot");
        if(queriedRevision.equals(revision))return;
        var frame=fromJson(OpportunityJson.object(root.get(FIELD),FIELD));
        StrictJson.require(frame.originalRevision().equals(queriedRevision)&&frame.snapshotId().equals(snapshotId)
                &&frame.publicRevision().equals(revision)&&frame.nativeRevision().equals(nativeRevision)
                &&frame.dateRaw().equals(StrictJson.integer(snapshot.get("date_raw"),BigInteger.ZERO,new BigInteger("4294967295")))&&frame.episodeRunId().equals(StrictJson.text(snapshot.get("episode_run_id")))
                &&frame.player().equals(snapshotPlayer),"ROOT qualified target DATA differs from actual current frame");
    }
    private static BigInteger decimal(JsonNode value) {return new BigInteger(new CrossJsDecimalUInt64(StrictJson.text(value)).decimal());}
    private static BigInteger number(JsonNode value) {return StrictJson.integer(value,BigInteger.ONE,new BigInteger("18446744073709551615"));}
}
