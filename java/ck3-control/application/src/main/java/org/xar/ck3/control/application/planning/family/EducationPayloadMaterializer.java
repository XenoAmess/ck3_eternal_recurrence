package org.xar.ck3.control.application.planning.family;

import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.family.FamilyJson.*;

/** Revalidates the shared education review against this fresh source; it creates no native authority. */
public final class EducationPayloadMaterializer {
    public static final String REQUEST_SCHEMA = "xar.ck3.education-payload-reviewed-request-private.v1";
    public static final String PAYLOAD_SCHEMA = "xar.ck3.education-payload-materialization-private.v1";
    private static final Set<String> FIELDS = Set.of("schema", "request_id", "review_token", "expected_snapshot_id",
            "expected_revision", "expected_native_revision", "recipient_id", "child_full_id", "guardian_full_id", "requested_option_keys");
    private EducationPayloadMaterializer() { }
    public record Request(String requestId, String reviewToken, String snapshotId, BigInteger publicRevision,
            BigInteger nativeRevision, long recipient, long child, long guardian, List<String> optionKeys) {
        public Request {
            StrictJson.require(requestId != null && requestId.matches("[A-Za-z0-9_.:-]{1,128}"), "education request ID");
            StrictJson.require(reviewToken != null && reviewToken.matches("[0-9a-f]{64}"), "education content token");
            StrictJson.text(snapshotId); revision(publicRevision); revision(nativeRevision); fullId(recipient); fullId(child); fullId(guardian);
            StrictJson.require(child != guardian, "education child and guardian differ"); optionKeys = List.copyOf(optionKeys);
            StrictJson.require(optionKeys.size() <= 4096 && optionKeys.stream().distinct().count() == optionKeys.size(), "explicit distinct education option keys");
            for (String key : optionKeys) StrictJson.require(key != null && key.matches("[A-Za-z0-9_]{1,128}"), "education ASCII option key");
        }
        public Obj toJson() {
            return obj("schema", t(REQUEST_SCHEMA), "request_id", t(requestId), "review_token", t(reviewToken), "expected_snapshot_id", t(snapshotId),
                    "expected_revision", new IntegerValue(publicRevision), "expected_native_revision", new IntegerValue(nativeRevision),
                    "recipient_id", n(recipient), "child_full_id", n(child), "guardian_full_id", n(guardian),
                    "requested_option_keys", new Arr(optionKeys.stream().<Value>map(Text::new).toList()));
        }
    }
    public record Materialized(Request reviewed, Obj sourceQuery, Obj requestIntent, Obj semanticPayload, Obj projection) { }
    public static Request readRequest(Obj raw) {
        StrictJson.require(raw.members().keySet().equals(FIELDS) && REQUEST_SCHEMA.equals(text(raw.get("schema"))), "closed education reviewed request");
        return new Request(text(raw.get("request_id")), text(raw.get("review_token")), text(raw.get("expected_snapshot_id")),
                integer(raw.get("expected_revision")), integer(raw.get("expected_native_revision")), fullId(raw.get("recipient_id")),
                fullId(raw.get("child_full_id")), fullId(raw.get("guardian_full_id")), array(raw.get("requested_option_keys")).stream().map(FamilyJson::text).toList());
    }
    /** The token is generated from the actual query now, never supplied by an earlier planner observation. */
    public static Materialized prepareAndMaterialize(String requestId, Obj freshQuery, Obj currentSnapshot,
            long recipient, long child, long guardian, List<String> optionKeys) {
        Obj intent = intent(recipient, child, guardian, optionKeys);
        Obj prepared = FamilyEducationReview.prepare(freshQuery, currentSnapshot, intent);
        requireAvailable(prepared);
        Request request = new Request(requestId, text(prepared.get("review_token")), text(freshQuery.get("queried_snapshot_id")),
                integer(freshQuery.get("queried_revision")), integer(freshQuery.get("queried_native_revision")), recipient, child, guardian, optionKeys);
        return materialize(request, freshQuery, currentSnapshot);
    }
    public static Materialized materialize(Request request, Obj freshQuery, Obj currentSnapshot) {
        StrictJson.require(integer(currentSnapshot.get("revision")).equals(request.publicRevision()), "education actual public revision changed");
        Obj prepared = FamilyEducationReview.prepare(freshQuery, currentSnapshot,
                intent(request.recipient(), request.child(), request.guardian(), request.optionKeys()));
        requireAvailable(prepared); Obj source = object(prepared.get("source_query"));
        StrictJson.require(text(source.get("queried_snapshot_id")).equals(request.snapshotId())
                && integer(source.get("queried_native_revision")).equals(request.nativeRevision())
                && text(prepared.get("review_token")).equals(request.reviewToken()), "education reviewed source, token or frame changed");
        Obj actualIntent = object(prepared.get("request_intent")), payload = object(prepared.get("semantic_payload"));
        Obj result = obj("schema", t(PAYLOAD_SCHEMA), "status", t("constructed_offline"), "read_only", new Bool(true),
                "request_id", t(request.requestId()), "review_token", t(request.reviewToken()), "review_binding_verified", new Bool(true),
                "queried_snapshot_id", source.get("queried_snapshot_id"), "queried_revision", source.get("queried_revision"),
                "queried_native_revision", source.get("queried_native_revision"), "request_intent", actualIntent, "semantic_payload", payload,
                "source_query", source, "requested_shown", prepared.get("requested_shown"), "requested_can_send", prepared.get("requested_can_send"),
                "generic_ordinary_context_supported", prepared.get("generic_ordinary_context_supported"), "native_materialization_ready", new Bool(false),
                "native_materialization_reason", t("education_all_roles_options_command_join_unqualified"), "dispatch_ready", new Bool(false),
                "dispatch_invoked", new Bool(false), "submitted", new Bool(false), "material_result", new Bool(false));
        return new Materialized(request, source, actualIntent, payload, result);
    }
    private static Obj intent(long recipient, long child, long guardian, List<String> keys) {
        fullId(recipient); fullId(child); fullId(guardian);
        return obj("recipient_id", n(recipient), "child_full_id", n(child), "guardian_full_id", n(guardian),
                "requested_option_keys", new Arr(List.copyOf(keys).stream().<Value>map(Text::new).toList()));
    }
    private static void requireAvailable(Obj prepared) {
        StrictJson.require("available".equals(string(prepared.get("status"))), "education payload unavailable: " + prepared.get("reason"));
    }
    private static long fullId(Value value) { long id = integer(value).longValueExact(); fullId(id); return id; }
    private static void fullId(long value) { StrictJson.require(value > 0 && value <= 0xffff_fffeL, "complete unsigned Character ID"); }
    private static void revision(BigInteger value) { StrictJson.require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "exact uint64 education revision"); }
}
