package org.xar.ck3.control.g2.m3;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;

/**
 * Bounded FH4-compatible research decoding of retained bytes, never a loaded ABI or Game proof.
 * ReadUnsigned is compressed; Microsoft's ReadInt is fixed little-endian signed32, not signed LEB.
 */
public final class Fh4ResearchDecoder {
    private static final long U32=0xffff_ffffL;
    private static final int[] LENGTH={1,2,1,3,1,2,1,4,1,2,1,3,1,2,1,5};
    private Fh4ResearchDecoder() { }
    public enum Qualification { FH4_COMPATIBLE_RESEARCH_ONLY }
    public enum Binding { UNKNOWN }
    public enum Absence { HEADER_FLAG_CLEAR, UNWIND_TYPE_HAS_NO_FIELD }
    public enum MapKind { DIRECT, SEPARATED_UNRESOLVED }
    public enum UnwindKind { NO_UW, DTOR_OBJECT, DTOR_POINTER, RVA }
    public record OfficialSources(ExactRef compactReader,ExactRef frameReader) {
        public OfficialSources { Objects.requireNonNull(compactReader);Objects.requireNonNull(frameReader); }
    }
    public static final OfficialSources OFFICIAL=new OfficialSources(
        new ExactRef("C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/include/ehdata4_export.h",
            42649,"b997c3f00192bb8c138532795d24b64c9b0f2ae4c4ee46af214b22bc7d88f447"),
        new ExactRef("C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/include/ehdata4.h",
            11920,"de358af9546d0cd7c3a5fb10db6baae6e0f08286bc598d05dd1adba2aaa06344"));
    public record Extent(ExactRef raw,long rawRva,int offset,int length) {
        public Extent {
            Objects.requireNonNull(raw);need(rawRva>=0&&rawRva<=U32,"invalid retained RVA");
            need(offset>=0&&length>0&&(long)offset+length<=raw.bytes(),"extent outside original");
            need(raw.bytes()<=0x1_0000_0000L-rawRva,"retained RVA extent overflows");
        }
        public long rva(){return rawRva+offset;}
    }
    public sealed interface Bound permits Decoded,FuncInfo,UnwindMap,IpMap {
        Extent extent();
        default Qualification qualification(){return Qualification.FH4_COMPATIBLE_RESEARCH_ONLY;}
        default OfficialSources officialSources(){return OFFICIAL;}
        default Binding exactBuildCrt(){return Binding.UNKNOWN;}
        default Binding runtimeBase(){return Binding.UNKNOWN;}
        default Binding actualInput(){return Binding.UNKNOWN;}
    }
    /** A verified immutable input copy; no file, process, native interface or writer is opened. */
    public static final class Raw {
        private final ExactRef source;private final long rva;private final byte[] bytes;
        private Raw(ExactRef source,long rva,byte[] bytes){this.source=source;this.rva=rva;this.bytes=bytes;}
        public ExactRef source(){return source;} public long rva(){return rva;}
        public byte[] bytes(){return bytes.clone();}
        public Slice slice(int offset,int length){return new Slice(this,offset,length);}
    }
    public static Raw retained(ExactRef source,long rva,byte[] original) {
        Objects.requireNonNull(source);Objects.requireNonNull(original);
        byte[] copy=original.clone();
        need(copy.length>0&&copy.length==source.bytes(),"original length differs");
        need(rva>=0&&rva<=U32&&copy.length<=0x1_0000_0000L-rva,"original RVA overflows");
        try {
            need(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(copy)).equals(source.sha256()),
                    "original SHA differs");
        } catch(NoSuchAlgorithmException failure){throw new IllegalStateException(failure);}
        return new Raw(source,rva,copy);
    }
    public record Slice(Raw raw,int offset,int length) {
        public Slice {
            Objects.requireNonNull(raw);
            need(offset>=0&&length>=0&&(long)offset+length<=raw.bytes.length,"slice outside original");
        }
        public long rva(){return raw.rva+offset;}
    }
    public record Decoded<T>(T value,Extent extent) implements Bound {
        public Decoded { Objects.requireNonNull(value);Objects.requireNonNull(extent); }
    }
    public record Read<T>(Decoded<T> field,Slice remaining) {
        public Read { Objects.requireNonNull(field);Objects.requireNonNull(remaining); }
    }
    public record Unsigned(long value) { public Unsigned {need(value>=0&&value<=U32,"unsigned32 overflow");} }
    public sealed interface Presence<T> permits Missing,Present { }
    public record Missing<T>(Absence reason,Extent discriminator) implements Presence<T> {
        public Missing {Objects.requireNonNull(reason);Objects.requireNonNull(discriminator);}
    }
    public record Present<T>(Decoded<T> field) implements Presence<T> {
        public Present {Objects.requireNonNull(field);}
    }
    public record Flags(int value) {
        public Flags {need(value>=0&&value<128,"reserved/unknown FuncInfo header bit");}
        public boolean isCatch(){return (value&1)!=0;}
        public boolean isSeparated(){return (value&2)!=0;}
        public boolean bbt(){return (value&4)!=0;}
        public boolean unwind(){return (value&8)!=0;}
        public boolean tries(){return (value&16)!=0;}
        public boolean ehs(){return (value&32)!=0;}
        public boolean noExcept(){return (value&64)!=0;}
    }
    public record IpReference(int displacement,MapKind kind) {
        public IpReference {Objects.requireNonNull(kind);}
    }
    public record FuncInfo(Decoded<Flags> header,Presence<Unsigned> bbtFlags,Presence<Integer> unwindMap,
            Presence<Integer> tryBlockMap,Decoded<IpReference> ipMap,Presence<Unsigned> frame,
            Extent extent,Slice remaining) implements Bound {
        public FuncInfo {
            Objects.requireNonNull(header);Objects.requireNonNull(bbtFlags);Objects.requireNonNull(unwindMap);
            Objects.requireNonNull(tryBlockMap);Objects.requireNonNull(ipMap);Objects.requireNonNull(frame);
            Objects.requireNonNull(extent);Objects.requireNonNull(remaining);
        }
    }
    public sealed interface BackTarget permits EmptyState,EarlierEntry {int byteOffset();}
    public record EmptyState(int byteOffset) implements BackTarget {
        public EmptyState {need(byteOffset>=0,"empty-state sentinel outside captured map");}
    }
    public record EarlierEntry(int ordinal,int byteOffset) implements BackTarget {
        public EarlierEntry {need(ordinal>=0&&byteOffset>=0,"invalid earlier entry");}
    }
    public record UnwindTag(UnwindKind kind,long backBytes,BackTarget target) {
        public UnwindTag {Objects.requireNonNull(kind);Objects.requireNonNull(target);need(backBytes>0,"non-backward unwind edge");}
    }
    public record UnwindEntry(Decoded<UnwindTag> tag,Presence<Integer> action,Presence<Unsigned> object) {
        public UnwindEntry {Objects.requireNonNull(tag);Objects.requireNonNull(action);Objects.requireNonNull(object);}
    }
    public record UnwindMap(Decoded<Unsigned> count,List<UnwindEntry> entries,Extent extent,Slice remaining) implements Bound {
        public UnwindMap {Objects.requireNonNull(count);entries=List.copyOf(entries);Objects.requireNonNull(extent);Objects.requireNonNull(remaining);}
    }
    public record State(long encoded,int value) {
        public State {need(encoded>=0&&encoded<=0x8000_0000L&&value==encoded-1,"FH4 encoded state overflow");}
    }
    public record IpEntry(Decoded<Unsigned> delta,Decoded<Long> functionRelativeIp,Decoded<State> state) {
        public IpEntry {Objects.requireNonNull(delta);Objects.requireNonNull(functionRelativeIp);Objects.requireNonNull(state);}
    }
    public record IpMap(Decoded<Unsigned> count,List<IpEntry> entries,Extent extent,Slice remaining) implements Bound {
        public IpMap {Objects.requireNonNull(count);entries=List.copyOf(entries);Objects.requireNonNull(extent);Objects.requireNonNull(remaining);}
    }

    public static Read<Unsigned> unsigned(Slice input) {
        Cursor c=new Cursor(input);Decoded<Unsigned> value=c.unsigned();return new Read<>(value,c.remaining());
    }
    public static Read<Integer> signed32(Slice input) {
        Cursor c=new Cursor(input);Decoded<Integer> value=c.signed32();return new Read<>(value,c.remaining());
    }
    /** Primary on-disk record only. A separated-map RVA stays unresolved; it is never followed implicitly. */
    public static FuncInfo funcInfo(Slice input) {
        Cursor c=new Cursor(input);int begin=c.pos;
        int start=c.pos;c.require(1);Flags flags=new Flags(c.byteAt(c.pos++));
        Decoded<Flags> header=new Decoded<>(flags,c.span(start,c.pos));
        Presence<Unsigned> bbt=flags.bbt()?new Present<>(c.unsigned()):missing(header.extent(),Absence.HEADER_FLAG_CLEAR);
        Presence<Integer> uw=flags.unwind()?new Present<>(c.signed32()):missing(header.extent(),Absence.HEADER_FLAG_CLEAR);
        Presence<Integer> tries=flags.tries()?new Present<>(c.signed32()):missing(header.extent(),Absence.HEADER_FLAG_CLEAR);
        Decoded<Integer> ip=c.signed32();
        Decoded<IpReference> reference=new Decoded<>(new IpReference(ip.value(),
                flags.isSeparated()?MapKind.SEPARATED_UNRESOLVED:MapKind.DIRECT),ip.extent());
        Presence<Unsigned> frame=flags.isCatch()?new Present<>(c.unsigned()):missing(header.extent(),Absence.HEADER_FLAG_CLEAR);
        return new FuncInfo(header,bbt,uw,tries,reference,frame,c.span(begin,c.pos),c.remaining());
    }
    /**
     * Complete captured map only. Back edges must reach an earlier decoded entry or the exact
     * bufferStart-1 empty-state sentinel used by the pinned reader. Other destinations stay unsupported.
     */
    public static UnwindMap unwindMap(Slice input) {
        Cursor c=new Cursor(input);int begin=c.pos;Decoded<Unsigned> count=c.unsigned();
        need(count.value().value()<=c.left(),"truncated unwind map count");
        int entriesStart=c.pos;var starts=new HashMap<Integer,Integer>();var rows=new ArrayList<UnwindEntry>();
        for(int i=0;i<count.value().value();i++){
            int start=c.pos;Decoded<Unsigned> word=c.unsigned();long bits=word.value().value(),back=bits>>>2;
            need(back>0&&back<=start-(long)(entriesStart-1),"unwind back distance outside captured map");
            int target=(int)(start-back);BackTarget destination;
            if(target==entriesStart-1)destination=new EmptyState(target);
            else {
                Integer ordinal=starts.get(target);need(ordinal!=null,"unwind edge targets a non-entry byte");
                destination=new EarlierEntry(ordinal,target);
            }
            UnwindKind kind=UnwindKind.values()[(int)(bits&3)];
            Decoded<UnwindTag> tag=new Decoded<>(new UnwindTag(kind,back,destination),word.extent());
            Presence<Integer> action=kind==UnwindKind.NO_UW?missing(word.extent(),Absence.UNWIND_TYPE_HAS_NO_FIELD):new Present<>(c.signed32());
            Presence<Unsigned> object=kind==UnwindKind.DTOR_OBJECT||kind==UnwindKind.DTOR_POINTER
                    ?new Present<>(c.unsigned()):missing(word.extent(),Absence.UNWIND_TYPE_HAS_NO_FIELD);
            rows.add(new UnwindEntry(tag,action,object));starts.put(start,i);
        }
        return new UnwindMap(count,rows,c.span(begin,c.pos),c.remaining());
    }
    /** Function-relative IPs only: no unknown function base is supplied or synthesized. */
    public static IpMap ipMap(Slice input) {
        Cursor c=new Cursor(input);int begin=c.pos;Decoded<Unsigned> count=c.unsigned();
        need(count.value().value()<=c.left()/2,"truncated IP map count");
        int entriesStart=c.pos;long ip=0;var rows=new ArrayList<IpEntry>();
        for(int i=0;i<count.value().value();i++){
            Decoded<Unsigned> delta=c.unsigned();ip+=delta.value().value();need(ip<=U32,"IP delta sum overflow");
            Decoded<Long> relative=new Decoded<>(ip,c.span(entriesStart,c.pos));
            Decoded<Unsigned> encoded=c.unsigned();long state=encoded.value().value();need(state<=0x8000_0000L,"EH state overflow");
            rows.add(new IpEntry(delta,relative,new Decoded<>(new State(state,(int)(state-1)),encoded.extent())));
        }
        return new IpMap(count,rows,c.span(begin,c.pos),c.remaining());
    }
    private static <T> Missing<T> missing(Extent e,Absence reason){return new Missing<>(reason,e);}
    private static final class Cursor {
        private final Slice input;private final int end;private int pos;
        Cursor(Slice input){this.input=Objects.requireNonNull(input);pos=input.offset();end=pos+input.length();}
        int byteAt(int i){return input.raw.bytes[i]&255;}
        int left(){return end-pos;}
        void require(int bytes){need(bytes>=0&&bytes<=left(),"truncated retained FH4 field");}
        Extent span(int from,int to){return new Extent(input.raw.source,input.raw.rva,from,to-from);}
        Slice remaining(){return input.raw.slice(pos,end-pos);}
        long le(int from,int bytes){long value=0;for(int i=0;i<bytes;i++)value|=(long)byteAt(from+i)<<(8*i);return value;}
        Decoded<Unsigned> unsigned(){
            require(1);int begin=pos,n=LENGTH[byteAt(pos)&15];require(n);
            long value=n==5?le(pos+1,4):le(pos,n)>>>n;pos+=n;
            return new Decoded<>(new Unsigned(value),span(begin,pos));
        }
        Decoded<Integer> signed32(){
            require(4);int begin=pos;int value=(int)le(pos,4);pos+=4;return new Decoded<>(value,span(begin,pos));
        }
    }
    private static void need(boolean condition,String message){if(!condition)throw new IllegalArgumentException(message);}
}
