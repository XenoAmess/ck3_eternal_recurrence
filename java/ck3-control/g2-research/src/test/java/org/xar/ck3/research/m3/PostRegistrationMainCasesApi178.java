package org.xar.ck3.research.m3;

import java.util.List;

/** Independent fixture declarations only; no production or expected-case algorithm. */
public final class PostRegistrationMainCasesApi178 {
    private PostRegistrationMainCasesApi178() { }
    public record Word(long address, int width, long bits) { }
    public record Probe(String exactEvent, int count) { }
    /** Port name matches the production API; Memory is implicit and must retain identity. */
    public record Call(String role, long[] arguments, long returned,
                       List<Word> observes, List<Word> effects) { }
    public record Case(String id, long moduleBase, long incomingVector, long sourceRsp,
                       List<Word> initial, List<Call> calls, List<Word> expectedWords,
                       List<Probe> probes, List<String> orderedEvents, boolean noWrites) { }
}
