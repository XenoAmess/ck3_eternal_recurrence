package org.xar.ck3.control.g2.common.nativecore.task.captured;

public final class RequestStringStorageConsumers {
    private RequestStringStorageConsumers() { }

    public static RequestConstruct855f00.Ports constructPorts(RequestE92780.Memory memory, RequestBlock856db0.Ports blockPorts, RequestConstruct855f00.Ports remainder) {
        return new RequestConstruct855f00.Ports() {
            @Override
            public long call856db0(long rcx) {
                return RequestBlock856db0.execute(rcx, memory, blockPorts);
            }
            @Override
            public void call4226860(long rcx, long rdx, long r8) {
                remainder.call4226860(rcx, rdx, r8);
            }
        };
    }

    public static RequestAssign855db0.Ports assignPorts(RequestE92780.Memory memory, RequestBlock856db0.Ports blockPorts, RequestAssign855db0.Ports remainder) {
        return new RequestAssign855db0.Ports() {
            @Override
            public long call856db0(long rcx) {
                return RequestBlock856db0.execute(rcx, memory, blockPorts);
            }
            @Override
            public void call4226860(long rcx, long rdx, long r8) {
                remainder.call4226860(rcx, rdx, r8);
            }
            @Override
            public void call4223f44(long rcx, long rdx, java.util.OptionalLong knownR8) {
                remainder.call4223f44(rcx, rdx, knownR8);
            }
        };
    }
}
