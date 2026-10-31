package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
/** Source-bound projections of 25AC237..25AC35D; caller supplies storage. */
public final class Idler79ePorts {
 private Idler79ePorts() { }
 public interface Memory extends NativeTaskMemory {
  /** Actual zero-extended byte, 0..255. */
  int readUnsignedByte(long address);
  void writeByte(long address,byte value);
  /** One non-LOCK DEC m32 effect, modulo32; no atomicity guarantee. */
  void decrementInt32(long address);
 }
 public record ScanResult(long initialCells,int rawDword4) { }
 /** Known registers/written caller-frame fields only; R9/padding omitted, not a Native-call signature. */
 public record Known383e320(long rcx,int edx,int r8d,long stack20,int stack28Byte,
                           long stack2c,int stack34,long stack38,int stack40) { }
 public interface Ports {
  void call383e320(Known383e320 known);
  void call28eed20(long rcx,int edx,int r8d);
 }
}
