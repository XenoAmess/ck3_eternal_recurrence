package org.xar.ck3.study.m6.copy4knownreverse203;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.study.m6.copy4add200.Copy4Add200Inputs;
import org.xar.ck3.study.m6.element190.RawMemory190;
import org.xar.ck3.study.m6.range8c194.Range8c194Inputs.Word16;
import org.xar.ck3.study.m6.reverse4220aa4_202.Reverse4220aa4Inputs;

public final class Copy4AddWithKnownReverse203Test {
    private static final long H=0x1000L,D=0x2000L,S=0x3000L,N=0x4000L,A=0x5000L,V=0x6000L;
    private static final long IMAGE=0x140000000L,GLOBAL=IMAGE+0x542f09cL;
    private static int checks;
    private Copy4AddWithKnownReverse203Test() { }
    private record Case(String id,boolean empty,int oldSize,int capacity,int index,int sourceCount,int aliasOffset,int newCapacity,Integer feature,String expectedHeader,String expectedOld,String expectedAllocation,String expectedSource,String expectedCallbacks,String expectedEvents) { }
    private static final class Memory extends RawMemory190 implements Reverse4220aa4Inputs.Memory {
        final List<String> events=new ArrayList<>();
        @Override protected void observed(Access access) {
            if(access.operation().equals("r32") && access.address()==GLOBAL)events.add("f");
            else if(access.bytes()==4 || access.bytes()==8)events.add(access.operation().substring(0,1)+access.bytes()+"@"+Long.toHexString(access.address()));
            else throw new IllegalStateException("unexpected memory width "+access.operation());
        }
        @Override public Word16 read16(long address) {
            events.add("r16@"+Long.toHexString(address));return new Word16(peek64(address),peek64(address+8));
        }
        @Override public void write16(long address,Word16 value) {
            events.add("w16@"+Long.toHexString(address));put64(address,value.lowRaw64());put64(address+8,value.highRaw64());
        }
        @Override public Reverse4220aa4Inputs.Word32 read32Bytes(long address) {
            events.add("r32@"+Long.toHexString(address));return new Reverse4220aa4Inputs.Word32(peek64(address),peek64(address+8),peek64(address+16),peek64(address+24));
        }
        @Override public void write32Bytes(long address,Reverse4220aa4Inputs.Word32 value) {
            events.add("w32@"+Long.toHexString(address));put64(address,value.q0Raw64());put64(address+8,value.q1Raw64());put64(address+16,value.q2Raw64());put64(address+24,value.q3Raw64());
        }
    }
    private static void check(boolean condition,String description) {
        ++checks;if(!condition)throw new IllegalStateException(description);
    }
    private static String hex(long value) { return Long.toHexString(value); }
    private static String words(Memory memory,long base,int count) {
        List<String> values=new ArrayList<>();for(int i=0;i<count;++i)values.add(Integer.toHexString(memory.peek32(base+4L*i)));return String.join(",",values);
    }
    private static String array(String csv) { return csv.isEmpty()?"[]":"[\""+csv.replace(",","\",\"")+"\"]"; }
    private static void guard(Memory memory,long base,int count) { memory.put32(base-4,0x12345678);memory.put32(base+4L*count,0x76543210); }
    private static boolean guarded(Memory memory,long base,int count) { return memory.peek32(base-4)==0x12345678 && memory.peek32(base+4L*count)==0x76543210; }
    private static void run(Case item) {
        Memory memory=new Memory();List<String> callbacks=new ArrayList<>();
        long source=item.aliasOffset()<0?S:D+4L*item.aliasOffset();
        if(!item.empty()) {
            memory.put64(H,D);memory.put32(H+8,item.capacity());memory.put32(H+12,item.oldSize());memory.put64(H+16,A);
            memory.put64(A,V);memory.put64(V+8,0x7000L);memory.put64(V+16,0x7010L);
            for(int i=0;i<item.capacity();++i)memory.put32(D+4L*i,0xcafe0000+i);
            for(int i=0;i<item.oldSize();++i)memory.put32(D+4L*i,0x10+i);
            guard(memory,D,item.capacity());
            if(item.aliasOffset()<0) {
                for(int i=0;i<item.sourceCount();++i)memory.put32(S+4L*i,0x90+i);
                guard(memory,S,item.sourceCount());
            }
            if(item.newCapacity()!=0) {
                for(int i=0;i<item.newCapacity();++i)memory.put32(N+4L*i,0xbeef0000+i);
                guard(memory,N,item.newCapacity());
            }
            if(item.feature()!=null)memory.put32(GLOBAL,item.feature());
        }
        Copy4Add200Inputs.Calls ports=new Copy4Add200Inputs.Calls() {
            @Override public long virtual8(long target,long rcx,long bytes,long alignment,long entryEnd) {
                callbacks.add("alloc:"+hex(target)+":"+hex(rcx)+":"+hex(bytes)+":"+hex(alignment)+":"+hex(entryEnd));return N;
            }
            @Override public void virtual16(long target,long rcx,long oldBase,long alignment) {
                callbacks.add("free:"+hex(target)+":"+hex(rcx)+":"+hex(oldBase)+":"+hex(alignment));
            }
            @Override public void copy4226860(long destination,long from,long bytes) {
                callbacks.add("copy:"+hex(destination)+":"+hex(from)+":"+hex(bytes));
                if(bytes<0 || bytes>80)throw new IllegalStateException("unfrozen COPY size");
                byte[] snapshot=new byte[(int)bytes];
                for(int i=0;i<snapshot.length;++i)snapshot[i]=(byte)memory.peek8(from+i);
                for(int i=0;i<snapshot.length;++i)memory.put8(destination+i,snapshot[i]);
            }
            @Override public void range9d0950(long begin,long middle,long end,long base) {
                throw new IllegalStateException("known range wrongly delegated");
            }
        };
        Copy4Add200Inputs.Input input=item.empty()?new Copy4Add200Inputs.Input(0x77770000L,2,0x33330000L,0x33330000L):new Copy4Add200Inputs.Input(H,item.index(),source,source+4L*item.sourceCount());
        Copy4AddWithKnownReverse203.apply(input,memory,ports,IMAGE,()->memory.events.add("z"));
        String header=item.empty()?"null":hex(memory.peek64(H))+","+Integer.toHexString(memory.peek32(H+8))+","+Integer.toHexString(memory.peek32(H+12))+","+hex(memory.peek64(H+16));
        String oldWords=item.empty()?"":words(memory,D,item.capacity());
        String allocationWords=words(memory,N,item.newCapacity());
        String sourceWords=item.empty()?"":words(memory,source,item.sourceCount());
        check(header.equals(item.expectedHeader()),item.id()+" header "+header);
        check(oldWords.equals(item.expectedOld()),item.id()+" oldRAM "+oldWords);
        check(allocationWords.equals(item.expectedAllocation()),item.id()+" allocationRAM "+allocationWords);
        check(sourceWords.equals(item.expectedSource()),item.id()+" sourceRAM "+sourceWords);
        check(String.join(",",callbacks).equals(item.expectedCallbacks()),item.id()+" typedcallbacks "+callbacks);
        check(String.join(",",memory.events).equals(item.expectedEvents()),item.id()+" exactwidth/order "+memory.events);
        if(!item.empty())check(guarded(memory,D,item.capacity()) && (item.aliasOffset()>=0 || guarded(memory,S,item.sourceCount())) && (item.newCapacity()==0 || guarded(memory,N,item.newCapacity())),item.id()+" boundaryguards");
        String headerJson="null";
        if(!item.empty()) {
            String[] fields=header.split(",");headerJson="{\"baseHex\":\""+fields[0]+"\",\"capacityHex\":\""+fields[1]+"\",\"sizeHex\":\""+fields[2]+"\",\"allocatorHex\":\""+fields[3]+"\"}";
        }
        System.out.println("{\"id\":\""+item.id()+"\",\"headerAfter\":"+headerJson+",\"oldWordsHex\":"+array(oldWords)+",\"allocationWordsHex\":"+array(allocationWords)+",\"sourceWordsHex\":"+array(sourceWords)+",\"callbacks\":"+array(String.join(",",callbacks))+",\"events\":"+array(String.join(",",memory.events))+"}");
    }
    public static void main(String[] args) {
        Case[] cases={
            new Case("empty_unseeded_header",true,0,0,0,0,-1,0,null,"null","","","","",""),
            new Case("middle_three",false,5,12,2,3,-1,0,null,"2000,c,8,5000","10,11,90,91,92,12,13,14,cafe0008,cafe0009,cafe000a,cafe000b","","90,91,92","copy:2014:3000:c","r4@100c,r4@1008,r8@1000,r4@100c,r8@1000,w4@100c,r4@2008,r4@2010,w4@2008,w4@2010,r4@2014,r4@201c,w4@2014,w4@201c,r4@2008,r4@201c,w4@2008,w4@201c,r4@200c,r4@2018,w4@200c,w4@2018,r4@2010,r4@2014,w4@2010,w4@2014"),
            new Case("append_no_reverse",false,5,12,5,3,-1,0,null,"2000,c,8,5000","10,11,12,13,14,90,91,92,cafe0008,cafe0009,cafe000a,cafe000b","","90,91,92","copy:2014:3000:c","r4@100c,r4@1008,r8@1000,r4@100c,r8@1000,w4@100c"),
            new Case("front_avx",false,9,20,0,9,-1,0,0x28,"2000,14,12,5000","90,91,92,93,94,95,96,97,98,10,11,12,13,14,15,16,17,18,cafe0012,cafe0013","","90,91,92,93,94,95,96,97,98","copy:2024:3000:24","r4@100c,r4@1008,r8@1000,r4@100c,r8@1000,w4@100c,r16@2000,r16@2014,w16@2000,w16@2014,r16@2024,r16@2038,w16@2024,w16@2038,f,r32@2000,r32@2028,w32@2000,w32@2028,z,r4@2020,r4@2024,w4@2020,w4@2024"),
            new Case("capacity_exact",false,6,9,1,3,-1,0,null,"2000,9,9,5000","10,90,91,92,11,12,13,14,15","","90,91,92","copy:2018:3000:c","r4@100c,r4@1008,r8@1000,r4@100c,r8@1000,w4@100c,r4@2004,r4@2014,w4@2004,w4@2014,r4@2008,r4@2010,w4@2008,w4@2010,r4@2018,r4@2020,w4@2018,w4@2020,r16@2004,r16@2014,w16@2004,w16@2014"),
            new Case("source_alias_old_words",false,5,10,2,3,1,0,null,"2000,a,8,5000","10,11,11,12,13,12,13,14,cafe0008,cafe0009","","11,11,12","copy:2014:2004:c","r4@100c,r4@1008,r8@1000,r4@100c,r8@1000,w4@100c,r4@2008,r4@2010,w4@2008,w4@2010,r4@2014,r4@201c,w4@2014,w4@201c,r4@2008,r4@201c,w4@2008,w4@201c,r4@200c,r4@2018,w4@200c,w4@2018,r4@2010,r4@2014,w4@2010,w4@2014"),
            new Case("growth_passthrough",false,4,4,2,2,-1,6,null,"4000,6,6,5000","10,11,12,13","10,11,90,91,12,13","90,91","alloc:7000:5000:18:4:3008,copy:4000:2000:8,copy:4008:3000:8,copy:4010:2008:8,free:7010:5000:2000:4","r4@100c,r4@1008,r8@1010,r8@5000,r8@6008,r8@1000,r8@1000,r4@100c,r8@1010,r8@1000,r8@5000,r8@6010,w8@1000,w4@1008,w4@100c")
        };
        for(Case item:cases)run(item);
        System.out.println("{\"cases\":"+cases.length+",\"checks\":"+checks+",\"failures\":0}");
    }
}
