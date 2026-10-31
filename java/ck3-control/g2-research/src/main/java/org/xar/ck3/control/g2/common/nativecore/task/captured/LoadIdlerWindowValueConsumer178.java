package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Actual178 known-target returning Ports composition; unknown targets stay opaque. */
public final class LoadIdlerWindowValueConsumer178 {
    private LoadIdlerWindowValueConsumer178() { }
    public static LoadIdlerVirtualGate178.Ports bind(long moduleBase, LoadIdlerVirtualGate178.Memory memory, LoadIdlerVirtualGate178.Ports external) {
        return new LoadIdlerVirtualGate178.Ports() {
            @Override
            public long invoke(LoadIdlerRootPublication175.Invocation call) {
                if (call.targetBits() == moduleBase + 0x3E098F0L) {
                    return LoadPdxWindowValue178.readRax(moduleBase, new LoadPdxWindowValue178.Memory() {
                        @Override
                        public long readPointer(long address) {
                            return memory.readPointer(address);
                        }
                    });
                }
                return external.invoke(call);
            }
        };
    }
}
