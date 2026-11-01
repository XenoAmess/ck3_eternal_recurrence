package org.xar.ck3.research.m3.manualtail250;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.LongConsumer;
import org.xar.ck3.research.m3.callee246.Callee68fcApi246;
import org.xar.ck3.research.m3.callee246.Callee68d4Memory246;
import org.xar.ck3.research.m3.tail249.Tail6670Api249;
import org.xar.ck3.research.m3.tail249.Tail4256670249;
import org.xar.ck3.research.m3.tail250.Tail4256874250;
import org.xar.ck3.research.m3.tail250.Tail6874From6670Binding250;
public final class TailValidation250 {
 private TailValidation250() { }
 private static int checks,groups,events,ramEvents,ports,opaqueEffects,xaddEvents,addEvents;
 private static void check(boolean ok,String label){checks++;if(!ok)throw new AssertionError(label);}
 private static String h(long v){return Long.toUnsignedString(v,16);}
 private static String rw(String kind,long a,long v){return kind+":"+h(a)+":"+h(v);}
 private static final class Ram implements Callee68d4Memory246 {
  final Map<Long,Byte> bytes=new HashMap<>();final List<String> trace=new ArrayList<>();int adds,xadds;LongConsumer afterXadd;
  private long raw(long a,int width){long v=0;for(int n=0;n<width;n++){Byte b=bytes.get(a+n);if(b==null)throw new AssertionError("unmapped "+h(a+n));v|=(b.longValue()&255L)<<(8*n);}return v;}
  private void store(long a,int width,long v){for(int n=0;n<width;n++)bytes.put(a+n,(byte)(v>>>(8*n)));}
  void seed8(long a,int v){check((v&~255)==0,"seed8width");store(a,1,v);}
  void seed32(long a,int v){store(a,4,Integer.toUnsignedLong(v));}
  void seed64(long a,long v){store(a,8,v);}
  void effect32(long a,int v){trace.add(rw("E32",a,Integer.toUnsignedLong(v)));store(a,4,Integer.toUnsignedLong(v));}
  void effect64(long a,long v){trace.add(rw("E64",a,v));store(a,8,v);}
  Map<Long,Byte> snapshot(){return Map.copyOf(bytes);}
  @Override public long readPointer(long a){long v=raw(a,8);trace.add(rw("R64",a,v));return v;}
  @Override public int readInt32(long a){long v=raw(a,4);trace.add(rw("R32",a,v));return (int)v;}
  @Override public void writeInt64(long a,long v){trace.add(rw("W64",a,v));store(a,8,v);}
  @Override public void writeInt32(long a,int v){trace.add(rw("W32",a,Integer.toUnsignedLong(v)));store(a,4,Integer.toUnsignedLong(v));}
  @Override public void writeInt16(long a,int v){trace.add(rw("W16",a,v&65535L));store(a,2,v);}
  @Override public void atomicAddInt32(long a,int delta){long old=raw(a,4),after=(old+Integer.toUnsignedLong(delta))&0xFFFFFFFFL;store(a,4,after);adds++;trace.add("A32:"+h(a)+":"+h(Integer.toUnsignedLong(delta))+":"+h(old)+":"+h(after));}
  @Override public int exchangeAddInt32(long a,int delta){long old=raw(a,4),after=(old+Integer.toUnsignedLong(delta))&0xFFFFFFFFL;store(a,4,after);xadds++;trace.add("X32:"+h(a)+":"+h(Integer.toUnsignedLong(delta))+":"+h(old)+":"+h(after));if(afterXadd!=null)afterXadd.accept(a);return (int)old;}
 }
 private static void expectedWrite(Map<Long,Byte> m,long a,int width,long v){for(int n=0;n<width;n++)m.put(a+n,(byte)(v>>>(8*n)));}
 private static void fallbackEvent(Ram m,long site,long rcx,long rdx,long rax,long r8){m.trace.add("F:"+h(site)+":"+h(rcx)+":"+h(rdx)+":"+h(rax)+":"+h(r8));}
 private static void sameException(Runnable work,RuntimeException marker,String label){try{work.run();}catch(RuntimeException x){check(x==marker,label);return;}throw new AssertionError("no original exception "+label);}
 private static void rejected(Runnable work,String label){try{work.run();}catch(RuntimeException x){checks++;return;}throw new AssertionError("not rejected "+label);}
 private static void complete(Ram m,List<String> expected,Map<Long,Byte> finalBytes,String label){check(m.trace.equals(expected),label+" expected="+expected+" actual="+m.trace);check(m.snapshot().equals(finalBytes),label+" finalbytes");groups++;events+=m.trace.size();for(String e:m.trace){if(e.startsWith("X32:"))xaddEvents++;if(e.startsWith("A32:"))addEvents++;if(e.startsWith("R")||e.startsWith("W")||e.startsWith("A32:")||e.startsWith("X32:"))ramEvents++;else if(e.startsWith("E"))opaqueEffects++;else ports++;}}
 private static void direct39(){
  {
   Ram m=new Ram();Map<Long,Byte> expected=new HashMap<>(m.snapshot());
   long zero=Tail4256874250.execute(null,0,0);
   long sentinel=Tail4256874250.execute(m,0xFFFFFFFFF0000000L,0xFFFFFFFFF44271D0L);
   check(zero==0x7FFFFFFFL&&sentinel==0x7FFFFFFFL,"zero and wrapped sentinel full64 constants");
   check(m.adds==0&&m.xadds==0,"constant zero Memory effects");
   complete(m,List.of(),expected,"constant branches");
  }
  {
   Ram m=new Ram();m.seed64(0x115C,0xAABBCCDDFFFFFFFFL);m.seed8(0x115B,0xA5);m.seed8(0x1164,0x5A);
   Map<Long,Byte> expected=new HashMap<>(m.snapshot());expectedWrite(expected,0x115C,4,0x12345678);
   m.afterXadd=address->{check(address==0x115C,"oldbits hook exact address");m.effect32(0x115C,0x12345678);};
   long value=Tail4256874250.execute(m,0x900000000L,0x1000);
   check(value==0,"actual oldFFFFFFFF INC wraps0 despite laterRAM mutation");
   check(m.xadds==1&&m.adds==0,"one exchangeAdd not ordinary add");
   complete(m,HOOK_TRACE,expected,"old returned bits not posthook RAM");
  }
  {
   Ram m=new Ram();m.seed64(0,0x112233447FFFFFFFL);m.seed8(-1L,0xA5);m.seed8(8,0x5A);
   Map<Long,Byte> expected=new HashMap<>(m.snapshot());expectedWrite(expected,0,4,0x80000000L);
   long value=Tail4256874250.execute(m,0,0xFFFFFFFFFFFFFEA4L);
   check(value==0x0000000080000000L,"old7FFFFFFF INC full positive z32");
   check(m.xadds==1&&m.adds==0,"wrapped address one exchangeAdd");
   complete(m,WRAP_TRACE,expected,"wrapped address0 and highDWORD canary");
  }
  {
   Ram m=new Ram();m.seed64(0x315C,0xDEADBEEF80000000L);m.seed8(0x315B,0xA5);m.seed8(0x3164,0x5A);
   Map<Long,Byte> expected=new HashMap<>(m.snapshot());expectedWrite(expected,0x315C,4,0x80000001L);
   RuntimeException marker=new RuntimeException("original direct XADD failure");
   m.afterXadd=address->{check(address==0x315C,"throw exact address");throw marker;};
   sameException(()->Tail4256874250.execute(m,0,0x3000),marker,"direct Memory exception original identity");
   check(m.xadds==1&&m.adds==0,"throw source prefix once");
   complete(m,EXCEPTION_TRACE,expected,"direct exception exact prefix");
  }
 }

