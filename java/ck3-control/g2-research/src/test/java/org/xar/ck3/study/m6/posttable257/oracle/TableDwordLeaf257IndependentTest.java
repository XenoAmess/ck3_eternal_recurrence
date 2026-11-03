package org.xar.ck3.study.m6.posttable257.oracle;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.posttable257.TableDwordLeaf257;

/**
 * Independent literal projection of held69B/22instruction leaf, not its implementation.
 * Oracle froze before this source and before reading any new producer.
 * Literal SHA256 fb98697de99e082c45d04e64b1154531023db0b403411beb9043228e8906d0b2.
 * All45rows and return slots below are artificial owned Memory; native table contents UNKNOWN.
 * No old case, call, hardware FP, flags/EH or Game execution is claimed.
 */
public final class TableDwordLeaf257IndependentTest {
    private TableDwordLeaf257IndependentTest() { }
    private static final long IMAGE=0x0000000140000000L,T=0x0000000144423A60L,S=0x0000000012345008L;
    private static int checks;
    private record Read(String kind,long address,long rawBits) { }
    private record RowPatch(int index,int key32,int mapped32) { }
    private record CaseData(String name,long inputRcx,RowPatch[] patches,long expectedRax,
            long expectedRcx,long expectedRdx,boolean inputDF,int mxValue,int mxMask,
            long actualRet,List<Read> literalDwordReads) { }
    private static final int[] TABLE_KEYS={
            0x61000000, 0x61000003, 0x61000006, 0x61000009, 0x6100000C, 0x6100000F, 0x61000012, 0x61000015, 0x61000018, 0x6100001B, 0x6100001E, 0x61000021, 0x61000024, 0x61000027, 0x6100002A, 0x6100002D, 0x61000030, 0x61000033, 0x61000036, 0x61000039, 0x6100003C, 0x6100003F, 0x61000042, 0x61000045, 0x61000048, 0x6100004B, 0x6100004E, 0x61000051, 0x61000054, 0x61000057, 0x6100005A, 0x6100005D, 0x61000060, 0x61000063, 0x61000066, 0x61000069, 0x6100006C, 0x6100006F, 0x61000072, 0x61000075, 0x61000078, 0x6100007B, 0x6100007E, 0x61000081, 0x61000084};
    private static final int[] TABLE_VALUES={
            0xA5000000, 0xA5010101, 0xA5020202, 0xA5030303, 0xA5040404, 0xA5050505, 0xA5060606, 0xA5070707, 0xA5080808, 0xA5090909, 0xA50A0A0A, 0xA50B0B0B, 0xA50C0C0C, 0xA50D0D0D, 0xA50E0E0E, 0xA50F0F0F, 0xA5101010, 0xA5111111, 0xA5121212, 0xA5131313, 0xA5141414, 0xA5151515, 0xA5161616, 0xA5171717, 0xA5181818, 0xA5191919, 0xA51A1A1A, 0xA51B1B1B, 0xA51C1C1C, 0xA51D1D1D, 0xA51E1E1E, 0xA51F1F1F, 0xA5202020, 0xA5212121, 0xA5222222, 0xA5232323, 0xA5242424, 0xA5252525, 0xA5262626, 0xA5272727, 0xA5282828, 0xA5292929, 0xA52A2A2A, 0xA52B2B2B, 0xA52C2C2C};
    private static final List<Read> DWORD_READS_0=List.of(
            new Read("DWORD",0x0000000144423A60L,0x00000000F0000021L),
            new Read("DWORD",0x0000000144423A64L,0x0000000080000001L));
    private static final List<Read> DWORD_READS_1=List.of(
            new Read("DWORD",0x0000000144423A60L,0x0000000061000000L),
            new Read("DWORD",0x0000000144423A68L,0x0000000061000003L),
            new Read("DWORD",0x0000000144423A70L,0x0000000061000006L),
            new Read("DWORD",0x0000000144423A78L,0x0000000061000009L),
            new Read("DWORD",0x0000000144423A80L,0x000000006100000CL),
            new Read("DWORD",0x0000000144423A88L,0x000000006100000FL),
            new Read("DWORD",0x0000000144423A90L,0x0000000061000012L),
            new Read("DWORD",0x0000000144423A98L,0x0000000061000015L),
            new Read("DWORD",0x0000000144423AA0L,0x0000000061000018L),
            new Read("DWORD",0x0000000144423AA8L,0x000000006100001BL),
            new Read("DWORD",0x0000000144423AB0L,0x000000006100001EL),
            new Read("DWORD",0x0000000144423AB8L,0x0000000061000021L),
            new Read("DWORD",0x0000000144423AC0L,0x0000000061000024L),
            new Read("DWORD",0x0000000144423AC8L,0x0000000061000027L),
            new Read("DWORD",0x0000000144423AD0L,0x000000006100002AL),
            new Read("DWORD",0x0000000144423AD8L,0x000000006100002DL),
            new Read("DWORD",0x0000000144423AE0L,0x0000000061000030L),
            new Read("DWORD",0x0000000144423AE8L,0x0000000061000033L),
            new Read("DWORD",0x0000000144423AF0L,0x0000000061000036L),
            new Read("DWORD",0x0000000144423AF8L,0x0000000061000039L),
            new Read("DWORD",0x0000000144423B00L,0x000000006100003CL),
            new Read("DWORD",0x0000000144423B08L,0x000000006100003FL),
            new Read("DWORD",0x0000000144423B10L,0x00000000CAFEBABEL),
            new Read("DWORD",0x0000000144423B14L,0x00000000FEDCBA98L));
    private static final List<Read> DWORD_READS_2=List.of(
            new Read("DWORD",0x0000000144423A60L,0x0000000061000000L),
            new Read("DWORD",0x0000000144423A68L,0x0000000061000003L),
            new Read("DWORD",0x0000000144423A70L,0x0000000061000006L),
            new Read("DWORD",0x0000000144423A78L,0x0000000061000009L),
            new Read("DWORD",0x0000000144423A80L,0x000000006100000CL),
            new Read("DWORD",0x0000000144423A88L,0x000000006100000FL),
            new Read("DWORD",0x0000000144423A90L,0x0000000061000012L),
            new Read("DWORD",0x0000000144423A98L,0x0000000061000015L),
            new Read("DWORD",0x0000000144423AA0L,0x0000000061000018L),
            new Read("DWORD",0x0000000144423AA8L,0x000000006100001BL),
            new Read("DWORD",0x0000000144423AB0L,0x000000006100001EL),
            new Read("DWORD",0x0000000144423AB8L,0x0000000061000021L),
            new Read("DWORD",0x0000000144423AC0L,0x0000000061000024L),
            new Read("DWORD",0x0000000144423AC8L,0x0000000061000027L),
            new Read("DWORD",0x0000000144423AD0L,0x000000006100002AL),
            new Read("DWORD",0x0000000144423AD8L,0x000000006100002DL),
            new Read("DWORD",0x0000000144423AE0L,0x0000000061000030L),
            new Read("DWORD",0x0000000144423AE8L,0x0000000061000033L),
            new Read("DWORD",0x0000000144423AF0L,0x0000000061000036L),
            new Read("DWORD",0x0000000144423AF8L,0x0000000061000039L),
            new Read("DWORD",0x0000000144423B00L,0x000000006100003CL),
            new Read("DWORD",0x0000000144423B08L,0x000000006100003FL),
            new Read("DWORD",0x0000000144423B10L,0x0000000061000042L),
            new Read("DWORD",0x0000000144423B18L,0x0000000061000045L),
            new Read("DWORD",0x0000000144423B20L,0x0000000061000048L),
            new Read("DWORD",0x0000000144423B28L,0x000000006100004BL),
            new Read("DWORD",0x0000000144423B30L,0x000000006100004EL),
            new Read("DWORD",0x0000000144423B38L,0x0000000061000051L),
            new Read("DWORD",0x0000000144423B40L,0x0000000061000054L),
            new Read("DWORD",0x0000000144423B48L,0x0000000061000057L),
            new Read("DWORD",0x0000000144423B50L,0x000000006100005AL),
            new Read("DWORD",0x0000000144423B58L,0x000000006100005DL),
            new Read("DWORD",0x0000000144423B60L,0x0000000061000060L),
            new Read("DWORD",0x0000000144423B68L,0x0000000061000063L),
            new Read("DWORD",0x0000000144423B70L,0x0000000061000066L),
            new Read("DWORD",0x0000000144423B78L,0x0000000061000069L),
            new Read("DWORD",0x0000000144423B80L,0x000000006100006CL),
            new Read("DWORD",0x0000000144423B88L,0x000000006100006FL),
            new Read("DWORD",0x0000000144423B90L,0x0000000061000072L),
            new Read("DWORD",0x0000000144423B98L,0x0000000061000075L),
            new Read("DWORD",0x0000000144423BA0L,0x0000000061000078L),
            new Read("DWORD",0x0000000144423BA8L,0x000000006100007BL),
            new Read("DWORD",0x0000000144423BB0L,0x000000006100007EL),
            new Read("DWORD",0x0000000144423BB8L,0x0000000061000081L),
            new Read("DWORD",0x0000000144423BC0L,0x00000000FFFFFFFFL),
            new Read("DWORD",0x0000000144423BC4L,0x00000000FFFFFFFFL));
    private static final List<Read> DWORD_READS_3=List.of(
            new Read("DWORD",0x0000000144423A60L,0x0000000010203040L),
            new Read("DWORD",0x0000000144423A64L,0x0000000089ABCDEFL));
    private static final List<Read> MISS_DWORD_READS=List.of(
            new Read("DWORD",0x0000000144423A60L,0x0000000061000000L),
            new Read("DWORD",0x0000000144423A68L,0x0000000061000003L),
            new Read("DWORD",0x0000000144423A70L,0x0000000061000006L),
            new Read("DWORD",0x0000000144423A78L,0x0000000061000009L),
            new Read("DWORD",0x0000000144423A80L,0x000000006100000CL),
            new Read("DWORD",0x0000000144423A88L,0x000000006100000FL),
            new Read("DWORD",0x0000000144423A90L,0x0000000061000012L),
            new Read("DWORD",0x0000000144423A98L,0x0000000061000015L),
            new Read("DWORD",0x0000000144423AA0L,0x0000000061000018L),
            new Read("DWORD",0x0000000144423AA8L,0x000000006100001BL),
            new Read("DWORD",0x0000000144423AB0L,0x000000006100001EL),
            new Read("DWORD",0x0000000144423AB8L,0x0000000061000021L),
            new Read("DWORD",0x0000000144423AC0L,0x0000000061000024L),
            new Read("DWORD",0x0000000144423AC8L,0x0000000061000027L),
            new Read("DWORD",0x0000000144423AD0L,0x000000006100002AL),
            new Read("DWORD",0x0000000144423AD8L,0x000000006100002DL),
            new Read("DWORD",0x0000000144423AE0L,0x0000000061000030L),
            new Read("DWORD",0x0000000144423AE8L,0x0000000061000033L),
            new Read("DWORD",0x0000000144423AF0L,0x0000000061000036L),
            new Read("DWORD",0x0000000144423AF8L,0x0000000061000039L),
            new Read("DWORD",0x0000000144423B00L,0x000000006100003CL),
            new Read("DWORD",0x0000000144423B08L,0x000000006100003FL),
            new Read("DWORD",0x0000000144423B10L,0x0000000061000042L),
            new Read("DWORD",0x0000000144423B18L,0x0000000061000045L),
            new Read("DWORD",0x0000000144423B20L,0x0000000061000048L),
            new Read("DWORD",0x0000000144423B28L,0x000000006100004BL),
            new Read("DWORD",0x0000000144423B30L,0x000000006100004EL),
            new Read("DWORD",0x0000000144423B38L,0x0000000061000051L),
            new Read("DWORD",0x0000000144423B40L,0x0000000061000054L),
            new Read("DWORD",0x0000000144423B48L,0x0000000061000057L),
            new Read("DWORD",0x0000000144423B50L,0x000000006100005AL),
            new Read("DWORD",0x0000000144423B58L,0x000000006100005DL),
            new Read("DWORD",0x0000000144423B60L,0x0000000061000060L),
            new Read("DWORD",0x0000000144423B68L,0x0000000061000063L),
            new Read("DWORD",0x0000000144423B70L,0x0000000061000066L),
            new Read("DWORD",0x0000000144423B78L,0x0000000061000069L),
            new Read("DWORD",0x0000000144423B80L,0x000000006100006CL),
            new Read("DWORD",0x0000000144423B88L,0x000000006100006FL),
            new Read("DWORD",0x0000000144423B90L,0x0000000061000072L),
            new Read("DWORD",0x0000000144423B98L,0x0000000061000075L),
            new Read("DWORD",0x0000000144423BA0L,0x0000000061000078L),
            new Read("DWORD",0x0000000144423BA8L,0x000000006100007BL),
            new Read("DWORD",0x0000000144423BB0L,0x000000006100007EL),
            new Read("DWORD",0x0000000144423BB8L,0x0000000061000081L),
            new Read("DWORD",0x0000000144423BC0L,0x0000000061000084L));
    private static final List<CaseData> CASES=List.of(
            new CaseData("match-first",0xF1234567F0000021L,new RowPatch[]{new RowPatch(0,0xF0000021,0x80000001)},0x0000000080000001L,0xF1234567F0000021L,0x0000000144423A60L,true,0x00001F80,0x0000FFC0,0xFEDCBA9876543210L,DWORD_READS_0),
            new CaseData("match-middle",0x81234567CAFEBABEL,new RowPatch[]{new RowPatch(22,0xCAFEBABE,0xFEDCBA98)},0x00000000FEDCBA98L,0x81234567CAFEBABEL,0x0000000144423B10L,false,0x00000000,0x00000000,0x8000000011112222L,DWORD_READS_1),
            new CaseData("match-last",0x7ABCDEFFFFFFFFFFL,new RowPatch[]{new RowPatch(44,0xFFFFFFFF,0xFFFFFFFF)},0x00000000FFFFFFFFL,0x7ABCDEFFFFFFFFFFL,0x0000000144423BC0L,true,0x00001F83,0x0000FFFF,0x13579BDF00000000L,DWORD_READS_2),
            new CaseData("duplicate-first-wins",0xFFFFFFFF10203040L,new RowPatch[]{new RowPatch(0,0x10203040,0x89ABCDEF),new RowPatch(44,0x10203040,0x13579BDF)},0x0000000089ABCDEFL,0xFFFFFFFF10203040L,0x0000000144423A60L,false,0x00000080,0x00000080,0xFEDCBA9876543210L,DWORD_READS_3),
            new CaseData("fallback13-low",0xFEDCBA9800000013L,new RowPatch[]{},0x000000000000000DL,0xFEDCBA9800000013L,0x0000000144423BC8L,true,0x00001F80,0x0000FFC0,0xFEDCBA9876543210L,MISS_DWORD_READS),
            new CaseData("fallback13-high",0xABCDEF0100000024L,new RowPatch[]{},0x000000000000000DL,0xABCDEF0100000024L,0x0000000144423BC8L,false,0x00000001,0x00000003,0xFEDCBA9876543210L,MISS_DWORD_READS),
            new CaseData("below-first-unsigned-wrap",0xABABABAB00000012L,new RowPatch[]{},0x0000000000000016L,0x00000000FFFFFF56L,0x0000000144423BC8L,true,0x00000000,0x00000000,0xFEDCBA9876543210L,MISS_DWORD_READS),
            new CaseData("above-first",0xCDCDCDCD00000025L,new RowPatch[]{},0x0000000000000016L,0x00000000FFFFFF69L,0x0000000144423BC8L,false,0x00001F80,0x0000FFC0,0xFEDCBA9876543210L,MISS_DWORD_READS),
            new CaseData("fallback8-low",0x81234567000000BCL,new RowPatch[]{},0x0000000000000008L,0x0000000000000000L,0x0000000144423BC8L,true,0x00001F83,0x0000FFFF,0xFEDCBA9876543210L,MISS_DWORD_READS),
            new CaseData("fallback8-high",0xFEDCBA98000000CAL,new RowPatch[]{},0x0000000000000008L,0x000000000000000EL,0x0000000144423BC8L,false,0x00001F80,0x0000FFC0,0xFEDCBA9876543210L,MISS_DWORD_READS),
            new CaseData("below-second-unsigned-wrap",0x01020304000000BBL,new RowPatch[]{},0x0000000000000016L,0x00000000FFFFFFFFL,0x0000000144423BC8L,true,0x00000080,0x00000080,0xFEDCBA9876543210L,MISS_DWORD_READS),
            new CaseData("above-second",0xF1234567000000CBL,new RowPatch[]{},0x0000000000000016L,0x000000000000000FL,0x0000000144423BC8L,false,0x00000000,0x00000000,0xFEDCBA9876543210L,MISS_DWORD_READS),
            new CaseData("low32-ffffffff-wrap",0x12345678FFFFFFFFL,new RowPatch[]{},0x0000000000000016L,0x00000000FFFFFF43L,0x0000000144423BC8L,true,0x00000001,0x00000003,0xFEDCBA9876543210L,MISS_DWORD_READS),
            new CaseData("same-low13-different-high32",0x0123456700000013L,new RowPatch[]{},0x000000000000000DL,0x0123456700000013L,0x0000000144423BC8L,true,0x00001F80,0x0000FFC0,0xFEDCBA9876543210L,MISS_DWORD_READS));

