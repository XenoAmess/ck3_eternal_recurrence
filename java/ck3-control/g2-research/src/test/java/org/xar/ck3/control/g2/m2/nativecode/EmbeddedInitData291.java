package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
/** Frozen DATA before any literal/target proposal; globaltrace only. */
public final class EmbeddedInitData291 {
    private EmbeddedInitData291() { }
    public enum Op { R64,W32,W64,CALL10,CALL20 }
    public record Step(Op op,List<Long> values) { }
    public record Scene(String name,long receiver,long moduleBase,List<Step> steps,long expectedReturn) { }
}
