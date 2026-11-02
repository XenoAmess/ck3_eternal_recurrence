package org.xar.ck3.study.m6.fc226;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Finite owner literal observations frozen from original204B before model POST. */
public final class Fc74FullState226Test {
    private Fc74FullState226Test() { }
    private static final long I=0x140000000L,S=0x300008L,RET=0x1111222233334444L;
    private static final long[] INITIAL={0x8000000000001201L,0xf000000080000044L,0xe000000000001203L,0x8000000000001208L,0xf000000000001209L,0x800000000000120aL,0xf00000000000120bL,0x1200L,0x1201L,0x1202L,0x1203L,0x1204L,0x1205L,0x1206L,0x1207L,0x1208L,0x1209L,0x120aL,0x120bL};
    private static final NonvolatileBits N=new NonvolatileBits(0x1234567887654321L,0xb002L,0x3456789a87654321L,0x456789ab87654321L,0xa00000000000b012L,0xb013L,0xb014L,0xb015L,new Bits128(0x6001L,0x6002L));
    private static int checks;
    private record Mutation(String operation,long address,long value) { }
    private record Step(Call expected,VolatileBits returned,List<Mutation> mutations,boolean throwsMarker) { }
    private record Scene(String id,int index,List<Step> steps,List<String> memory,NormalReturn expected) { }
    public static void main(String[] args) {
        List<Scene> scenes=List.of(
        new Scene("cached-positive",(int)0x7L,List.of(
            new Step(new Call(0x424fc83L,TargetKind.INDIRECT_ABSOLUTE,0x7fff000000001111L,0x2fffe0L,vec(-1),nv(0x1234567887654321L,0x3456789a87654321L,0x456789ab87654321L)),vec(0 ,0L,0xa000000080000011L),List.of(new Mutation("W64",0x1443da420L,0x7fff00000000f222L)),false),
            new Step(new Call(0x424fc96L,TargetKind.DIRECT_RVA,0x424e900L,0x2fffe0L,vec(0 ,0L,0xa000000080000011L,1L,0x7L),nv(0x80000011L,0x3456789a87654321L,0x456789ab87654321L)),vec(2 ,0L,0x7000000000000200L),List.of(),false),
            new Step(new Call(0x424fd21L,TargetKind.INDIRECT_ABSOLUTE,0x7fff00000000f222L,0x2fffe0L,vec(2 ,0L,0x7000000000000200L,1L,0x80000011L),nv(0x80000011L,0x7000000000000200L,0x7000000000000200L)),vec(3 ,0L,0xdeadbeefcafebabeL),List.of(new Mutation("W64",0x300008L,0x5555666677778888L)),false)),
            List.of("P:W64:300010:1234567887654321","P:W64:300018:3456789a87654321","P:W64:300000:456789ab87654321","P:R64:1443da738:7fff000000001111","P:W64:2fffd8:14424fc89","C:R64:2fffd8:14424fc89","C:W64:1443da420:7fff00000000f222","P:R32:14542f328:7","P:W64:2fffd8:14424fc9b","C:R64:2fffd8:14424fc9b","P:R64:1443da420:7fff00000000f222","P:W64:2fffd8:14424fd27","C:R64:2fffd8:14424fd27","C:W64:300008:5555666677778888","P:R64:300010:1234567887654321","P:R64:300018:3456789a87654321","P:R64:300000:456789ab87654321","P:R64:300008:5555666677778888"),new NormalReturn(vec(3 ,0L,0x7000000000000200L),0x5555666677778888L,0x300010L,nv(0x1234567887654321L,0x3456789a87654321L,0x456789ab87654321L))),
        new Scene("cached-sentinel",(int)0x7L,List.of(
            new Step(new Call(0x424fc83L,TargetKind.INDIRECT_ABSOLUTE,0x7fff000000001111L,0x2fffe0L,vec(-1),nv(0x1234567887654321L,0x3456789a87654321L,0x456789ab87654321L)),vec(0 ,0L,0xa000000080000011L),List.of(new Mutation("W64",0x1443da420L,0x7fff00000000f222L)),false),
            new Step(new Call(0x424fc96L,TargetKind.DIRECT_RVA,0x424e900L,0x2fffe0L,vec(0 ,0L,0xa000000080000011L,1L,0x7L),nv(0x80000011L,0x3456789a87654321L,0x456789ab87654321L)),vec(2 ,0L,0xffffffffffffffffL),List.of(),false),
            new Step(new Call(0x424fd21L,TargetKind.INDIRECT_ABSOLUTE,0x7fff00000000f222L,0x2fffe0L,vec(2 ,0L,0xffffffffffffffffL,1L,0x80000011L),nv(0x80000011L,0x0L,0x0L)),vec(3 ,0L,0xdeadbeefcafebabeL),List.of(new Mutation("W64",0x300008L,0x5555666677778888L)),false)),
            List.of("P:W64:300010:1234567887654321","P:W64:300018:3456789a87654321","P:W64:300000:456789ab87654321","P:R64:1443da738:7fff000000001111","P:W64:2fffd8:14424fc89","C:R64:2fffd8:14424fc89","C:W64:1443da420:7fff00000000f222","P:R32:14542f328:7","P:W64:2fffd8:14424fc9b","C:R64:2fffd8:14424fc9b","P:R64:1443da420:7fff00000000f222","P:W64:2fffd8:14424fd27","C:R64:2fffd8:14424fd27","C:W64:300008:5555666677778888","P:R64:300010:1234567887654321","P:R64:300018:3456789a87654321","P:R64:300000:456789ab87654321","P:R64:300008:5555666677778888"),new NormalReturn(vec(3 ,0L,0x0L),0x5555666677778888L,0x300010L,nv(0x1234567887654321L,0x3456789a87654321L,0x456789ab87654321L))),
        new Scene("saved-stack-mutated",(int)0x7L,List.of(
            new Step(new Call(0x424fc83L,TargetKind.INDIRECT_ABSOLUTE,0x7fff000000001111L,0x2fffe0L,vec(-1),nv(0x1234567887654321L,0x3456789a87654321L,0x456789ab87654321L)),vec(0 ,0L,0xa000000080000011L),List.of(new Mutation("W64",0x1443da420L,0x7fff00000000f222L)),false),
            new Step(new Call(0x424fc96L,TargetKind.DIRECT_RVA,0x424e900L,0x2fffe0L,vec(0 ,0L,0xa000000080000011L,1L,0x7L),nv(0x80000011L,0x3456789a87654321L,0x456789ab87654321L)),vec(2 ,0L,0x7000000000000200L),List.of(),false),
            new Step(new Call(0x424fd21L,TargetKind.INDIRECT_ABSOLUTE,0x7fff00000000f222L,0x2fffe0L,vec(2 ,0L,0x7000000000000200L,1L,0x80000011L),nv(0x80000011L,0x7000000000000200L,0x7000000000000200L)),vec(3 ,0L,0xdeadbeefcafebabeL),List.of(new Mutation("W64",0x300008L,0x5555666677778888L),new Mutation("W64",0x300010L,0xaabbccddeeff1122L),new Mutation("W64",0x300018L,0xbbccddeeff112233L),new Mutation("W64",0x300000L,0xccddeeff11223344L)),false)),
            List.of("P:W64:300010:1234567887654321","P:W64:300018:3456789a87654321","P:W64:300000:456789ab87654321","P:R64:1443da738:7fff000000001111","P:W64:2fffd8:14424fc89","C:R64:2fffd8:14424fc89","C:W64:1443da420:7fff00000000f222","P:R32:14542f328:7","P:W64:2fffd8:14424fc9b","C:R64:2fffd8:14424fc9b","P:R64:1443da420:7fff00000000f222","P:W64:2fffd8:14424fd27","C:R64:2fffd8:14424fd27","C:W64:300008:5555666677778888","C:W64:300010:aabbccddeeff1122","C:W64:300018:bbccddeeff112233","C:W64:300000:ccddeeff11223344","P:R64:300010:aabbccddeeff1122","P:R64:300018:bbccddeeff112233","P:R64:300000:ccddeeff11223344","P:R64:300008:5555666677778888"),new NormalReturn(vec(3 ,0L,0x7000000000000200L),0x5555666677778888L,0x300010L,nv(0xaabbccddeeff1122L,0xbbccddeeff112233L,0xccddeeff11223344L))),
        new Scene("probe-low32zero-high64nonzero",(int)0xffffffffL,List.of(
            new Step(new Call(0x424fc83L,TargetKind.INDIRECT_ABSOLUTE,0x7fff000000001111L,0x2fffe0L,vec(-1),nv(0x1234567887654321L,0x3456789a87654321L,0x456789ab87654321L)),vec(0 ,0L,0xa000000080000011L),List.of(new Mutation("W64",0x1443da420L,0x7fff00000000f222L)),false),
            new Step(new Call(0x424fcb9L,TargetKind.DIRECT_RVA,0x424e948L,0x2fffe0L,vec(0 ,0L,0xa000000080000011L,1L,0xffffffffL,2L,0xffffffffffffffffL),nv(0x80000011L,0x3456789a87654321L,0x456789ab87654321L)),vec(2 ,0L,0xb000000000000000L),List.of(),false),
            new Step(new Call(0x424fd21L,TargetKind.INDIRECT_ABSOLUTE,0x7fff00000000f222L,0x2fffe0L,vec(2 ,0L,0xb000000000000000L,1L,0x80000011L),nv(0x80000011L,0x0L,0x0L)),vec(3 ,0L,0xdeadbeefcafebabeL),List.of(new Mutation("W64",0x300008L,0x5555666677778888L)),false)),
            List.of("P:W64:300010:1234567887654321","P:W64:300018:3456789a87654321","P:W64:300000:456789ab87654321","P:R64:1443da738:7fff000000001111","P:W64:2fffd8:14424fc89","C:R64:2fffd8:14424fc89","C:W64:1443da420:7fff00000000f222","P:R32:14542f328:ffffffff","P:W64:2fffd8:14424fcbe","C:R64:2fffd8:14424fcbe","P:R64:1443da420:7fff00000000f222","P:W64:2fffd8:14424fd27","C:R64:2fffd8:14424fd27","C:W64:300008:5555666677778888","P:R64:300010:1234567887654321","P:R64:300018:3456789a87654321","P:R64:300000:456789ab87654321","P:R64:300008:5555666677778888"),new NormalReturn(vec(3 ,0L,0x0L),0x5555666677778888L,0x300010L,nv(0x1234567887654321L,0x3456789a87654321L,0x456789ab87654321L))),
        new Scene("allocation-success",(int)0xffffffffL,List.of(
            new Step(new Call(0x424fc83L,TargetKind.INDIRECT_ABSOLUTE,0x7fff000000001111L,0x2fffe0L,vec(-1),nv(0x1234567887654321L,0x3456789a87654321L,0x456789ab87654321L)),vec(0 ,0L,0xa000000080000011L),List.of(new Mutation("W64",0x1443da420L,0x7fff00000000f222L)),false),
            new Step(new Call(0x424fcb9L,TargetKind.DIRECT_RVA,0x424e948L,0x2fffe0L,vec(0 ,0L,0xa000000080000011L,1L,0xffffffffL,2L,0xffffffffffffffffL),nv(0x80000011L,0x3456789a87654321L,0x456789ab87654321L)),vec(2 ,0L,0x1L),List.of(),false),
            new Step(new Call(0x424fcccL,TargetKind.DIRECT_RVA,0x424e2ecL,0x2fffe0L,vec(2 ,0L,0x1L,1L,0x1L,2L,0x3c8L),nv(0x80000011L,0x3456789a87654321L,0x456789ab87654321L)),vec(3 ,0L,0x7000000000000200L),List.of(new Mutation("W32",0x14542f328L,0x9L)),false),
            new Step(new Call(0x424fcf2L,TargetKind.DIRECT_RVA,0x424e948L,0x2fffe0L,vec(3 ,0L,0x7000000000000200L,1L,0x9L,2L,0x7000000000000200L),nv(0x80000011L,0x3456789a87654321L,0x7000000000000200L)),vec(5 ,0L,0x1L),List.of(),false),
            new Step(new Call(0x424fd10L,TargetKind.DIRECT_RVA,0x424f8a8L,0x2fffe0L,vec(5 ,0L,0x1L,1L,0x7000000000000200L),nv(0x80000011L,0x3456789a87654321L,0x7000000000000200L)),vec(6 ,0L,0x777L),List.of(),false),
            new Step(new Call(0x424fd17L,TargetKind.DIRECT_RVA,0x424e364L,0x2fffe0L,vec(6 ,0L,0x777L,1L,0x0L),nv(0x80000011L,0x3456789a87654321L,0x7000000000000200L)),vec(7 ,0L,0x888L),List.of(),false),
            new Step(new Call(0x424fd21L,TargetKind.INDIRECT_ABSOLUTE,0x7fff00000000f222L,0x2fffe0L,vec(7 ,0L,0x888L,1L,0x80000011L),nv(0x80000011L,0x7000000000000200L,0x7000000000000200L)),vec(8 ,0L,0xdeadbeefcafebabeL),List.of(new Mutation("W64",0x300008L,0x5555666677778888L)),false)),
            List.of("P:W64:300010:1234567887654321","P:W64:300018:3456789a87654321","P:W64:300000:456789ab87654321","P:R64:1443da738:7fff000000001111","P:W64:2fffd8:14424fc89","C:R64:2fffd8:14424fc89","C:W64:1443da420:7fff00000000f222","P:R32:14542f328:ffffffff","P:W64:2fffd8:14424fcbe","C:R64:2fffd8:14424fcbe","P:W64:2fffd8:14424fcd1","C:R64:2fffd8:14424fcd1","C:W32:14542f328:9","P:R32:14542f328:9","P:W64:2fffd8:14424fcf7","C:R64:2fffd8:14424fcf7","P:W64:2fffd8:14424fd15","C:R64:2fffd8:14424fd15","P:W64:2fffd8:14424fd1c","C:R64:2fffd8:14424fd1c","P:R64:1443da420:7fff00000000f222","P:W64:2fffd8:14424fd27","C:R64:2fffd8:14424fd27","C:W64:300008:5555666677778888","P:R64:300010:1234567887654321","P:R64:300018:3456789a87654321","P:R64:300000:456789ab87654321","P:R64:300008:5555666677778888"),new NormalReturn(vec(8 ,0L,0x7000000000000200L),0x5555666677778888L,0x300010L,nv(0x1234567887654321L,0x3456789a87654321L,0x456789ab87654321L))),
        new Scene("registration-fails",(int)0xffffffffL,List.of(
            new Step(new Call(0x424fc83L,TargetKind.INDIRECT_ABSOLUTE,0x7fff000000001111L,0x2fffe0L,vec(-1),nv(0x1234567887654321L,0x3456789a87654321L,0x456789ab87654321L)),vec(0 ,0L,0xa000000080000011L),List.of(new Mutation("W64",0x1443da420L,0x7fff00000000f222L)),false),
            new Step(new Call(0x424fcb9L,TargetKind.DIRECT_RVA,0x424e948L,0x2fffe0L,vec(0 ,0L,0xa000000080000011L,1L,0xffffffffL,2L,0xffffffffffffffffL),nv(0x80000011L,0x3456789a87654321L,0x456789ab87654321L)),vec(2 ,0L,0x1L),List.of(),false),
            new Step(new Call(0x424fcccL,TargetKind.DIRECT_RVA,0x424e2ecL,0x2fffe0L,vec(2 ,0L,0x1L,1L,0x1L,2L,0x3c8L),nv(0x80000011L,0x3456789a87654321L,0x456789ab87654321L)),vec(3 ,0L,0x7000000000000200L),List.of(new Mutation("W32",0x14542f328L,0x9L)),false),
            new Step(new Call(0x424fcf2L,TargetKind.DIRECT_RVA,0x424e948L,0x2fffe0L,vec(3 ,0L,0x7000000000000200L,1L,0x9L,2L,0x7000000000000200L),nv(0x80000011L,0x3456789a87654321L,0x7000000000000200L)),vec(5 ,0L,0x0L),List.of(new Mutation("W32",0x14542f328L,0x42L)),false),
            new Step(new Call(0x424fd03L,TargetKind.DIRECT_RVA,0x424e948L,0x2fffe0L,vec(5 ,0L,0x0L,1L,0x42L,2L,0x0L),nv(0x80000011L,0x3456789a87654321L,0x7000000000000200L)),vec(7 ,0L,0xaaaL),List.of(),false),
            new Step(new Call(0x424fce8L,TargetKind.DIRECT_RVA,0x424e364L,0x2fffe0L,vec(7 ,0L,0xaaaL,1L,0x7000000000000200L),nv(0x80000011L,0x3456789a87654321L,0x7000000000000200L)),vec(8 ,0L,0xbbbL),List.of(),false),
            new Step(new Call(0x424fd21L,TargetKind.INDIRECT_ABSOLUTE,0x7fff00000000f222L,0x2fffe0L,vec(8 ,0L,0xbbbL,1L,0x80000011L),nv(0x80000011L,0x0L,0x0L)),vec(9 ,0L,0xdeadbeefcafebabeL),List.of(new Mutation("W64",0x300008L,0x5555666677778888L)),false)),
            List.of("P:W64:300010:1234567887654321","P:W64:300018:3456789a87654321","P:W64:300000:456789ab87654321","P:R64:1443da738:7fff000000001111","P:W64:2fffd8:14424fc89","C:R64:2fffd8:14424fc89","C:W64:1443da420:7fff00000000f222","P:R32:14542f328:ffffffff","P:W64:2fffd8:14424fcbe","C:R64:2fffd8:14424fcbe","P:W64:2fffd8:14424fcd1","C:R64:2fffd8:14424fcd1","C:W32:14542f328:9","P:R32:14542f328:9","P:W64:2fffd8:14424fcf7","C:R64:2fffd8:14424fcf7","C:W32:14542f328:42","P:R32:14542f328:42","P:W64:2fffd8:14424fd08","C:R64:2fffd8:14424fd08","P:W64:2fffd8:14424fced","C:R64:2fffd8:14424fced","P:R64:1443da420:7fff00000000f222","P:W64:2fffd8:14424fd27","C:R64:2fffd8:14424fd27","C:W64:300008:5555666677778888","P:R64:300010:1234567887654321","P:R64:300018:3456789a87654321","P:R64:300000:456789ab87654321","P:R64:300008:5555666677778888"),new NormalReturn(vec(9 ,0L,0x0L),0x5555666677778888L,0x300010L,nv(0x1234567887654321L,0x3456789a87654321L,0x456789ab87654321L))),
        new Scene("first-port-throws",(int)0x7L,List.of(
            new Step(new Call(0x424fc83L,TargetKind.INDIRECT_ABSOLUTE,0x7fff000000001111L,0x2fffe0L,vec(-1),nv(0x1234567887654321L,0x3456789a87654321L,0x456789ab87654321L)),vec(0 ,0L,0xa000000080000011L),List.of(),true)),
            List.of("P:W64:300010:1234567887654321","P:W64:300018:3456789a87654321","P:W64:300000:456789ab87654321","P:R64:1443da738:7fff000000001111","P:W64:2fffd8:14424fc89"),null));
        for(Scene scene:scenes) run(scene);
        whole("whole225-FC74-real-cached",0);
        whole("whole225-corrupt-FC74-RET",1);
        whole("whole225-corrupt-FC74-savedRBX",2);
        System.out.println("PASS scenes="+(scenes.size()+3)+" checks="+checks+" direct7=true wholeNormal1=true wholeGuardPrefix2=true Native=false Game=false represented185Only=true");
    }
    private static void run(Scene scene) {
        Ram m=new Ram();m.seed(S,RET,8);m.seed(I+0x542F328L,Integer.toUnsignedLong(scene.index()),4);
        m.seed(I+0x43DA738L,0x7FFF000000001111L,8);m.seed(I+0x43DA420L,0x7FFF000000002222L,8);
        int[] cursor={0};UnsupportedOperationException marker=new UnsupportedOperationException("owned unavailable input");
        Calls calls=new Calls(){
            @Override public VolatileBits invoke(Call c){
                ok(cursor[0]<scene.steps().size(),"noextraCALL");Step step=scene.steps().get(cursor[0]++);
                eq(c,step.expected(),"fullactualCALLframe");
                if(step.throwsMarker())throw marker;
                return m.callback(()->{
                    int length=c.kind()==TargetKind.INDIRECT_ABSOLUTE?6:5;
                    eq(m.readQword(c.rspBits()-8),I+c.callSiteRva()+length,"actualownedCALLreturnslot");
                    for(Mutation mutation:step.mutations()){
                        if(mutation.operation().equals("W64"))m.writeQword(mutation.address(),mutation.value());
                        else if(mutation.operation().equals("W32"))m.writeDword(mutation.address(),(int)mutation.value());
                        else throw new AssertionError("unknown fixture mutation");
                    }
                    return step.returned();
                });
            }
            @Override public NormalReturn tail(Tail t){throw new AssertionError("unexpectedtail "+t);}
            @Override public long readGsQword58(){throw new AssertionError("unexpectedGS");}
        };
        Entry entry=new Entry(I,S,vec(-1),N);
        if(scene.expected()==null){
            try{Fc74FullState226.execute(entry,m,calls);throw new AssertionError("expectedownedexception");}
            catch(UnsupportedOperationException ex){ok(ex==marker,"sameexceptionprefix");}
        }else eq(Fc74FullState226.execute(entry,m,calls),scene.expected(),"allactualNormalReturnfields");
        eq(cursor[0],scene.steps().size(),"exactCALLcount");eq(m.trace,scene.memory(),"orderedactualRAMsourceandcallback");
        System.out.println("PASS "+scene.id());
    }

