package org.xar.ck3.research.m1;

import java.util.List;
import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.*;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.IatCall;

/** Test-local finite strict callback runner; two literal scene providers remain unwritten. */
public final class GovernmentThreadWait179Witness {
    private GovernmentThreadWait179Witness() { }
    public enum Kind { READ_QWORD, WRITE_QWORD, READ_DWORD, WRITE_DWORD, IAT }
    public record Step(Kind kind,long address,long value,IatCall call,VolatileBits returned) { }
    public record Scene(String name,Entry entry,List<Step> steps,NormalReturn expected) { }
    public static Step r(long address,long value) { return new Step(Kind.READ_QWORD,address,value,null,null); }
    public static Step w(long address,long value) { return new Step(Kind.WRITE_QWORD,address,value,null,null); }
    public static Step dr(long address,long value) { return new Step(Kind.READ_DWORD,address,value,null,null); }
    public static Step dw(long address,long value) { return new Step(Kind.WRITE_DWORD,address,value,null,null); }
    public static Step p(IatCall call,VolatileBits returned) { return new Step(Kind.IAT,0,0,call,returned); }
    public static Bits128 x(long a,long b) { return new Bits128(a,b); }
    public static VolatileBits v(long seed) {
        return new VolatileBits(seed,seed+1,seed+2,seed+3,seed+4,seed+5,seed+6,
            x(seed+10,seed+11),x(seed+12,seed+13),x(seed+14,seed+15),
            x(seed+16,seed+17),x(seed+18,seed+19),x(seed+20,seed+21));
    }
    public static NonvolatileBits n(long seed) {
        return new NonvolatileBits(seed,seed+1,seed+2,seed+3,seed+4,seed+5,seed+6,seed+7,x(seed+8,seed+9));
    }
    static final class Script implements GovernmentSharedManager167Api.Memory,GovernmentThreadHeader178Api.Ports {
        private final List<Step> steps;
        private int index;
        Script(List<Step> steps) { this.steps=List.copyOf(steps); }
        private Step next(Kind kind) {
            if(index>=steps.size()) throw new AssertionError("extra "+kind);
            Step value=steps.get(index++);
            if(value.kind()!=kind) throw new AssertionError("step "+(index-1)+" expected "+value.kind()+" got "+kind);
            return value;
        }
        @Override public long readQword(long address) {
            Step step=next(Kind.READ_QWORD);
            if(step.address()!=address) throw new AssertionError("read address "+Long.toHexString(address));
            return step.value();
        }
        @Override public void writeQword(long address,long value) {
            Step step=next(Kind.WRITE_QWORD);
            if(step.address()!=address||step.value()!=value) throw new AssertionError("write mismatch");
        }
        @Override public VolatileBits invokeIat(IatCall call) {
            Step step=next(Kind.IAT);
            if(!step.call().equals(call)) throw new AssertionError("full IAT call mismatch expected "+step.call()+" got "+call);
            return step.returned();
        }
        @Override public int readDword(long a) {
            Step step=next(Kind.READ_DWORD);
            if(step.address()!=a) throw new AssertionError("dword read address");
            return (int)step.value();
        }
        @Override public int readUnsignedByte(long a) { throw new AssertionError("unexpected readUnsignedByte"); }
        @Override public void writeDword(long a,int v) {
            Step step=next(Kind.WRITE_DWORD);
            if(step.address()!=a||step.value()!=Integer.toUnsignedLong(v)) throw new AssertionError("dword write mismatch");
        }
        @Override public int lockedXaddDword(long a,int v) { throw new AssertionError("unexpected lockedXaddDword"); }
        @Override public void writeByte(long a,int v) { throw new AssertionError("unexpected writeByte"); }
        @Override public Bits128 read128(long a) { throw new AssertionError("unexpected read128"); }
        @Override public void write128(long a,Bits128 v) { throw new AssertionError("unexpected write128"); }
        @Override public int lockedXaddByte(long a,int v) { throw new AssertionError("unexpected lockedXaddByte"); }
        @Override public long readGsQword58() { throw new AssertionError("unexpected GS read"); }
        @Override public VolatileBits invoke(OpaqueCall c) { throw new AssertionError("unexpected direct call"); }
        void complete() { if(index!=steps.size()) throw new AssertionError("missing callbacks"); }
    }
    public static void main(String[] args) {
        List<Scene> scenes=List.of(GovernmentThreadWait179FastCase.scene(),GovernmentThreadWait179SlowCase.scene());
        for(Scene scene:scenes) {
            Script script=new Script(scene.steps());
            NormalReturn actual=GovernmentThreadWait179.execute(scene.entry(),script,script);
            if(!actual.equals(scene.expected())||script.index!=scene.steps().size()) throw new AssertionError(scene.name()+" actual="+actual);
        }
        System.out.println("PASS "+scenes.size()+" independently scripted Wait179 branches");
    }
}
