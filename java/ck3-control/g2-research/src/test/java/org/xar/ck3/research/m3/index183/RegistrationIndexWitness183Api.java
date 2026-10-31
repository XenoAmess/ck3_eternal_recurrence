package org.xar.ck3.research.m3.index183;
import java.util.List;
import org.xar.ck3.research.m3.index183.RegistrationIndex183Api.Input;
public final class RegistrationIndexWitness183Api {
    private RegistrationIndexWitness183Api() { }
    public enum Kind { R8, R32, R64, R128, W8, W32, W64, W128, COMPARE }
    public record Cell(long address, int width, long low, long high) { }
    /** Compare args=[siteRva,RCX,RDX,signedR8]; address/low/high0, returned actual EAX bits. */
    public record Step(Kind kind, long address, long low, long high, List<Long> arguments, int returned, List<Cell> effects) { }
    public record Scene(String name, Input input, List<Cell> initial, List<Step> steps, int expectedEax, List<Cell> finalCells) { }
}
