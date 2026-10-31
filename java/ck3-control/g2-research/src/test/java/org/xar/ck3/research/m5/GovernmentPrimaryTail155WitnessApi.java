package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.*;

/** Independent literal witnesses and recorder protocol; no tail algorithm or green result embedded. */
public final class GovernmentPrimaryTail155WitnessApi {
    private GovernmentPrimaryTail155WitnessApi() { }
    public record SeedByte(long addressBits, int byteBits) { }
    /** Initial bytes are explicit; missing read addresses must fail, not silently return zero. */
    public record MemorySeed(List<SeedByte> bytes) {
        public MemorySeed { bytes=List.copyOf(bytes); }
    }
    public enum Register { RAX,RCX,RDX,R8,R9,R10,R11,RBX,RBP,RSI,RDI,R12,R13,R14,R15,RSP }
    /** Only these selected fields are asserted; all actual call state remains available to the recorder. */
    public record CallStep(long siteRva, long targetRva, Map<Register,Long> expectedRegisterBits,
            Map<Long,Integer> expectedMemoryBytes, List<SeedByte> memoryMutation,
            VolatileBits returnedVolatile) {
        public CallStep {
            expectedRegisterBits=Map.copyOf(expectedRegisterBits); expectedMemoryBytes=Map.copyOf(expectedMemoryBytes);
            memoryMutation=List.copyOf(memoryMutation);
        }
    }
    public record Witness(String name, Entry entry, MemorySeed memorySeed, long gs58Bits,
            List<CallStep> calls, long iterationLimit,
            Map<Long,Integer> expectedFinalBytes, NormalReturn expectedReturn,
            boolean expectedBudgetUnsupported) {
        public Witness {
            calls=List.copyOf(calls); expectedFinalBytes=Map.copyOf(expectedFinalBytes);
        }
    }
    public interface WitnessBook { List<Witness> witnesses(); }
    public record WitnessResult(String name, boolean passed, String detail) { }
}
