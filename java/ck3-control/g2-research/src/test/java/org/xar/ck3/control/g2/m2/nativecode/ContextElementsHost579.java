package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import static org.xar.ck3.control.g2.m2.nativecode.ContextElementsData579.*;

/** Owner mechanical strict single-RAM/global-cursor fixture; no function semantics. */
public final class ContextElementsHost579 {
    private ContextElementsHost579() { }
    public static void verify(Scene scene) {
        final class Harness implements FullCopy437Api.Memory {
            final Map<Long,Byte> ram=new HashMap<>();
            final UnsupportedOperationException marker=new UnsupportedOperationException("budget marker");
            int cursor;
            Harness() { for (Cell c:scene.initial()) seed(c); }
            void canonical(int width,long value) {
                if (width!=1 && width!=2 && width!=4 && width!=8 && width!=16) throw new AssertionError("fixture width");
                if (width<8 && (value >>> (width*8))!=0) throw new AssertionError("noncanonical DWORD");
            }
            void seed(Cell c) {
                canonical(c.widthBytes(),c.valueBits());
                if(c.widthBytes()!=16 && c.highBits()!=0) throw new AssertionError("scalar high");
                store(Math.min(8,c.widthBytes()),c.addressBits(),c.valueBits());
                if(c.widthBytes()==16) store(8,c.addressBits()+8,c.highBits());
            }
            void store(int width,long address,long value) {
                for(int i=0;i<width;i++) ram.put(address+i,(byte)(value>>>(8*i)));
            }
            long bytes(int width,long address) {
                long value=0;
                for(int i=0;i<width;i++) {
                    Byte v=ram.get(address+i);
                    if(v==null) throw new AssertionError("unseeded byte "+Long.toHexString(address+i));
                    value|=Byte.toUnsignedLong(v)<<(8*i);
                }
                return value;
            }
            Step next() {
                if(cursor>=scene.steps().size()) throw new AssertionError("extra event");
                return scene.steps().get(cursor++);
            }
            long read(int width,long address) {
                long value=bytes(width,address);canonical(width,value);
                if(!new Read(width,address,value).equals(next())) throw new AssertionError("read at event "+(cursor-1));
                return value;
            }
            void write(int width,long address,long value) {
                canonical(width,value);
                if(!new Write(width,address,value).equals(next())) throw new AssertionError("write at event "+(cursor-1));
                store(width,address,value);
            }
            void beforeStep(long header,long guard) {
                Step step=next();
                if(!(step instanceof Budget e) || e.headerRva()!=header || e.guardBits()!=guard)
                    throw new AssertionError("budget at event "+(cursor-1));
                if(e.stop()) throw marker;
            }
            FullCopy437Api.CallResult invoke(EmbeddedElements578Api.CallFrame frame) {
                Step step=next();
                if(!(step instanceof Invoke e) || !frame.equals(e.frame()))
                    throw new AssertionError("whole frame at event "+(cursor-1));
                frame.checkNormalReturn(e.result());
                for(Cell effect:e.effects()) {
                    effect(effect);
                }
                return e.result();
            }
            void effect(Cell c) {
                canonical(c.widthBytes(),c.valueBits());
                if(c.widthBytes()!=16 && c.highBits()!=0) throw new AssertionError("scalar high");
                switch(c.widthBytes()) {
                    case 1 -> writeByte(c.addressBits(),(int)c.valueBits());
                    case 2 -> writeWord(c.addressBits(),(int)c.valueBits());
                    case 4 -> writeDword(c.addressBits(),(int)c.valueBits());
                    case 8 -> writeQword(c.addressBits(),c.valueBits());
                    case 16 -> write128(c.addressBits(),new Bits128(c.valueBits(),c.highBits()));
                    default -> throw new AssertionError();
                }
            }
            FullCopy437Api.CallResult invoke(ContextConstructor543Api.CallFrame frame) {
                Step step=next();
                if(!(step instanceof ForeignInvoke e) || !frame.equals(e.frame()))
                    throw new AssertionError("foreignwholeframe at event "+(cursor-1));
                frame.checkNormalReturn(e.result());
                for(Cell c:e.effects()) effect(c);
                return e.result();
            }
            public int readDword(long a) { return (int)read(4,a); }
            public long readQword(long a) { return read(8,a); }
            public void writeDword(long a,int v) { write(4,a,Integer.toUnsignedLong(v)); }
            public void writeQword(long a,long v) { write(8,a,v); }
            public int readUnsignedByte(long a) { throw new UnsupportedOperationException(); }
            public int readUnsignedWord(long a) { throw new UnsupportedOperationException(); }
            public int lockedXaddDword(long a,int v) { throw new UnsupportedOperationException(); }
            public void writeByte(long a,int v) { write(1,a,v & 0xffL); }
            public void writeWord(long a,int v) { write(2,a,v & 0xffffL); }
            public Bits128 read128(long a) {
                Bits128 value=new Bits128(bytes(8,a),bytes(8,a+8));
                if(!new Read(16,a,value.lowBits(),value.highBits()).equals(next())) throw new AssertionError("R128");
                return value;
            }
            public void write128(long a,Bits128 v) {
                if(!new Write(16,a,v.lowBits(),v.highBits()).equals(next())) throw new AssertionError("W128");
                store(8,a,v.lowBits());store(8,a+8,v.highBits());
            }
            public void write128NonTemporal(long a,Bits128 v) { throw new UnsupportedOperationException(); }
            public FullCopy437Api.Bits256 read256(long a) { throw new UnsupportedOperationException(); }
            public void write256(long a,FullCopy437Api.Bits256 v) { throw new UnsupportedOperationException(); }
            public void write256NonTemporal(long a,FullCopy437Api.Bits256 v) { throw new UnsupportedOperationException(); }
            public void sfence() { throw new UnsupportedOperationException(); }
        }
        Harness h=new Harness();
        FullCopy437Api.CallResult actual=null;
        try {
            actual=ContextConstructorWithKnownEmbeddedElements579.execute(
                new FullCopy437Api.Input(scene.entry(),scene.df(),h::beforeStep),h,h::invoke,h::invoke);
            if(scene.stopped()) throw new AssertionError("missing marker");
        } catch(UnsupportedOperationException ex) {
            if(!scene.stopped() || ex!=h.marker) throw ex;
        }
        if(!scene.stopped() && !scene.expected().equals(actual)) throw new AssertionError("whole result");
        if(h.cursor!=scene.steps().size()) throw new AssertionError("remaining events");
        for(Cell c:scene.finalCells()) {
            h.canonical(c.widthBytes(),c.valueBits());
            if(c.widthBytes()!=16 && c.highBits()!=0) throw new AssertionError("scalarhigh");
            if(h.bytes(Math.min(8,c.widthBytes()),c.addressBits())!=c.valueBits()) throw new AssertionError("finalRAMlow");
            if(c.widthBytes()==16 && h.bytes(8,c.addressBits()+8)!=c.highBits()) throw new AssertionError("finalRAMhigh");
        }
    }
}
