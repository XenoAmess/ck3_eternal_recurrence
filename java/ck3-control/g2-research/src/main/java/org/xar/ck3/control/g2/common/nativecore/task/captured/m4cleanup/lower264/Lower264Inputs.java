package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower264;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374.B374Inputs;
/** Consumed normal roles only; opaquecallee names and rawreturn unqualified. */
public final class Lower264Inputs {
 private Lower264Inputs() { }
 public record CallInput(long objectRaw) { }
 public interface Memory extends B374Inputs.Memory { }
 public interface Calls {
  void call4255C64(long knownRcxRaw,long knownRdxRaw);
  void call424E364(long knownRcxRaw);
 }
}
