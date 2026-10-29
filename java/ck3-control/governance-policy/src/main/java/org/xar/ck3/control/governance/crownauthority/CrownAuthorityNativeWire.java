package org.xar.ck3.control.governance.crownauthority;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.NativeObservation;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Choice;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Currency;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Readback;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.TitleSuccessors;

/**
 * Strict DATA adapter for the four original native law envelopes.
 * It cannot issue a Root input, current membership, native action or lifecycle proof.
 */
public final class CrownAuthorityNativeWire {
    public static final int MAX_BYTES=65536;
    private static final Set<String> OUTER=Set.of("type","protocol_version","request_id","ok","result");
    private static final Set<String> RESULT=Set.of("step","accepted","private_build","advertised","backend_id",
            "game_version","executable_sha256","read_only","status","observation","ack","receipt");
    private CrownAuthorityNativeWire() { }
    public enum Stage {
        QUERY("available","query-realm-law-crown-action-v1-private",true),
        SUBMITTED_PENDING("submitted_verification_pending","enact-realm-law-crown-v1-private",false),
        UNCHANGED("failed","verify-realm-law-crown-v1-private",true),
        ENACTED("enacted","verify-realm-law-crown-v1-private",true);
        private final String status,step;private final boolean readOnly;
        Stage(String status,String step,boolean readOnly){this.status=status;this.step=step;this.readOnly=readOnly;}
        public String status(){return status;} public String step(){return step;} public boolean readOnly(){return readOnly;}
        static Stage decode(String status){
            for(Stage stage:values())if(stage.status.equals(status))return stage;
            throw new IllegalArgumentException("unsupported original native law status");
        }
    }
    public enum Relation { UNKNOWN }
    public enum Effect { QUERY_DATA, PENDING, NOT_ENACTED, NATIVE_ENACTED_UNBOUND }
    public enum Missing { WRONG_STAGE, SOURCE_MISMATCH, IDENTITY_MISMATCH, CURRENT_REQUEST_FRAME,
        MEMBERSHIP_UNOBSERVED, MEMBERSHIP_MISMATCH, OBSERVATION_CHANGED, QUERY_UNAVAILABLE }
    public record Source(String gameVersion,String executableSha256) {
        public Source {
            StrictJson.text(gameVersion);StrictJson.text(executableSha256);
            StrictJson.require(executableSha256.matches("[0-9a-fA-F]{64}"),"invalid native source SHA");
        }
    }
    public record Revisions(BigInteger publicRevision,BigInteger nativeRevision,BigInteger proofEpoch,BigInteger dateRaw) {
        public Revisions { for(BigInteger value:List.of(publicRevision,nativeRevision,proofEpoch))
            StrictJson.require(value.signum()>0,"positive original revision required");Objects.requireNonNull(dateRaw); }
    }
    public record Charge(Currency currency,BigInteger costRaw,BigInteger preBalanceRaw,BigInteger postBalanceRaw) {
        public Charge { Objects.requireNonNull(currency);CrownAuthorityPolicy.nonnegative(costRaw);
            for(BigInteger value:List.of(costRaw,preBalanceRaw,postBalanceRaw))CrownAuthorityPolicy.q64(value); }
    }
    public sealed interface Payload permits Query,Submitted,Verified { Stage stage(); }
    public record Query(NativeObservation observation) implements Payload {
        public Query { Objects.requireNonNull(observation); }
        @Override public Stage stage(){return Stage.QUERY;}
    }
    public record Submission(String submittedRequestId,boolean verificationPending,String failure,BigInteger actor,
            String groupKey,String previousLaw,String requestedLaw,Revisions before,List<Charge> charges,
            TitleSuccessors titleSuccessors) {
        public Submission { StrictJson.text(submittedRequestId);StrictJson.text(failure);Objects.requireNonNull(actor);
            StrictJson.require(actor.signum()>0,"positive native actor required");StrictJson.text(groupKey);
            StrictJson.text(previousLaw);StrictJson.text(requestedLaw);Objects.requireNonNull(before);
            charges=List.copyOf(charges);Objects.requireNonNull(titleSuccessors); }
    }
    public record Submitted(Submission ack) implements Payload {
        public Submitted { Objects.requireNonNull(ack); }
        @Override public Stage stage(){return Stage.SUBMITTED_PENDING;}
    }
    public record Receipt(String submittedRequestId,String failure,Revisions after,String effectiveLaw,
            boolean effectiveLawVerified,boolean resourcesVerified,boolean successionVerified,List<Charge> charges,
            TitleSuccessors titleSuccessors) {
        public Receipt { StrictJson.text(submittedRequestId);StrictJson.text(failure);Objects.requireNonNull(after);
            StrictJson.text(effectiveLaw);charges=List.copyOf(charges);Objects.requireNonNull(titleSuccessors); }
    }
    public record Verified(Stage stage,Receipt receipt) implements Payload {
        public Verified { StrictJson.require(stage==Stage.UNCHANGED||stage==Stage.ENACTED,"verification stage required");
            Objects.requireNonNull(receipt); }
    }
    public record Envelope(Source source,String requestId,Payload payload) {
        public Envelope { Objects.requireNonNull(source);StrictJson.text(requestId);Objects.requireNonNull(payload); }
        public Relation currentMembership(){return Relation.UNKNOWN;}
        public boolean currentRootQualification(){return false;}
    }
    public sealed interface Decision permits Unknown,ProjectedData { Relation membership(); }
    public record Unknown(Missing reason) implements Decision {
        public Unknown { Objects.requireNonNull(reason); }
        @Override public Relation membership(){return Relation.UNKNOWN;}
    }
    /** A pure existing selector result over independently supplied DATA, never current Root admission. */
    public record ProjectedData(Choice choice) implements Decision {
        public ProjectedData { Objects.requireNonNull(choice); }
        @Override public Relation membership(){return Relation.UNKNOWN;}
        public boolean currentRootQualification(){return false;}
    }

