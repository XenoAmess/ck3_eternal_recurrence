package org.xar.ck3.research.m1;

import java.util.List;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.CallScript;
import org.xar.ck3.research.m1.GovernmentSharedRecord180Witness.Seed;
import static org.xar.ck3.research.m1.GovernmentSharedRecord180Witness.*;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;

/** One new record93->actual Header178 consumer; full manager cold composition belongs to parent. */
public final class GovernmentSharedRecord180HeaderWitness {
    private GovernmentSharedRecord180HeaderWitness() { }
    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("no arguments");
        Seed s=seed(9,5);var m=s.memory();VolatileBits in=s.entry().volatileBits();
        VolatileBits enter=bits(0x2600,0x3600,0x4600,0x5600),leave=bits(0x3700,0x4700,0x5700,0x6700);
        m.writeDword(B+0x5C5CBC4,0);m.writeDword(B+0x542F090,17);
        NonvolatileBits n=s.entry().nonvolatileBits();
        NonvolatileBits inside=new NonvolatileBits(GUARD,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
        final int[] iat={0},headerGs={0};
        GovernmentThreadHeader178Api.Ports ports=new GovernmentThreadHeader178Api.Ports() {
            @Override public long readGsQword58(){headerGs[0]++;return GS;}
            @Override public VolatileBits invoke(OpaqueCall call){throw new AssertionError("unexpected opaque Header wait "+call);}
            @Override public VolatileBits invokeIat(GovernmentThreadHeader178Api.IatCall call) {
                if(iat[0]++==0) {
                    equal(new GovernmentThreadHeader178Api.IatCall(0x4223A94,0x43DA500,S-0x58,false,
                            fields(in,5,B+0x5C5CB18,0x10),inside),call,"actual Header enter full frame");
                    equal(B+0x2D888A8,m.readQword(S-0x30),"outer93 Header CALL return");
                    equal(n.rbxBits(),m.readQword(S-0x38),"Header saved incoming RBX");
                    equal(B+0x4223A9A,m.readQword(S-0x60),"Header own IAT CALL return");return enter;
                }
                equal(2,iat[0],"exact two IAT edges");
                VolatileBits expected=new VolatileBits(17,B+0x5C5CB18,TLS,0x10,
                        enter.r9Bits(),enter.r10Bits(),enter.r11Bits(),enter.xmm0(),enter.xmm1(),enter.xmm2(),enter.xmm3(),enter.xmm4(),enter.xmm5());
                equal(new GovernmentThreadHeader178Api.IatCall(0x4223AE4,0x43DA4F0,S-0x30,true,expected,n),call,"actual Header tailLeave full frame");
                equal(17,m.readDword(TLS+0x10),"actual Header wrote owned TLS epoch");return leave;
            }
        };
        CallScript delegate=new CallScript(GS);
        var bound=GovernmentSharedRecord180Calls.bind(B,m,delegate,ports,(rva,address,value)->{
            throw new AssertionError("no wait path selected");
        });
        GovernmentCallee164Api.NormalReturn actual=GovernmentSharedRecord180.execute(s.entry(),m,bound);
        equal(new GovernmentCallee164Api.NormalReturn(fields(leave,RECORD,leave.rcxBits(),leave.rdxBits()),n,RET,S+8),actual,"whole newHeader composition result");
        delegate.done(1);equal(1,headerGs[0],"separate actual Header GS read");equal(2,iat[0],"all actual IAT edges consumed");
        equal(List.of(S-0x30,S-0x38,S-0x60),m.qwordWrites,"already pushed outer call is never pushed twice");
        equal(RET,m.readQword(S),"original parent RET unchanged");
        equal(0x44332211,m.readDword(RECORD+4),"positive guard skips record byte4");
        equal(0x88776655,m.readDword(RECORD+0x34),"positive guard skips record byte34");
        System.out.println("GovernmentSharedRecord180HeaderWitness:1 new actualHeader consumer");
    }
}
