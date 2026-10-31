package org.xar.ck3.research.m5;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentNormalizeWithCrt187WitnessApi.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** R2 byte utilities reused; owner separates actual GS and budget domains. */
public final class GovernmentNormalizeWithCrt187Probe {
    private GovernmentNormalizeWithCrt187Probe() { }
    public static void main(String[] args) {
        check(args.length==0,"no arguments");verify(new GovernmentNormalizeWithCrt187Fixtures());
    }
    public static void verify(Book book) {
        check(book.witnesses().size()==1,"one witness");
        Witness w=book.witnesses().get(0);check(!w.name().isBlank(),"name");
        Recorder rec=new Recorder(w);
        GovernmentPrimaryTail155Api.Calls ordinary=new GovernmentPrimaryTail155Api.Calls() {
            @Override public VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                throw new AssertionError("unexpected ordinary opaque");
            }
            @Override public long readGsQword58() { return rec.gs(Port.ORDINARY); }
        };
        GovernmentCrtBoundary185Api.Calls crt=new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                CrtCallStep e=rec.next(CrtCallStep.class);
                check(call.equals(e.expected()),"CRT call frame");
                check(rec.bytes.equals(e.expectedMemoryBefore()),"CRT call complete image");
                rec.mutate(e.mutation());return e.normalPost();
            }
            @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                CrtTailStep e=rec.next(CrtTailStep.class);
                check(transfer.equals(e.expected()),"CRT tail frame");
                check(rec.bytes.equals(e.expectedMemoryBefore()),"CRT tail complete image");
                rec.mutate(e.mutation());return e.normalPost();
            }
            @Override public long readGsQword58() { return rec.gs(Port.CRT); }
        };
        var actual=GovernmentNormalizeWithCrt187.execute(w.entry(),rec,ordinary,
                (header,node,end)->{throw new AssertionError("unexpected helper loop");},
                pause->{throw new AssertionError("unexpected token pause");},
                (header,lock)->{throw new AssertionError("unexpected token loop");},crt,
                (header,guard)->{CrtLoopStep e=rec.next(CrtLoopStep.class);
                    check(header==e.loopHeaderRva() && guard==e.guardAddressBits(),"CRT loop fields");});
        check(actual.equals(w.expected()),"full NormalReturn");
        check(rec.cursor==w.events().size(),"all events consumed");
        Map<Long,Integer> end=new HashMap<>(w.memorySeed());validate(w.expectedFinalBytes());
        end.putAll(w.expectedFinalBytes());check(rec.bytes.equals(end),"exact final image");
        System.out.println("cases=1");
    }
    private static void check(boolean b,String why) { if(!b) throw new AssertionError(why); }
    private static void validate(Map<Long,Integer> image) {
        for(int value:image.values()) check(value>=0 && value<=255,"literal byte range");
    }
    private static final class Recorder implements GovernmentNormalizeWithCrt187Api.Memory {
        final Map<Long,Integer> bytes;
        final List<Event> events;
        int cursor;
        Recorder(Witness w) {
            validate(w.memorySeed());bytes=new HashMap<>(w.memorySeed());events=w.events();
        }
        <T extends Event> T next(Class<T> type) {
            check(cursor<events.size(),"event overflow");Event e=events.get(cursor++);
            check(type.isInstance(e),"event kind");return type.cast(e);
        }
        long gs(Port actualPort) {
            GsStep e=next(GsStep.class);check(e.port()==actualPort,"GS domain");return e.returnedBits();
        }
        void mutate(Map<Long,Integer> change) { validate(change);bytes.putAll(change); }
        private long read(long addressBits, int width) {
            long v = 0;
            for (int i = 0; i < width; i++) {
                Integer b = bytes.get(addressBits + i);
                if (b == null) throw new AssertionError("missingbyte");
                v |= ((long) b) << (i * 8);
            }
            return v;
        }

        private void write(long addressBits, long valueBits, int width) {
            for (int i = 0; i < width; i++) {
                bytes.put(addressBits + i, (int) ((valueBits >>> (i * 8)) & 0xFF));
            }
        }


        @Override public int readDword(long a) { return (int)read(a,4); }
        @Override public long readQword(long a) { return read(a,8); }
        @Override public int readUnsignedByte(long a) { return (int)read(a,1); }
        @Override public int readUnsignedWord(long a) { return (int)read(a,2); }
        @Override public void writeDword(long a,int n) { write(a,n,4); }
        @Override public void writeQword(long a,long n) { write(a,n,8); }
        @Override public void writeByte(long a,int n) { write(a,n,1); }
        @Override public void writeWord(long a,int n) { write(a,n,2); }
        @Override public Bits128 read128(long a) { return new Bits128(read(a,8),read(a+8L,8)); }
        @Override public void write128(long a,Bits128 n) { write(a,n.lowBits(),8);write(a+8L,n.highBits(),8); }
        @Override public int lockedXaddDword(long a,int addend) {
            AtomicStep e=next(AtomicStep.class);int old=readDword(a),stored=old+addend;
            check(e.addressBits()==a && e.addendBits()==addend && e.oldBits()==old && e.storedBits()==stored,"atomic fields/values");
            writeDword(a,stored);return old;
        }
    }
}
