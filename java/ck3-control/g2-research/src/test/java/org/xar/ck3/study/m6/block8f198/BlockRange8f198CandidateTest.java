package org.xar.ck3.study.m6.block8f198;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.study.m6.element190.RawMemory190;
import org.xar.ck3.study.m6.range8c194.Range8c194Inputs;

/** Portable bounded DATA main; does not execute the game or native code. */
public final class BlockRange8f198CandidateTest {
    private static final long BASE=0x1003L;
    private static int checks;
    private BlockRange8f198CandidateTest() { }

    private static final class Memory extends RawMemory190 implements Range8c194Inputs.Memory {
        final List<String> events=new ArrayList<>();
        @Override protected void observed(Access access) {
            events.add(access.operation()+":"+Long.toUnsignedString(access.address(),16));
        }
        @Override public Range8c194Inputs.Word16 read16(long address) {
            Range8c194Inputs.Word16 word=new Range8c194Inputs.Word16(peek64(address),peek64(address+8));
            events.add("r16:"+Long.toUnsignedString(address,16));
            return word;
        }
        @Override public void write16(long address,Range8c194Inputs.Word16 word) {
            events.add("w16:"+Long.toUnsignedString(address,16));
            put64(address,word.lowRaw64());put64(address+8,word.highRaw64());
        }
    }

    private static void check(boolean condition,String message) {
        ++checks;if(!condition)throw new AssertionError(message);
    }
    private static long address(int index) { return index==-1 ? 0 : BASE+16L*index; }
    private static void seed(Memory memory,long address,int word) {
        memory.put64(address,0x1100L+word);memory.put64(address+8,0x2200L+word);
    }
    private static void word(Memory memory,long address,int expected,String label) {
        check(memory.peek64(address)==0x1100L+expected && memory.peek64(address+8)==0x2200L+expected,label);
    }

    public static void main(String[] args) {
        String[] names={"null_first","null_second","two","left2","left3","offset"};
        int[][] ranges={{-1,-1,-1},{-1,6,6},{0,1,2},{0,2,5},{0,3,5},{1,3,6}};
        int[] results={-1,-1,1,3,2,4};
        int[][] literal={{0,1,2,3,4,5},{0,1,2,3,4,5},{1,0,2,3,4,5},{2,3,4,0,1,5},{3,4,0,1,2,5},{0,3,4,5,1,2}};
        for(int c=0;c<names.length;++c) {
            Memory memory=new Memory();
            memory.fill(BASE-32,32,0xA5);memory.fill(BASE+96,32,0xA5);
            for(int i=0;i<6;++i)seed(memory,address(i),i);
            int[] r=ranges[c];
            long actual=BlockRange8f198Candidate.apply(new BlockRange8f198Inputs.Input(address(r[0]),address(r[1]),address(r[2]),0xF123456789ABCDEFL),memory);
            check(actual==address(results[c]),names[c]+" exact RAX");
            if(c<2)check(memory.events.isEmpty(),names[c]+" must not access memory");
            if(c==2)check(memory.events.equals(List.of("r16:1003","r16:1013","w16:1003","w16:1013")),"two swap reads both complete values before writing");
            for(int i=0;i<6;++i)word(memory,address(i),literal[c][i],names[c]+" whole word "+i);
            boolean guard=true;
            for(int i=0;i<32;++i)guard &= memory.peek8(BASE-32+i)==0xA5 && memory.peek8(BASE+96+i)==0xA5;
            check(guard,names[c]+" guard bytes");
        }

        Memory untouched=new Memory();
        long highBegin=Long.MIN_VALUE+3, highEnd=Long.MAX_VALUE-12;
        check(BlockRange8f198Candidate.apply(new BlockRange8f198Inputs.Input(highBegin,highBegin,highEnd,0),untouched)==highEnd,"first early return preserves full64bits");
        check(BlockRange8f198Candidate.apply(new BlockRange8f198Inputs.Input(highBegin,highEnd,highEnd,0),untouched)==highBegin,"second early return preserves full64bits");
        check(untouched.events.isEmpty(),"both raw64 early returns do not dereference");

        Memory memory=new Memory();
        long header=0x5000,source=0x7003,allocator=0x9000;
        memory.put64(header,BASE);memory.put32(header+8,8);memory.put32(header+12,4);memory.put64(header+16,allocator);
        for(int i=0;i<4;++i)seed(memory,address(i),i);
        seed(memory,source,4);seed(memory,source+16,5);
        int[] virtualCalls={0};
        Range8cWithKnownBlock198.apply(new Range8c194Inputs.Input(header,1,source,source+32),memory,new Range8cWithKnownBlock198.Calls() {
            @Override public long virtual8(long target,long rcx,long rdx,long r8,long r9) {
                ++virtualCalls[0];throw new AssertionError("unexpected allocator call");
            }
            @Override public void virtual16(long target,long rcx,long rdx,long r8,long r9) {
                ++virtualCalls[0];throw new AssertionError("unexpected release call");
            }
        });
        int[] inserted={0,4,5,1,2,3};
        for(int i=0;i<6;++i)word(memory,address(i),inserted[i],"real194 to154 insertion "+i);
        check(memory.peek64(header)==BASE,"binding preserves buffer");
        check(memory.peek32(header+8)==8,"binding preserves capacity");
        check(memory.peek32(header+12)==6,"binding updates size");
        check(memory.peek64(header+16)==allocator,"binding preserves allocator");
        check(virtualCalls[0]==0,"within capacity route uses actual154 without virtual calls");
        System.out.println("BlockRange8f198CandidateTest cases=9 checks="+checks+" failures=0");
    }
}
