package org.xar.ck3.study.m6.full247.oracle;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.*;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api.CallFrame;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api.Children;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api.TailFrame;
import org.xar.ck3.study.m6.postvtable247.PostVtableForward247;
import static org.xar.ck3.study.m6.full247.oracle.LiteralPostState247Data.*;

/**
 * New source-only literal247 witnesses. Defaults: three core inputs. "stopped": only two new negatives.
 * Supplier effects are synthetic typedopaque contracts; no actual getter/allocator/free kernel runs.
 * Never executes old221/237 entry/test bodies or wraps an oldNR with pre-environment.
 */
public final class LiteralPostState247Test {
    private static int scenes,checks;
    private LiteralPostState247Test() { }
    public static void main(String[] args) {
        scenes=0;checks=0; // each explicit selection reports only its own inputs, even in one software host.
        if(args.length==0) {
            allocateTailUsesPostState();scenes++;
            freeFourByteCallThenFreshRet();scenes++;
            selfWrapKeepsPartialEnvironment();scenes++;
        } else if(args.length==1&&args[0].equals("stopped")) {
            firstAllocateStopPreventsTail();scenes++;
            secondFreeStopPreventsOuterRet();scenes++;
        } else throw new IllegalArgumentException("no args=three newcore; stopped=two newnegative only");
        System.out.println("PASS selection="+(args.length==0?"core":"stopped")+" scenes="+scenes
                +" checks="+checks+" typedOpaqueSuppliersOnly=true old221237Executed=0"
                +" actualCalleeKernelRuns=0 Native=false Game=false hardwareABI=false");
    }

    private static void allocateTailUsesPostState() {
        Allocate51 d=allocate51();Ram m=ram(d.initialQwords());int[] calls={0},tails={0};
        long outerOrigin=0x21A51B9L;
        Children children=new RejectChildren() {
            @Override public Outcome invoke(CallFrame frame,Memory memory) {
                check(memory==m);equal(calls[0]++,0);
                first(frame,d.firstCall(),d.inputDF(),d.inputMxcsr(),0x855870L,3,I+0x855886L);
                equal(m.peek(C),I+0x855886L);equal(m.writes,prologueAndCall(d.input(),I+0x855886L));
                applyEffects(m,d.firstRamEffects());return d.firstNormal();
            }
            @Override public Outcome tail(TailFrame frame,Memory memory) {
                check(memory==m);equal(tails[0]++,0);equal(calls[0],1);
                equal(frame.ownerEntryRva(),0x855870L);equal(frame.instructionLength(),3);
                equal(frame.transfer(),d.expectedTail());equal(frame.targetInput().entry(),d.expectedTail().entry());
                equal(frame.targetInput().directionFlagSet(),d.expectedTailDF());
                equal(frame.targetInput().mxcsr(),d.expectedTailMxcsr());
                equal(frame.targetInput().originCallSiteRva(),outerOrigin); // JMP retains continuation origin.
                equal(m.writes.size(),6);equal(m.peek(C),I+0x855886L); // no second/tail push.
                equal(m.reads,List.of(A,TA+0x38L,B,TB+8L,S+8L,S-8L));
                // Explicit tail-target RET contract. The literal source itself has no RET here.
                equal(m.readQword(S),d.tailNormal().base().normalReturn().returnRipBits());
                return d.tailNormal();
            }
        };
        Outcome out=PostVtableForward247.fromSlot08(
                new PostVtable247Api.Input(d.input(),d.inputDF(),d.inputMxcsr(),outerOrigin),m,children);
        check(out==d.tailNormal());equal(calls[0],1);equal(tails[0],1);
        equal(m.reads,List.of(A,TA+0x38L,B,TB+8L,S+8L,S-8L,S));
        equal(m.writes,List.of(new Write(S+8L,d.input().nonvolatileBits().rbxBits()),
                new Write(S-8L,d.input().nonvolatileBits().rdiBits()),new Write(C,I+0x855886L),
                new Write(S+8L,FRESH_BX),new Write(S-8L,FRESH_DI),new Write(S,FRESH_RET)));
        equal(((Normal)out).postMxcsr(),new Mxcsr(0x80,0x80));
        equal(((Normal)out).base().postDirectionFlagSet(),false);
    }

