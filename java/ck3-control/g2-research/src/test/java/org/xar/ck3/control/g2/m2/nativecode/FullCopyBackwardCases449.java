package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import java.util.stream.LongStream;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyBackwardData449.Op;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyBackwardData449.Step;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyBackwardData449.Scene;
import static org.xar.ck3.control.g2.m2.nativecode.FullCopyBackwardData449.B;
import static org.xar.ck3.control.g2.m2.nativecode.FullCopyBackwardData449.D;
import static org.xar.ck3.control.g2.m2.nativecode.FullCopyBackwardData449.E;
import static org.xar.ck3.control.g2.m2.nativecode.FullCopyBackwardData449.RET;

/** Three finite source-derived literal books; helpers only pack the frozen input byte pattern. */
public final class FullCopyBackwardCases449 {
 private FullCopyBackwardCases449() { }
 private static Step s(Op op,long...values){return new Step(op,LongStream.of(values).boxed().toList());}
 private static long word(int offset){
  long value=0;for(int i=0;i<8;i++)value|=((offset+i)&255L)<<(8*i);return value;
 }
 private static Step r(int offset){return s(Op.R128,B+offset,word(offset),word(offset+8));}
 private static Step w(int destination,int capturedOffset){return s(Op.W128,B+destination,word(capturedOffset),word(capturedOffset+8));}
 private static Step b(int currentOffset){return s(Op.STEP,0x4226E47L,B+currentOffset);}
 private static Step t(int currentOffset){return s(Op.STEP,0x4226EB0L,B+currentOffset);}
 private static Step ret(){return s(Op.R64,E,RET);}
 private static FullCopy437Api.CallResult post(){
  VolatileBits input=FullCopyBackwardData449.incoming(33L);
  VolatileBits value=new VolatileBits(D,B+16L,-3L,13L,0L,B,D,
      new Bits128(word(13),word(21)),new Bits128(word(0),word(8)),
      input.xmm2(),input.xmm3(),input.xmm4(),input.xmm5());
  return new FullCopy437Api.CallResult(new NormalReturn(value,RET,E+8L,FullCopyBackwardData449.nonvolatile()),false);
 }
 public static List<Scene> scenes(){
  FullCopy437Api.CallResult expected=post();
  return List.of(
   new Scene(33L,List.of(
      r(17), r(13), w(20,17), r(0), w(3,0),
      w(16,13), ret()
   ),expected),
   new Scene(273L,List.of(
      r(257), r(253), w(260,257), w(256,253), b(256),
      r(237), r(221), w(240,237), w(224,221), r(205),
      r(189), w(208,205), w(192,189), r(173), r(157),
      w(176,173), w(160,157), r(141), r(125), w(144,141),
      t(128), w(128,125), r(109), t(112), w(112,109),
      r(93), t(96), w(96,93), r(77), t(80),
      w(80,77), r(61), t(64), w(64,61), r(45),
      t(48), w(48,45), r(29), t(32), w(32,29),
      r(13), r(0), w(3,0), w(16,13), ret()
   ),expected),
   new Scene(529L,List.of(
      r(513), r(509), w(516,513), w(512,509), b(512),
      r(493), r(477), w(496,493), w(480,477), r(461),
      r(445), w(464,461), w(448,445), r(429), r(413),
      w(432,429), w(416,413), r(397), r(381), w(400,397),
      w(384,381), b(384), r(365), r(349), w(368,365),
      w(352,349), r(333), r(317), w(336,333), w(320,317),
      r(301), r(285), w(304,301), w(288,285), r(269),
      r(253), w(272,269), w(256,253), b(256), r(237),
      r(221), w(240,237), w(224,221), r(205), r(189),
      w(208,205), w(192,189), r(173), r(157), w(176,173),
      w(160,157), r(141), r(125), w(144,141), t(128),
      w(128,125), r(109), t(112), w(112,109), r(93),
      t(96), w(96,93), r(77), t(80), w(80,77),
      r(61), t(64), w(64,61), r(45), t(48),
      w(48,45), r(29), t(32), w(32,29), r(13),
      r(0), w(3,0), w(16,13), ret()
   ),expected)
  );
 }
}
