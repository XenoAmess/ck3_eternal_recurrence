package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.CopyWitnessData370.*;
public final class CopyForwardBook370 {
    private CopyForwardBook370() { }
    private static final long M=0x3300000000L, S=0x2200000000L, D=0x1100000000L;
    private static long le(long offset) { long v=0; for(int i=0;i<8;i++)v|=((offset+i+0x10)&255L)<<(8*i); return v; }
    private static Step r128(long offset) { return new Step(Op.R128,List.of(S+offset,le(offset),le(offset+8)),0); }
    private static Step w128(long address,long capturedOffset) { return new Step(Op.W128,List.of(address,le(capturedOffset),le(capturedOffset+8)),0); }
    private static Step r256(long offset) { return new Step(Op.R256,List.of(S+offset,le(offset),le(offset+8),le(offset+16),le(offset+24)),0); }
    private static Step w256(long address,long capturedOffset) { return new Step(Op.W256,List.of(address,le(capturedOffset),le(capturedOffset+8),le(capturedOffset+16),le(capturedOffset+24)),0); }
    public static List<Scene> scenes() {
        return List.of(
            new Scene("SSE64",Target.SSE,D,S,64,M,List.of(
                r128(0),r128(48),new Step(Op.R32,List.of(M+0x6090088L+4*4,0x04226db1L),0),
                r128(0),w128(D,0),r128(16),w128(D+16,16),r128(32),w128(D+32,32),w128(D+48,48),w128(D,0)),0),
            new Scene("AVX96",Target.AVX,D,S,96,M,List.of(
                r256(0),r256(64),new Step(Op.R32,List.of(M+0x6090040L+3*4,0x04226b33L),0),
                r256(0),w256(D,0),r256(32),w256(D+32,32),w256(D+64,64),w256(D,0)),0));
    }
}
