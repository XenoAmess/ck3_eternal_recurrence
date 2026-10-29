package org.xar.ck3.control.nativebridge.capabilities.army;

import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import static org.junit.jupiter.api.Assertions.*;

final class ContactScopePublicCodecTest {
    @Test void exactPublicRevisionAndOptionalBranchesRoundtripWithoutChangingInt32Ids() {
        var projected=ContactScopePublicCodec.projected(arguments("{\"subject_army_id\":0,\"target_province_id\":31,\"incoming_entry_province_id\":30,\"expected_revision\":\"18446744073709551615\"}"));
        assertEquals(0,projected.query().subjectArmyId());assertEquals("18446744073709551615",projected.expectedRevision().decimal());
        assertEquals(projected,ContactScopePublicCodec.projected(PublicBindings.present(ContactScopePublicCodec.encode(projected))));
        for(String suffix:List.of("",",\"expected_revision\":null",",\"expected_revision\":\"0\"",",\"expected_revision\":\"9007199254740993\"")) {
            var actual=ContactScopePublicCodec.actual(arguments("{\"subject_army_id\":0,\"target_province_id\":31"+suffix+"}"));
            assertEquals(actual,ContactScopePublicCodec.actual(PublicBindings.present(ContactScopePublicCodec.encode(actual))));
            if(suffix.isEmpty())assertInstanceOf(ArmyTypes.Missing.class,actual.expectedRevision());
            else if(suffix.contains("null"))assertInstanceOf(ArmyTypes.NullValue.class,actual.expectedRevision());
            else assertInstanceOf(ArmyTypes.Present.class,actual.expectedRevision());
        }
    }
    @Test void wrongTokenDomainsMissingAndInventedFieldsDoNotReachAReadFamily() {
        String prefix="{\"subject_army_id\":0,\"target_province_id\":31,\"incoming_entry_province_id\":30";
        for(String token:List.of("null","true","1","1.0","\"01\"","\"+1\"","\"-1\"","\"18446744073709551616\""))
            assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.projected(arguments(prefix+",\"expected_revision\":"+token+"}")));
        assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.projected(arguments(prefix+"}")));
        for(String id:List.of("true","0.0","\"0\"","-1","2147483648"))
            assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.actual(arguments("{\"subject_army_id\":"+id+",\"target_province_id\":31}")));
        assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.actual(arguments("{\"subject_army_id\":0,\"target_province_id\":31,\"incoming_entry_province_id\":30}")));
        assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.projected(arguments("{\"subject_army_id\":0,\"target_province_id\":31,\"incoming_entry_province_id\":31,\"expected_revision\":\"0\"}")));
        assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.actual(new PublicBindings.Missing()));
        assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.actual(new PublicBindings.Null()));
        assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.actual(arguments("{\"subject_army_id\":0,\"subject_army_id\":1,\"target_province_id\":31}")));
        assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.actual(arguments("{\"subject_army_id\":0,\"target_province_id\":31} false")));
        assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.actual(PublicBindings.present(new RawJson(new byte[]{'{','"',(byte)0xc3,'"',':','0','}'}))));
    }
    private static PublicBindings.Arguments arguments(String json){return PublicBindings.present(new RawJson(json.getBytes(StandardCharsets.UTF_8)));}
}
