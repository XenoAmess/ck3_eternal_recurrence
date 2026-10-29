package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent.Route;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus;

/** Pre-Managed definitions for the four original private sends. Every real submission still requires actual source qualification. */
public final class FamilyNativePrivatePermissions {
    private FamilyNativePrivatePermissions() { }
    public record Sources(ExactRef firstHeirNative,ExactRef fulfillmentNative,ExactRef childMatrilinealNative,ExactRef childDefaultNative) {
        public Sources {
            for(var source:List.of(firstHeirNative,fulfillmentNative,childMatrilinealNative,childDefaultNative))
                StrictJson.require(Objects.requireNonNull(source).bytes()>0,"actual original private native producer source required");
        }
        public ExactRef forRoute(Route route) {
            return switch(Objects.requireNonNull(route)) {
                case FIRST_HEIR -> firstHeirNative;
                case FULFILL_BETROTHAL -> fulfillmentNative;
                case CHILD_MATRILINEAL -> childMatrilinealNative;
                case CHILD_DEFAULT -> childDefaultNative;
            };
        }
    }
    /** This constructor does not open a Game, create a context, or qualify its own source. */
    public static List<NativePrivateActionPermission> privateMarriages(Sources actualNativeSources,
            NativePrivateActionPermission.QualificationVerifier actualQualification) {
        Objects.requireNonNull(actualNativeSources);Objects.requireNonNull(actualQualification);
        return java.util.Arrays.stream(Route.values()).map(route -> new NativePrivateActionPermission(
                new OperationKey(route.step()),permissionKey(route),actualNativeSources.forRoute(route),
                request -> validate(route,request),actualQualification)).toList();
    }
    /** Separate original focus primitive; this permission alone supplies no action preparation or effect reader. */
    public static NativePrivateActionPermission childFocus(ExactRef actualNativeSource,
            NativePrivateActionPermission.QualificationVerifier actualQualification) {
        Objects.requireNonNull(actualQualification);Objects.requireNonNull(actualNativeSource);
        StrictJson.require(actualNativeSource.bytes()>0,"actual native child focus producer required");
        return new NativePrivateActionPermission(new OperationKey(ChildEducationFocus.SUBMIT_STEP),ChildEducationFocus.PERMISSION,
                actualNativeSource,FamilyNativePrivatePermissions::validateChildFocus,actualQualification);
    }
    public static void validateChildFocus(NativeRequest request) {
        Objects.requireNonNull(request);
        StrictJson.require(request.step().equals(ChildEducationFocus.SUBMIT_STEP)&&request.requiredCapability().isEmpty(),"exact original private focus primitive required");
        JsonNode row=StrictJson.object(StrictJson.parse(request.additionalFields().bytes()),Set.of("expected_snapshot_id","expected_date_raw",
                "expected_player_character_id","episode_run_id","child_full_id","target_key","action_request_id"));
        String snapshot=StrictJson.text(row.get("expected_snapshot_id"));
        StrictJson.require(snapshot.matches("native:[1-9][0-9]{0,19}"),"canonical original native snapshot ID required");
        StrictJson.require(new BigInteger(snapshot.substring(7)).compareTo(StrictJson.UINT64_MAX)<=0,"focus snapshot revision exceeds original native domain");
        StrictJson.integer(row.get("expected_date_raw"),0,Integer.MAX_VALUE);
        StrictJson.integer(row.get("expected_player_character_id"),1,0xFFFF_FFFEL);StrictJson.integer(row.get("child_full_id"),1,0xFFFF_FFFEL);
        String episode=StrictJson.text(row.get("episode_run_id")),action=StrictJson.text(row.get("action_request_id"));
        StrictJson.require(episode.length()<=128&&action.length()<=128,"original native focus identity bounds required");
        String selected=StrictJson.text(row.get("target_key"));
        StrictJson.require(java.util.Arrays.stream(ChildEducationFocus.Key.values()).anyMatch(key->key.wire().equals(selected)),"exact original education focus key required");
        // The actual native handler additionally compares action_request_id to
        // its envelope request_id and all frame fields to its published snapshot.
    }
    public static String permissionKey(Route route) {
        return switch(Objects.requireNonNull(route)) {
            case FIRST_HEIR -> "source_qualified_observed_first_heir_marriage_action_v1";
            case FULFILL_BETROTHAL -> "source_qualified_current_first_heir_betrothal_fulfillment_action_v1";
            case CHILD_MATRILINEAL -> "allow_private_player_child_matrilineal_action";
            case CHILD_DEFAULT -> "allow_private_player_child_default_action";
        };
    }
    /** Closed fields match the actual original bridge route; envelope expected_revision remains transport-owned. */
    public static void validate(Route route,NativeRequest request) {
        Objects.requireNonNull(route);Objects.requireNonNull(request);
        StrictJson.require(route.step().equals(request.step())&&request.requiredCapability().isEmpty(),
                "private family primitive differs from its fixed source-owned operation");
        Set<String> fields=switch(route) {
            case FIRST_HEIR -> Set.of("query_sequence","candidate_character_id");
            case FULFILL_BETROTHAL -> Set.of("heir_character_id","candidate_character_id","recipient_character_id");
            case CHILD_MATRILINEAL,CHILD_DEFAULT -> Set.of("legality_query_sequence","subject_character_id","candidate_character_id");
        };
        JsonNode row=StrictJson.object(StrictJson.parse(request.additionalFields().bytes()),fields);
        long candidate=id(row,"candidate_character_id");
        switch(route) {
            case FIRST_HEIR -> sequence(row,"query_sequence");
            case FULFILL_BETROTHAL -> {
                StrictJson.require(id(row,"heir_character_id")!=candidate,"original fixed betrothal pair must be distinct");id(row,"recipient_character_id");
            }
            case CHILD_MATRILINEAL,CHILD_DEFAULT -> {
                sequence(row,"legality_query_sequence");StrictJson.require(id(row,"subject_character_id")!=candidate,"original child proposal pair must be distinct");
            }
        }
    }
    private static long id(JsonNode row,String name){return StrictJson.integer(row.get(name),1,Integer.MAX_VALUE);}
    private static void sequence(JsonNode row,String name){StrictJson.integer(row.get(name),BigInteger.ONE,StrictJson.UINT64_MAX);}
}
