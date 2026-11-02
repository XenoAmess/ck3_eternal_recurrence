package org.xar.ck3.study.m6.indexed228;

import java.util.Objects;
import org.xar.ck3.research.m3.indexed225.IndexedHelper225Api;
import org.xar.ck3.research.m3.indexed225.IndexedLookupHelper424E448;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Only the two cached arms of held470B; observed zero is an unsupported scope boundary. */
public final class Indexed448CachedOnly228 {
    private Indexed448CachedOnly228() { }

    public static GovernmentCrtBoundary185Api.NormalReturn executeCachedOnly(
            GovernmentCrtBoundary185Api.Entry entry,GovernmentCrtBoundary185Api.Memory memory) {
        Objects.requireNonNull(entry);Objects.requireNonNull(memory);
        long image=entry.imageBaseBits(),s=entry.rspBits(),pre=s-0x48L;
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                image,s,entry.volatileBits(),entry.nonvolatileBits()));
        memory.writeQword(s+8L,r.rbx);memory.writeQword(s+0x10L,r.rbp);memory.writeQword(s+0x18L,r.rsi);
        memory.writeQword(s-8L,r.rdi);memory.writeQword(s-0x10L,r.r12);memory.writeQword(s-0x18L,r.r13);
        memory.writeQword(s-0x20L,r.r14);memory.writeQword(s-0x28L,r.r15);
        r.rsp=pre;r.r15=Integer.toUnsignedLong((int)r.rcx);r.r14=image;
        r.r12=r.r9;r.rbp=r.r8;r.r13=r.rdx;
        long table=image+0x5C5D790L+r.r15*8L;
        int[] observations={0};
        IndexedHelper225Api.Memory view=new IndexedHelper225Api.Memory(){
            private long encoded;
            @Override public long readPointer(long address){
                if(observations[0]==0 && address==table){
                    encoded=memory.readQword(address);observations[0]=1;r.rcx=encoded;return encoded;
                }
                if(observations[0]==1 && address==image+0x542F0B8L){
                    long cookie=memory.readQword(address);observations[0]=2;
                    r.r10=cookie;r.rdi=-1L;r.rax=cookie&0x3FL;
                    r.rdx=Long.rotateRight(cookie^encoded,(int)r.rax);
                    r.rcx=(encoded&~0xFFL)|r.rax;
                    if(r.rdx==0L)throw new UnsupportedOperationException("uncached path after observed zero");
                    return cookie;
                }
                throw outside();
            }
            @Override public int readInt32(long address){return memory.readDword(address);}
            @Override public void writeInt32(long address,int value){memory.writeDword(address,value);}
            @Override public void writeInt64(long address,long value){memory.writeQword(address,value);}
            @Override public long exchangeInt64(long address,long value){throw outside();}
        };
        long selected=IndexedLookupHelper424E448.execute(view,OutsidePorts.INSTANCE,
                new IndexedHelper225Api.Input(image,(int)r.r15,r.r13,r.rbp,r.r12));
        if(observations[0]!=2)throw outside();
        r.rax=selected;
        r.rbx=memory.readQword(pre+0x50L);r.rbp=memory.readQword(pre+0x58L);r.rsi=memory.readQword(pre+0x60L);
        r.rsp=pre+0x20L;
        r.r15=memory.readQword(r.rsp);r.rsp+=8L;r.r14=memory.readQword(r.rsp);r.rsp+=8L;
        r.r13=memory.readQword(r.rsp);r.rsp+=8L;r.r12=memory.readQword(r.rsp);r.rsp+=8L;
        r.rdi=memory.readQword(r.rsp);r.rsp+=8L;
        long actualRip=memory.readQword(r.rsp);
        return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(),actualRip,r.rsp+8L,r.nonvolatileBits());
    }
    private static UnsupportedOperationException outside(){return new UnsupportedOperationException("outside cached-only source path");}
    private enum OutsidePorts implements IndexedHelper225Api.Ports {
        INSTANCE;
        @Override public long call43da478(IndexedHelper225Api.Memory m,long s,long t,long c,int d,int b){throw outside();}
        @Override public int call43da738(IndexedHelper225Api.Memory m,long s,long t){throw outside();}
        @Override public int call4246a60(IndexedHelper225Api.Memory m,long s,long c,long d,int b){throw outside();}
        @Override public void call43da7c0(IndexedHelper225Api.Memory m,long s,long t,long c){throw outside();}
        @Override public long call43da680(IndexedHelper225Api.Memory m,long s,long t,long c,long d){throw outside();}
    }
}
