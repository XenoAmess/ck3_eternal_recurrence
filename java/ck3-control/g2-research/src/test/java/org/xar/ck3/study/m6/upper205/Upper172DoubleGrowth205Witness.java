package org.xar.ck3.study.m6.upper205;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.StringJoiner;
import org.xar.ck3.study.m6.copy4add200.Copy4Add200Inputs;
import org.xar.ck3.study.m6.copy4add200.Element172WithKnownCopy4Add200;
import org.xar.ck3.study.m6.element172.Element172Inputs;
import org.xar.ck3.study.m6.element190.RawMemory190;
import org.xar.ck3.study.m6.range8c194.Range8c194Inputs;

/** Two new bounded same-RAM witnesses using the existing mature production composition. */
public final class Upper172DoubleGrowth205Witness {
    private static final long IMAGE=0x10000000L,D=0x1000,S=0x2000;
    private static final long N16=0x4000,N4=0x5000,S16=0x6000,S4=0x7000,V16=0x9000,V4=0xA000;
    private static final long TA16=0xB008,FA16=0xB010,TA4=0xC008,FA4=0xC010;
    private static final long ALLOC16=IMAGE+0x54DE260L,ALLOC4=IMAGE+0x54DE268L;
    private static int checks;
    private Upper172DoubleGrowth205Witness() { }
    private static void check(boolean value,String reason) {
        ++checks;if(!value)throw new AssertionError(reason);
    }
    private static final class Memory extends RawMemory190 implements Range8c194Inputs.Memory {
        @Override public Range8c194Inputs.Word16 read16(long address) {
            return new Range8c194Inputs.Word16(peek64(address),peek64(address+8));
        }
        @Override public void write16(long address,Range8c194Inputs.Word16 word) {
            put64(address,word.lowRaw64());put64(address+8,word.highRaw64());
        }
    }
    private record Header(String base,int capacity,int size,String allocatorRvaHex) {
        String json() {
            return "{"+field("base",quote(base))+","+field("capacity",Integer.toString(capacity))+","
                +field("size",Integer.toString(size))+","+field("allocatorRvaHex",quote(allocatorRvaHex))+"}";
        }
    }
    private record Call(String kind,String target,List<String> args) {
        String json() {
            StringJoiner values=new StringJoiner(",","[","]");for(String value:args)values.add(quote(value));
            return "{"+field("kind",quote(kind))+","+field("target",quote(target))+","+field("args",values.toString())+"}";
        }
    }
    private static final class Snapshots { Header before16,before4; }
    private static String quote(String text) { return "\""+text.replace("\\","\\\\").replace("\"","\\\"")+"\""; }
    private static String field(String key,String json) { return quote(key)+":"+json; }
    private static String pointer(long value) {
        if(value==0)return "NULL";if(value==ALLOC16)return "ALLOC16";if(value==ALLOC4)return "ALLOC4";
        long[] bases={D,S,N16,N4,S16,S4};String[] names={"D","S","N16","N4","S16","S4"};
        for(int i=0;i<bases.length;++i) {
            long offset=value-bases[i];if(offset>=0 && offset<(i<2?128:64))return names[i]+"+"+offset;
        }
        throw new AssertionError("unqualified pointer "+Long.toHexString(value));
    }
    private static String target(long value) {
        if(value==TA16)return "TA16";if(value==FA16)return "FA16";
        if(value==TA4)return "TA4";if(value==FA4)return "FA4";
        throw new AssertionError("unqualified target "+Long.toHexString(value));
    }
    private static Call call(String kind,long target,long... values) {
        int arity=switch(kind) { case "a16","f16","a4" -> 4;case "c4","f4" -> 3;default -> throw new AssertionError("unknown call kind"); };
        check(values.length==arity,"actual typed port arity");
        List<String> args=new ArrayList<>();
        for(int i=0;i<values.length;++i) {
            boolean isPointer=switch(kind) { case "a16","a4" -> i==0 || i==3;case "f16" -> i!=2;case "c4","f4" -> i<2;default -> throw new AssertionError("unknown call kind"); };
            args.add(isPointer?pointer(values[i]):String.format(Locale.ROOT,"0x%016x",values[i]));
        }
        if(kind.equals("c4")) { check(target==0,"metadata COPY has no virtual target");return new Call(kind,"",List.copyOf(args)); }
        return new Call(kind,target(target),List.copyOf(args));
    }
    private static Header header(Memory memory,long address) {
        return new Header(pointer(memory.peek64(address)),memory.peek32(address+8),memory.peek32(address+12),Long.toHexString(memory.peek64(address+16)-IMAGE));
    }
    private static String bytes(Memory memory,long address,int count) {
        StringBuilder out=new StringBuilder();for(int i=0;i<count;++i)out.append(String.format(Locale.ROOT,"%02x",memory.peek8(address+i)));return out.toString();
    }
    private static String run(String id,boolean headerAlias,int count16,int count4) {
        Memory memory=new Memory();memory.fill(0x1000,0xA000,0xA5);
        for(int i=0;i<32;++i)memory.put8(S16+i,0x10+i);
        for(int i=0;i<16;++i)memory.put8(S4+i,0x70+i);
        for(int i=0;i<4;++i)memory.put8(D+0x45+i,0xC5+i);
        long begin16=headerAlias?D+0x10:S16;
        memory.put32(S+8,0x81234567);memory.put64(S+0x10,begin16);memory.put32(S+0x1C,count16);
        memory.put64(S+0x28,S4);memory.put32(S+0x34,count4);memory.put32(S+0x40,0x76543210);memory.put8(S+0x44,0xA5);
        memory.put64(ALLOC16,V16);memory.put64(ALLOC4,V4);
        memory.put64(V16+8,TA16);memory.put64(V16+16,FA16);memory.put64(V4+8,TA4);memory.put64(V4+16,FA4);
        List<Call> calls=new ArrayList<>();Snapshots snapshots=new Snapshots();
        Range8c194Inputs.Calls rangeCalls=new Range8c194Inputs.Calls() {
            @Override public long virtual8(long target,long rcx,long rdx,long r8,long r9) {
                check(target==TA16 && rcx==ALLOC16,"actual 16-byte allocator binding");
                calls.add(call("a16",target,rcx,rdx,r8,r9));return N16;
            }
            @Override public void virtual16(long target,long rcx,long rdx,long r8,long r9) {
                check(target==FA16 && rcx==ALLOC16 && snapshots.before16==null,"actual 16-byte release binding");
                snapshots.before16=header(memory,D+0x10);calls.add(call("f16",target,rcx,rdx,r8,r9));
            }
            @Override public void direct8f8550(long rcx,long rdx,long r8,long r9) { throw new AssertionError("unreachable 8F port"); }
        };
        Copy4Add200Inputs.Calls copyCalls=new Copy4Add200Inputs.Calls() {
            @Override public long virtual8(long target,long rcx,long rdx,long r8,long r9) {
                check(target==TA4 && rcx==ALLOC4,"actual 4-byte allocator binding");
                calls.add(call("a4",target,rcx,rdx,r8,r9));return N4;
            }
            @Override public void virtual16(long target,long rcx,long rdx,long r8) {
                check(target==FA4 && rcx==ALLOC4 && snapshots.before4==null,"actual 4-byte release binding");
                snapshots.before4=header(memory,D+0x28);calls.add(call("f4",target,rcx,rdx,r8));
            }
            @Override public void copy4226860(long destination,long source,long count) {
                calls.add(call("c4",0,destination,source,count));
            }
            @Override public void range9d0950(long begin,long middle,long end,long base) { throw new AssertionError("unreachable 9D port"); }
        };
        long returned=Element172WithKnownCopy4Add200.assign(new Element172Inputs.Input(D,S,IMAGE),memory,rangeCalls,copyCalls);
        check(returned==D,"full64 parent return");check(calls.size()==7,"both growth branches actually reached");
        check(snapshots.before16!=null && snapshots.before4!=null,"both actual release snapshots");
        for(int i=0;i<4;++i)check(memory.peek8(D+0x45+i)==0xC5+i,"destination padding");
        for(int i=count16*16;i<64;++i)check(memory.peek8(N16+i)==0xA5,"16-byte buffer boundary");
        for(int i=0;i<64;++i)check(memory.peek8(N4+i)==0xA5,"metadata COPY has no RAM effect");
        for(int i=0;i<32;++i)check(memory.peek8(S16+i)==0x10+i,"source16 guard");
        for(int i=0;i<16;++i)check(memory.peek8(S4+i)==0x70+i,"source4 guard");
        StringJoiner logs=new StringJoiner(",","[","]");for(Call entry:calls)logs.add(entry.json());
        return "{"+String.join(",",field("id",quote(id)),field("returnedDestination",Boolean.toString(returned==D)),
            field("vptrRvaHex",quote(Long.toHexString(memory.peek64(D)-IMAGE))),
            field("kindHex",quote(Integer.toHexString(memory.peek32(D+8)))),field("tailHex",quote(Integer.toHexString(memory.peek32(D+0x40)))),field("flagHex",quote(Integer.toHexString(memory.peek8(D+0x44)))),
            field("header16",header(memory,D+0x10).json()),field("header4",header(memory,D+0x28).json()),
            field("release16SnapshotTaken",Boolean.toString(snapshots.before16!=null)),field("release4SnapshotTaken",Boolean.toString(snapshots.before4!=null)),
            field("beforeRelease16",snapshots.before16==null?"null":snapshots.before16.json()),field("beforeRelease4",snapshots.before4==null?"null":snapshots.before4.json()),
            field("buffer16Hex",quote(bytes(memory,N16,32))),field("buffer4Hex",quote(bytes(memory,N4,16))),field("calls",logs.toString()))+"}";
    }
    public static void main(String[] args) {
        String first=run("separate_double_growth",false,2,2);
        String second=run("source16_header_alias_double_growth",true,1,1);
        System.out.println("{\"rows\":["+first+","+second+"]}");
        System.err.println("Upper172DoubleGrowth205Witness cases=2 checks="+checks+" failures=0; controlled-port bounded DATA");
    }
}
