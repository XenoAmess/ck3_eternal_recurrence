package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Supplied-storage caller wiring; no current U, native ABI, queue drain or Save completion. */
public final class RequestStringConsumers {
    private RequestStringConsumers() { }

    public interface InitializerRemainder {
        long call4223b94(int ecx);
        void call856050(long rcx);
    }

    public interface FactoryRemainder {
        void call3852500(Request26769e0.Known3852500 known);
        void callVirtual0(long target, long rcx, int edx);
        void call856050(long rcx);
    }

    // These adapters replace only the two established string-helper call sites.

public static RequestE92780.Ports initializerPorts(RequestE92780.Memory memory, InitializerRemainder remainder, RequestConstruct855f00.Ports constructPorts) {
    return new RequestE92780.Ports() {
        @Override
        public long call4223b94(int ecx) {
            return remainder.call4223b94(ecx);
        }

        @Override
        public void call855f00(long rcx, long rdx) {
            RequestConstruct855f00.construct(rcx, rdx, memory, constructPorts);
        }

        @Override
        public void call856050(long rcx) {
            remainder.call856050(rcx);
        }
    };
}

public static Request26769e0.Ports factoryPorts(RequestE92780.Memory memory, FactoryRemainder remainder, RequestAssign855db0.Ports assignPorts) {
    return new Request26769e0.Ports() {
        @Override
        public void call3852500(Request26769e0.Known3852500 known) {
            remainder.call3852500(known);
        }

        @Override
        public void callVirtual0(long target, long rcx, int edx) {
            remainder.callVirtual0(target, rcx, edx);
        }

        @Override
        public void call856050(long rcx) {
            remainder.call856050(rcx);
        }

        @Override
        public void call855db0(long rcx, long rdx, long r8) {
            RequestAssign855db0.assign(rcx, rdx, r8, memory, assignPorts);
        }
    };
}
}
