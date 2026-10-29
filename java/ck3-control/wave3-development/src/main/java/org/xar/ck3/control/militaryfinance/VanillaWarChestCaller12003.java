package org.xar.ck3.control.militaryfinance;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.wave2.military.landstock.LandStockPolicy;

/** Pure arithmetic of the held complete .3 caller, never a .4 admission or full AI chooser. */
public final class VanillaWarChestCaller12003 {
    public static final String EXE_SHA256 = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6";
    public static final String SOURCE_SHA256 = "67817245116fff77a229eaebe34f3d09a533afaa97b509577e69812653077a63";
    public static final long START_RVA = 0x19EA9C0L;
    public static final long END_RVA = 0x19EADA5L;
    public enum Branch { NONPOSITIVE_TREASURY, POSITIVE_TREASURY }
    /** These are actual caller operands, not hardcoded native defaults or inferred future costs. */
    public record Operands(int tierMinimumWholeUnits, int maintenanceMonths,
                           long maximumGoldMaintenanceRaw, long maximumTreasuryMaintenanceRaw) { }
    public record Projection(Operands operands, Branch branch, Long goldTreasuryRatioRaw,
                             List<Long> resourceTargetsRaw) {
        public Projection { resourceTargetsRaw = List.copyOf(resourceTargetsRaw); }
        public boolean current12004Qualified() { return false; }
        public boolean fullNativeAiChoiceReconstructed() { return false; }
        public boolean futureWarCostUpperBound() { return false; }
    }
    private VanillaWarChestCaller12003() { }

    public static Projection project(Operands in) {
        if (in == null) throw new IllegalArgumentException("explicit caller operands required");
        long minimum = in.tierMinimumWholeUnits() * 100_000L;
        long months = in.maintenanceMonths() * 100_000L;
        long gold = LandStockPolicy.nativeFixedMultiply(in.maximumGoldMaintenanceRaw(), months);
        long treasury = LandStockPolicy.nativeFixedMultiply(in.maximumTreasuryMaintenanceRaw(), months);
        Long ratio = null;
        Branch branch;
        if (in.maximumTreasuryMaintenanceRaw() <= 0) {
            branch = Branch.NONPOSITIVE_TREASURY;
            gold = Math.max(minimum, gold);
        } else {
            branch = Branch.POSITIVE_TREASURY;
            ratio = LandStockPolicy.nativeFixedDivide(in.maximumGoldMaintenanceRaw(),
                    in.maximumTreasuryMaintenanceRaw()).value().longValue();
            gold = Math.max(gold, LandStockPolicy.nativeFixedMultiply(minimum, ratio));
            // Source SUB and all shared multiply wrap points remain signed64.
            treasury = Math.max(treasury, LandStockPolicy.nativeFixedMultiply(minimum, 100_000L - ratio));
        }
        List<Long> vector = new ArrayList<>(java.util.Collections.nCopies(10, 0L));
        vector.set(0, gold); vector.set(6, treasury);
        return new Projection(in, branch, ratio, vector);
    }
}
