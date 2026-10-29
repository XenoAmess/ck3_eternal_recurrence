package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;

/** Material and protocol roles use the same strict token visitor with separate declared numeric bounds. */
class RawJsonFullMaterialBoundaryTest {
    private static byte[] bytes(String text){return text.getBytes(StandardCharsets.UTF_8);}
    @Test void largeMaterialRetainsTokensButCannotEnterActualNativeRequestProducer(){
        byte[] original=bytes("{\"contract_progress\":"+"9".repeat(70000)+",\"opaque\":[-0.0,1.0,1e999]}");
        RawJson material=RawJson.fullMaterial(original);assertArrayEquals(original,material.bytes());
        assertEquals(Set.of("contract_progress","opaque"),material.objectFieldNames());
        assertThrows(IllegalArgumentException.class,()->new RawJson(original));
        assertThrows(IllegalArgumentException.class,material::requireProtocolBound);
        assertThrows(IllegalArgumentException.class,()->new NativeRequest("query-army-strengths-v1",Optional.empty(),material,List.of()));
    }
    @Test void ordinaryNativeRequestStillAcceptsItsOriginalBoundedShapeAndRejectsReservedFields(){
        RawJson material=RawJson.fullMaterial(bytes("{\"integer\":17,\"opaque\":[-0.0,1.0]}"));
        assertDoesNotThrow(material::requireProtocolBound);
        NativeRequest request=new NativeRequest("query-army-strengths-v1",Optional.empty(),material,List.of());
        assertArrayEquals(material.bytes(),request.additionalFields().bytes());
        RawJson reserved=RawJson.fullMaterial(bytes("{\"step\":\"other\"}"));
        assertThrows(IllegalArgumentException.class,()->new NativeRequest("query-army-strengths-v1",Optional.empty(),reserved,List.of()));
    }
    @Test void completeMaterialStillRejectsInvalidUtf8DuplicatesTrailingAndNonJsonNumbers(){
        for(String invalid:List.of("{\"x\":1,\"x\":2}","{}[]","{\"x\":NaN}","{\"x\":Infinity}","{\"x\":01}","{\"x\":true"))
            assertThrows(IllegalArgumentException.class,()->RawJson.fullMaterial(bytes(invalid)));
        assertThrows(IllegalArgumentException.class,()->RawJson.fullMaterial(new byte[]{(byte)0xc3,0x28}));
        assertThrows(IllegalArgumentException.class,()->RawJson.fullMaterial(bytes("\"\\ud800\"")));
        assertThrows(IllegalArgumentException.class,()->RawJson.fullMaterial(new byte[0]));
    }
}