    private static void freeFourByteCallThenFreshRet() {
        Free58 d=free58();Ram m=ram(d.initialQwords());int[] calls={0};
        Children children=new RejectChildren() {
            @Override public Outcome invoke(CallFrame frame,Memory memory) {
                check(memory==m);int index=calls[0]++;check(index<2);
                if(index==0) {
                    first(frame,d.firstCall(),d.inputDF(),d.inputMxcsr(),0x855830L,3,I+0x85584FL);
                    equal(m.writes,prologueAndCall(d.input(),I+0x85584FL));return d.firstNormal();
                }
                first(frame,d.secondCall(),d.expectedSecondDF(),d.expectedSecondMxcsr(),
                        0x855830L,4,I+0x85585FL);
                equal(m.peek(C),I+0x85585FL);equal(m.writes.size(),4);
                equal(m.reads,List.of(A,TA+0x38L,B,TB+0x10L));
                applyEffects(m,d.secondRamEffects());return d.secondNormal();
            }
        };
        Outcome out=PostVtableForward247.fromSlot10(
                new PostVtable247Api.Input(d.input(),d.inputDF(),d.inputMxcsr(),0x21A5223L),m,children);
        equal(out,d.expectedReturn());equal(calls[0],2);
        equal(m.reads,List.of(A,TA+0x38L,B,TB+0x10L,S+8L,S-8L,S));
        equal(m.writes,List.of(new Write(S+8L,d.input().nonvolatileBits().rbxBits()),
                new Write(S-8L,d.input().nonvolatileBits().rdiBits()),new Write(C,I+0x85584FL),
                new Write(C,I+0x85585FL),new Write(S+8L,FRESH_BX),new Write(S-8L,FRESH_DI),
                new Write(S,FRESH_RET)));
        Normal normal=(Normal)out;
        equal(normal.base().normalReturn().volatileBits(),d.secondNormal().base().normalReturn().volatileBits());
        equal(normal.postMxcsr(),new Mxcsr(0x80,0x80));check(!normal.postMxcsr().isExact());
    }

    private static void selfWrapKeepsPartialEnvironment() {
        Self58 d=self58Wrap64();Ram m=ram(d.initialQwords());
        // The actual declared producer explicitly allows null Children on this reached branch.
        Outcome out=PostVtableForward247.fromSlot10(
                new PostVtable247Api.Input(d.input(),d.inputDF(),d.inputMxcsr(),0x21A508FL),m,null);
        equal(out,d.expectedReturn());equal(m.reads,List.of(S+8L,S-8L,S));
        equal(m.writes,List.of(new Write(S+8L,d.input().nonvolatileBits().rbxBits()),
                new Write(S-8L,d.input().nonvolatileBits().rdiBits())));
        check(!m.has(C));equal(((Normal)out).base().postDirectionFlagSet(),true);
        equal(((Normal)out).postMxcsr(),new Mxcsr(0x1F80,0xFFC0));
        equal(((Normal)out).postMxcsr().knownMaskBits()&0x3F,0);
    }

    private static void firstAllocateStopPreventsTail() {
        Allocate51 d=allocate51();StopData stop=stoppedPrefixes().get(0);
        Ram m=ram(d.initialQwords());int[] calls={0};
        Outcome out=PostVtableForward247.fromSlot08(
                new PostVtable247Api.Input(d.input(),d.inputDF(),d.inputMxcsr(),0x21A51B9L),m,
                new RejectChildren() {
                    @Override public Outcome invoke(CallFrame frame,Memory memory) {
                        check(memory==m);equal(calls[0]++,0);
                        first(frame,d.firstCall(),d.inputDF(),d.inputMxcsr(),0x855870L,3,I+0x855886L);
                        return stop.offered();
                    }
                });
        check(out==stop.offered());check(((Stopped)out).snapshot()==stop.offered().snapshot());
        equal(calls[0],1);equal(m.reads,List.of(A,TA+0x38L));
        equal(m.writes,prologueAndCall(d.input(),I+0x855886L));
        equal(((Stopped)out).snapshot().currentState().rspBits(),C-0x60L);
        equal(((Stopped)out).snapshot().instructionRva(),0xD24701L); // supplier sentinel, no heldkernelPC.
        equal(((Stopped)out).snapshot().mxcsr(),Mxcsr.unknown());
    }