    public static Envelope decode(byte[] originalEnvelope){
        StrictJson.require(originalEnvelope!=null&&originalEnvelope.length<=MAX_BYTES,"native law envelope exceeds bound");
        ObjectNode outer=StrictJson.object(StrictJson.parse(originalEnvelope),OUTER);
        StrictJson.require(text(outer,"type").equals("command_result")&&number(outer,"protocol_version").equals(BigInteger.ONE)
                &&bool(outer,"ok"),"original command_result required");
        return decodeResult(text(outer,"request_id"),StrictJson.canonical(outer.get("result")));
    }
    /** Successful coordinator ACK supplies request identity; resultToken is its unchanged original native RESULT. */
    public static Envelope decodeResult(String actualRequestId,byte[] resultToken){
        StrictJson.text(actualRequestId);
        StrictJson.require(resultToken!=null&&resultToken.length<=MAX_BYTES,"native law result exceeds bound");
        ObjectNode row=StrictJson.object(StrictJson.parse(resultToken),RESULT);
        StrictJson.require(bool(row,"accepted")&&bool(row,"private_build")&&!bool(row,"advertised")
                &&text(row,"backend_id").equals("native-headless"),"original private native flags required");
        Stage stage=Stage.decode(text(row,"status"));
        StrictJson.require(text(row,"step").equals(stage.step())&&bool(row,"read_only")==stage.readOnly(),"native stage drift");
        Source source=new Source(text(row,"game_version"),text(row,"executable_sha256"));Payload payload;
        if(stage==Stage.QUERY){
            nil(row,"ack");nil(row,"receipt");
            payload=new Query(CrownAuthorityCodec.decodeNativeObservation(StrictJson.canonical(row.get("observation"))));
        }else if(stage==Stage.SUBMITTED_PENDING){
            nil(row,"observation");nil(row,"receipt");payload=new Submitted(submission(row.get("ack")));
        }else{
            nil(row,"observation");nil(row,"ack");payload=new Verified(stage,receipt(row.get("receipt")));
        }
        return new Envelope(source,actualRequestId,payload);
    }
    public static byte[] encode(Envelope original){
        Objects.requireNonNull(original);Stage stage=original.payload().stage();ObjectNode outer=StrictJson.object();
        outer.put("type","command_result");outer.put("protocol_version",1);outer.put("request_id",original.requestId());
        outer.put("ok",true);ObjectNode row=outer.putObject("result");
        row.put("step",stage.step());row.put("accepted",true);row.put("private_build",true);row.put("advertised",false);
        row.put("backend_id","native-headless");row.put("game_version",original.source().gameVersion());
        row.put("executable_sha256",original.source().executableSha256());row.put("read_only",stage.readOnly());
        row.put("status",stage.status());row.putNull("observation");row.putNull("ack");row.putNull("receipt");
        if(original.payload() instanceof Query value)
            row.set("observation",StrictJson.parse(CrownAuthorityCodec.encodeNativeObservation(value.observation())));
        else if(original.payload() instanceof Submitted value)row.set("ack",write(value.ack()));
        else if(original.payload() instanceof Verified value)row.set("receipt",write(value.receipt()));
        byte[] encoded=StrictJson.canonical(outer);StrictJson.require(encoded.length<=MAX_BYTES,"native law envelope exceeds bound");
        return encoded;
    }
    public static Relation querySubmitRelation(Envelope query,Envelope submitted){
        StrictJson.require(query.payload() instanceof Query&&submitted.payload() instanceof Submitted,"query and submit DATA required");
        // Equal revisions, actor, titles or image bytes cannot prove that an original native call produced both.
        return Relation.UNKNOWN;
    }
    public static Effect effect(Envelope original){
        if(original.payload() instanceof Query)return Effect.QUERY_DATA;
        if(original.payload() instanceof Submitted)return Effect.PENDING;
        var verified=(Verified)original.payload();var value=verified.receipt();
        return verified.stage()==Stage.ENACTED&&value.failure().equals("none")&&value.effectiveLawVerified()
                &&value.resourcesVerified()&&value.successionVerified()?Effect.NATIVE_ENACTED_UNBOUND:Effect.NOT_ENACTED;
    }
    public static Decision consume(Envelope originalQuery,Source expectedSource,BigInteger expectedActor,
            Optional<TitleSuccessors> independentMembership,Optional<Readback> independentCurrent,Map<Currency,BigInteger> reservesRaw){
        Objects.requireNonNull(expectedSource);Objects.requireNonNull(expectedActor);
        Objects.requireNonNull(independentMembership);Objects.requireNonNull(independentCurrent);Objects.requireNonNull(reservesRaw);
        if(!(originalQuery.payload() instanceof Query query))return new Unknown(Missing.WRONG_STAGE);
        if(!sameSource(originalQuery.source(),expectedSource))return new Unknown(Missing.SOURCE_MISMATCH);
        var nativeFrame=query.observation().frame();var fields=query.observation().fields();
        if(!nativeFrame.playerCharacterId().equals(expectedActor))return new Unknown(Missing.IDENTITY_MISMATCH);
        if(!fields.available()||!fields.paused())return new Unknown(Missing.QUERY_UNAVAILABLE);
        if(independentMembership.isEmpty())return new Unknown(Missing.MEMBERSHIP_UNOBSERVED);
        if(!independentMembership.orElseThrow().equals(fields.titleSuccessors()))return new Unknown(Missing.MEMBERSHIP_MISMATCH);
        if(independentCurrent.isEmpty())return new Unknown(Missing.CURRENT_REQUEST_FRAME);
        Readback current=independentCurrent.orElseThrow();var frame=current.sourceFrame();
        if(!frame.exactCk3Build().equals(expectedSource.gameVersion())
                ||!frame.exeSha256().equalsIgnoreCase(expectedSource.executableSha256()))return new Unknown(Missing.SOURCE_MISMATCH);
        if(!frame.playerCharacterId().equals(expectedActor))return new Unknown(Missing.IDENTITY_MISMATCH);
        if(frame.queriedSnapshotId()==null)return new Unknown(Missing.CURRENT_REQUEST_FRAME);
        if(!current.titleSuccessors().equals(fields.titleSuccessors()))return new Unknown(Missing.MEMBERSHIP_MISMATCH);
        if(!frame.snapshotRevision().equals(nativeFrame.snapshotRevision())
                ||!frame.nativeSnapshotRevision().equals(nativeFrame.nativeSnapshotRevision())
                ||!frame.proofEpoch().equals(nativeFrame.proofEpoch())||!frame.dateRaw().equals(nativeFrame.dateRaw())
                ||!current.candidates().equals(fields.candidates())||!current.resources().equals(fields.resources())
                ||!current.activeLawKey().equals(fields.activeLawKey())||!current.groupKey().equals(fields.groupKey()))
            return new Unknown(Missing.OBSERVATION_CHANGED);
        // Reuse the existing strict serde and selector. No missing frame field is populated from native DATA.
        Readback decoded=CrownAuthorityCodec.decodeReadback(CrownAuthorityCodec.encodeReadback(current));
        return new ProjectedData(CrownAuthorityPolicy.choose(decoded,reservesRaw));
    }
    private static boolean sameSource(Source left,Source right){
        return left.gameVersion().equals(right.gameVersion())&&left.executableSha256().equalsIgnoreCase(right.executableSha256());
    }
    private static Submission submission(JsonNode value){
        ObjectNode row=StrictJson.object(value,Set.of("submitted_request_id","verification_pending","failure",
                "player_character_id","group_key","previous_effective_law_key","requested_law_key",
                "pre_public_revision","pre_native_revision","pre_proof_epoch","pre_date_raw","charges","title_successors"));
        return new Submission(text(row,"submitted_request_id"),bool(row,"verification_pending"),text(row,"failure"),
                number(row,"player_character_id"),text(row,"group_key"),text(row,"previous_effective_law_key"),
                text(row,"requested_law_key"),revisions(row,"pre_"),charges(row.get("charges")),titles(row.get("title_successors")));
    }
    private static Receipt receipt(JsonNode value){
        ObjectNode row=StrictJson.object(value,Set.of("submitted_request_id","failure","post_public_revision",
                "post_native_revision","post_proof_epoch","post_date_raw","effective_law_key","effective_law_verified",
                "resources_verified","succession_verified","charges","title_successors"));
        return new Receipt(text(row,"submitted_request_id"),text(row,"failure"),revisions(row,"post_"),
                text(row,"effective_law_key"),bool(row,"effective_law_verified"),bool(row,"resources_verified"),
                bool(row,"succession_verified"),charges(row.get("charges")),titles(row.get("title_successors")));
    }
    private static Revisions revisions(ObjectNode row,String prefix){
        return new Revisions(number(row,prefix+"public_revision"),number(row,prefix+"native_revision"),
                number(row,prefix+"proof_epoch"),number(row,prefix+"date_raw"));
    }
    private static List<Charge> charges(JsonNode value){
        StrictJson.require(value instanceof ArrayNode,"native charges array required");List<Charge> result=new ArrayList<>();
        for(JsonNode item:value){
            ObjectNode row=StrictJson.object(item,Set.of("currency_key","cost_raw","pre_balance_raw","post_balance_raw"));
            result.add(new Charge(Currency.fromWire(text(row,"currency_key")),number(row,"cost_raw"),
                    number(row,"pre_balance_raw"),number(row,"post_balance_raw")));
        }
        return List.copyOf(result);
    }
    private static TitleSuccessors titles(JsonNode value){
        return CrownAuthorityCodec.decodeTitleSuccessors(StrictJson.canonical(value));
    }
    private static ObjectNode write(Submission value){
        ObjectNode row=StrictJson.object();row.put("submitted_request_id",value.submittedRequestId());
        row.put("verification_pending",value.verificationPending());row.put("failure",value.failure());
        row.put("player_character_id",value.actor());row.put("group_key",value.groupKey());
        row.put("previous_effective_law_key",value.previousLaw());row.put("requested_law_key",value.requestedLaw());
        write(row,"pre_",value.before());writeCharges(row,value.charges());writeTitles(row,value.titleSuccessors());return row;
    }
    private static ObjectNode write(Receipt value){
        ObjectNode row=StrictJson.object();row.put("submitted_request_id",value.submittedRequestId());
        row.put("failure",value.failure());write(row,"post_",value.after());row.put("effective_law_key",value.effectiveLaw());
        row.put("effective_law_verified",value.effectiveLawVerified());row.put("resources_verified",value.resourcesVerified());
        row.put("succession_verified",value.successionVerified());writeCharges(row,value.charges());
        writeTitles(row,value.titleSuccessors());return row;
    }
    private static void write(ObjectNode row,String prefix,Revisions value){
        row.put(prefix+"public_revision",value.publicRevision());row.put(prefix+"native_revision",value.nativeRevision());
        row.put(prefix+"proof_epoch",value.proofEpoch());row.put(prefix+"date_raw",value.dateRaw());
    }
    private static void writeCharges(ObjectNode row,List<Charge> values){
        ArrayNode array=row.putArray("charges");for(Charge value:values)array.addObject().put("currency_key",value.currency().wire())
                .put("cost_raw",value.costRaw()).put("pre_balance_raw",value.preBalanceRaw()).put("post_balance_raw",value.postBalanceRaw());
    }
    private static void writeTitles(ObjectNode row,TitleSuccessors values){
        row.set("title_successors",StrictJson.parse(CrownAuthorityCodec.encodeTitleSuccessors(values)));
    }
    private static String text(ObjectNode row,String field){return StrictJson.text(row.get(field));}
    private static BigInteger number(ObjectNode row,String field){
        JsonNode value=row.get(field);StrictJson.require(value!=null&&value.isIntegralNumber(),"actual native integer token required: "+field);
        return value.bigIntegerValue();
    }
    private static boolean bool(ObjectNode row,String field){
        JsonNode value=row.get(field);StrictJson.require(value!=null&&value.isBoolean(),"actual native boolean required: "+field);
        return value.booleanValue();
    }
    private static void nil(ObjectNode row,String field){
        StrictJson.require(row.get(field)!=null&&row.get(field).isNull(),"native absent branch must be explicit null: "+field);
    }
}
