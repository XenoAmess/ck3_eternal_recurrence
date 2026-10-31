package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

import java.util.List;

public final class ReleaseApi167 {
    private ReleaseApi167() {}
    public interface Ports {
        long slot38(NativeTaskMemory memory,long target,long receiver,long rows,long alignment,long incomingR9);
        long release10(NativeTaskMemory memory,long target,long receiver,long rows,long alignment,long vptrR9);
    }
    public enum Stage { SLOT38, RELEASE10 }
    public record Word(long address,long value) {}
    public record Call(Stage stage,long target,long receiver,long rows,long alignment,long r9) {}
    public record Scenario(String id,long receiver,long rows,long alignment,long incomingR9,
        List<Word> initialWords,long firstReturn,List<Word> firstEffects,long releaseReturn,
        List<Call> expectedCalls,List<Word> expectedFinalWords,long expectedResult) {}
}
