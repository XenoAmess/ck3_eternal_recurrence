package org.xar.ck3.control.g2.common.nativecore.task.captured;

public final class Idler79eContinuationPorts implements Idler79ePorts.Ports {
    @FunctionalInterface public interface RootPort { void call383e320(Idler79ePorts.Known383e320 known); }
    private final RootPort rootPort;
    private final Idler28eed20.Port continuation;

    public Idler79eContinuationPorts(RootPort rootPort, Idler28eed20.Port continuation) {
        this.rootPort = rootPort;
        this.continuation = continuation;
    }

    @Override
    public void call383e320(Idler79ePorts.Known383e320 known) {
        rootPort.call383e320(known);
    }

    @Override
    public void call28eed20(long rcx, int edx, int r8d) {
        Idler28eed20.invoke(rcx, edx, r8d, continuation);
    }
}
