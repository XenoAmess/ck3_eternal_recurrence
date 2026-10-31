package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Explicit call/memory effects of full154B25F8A00; raw RAX and EH are not projected. */
public final class RegistrationClearApi174 {
    private RegistrationClearApi174() { }
    public enum Completion {
        CLEARED,
        UNSUPPORTED_INITIAL_RANGE,
        UNSUPPORTED_CLEANUP_RANGE,
        UNSUPPORTED_TARGET
    }
    /** Java-only finite-domain limits, not extra Native branches or native validity evidence. */
    public record Limits(int maxFirstRows,int maxCleanupRows) {
        public Limits {
            if(maxFirstRows<0||maxCleanupRows<0)throw new IllegalArgumentException("nonnegative limits");
        }
    }
    public interface Ports {
        void destroyRow(NativeTaskMemory memory,long pointee,long row);
        void cleanupField(NativeTaskMemory memory,long field);
    }
    /** Only the normal returned receiver observation of held C85860 is supplied here. */
    @FunctionalInterface public interface Singleton {
        long get();
    }
}
