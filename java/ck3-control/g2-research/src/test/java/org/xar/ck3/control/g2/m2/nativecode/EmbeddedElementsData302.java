package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
/** PureDATA frozen before proposal; globallyorderedscript, not fullRAM. */
public final class EmbeddedElementsData302 {
    private EmbeddedElementsData302() { }
    public enum Op { R8,R32,R64,W8,W32,W64,PREP,ALLOC,REPLACE,DESTROY,COPY16HEAD,COPY4HEAD,COPY16RANGE,COPY4RANGE }
    public record Step(Op op,List<Long> values,long returned) { }
    public record Scene(String name,long destination,long source,long moduleBase,List<Step> steps,long expectedReturn) { }
}
