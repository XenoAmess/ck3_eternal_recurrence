package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m1.GovernmentFull193172Composition;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentWhole4798Api;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m1.GovernmentRowResolve164Api;
import org.xar.ck3.research.m5.GovernmentByteHash169LookupCalls;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api;
import org.xar.ck3.research.m1.GovernmentLookup167Api;
import org.xar.ck3.research.m5.GovernmentResult168Api;

/**
 * Owned normal composition contract for held4798B; no live capture, Native ABI or Game claim.
 */
public final class GovernmentWholeConcrete173 {
    private GovernmentWholeConcrete173() { }

    public static Calls bindOrdinary(long imageBaseBits,
            GovernmentWholeConcrete173Api.Memory memory,
            Calls fallback,
            GovernmentWholeConcrete173Api.DeepInputs deepInputs) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(deepInputs);

        return new Calls() {
            @Override public long readGsQword58() {
                return fallback.readGsQword58();
            }

            @Override public VolatileBits invoke(OpaqueCall call) {
                Objects.requireNonNull(call);

                if (call.callSiteRva() == 0x30A3C12L && call.targetRva() == 0x2D0B490L) {
                    return handleM0(imageBaseBits, memory, fallback, deepInputs, call);
                }
                if (call.callSiteRva() == 0x30A3646L && call.targetRva() == 0x2D1B7F0L) {
                    return handleM1(imageBaseBits, memory, fallback, deepInputs, call);
                }

                return fallback.invoke(call);
            }
        };
    }

    private static VolatileBits handleM0(long imageBaseBits,
            GovernmentWholeConcrete173Api.Memory memory,
            Calls fallback,
            GovernmentWholeConcrete173Api.DeepInputs deepInputs,
            OpaqueCall call) {

        GovernmentWhole4798Api.MxcsrObservation obs = deepInputs.m0HashMxcsrAt2D0B4FE();
        if (!(obs instanceof GovernmentWhole4798Api.AvailableMxcsr)) {
            String reason = (obs instanceof GovernmentWhole4798Api.UnavailableMxcsr)
                    ? ((GovernmentWhole4798Api.UnavailableMxcsr) obs).reason()
                    : "unknown MXCSR observation type";
            throw new GovernmentWhole4798Api.MxcsrUnavailableException(reason);
        }
        GovernmentLookupLoop580Api.Mxcsr32 mxcsr = ((GovernmentWhole4798Api.AvailableMxcsr) obs).bits();

        long calleeRsp = call.rspBits() - 8L;
        long returnVA = imageBaseBits + 0x30A3C12L + 5L;

        memory.writeQword(calleeRsp, returnVA);

        GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                imageBaseBits,
                calleeRsp,
                call.volatileBits(),
                call.nonvolatileBits()
        );

        GovernmentCallee164Api.NormalReturn result = GovernmentFull193Composition168.execute(
                entry,
                memory,
                fallback,
                mxcsr,
                deepInputs.m0HashBudget(),
                deepInputs.m0LookupBudget(),
                deepInputs.m0ResultBudget()
        );

        if (result.returnRipBits() != returnVA) {
            throw new UnsupportedOperationException("M0 return RIP mismatch");
        }
        if (result.callerRspBits() != call.rspBits()) {
            throw new UnsupportedOperationException("M0 caller RSP mismatch");
        }
        if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
            throw new UnsupportedOperationException("M0 nonvolatile mismatch");
        }

        return result.volatileBits();
    }

    private static VolatileBits handleM1(long imageBaseBits,
            GovernmentWholeConcrete173Api.Memory memory,
            Calls fallback,
            GovernmentWholeConcrete173Api.DeepInputs deepInputs,
            OpaqueCall call) {

        GovernmentWhole4798Api.MxcsrObservation obs = deepInputs.m1HashMxcsrAt2D1B85E();
        if (!(obs instanceof GovernmentWhole4798Api.AvailableMxcsr)) {
            String reason = (obs instanceof GovernmentWhole4798Api.UnavailableMxcsr)
                    ? ((GovernmentWhole4798Api.UnavailableMxcsr) obs).reason()
                    : "unknown MXCSR observation type";
            throw new GovernmentWhole4798Api.MxcsrUnavailableException(reason);
        }
        GovernmentLookupLoop580Api.Mxcsr32 mxcsr = ((GovernmentWhole4798Api.AvailableMxcsr) obs).bits();

        long calleeRsp = call.rspBits() - 8L;
        long returnVA = imageBaseBits + 0x30A3646L + 5L;

        memory.writeQword(calleeRsp, returnVA);

        GovernmentRowResolve164Api.Entry entry = new GovernmentRowResolve164Api.Entry(
                imageBaseBits,
                calleeRsp,
                call.volatileBits(),
                call.nonvolatileBits()
        );

        GovernmentRowResolve164Api.Result result = GovernmentFull193172Composition.execute(
                entry,
                memory,
                fallback,
                deepInputs.m1LookupBudget(),
                deepInputs.m1ResultBudget(),
                deepInputs.m1HashBudget(),
                mxcsr
        );

        if (result.returnRipBits() != returnVA) {
            throw new UnsupportedOperationException("M1 return RIP mismatch");
        }
        if (result.callerRspBits() != call.rspBits()) {
            throw new UnsupportedOperationException("M1 caller RSP mismatch");
        }
        if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
            throw new UnsupportedOperationException("M1 nonvolatile mismatch");
        }

        return result.volatileBits();
    }

    public static GovernmentWhole4798Api.Result execute(GovernmentInitialFrame162Api.Entry entry,
            GovernmentWholeConcrete173Api.Memory memory,
            GovernmentWhole4798Api.Calls calls,
            GovernmentWhole4798Api.Budgets budgets,
            GovernmentLookupLoop580Api.Cpu cpu,
            GovernmentWhole4798Api.MxcsrBoundary mxcsrBoundary,
            GovernmentWholeConcrete173Api.DeepInputs deepInputs) {

        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(budgets);
        Objects.requireNonNull(cpu);
        Objects.requireNonNull(mxcsrBoundary);
        Objects.requireNonNull(deepInputs);

        // Bind the primary hash lookup calls using the existing adapter
        GovernmentLookupLoop580Api.Calls primaryHashLookupCalls = GovernmentByteHash169LookupCalls.bind(
                entry.imageBaseBits(),
                memory,
                calls.lookup(),
                deepInputs.primaryHashBudget()
        );

        // Bind the ordinary calls using the new wrapper
        Calls ordinaryCalls = bindOrdinary(
                entry.imageBaseBits(),
                memory,
                calls.ordinary(),
                deepInputs
        );

        // Construct the new Calls record preserving other ports
        GovernmentWhole4798Api.Calls newCalls = new GovernmentWhole4798Api.Calls(
                calls.initial(),
                primaryHashLookupCalls,
                ordinaryCalls,
                calls.lookup155(),
                calls.prefix153(),
                calls.post153()
        );

        return GovernmentWhole4798.execute(
                entry,
                memory,
                newCalls,
                budgets,
                cpu,
                mxcsrBoundary
        );
    }
}
