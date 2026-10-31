package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import org.xar.ck3.research.m1.GovernmentThreadHeader178;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Calls;

public final class GovernmentSharedRecord180Calls {
    private GovernmentSharedRecord180Calls() { }

    public static GovernmentPrimaryTail155Api.Calls bind(
            long imageBase,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls delegate,
            GovernmentThreadHeader178Api.Ports headerPorts,
            GovernmentThreadHeader178Api.WaitBudget headerBudget) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(delegate);
        Objects.requireNonNull(headerPorts);
        Objects.requireNonNull(headerBudget);

        return new Adapter(imageBase, memory, delegate, headerPorts, headerBudget);
    }

    private static final class Adapter implements GovernmentPrimaryTail155Api.Calls {
        private final long imageBase;
        private final GovernmentSharedManager167Api.Memory memory;
        private final GovernmentPrimaryTail155Api.Calls delegate;
        private final GovernmentThreadHeader178Api.Ports headerPorts;
        private final GovernmentThreadHeader178Api.WaitBudget headerBudget;

        Adapter(long imageBase, GovernmentSharedManager167Api.Memory memory, GovernmentPrimaryTail155Api.Calls delegate,
                GovernmentThreadHeader178Api.Ports headerPorts, GovernmentThreadHeader178Api.WaitBudget headerBudget) {
            this.imageBase = imageBase;
            this.memory = memory;
            this.delegate = delegate;
            this.headerPorts = headerPorts;
            this.headerBudget = headerBudget;
        }

        @Override
        public long readGsQword58() {
            return delegate.readGsQword58();
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
            // Branch A: manager3F8A834 -> 2D88870 (newSharedRecord180 core)
            if (call.callSiteRva() == 0x3F8A834L && call.targetRva() == 0x2D88870L) {
                return handleManagerToNewRecord(call);
            }
            // Branch B: newHeader2D888A3 -> 4223A84 (existing Header178 core)
            if (call.callSiteRva() == 0x2D888A3L && call.targetRva() == 0x4223A84L) {
                return handleNewRecordToHeader(call);
            }
            // All other calls delegate unchanged
            return delegate.invoke(call);
        }

        private GovernmentPrimaryTail155Api.VolatileBits handleManagerToNewRecord(GovernmentPrimaryTail155Api.OpaqueCall call) {
            long p = call.rspBits();
            long returnAddr = imageBase + call.callSiteRva() + 5L;
            long calleeRsp = p - 8L;

            // Physical push of return address before invoking the core
            memory.writeQword(calleeRsp, returnAddr);

            GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                    imageBase,
                    calleeRsp,
                    call.volatileBits(),
                    call.nonvolatileBits()
            );

            // Invoke the actual new93 GovernmentSharedRecord180 core
            // using THIS bound adapter so its nested calls come back through this
            GovernmentCallee164Api.NormalReturn result = GovernmentSharedRecord180.execute(
                    entry, memory, this
            );

            // Validate return RIP
            if (result.returnRipBits() != returnAddr) {
                throw new UnsupportedOperationException("Target returned unexpected RIP");
            }
            // Validate return RSP
            if (result.callerRspBits() != p) {
                throw new UnsupportedOperationException("Target returned unexpected caller RSP");
            }
            // Validate nonvolatile preservation
            GovernmentPrimaryTail155Api.NonvolatileBits incoming = call.nonvolatileBits();
            GovernmentPrimaryTail155Api.NonvolatileBits restored = result.nonvolatileBits();
            if (incoming.rbxBits() != restored.rbxBits() ||
                incoming.rbpBits() != restored.rbpBits() ||
                incoming.rsiBits() != restored.rsiBits() ||
                incoming.rdiBits() != restored.rdiBits() ||
                incoming.r12Bits() != restored.r12Bits() ||
                incoming.r13Bits() != restored.r13Bits() ||
                incoming.r14Bits() != restored.r14Bits() ||
                incoming.r15Bits() != restored.r15Bits() ||
                !incoming.xmm6().equals(restored.xmm6())) {
                throw new UnsupportedOperationException("Target failed to preserve nonvolatile state.");
            }

            return result.volatileBits();
        }

        private GovernmentPrimaryTail155Api.VolatileBits handleNewRecordToHeader(GovernmentPrimaryTail155Api.OpaqueCall call) {
            long p = call.rspBits();
            long returnAddr = imageBase + call.callSiteRva() + 5L;
            long calleeRsp = p - 8L;

            // The new core ALREADY pushed the return address at calleeRsp.
            // We do NOT write again. We just construct the entry and invoke Header178.

            GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                    imageBase,
                    calleeRsp,
                    call.volatileBits(),
                    call.nonvolatileBits()
            );

            // Invoke existing GovernmentThreadHeader178.execute
            GovernmentCallee164Api.NormalReturn result = GovernmentThreadHeader178.execute(
                    entry,
                    memory,
                    headerPorts,
                    headerBudget
            );

            // Validate return RIP
            if (result.returnRipBits() != returnAddr) {
                throw new UnsupportedOperationException("Target returned unexpected RIP");
            }
            // Validate return RSP
            if (result.callerRspBits() != p) {
                throw new UnsupportedOperationException("Target returned unexpected caller RSP");
            }
            // Validate nonvolatile preservation
            GovernmentPrimaryTail155Api.NonvolatileBits incoming = call.nonvolatileBits();
            GovernmentPrimaryTail155Api.NonvolatileBits restored = result.nonvolatileBits();
            if (incoming.rbxBits() != restored.rbxBits() ||
                incoming.rbpBits() != restored.rbpBits() ||
                incoming.rsiBits() != restored.rsiBits() ||
                incoming.rdiBits() != restored.rdiBits() ||
                incoming.r12Bits() != restored.r12Bits() ||
                incoming.r13Bits() != restored.r13Bits() ||
                incoming.r14Bits() != restored.r14Bits() ||
                incoming.r15Bits() != restored.r15Bits() ||
                !incoming.xmm6().equals(restored.xmm6())) {
                throw new UnsupportedOperationException("Target failed to preserve nonvolatile state.");
            }

            return result.volatileBits();
        }
    }

    public static GovernmentCallee164Api.NormalReturn executeManager(
            GovernmentCallee164Api.Entry entry,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls delegate,
            GovernmentThreadHeader178Api.Ports headerPorts,
            GovernmentThreadHeader178Api.WaitBudget headerBudget) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(delegate);
        Objects.requireNonNull(headerPorts);
        Objects.requireNonNull(headerBudget);

        // Compose existing Header178Calls.bind for the old manager edge (3F8A813 -> 4223A84)
        GovernmentPrimaryTail155Api.Calls headerBound = GovernmentThreadHeader178Calls.bind(
                entry.imageBaseBits(),
                memory,
                delegate,
                headerPorts,
                headerBudget
        );

        // Then bind newRecord adapter on top
        GovernmentPrimaryTail155Api.Calls boundCalls = bind(
                entry.imageBaseBits(),
                memory,
                headerBound,
                headerPorts,
                headerBudget
        );

        // Invoke unchanged manager211 (GovernmentSharedManager167.execute)
        return GovernmentSharedManager167.execute(entry, memory, boundCalls);
    }
}