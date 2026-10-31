package org.xar.ck3.control.g2.common.nativecore.task;

import org.xar.ck3.control.g2.common.nativecore.task.retained.InGameIdlerEventDispatch;

/**
 * Public facade for native idler event dispatch.
 *
 * This class delegates to the retained kernel {@code InGameIdlerEventDispatch.dispatch}.
 * It does not implement the dispatch algorithm itself.
 *
 * The {@code Calls} interface maps to the retained kernel's callback interface.
 * The {@code NativeTaskMemory} interface extends the retained kernel's memory interface.
 *
 * Semantics:
 * - Addresses are supplied by the caller and are not validated.
 * - {@code virtualSlot10} corresponds to the retained kernel's slot 10 invocation.
 * - {@code onNullListener} is an opaque callback for null listener targets.
 * - No game attachment, save status, or authority grants are implied.
 * - Exceptions from callbacks or the retained kernel propagate directly.
 */
public final class NativeIdlerDispatch {

    /**
     * Callback interface for dispatch operations.
     * Maps directly to {@code InGameIdlerEventDispatch.Calls}.
     */
    public interface Calls {
        /**
         * Invokes the virtual slot 10 handler.
         * @param receiver The receiver address.
         * @param eventAddress The event address.
         */
        void virtualSlot10(long receiver, long eventAddress);

        /**
         * Finds the event bucket index for a given event type.
         * @param registryAddress The registry address.
         * @param copiedEventType The event type.
         * @return The bucket index, or negative if not found.
         */
        int findEventBucket(long registryAddress, int copiedEventType);

        /**
         * Handles a null listener target.
         * @param nativeCallTargetRva The target RVA.
         */
        void onNullListener(long nativeCallTargetRva);
    }

    private NativeIdlerDispatch() {
    }

    /**
     * Dispatches an idler event using the retained kernel.
     *
     * @param holder The holder address.
     * @param eventAddress The event address.
     * @param memory The memory interface for address operations.
     * @param calls The callback interface for dispatch operations.
     */
    public static void dispatch(long holder, long eventAddress, NativeTaskMemory memory, Calls calls) {
        InGameIdlerEventDispatch.dispatch(
            holder,
            eventAddress,
            memory,
            new CallsAdapter(calls)
        );
    }

    /**
     * Adapter to map {@code NativeIdlerDispatch.Calls} to {@code InGameIdlerEventDispatch.Calls}.
     */
    private static class CallsAdapter implements InGameIdlerEventDispatch.Calls {
        private final Calls calls;

        CallsAdapter(Calls calls) {
            this.calls = calls;
        }

        @Override
        public void virtualSlot10(long receiver, long eventAddress) {
            calls.virtualSlot10(receiver, eventAddress);
        }

        @Override
        public int findEventBucket(long registryAddress, int copiedEventType) {
            return calls.findEventBucket(registryAddress, copiedEventType);
        }

        @Override
        public void onNullListener(long nativeCallTargetRva) {
            calls.onNullListener(nativeCallTargetRva);
        }
    }
}