 private static void actual249Protocol250(){
  {
   Ram m=new Ram();m.seed64(0x6010,0x5566778800000009L);
   m.seed64(0x60E0,0);m.seed64(0x60F0,0);m.seed64(0x60E8,0);m.seed64(0x6100,0);
   for(int i=0;i<6;i++){m.seed64(0x6028L+0x20L*i,0x30542F498L);m.seed64(0x6020L+0x20L*i,0);}
   m.seed64(0x6120,0x7000);m.seed64(0x715C,0xDEADC0DE7FFFFFFFL);
   m.seed8(0x600F,0xA5);m.seed8(0x715B,0xB6);m.seed8(0x7164,0xC7);
   Map<Long,Byte> expected=new HashMap<>(m.snapshot());
   expectedWrite(expected,0x6010,4,10);expectedWrite(expected,0x715C,4,0x80000000L);expectedWrite(expected,0x6120,8,0x8000);
   m.afterXadd=address->{check(address==0x715C,"actual received RCX7000 target715c");m.effect64(0x6120,0x8000);};
   Tail6670Api249.Ports fallback=(memory,site,rcx,rdx,rax,r8)->{throw new AssertionError("qualified real source must not fallback");};
   Map<Long,Byte> beforeFactory=m.snapshot();
   Tail6670Api249.Ports bound=Tail6874From6670Binding250.bind(0x300000000L,m,fallback);
   check(m.trace.isEmpty()&&m.snapshot().equals(beforeFactory),"actual factory zero RAM effect");
   Tail4256670249.execute(m,bound,new Tail6670Api249.Input(0x300000000L,0x6000));
   check(m.adds==1&&m.xadds==1,"new actual edge one outer INC one inner XADD");
   complete(m,CHAIN_TRACE,expected,"actual mature249 to new250 only");
  }
  {
   Ram captured=new Ram(),foreign=new Ram();captured.seed64(0x315C,0xAABBCCDDFFFFFFFFL);captured.seed8(0x315B,0xA5);captured.seed8(0x3164,0x5A);
   Tail6670Api249.Ports forbidden=(memory,site,rcx,rdx,rax,r8)->{throw new AssertionError("factory must not invoke fallback");};
   rejected(()->Tail6874From6670Binding250.bind(0,null,forbidden),"null captured factory");
   rejected(()->Tail6874From6670Binding250.bind(0,captured,null),"null fallback factory");
   check(captured.trace.isEmpty()&&foreign.trace.isEmpty()&&captured.xadds==0&&captured.adds==0,"null factory zero effects");
   Map<Long,Byte> expected=new HashMap<>(captured.snapshot());expectedWrite(expected,0x315C,4,0);
   RuntimeException fallbackMarker=new RuntimeException("original nonqualified fallback"),memoryMarker=new RuntimeException("original qualified XADD failure");
   int[] fallbackCalls={0};
   Tail6670Api249.Ports fallback=(memory,site,rcx,rdx,rax,r8)->{
    fallbackCalls[0]++;
    if(fallbackCalls[0]==1){
     check(memory==foreign&&site==0x42566F6L&&rcx==0x8000000000000001L&&rdx==0xFEDCBA9876543210L&&rax==-1L&&r8==0x123456789ABCDEF0L,"foreign identity all six exact received args");
    }else if(fallbackCalls[0]==2){
     check(memory==captured&&site==Long.MIN_VALUE&&rcx==-1L&&rdx==0&&rax==0xFEDCBA9876543210L&&r8==-1L,"wrong site all six exact received args");
    }else{
     check(fallbackCalls[0]==3&&memory==null&&site==0x42566F5L&&rcx==0&&rdx==Long.MIN_VALUE&&rax==0&&r8==-1L,"null received Memory passive not factory null");
    }
    fallbackEvent(captured,site,rcx,rdx,rax,r8);if(fallbackCalls[0]==3)throw fallbackMarker;
   };
   captured.afterXadd=address->{check(address==0x315C,"qualified exception source address");throw memoryMarker;};
   Map<Long,Byte> beforeFactory=captured.snapshot();
   Tail6670Api249.Ports bound=Tail6874From6670Binding250.bind(0,captured,fallback);
   check(captured.trace.isEmpty()&&captured.snapshot().equals(beforeFactory),"base0 factory legal and pure");
   bound.tail4256874(foreign,0x42566F6L,0x8000000000000001L,0xFEDCBA9876543210L,-1L,0x123456789ABCDEF0L);
   bound.tail4256874(captured,Long.MIN_VALUE,-1L,0,0xFEDCBA9876543210L,-1L);
   sameException(()->bound.tail4256874(null,0x42566F5L,0,Long.MIN_VALUE,0,-1L),fallbackMarker,"original fallback exception identity");
   check(captured.xadds==0&&captured.adds==0&&captured.snapshot().equals(beforeFactory),"three nonqualified calls zero target Memory effect");
   check(foreign.trace.isEmpty()&&foreign.bytes.isEmpty()&&foreign.xadds==0&&foreign.adds==0,"foreign Memory unchanged");
   sameException(()->bound.tail4256874(captured,0x42566F6L,0x3000,Long.MIN_VALUE,0xFEDCBA9876543210L,-1L),memoryMarker,"qualified Memory exception original identity");
   check(fallbackCalls[0]==3&&captured.xadds==1&&captured.adds==0,"nonqual3fallback and qualified1leaf once");
   complete(captured,PROTOCOL_TRACE,expected,"precise nonqualification fallback and active exception");
  }
 }

