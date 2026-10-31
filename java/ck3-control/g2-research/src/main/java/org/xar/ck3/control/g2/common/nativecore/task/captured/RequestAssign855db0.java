package org.xar.ck3.control.g2.common.nativecore.task.captured;

public final class RequestAssign855db0 {
 private RequestAssign855db0() { }
 public interface Ports {
  long call856db0(long rcx);
  void call4226860(long rcx,long rdx,long r8);
  void call4223f44(long rcx,long rdx,java.util.OptionalLong knownR8);
 }
 public static final class UnsupportedSourcePath extends RuntimeException {
  private static final long serialVersionUID = 1L;
  private final long targetRva;
  private final long trapSiteRva;
  private final long knownRcx;
  private final long knownRdx;
  private final long knownR8;
  public UnsupportedSourcePath(long targetRva,long trapSiteRva,long knownRcx,long knownRdx,long knownR8) {
   super("source error helper remains unexecuted");
   this.targetRva=targetRva; this.trapSiteRva=trapSiteRva;
   this.knownRcx=knownRcx; this.knownRdx=knownRdx; this.knownR8=knownR8;
  }
  public long targetRva() { return targetRva; }
  public long trapSiteRva() { return trapSiteRva; }
  public long knownRcx() { return knownRcx; }
  public long knownRdx() { return knownRdx; }
  public long knownR8() { return knownR8; }
 }

public static long assign(long dest, long source, long lengthBits, RequestE92780.Memory memory, Ports ports) {
    long oldCapacityBits = memory.readPointer(dest + 0x18L);
    if (Long.compareUnsigned(lengthBits, oldCapacityBits) <= 0) {
        long data = dest;
        if (Long.compareUnsigned(oldCapacityBits, 0x10L) >= 0) {
            data = memory.readPointer(dest);
        }
        memory.writeInt64(dest + 0x10L, lengthBits);
        ports.call4226860(data, source, lengthBits);
        memory.writeByte(data + lengthBits, (byte) 0);
        return dest;
    }
    if (Long.compareUnsigned(lengthBits, 0x7fffffffffffffffL) > 0) {
        throw new UnsupportedSourcePath(0x8523a0L, 0x855eb5L, dest, source, lengthBits);
    }
    long newCapacityBits = growthCapacity(oldCapacityBits, lengthBits);
    long newPointer = ports.call856db0(newCapacityBits + 1L);
    memory.writeInt64(dest + 0x10L, lengthBits);
    memory.writeInt64(dest + 0x18L, newCapacityBits);
    ports.call4226860(newPointer, source, lengthBits);
    memory.writeByte(newPointer + lengthBits, (byte) 0);
    if (Long.compareUnsigned(oldCapacityBits, 0x10L) >= 0) {
        long oldPointer = memory.readPointer(dest);
        long freeSizeBits = oldCapacityBits + 1L;
        if (Long.compareUnsigned(freeSizeBits, 0x1000L) >= 0) {
            long header = memory.readPointer(oldPointer - 8L);
            freeSizeBits += 0x27L;
            long delta = oldPointer - header;
            if (Long.compareUnsigned(delta - 8L, 0x1fL) > 0) {
                throw new UnsupportedSourcePath(0x4232a70L, 0x855ebbL, delta, freeSizeBits, header);
            }
            ports.call4223f44(header, freeSizeBits, java.util.OptionalLong.of(header));
        } else {
            ports.call4223f44(oldPointer, freeSizeBits, java.util.OptionalLong.empty());
        }
    }
    memory.writeInt64(dest, newPointer);
    return dest;
}

static long growthCapacity(long oldCapacityBits, long lengthBits) {
    long rdi = 0x7fffffffffffffffL;
    long rcx = lengthBits;
    rcx |= 0xfL;
    if (Long.compareUnsigned(rcx, rdi) > 0) {
        return rdi;
    }
    long rdx = oldCapacityBits;
    long rax = rdi;
    rdx >>>= 1;
    rax -= rdx;
    if (Long.compareUnsigned(oldCapacityBits, rax) > 0) {
        return rdi;
    }
    rax = rdx + oldCapacityBits;
    rdi = rcx;
    if (Long.compareUnsigned(rcx, rax) < 0) {
        rdi = rax;
    }
    return rdi;
}
}