    /** Three post-model owner integration/counter cases; the seven direct literals above stay frozen. */
    private static void whole(String id,int mode) {
        long w=0x400008L,object=0x7000000000000200L,cell=0x7000000000000220L;
        long block=0x8888000000000055L,heap=0x7777000000000033L;
        long heapTarget=0x7FFF000000003333L,errorTarget=0x7FFF000000001111L,late=0x7FFF00000000F222L;
        long changed=0x5555666677778888L,bad=0xBADL;
        Ram m=new Ram();m.seed(w,RET,8);m.seed(I+0x5C5DE30L,heap,8);
        m.seed(I+0x43DA748L,heapTarget,8);m.seed(I+0x43DA738L,errorTarget,8);
        m.seed(I+0x43DA420L,0x7FFF000000002222L,8);m.seed(I+0x542F328L,7,4);
        int[] cursor={0};
        Calls lower=new Calls(){
            @Override public VolatileBits invoke(Call c){
                cursor[0]++;
                if(cursor[0]==1){
                    eq(c,new Call(0x424E37AL,TargetKind.INDIRECT_ABSOLUTE,heapTarget,w-0x28L,
                            vec(-1,0L,0L,1L,heap,2L,0L,3L,block),N),"whole Heap fullCALL");
                    return m.callback(()->{eq(m.readQword(w-0x30L),I+0x424E380L,"whole Heap ownedRET");return vec(20,0L,0L);});
                }
                if(cursor[0]==2){
                    eq(c,new Call(0x424FC83L,TargetKind.INDIRECT_ABSOLUTE,errorTarget,w-0x88L,
                            vec(20,0L,0L),N),"whole first FC74 fullCALL");
                    return m.callback(()->{
                        eq(m.readQword(w-0x90L),I+0x424FC89L,"whole FC74 IAT ownedRET");
                        m.writeQword(I+0x43DA420L,late);return vec(21,0L,0xA000000080000011L);
                    });
                }
                if(cursor[0]==3){
                    eq(c,new Call(0x424FC96L,TargetKind.DIRECT_RVA,0x424E900L,w-0x88L,
                            vec(21,0L,0xA000000080000011L,1L,7L),nv(0x80000011L,N.rsiBits(),N.rdiBits())),"whole cached FC74 fullCALL");
                    return m.callback(()->{eq(m.readQword(w-0x90L),I+0x424FC9BL,"whole cached ownedRET");return vec(22,0L,object);});
                }
                if(cursor[0]==4){
                    eq(c,new Call(0x424FD21L,TargetKind.INDIRECT_ABSOLUTE,late,w-0x88L,
                            vec(22,0L,object,1L,0x80000011L),nv(0x80000011L,object,object)),"whole fresh final FC74 fullCALL");
                    return m.callback(()->{
                        eq(m.readQword(w-0x90L),I+0x424FD27L,"whole last FC74 ownedRET");
                        if(mode==1)m.writeQword(w-0x60L,bad);
                        else if(mode==2)m.writeQword(w-0x58L,bad);
                        else m.writeQword(w,changed);
                        return vec(23,0L,0xDEADBEEFCAFEBABEL);
                    });
                }
                if(cursor[0]==5){
                    eq(c,new Call(0x424E38CL,TargetKind.INDIRECT_ABSOLUTE,errorTarget,w-0x28L,
                            vec(23,0L,cell),nv(cell,N.rsiBits(),N.rdiBits())),"whole outer lastError fullCALL");
                    return m.callback(()->{eq(m.readQword(w-0x30L),I+0x424E392L,"whole outer lastError ownedRET");return vec(24,0L,0xC000000080000001L);});
                }
                if(cursor[0]==6){
                    eq(c,new Call(0x424E394L,TargetKind.DIRECT_RVA,0x423B0D4L,w-0x28L,
                            vec(24,0L,0xC000000080000001L,1L,0x80000001L),nv(cell,N.rsiBits(),N.rdiBits())),"whole outer map fullCALL");
                    return m.callback(()->{eq(m.readQword(w-0x30L),I+0x424E399L,"whole outer map ownedRET");return vec(25,0L,0xD0000000FEDCBA98L);});
                }
                throw new AssertionError("unexpected whole lower "+c);
            }
            @Override public NormalReturn tail(Tail t){throw new AssertionError("unexpected whole tail "+t);}
            @Override public long readGsQword58(){throw new AssertionError("unexpected whole GS");}
        };
        Entry entry=new Entry(I,w,vec(-1,2L,block),N);
        Calls bound=Fc74Calls226.bind(I,m,lower);
        if(mode==0){
            NormalReturn got=org.xar.ck3.study.m6.error225.DefaultFreeWithErrorCell225.execute(entry,m,bound);
            eq(got,new NormalReturn(vec(25,0L,0xD0000000FEDCBA98L),changed,w+8,N),"whole225 full actual normal return");
            eq(m.load(cell,4),0xFEDCBA98L,"whole mapped DWORD");eq(cursor[0],6,"whole exact lower6");
        }else{
            try{org.xar.ck3.study.m6.error225.DefaultFreeWithErrorCell225.execute(entry,m,bound);throw new AssertionError("whole corrupt FC74 accepted");}
            catch(IllegalStateException ex){eq(ex.getMessage(),mode==1?"returnRip mismatch":"nonvolatile mismatch","whole exact child guard");}
            eq(cursor[0],4,"whole no parent continuation after actual child guard");
        }
        List<String> expected=new ArrayList<>(List.of(
                event("P","W32",w+0x10L,0),event("P","R32",w+0x10L,0),event("P","W64",w-8,N.rbxBits()),
                event("P","R64",I+0x5C5DE30L,heap),event("P","R64",I+0x43DA748L,heapTarget),
                event("P","W64",w-0x30L,I+0x424E380L),event("C","R64",w-0x30L,I+0x424E380L),
                event("P","W64",w-0x30L,I+0x424E389L),event("P","W64",w-0x60L,I+0x423B195L),
                event("P","W64",w-0x58L,N.rbxBits()),event("P","W64",w-0x50L,N.rsiBits()),event("P","W64",w-0x68L,N.rdiBits()),
                event("P","R64",I+0x43DA738L,errorTarget),event("P","W64",w-0x90L,I+0x424FC89L),
                event("C","R64",w-0x90L,I+0x424FC89L),event("C","W64",I+0x43DA420L,late),
                event("P","R32",I+0x542F328L,7),event("P","W64",w-0x90L,I+0x424FC9BL),event("C","R64",w-0x90L,I+0x424FC9BL),
                event("P","R64",I+0x43DA420L,late),event("P","W64",w-0x90L,I+0x424FD27L),event("C","R64",w-0x90L,I+0x424FD27L)));
        if(mode==1)expected.add(event("C","W64",w-0x60L,bad));
        else if(mode==2)expected.add(event("C","W64",w-0x58L,bad));
        else expected.add(event("C","W64",w,changed));
        expected.addAll(List.of(event("P","R64",w-0x58L,mode==2?bad:N.rbxBits()),event("P","R64",w-0x50L,N.rsiBits()),
                event("P","R64",w-0x68L,N.rdiBits()),event("P","R64",w-0x60L,mode==1?bad:I+0x423B195L)));
        if(mode==0)expected.addAll(List.of(event("P","R64",w-0x30L,I+0x424E389L),event("P","R64",I+0x43DA738L,errorTarget),
                event("P","W64",w-0x30L,I+0x424E392L),event("C","R64",w-0x30L,I+0x424E392L),
                event("P","W64",w-0x30L,I+0x424E399L),event("C","R64",w-0x30L,I+0x424E399L),
                event("P","W32",cell,0xFEDCBA98L),event("P","R64",w-8,N.rbxBits()),event("P","R64",w,changed)));
        eq(m.trace,expected,"whole exact ordered RAM source and callbacks");System.out.println("PASS "+id);
    }

