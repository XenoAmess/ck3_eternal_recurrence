package org.xar.ck3.study.m6.reverse4220aa4_202;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.study.m6.element190.RawMemory190;
import org.xar.ck3.study.m6.range8c194.Range8c194Inputs.Word16;
import org.xar.ck3.study.m6.range9d201.Range9d201Inputs;

public final class Reverse4220aa4CandidateTest {
    private static final long BASE=0x10000L, IMAGE=0x140000000L, GLOBAL=IMAGE+0x542f09cL;
    private static int checks;
    private Reverse4220aa4CandidateTest() { }
    private record Case(String id,int words,int split,boolean whole,Integer feature,long rax,String expectedWords,String expectedTrace) { }
    private static final class Memory extends RawMemory190 implements Reverse4220aa4Inputs.Memory {
        final List<String> trace=new ArrayList<>();
        private String offset(long address) { return Long.toString(address-BASE); }
        @Override protected void observed(Access access) {
            if (access.operation().equals("r32")) trace.add(access.address()==GLOBAL ? "f" : "r4@"+offset(access.address()));
            else if (access.operation().equals("w32")) trace.add("w4@"+offset(access.address()));
            else throw new IllegalStateException("unexpected scalar width "+access.operation());
        }
        @Override public Word16 read16(long address) {
            trace.add("r16@"+offset(address));
            return new Word16(peek64(address),peek64(address+8));
        }
        @Override public void write16(long address,Word16 value) {
            trace.add("w16@"+offset(address));
            put64(address,value.lowRaw64());put64(address+8,value.highRaw64());
        }
        @Override public Reverse4220aa4Inputs.Word32 read32Bytes(long address) {
            trace.add("r32@"+offset(address));
            return new Reverse4220aa4Inputs.Word32(peek64(address),peek64(address+8),peek64(address+16),peek64(address+24));
        }
        @Override public void write32Bytes(long address,Reverse4220aa4Inputs.Word32 value) {
            trace.add("w32@"+offset(address));
            put64(address,value.q0Raw64());put64(address+8,value.q1Raw64());
            put64(address+16,value.q2Raw64());put64(address+24,value.q3Raw64());
        }
    }
    private static void check(boolean condition,String message) {
        ++checks;if(!condition)throw new IllegalStateException(message);
    }
    private static String jsonArray(String csv) {
        return csv.isEmpty() ? "[]" : "[\""+csv.replace(",","\",\"")+"\"]";
    }
    private static void run(Case item) {
        Memory memory=new Memory();
        for(int i=0;i<item.words();++i)memory.put32(BASE+i*4L,0x80000010+i);
        memory.put32(BASE-4,0x11223344);memory.put32(BASE+item.words()*4L,0x55667788);
        if(item.feature()!=null)memory.put32(GLOBAL,item.feature());
        Reverse4220aa4Inputs.Effects effects=()->memory.trace.add("z");
        long result=item.whole()
                ? Range9dWithKnown4220aa4_202.apply(new Range9d201Inputs.Input(BASE,BASE+item.split()*4L,BASE+item.words()*4L,0x77770000L),memory,IMAGE,effects)
                : Reverse4220aa4Candidate.apply(new Reverse4220aa4Inputs.Input(BASE,BASE+item.words()*4L,IMAGE),memory,effects);
        StringBuilder words=new StringBuilder();
        for(int i=0;i<item.words();++i) {
            if(i!=0)words.append(',');words.append(Integer.toHexString(memory.peek32(BASE+i*4L)));
        }
        String trace=String.join(",",memory.trace);
        check(result==item.rax(),item.id()+" full rawRAX "+Long.toHexString(result));
        check(words.toString().equals(item.expectedWords()),item.id()+" final sameRAM DWORDs");
        check(trace.equals(item.expectedTrace()),item.id()+" exact instruction-width/feature/zeroUpper order "+trace);
        check(memory.peek32(BASE-4)==0x11223344,item.id()+" leftguard");
        check(memory.peek32(BASE+item.words()*4L)==0x55667788,item.id()+" rightguard");
        System.out.println("{\"id\":\""+item.id()+"\",\"rax\":\""+Long.toHexString(result)+"\",\"wordsHex\":"+jsonArray(words.toString())+",\"trace\":"+jsonArray(trace)+"}");
    }
    public static void main(String[] args) {
        Case[] cases={
            new Case("n0_short_unseeded",0,0,false,null,0x0L,"",""),
            new Case("n1_short_unseeded",1,0,false,null,0x4L,"80000010",""),
            new Case("n2_short_unseeded",2,0,false,null,0x80000011L,"80000011,80000010","r4@0,r4@4,w4@0,w4@4"),
            new Case("n7_short_unseeded",7,0,false,null,0x80000014L,"80000016,80000015,80000014,80000013,80000012,80000011,80000010","r4@0,r4@24,w4@0,w4@24,r4@4,r4@20,w4@4,w4@20,r4@8,r4@16,w4@8,w4@16"),
            new Case("n8_short_unseeded",8,0,false,null,0x10010L,"80000017,80000016,80000015,80000014,80000013,80000012,80000011,80000010","r16@0,r16@16,w16@0,w16@16"),
            new Case("n9_short_unseeded",9,0,false,null,0x10010L,"80000018,80000017,80000016,80000015,80000014,80000013,80000012,80000011,80000010","r16@0,r16@20,w16@0,w16@20"),
            new Case("n10_short_unseeded",10,0,false,null,0x80000015L,"80000019,80000018,80000017,80000016,80000015,80000014,80000013,80000012,80000011,80000010","r16@0,r16@24,w16@0,w16@24,r4@16,r4@20,w4@16,w4@20"),
            new Case("n16_bit5_off_otherbit_on",16,0,false,0x40000000,0x10020L,"8000001f,8000001e,8000001d,8000001c,8000001b,8000001a,80000019,80000018,80000017,80000016,80000015,80000014,80000013,80000012,80000011,80000010","f,r16@0,r16@48,w16@0,w16@48,r16@16,r16@32,w16@16,w16@32"),
            new Case("n16_bit5_on",16,0,false,0x28,0x0L,"8000001f,8000001e,8000001d,8000001c,8000001b,8000001a,80000019,80000018,80000017,80000016,80000015,80000014,80000013,80000012,80000011,80000010","f,r32@0,r32@32,w32@0,w32@32,z"),
            new Case("n17_bit5_on",17,0,false,0x28,0x4L,"80000020,8000001f,8000001e,8000001d,8000001c,8000001b,8000001a,80000019,80000018,80000017,80000016,80000015,80000014,80000013,80000012,80000011,80000010","f,r32@0,r32@36,w32@0,w32@36,z"),
            new Case("n18_bit5_on",18,0,false,0x28,0x80000019L,"80000021,80000020,8000001f,8000001e,8000001d,8000001c,8000001b,8000001a,80000019,80000018,80000017,80000016,80000015,80000014,80000013,80000012,80000011,80000010","f,r32@0,r32@40,w32@0,w32@40,z,r4@32,r4@36,w4@32,w4@36"),
            new Case("n24_bit5_on",24,0,false,0x28,0x10030L,"80000027,80000026,80000025,80000024,80000023,80000022,80000021,80000020,8000001f,8000001e,8000001d,8000001c,8000001b,8000001a,80000019,80000018,80000017,80000016,80000015,80000014,80000013,80000012,80000011,80000010","f,r32@0,r32@64,w32@0,w32@64,z,r16@32,r16@48,w16@32,w16@48"),
            new Case("whole8_split3",8,3,true,null,0x10014L,"80000013,80000014,80000015,80000016,80000017,80000010,80000011,80000012","r4@0,r4@8,w4@0,w4@8,r4@12,r4@28,w4@12,w4@28,r4@16,r4@24,w4@16,w4@24,r16@0,r16@16,w16@0,w16@16"),
            new Case("whole24_split8",24,8,true,0x28,0x10040L,"80000018,80000019,8000001a,8000001b,8000001c,8000001d,8000001e,8000001f,80000020,80000021,80000022,80000023,80000024,80000025,80000026,80000027,80000010,80000011,80000012,80000013,80000014,80000015,80000016,80000017","r16@0,r16@16,w16@0,w16@16,f,r32@32,r32@64,w32@32,w32@64,z,f,r32@0,r32@64,w32@0,w32@64,z,r16@32,r16@48,w16@32,w16@48")
        };
        for(Case item:cases)run(item);
        System.out.println("{\"cases\":"+cases.length+",\"checks\":"+checks+",\"failures\":0}");
    }
}