    private static void secondFreeStopPreventsOuterRet() {
        Free58 d=free58();StopData stop=stoppedPrefixes().get(2);
        Ram m=ram(d.initialQwords());int[] calls={0};
        Outcome out=PostVtableForward247.fromSlot10(
                new PostVtable247Api.Input(d.input(),d.inputDF(),d.inputMxcsr(),0x21A5159L),m,
                new RejectChildren() {
                    @Override public Outcome invoke(CallFrame frame,Memory memory) {
                        check(memory==m);int index=calls[0]++;check(index<2);
                        if(index==0) {
                            first(frame,d.firstCall(),d.inputDF(),d.inputMxcsr(),0x855830L,3,I+0x85584FL);
                            return d.firstNormal();
                        }
                        first(frame,d.secondCall(),d.expectedSecondDF(),d.expectedSecondMxcsr(),
                                0x855830L,4,I+0x85585FL);
                        return stop.offered();
                    }
                });
        check(out==stop.offered());equal(calls[0],2);
        equal(m.reads,List.of(A,TA+0x38L,B,TB+0x10L));
        equal(m.writes,List.of(new Write(S+8L,d.input().nonvolatileBits().rbxBits()),
                new Write(S-8L,d.input().nonvolatileBits().rdiBits()),new Write(C,I+0x85584FL),
                new Write(C,I+0x85585FL)));
        check(((Stopped)out).snapshot()==stop.offered().snapshot());
        equal(((Stopped)out).originCallSiteRva(),0x85585BL);
        equal(((Stopped)out).snapshot().instructionRva(),0xD24703L); // synthetic innerorigin/currentstate retained.
        equal(m.peek(S),RET); // no callback effects or wrapper RET happened.
    }

    private static void first(CallFrame frame,org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call call,
            boolean df,Mxcsr mx,long owner,int length,long rip) {
        equal(frame.ownerEntryRva(),owner);equal(frame.imageBaseBits(),I);equal(frame.call(),call);
        equal(frame.instructionLength(),length);equal(frame.returnRipBits(),rip);
        equal(frame.childInput().entry().rspBits(),C);
        equal(frame.childInput().entry().volatileBits(),call.volatileBits());
        equal(frame.childInput().entry().nonvolatileBits(),call.nonvolatileBits());
        equal(frame.childInput().directionFlagSet(),df);equal(frame.childInput().mxcsr(),mx);
        equal(frame.childInput().originCallSiteRva(),call.callSiteRva());
    }
    private static List<Write> prologueAndCall(
            org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry entry,long rip) {
        return List.of(new Write(S+8L,entry.nonvolatileBits().rbxBits()),
                new Write(S-8L,entry.nonvolatileBits().rdiBits()),new Write(C,rip));
    }
    private static void applyEffects(Ram m,Map<Long,Long> effects) {
        // Only these explicit selected supplier writes, deterministic ordering, no branch-forcing reads.
        m.writeQword(S+8L,effects.get(S+8L));m.writeQword(S-8L,effects.get(S-8L));m.writeQword(S,effects.get(S));
    }
    private static Ram ram(Map<Long,Long> input) {
        Ram m=new Ram();input.forEach(m::poke);return m;
    }
    private static class RejectChildren implements Children {
        @Override public Outcome invoke(CallFrame frame,Memory memory) {throw new AssertionError("unexpected literal247 child");}
        @Override public Outcome tail(TailFrame frame,Memory memory) {throw new AssertionError("unexpected literal247 tail");}
    }
    private record Write(long address,long value) { }
    private static final class Ram implements Memory {
        final Map<Long,Integer> data=new HashMap<>();final List<Long> reads=new ArrayList<>();
        final List<Write> writes=new ArrayList<>();
        boolean has(long a) {return data.containsKey(a);}
        void poke(long a,long value) {for(int j=0;j<8;j++)data.put(a+j,(int)(value>>>(j*8))&255);}
        long peek(long a) {
            long value=0L;for(int j=0;j<8;j++) {
                Integer b=data.get(a+j);
                if(b==null)throw new UnsupportedOperationException("unheldLiteral247RAM "+Long.toHexString(a+j));
                value|=(long)b<<(j*8);
            }
            return value;
        }
        @Override public long readQword(long a) {reads.add(a);return peek(a);}
        @Override public void writeQword(long a,long value) {writes.add(new Write(a,value));poke(a,value);}
        @Override public int readDword(long a) {throw new AssertionError("no literal247 DWORD read");}
        @Override public int readUnsignedByte(long a) {throw new AssertionError("no literal247 byte read");}
        @Override public void writeDword(long a,int value) {throw new AssertionError("no literal247 DWORD write");}
        @Override public void writeByte(long a,int value) {throw new AssertionError("no literal247 byte write");}
        @Override public Bits128 read128(long a) {throw new AssertionError("no literal247 vector read");}
        @Override public void write128(long a,Bits128 value) {throw new AssertionError("no literal247 vector write");}
        @Override public int lockedXaddDword(long a,int addend) {throw new AssertionError("no literal247 atomic");}
    }
    private static void equal(Object actual,Object expected) {
        checks++;if(!java.util.Objects.equals(actual,expected))
            throw new AssertionError("check="+checks+" actual="+actual+" expected="+expected);
    }
    private static void check(boolean condition) {
        checks++;if(!condition)throw new AssertionError("check="+checks);
    }
}
