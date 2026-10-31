package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Mxcsr32;

/** New literal full-primary paths with independently supplied nested hash observations. */
public final class GovernmentWholeConcrete173WitnessApi {
    private GovernmentWholeConcrete173WitnessApi() { }
    public enum Branch { PRIMARY_LOOKUP,M0_2D0B490,M1_2D1B7F0 }
    public sealed interface DeepStep permits HashStep,LookupStep,ResultStep {
        Branch branch(); boolean reject();
    }
    public record HashStep(Branch branch,long headerRva,long r8Bits,long r9dBits,long rbxBits,boolean reject) implements DeepStep { }
    public record LookupStep(Branch branch,long instructionRva,long lockAddressBits,boolean reject) implements DeepStep { }
    public record ResultStep(Branch branch,long instructionRva,long addressBits,boolean reject) implements DeepStep { }
    /** Software atomics preserve widths/order/old-return semantics, without a Native concurrency claim.
     * For width8, addend/old/stored are canonical low8 unsigned0..255; width32 keeps raw int bits. */
    public record AtomicStep(int widthBits,long addressBits,int addendBits,int oldBits,int storedBits) { }
    public enum GsPort { INITIAL,LOOKUP,ORDINARY }
    public record GsStep(GsPort port,long returnedQword58Bits) { }
    /**
     * `whole` is a NEW independent literal input/oracle, never an old green case renamed/reexecuted.
     * whole ordinary/lookup call lists include only remaining unknown FALLBACK calls, excluding all
     * newly concrete intercepted parent/manager/lookup/hash/result edges. All share one owned Memory.
     * M0/M1 MXCSR fields are owned at ACTUAL inner hash2D0B4FE/2D1B85E respectively, not derived
     * from entry/afterInitial or earlier opaque effects. Unexecuted branch inputs are only latent
     * owned fixture inputs and give no actual-observation credit. Final primary MXCSR remains independent.
     * Deep budgets, GS and atomics each have one globally ordered script across all their ports.
     */
    public record Witness(GovernmentWhole4798WitnessApi.Witness whole,
            Mxcsr32 m0HashMxcsrAt4FE,Mxcsr32 m1HashMxcsrAt85E,
            List<DeepStep> deepSteps,List<AtomicStep> atomicSteps,List<GsStep> gsSteps) {
        public Witness {
            Objects.requireNonNull(whole);Objects.requireNonNull(m0HashMxcsrAt4FE);Objects.requireNonNull(m1HashMxcsrAt85E);
            deepSteps=List.copyOf(deepSteps);atomicSteps=List.copyOf(atomicSteps);gsSteps=List.copyOf(gsSteps);
        }
    }
    public interface Book { List<Witness> witnesses(); }
}