    private static VolatileBits vec(int seed,long... overrides){
        long[] a=INITIAL.clone();if(seed>=0)for(int j=0;j<19;j++)a[j]=0x9000000000000000L+seed*0x100L+j;
        for(int j=0;j<overrides.length;j+=2)a[(int)overrides[j]]=overrides[j+1];
        return new VolatileBits(a[0],a[1],a[2],a[3],a[4],a[5],a[6],new Bits128(a[7],a[8]),new Bits128(a[9],a[10]),new Bits128(a[11],a[12]),new Bits128(a[13],a[14]),new Bits128(a[15],a[16]),new Bits128(a[17],a[18]));
    }
    private static NonvolatileBits nv(long bx,long si,long di){return new NonvolatileBits(bx,N.rbpBits(),si,di,N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6());}
    private static void eq(Object a,Object b,String label){checks++;if(!a.equals(b))throw new AssertionError(label+" actual="+a+" expected="+b);}
    private static void eq(long a,long b,String label){checks++;if(a!=b)throw new AssertionError(label+" actual="+Long.toHexString(a)+" expected="+Long.toHexString(b));}
    private static void ok(boolean value,String label){checks++;if(!value)throw new AssertionError(label);}
    private static String event(String who,String op,long a,long value){return who+":"+op+":"+Long.toUnsignedString(a,16)+":"+Long.toUnsignedString(value,16);}
    private static final class Ram implements GovernmentCrtBoundary185Api.Memory{
        private final Map<Long,Byte> data=new HashMap<>();private final List<String> trace=new ArrayList<>();private String who="P";
        void seed(long a,long value,int width){for(int j=0;j<width;j++)data.put(a+j,(byte)(value>>>(8*j)));}
        long load(long a,int width){long value=0;for(int j=0;j<width;j++){Byte b=data.get(a+j);if(b==null)throw new AssertionError("unownedRAM "+Long.toHexString(a+j));value|=(long)Byte.toUnsignedInt(b)<<(8*j);}return value;}
        <T>T callback(Supplier<T> f){String old=who;who="C";try{return f.get();}finally{who=old;}}
        @Override public int readDword(long a){long v=load(a,4);trace.add(event(who,"R32",a,v));return(int)v;}
        @Override public long readQword(long a){long v=load(a,8);trace.add(event(who,"R64",a,v));return v;}
        @Override public int readUnsignedByte(long a){long v=load(a,1);trace.add(event(who,"R8",a,v));return(int)v;}
        @Override public void writeDword(long a,int v){seed(a,Integer.toUnsignedLong(v),4);trace.add(event(who,"W32",a,Integer.toUnsignedLong(v)));}
        @Override public void writeQword(long a,long v){seed(a,v,8);trace.add(event(who,"W64",a,v));}
        @Override public void writeByte(long a,int v){seed(a,v&0xFFL,1);trace.add(event(who,"W8",a,v&0xFFL));}
        @Override public int lockedXaddDword(long a,int v){throw new AssertionError("unexpectedLOCK");}
        @Override public Bits128 read128(long a){throw new AssertionError("unexpectedmemoryvector");}
        @Override public void write128(long a,Bits128 v){throw new AssertionError("unexpectedmemoryvector");}
    }
}
