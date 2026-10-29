package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent.Route;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class FamilyNativePrivatePermissionsTest {
    @Test void preManagedDefinitionsAreFourFixedSourcesAndNeverRunQualification() {
        var sources=new FamilyNativePrivatePermissions.Sources(ref(1),ref(2),ref(3),ref(4));
        var actual=FamilyNativePrivatePermissions.privateMarriages(sources,(config,hello,guard,request)->{
            throw new AssertionError("pre-Managed definitions must not invoke an actual submission/source verifier");
        });
        assertEquals(4,actual.size());assertEquals(4,actual.stream().map(p->p.operation().value()).distinct().count());
        for(var permission:actual) {
            Route route=java.util.Arrays.stream(Route.values()).filter(r->r.step().equals(permission.operation().value())).findFirst().orElseThrow();
            assertEquals(sources.forRoute(route),permission.originalProducerSource());
            assertEquals(FamilyNativePrivatePermissions.permissionKey(route),permission.permissionKey());
        }
        assertThrows(NullPointerException.class,()->FamilyNativePrivatePermissions.privateMarriages(sources,null));
    }
    @Test void allFourOriginalNativePayloadsValidateWithoutWideningTheirActionRange() {
        for(var route:Route.values())assertDoesNotThrow(()->FamilyNativePrivatePermissions.validate(route,request(route,fields(route))));
        var maximum=fields(Route.FIRST_HEIR).put("query_sequence",StrictJson.UINT64_MAX).put("candidate_character_id",Integer.MAX_VALUE);
        assertDoesNotThrow(()->FamilyNativePrivatePermissions.validate(Route.FIRST_HEIR,request(Route.FIRST_HEIR,maximum)));
        var highBit=fields(Route.FIRST_HEIR).put("candidate_character_id",BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE));
        reject(Route.FIRST_HEIR,highBit);
    }
    @Test void closedFieldsRejectMissingNullFloatBooleanAndUnknownValues() {
        for(var route:Route.values()) {
            var absent=fields(route);absent.remove("candidate_character_id");reject(route,absent);
            reject(route,fields(route).putNull("candidate_character_id"));
            reject(route,fields(route).put("candidate_character_id",true));
            reject(route,fields(route).put("candidate_character_id",202.0));
            reject(route,fields(route).put("candidate_character_id",0));
            reject(route,fields(route).put("unexpected_native_flag",true));
        }
        for(var invalid:List.of(StrictJson.object().booleanNode(true),StrictJson.object().numberNode(7.0),
                StrictJson.object().numberNode(BigInteger.ZERO),StrictJson.object().numberNode(StrictJson.UINT64_MAX.add(BigInteger.ONE)))) {
            var first=fields(Route.FIRST_HEIR);first.set("query_sequence",invalid);reject(Route.FIRST_HEIR,first);
            var child=fields(Route.CHILD_DEFAULT);child.set("legality_query_sequence",invalid);reject(Route.CHILD_DEFAULT,child);
        }
    }
    @Test void onePrivateRouteCannotBorrowAnOperationCapabilityOrIdenticalPair() {
        var fields=fields(Route.FIRST_HEIR);
        assertThrows(IllegalArgumentException.class,()->FamilyNativePrivatePermissions.validate(Route.CHILD_DEFAULT,request(Route.FIRST_HEIR,fields)));
        var advertised=new NativeRequest(Route.FIRST_HEIR.step(),Optional.of("invented.public.capability"),raw(fields));
        assertThrows(IllegalArgumentException.class,()->FamilyNativePrivatePermissions.validate(Route.FIRST_HEIR,advertised));
        reject(Route.FULFILL_BETROTHAL,fields(Route.FULFILL_BETROTHAL).put("heir_character_id",202));
        reject(Route.CHILD_DEFAULT,fields(Route.CHILD_DEFAULT).put("subject_character_id",202));
    }
    @Test void focusPermissionRetainsItsSeparateNativeFrameAndActionIdentityFields() {
        var fields=StrictJson.object().put("expected_snapshot_id","native:18446744073709551615").put("expected_date_raw",53146848)
                .put("expected_player_character_id",0xFE000001L).put("episode_run_id","synthetic-episode")
                .put("child_full_id",0xFD000002L).put("target_key","education_martial").put("action_request_id","original-attempt-1");
        var request=new NativeRequest("private-select-child-education-focus-v1",Optional.empty(),raw(fields));
        assertDoesNotThrow(()->FamilyNativePrivatePermissions.validateChildFocus(request));
        var definition=FamilyNativePrivatePermissions.childFocus(ref(5),(config,hello,guard,actual)->{
            throw new AssertionError("definition must not invent submission qualification");
        });
        assertEquals(request.step(),definition.operation().value());assertEquals("allow_private_lifestyle_formal_trial",definition.permissionKey());
        for(String snapshot:List.of("native:0","native:01","native:18446744073709551616","native:7.0")) {
            var invalid=fields.deepCopy().put("expected_snapshot_id",snapshot);
            assertThrows(IllegalArgumentException.class,()->FamilyNativePrivatePermissions.validateChildFocus(new NativeRequest(request.step(),Optional.empty(),raw(invalid))));
        }
        var booleanId=fields.deepCopy().put("child_full_id",true);
        assertThrows(IllegalArgumentException.class,()->FamilyNativePrivatePermissions.validateChildFocus(new NativeRequest(request.step(),Optional.empty(),raw(booleanId))));
        var wrongKey=fields.deepCopy().put("target_key","martial");
        assertThrows(IllegalArgumentException.class,()->FamilyNativePrivatePermissions.validateChildFocus(new NativeRequest(request.step(),Optional.empty(),raw(wrongKey))));
    }
    private static ObjectNode fields(Route route) {
        return switch(route) {
            case FIRST_HEIR -> StrictJson.object().put("query_sequence",7).put("candidate_character_id",202);
            case FULFILL_BETROTHAL -> StrictJson.object().put("heir_character_id",303).put("candidate_character_id",202).put("recipient_character_id",404);
            case CHILD_MATRILINEAL,CHILD_DEFAULT -> StrictJson.object().put("legality_query_sequence",7).put("subject_character_id",303).put("candidate_character_id",202);
        };
    }
    private static NativeRequest request(Route route,ObjectNode fields){return new NativeRequest(route.step(),Optional.empty(),raw(fields));}
    private static RawJson raw(ObjectNode fields){return new RawJson(StrictJson.canonical(fields));}
    private static void reject(Route route,ObjectNode fields){assertThrows(IllegalArgumentException.class,()->FamilyNativePrivatePermissions.validate(route,request(route,fields)));}
    private static ExactRef ref(int digit){return new ExactRef("synthetic/native-producer-"+digit,1,Integer.toHexString(digit).repeat(64));}
}
