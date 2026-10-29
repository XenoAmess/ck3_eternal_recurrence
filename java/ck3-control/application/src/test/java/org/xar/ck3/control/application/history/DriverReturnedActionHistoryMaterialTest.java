package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import static org.xar.ck3.control.application.history.DriverReturnedActionHistoryMaterial.*;

/** Shared selector DATA only. The actual native adapter/preflight/formatter has its own mandatory consumer regression. */
final class DriverReturnedActionHistoryMaterialTest {
    @Test void originalSelectorsHaveOneLosslessTypedParserAndRenderer(){
        for(StructuralCall call:List.of(new Halt(0),new Halt(Integer.MAX_VALUE),new SplitHalf(7),new Merge(0,1),new Merge(Integer.MAX_VALUE,0))){
            assertEquals(call,parse(call.operation()).orElseThrow());
            assertEquals(call.operation(),parse(call.operation()).orElseThrow().operation());
        }
    }
    @Test void aliasesMalformedAndOutOfRangeSelectorsRemainUnavailable(){
        for(String bad:List.of("halt-army--1","halt-army-01","halt-army-1.0","halt-army-2147483648",
                "split-army-half-01","split-army-half-2147483648","merge-armies-1-with-1","merge-armies-01-with-2",
                "merge-armies-1-with-2:alias","query-army-strengths-v1","enable-army-observer-research-sampling-v1"))
            assertTrue(parse(new OperationKey(bad)).isEmpty(),bad);
        assertThrows(IllegalArgumentException.class,()->new OperationKey("halt-army-+1"));
        assertThrows(IllegalArgumentException.class,()->new OperationKey("halt-army-１"));
        assertThrows(IllegalArgumentException.class,()->new Halt(-1));
        assertThrows(IllegalArgumentException.class,()->new SplitHalf(-1));
        assertThrows(IllegalArgumentException.class,()->new Merge(1,1));
    }
}
