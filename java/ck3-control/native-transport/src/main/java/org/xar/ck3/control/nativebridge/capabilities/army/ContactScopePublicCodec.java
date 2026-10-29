package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** One typed public boundary for both contact reads; only the five uint64 roles become canonical decimal strings. */
public final class ContactScopePublicCodec {
    private ContactScopePublicCodec() { }
    public record ProjectedRequest(ProjectedContactPolicy.QueryKey query,UInt64 expectedRevision) {
        public ProjectedRequest {Objects.requireNonNull(query);Objects.requireNonNull(expectedRevision);}
    }
    public record ActualRequest(ActualContactModel.Query query,Field<UInt64> expectedRevision) {
        public ActualRequest {Objects.requireNonNull(query);Objects.requireNonNull(expectedRevision);}
    }
    public sealed interface Response permits Available,Unavailable { ContactScopeObservation.Query query(); }
    public record Available(ContactScopeObservation observation,ExactRef originalReceipt) implements Response {
        public Available {Objects.requireNonNull(observation);Objects.requireNonNull(originalReceipt);require(originalReceipt.bytes()>0,"actual archived read descriptor required");}
        @Override public ContactScopeObservation.Query query(){return observation.query();}
    }
    public record Unavailable(ContactScopeObservation.Query query,String reason) implements Response {
        public Unavailable {Objects.requireNonNull(query);require(reason!=null&&!reason.isBlank(),"actual contact unavailable reason required");}
    }
    public static ProjectedRequest projected(PublicBindings.Arguments arguments) {
        ObjectNode n=input(arguments);closed(n,"subject_army_id","target_province_id","incoming_entry_province_id","expected_revision");
        return new ProjectedRequest(new ProjectedContactPolicy.QueryKey(unit(n.get("subject_army_id")).value(),id(n.get("target_province_id")).value(),id(n.get("incoming_entry_province_id")).value()),decimal(n.get("expected_revision")));
    }
    public static ActualRequest actual(PublicBindings.Arguments arguments) {
        ObjectNode n=input(arguments);require(Set.of("subject_army_id","target_province_id","expected_revision").containsAll(names(n)),"invented actual contact argument");
        required(n,"subject_army_id","target_province_id");
        return new ActualRequest(new ActualContactModel.Query(unit(n.get("subject_army_id")).value(),id(n.get("target_province_id")).value()),field(n,"expected_revision",ContactScopePublicCodec::decimal));
    }
    public static RawJson encode(ProjectedRequest input) {
        var q=input.query();return new RawJson(bytes(empty().put("subject_army_id",q.subjectArmyId()).put("target_province_id",q.targetProvinceId())
                .put("incoming_entry_province_id",q.incomingEntryProvinceId()).put("expected_revision",input.expectedRevision().decimal())));
    }
    public static RawJson encode(ActualRequest input) {
        ObjectNode n=empty().put("subject_army_id",input.query().subjectArmyId()).put("target_province_id",input.query().targetProvinceId());
        if(input.expectedRevision() instanceof NullValue<UInt64>)n.putNull("expected_revision");
        else if(input.expectedRevision() instanceof Present<UInt64> value)n.put("expected_revision",value.value().decimal());
        return new RawJson(bytes(n));
    }
    public static Response capture(ContactScopeObservation.Query selected,PlanningReadResult<ContactScopeObservation> actual) {
        Objects.requireNonNull(selected);Objects.requireNonNull(actual);
        if(actual instanceof PlanningReadResult.Known<ContactScopeObservation> known) {
            require(known.value().query().equals(selected)&&known.receipt().request().operation().value().equals(selected.step()),"contact public result crossed its actual query");
            return new Available(known.value(),known.originalReceipt());
        }
        return new Unavailable(selected,((PlanningReadResult.Unavailable<ContactScopeObservation>)actual).reason());
    }
    public static RawJson encode(Response response) {
        if(response instanceof Unavailable missing)return new RawJson(bytes(empty().put("step",missing.query().step()).put("status","unavailable").put("reason",missing.reason())));
        var available=(Available)response;ObjectNode n=originalData(available.observation());
        n.set("original_read_receipt",available.originalReceipt().toJson());return new RawJson(bytes(n));
    }
    /** Original generic EXECUTE result. DATA formatting never grants a current read or a receipt. */
    public static RawJson encodeOriginal(ContactScopeObservation actual) { return new RawJson(bytes(originalData(actual))); }
    private static ObjectNode originalData(ContactScopeObservation actual) {
        ObjectNode n=object(OpportunityJson.toNode(Objects.requireNonNull(actual).normalizedResult()));
        for(String field:UINT64_FIELDS)n.put(field,u64(get(n,field)).decimal());
        ObjectNode body=object(n.get(actual.query() instanceof ContactScopeObservation.Projected?"projected_contact_scope":"actual_contact_scope"));
        body.put("snapshot_revision",positive(body.get("snapshot_revision")).decimal());
        return n;
    }
    /** Wire validation/roundtrip only. Reconstructed data is never a source-qualified ReadFamily result. */
    public static Response decode(RawJson encoded) {
        ObjectNode n=parse(encoded.bytes());String step=text(get(n,"step"));ContactScopeObservation.Query query=ContactScopeObservation.parseQuery(step);
        if(text(get(n,"status")).equals("unavailable")) {
            closed(n,"step","status","reason");return new Unavailable(query,text(n.get("reason")));
        }
        required(n,"original_read_receipt");ExactRef reference=ExactRef.fromJson(n.get("original_read_receipt"));n.remove("original_read_receipt");
        return new Available(decodeOriginalData(n),reference);
    }
    /** Strict generic wire DATA decoder, separate from the dedicated MCP receipt envelope. */
    public static ContactScopeObservation decodeOriginal(RawJson encoded) { return decodeOriginalData(parse(encoded.bytes())); }
    private static ContactScopeObservation decodeOriginalData(ObjectNode n) {
        ContactScopeObservation.Query query=ContactScopeObservation.parseQuery(text(get(n,"step")));
        String payload=query instanceof ContactScopeObservation.Projected?"projected_contact_scope":"actual_contact_scope";
        if(query instanceof ContactScopeObservation.Projected) {
            closed(n,"step","accepted","status","query_sequence","snapshot_revision",payload,"backend_id","queried_snapshot_id","queried_revision","queried_native_revision","queried_connection_generation","queried_episode_run_id");
        } else {
            closed(n,"step","accepted","status","query_sequence","snapshot_revision",payload,"queried_snapshot_id","queried_revision","queried_native_revision","queried_connection_generation","queried_episode_run_id");
        }
        yes(n.get("accepted"));equal(n.get("status"),"available");
        for(String field:UINT64_FIELDS) {UInt64 value=decimal(n.get(field));n.put(field,value.value());}
        BigInteger nativeRevision=positive(n.get("snapshot_revision")).value();
        require(nativeRevision.equals(positive(n.get("queried_native_revision")).value()),"contact public native revisions disagree");
        ObjectNode body=object(n.get(payload));body.put("snapshot_revision",decimal(body.get("snapshot_revision")).value());
        require(positive(body.get("snapshot_revision")).value().equals(nativeRevision),"contact public body revision differs");
        var observation=ContactScopeObservation.decodeHistoryResult(DriverJson.object(bytes(n),DriverJson.MAX_NATIVE_BYTES),i32(body.get("date_raw")));
        return observation;
    }
    public static Optional<BigInteger> expected(ActualRequest input) {
        return input.expectedRevision() instanceof Present<UInt64> p?Optional.of(p.value().value()):Optional.empty();
    }
    private static final List<String> UINT64_FIELDS=List.of("query_sequence","snapshot_revision","queried_revision","queried_native_revision","queried_connection_generation");
    private static ObjectNode input(PublicBindings.Arguments arguments) {
        require(arguments instanceof PublicBindings.Value,"contact query requires an argument object");
        byte[] bytes=((PublicBindings.Value)arguments).original().bytes();require(bytes.length<=65_536,"finite contact argument object required");return parse(bytes);
    }
    private static UInt64 decimal(JsonNode value) {
        String text=text(value);require(text.matches("0|[1-9][0-9]*"),"canonical public uint64 decimal string required");return new UInt64(new BigInteger(text));
    }
}
