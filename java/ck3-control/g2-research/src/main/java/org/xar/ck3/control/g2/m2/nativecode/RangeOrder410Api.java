package org.xar.ck3.control.g2.m2.nativecode;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.Copy4226860Api.Bits256;
/** Observable dataMemory profile; privateABI stack/V/N/flags outside this API. */
public final class RangeOrder410Api {
 private RangeOrder410Api() { }
 public record Input(long first,long middle,long last,long moduleBase) { }
 public interface Memory {
  int read8(long address);
  int read32(long address);
  Bits128 read128(long address);
  Bits256 read256(long address);
  void write8(long address,int value);
  void write128(long address,Bits128 value);
  void write256(long address,Bits256 value);
 }
 @FunctionalInterface public interface LoopBudget {
  void beforeStep(int headerRva,long frontPointer);
 }
}
