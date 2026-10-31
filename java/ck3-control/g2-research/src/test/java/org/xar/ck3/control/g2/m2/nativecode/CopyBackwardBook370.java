package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.CopyWitnessData370.*;
public final class CopyBackwardBook370 {
    private CopyBackwardBook370() { }
    private static final long M=0x3300000000L, S=0x2200000000L, D=0x1100000000L;
    private static long le(long offset) { long v=0; for(int i=0;i<8;i++)v|=((offset+i+0x10)&255L)<<(8*i); return v; }
    private static Step r128(long offset) { return new Step(Op.R128,List.of(S+offset,le(offset),le(offset+8)),0); }
    private static Step w128(long address,long capturedOffset) { return new Step(Op.W128,List.of(address,le(capturedOffset),le(capturedOffset+8)),0); }
    private static Step r256(long offset) { return new Step(Op.R256,List.of(S+offset,le(offset),le(offset+8),le(offset+16),le(offset+24)),0); }
    private static Step w256(long address,long capturedOffset) { return new Step(Op.W256,List.of(address,le(capturedOffset),le(capturedOffset+8),le(capturedOffset+16),le(capturedOffset+24)),0); }
    public static List<Scene> scenes() {
        return List.of(new Scene("BACKWARD48",Target.BACKWARD,S+8,S,48,M,List.of(
            r128(32),r128(24),w128(S+40,32),w128(S+32,24),r128(8),r128(0),w128(S+8,0),w128(S+16,8)),0));
    }
}
