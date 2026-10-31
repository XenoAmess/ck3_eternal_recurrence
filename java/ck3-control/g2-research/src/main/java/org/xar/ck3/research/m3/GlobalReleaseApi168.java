package org.xar.ck3.research.m3;

public final class GlobalReleaseApi168 {
    private GlobalReleaseApi168() {}
    public interface Ports {
        long tail40ec530(long rcx,long rdx,long r8,long r9,long incomingRax);
    }
    public record Registers(long rcx,long rdx,long r8,long r9,long rax) {}
    public record Scenario(String id,Registers incoming,long tailResult,
        int expectedCalls,Registers expectedTail,long expectedResult) {}
}
