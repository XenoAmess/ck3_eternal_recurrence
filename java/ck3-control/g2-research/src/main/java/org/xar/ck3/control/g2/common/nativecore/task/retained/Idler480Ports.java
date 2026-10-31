package org.xar.ck3.control.g2.common.nativecore.task.retained;
public final class Idler480Ports {
    public interface Symbols { long address(long rva); }
    public record Descriptor(long data, int length, byte flag) {}
    public interface Calls {
        long allocate(long size);
        long constructChild(long storage, long freshH, int zero);
        long getRegistry(long architecturalRcx);
        long findName(long registry, Descriptor knownDescriptorFields);
        void virtual30(long receiver, long lookupResult, long savedO50);
    }
    private Idler480Ports() {}
}
