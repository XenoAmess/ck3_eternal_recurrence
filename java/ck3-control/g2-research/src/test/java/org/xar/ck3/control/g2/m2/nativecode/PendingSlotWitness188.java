package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;

/** Test-local strict callback script, owner written after two rejected whole model rounds. */
public final class PendingSlotWitness188 {
    private PendingSlotWitness188() { }
    public enum Op { R8,R32,R64,W8,W32,W64,GROW,PAGE,COPY }
    public record Step(Op op,long address,long second,long value) { }
    public static Step e(Op op,long address,long value) { return new Step(op,address,0,value); }
    public static Step c(Op op,long rcx,long rdx,long value) { return new Step(op,rcx,rdx,value); }
    private static final class Script implements PendingSlotProducer2A32770.Memory,PendingSlotProducer2A32770.Calls {
        private final List<Step> steps;
        private int cursor;
        Script(List<Step> steps) { this.steps=List.copyOf(steps); }
        private Step next(Op op,long address) {
            if(cursor>=steps.size()) throw new AssertionError("extra "+op+"@"+Long.toHexString(address));
            Step step=steps.get(cursor++);
            if(step.op()!=op||step.address()!=address) throw new AssertionError("callback "+(cursor-1)+" expected "+step+" actual="+op+"@"+Long.toHexString(address));
            return step;
        }
        private void write(Op op,long address,long value) {
            Step step=next(op,address);
            if(step.value()!=value) throw new AssertionError("write "+op+" expected "+Long.toHexString(step.value())+" actual "+Long.toHexString(value));
        }
        @Override public int read8(long a) { return (int)next(Op.R8,a).value(); }
        @Override public int read32(long a) { return (int)next(Op.R32,a).value(); }
        @Override public long read64(long a) { return next(Op.R64,a).value(); }
        @Override public void write8(long a,int v) { write(Op.W8,a,v&0xff); }
        @Override public void write32(long a,int v) { write(Op.W32,a,Integer.toUnsignedLong(v)); }
        @Override public void write64(long a,long v) { write(Op.W64,a,v); }
        private Step call(Op op,PendingSlotProducer2A32770.Memory memory,long rcx,long rdx) {
            if(memory!=this) throw new AssertionError("callee crossed exact memory");
            Step step=next(op,rcx);
            if(step.second()!=rdx) throw new AssertionError("callee second argument");
            return step;
        }
        @Override public boolean call1ACDFB0(PendingSlotProducer2A32770.Memory m,long rcx,int edx) { return call(Op.GROW,m,rcx,Integer.toUnsignedLong(edx)).value()==1; }
        @Override public boolean call2A321F0(PendingSlotProducer2A32770.Memory m,long rcx,int edx) { return call(Op.PAGE,m,rcx,Integer.toUnsignedLong(edx)).value()==1; }
        @Override public void call3076B60(PendingSlotProducer2A32770.Memory m,long rcx,long rdx) { call(Op.COPY,m,rcx,rdx); }
    }
    public static void run(String name,PendingSlotProducer2A32770.Input input,List<Step> steps,long expected) {
        Script memory=new Script(steps);
        long actual=PendingSlotProducer2A32770.produce(memory,memory,input);
        if(actual!=expected||memory.cursor!=steps.size()) throw new AssertionError(name+" returned "+Long.toHexString(actual)+" cursor "+memory.cursor+"/"+steps.size());
        System.out.println("PASS "+name+" callbacks="+steps.size());
    }
}
