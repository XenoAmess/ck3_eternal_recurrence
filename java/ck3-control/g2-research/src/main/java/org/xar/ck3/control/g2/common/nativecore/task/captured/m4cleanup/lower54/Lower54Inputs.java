package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower54;
/** Complete known effects-only roles; no raw-return ABI is asserted. */
public final class Lower54Inputs {
 private Lower54Inputs() { }
 public record CallInput(long moduleBaseRaw,long objectRaw) { }
 public interface Memory { int readInt32(long address); }
 public interface Calls { void call4255FFC(long knownRcxRaw); void call424E364(long knownRcxRaw); }
}