 private static final List<String> HOOK_TRACE=List.of(
  "X32:115c:1:ffffffff:0",
  "E32:115c:12345678");
 private static final List<String> WRAP_TRACE=List.of(
  "X32:0:1:7fffffff:80000000");
 private static final List<String> EXCEPTION_TRACE=List.of(
  "X32:315c:1:80000000:80000001");
 private static final List<String> CHAIN_TRACE=List.of(
  "A32:6010:1:9:a",
  "R64:60e0:0",
  "R64:60f0:0",
  "R64:60e8:0",
  "R64:6100:0",
  "R64:6028:30542f498",
  "R64:6020:0",
  "R64:6048:30542f498",
  "R64:6040:0",
  "R64:6068:30542f498",
  "R64:6060:0",
  "R64:6088:30542f498",
  "R64:6080:0",
  "R64:60a8:30542f498",
  "R64:60a0:0",
  "R64:60c8:30542f498",
  "R64:60c0:0",
  "R64:6120:7000",
  "X32:715c:1:7fffffff:80000000",
  "E64:6120:8000");
 private static final List<String> PROTOCOL_TRACE=List.of(
  "F:42566f6:8000000000000001:fedcba9876543210:ffffffffffffffff:123456789abcdef0",
  "F:8000000000000000:ffffffffffffffff:0:fedcba9876543210:ffffffffffffffff",
  "F:42566f5:0:8000000000000000:0:ffffffffffffffff",
  "X32:315c:1:ffffffff:0");
 public static void main(String[] args){direct39();actual249Protocol250();check(groups==6&&events==28&&ramEvents==23&&ports==3&&opaqueEffects==2&&xaddEvents==5&&addEvents==1,"all scenario event totals");System.out.println("TAIL250_PASS groups="+groups+" orderedEvents="+events+" RAM="+ramEvents+" Ports="+ports+" OpaqueEffects="+opaqueEffects+" X32="+xaddEvents+" A32="+addEvents+" mixedChecks="+checks+" Native=0 Game=0");}
}
