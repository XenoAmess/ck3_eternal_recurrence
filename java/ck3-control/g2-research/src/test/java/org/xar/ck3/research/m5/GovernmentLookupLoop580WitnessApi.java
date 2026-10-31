package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.CallFrame;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.CallPost;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.EaxPost;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Entry;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Join;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Mxcsr32;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.VectorPost;

/** Synthetic owned normal observations test exact protocol flow, not the truth of Native FP results. */
public final class GovernmentLookupLoop580WitnessApi {
    private GovernmentLookupLoop580WitnessApi() { }
    public record CallExpectation(CallFrame expected,Map<Long,Integer> expectedMemoryBytes,
            List<SeedByte> memoryMutation,CallPost normalPost,boolean unsupported) {
        public CallExpectation { expectedMemoryBytes=Map.copyOf(expectedMemoryBytes);memoryMutation=List.copyOf(memoryMutation); }
    }
    public sealed interface CpuInput permits Movss,Movd,Convert,Multiply,Truncate { }
    public record Movss(long siteRva,int memoryDwordBits,Bits128 beforeXmm6,Mxcsr32 before) implements CpuInput { }
    public record Movd(long siteRva,int ecxBits,Bits128 beforeXmm0,Mxcsr32 before) implements CpuInput { }
    public record Convert(long siteRva,Bits128 xmm0,Mxcsr32 before) implements CpuInput { }
    public record Multiply(long siteRva,Bits128 xmm0,Bits128 xmm6,Mxcsr32 before) implements CpuInput { }
    public record Truncate(long siteRva,Bits128 xmm0,Mxcsr32 before) implements CpuInput { }
    public sealed interface CpuReply permits VectorReply,EaxReply { }
    public record VectorReply(VectorPost post) implements CpuReply { }
    public record EaxReply(EaxPost post) implements CpuReply { }
    /** normalPost is null only for explicitly unsupported owned CPU behavior. */
    public record CpuExpectation(CpuInput expected,CpuReply normalPost,boolean unsupported) { }
    public record LoopVisit(long headerRva,long cursorBits,long endSlotAddressBits) { }
    public enum Failure { NONE,BUDGET,CPU_UNSUPPORTED,CALL_UNSUPPORTED }
    /** expectedJoin is null only for the specifically expected owned rejection; no fake normal result. */
    public record Witness(String name,Entry entry,MemorySeed memorySeed,long gs58Bits,
            List<CallExpectation> calls,List<CpuExpectation> cpuCalls,List<LoopVisit> loops,long iterationLimit,
            Map<Long,Integer> expectedFinalBytes,Join expectedJoin,Failure expectedFailure) {
        public Witness { calls=List.copyOf(calls);cpuCalls=List.copyOf(cpuCalls);loops=List.copyOf(loops);expectedFinalBytes=Map.copyOf(expectedFinalBytes); }
    }
    public interface Book { List<Witness> witnesses(); }
}