    private static final Bits128[] XMM={
            new Bits128(0x8000000000000010L,0xF000000000000011L),
            new Bits128(0x8000000000000030L,0xF000000000000031L),
            new Bits128(0x8000000000000050L,0xF000000000000051L),
            new Bits128(0x8000000000000070L,0xF000000000000071L),
            new Bits128(0x8000000000000090L,0xF000000000000091L),
            new Bits128(0x80000000000000B0L,0xF0000000000000B1L),
            new Bits128(0x80000000000000D0L,0xF0000000000000D1L)};
    private static final NonvolatileBits N=new NonvolatileBits(
            0x8100000000000001L,0x8200000000000002L,0x8300000000000003L,0x8400000000000004L,0xABCDEF0198765432L,0x8600000000000006L,0x8700000000000007L,0x8800000000000008L,XMM[6]);

    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("one new finite257 literal corpus only");
        PostState240Api.EntryExecutor leaf=new TableDwordLeaf257();
        for(CaseData c:CASES)run(leaf,c);
        System.out.println("PASS leaf257 independentVectors=14 checks="+checks
                +" synthetic45x8Memory=true fullRepresentedState=true exactReadTrace=true"
                +" writes=0 calls=0 producerSourceRead=false NativeTable=false Game=false hardwareABI=false");
    }

    private static void run(PostState240Api.EntryExecutor leaf,CaseData c) {
        Ram memory=new Ram();
        for(int i=0;i<45;i++) {
            memory.seed32(T+i*8L,TABLE_KEYS[i]);memory.seed32(T+i*8L+4L,TABLE_VALUES[i]);
        }
        for(RowPatch p:c.patches()) {
            memory.seed32(T+p.index()*8L,p.key32());memory.seed32(T+p.index()*8L+4L,p.mapped32());
        }
        memory.seed64(S,c.actualRet());
        Map<Long,Byte> originalBytes=Map.copyOf(memory.bytes);
        VolatileBits incoming=new VolatileBits(0xA100000000000001L,c.inputRcx(),0xD200000000000003L,0xE800000000000004L,0xE900000000000005L,0xAA00000000000006L,0xBB00000000000007L,
                XMM[0],XMM[1],XMM[2],XMM[3],XMM[4],XMM[5]);
        QueueFp604Api.Mxcsr mxcsr=new QueueFp604Api.Mxcsr(c.mxValue(),c.mxMask());
        PostState240Api.Input input=new PostState240Api.Input(
                new GovernmentCrtBoundary185Api.Entry(IMAGE,S,incoming,N),c.inputDF(),mxcsr,0x424E394L);
        QueueFp604Api.Outcome result=leaf.execute(input,memory);
        need(result instanceof QueueFp604Api.Normal,c,"Normal required; no manufactured Stop");
        QueueFp604Api.Normal actual=(QueueFp604Api.Normal)result;
        GovernmentCrtBoundary185Api.NormalReturn nr=actual.base().normalReturn();
        // These expected bits are a mechanical projection of the pre-frozen literal vector.
        VolatileBits expected=new VolatileBits(c.expectedRax(),c.expectedRcx(),c.expectedRdx(),8L,T,
                incoming.r10Bits(),incoming.r11Bits(),XMM[0],XMM[1],XMM[2],XMM[3],XMM[4],XMM[5]);
        eq(nr.volatileBits(),expected,c,"wholeV including all GPR and XMM0..5");
        eq(nr.nonvolatileBits(),N,c,"wholeN including full64R12 and XMM6");
        eq(nr.returnRipBits(),c.actualRet(),c,"fresh full64 actualMemoryRET");
        eq(nr.callerRspBits(),0x0000000012345010L,c,"actualSP+8");
        eq(actual.base().postDirectionFlagSet(),c.inputDF(),c,"unchanged explicitDF");
        eq(actual.postMxcsr(),mxcsr,c,"unchanged MXCSR values/knowledge");
        need(actual.postMxcsr()==mxcsr,c,"same exact input MXCSR object");
        List<Read> expectedReads=new ArrayList<>(c.literalDwordReads());
        expectedReads.add(new Read("QWORD",S,c.actualRet()));
        eq(memory.reads,expectedReads,c,"complete ordered width/address/value readtrace");
        eq(memory.bytes,originalBytes,c,"all supplied bytes unchanged");
    }

    /** Stable strict byte RAM; fixture seeding has no source events and reads never mutate data. */
    private static final class Ram implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long,Byte> bytes=new HashMap<>();
        private final List<Read> reads=new ArrayList<>();
        private void seed32(long a,int value) {for(int i=0;i<4;i++)bytes.put(a+i,(byte)(value>>>(i*8)));}
        private void seed64(long a,long value) {for(int i=0;i<8;i++)bytes.put(a+i,(byte)(value>>>(i*8)));}
        private int raw(long a) {
            Byte b=bytes.get(a);if(b==null)throw new AssertionError("unprovided257RAM "+Long.toHexString(a));
            return b&255;
        }
        @Override public int readDword(long a) {
            int value=0;for(int i=0;i<4;i++)value|=raw(a+i)<<(i*8);
            reads.add(new Read("DWORD",a,Integer.toUnsignedLong(value)));return value;
        }
        @Override public long readQword(long a) {
            if(a!=S)throw unexpected("nonRET QWORD read");
            long value=0;for(int i=0;i<8;i++)value|=(long)raw(a+i)<<(i*8);
            reads.add(new Read("QWORD",a,value));return value;
        }
        @Override public int readUnsignedByte(long a) {throw unexpected("byte read");}
        @Override public void writeQword(long a,long value) {throw unexpected("QWORD write");}
        @Override public void writeDword(long a,int value) {throw unexpected("DWORD write");}
        @Override public void writeByte(long a,int value) {throw unexpected("byte write");}
        @Override public int lockedXaddDword(long a,int value) {throw unexpected("XADD");}
        @Override public Bits128 read128(long a) {throw unexpected("XMM read");}
        @Override public void write128(long a,Bits128 value) {throw unexpected("XMM write");}
        private AssertionError unexpected(String op) {return new AssertionError("no held257 operation: "+op);}
    }
    private static void eq(Object actual,Object expected,CaseData c,String why) {
        checks++;if(!Objects.equals(actual,expected))throw new AssertionError(c.name()+": "+why+" actual="+actual+" expected="+expected);
    }
    private static void need(boolean yes,CaseData c,String why) {
        checks++;if(!yes)throw new AssertionError(c.name()+": "+why);
    }
}
