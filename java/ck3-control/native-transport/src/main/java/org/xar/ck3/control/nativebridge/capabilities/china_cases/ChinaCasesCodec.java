package org.xar.ck3.control.nativebridge.capabilities.china_cases;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.*;

/** The sole dynamic boundary. Exact original native envelope/schema is checked before constructing records. */
public final class ChinaCasesCodec {
private ChinaCasesCodec() { }
private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
.enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
.streamReadConstraints(StreamReadConstraints.builder().maxStringLength(RawJson.MAXIMUM_BYTES)
.maxNumberLength(4300).maxNestingDepth(1000).build()).build())
.enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
.enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
public enum Family {
B1("query-zhongguo-b1-cycle-snapshot-v1", "game.command.query-zhongguo-b1-cycle-snapshot-v1", "game.command.query-zhongguo-b1-cycle-snapshot-v1", "zhongguo_b1_cycle_snapshot", Set.of("case_kind","closure","cycle","date_raw","manager_character_id","paused","pending","player_character_id","processing","provenance","quota","readiness","request_nonce","roster","schema_version","snapshot_revision","status","unavailable_reason"), Set.of("cycle_unavailable","lifecycle_not_reached","value_out_of_range","value_type_mismatch","variable_absent"), Set.of("cycle_inconsistent","cycle_not_found","internal_error","map_not_ready","requires_application_main","requires_paused","state_changed","unsupported_build","variable_context_unavailable","variable_identifier_unavailable")),
CASE("query-zhongguo-case-snapshot-v1", "game.command.query-zhongguo-case-snapshot-v1", "game.command.query-zhongguo-case-snapshot-v1", "zhongguo_case_snapshot", Set.of("case","case_kind","date_raw","deadline","operation","paused","player_character_id","policy","provenance","readiness","receipt","request_nonce","requested_owner_character_id","schema_version","snapshot_revision","status","subject_character_id","unavailable_reason"), Set.of("case_unavailable","deadline_inconsistent","deadline_not_scheduled","due_date_not_persisted_by_product","no_operation_recorded","not_applicable","receipt_inconsistent","receipt_not_recorded","unknown_allowlisted_operation","value_out_of_range","value_type_mismatch","variable_absent"), Set.of("case_not_found","internal_error","map_not_ready","owner_filter_mismatch","player_binding_mismatch","requires_application_main","requires_paused","state_changed","subject_not_found","unsupported_build","variable_context_unavailable","variable_identifier_unavailable")),
AIOWNED("query-zhongguo-ai-owned-case-snapshot-v1", "game.command.query-zhongguo-ai-owned-case-snapshot-v1", "game.command.query-zhongguo-ai-owned-case-snapshot-v1", "zhongguo_ai_owned_case_snapshot", Set.of("case","case_kind","date_raw","operation","owner_eligibility","paused","player_character_id","policy","provenance","readiness","receipt","request_nonce","requested_owner_character_id","route","schema_version","snapshot_revision","stage","status","subject_character_id","unavailable_reason"), Set.of("case_unavailable","no_operation_recorded","not_applicable","receipt_inconsistent","receipt_not_recorded","stage_inconsistent","unknown_allowlisted_operation","value_out_of_range","value_type_mismatch","variable_absent"), Set.of("case_not_found","internal_error","map_not_ready","owner_eligibility_unavailable","owner_filter_mismatch","owner_is_played_character","owner_not_ai","owner_not_alive","owner_not_celestial","owner_not_landed_duke_plus","requires_application_main","requires_paused","state_changed","subject_not_direct_subject","subject_not_found","unsupported_build","variable_context_unavailable","variable_identifier_unavailable")),
RESULT("query-zhongguo-result-case-snapshot-v1", "game.command.query-zhongguo-result-case-snapshot-v1", "game.command.query-zhongguo-result-case-snapshot-v1", "zhongguo_result_case_snapshot", Set.of("case","case_kind","date_raw","delivery","notice","paused","player_character_id","provenance","readiness","request_nonce","requested_owner_character_id","schema_version","snapshot_revision","status","subject_character_id","unavailable_reason"), Set.of("case_unavailable","value_out_of_range","value_type_mismatch","variable_absent"), Set.of("case_inconsistent","case_not_found","internal_error","map_not_ready","not_received_self","owner_filter_mismatch","requires_application_main","requires_paused","state_changed","unsupported_build","variable_context_unavailable","variable_identifier_unavailable")),
PIP("query-zhongguo-b2-pip-snapshot-v1", "game.command.query-zhongguo-b2-pip-snapshot-v1", "game.command.query-zhongguo-b2-pip-snapshot-v1", "zhongguo_b2_pip_snapshot", Set.of("budget_ledger","case_kind","d180_ticket","d365_ticket","date_raw","gate","midpoint","next_cycle_evidence","outcome","paused","pip","pip_modifier_present","player_character_id","provenance","readiness","request_nonce","requested_owner_character_id","response","schema_version","snapshot_revision","status","subject_character_id","support","unavailable_reason"), Set.of("case_binding_mismatch","case_unavailable","native_observation_unavailable","not_applicable","product_not_persisted","value_out_of_range","value_type_mismatch","variable_absent"), Set.of("case_inconsistent","case_not_found","internal_error","map_not_ready","not_received_self","owner_filter_mismatch","requires_application_main","requires_paused","state_changed","unsupported_build","variable_context_unavailable","variable_identifier_unavailable")),
PROMOTION("query-zhongguo-promotion-compensation-postcondition-v1", "game.command.query-zhongguo-promotion-compensation-postcondition-v1", "game.command.query-zhongguo-promotion-compensation-postcondition-v1", "zhongguo_promotion_compensation_postcondition", Set.of("schema_version","status","capability","source_backend_id","request_nonce","snapshot_revision","date_raw","paused","player_character_id","readiness","unavailable_reason","subject_character_id","promotion_compensation"), Set.of(), Set.of()),
AF5("query-zhongguo-compensation-af5-snapshot-v1", "game.command.query-zhongguo-compensation-af5-snapshot-v1", "game.command.query-zhongguo-compensation-af5-snapshot-v1", "zhongguo_compensation_af5_snapshot", Set.of("schema_version","status","capability","source_backend_id","request_nonce","snapshot_revision","date_raw","paused","player_character_id","readiness","unavailable_reason","subject_character_id","af5","terminal"), Set.of(), Set.of()),
PROJECTS("query-zhongguo-projects-metrics-postcondition-v1", "game.command.query-zhongguo-projects-metrics-postcondition-v1", "game.command.query-zhongguo-projects-metrics-postcondition-v1", "zhongguo_projects_metrics_postcondition", Set.of("schema_version","status","capability","source_backend_id","request_nonce","snapshot_revision","date_raw","paused","player_character_id","readiness","unavailable_reason","case_kind","requested_owner_character_id","requested_subject_character_id","checkpoint_state","credit_project_portfolio","source_identity","result_identity","projects_metrics","provenance"), Set.of(), Set.of()),
INCIDENT("query-zhongguo-incident-snapshot-v1", "game.command.query-zhongguo-incident-snapshot-v1", "game.command.query-zhongguo-incident-snapshot-v1", "zhongguo_incident_snapshot", Set.of("case_kind","date_raw","kpi","paused","player_character_id","probe","profile","provenance","readiness","request_nonce","requested_owner_character_id","resources","schema_version","snapshot_revision","status","subject_character_id","terminal","unavailable_reason"), Set.of("kpi_not_staged","not_applicable","not_yet_consumed","snapshot_unavailable","terminal_not_selected","value_out_of_range","value_type_mismatch","variable_absent"), Set.of("incident_inconsistent","incident_not_found","internal_error","map_not_ready","not_received_self","owner_filter_mismatch","requires_application_main","requires_paused","state_changed","unsupported_build","variable_context_unavailable","variable_identifier_unavailable")),
SCOREBOARD("query-zhongguo-scoreboard-state-v1", "game.command.query-zhongguo-scoreboard-state-v1", "game.command.query-zhongguo-scoreboard-state-v1", "zhongguo_scoreboard_state", Set.of("acl","actions","case_kind","date_raw","observation_sequence","observed_state_revision","paused","player_character_id","provenance","provider_session_id","readiness","request_nonce","schema_version","semantic_fingerprint_v1","snapshot_revision","status","tree_fingerprint_v1","unavailable_reason","widgets"), Set.of("enabled_state_abi_not_frozen","focus_owner_abi_not_frozen","modal_blocking_abi_not_frozen","named_clickable_child_not_stable","read_only_provider_action_not_exposed","screen_rect_abi_not_frozen","scroll_area_extent_abi_not_frozen","snapshot_unavailable","state_projection_unavailable","surface_not_available","value_out_of_range","value_type_mismatch","variable_absent","widget_not_instantiated"), Set.of("acl_inconsistent","gui_root_unavailable","internal_error","map_not_ready","provider_revision_unavailable","requires_application_main","requires_paused","state_changed","state_projection_unavailable","unsupported_build","widget_not_instantiated","widget_state_unavailable")),
PROGRESS("query-zhongguo-promotion-source-progress-v1", "game.contract.zhongguo-promotion-source-progress-v1-fail-closed", "game.command.query-zhongguo-promotion-source-progress-v1", "zhongguo_promotion_source_progress", Set.of("schema_version","status","capability","source_backend_id","request_nonce","snapshot_revision","date_raw","paused","player_character_id","readiness","unavailable_reason","widgets"), Set.of(), Set.of());

final String step, requiredCapability, capability, payload;
final Set<String> fields, fieldReasons, topReasons;
Family(String step, String requiredCapability, String capability, String payload, Set<String> fields, Set<String> fieldReasons, Set<String> topReasons) {
this.step=step; this.requiredCapability=requiredCapability; this.capability=capability; this.payload=payload;
this.fields=fields; this.fieldReasons=fieldReasons; this.topReasons=topReasons;
}
public String step() { return step; }
public String capability() { return requiredCapability; }
}
static ObjectNode parse(RawJson original) {
try { JsonNode node=JSON.readTree(original.bytes()); check(node instanceof ObjectNode,"native object required"); return (ObjectNode)node; }
catch (IOException failure) { throw new IllegalArgumentException("invalid original native JSON",failure); }
}
static ObjectNode exact(JsonNode node, Set<String> fields) { return StrictJson.object(node,fields); }
static void check(boolean condition,String reason) { StrictJson.require(condition,reason); }
static String text(JsonNode node) { check(node!=null && node.isTextual(),"exact string required"); return node.textValue(); }
static boolean bool(JsonNode node) { check(node!=null && node.isBoolean(),"exact boolean required"); return node.booleanValue(); }
static BigInteger integer(JsonNode node) { check(node!=null && node.isIntegralNumber(),"exact integer required; bool/float/string refused"); return node.bigIntegerValue(); }
static BigInteger uint64(JsonNode node,boolean positive) { BigInteger n=integer(node); check(n.compareTo(positive?BigInteger.ONE:BigInteger.ZERO)>=0 && n.compareTo(StrictJson.UINT64_MAX)<=0,"uint64 required"); return n; }
static CharacterId character(JsonNode node) { return new CharacterId(integer(node).intValueExact()); }
static <E extends Enum<E>> E enumeration(JsonNode node,Class<E> type) {
String value=text(node); E result=Enum.valueOf(type,value.replace('-','_').toUpperCase(Locale.ROOT));
check(result.name().toLowerCase(Locale.ROOT).equals(value.replace('-','_')),"canonical enum required"); return result;
}
private static <T> Field<T> field(JsonNode node,Family family,java.util.function.Function<JsonNode,T> decode) {
ObjectNode f=exact(node,Set.of("status","value","unavailable_reason")); String status=text(f.get("status"));
if(status.equals("available")) { check(f.get("unavailable_reason").isNull(),"available field reason must be null"); return new Available<>(decode.apply(f.get("value"))); }
check(status.equals("unavailable") && f.get("value").isNull(),"typed unavailable field must have null value");
String reason=text(f.get("unavailable_reason")); check(family.fieldReasons.isEmpty() || family.fieldReasons.contains(reason),"field unavailable reason not allowlisted"); return new Unavailable<>(reason);
}
private static Field<BigInteger> i(ObjectNode n,String k,Family f) { return intField(n.get(k),f); }
private static Field<Boolean> b(ObjectNode n,String k,Family f) { return boolField(n.get(k),f); }
private static Field<String> t(ObjectNode n,String k,Family f) { return textField(n.get(k),f,k); }
private static Field<BigInteger> intField(JsonNode node,Family f) {
return field(node,f,value->{BigInteger n=integer(value);
if(f==Family.CASE || f==Family.AIOWNED || f==Family.RESULT || f==Family.PIP || f==Family.INCIDENT || f==Family.SCOREBOARD)
check(n.bitLength()<=63,"signed int64 field required");
return n;});
}
private static Field<Boolean> boolField(JsonNode node,Family f) { return field(node,f,ChinaCasesCodec::bool); }
private static Field<String> textField(JsonNode node,Family f,String field) {
return field(node,f,value->{String s=text(value);
if(field.endsWith("pointer")) check(s.matches("0x[0-9A-F]+"),"uppercase native pointer required");
else if(f==Family.CASE || f==Family.AIOWNED) check(s.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"),"bounded stable key required");
return s;});
}
private static Header header(ObjectNode frame,Family family,PlanningReadReceipt receipt) {
var before=receipt.request().before(); var id=before.frame().identity();
check(integer(frame.get("schema_version")).equals(BigInteger.ONE),"schema version must be exact integer 1");
check(uint64(frame.get("snapshot_revision"),true).equals(id.nativeRevision()),"native revision changed");
int date=integer(frame.get("date_raw")).intValueExact(); check(BigInteger.valueOf(date).equals(id.dateRaw()),"paused date changed");
check(bool(frame.get("paused")),"paused true required"); CharacterId player=character(frame.get("player_character_id"));
check(player.integer().equals(id.player()),"played character changed");
ObjectNode args=(ObjectNode)OpportunityJson.toNode(receipt.request().arguments());
Nonce nonce=new Nonce(text(frame.get("request_nonce"))); check(nonce.value().equals(text(args.get("request_nonce"))),"query nonce changed");
Status status=enumeration(frame.get("status"),Status.class);
JsonNode reason=frame.get("unavailable_reason"); Optional<String> unavailable=reason.isNull()?Optional.empty():Optional.of(text(reason));
if(status==Status.UNAVAILABLE) check(family.topReasons.isEmpty() || family.topReasons.contains(unavailable.orElseThrow()),"top reason not allowlisted");
switch(family) {
case B1 -> check(text(frame.get("case_kind")).equals("zhongguo.b1.cycle"),"fixed case kind drift");
case CASE -> check(text(frame.get("case_kind")).equals("zhongguo.b1.performance"),"fixed case kind drift");
case AIOWNED -> check(text(frame.get("case_kind")).equals("zhongguo.b1.performance"),"fixed case kind drift");
case RESULT -> check(text(frame.get("case_kind")).equals("zhongguo.result.received-self"),"fixed case kind drift");
case PIP -> check(text(frame.get("case_kind")).equals("zhongguo.b2.pip"),"fixed case kind drift");
case PROJECTS -> check(text(frame.get("case_kind")).equals("zhongguo.projects-metrics.project-correlation"),"fixed case kind drift");
case INCIDENT -> check(text(frame.get("case_kind")).equals("zhongguo.incident.subject-self"),"fixed case kind drift");
case SCOREBOARD -> check(text(frame.get("case_kind")).equals("zhongguo.scoreboard.named-state-acl"),"fixed case kind drift");
default -> { }
}
String backend;
if(frame.has("provenance") && family!=Family.PROJECTS) {
ObjectNode provenance=(ObjectNode)frame.get("provenance"); verifyProvenance(provenance,family); backend=text(provenance.get("backend_id"));
} else backend=text(frame.get("source_backend_id"));
if(frame.has("capability")) check(text(frame.get("capability")).equals(family.capability),"provider capability changed");
return new Header(status,nonce,id.nativeRevision(),date,player,backend,unavailable);
}
static ObjectNode envelope(PlanningReadReceipt receipt,Family family) {
check(receipt.original().nativeOk(),"native query outer success required");
ObjectNode result=parse(receipt.original().originalResultToken().orElseThrow());
Set<String> keys=family==Family.PROGRESS?Set.of("step","accepted","status","query_sequence","snapshot_revision",family.payload,"production_capability_advertised","backend_id"):
Set.of("step","accepted","status","query_sequence","snapshot_revision",family.payload,"backend_id");
exact(result,keys); check(text(result.get("step")).equals(family.step) && bool(result.get("accepted")),"native query identity mismatch");
uint64(result.get("query_sequence"),true); check(uint64(result.get("snapshot_revision"),true).equals(receipt.request().before().frame().identity().nativeRevision()),"query envelope revision drift");
check(!text(result.get("backend_id")).isEmpty(),"native backend missing");
ObjectNode frame=exact(result.get(family.payload),family.fields);
check(text(result.get("status")).equals(text(frame.get("status"))),"native envelope status differs from payload");
if(family==Family.PROGRESS) check(!bool(result.get("production_capability_advertised")),"fail-closed progress must not advertise production");
return frame;
}
/** Original ten query drivers; pure replay never issues this source-owned live diagnostic. */
static Optional<ChinaCasesFacade.OriginalDriverFailure.Kind> originalCaseEnvelopeFailure(PlanningReadReceipt receipt) {
    return originalDriverEnvelopeFailure(receipt,Family.CASE);
}
static Optional<ChinaCasesFacade.OriginalDriverFailure.Kind> originalDriverEnvelopeFailure(PlanningReadReceipt receipt,Family family) {
    if(family==Family.PROGRESS)return Optional.empty();
    check(receipt.original().nativeOk(),"native query outer success required");
    ObjectNode result=parse(receipt.original().originalResultToken().orElseThrow());
    Set<String> keys=Set.of("step","accepted","status","query_sequence","snapshot_revision",family.payload,"backend_id");
    var actualKeys=new java.util.HashSet<String>();result.fieldNames().forEachRemaining(actualKeys::add);
    JsonNode step=result.get("step"),accepted=result.get("accepted");
    if(!actualKeys.equals(keys)||step==null||!step.isTextual()||!step.textValue().equals(family.step)
            ||accepted==null||!accepted.isBoolean()||!accepted.booleanValue()
            ||!pythonNumericEqual(result.get("snapshot_revision"),receipt.request().before().frame().identity().nativeRevision()))
        return Optional.of(originalKind(family,false));
    JsonNode sequence=result.get("query_sequence");
    if(sequence==null||!sequence.isIntegralNumber()||sequence.bigIntegerValue().signum()<=0
            ||(family!=Family.B1&&sequence.bigIntegerValue().compareTo(StrictJson.UINT64_MAX)>0))
        return Optional.of(originalKind(family,true));
    return Optional.empty();
}
private static ChinaCasesFacade.OriginalDriverFailure.Kind originalKind(Family family,boolean sequence) {
    return switch(family) {
        case B1 -> sequence?ChinaCasesFacade.OriginalDriverFailure.Kind.B1_QUERY_SEQUENCE_MISSING:ChinaCasesFacade.OriginalDriverFailure.Kind.B1_MALFORMED_ENVELOPE;
        case CASE -> sequence?ChinaCasesFacade.OriginalDriverFailure.Kind.CASE_QUERY_SEQUENCE_MISSING:ChinaCasesFacade.OriginalDriverFailure.Kind.CASE_MALFORMED_ENVELOPE;
        case AIOWNED -> sequence?ChinaCasesFacade.OriginalDriverFailure.Kind.AIOWNED_QUERY_SEQUENCE_MISSING:ChinaCasesFacade.OriginalDriverFailure.Kind.AIOWNED_MALFORMED_ENVELOPE;
        case RESULT -> sequence?ChinaCasesFacade.OriginalDriverFailure.Kind.RESULT_QUERY_SEQUENCE_MISSING:ChinaCasesFacade.OriginalDriverFailure.Kind.RESULT_MALFORMED_ENVELOPE;
        case PIP -> sequence?ChinaCasesFacade.OriginalDriverFailure.Kind.PIP_QUERY_SEQUENCE_MISSING:ChinaCasesFacade.OriginalDriverFailure.Kind.PIP_MALFORMED_ENVELOPE;
        case PROMOTION -> sequence?ChinaCasesFacade.OriginalDriverFailure.Kind.PROMOTION_QUERY_SEQUENCE_MISSING:ChinaCasesFacade.OriginalDriverFailure.Kind.PROMOTION_MALFORMED_ENVELOPE;
        case AF5 -> sequence?ChinaCasesFacade.OriginalDriverFailure.Kind.AF5_QUERY_SEQUENCE_MISSING:ChinaCasesFacade.OriginalDriverFailure.Kind.AF5_MALFORMED_ENVELOPE;
        case PROJECTS -> sequence?ChinaCasesFacade.OriginalDriverFailure.Kind.PROJECTS_QUERY_SEQUENCE_MISSING:ChinaCasesFacade.OriginalDriverFailure.Kind.PROJECTS_MALFORMED_ENVELOPE;
        case INCIDENT -> sequence?ChinaCasesFacade.OriginalDriverFailure.Kind.INCIDENT_QUERY_SEQUENCE_MISSING:ChinaCasesFacade.OriginalDriverFailure.Kind.INCIDENT_MALFORMED_ENVELOPE;
        case SCOREBOARD -> sequence?ChinaCasesFacade.OriginalDriverFailure.Kind.SCOREBOARD_QUERY_SEQUENCE_MISSING:ChinaCasesFacade.OriginalDriverFailure.Kind.SCOREBOARD_MALFORMED_ENVELOPE;
        case PROGRESS -> throw new IllegalArgumentException("PROGRESS has no Cases10 original driver branch");
    };
}
/** Original Python envelope equality accepts bool/float numeric equality. Later strict Java guards stay separate. */
private static boolean pythonNumericEqual(JsonNode original,BigInteger expected) {
    if(original==null)return false;
    if(original.isBoolean())return expected.equals(original.booleanValue()?BigInteger.ONE:BigInteger.ZERO);
    if(original.isIntegralNumber())return expected.equals(original.bigIntegerValue());
    if(original.isFloatingPointNumber()) {
        double value=original.doubleValue();
        if(!Double.isFinite(value))return false;
        try{return new java.math.BigDecimal(value).toBigIntegerExact().equals(expected);}
        catch(ArithmeticException fractional){return false;}
    }
    return false;
}
public static BigInteger querySequence(PlanningReadReceipt receipt,Family family) { envelope(receipt,family); return uint64(parse(receipt.original().originalResultToken().orElseThrow()).get("query_sequence"),true); }
private static void verifyProvenance(ObjectNode node,Family family) {
switch(family) {
case B1 -> {
exact(node,Set.of("game_version","executable_sha256","backend_id","consumer_id","allowlist_id","variable_context_for_scope_rva","variable_identifier_table_rva","variable_identifier_lookup_rva","variable_identifier_name_rva","character_storage_slot_rva"));
check(text(node.get("game_version")).equals("1.19.0.6"),"provenance drift");
check(text(node.get("executable_sha256")).equals("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),"provenance drift");
check(text(node.get("backend_id")).equals("ck3-1.19.0.6-native-zhongguo-b1-cycle-snapshot-v1"),"provenance drift");
check(text(node.get("consumer_id")).equals("xar-autoplayer-zhongguo-b1-cycle-snapshot-v1"),"provenance drift");
check(text(node.get("allowlist_id")).equals("zg361-b1-cycle-manager-v1"),"provenance drift");
check(text(node.get("variable_context_for_scope_rva")).equals("0x3329A40"),"provenance drift");
check(text(node.get("variable_identifier_table_rva")).equals("0x3B971A0"),"provenance drift");
check(text(node.get("variable_identifier_lookup_rva")).equals("0x3B97020"),"provenance drift");
check(text(node.get("variable_identifier_name_rva")).equals("0x3B97090"),"provenance drift");
check(text(node.get("character_storage_slot_rva")).equals("0x570C130"),"provenance drift");
}
case CASE -> {
exact(node,Set.of("game_version","executable_sha256","backend_id","consumer_id","allowlist_id","variable_context_for_scope_rva","variable_identifier_table_rva","variable_identifier_lookup_rva","variable_identifier_name_rva","character_storage_slot_rva"));
check(text(node.get("game_version")).equals("1.19.0.6"),"provenance drift");
check(text(node.get("executable_sha256")).equals("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),"provenance drift");
check(text(node.get("backend_id")).equals("ck3-1.19.0.6-native-zhongguo-case-snapshot-v1"),"provenance drift");
check(text(node.get("consumer_id")).equals("xar-autoplayer-zhongguo-case-snapshot-v1"),"provenance drift");
check(text(node.get("allowlist_id")).equals("zg361-b1-performance-case-v1"),"provenance drift");
check(text(node.get("variable_context_for_scope_rva")).equals("0x3329A40"),"provenance drift");
check(text(node.get("variable_identifier_table_rva")).equals("0x3B971A0"),"provenance drift");
check(text(node.get("variable_identifier_lookup_rva")).equals("0x3B97020"),"provenance drift");
check(text(node.get("variable_identifier_name_rva")).equals("0x3B97090"),"provenance drift");
check(text(node.get("character_storage_slot_rva")).equals("0x570C130"),"provenance drift");
}
case AIOWNED -> {
exact(node,Set.of("game_version","executable_sha256","backend_id","consumer_id","allowlist_id","variable_context_for_scope_rva","character_storage_slot_rva","primary_title_rva","immediate_liege_rva","government_rva","is_human_player_rva"));
check(text(node.get("game_version")).equals("1.19.0.6"),"provenance drift");
check(text(node.get("executable_sha256")).equals("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),"provenance drift");
check(text(node.get("backend_id")).equals("ck3-1.19.0.6-native-zhongguo-ai-owned-case-snapshot-v1"),"provenance drift");
check(text(node.get("consumer_id")).equals("xar-autoplayer-zhongguo-ai-owned-case-snapshot-v1"),"provenance drift");
check(text(node.get("allowlist_id")).equals("zg361-b1-ai-owned-case-v1"),"provenance drift");
check(text(node.get("variable_context_for_scope_rva")).equals("0x3329A40"),"provenance drift");
check(text(node.get("character_storage_slot_rva")).equals("0x570C130"),"provenance drift");
check(text(node.get("primary_title_rva")).equals("0x25F3350"),"provenance drift");
check(text(node.get("immediate_liege_rva")).equals("0x2613480"),"provenance drift");
check(text(node.get("government_rva")).equals("0x26165B0"),"provenance drift");
check(text(node.get("is_human_player_rva")).equals("0x28BCEB0"),"provenance drift");
}
case RESULT -> {
exact(node,Set.of("game_version","executable_sha256","backend_id","consumer_id","allowlist_id","variable_context_for_scope_rva","variable_identifier_table_rva","variable_identifier_lookup_rva","variable_identifier_name_rva","character_storage_slot_rva"));
check(text(node.get("game_version")).equals("1.19.0.6"),"provenance drift");
check(text(node.get("executable_sha256")).equals("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),"provenance drift");
check(text(node.get("backend_id")).equals("ck3-1.19.0.6-native-zhongguo-result-case-snapshot-v1"),"provenance drift");
check(text(node.get("consumer_id")).equals("xar-autoplayer-zhongguo-result-case-snapshot-v1"),"provenance drift");
check(text(node.get("allowlist_id")).equals("zg361-result-received-self-v1"),"provenance drift");
check(text(node.get("variable_context_for_scope_rva")).equals("0x3329A40"),"provenance drift");
check(text(node.get("variable_identifier_table_rva")).equals("0x3B971A0"),"provenance drift");
check(text(node.get("variable_identifier_lookup_rva")).equals("0x3B97020"),"provenance drift");
check(text(node.get("variable_identifier_name_rva")).equals("0x3B97090"),"provenance drift");
check(text(node.get("character_storage_slot_rva")).equals("0x570C130"),"provenance drift");
}
case PIP -> {
exact(node,Set.of("game_version","executable_sha256","backend_id","consumer_id","allowlist_id","variable_context_for_scope_rva","variable_identifier_table_rva","variable_identifier_lookup_rva","variable_identifier_name_rva","character_storage_slot_rva"));
check(text(node.get("game_version")).equals("1.19.0.6"),"provenance drift");
check(text(node.get("executable_sha256")).equals("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),"provenance drift");
check(text(node.get("backend_id")).equals("ck3-1.19.0.6-native-zhongguo-b2-pip-snapshot-v1"),"provenance drift");
check(text(node.get("consumer_id")).equals("xar-autoplayer-zhongguo-b2-pip-snapshot-v1"),"provenance drift");
check(text(node.get("allowlist_id")).equals("zg361-b2-pip-received-self-v1"),"provenance drift");
check(text(node.get("variable_context_for_scope_rva")).equals("0x3329A40"),"provenance drift");
check(text(node.get("variable_identifier_table_rva")).equals("0x3B971A0"),"provenance drift");
check(text(node.get("variable_identifier_lookup_rva")).equals("0x3B97020"),"provenance drift");
check(text(node.get("variable_identifier_name_rva")).equals("0x3B97090"),"provenance drift");
check(text(node.get("character_storage_slot_rva")).equals("0x570C130"),"provenance drift");
}
case INCIDENT -> {
exact(node,Set.of("game_version","executable_sha256","backend_id","consumer_id","allowlist_id","variable_context_for_scope_rva","variable_identifier_table_rva","variable_identifier_lookup_rva","variable_identifier_name_rva","character_storage_slot_rva","manager_treasury_source"));
check(text(node.get("game_version")).equals("1.19.0.6"),"provenance drift");
check(text(node.get("executable_sha256")).equals("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),"provenance drift");
check(text(node.get("backend_id")).equals("ck3-1.19.0.6-native-zhongguo-incident-snapshot-v1"),"provenance drift");
check(text(node.get("consumer_id")).equals("xar-autoplayer-zhongguo-incident-snapshot-v1"),"provenance drift");
check(text(node.get("allowlist_id")).equals("zg361-incident-terminal-x-y-z-v1"),"provenance drift");
check(text(node.get("variable_context_for_scope_rva")).equals("0x3329A40"),"provenance drift");
check(text(node.get("variable_identifier_table_rva")).equals("0x3B971A0"),"provenance drift");
check(text(node.get("variable_identifier_lookup_rva")).equals("0x3B97020"),"provenance drift");
check(text(node.get("variable_identifier_name_rva")).equals("0x3B97090"),"provenance drift");
check(text(node.get("character_storage_slot_rva")).equals("0x570C130"),"provenance drift");
check(text(node.get("manager_treasury_source")).equals("zg361_ip_probe_manager_treasury"),"provenance drift");
}
case SCOREBOARD -> {
exact(node,Set.of("game_version","executable_sha256","backend_id","consumer_id","allowlist_id","gui_global_slot_rva","find_top_level_widget_rva","widget_hidden_flags_offset","widget_local_hidden_mask","widget_effective_hidden_mask","widget_local_disabled_mask","widget_effective_disabled_mask","widget_parent_offset","widget_children_offset","widget_name_offset","modal_receivers_offset","modal_receiver_count_offset","tree_fingerprint_domain","semantic_fingerprint_domain","state_digest_domain","query_scope","contract_stage"));
check(text(node.get("game_version")).equals("1.19.0.6"),"provenance drift");
check(text(node.get("executable_sha256")).equals("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),"provenance drift");
check(text(node.get("backend_id")).equals("ck3-1.19.0.6-native-zhongguo-scoreboard-state-v1"),"provenance drift");
check(text(node.get("consumer_id")).equals("xar-autoplayer-zhongguo-scoreboard-state-v1"),"provenance drift");
check(text(node.get("allowlist_id")).equals("zg361-scoreboard-fixed-widget-acl-v1"),"provenance drift");
check(text(node.get("gui_global_slot_rva")).equals("0x576CC68"),"provenance drift");
check(text(node.get("find_top_level_widget_rva")).equals("0x36D0B20"),"provenance drift");
check(text(node.get("widget_hidden_flags_offset")).equals("0xD0"),"provenance drift");
check(text(node.get("widget_local_hidden_mask")).equals("0x10"),"provenance drift");
check(text(node.get("widget_effective_hidden_mask")).equals("0x08"),"provenance drift");
check(text(node.get("widget_local_disabled_mask")).equals("0x04"),"provenance drift");
check(text(node.get("widget_effective_disabled_mask")).equals("0x02"),"provenance drift");
check(text(node.get("widget_parent_offset")).equals("0xE8"),"provenance drift");
check(text(node.get("widget_children_offset")).equals("0xF0"),"provenance drift");
check(text(node.get("widget_name_offset")).equals("0x1B8"),"provenance drift");
check(text(node.get("modal_receivers_offset")).equals("0x290"),"provenance drift");
check(text(node.get("modal_receiver_count_offset")).equals("0x29C"),"provenance drift");
check(text(node.get("tree_fingerprint_domain")).equals("XAR/ZG361/SCOREBOARD/TREE/V1\u0000"),"provenance drift");
check(text(node.get("semantic_fingerprint_domain")).equals("XAR/ZG361/SCOREBOARD/SEMANTIC/V1\u0000"),"provenance drift");
check(text(node.get("state_digest_domain")).equals("XAR/ZG361/SCOREBOARD/STATE/V1\u0000"),"provenance drift");
check(text(node.get("query_scope")).equals("fixed_scoreboard_instances_and_player_frozen_acl"),"provenance drift");
check(text(node.get("contract_stage")).equals("static_provider_observed_revision_live_unverified"),"provenance drift");
}
default -> throw new IllegalArgumentException("family has no offset provenance contract");
}
}
private static CaseIdentity g0(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("owner_character_id","subject_character_id","cycle_serial","case_serial","state","active","revision","timeline_serial","feedback_revision"));
return new CaseIdentity(i(n,"owner_character_id",f), i(n,"subject_character_id",f), i(n,"cycle_serial",f), i(n,"case_serial",f), i(n,"state",f), b(n,"active",f), i(n,"revision",f), i(n,"timeline_serial",f), i(n,"feedback_revision",f));
}
private static Policy g1(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("policy_id","choice"));
return new Policy(t(n,"policy_id",f), i(n,"choice",f));
}
private static Operation g2(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("operation_id","operation_key","hook","pre_state","post_state"));
return new Operation(i(n,"operation_id",f), t(n,"operation_key",f), t(n,"hook",f), i(n,"pre_state",f), i(n,"post_state",f));
}
private static Receipt g3(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("status","key","owner_character_id","subject_character_id","cycle_serial","case_serial","state","choice"));
return new Receipt(enumeration(n.get("status"),ReceiptStatus.class), t(n,"key",f), i(n,"owner_character_id",f), i(n,"subject_character_id",f), i(n,"cycle_serial",f), i(n,"case_serial",f), i(n,"state",f), i(n,"choice",f));
}
private static Deadline g4(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("status","target_character_id","owner_character_id","cycle_serial","case_serial","expected_state","days","open_date_raw","due_date_raw","pending","expired","on_due_operation"));
return new Deadline(enumeration(n.get("status"),DeadlineStatus.class), i(n,"target_character_id",f), i(n,"owner_character_id",f), i(n,"cycle_serial",f), i(n,"case_serial",f), i(n,"expected_state",f), i(n,"days",f), i(n,"open_date_raw",f), i(n,"due_date_raw",f), b(n,"pending",f), b(n,"expired",f), t(n,"on_due_operation",f));
}
private static B1Cycle g5(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("cycle_serial","case_serial","state","open_year","runtime_schema","active"));
return new B1Cycle(i(n,"cycle_serial",f), i(n,"case_serial",f), i(n,"state",f), i(n,"open_year",f), i(n,"runtime_schema",f), b(n,"active",f));
}
private static B1Roster g6(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("subject_count","before_prune_count","pruned_count","amendment_count","audit_version","reopen_required"));
return new B1Roster(i(n,"subject_count",f), i(n,"before_prune_count",f), i(n,"pruned_count",f), i(n,"amendment_count",f), i(n,"audit_version",f), b(n,"reopen_required",f));
}
private static B1Processing g7(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("count","agenda_count","local_candidate_count","pre_calibration_valid_count"));
return new B1Processing(i(n,"count",f), i(n,"agenda_count",f), i(n,"local_candidate_count",f), i(n,"pre_calibration_valid_count",f));
}
private static B1Quota g8(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("rebuild_generation","built_case_serial","book_version","target_top","target_middle","target_bottom","recount_top","recount_middle","recount_bottom","pre_calibration_expected_count","pre_calibration_mismatch","pool_membership"));
return new B1Quota(i(n,"rebuild_generation",f), i(n,"built_case_serial",f), i(n,"book_version",f), i(n,"target_top",f), i(n,"target_middle",f), i(n,"target_bottom",f), i(n,"recount_top",f), i(n,"recount_middle",f), i(n,"recount_bottom",f), i(n,"pre_calibration_expected_count",f), b(n,"pre_calibration_mismatch",f), b(n,"pool_membership",f));
}
private static B1Closure g9(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("calibration_finalized","state","rewards_issued","publication_blocked"));
return new B1Closure(b(n,"calibration_finalized",f), i(n,"state",f), b(n,"rewards_issued",f), b(n,"publication_blocked",f));
}
private static B1Pending g10(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("open_count","slot_used","reward_expected_count","rewards_paid_count","rewards_committed","watchdog_cancelled_count","watchdog_orphan_count"));
return new B1Pending(i(n,"open_count",f), i(n,"slot_used",f), i(n,"reward_expected_count",f), i(n,"rewards_paid_count",f), b(n,"rewards_committed",f), i(n,"watchdog_cancelled_count",f), i(n,"watchdog_orphan_count",f));
}
private static OwnerEligibility g11(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("owner_character_id","owner_alive","owner_is_ai","primary_title_id","primary_title_tier_raw","primary_title_tier_key","government_key","subject_immediate_liege_character_id","subject_is_direct_subject","authorized"));
return new OwnerEligibility(i(n,"owner_character_id",f), b(n,"owner_alive",f), b(n,"owner_is_ai",f), i(n,"primary_title_id",f), i(n,"primary_title_tier_raw",f), t(n,"primary_title_tier_key",f), t(n,"government_key",f), i(n,"subject_immediate_liege_character_id",f), b(n,"subject_is_direct_subject",f), b(n,"authorized",f));
}
private static Stage g12(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("state","key","active"));
return new Stage(i(n,"state",f), t(n,"key",f), b(n,"active",f));
}
private static Route g13(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("kind","visible_event_allowed","owner_is_ai","manager_eligible","direct_subject_eligible"));
return new Route(t(n,"kind",f), b(n,"visible_event_allowed",f), b(n,"owner_is_ai",f), b(n,"manager_eligible",f), b(n,"direct_subject_eligible",f));
}
private static ResultIdentity g14(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("case_serial","cycle_serial","grade","owner_character_id","state","subject_character_id"));
return new ResultIdentity(i(n,"case_serial",f), i(n,"cycle_serial",f), i(n,"grade",f), i(n,"owner_character_id",f), i(n,"state",f), i(n,"subject_character_id",f));
}
private static Notice g15(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("absolute_grade","cohort_n_frozen","kpi_frozen_q100000","rank_frozen"));
return new Notice(i(n,"absolute_grade",f), i(n,"cohort_n_frozen",f), i(n,"kpi_frozen_q100000",f), i(n,"rank_frozen",f));
}
private static Delivery g16(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("method","objection_recorded","settlement_posted_serial","appeal_open"));
return new Delivery(i(n,"method",f), b(n,"objection_recorded",f), i(n,"settlement_posted_serial",f), b(n,"appeal_open",f));
}
private static PipGate g17(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("owner_character_id","subject_character_id","cycle_serial","case_serial","threshold","negative_component_count","evidence_complete","status","result_case_serial","result_grade","absolute_grade","kpi_frozen_q100000","governance_q100000","capability_q100000","growth_q100000","superior_q100000","values_q100000","collaboration_q100000","jingcha_q100000","organization_q100000"));
return new PipGate(i(n,"owner_character_id",f), i(n,"subject_character_id",f), i(n,"cycle_serial",f), i(n,"case_serial",f), i(n,"threshold",f), i(n,"negative_component_count",f), b(n,"evidence_complete",f), i(n,"status",f), i(n,"result_case_serial",f), i(n,"result_grade",f), i(n,"absolute_grade",f), i(n,"kpi_frozen_q100000",f), i(n,"governance_q100000",f), i(n,"capability_q100000",f), i(n,"growth_q100000",f), i(n,"superior_q100000",f), i(n,"values_q100000",f), i(n,"collaboration_q100000",f), i(n,"jingcha_q100000",f), i(n,"organization_q100000",f));
}
private static PipPip g18(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("owner_character_id","subject_character_id","cycle_serial","case_serial","state","task_kind","task_controllable","policy_route"));
return new PipPip(i(n,"owner_character_id",f), i(n,"subject_character_id",f), i(n,"cycle_serial",f), i(n,"case_serial",f), i(n,"state",f), i(n,"task_kind",f), b(n,"task_controllable",f), i(n,"policy_route",f));
}
private static PipResponse g19(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("subject_response","response_case_serial","response_author_character_id","acknowledgement_receipt_serial","goal_revision_used","refusal_receipt_serial"));
return new PipResponse(i(n,"subject_response",f), i(n,"response_case_serial",f), i(n,"response_author_character_id",f), i(n,"acknowledgement_receipt_serial",f), b(n,"goal_revision_used",f), i(n,"refusal_receipt_serial",f));
}
private static PipSupport g20(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("capacity_reserved","owner_capacity_used","support_absent","hours","attention_units","mentor_character_id","budget_owner_character_id","treasury_budget_allocated","treasury_budget_spent","support_receipt_serial","released","withheld","atomic_shortfall"));
return new PipSupport(b(n,"capacity_reserved",f), i(n,"owner_capacity_used",f), b(n,"support_absent",f), i(n,"hours",f), i(n,"attention_units",f), i(n,"mentor_character_id",f), i(n,"budget_owner_character_id",f), i(n,"treasury_budget_allocated",f), i(n,"treasury_budget_spent",f), i(n,"support_receipt_serial",f), b(n,"released",f), b(n,"withheld",f), b(n,"atomic_shortfall",f));
}
private static PipBudgetLedger g21(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("result_case_serial","treasury_penalty_paid","personal_gold_penalty_paid","support_treasury_allocated","support_treasury_spent"));
return new PipBudgetLedger(i(n,"result_case_serial",f), i(n,"treasury_penalty_paid",f), i(n,"personal_gold_penalty_paid",f), i(n,"support_treasury_allocated",f), i(n,"support_treasury_spent",f));
}
private static PipD180Ticket g22(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("owner_character_id","subject_character_id","cycle_serial","case_serial","expected_state","due_date_raw"));
return new PipD180Ticket(i(n,"owner_character_id",f), i(n,"subject_character_id",f), i(n,"cycle_serial",f), i(n,"case_serial",f), i(n,"expected_state",f), i(n,"due_date_raw",f));
}
private static PipD365Ticket g23(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("owner_character_id","subject_character_id","cycle_serial","case_serial","expected_state","due_date_raw"));
return new PipD365Ticket(i(n,"owner_character_id",f), i(n,"subject_character_id",f), i(n,"cycle_serial",f), i(n,"case_serial",f), i(n,"expected_state",f), i(n,"due_date_raw",f));
}
private static PipMidpoint g24(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("receipt_serial","resource_delivery_valid","progress_status","progress_red_code","state"));
return new PipMidpoint(i(n,"receipt_serial",f), b(n,"resource_delivery_valid",f), i(n,"progress_status",f), i(n,"progress_red_code",f), i(n,"state",f));
}
private static PipOutcome g25(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("code","settlement_receipt_serial","result_cycle_serial","result_case_serial","result_grade","stability_days_observed","independent_review_status","independent_review_red_code","graduation_receipt_serial","failure_receipt_serial","no_support_liability"));
return new PipOutcome(i(n,"code",f), i(n,"settlement_receipt_serial",f), i(n,"result_cycle_serial",f), i(n,"result_case_serial",f), i(n,"result_grade",f), i(n,"stability_days_observed",f), i(n,"independent_review_status",f), i(n,"independent_review_red_code",f), i(n,"graduation_receipt_serial",f), i(n,"failure_receipt_serial",f), b(n,"no_support_liability",f));
}
private static PipNextCycleEvidence g26(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("status","owner_character_id","subject_character_id","source_cycle_serial","source_case_serial","due_cycle_serial","delta","consumed_cycle_serial","consumed_case_serial"));
return new PipNextCycleEvidence(i(n,"status",f), i(n,"owner_character_id",f), i(n,"subject_character_id",f), i(n,"source_cycle_serial",f), i(n,"source_case_serial",f), i(n,"due_cycle_serial",f), i(n,"delta",f), i(n,"consumed_cycle_serial",f), i(n,"consumed_case_serial",f));
}
private static Identity g27(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("owner_character_id","subject_character_id","cycle_serial","case_serial","revision"));
return new Identity(i(n,"owner_character_id",f), i(n,"subject_character_id",f), i(n,"cycle_serial",f), i(n,"case_serial",f), i(n,"revision",f));
}
private static ProjectIdentity g28(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("owner_character_id","subject_character_id","cycle_serial","case_serial"));
return new ProjectIdentity(i(n,"owner_character_id",f), i(n,"subject_character_id",f), i(n,"cycle_serial",f), i(n,"case_serial",f));
}
private static FrozenCase g29(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("identity","frozen"));
return new FrozenCase(g27(n.get("identity"),f), bool(n.get("frozen")));
}
private static PromotionChoice g30(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("identity","option_number","receipt_serial","active","consumed"));
return new PromotionChoice(g27(n.get("identity"),f), i(n,"option_number",f), i(n,"receipt_serial",f), b(n,"active",f), b(n,"consumed",f));
}
private static CompensationReceipt g31(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("identity","operation_id","option_number","receipt_serial","active","consumed","posted"));
return new CompensationReceipt(g27(n.get("identity"),f), i(n,"operation_id",f), i(n,"option_number",f), i(n,"receipt_serial",f), b(n,"active",f), b(n,"consumed",f), b(n,"posted",f));
}
private static PromotionCompensation g32(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("source_identity","result_identity","frozen_case","promotion_choice","compensation_receipt"));
return new PromotionCompensation(g27(n.get("source_identity"),f), g27(n.get("result_identity"),f), g29(n.get("frozen_case"),f), g30(n.get("promotion_choice"),f), g31(n.get("compensation_receipt"),f));
}
private static Af5Portfolio g33(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("domain","stage","completed_cycle","visible_pending","result_identity"));
return new Af5Portfolio(i(n,"domain",f), i(n,"stage",f), i(n,"completed_cycle",f), b(n,"visible_pending",f), g27(n.get("result_identity"),f));
}
private static Af5Case g34(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("identity","state","active","last_operation","last_route","repurchase_resolved","unit_conserved","result_case_serial"));
return new Af5Case(g27(n.get("identity"),f), i(n,"state",f), b(n,"active",f), i(n,"last_operation",f), i(n,"last_route",f), b(n,"repurchase_resolved",f), b(n,"unit_conserved",f), i(n,"result_case_serial",f));
}
private static Af5Receipt g35(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("identity","state","active","consumed","route"));
return new Af5Receipt(g27(n.get("identity"),f), i(n,"state",f), b(n,"active",f), b(n,"consumed",f), i(n,"route",f));
}
private static Af5 g36(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("portfolio","case","m299","m300"));
return new Af5(g33(n.get("portfolio"),f), g34(n.get("case"),f), g35(n.get("m299"),f), g35(n.get("m300"),f));
}
private static ProjectPortfolio g37(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("provider_observed","closed","cycle_serial","final_case_serial","final_conservation_ok","final_cycle_serial","final_owner_character_id","final_state","final_subject_character_id","pending_player_event"));
return new ProjectPortfolio(bool(n.get("provider_observed")), i(n,"closed",f), i(n,"cycle_serial",f), i(n,"final_case_serial",f), i(n,"final_conservation_ok",f), i(n,"final_cycle_serial",f), i(n,"final_owner_character_id",f), i(n,"final_state",f), i(n,"final_subject_character_id",f), i(n,"pending_player_event",f));
}
private static Contribution g38(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("identity","receipt_id","receipt_revision","value","provider_observed"));
return new Contribution(g28(n.get("identity"),f), i(n,"receipt_id",f), i(n,"receipt_revision",f), i(n,"value",f), bool(n.get("provider_observed")));
}
private static MetricsResult g39(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("identity","source_contribution_receipt_id","source_contribution_receipt_revision","metrics_revision","dictionary_key","provider_observed"));
return new MetricsResult(g28(n.get("identity"),f), i(n,"source_contribution_receipt_id",f), i(n,"source_contribution_receipt_revision",f), i(n,"metrics_revision",f), t(n,"dictionary_key",f), bool(n.get("provider_observed")));
}
private static ProjectsMetrics g40(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("source_identity","result_identity","contribution","metrics_result"));
return new ProjectsMetrics(g28(n.get("source_identity"),f), g28(n.get("result_identity"),f), g38(n.get("contribution"),f), g39(n.get("metrics_result"),f));
}
private static Probe g41(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("consequence_kind","cycle_serial","owner_character_id","probe_serial","result","source_kind","subject_character_id"));
return new Probe(i(n,"consequence_kind",f), i(n,"cycle_serial",f), i(n,"owner_character_id",f), i(n,"probe_serial",f), i(n,"result",f), i(n,"source_kind",f), i(n,"subject_character_id",f));
}
private static Resources g42(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("capital_control_q100000","manager_treasury_q100000","subject_personal_gold_q100000"));
return new Resources(i(n,"capital_control_q100000",f), i(n,"manager_treasury_q100000",f), i(n,"subject_personal_gold_q100000",f));
}
private static NotApplicable g43(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("applicable","cycle_serial","kpi_staged","owner_character_id","probe_serial","reason","receipt_serial","subject_character_id"));
return new NotApplicable(i(n,"applicable",f), i(n,"cycle_serial",f), i(n,"kpi_staged",f), i(n,"owner_character_id",f), i(n,"probe_serial",f), i(n,"reason",f), i(n,"receipt_serial",f), i(n,"subject_character_id",f));
}
private static Incident g44(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("applicable","case_serial","consequence_kind","cycle_serial","final_score","incident_serial","kpi_staged","owner_character_id","revision","source_kind","state","subject_character_id"));
return new Incident(i(n,"applicable",f), i(n,"case_serial",f), i(n,"consequence_kind",f), i(n,"cycle_serial",f), i(n,"final_score",f), i(n,"incident_serial",f), i(n,"kpi_staged",f), i(n,"owner_character_id",f), i(n,"revision",f), i(n,"source_kind",f), i(n,"state",f), i(n,"subject_character_id",f));
}
private static Kpi g45(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("disposition","case_serial","consequence_kind","consumed","consumed_case_serial","consumed_cycle","consumed_due_cycle","consumed_incident_serial","consumed_origin_cycle","consumed_owner_character_id","consumed_score","consumed_subject_character_id","due_cycle","due_offset","incident_serial","origin_cycle","owner_character_id","pending","receipt_serial","score","source_kind","state","subject_character_id"));
return new Kpi(enumeration(n.get("disposition"),KpiDisposition.class), i(n,"case_serial",f), i(n,"consequence_kind",f), i(n,"consumed",f), i(n,"consumed_case_serial",f), i(n,"consumed_cycle",f), i(n,"consumed_due_cycle",f), i(n,"consumed_incident_serial",f), i(n,"consumed_origin_cycle",f), i(n,"consumed_owner_character_id",f), i(n,"consumed_score",f), i(n,"consumed_subject_character_id",f), i(n,"due_cycle",f), i(n,"due_offset",f), i(n,"incident_serial",f), i(n,"origin_cycle",f), i(n,"owner_character_id",f), i(n,"pending",f), i(n,"receipt_serial",f), i(n,"score",f), i(n,"source_kind",f), i(n,"state",f), i(n,"subject_character_id",f));
}
private static Terminal g46(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("kind","na","incident"));
return new Terminal(enumeration(n.get("kind"),TerminalKind.class), n.get("na").isNull()?Optional.empty():Optional.of(g43(n.get("na"),f)), n.get("incident").isNull()?Optional.empty():Optional.of(g44(n.get("incident"),f)));
}
private static Widget g47(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("stable_identity","runtime_name","instance_pointer","vtable_pointer","exists","local_visible","effective_visible","enabled","focused","modal_blocking","screen_x","screen_y","screen_width","screen_height","scroll_min","scroll_max","scroll_value"));
return new Widget(text(n.get("stable_identity")), text(n.get("runtime_name")), t(n,"instance_pointer",f), t(n,"vtable_pointer",f), b(n,"exists",f), b(n,"local_visible",f), b(n,"effective_visible",f), b(n,"enabled",f), b(n,"focused",f), b(n,"modal_blocking",f), i(n,"screen_x",f), i(n,"screen_y",f), i(n,"screen_width",f), i(n,"screen_height",f), i(n,"scroll_min",f), i(n,"scroll_max",f), i(n,"scroll_value",f));
}
private static ManagedAcl g48(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("surface_available","current_player_can_assess_others","owner_character_id","first_subject_character_id"));
return new ManagedAcl(bool(n.get("surface_available")), bool(n.get("current_player_can_assess_others")), i(n,"owner_character_id",f), i(n,"first_subject_character_id",f));
}
private static ReceivedAcl g49(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("surface_available","current_player_is_subject","b1_case_serial","cycle_serial","disclosure_acl_mode","disclosure_blackbox_risk","disclosure_evaluator_identity_mode","disclosure_policy_available","disclosure_policy_id","disclosure_self_mode","disclosure_team_mode","first_row_character_id","owner_character_id","result_case_serial","subject_character_id"));
return new ReceivedAcl(bool(n.get("surface_available")), bool(n.get("current_player_is_subject")), i(n,"b1_case_serial",f), i(n,"cycle_serial",f), i(n,"disclosure_acl_mode",f), i(n,"disclosure_blackbox_risk",f), i(n,"disclosure_evaluator_identity_mode",f), i(n,"disclosure_policy_available",f), i(n,"disclosure_policy_id",f), i(n,"disclosure_self_mode",f), i(n,"disclosure_team_mode",f), i(n,"first_row_character_id",f), i(n,"owner_character_id",f), i(n,"result_case_serial",f), i(n,"subject_character_id",f));
}
private static Acl g50(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("managed","received_self"));
return new Acl(g48(n.get("managed"),f), g49(n.get("received_self"),f));
}
private static ReadOnlyActions g51(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("activate","close","reopen"));
return new ReadOnlyActions(b(n,"activate",f), b(n,"close",f), b(n,"reopen",f));
}
private static ProgressWidget g52(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("stable_identity","runtime_name","instance_pointer","vtable_pointer","exists","effective_visible","enabled"));
return new ProgressWidget(text(n.get("stable_identity")), text(n.get("runtime_name")), t(n,"instance_pointer",f), t(n,"vtable_pointer",f), b(n,"exists",f), b(n,"effective_visible",f), b(n,"enabled",f));
}
private static B1Readiness g53(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("closure_ready","cycle_identity_ready","manager_binding_ready","pending_ready","processing_ready","quota_ready","ready","roster_ready","same_frame_ready"));
return new B1Readiness(bool(n.get("closure_ready")), bool(n.get("cycle_identity_ready")), bool(n.get("manager_binding_ready")), bool(n.get("pending_ready")), bool(n.get("processing_ready")), bool(n.get("quota_ready")), bool(n.get("ready")), bool(n.get("roster_ready")), bool(n.get("same_frame_ready")));
}
private static CaseReadiness g54(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("case_identity_ready","deadline_due_date_ready","deadline_identity_ready","operation_ready","player_binding_ready","policy_ready","ready","receipt_ready","same_frame_ready"));
return new CaseReadiness(bool(n.get("case_identity_ready")), bool(n.get("deadline_due_date_ready")), bool(n.get("deadline_identity_ready")), bool(n.get("operation_ready")), bool(n.get("player_binding_ready")), bool(n.get("policy_ready")), bool(n.get("ready")), bool(n.get("receipt_ready")), bool(n.get("same_frame_ready")));
}
private static AiOwnedReadiness g55(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("case_identity_ready","owner_eligibility_ready","ready","receipt_ready","route_ready","same_frame_ready","stage_ready"));
return new AiOwnedReadiness(bool(n.get("case_identity_ready")), bool(n.get("owner_eligibility_ready")), bool(n.get("ready")), bool(n.get("receipt_ready")), bool(n.get("route_ready")), bool(n.get("same_frame_ready")), bool(n.get("stage_ready")));
}
private static ResultReadiness g56(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("case_identity_ready","delivery_state_ready","notice_facts_ready","owner_binding_ready","player_subject_binding_ready","ready","same_frame_ready"));
return new ResultReadiness(bool(n.get("case_identity_ready")), bool(n.get("delivery_state_ready")), bool(n.get("notice_facts_ready")), bool(n.get("owner_binding_ready")), bool(n.get("player_subject_binding_ready")), bool(n.get("ready")), bool(n.get("same_frame_ready")));
}
private static PipReadiness g57(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("budget_ledger_ready","d180_ticket_observation_ready","d365_ticket_observation_ready","gate_evidence_ready","gate_ready","midpoint_ready","modifier_observation_ready","next_cycle_evidence_ready","outcome_ready","owner_binding_ready","pip_identity_ready","player_subject_binding_ready","ready","response_ready","same_frame_ready","support_ready"));
return new PipReadiness(bool(n.get("budget_ledger_ready")), bool(n.get("d180_ticket_observation_ready")), bool(n.get("d365_ticket_observation_ready")), bool(n.get("gate_evidence_ready")), bool(n.get("gate_ready")), bool(n.get("midpoint_ready")), bool(n.get("modifier_observation_ready")), bool(n.get("next_cycle_evidence_ready")), bool(n.get("outcome_ready")), bool(n.get("owner_binding_ready")), bool(n.get("pip_identity_ready")), bool(n.get("player_subject_binding_ready")), bool(n.get("ready")), bool(n.get("response_ready")), bool(n.get("same_frame_ready")), bool(n.get("support_ready")));
}
private static PromotionReadiness g58(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("compensation_receipt_posted","frozen_case_identity_ready","player_owner_binding_ready","portfolio_subject_binding_ready","promotion_choice_receipt_ready","ready","receipt_serials_ready","result_identity_ready","revision_binding_ready","same_case_identity_ready","same_frame_ready","source_identity_ready"));
return new PromotionReadiness(bool(n.get("compensation_receipt_posted")), bool(n.get("frozen_case_identity_ready")), bool(n.get("player_owner_binding_ready")), bool(n.get("portfolio_subject_binding_ready")), bool(n.get("promotion_choice_receipt_ready")), bool(n.get("ready")), bool(n.get("receipt_serials_ready")), bool(n.get("result_identity_ready")), bool(n.get("revision_binding_ready")), bool(n.get("same_case_identity_ready")), bool(n.get("same_frame_ready")), bool(n.get("source_identity_ready")));
}
private static Af5Readiness g59(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("player_owner_binding_ready","portfolio_subject_binding_ready","ready","same_case_identity_ready","same_frame_ready"));
return new Af5Readiness(bool(n.get("player_owner_binding_ready")), bool(n.get("portfolio_subject_binding_ready")), bool(n.get("ready")), bool(n.get("same_case_identity_ready")), bool(n.get("same_frame_ready")));
}
private static ProjectsReadiness g60(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("contribution_ready","metrics_ready","owner_binding_ready","player_subject_binding_ready","portfolio_closed","portfolio_observed","ready","receipt_lineage_ready","result_identity_ready","result_operation_committed","same_frame_ready","same_project_case_identity","source_identity_ready"));
return new ProjectsReadiness(bool(n.get("contribution_ready")), bool(n.get("metrics_ready")), bool(n.get("owner_binding_ready")), bool(n.get("player_subject_binding_ready")), bool(n.get("portfolio_closed")), bool(n.get("portfolio_observed")), bool(n.get("ready")), bool(n.get("receipt_lineage_ready")), bool(n.get("result_identity_ready")), bool(n.get("result_operation_committed")), bool(n.get("same_frame_ready")), bool(n.get("same_project_case_identity")), bool(n.get("source_identity_ready")));
}
private static IncidentReadiness g61(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("kpi_state_ready","owner_binding_ready","player_subject_binding_ready","probe_ready","profile_binding_ready","ready","resource_snapshot_ready","same_frame_ready","terminal_ready"));
return new IncidentReadiness(bool(n.get("kpi_state_ready")), bool(n.get("owner_binding_ready")), bool(n.get("player_subject_binding_ready")), bool(n.get("probe_ready")), bool(n.get("profile_binding_ready")), bool(n.get("ready")), bool(n.get("resource_snapshot_ready")), bool(n.get("same_frame_ready")), bool(n.get("terminal_ready")));
}
private static ScoreboardReadiness g62(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("acl_ready","entry_window_state_ready","full_widget_gate_ready","gui_root_ready","player_binding_ready","production_live_ready","same_frame_ready","state_acl_query_ready"));
return new ScoreboardReadiness(bool(n.get("acl_ready")), bool(n.get("entry_window_state_ready")), bool(n.get("full_widget_gate_ready")), bool(n.get("gui_root_ready")), bool(n.get("player_binding_ready")), bool(n.get("production_live_ready")), bool(n.get("same_frame_ready")), bool(n.get("state_acl_query_ready")));
}
private static ProgressReadiness g63(JsonNode raw,Family f) {
ObjectNode n=exact(raw,Set.of("player_binding_ready","gui_root_ready","exact_widget_set_ready","same_frame_ready","query_ready","production_live_ready"));
return new ProgressReadiness(bool(n.get("player_binding_ready")), bool(n.get("gui_root_ready")), bool(n.get("exact_widget_set_ready")), bool(n.get("same_frame_ready")), bool(n.get("query_ready")), bool(n.get("production_live_ready")));
}
private static <T> List<T> list(JsonNode node,java.util.function.Function<JsonNode,T> decode) {
check(node!=null && node.isArray(),"array required"); List<T> values=new ArrayList<>();
for(JsonNode value:node) values.add(decode.apply(value)); return List.copyOf(values);
}
public static B1Frame decodeB1Frame(PlanningReadReceipt receipt) {
Family f=Family.B1; ObjectNode n=envelope(receipt,f); Header h=header(n,f,receipt);
B1Frame result=new B1Frame(h,character(n.get("manager_character_id")), g5(n.get("cycle"),f), g6(n.get("roster"),f), g7(n.get("processing"),f), g8(n.get("quota"),f), g9(n.get("closure"),f), g10(n.get("pending"),f), g53(n.get("readiness"),f));
ChinaCasesSemantics.verify(result,receipt); return result;
}
public static CaseFrame decodeCaseFrame(PlanningReadReceipt receipt) {
Family f=Family.CASE; ObjectNode n=envelope(receipt,f); Header h=header(n,f,receipt);
CaseFrame result=new CaseFrame(h,character(n.get("subject_character_id")), n.get("requested_owner_character_id").isNull()?Optional.empty():Optional.of(character(n.get("requested_owner_character_id"))), g0(n.get("case"),f), g1(n.get("policy"),f), g2(n.get("operation"),f), g3(n.get("receipt"),f), g4(n.get("deadline"),f), g54(n.get("readiness"),f));
ChinaCasesSemantics.verify(result,receipt); return result;
}
public static AiOwnedFrame decodeAiOwnedFrame(PlanningReadReceipt receipt) {
Family f=Family.AIOWNED; ObjectNode n=envelope(receipt,f); Header h=header(n,f,receipt);
AiOwnedFrame result=new AiOwnedFrame(h,character(n.get("subject_character_id")), character(n.get("requested_owner_character_id")), g0(n.get("case"),f), g11(n.get("owner_eligibility"),f), g12(n.get("stage"),f), g13(n.get("route"),f), g1(n.get("policy"),f), g2(n.get("operation"),f), g3(n.get("receipt"),f), g55(n.get("readiness"),f));
ChinaCasesSemantics.verify(result,receipt); return result;
}
public static ResultFrame decodeResultFrame(PlanningReadReceipt receipt) {
Family f=Family.RESULT; ObjectNode n=envelope(receipt,f); Header h=header(n,f,receipt);
ResultFrame result=new ResultFrame(h,character(n.get("subject_character_id")), character(n.get("requested_owner_character_id")), g14(n.get("case"),f), g15(n.get("notice"),f), g16(n.get("delivery"),f), g56(n.get("readiness"),f));
ChinaCasesSemantics.verify(result,receipt); return result;
}
public static PipFrame decodePipFrame(PlanningReadReceipt receipt) {
Family f=Family.PIP; ObjectNode n=envelope(receipt,f); Header h=header(n,f,receipt);
PipFrame result=new PipFrame(h,character(n.get("subject_character_id")), character(n.get("requested_owner_character_id")), g17(n.get("gate"),f), g18(n.get("pip"),f), g19(n.get("response"),f), g20(n.get("support"),f), g21(n.get("budget_ledger"),f), g22(n.get("d180_ticket"),f), g23(n.get("d365_ticket"),f), g24(n.get("midpoint"),f), g25(n.get("outcome"),f), g26(n.get("next_cycle_evidence"),f), b(n,"pip_modifier_present",f), g57(n.get("readiness"),f));
ChinaCasesSemantics.verify(result,receipt); return result;
}
public static PromotionFrame decodePromotionFrame(PlanningReadReceipt receipt) {
Family f=Family.PROMOTION; ObjectNode n=envelope(receipt,f); Header h=header(n,f,receipt);
PromotionFrame result=new PromotionFrame(h,character(n.get("subject_character_id")), g32(n.get("promotion_compensation"),f), g58(n.get("readiness"),f));
ChinaCasesSemantics.verify(result,receipt); return result;
}
public static Af5Frame decodeAf5Frame(PlanningReadReceipt receipt) {
Family f=Family.AF5; ObjectNode n=envelope(receipt,f); Header h=header(n,f,receipt);
Af5Frame result=new Af5Frame(h,character(n.get("subject_character_id")), g36(n.get("af5"),f), bool(n.get("terminal")), g59(n.get("readiness"),f));
ChinaCasesSemantics.verify(result,receipt); return result;
}
public static ProjectsFrame decodeProjectsFrame(PlanningReadReceipt receipt) {
Family f=Family.PROJECTS; ObjectNode n=envelope(receipt,f); Header h=header(n,f,receipt);
ProjectsFrame result=new ProjectsFrame(h,character(n.get("requested_owner_character_id")), character(n.get("requested_subject_character_id")), enumeration(n.get("checkpoint_state"),CheckpointState.class), g37(n.get("credit_project_portfolio"),f), g28(n.get("source_identity"),f), g28(n.get("result_identity"),f), g40(n.get("projects_metrics"),f), g60(n.get("readiness"),f));
ChinaCasesSemantics.verify(result,receipt); return result;
}
public static IncidentFrame decodeIncidentFrame(PlanningReadReceipt receipt) {
Family f=Family.INCIDENT; ObjectNode n=envelope(receipt,f); Header h=header(n,f,receipt);
IncidentFrame result=new IncidentFrame(h,character(n.get("subject_character_id")), character(n.get("requested_owner_character_id")), enumeration(n.get("profile"),IncidentProfile.class), g41(n.get("probe"),f), g42(n.get("resources"),f), g46(n.get("terminal"),f), g45(n.get("kpi"),f), g61(n.get("readiness"),f));
ChinaCasesSemantics.verify(result,receipt); return result;
}
public static ScoreboardFrame decodeScoreboardFrame(PlanningReadReceipt receipt) {
Family f=Family.SCOREBOARD; ObjectNode n=envelope(receipt,f); Header h=header(n,f,receipt);
ScoreboardFrame result=new ScoreboardFrame(h,text(n.get("tree_fingerprint_v1")), text(n.get("semantic_fingerprint_v1")), text(n.get("provider_session_id")), uint64(n.get("observation_sequence"),false), uint64(n.get("observed_state_revision"),false), list(n.get("widgets"),item->g47(item,f)), g50(n.get("acl"),f), g51(n.get("actions"),f), g62(n.get("readiness"),f));
ChinaCasesSemantics.verify(result,receipt); return result;
}
public static ProgressFrame decodeProgressFrame(PlanningReadReceipt receipt) {
Family f=Family.PROGRESS; ObjectNode n=envelope(receipt,f); Header h=header(n,f,receipt);
ProgressFrame result=new ProgressFrame(h,list(n.get("widgets"),item->g52(item,f)), g63(n.get("readiness"),f));
ChinaCasesSemantics.verify(result,receipt); return result;
}
}

