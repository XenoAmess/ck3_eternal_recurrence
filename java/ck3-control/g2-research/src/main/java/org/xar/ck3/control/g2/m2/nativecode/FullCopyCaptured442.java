package org.xar.ck3.control.g2.m2.nativecode;
import java.util.Objects;
public record FullCopyCaptured442(FullCopy437Api.Input input, FullCopy437Api.Bits256 head, FullCopy437Api.Bits256 tail, boolean initialBulk) {
    public FullCopyCaptured442 { Objects.requireNonNull(input); Objects.requireNonNull(head); Objects.requireNonNull(tail); }
}
