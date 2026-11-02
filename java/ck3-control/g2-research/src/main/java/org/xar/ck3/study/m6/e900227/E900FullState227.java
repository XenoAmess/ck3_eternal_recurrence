package org.xar.ck3.study.m6.e900227;

import java.util.Objects;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.e900239.E900Api239;
import org.xar.ck3.research.m3.e900239.E900Target424E900;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Represented185 normal frame for held70B E900; deeper CALL/TAIL and machine planes stay opaque. */
public final class E900FullState227 {
    private E900FullState227() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls lower) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(lower);
        long image=entry.imageBaseBits(),s=entry.rspBits(),pre=s-0x28L;
        memory.writeQword(s-8L,entry.nonvolatileBits().rbxBits());
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                image,pre,entry.volatileBits(),entry.nonvolatileBits()));
        r.rbx=Integer.toUnsignedLong((int)r.rcx);
        GovernmentCrtBoundary185Api.NormalReturn[] actualTail={null};
        NativeTaskMemory view=new NativeTaskMemory(){
            @Override public long readPointer(long address){return memory.readQword(address);}
            @Override public int readInt32(long address){return memory.readDword(address);}
            @Override public void writeInt32(long address,int value){memory.writeDword(address,value);}
            @Override public void writeInt64(long address,long value){memory.writeQword(address,value);}
        };
        E900Api239.Ports ports=new E900Api239.Ports(){
            @Override public long call424e448(NativeTaskMemory ignored,long site,int ecx,long rdx,long r8,long r9){
                r.rcx=Integer.toUnsignedLong(ecx);r.rdx=rdx;r.r8=r8;r.r9=r9;
                memory.writeQword(pre-8L,image+site+5L);
                r.apply(lower.invoke(new GovernmentCrtBoundary185Api.Call(site,
                        GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424E448L,
                        pre,r.volatileBits(),r.nonvolatileBits())));
                r.rcx=Integer.toUnsignedLong((int)r.rbx);
                r.rsp=pre+0x20L;
                r.rbx=memory.readQword(r.rsp);
                r.rsp+=8L;
                return r.rax;
            }
            private long tail(long site,long target){
                actualTail[0]=lower.tail(new GovernmentCrtBoundary185Api.Tail(site,
                        GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,
                        new GovernmentCrtBoundary185Api.Entry(image,r.rsp,r.volatileBits(),r.nonvolatileBits())));
                return actualTail[0].volatileBits().raxBits();
            }
            @Override public long tail43dbba8(NativeTaskMemory ignored,long site,long target,long liveRax,int ecx){
                return tail(site,target);
            }
            @Override public long tail43da460(NativeTaskMemory ignored,long site,long target,long liveRax,int ecx){
                return tail(site,target);
            }
        };
        E900Target424E900.execute(view,ports,new E900Api239.Input(image,(int)entry.volatileBits().rcxBits()));
        return Objects.requireNonNull(actualTail[0]);
    }
}
