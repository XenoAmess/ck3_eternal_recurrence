package org.xar.ck3.control.g2.common.nativecore.task.captured;

public final class RequestStaticDispatch4267630 {
    private RequestStaticDispatch4267630() { }

    public interface TailTarget {
        int jumpRax(long targetRax, long knownRcx);
    }

    public static int execute(long knownRcx, long liveRax, TailTarget target) {
        // The caller Gate424CFFC performs 'call QWORD PTR [slot43DBBA8]' with RCX=size and RAX=decoded.
        // The slot QWORD points to a static body containing JMP RAX.
        // The Java model represents the *result* of this control transfer as seen by the caller.
        // The caller consumes the return value as EAX32 (int).
        // We pass the full 64-bit targetRax (liveRax) and knownRcx to the injected TailTarget.
        // The TailTarget is responsible for providing the int result that the caller would see.
        // No validation, no memory access, no native emulation.
        return target.jumpRax(liveRax, knownRcx);
    }
}
