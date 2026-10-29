package org.xar.ck3.control.g2.m3;

import static org.junit.jupiter.api.Assertions.*;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.m3.Fh4ResearchDecoder.*;

/** Real goldens; negative fixtures are synthetic. */
public final class Fh4ResearchDecoderTest {
    private static final String ROOT="D:/ck3-state/ck3-java-g2-r4-native/";
    private static final String M0="28bd502505c9502505040aa0b1f100c03eb05c220408de";
    private static final String M6="111c09001c341c001c01140010f00ee00c700b600a500000645a22043c5636052809472405455636050858008103020906046802";
    private static final String TABLE="fffefffdfffefffcfffefffdfffefffb1912190b191219041912190b19121900";
    private static Raw m0(){return actual("raw40/shared-static/capture01/window-002.raw",23,
            "c9168772d8fba16db75e07e29a2dbb6dfc2ce12366090cbc6cf369d0bd02d925",0x52550b4L,M0);}
    private static Raw m6(){return actual("raw39/shared-static/capture01/window-015.raw",52,
            "cd1836c2705b1a6726f67929357595a663707f83a40b6e7f8021f13801b5a9cc",0x536561cL,M6);}
    private static Raw actual(String path,int bytes,String sha,long rva,String hex) {
        return Fh4ResearchDecoder.retained(new ExactRef(ROOT+path,bytes,sha),rva,HexFormat.of().parseHex(hex));
    }
    private static Raw negative(String hex) throws Exception {return synthetic(HexFormat.of().parseHex(hex));}
    private static Raw synthetic(byte[] bytes) throws Exception {
        String sha=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        return Fh4ResearchDecoder.retained(new ExactRef("in-memory-synthetic-validation/"+sha,bytes.length,sha),0,bytes);
    }
    private static <T> Decoded<T> present(Presence<T> value) {
        if(value instanceof Present<T> actual)return actual.field();
        throw new AssertionError("present field required");
    }
    @Test public void raw40FuncInfoAndCompleteUnwindMapRetainEveryFieldOrigin() {
        Raw raw=m0();FuncInfo info=Fh4ResearchDecoder.funcInfo(raw.slice(0,23));
        assertEquals(0x28,info.header().value().value());assertTrue(info.header().value().ehs());
        assertFalse(info.header().value().isCatch());assertFalse(info.header().value().isSeparated());
        assertEquals(0x52550bd,present(info.unwindMap()).value());assertEquals(0x52550c9,info.ipMap().value().displacement());
        assertInstanceOf(Missing.class,info.bbtFlags());assertInstanceOf(Missing.class,info.tryBlockMap());
        assertInstanceOf(Missing.class,info.frame());assertEquals(9,info.extent().length());
        UnwindMap map=Fh4ResearchDecoder.unwindMap(info.remaining());
        assertEquals(2,map.count().value().value());assertEquals(12,map.extent().length());
        assertEquals(0x52550bdL,map.extent().rva());assertEquals(0x52550c9L,map.remaining().rva());
        assertEquals(2,map.remaining().length());
        var first=map.entries().get(0);var second=map.entries().get(1);
        assertEquals(UnwindKind.DTOR_OBJECT,first.tag().value().kind());assertEquals(1,first.tag().value().backBytes());
        assertEquals(0x00f1b1a0,present(first.action()).value());assertEquals(96,present(first.object()).value().value());
        assertEquals(UnwindKind.RVA,second.tag().value().kind());assertEquals(7,second.tag().value().backBytes());
        assertEquals(0x04225cb0,present(second.action()).value());assertInstanceOf(Missing.class,second.object());
        for(var entry:map.entries()){
            assertInstanceOf(EmptyState.class,entry.tag().value().target());
            assertEquals(raw.source(),entry.tag().extent().raw());
            assertEquals(Qualification.FH4_COMPATIBLE_RESEARCH_ONLY,entry.tag().qualification());
            assertEquals(Binding.UNKNOWN,entry.tag().actualInput());assertEquals(Binding.UNKNOWN,entry.tag().runtimeBase());
            assertEquals(Fh4ResearchDecoder.OFFICIAL,entry.tag().officialSources());
        }
        assertEquals(4,Fh4ResearchDecoder.unsigned(map.remaining()).field().value().value());
        assertThrows(IllegalArgumentException.class,()->Fh4ResearchDecoder.ipMap(map.remaining()));
    }
    @Test public void raw39M6HasAnEntireElevenByteIpMapButNoInventedFunctionBase() {
        Raw raw=m6();FuncInfo info=Fh4ResearchDecoder.funcInfo(raw.slice(32,20));
        assertEquals(0x5244709,present(info.unwindMap()).value());assertEquals(0x5365645,info.ipMap().value().displacement());
        IpMap map=Fh4ResearchDecoder.ipMap(info.remaining());assertEquals(4,map.count().value().value());
        assertEquals(11,map.extent().length());assertEquals(0,map.remaining().length());
        long[] ips={44,268,654,706};int[] states={-1,0,1,0};
        for(int i=0;i<4;i++){
            var row=map.entries().get(i);assertEquals(ips[i],row.functionRelativeIp().value());
            assertEquals(states[i],row.state().value().value());assertEquals(states[i]+1L,row.state().value().encoded());
            assertEquals(raw.source(),row.state().extent().raw());assertEquals(Binding.UNKNOWN,row.state().exactBuildCrt());
            assertTrue(row.functionRelativeIp().extent().rva()>=0x5365646L);
        }
    }
    @Test public void lookupOracleAndFixedSigned32() throws Exception {
        Raw table=actual("raw39/shared-static/capture01/window-013.raw",32,
                "cac716064a9fa8dec3ed1eb6f31d016034cccca0c1a37d81f3d4f20767f6f1a9",0x44210c8L,TABLE);
        byte[] lookup=table.bytes();
        for(int first=0;first<256;first++){
            byte[] input={(byte)0xa5,(byte)0x5a,(byte)0xc3,(byte)first,0x12,0x34,0x56,0x78};
            int n=-lookup[first&15],shift=lookup[16+(first&15)]&255;long load=0;
            for(int j=0;j<4;j++)load|=(long)(input[3+n-4+j]&255)<<(8*j);
            var read=Fh4ResearchDecoder.unsigned(synthetic(input).slice(3,5));
            assertEquals(load>>>shift,read.field().value().value());assertEquals(n,read.field().extent().length());
        }
        Raw wide=negative("0fffffffff");assertEquals(0xffff_ffffL,Fh4ResearchDecoder.unsigned(wide.slice(0,5)).field().value().value());
        assertEquals(-1,Fh4ResearchDecoder.signed32(wide.slice(1,4)).field().value());
    }
    @Test public void rejectsTruncationReservedHeadersOverflowAndInvalidBackEdges() throws Exception {
        for(String hex:new String[]{"0f0000","0f","ff000000"}){
            Raw value=negative(hex);assertThrows(IllegalArgumentException.class,()->Fh4ResearchDecoder.unsigned(value.slice(0,value.bytes().length)));
        }
        Raw header=negative("80");assertThrows(IllegalArgumentException.class,()->Fh4ResearchDecoder.funcInfo(header.slice(0,1)));
        Raw state=negative("02000f01000080");assertThrows(IllegalArgumentException.class,()->Fh4ResearchDecoder.ipMap(state.slice(0,7)));
        Raw sum=negative("040fffffffff000200");assertThrows(IllegalArgumentException.class,()->Fh4ResearchDecoder.ipMap(sum.slice(0,9)));
        for(String hex:new String[]{"0210","040e0000000008","0200"}){
            Raw value=negative(hex);assertThrows(IllegalArgumentException.class,()->Fh4ResearchDecoder.unwindMap(value.slice(0,value.bytes().length)));
        }
        Raw raw=m0();byte[] changed=raw.bytes();changed[0]^=1;
        assertThrows(IllegalArgumentException.class,()->Fh4ResearchDecoder.retained(raw.source(),raw.rva(),changed));
        assertThrows(IllegalArgumentException.class,()->raw.slice(22,2));
    }
    @Test public void absentFieldAndPresentZeroAreDifferentAndSeparatedReferenceIsUnresolved() throws Exception {
        Raw zero=negative("080000000000000000");FuncInfo info=Fh4ResearchDecoder.funcInfo(zero.slice(0,9));
        assertEquals(0,present(info.unwindMap()).value());assertInstanceOf(Missing.class,info.tryBlockMap());
        Raw separated=negative("0200000000");FuncInfo other=Fh4ResearchDecoder.funcInfo(separated.slice(0,5));
        assertEquals(MapKind.SEPARATED_UNRESOLVED,other.ipMap().value().kind());assertEquals(5,other.extent().length());
        Raw empty=negative("00");assertEquals(0,Fh4ResearchDecoder.unwindMap(empty.slice(0,1)).entries().size());
    }
}
