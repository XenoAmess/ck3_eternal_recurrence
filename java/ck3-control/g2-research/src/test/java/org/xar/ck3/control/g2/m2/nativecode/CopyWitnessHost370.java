package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.CopyWitnessData370.*;
import java.util.ArrayList;
import java.util.EnumSet;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.Copy4226860Api.Bits256;
public final class CopyWitnessHost370 {
    private CopyWitnessHost370() { }
    private static void check(boolean ok,String why) { if(!ok)throw new AssertionError(why); }
    private static final class Script implements Copy4226860Api.Memory {
        final Scene scene; int cursor;
        Script(Scene scene) { this.scene=scene; }
        Step take(Op op,long address,int size) {
            check(cursor<scene.steps().size(),scene.name()+" unexpected "+op);
            Step step=scene.steps().get(cursor++);
            check(step.op()==op&&step.values().size()==size&&step.returned()==0,scene.name()+" step "+cursor+" shape");
            if(size>0)check(step.values().getFirst()==address,scene.name()+" step "+cursor+" address");
            return step;
        }
        long scalar(Op op,long address,long mask) { long value=take(op,address,2).values().get(1); check((value&mask)==value,"noncanonical scalar");return value; }
        void scalarWrite(Op op,long address,long value,long mask) { long expected=take(op,address,2).values().get(1);check((expected&mask)==expected&&(value&mask)==expected,"write value"); }
        public int read8(long a) { return (int)scalar(Op.R8,a,255); }
        public int read16(long a) { return (int)scalar(Op.R16,a,65535); }
        public int read32(long a) { return (int)scalar(Op.R32,a,0xffffffffL); }
        public long read64(long a) { return scalar(Op.R64,a,-1L); }
        public Bits128 read128(long a) { var v=take(Op.R128,a,3).values();return new Bits128(v.get(1),v.get(2)); }
        public Bits256 read256(long a) { var v=take(Op.R256,a,5).values();return new Bits256(new Bits128(v.get(1),v.get(2)),new Bits128(v.get(3),v.get(4))); }
        public void write8(long a,int v) { scalarWrite(Op.W8,a,v,255); }
        public void write16(long a,int v) { scalarWrite(Op.W16,a,v,65535); }
        public void write32(long a,int v) { scalarWrite(Op.W32,a,v,0xffffffffL); }
        public void write64(long a,long v) { scalarWrite(Op.W64,a,v,-1L); }
        public void write128(long a,Bits128 value) { var v=take(Op.W128,a,3).values();check(value.low()==v.get(1)&&value.high()==v.get(2),"write128 bits"); }
        public void write256(long a,Bits256 value) { var v=take(Op.W256,a,5).values();check(value.low128().low()==v.get(1)&&value.low128().high()==v.get(2)&&value.high128().low()==v.get(3)&&value.high128().high()==v.get(4),"write256 bits"); }
        public void storeFence() { take(Op.FENCE,0,0); }
    }
    public static int verify() {
        var scenes=new ArrayList<Scene>();scenes.addAll(CopyBasicBook370.scenes());scenes.addAll(CopyForwardBook370.scenes());scenes.addAll(CopyBackwardBook370.scenes());
        check(scenes.size()==6,"exact six cases");var seen=EnumSet.noneOf(Target.class);int events=0;
        for(Scene scene:scenes) {
            check(seen.add(scene.target()),"duplicate target");check(scene.source()==0x2200000000L&&scene.moduleBase()==0x3300000000L,"source/module input");
            long size=switch(scene.target()) {case SMALL->15;case REP->3;case DISPATCH->17;case SSE->64;case AVX->96;case BACKWARD->48;};
            long destination=switch(scene.target()) {case SMALL,DISPATCH->scene.source()+1;case BACKWARD->scene.source()+8;default->0x1100000000L;};
            check(scene.bytes()==size&&scene.destination()==destination,"exact path input");check(!scene.steps().isEmpty()&&scene.steps().size()<=256,"finite nonempty trace");
            long expected=scene.target()==Target.DISPATCH?destination:0;check(scene.expectedReturn()==expected,"return contract");
            Script memory=new Script(scene);
            switch(scene.target()) {
                case SMALL->PendingCopySmall4226860.copy(memory,destination,scene.source(),size,scene.moduleBase());
                case REP->PendingCopyRep4226840.copy(memory,destination,scene.source(),size);
                case DISPATCH->check(PendingMemoryCopy4226860.copy(memory,destination,scene.source(),size,scene.moduleBase())==expected,"raw dispatch return");
                case SSE->PendingCopySse4226860.copy(memory,destination,scene.source(),size,scene.moduleBase());
                case AVX->PendingCopyAvx4226860.copy(memory,destination,scene.source(),size,scene.moduleBase());
                case BACKWARD->PendingCopyBackward4226860.copy(memory,destination,scene.source(),size);
            }
            check(memory.cursor==scene.steps().size(),scene.name()+" unconsumed trace");events+=memory.cursor;
        }
        check(seen.size()==6,"all targets");System.out.println("cases=6 events="+events);return scenes.size();
    }
    public static void main(String[] args) { verify(); }
}
