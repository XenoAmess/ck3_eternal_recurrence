package org.xar.ck3.control.g2.m2.nativecode;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.Copy4226860Api.Bits256;
/** Actual scalar16/Word16 naming bridge. */
public final class Copy4226860SharedAdapter395 {
 private Copy4226860SharedAdapter395() { }
 public interface Memory {
  int read8(long address);
  int readScalar16(long address);
  int read32(long address);
  long read64(long address);
  Bits128 read128(long address);
  Bits256 read256(long address);
  void write8(long address,int value);
  void write16(long address,int value);
  void write32(long address,int value);
  void write64(long address,long value);
  void write128(long address,Bits128 value);
  void write256(long address,Bits256 value);
  void storeFence();
 }
 public static Copy4226860Api.Memory bind(Memory memory) {
  return new Copy4226860Api.Memory() {
   @Override
   public int read8(long address) {
    return memory.read8(address);
   }
   @Override
   public int read16(long address) {
    return memory.readScalar16(address);
   }
   @Override
   public int read32(long address) {
    return memory.read32(address);
   }
   @Override
   public long read64(long address) {
    return memory.read64(address);
   }
   @Override
   public Bits128 read128(long address) {
    return memory.read128(address);
   }
   @Override
   public Bits256 read256(long address) {
    return memory.read256(address);
   }
   @Override
   public void write8(long address, int value) {
    memory.write8(address, value);
   }
   @Override
   public void write16(long address, int value) {
    memory.write16(address, value);
   }
   @Override
   public void write32(long address, int value) {
    memory.write32(address, value);
   }
   @Override
   public void write64(long address, long value) {
    memory.write64(address, value);
   }
   @Override
   public void write128(long address, Bits128 value) {
    memory.write128(address, value);
   }
   @Override
   public void write256(long address, Bits256 value) {
    memory.write256(address, value);
   }
   @Override
   public void storeFence() {
    memory.storeFence();
   }
  };
 }
}