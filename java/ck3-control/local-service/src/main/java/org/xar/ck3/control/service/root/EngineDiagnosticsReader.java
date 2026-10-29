package org.xar.ck3.control.service.root;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.PushbackInputStream;
import java.io.Reader;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.regex.Pattern;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog.TextRules;
import static org.xar.ck3.control.service.root.EngineDiagnostics.*;

/** Fixed-name, source-bound filesystem producer. No caller-supplied path or regular expression enters this reader. */
final class EngineDiagnosticsReader {
    private static final Pattern LEVEL=Pattern.compile("^\\[[^\\]]+\\]\\[([EFW])\\]");
    private static final Pattern HEX=Pattern.compile("0x[0-9A-Fa-f]+");
    private static final String WORD="[\\p{L}\\p{N}_]";
    private static final String BOUNDARY="(?:(?<="+WORD+")(?!"+WORD+")|(?<!"+WORD+")(?="+WORD+"))";
    private static final Pattern UUID=Pattern.compile("(?<!"+WORD+")[0-9A-Fa-f]{8}-[0-9A-Fa-f-]{27,}"+BOUNDARY);
    private static final Pattern NUMBER=Pattern.compile("(?<!"+WORD+")\\p{Nd}+(?!"+WORD+")");
    private static final Pattern PACKAGE=Pattern.compile("ck3_[0-9]{8}_[0-9]{6}");
    private static final Pattern META=Pattern.compile("^([A-Za-z0-9_]+):(.*)$");
    private static final List<String> MILESTONES=List.of("initializing game","game initialization","main menu","checksum","loading map","loaded map","startup");
    private final RootEngineDiagnosticsPublicProducts.Prepared authority;
    EngineDiagnosticsReader(RootEngineDiagnosticsPublicProducts.Prepared authority){this.authority=java.util.Objects.requireNonNull(authority);}
    Diagnostics diagnostics(Query query,Instant deadline)throws IOException {
        Path profile=authority.requireCurrent();var logs=new EnumMap<LogName,LogRecord>(LogName.class);
        for(var name:LogName.values()){check(deadline);Path path=profile.resolve("logs").resolve(name.wire());
            if(!regular(path)){logs.put(name,MissingLog.INSTANCE);continue;}
            var accumulator=new LogAccumulator(name,query,authority.textRules());FileRecord file=read(path,MAX_LOG_BYTES,deadline,accumulator::line);
            logs.put(name,accumulator.finish(file));}
        Path root=profile.resolve("crashes");SharedSourceFiles.plainAncestors(root);List<Path> packages=new ArrayList<>();boolean exists=Files.isDirectory(root,LinkOption.NOFOLLOW_LINKS);
        if(exists)try(var entries=Files.newDirectoryStream(root)){for(Path entry:entries){check(deadline);if(PACKAGE.matcher(entry.getFileName().toString()).matches()&&Files.isDirectory(entry)){SharedSourceFiles.plainAncestors(entry);packages.add(entry);if(packages.size()>32)throw new IOException("refusing to inspect more than32 crash packages");}}}
        packages.sort(Comparator.comparing((Path path)->path.getFileName().toString()).reversed());List<Crash> crashes=new ArrayList<>();for(Path path:packages)crashes.add(crash(path,deadline));
        authority.requireCurrent();check(deadline);return new Diagnostics(profile,logs,new Crashes(exists,crashes));
    }
    Literals literals(LiteralQuery query,Instant deadline)throws IOException {
        Path profile=authority.requireCurrent(),path=profile.resolve("logs").resolve(query.logName().wire());
        if(!regular(path)){authority.requireCurrent();return new Literals(query.logName(),false,0,null,0,List.of());}
        var counts=new LiteralAccumulator(query);FileRecord file=read(path,MAX_LOG_BYTES,deadline,counts::line);
        authority.requireCurrent();check(deadline);return counts.finish(file);
    }
    private Crash crash(Path packageRoot,Instant deadline)throws IOException {
        SharedSourceFiles.plainAncestors(packageRoot);var directory=SharedSourceFiles.nativeDirectory(packageRoot);
        List<String> exception=new ArrayList<>();var files=new EnumMap<CrashFile,FileRecord>(CrashFile.class);
        Path exceptionPath=packageRoot.resolve("exception.txt");files.put(CrashFile.EXCEPTION,readOptional(exceptionPath,MAX_CRASH_TEXT_BYTES,deadline,line->{String value=authority.textRules().strip(line);if(!value.isEmpty())exception.add(value);}));
        String headline=null;List<String> stack=List.of();for(String value:exception)if(value.startsWith("Unhandled Exception")){headline=bounded(value);break;}
        int start=exception.indexOf("Stack Trace:");if(start>=0)stack=exception.subList(start+1,Math.min(exception.size(),start+33)).stream().map(EngineDiagnosticsReader::bounded).toList();
        var meta=new EnumMap<MetaKey,String>(MetaKey.class);List<String> mods=new ArrayList<>();
        files.put(CrashFile.META,readOptional(packageRoot.resolve("meta.yml"),MAX_CRASH_TEXT_BYTES,deadline,line->{var match=META.matcher(authority.textRules().strip(line));if(!match.matches())return;String key=match.group(1),value=authority.textRules().strip(match.group(2));int a=0,b=value.length();while(a<b&&value.charAt(a)=='"')a++;while(b>a&&value.charAt(b-1)=='"')b--;String text=bounded(value.substring(a,b));var known=MetaKey.find(key);if(known.isPresent())meta.put(known.orElseThrow(),text);else if(key.startsWith("Mod_")&&mods.size()<256)mods.add(text);}));
        for(var name:CrashFile.values())if(!files.containsKey(name))files.put(name,readOptional(packageRoot.resolve(name.wire()),Long.MAX_VALUE,deadline,null));
        if(!directory.equals(SharedSourceFiles.nativeDirectory(packageRoot)))throw new IOException("original crash directory identity changed");
        return new Crash(packageRoot.getFileName().toString(),new ExceptionRecord(headline,stack),meta,mods,files);
    }
    private static final class Group {long count;final String sample;Group(String sample){this.sample=sample;}}
    private static final class LogAccumulator {
        final LogName name;final Query query;final TextRules text;long lines,nonempty,fatal,error,warning;
        final ArrayDeque<String> milestones=new ArrayDeque<>(),tail=new ArrayDeque<>();final Map<String,Group> groups=new HashMap<>();
        LogAccumulator(LogName name,Query query,TextRules text){this.name=name;this.query=query;this.text=text;}
        void line(String line){lines++;var level=LEVEL.matcher(line);String severity=level.find()?level.group(1):null;
            if("F".equals(severity))fatal++;if("E".equals(severity))error++;if("W".equals(severity))warning++;
            if(text.strip(line).isEmpty())return;nonempty++;push(tail,bounded(line),query.tailLimit());
            String folded=text.fold(line);if(MILESTONES.stream().anyMatch(folded::contains))push(milestones,bounded(line),40);
            if(name.fingerprints()&&severity!=null){String value=line.substring(level.end());int offset=0;while(offset<value.length()&&text.whitespace().contains(value.codePointAt(offset)))offset+=Character.charCount(value.codePointAt(offset));
                value=value.substring(offset);value=HEX.matcher(value).replaceAll("<hex>");value=UUID.matcher(value).replaceAll("<uuid>");value=bounded(NUMBER.matcher(value).replaceAll("<n>"));
                Group group=groups.computeIfAbsent(value,ignored->new Group(bounded(line)));group.count++;}
        }
        PresentLog finish(FileRecord file){Optional<Fingerprints> fingerprints=Optional.empty();if(name.fingerprints()){
            var ordered=new ArrayList<>(groups.entrySet());ordered.sort((a,b)->{int count=Long.compare(b.getValue().count,a.getValue().count);return count!=0?count:scalarCompare(a.getKey(),b.getKey());});
            var values=ordered.stream().limit(query.fingerprintLimit()).map(row->new Fingerprint(row.getValue().count,row.getKey(),row.getValue().sample)).toList();fingerprints=Optional.of(new Fingerprints(ordered.size(),values,ordered.size()>query.fingerprintLimit()));}
            return new PresentLog(file.bytes(),file.sha256(),lines,nonempty,new Severity(fatal,error,warning),List.copyOf(milestones),List.copyOf(tail),fingerprints);}
    }
    private static final class LiteralAccumulator {
        final LiteralQuery query;final long[] counts;final List<List<Sample>> samples=new ArrayList<>();long lines;
        LiteralAccumulator(LiteralQuery query){this.query=query;counts=new long[query.literals().size()];for(int i=0;i<counts.length;i++)samples.add(new ArrayList<>());}
        void line(String line){lines++;for(int i=0;i<counts.length;i++)if(line.contains(query.literals().get(i))){counts[i]++;if(samples.get(i).size()<query.sampleLimit())samples.get(i).add(new Sample(lines,bounded(line)));}}
        Literals finish(FileRecord file){List<Match> matches=new ArrayList<>();for(int i=0;i<counts.length;i++)matches.add(new Match(query.literals().get(i),counts[i],samples.get(i)));return new Literals(query.logName(),true,file.bytes(),file.sha256(),lines,matches);}
    }
    private static void push(ArrayDeque<String> values,String value,int limit){values.addLast(value);if(values.size()>limit)values.removeFirst();}
    static String bounded(String value){int count=value.codePointCount(0,value.length());return count<=MAX_LINE_CHARS?value:value.substring(0,value.offsetByCodePoints(0,MAX_LINE_CHARS))+"…";}
    static int scalarCompare(String a,String b){int x=0,y=0;while(x<a.length()&&y<b.length()){int ac=a.codePointAt(x),bc=b.codePointAt(y);if(ac!=bc)return Integer.compare(ac,bc);x+=Character.charCount(ac);y+=Character.charCount(bc);}return Integer.compare(a.length()-x,b.length()-y);}
    static PresentLog summarize(LogName name,byte[] bytes,Query query,TextRules text)throws IOException {
        require(bytes.length<=MAX_LOG_BYTES,"bounded original payload required");var value=new LogAccumulator(name,query,text);
        try(var reader=new PythonUtf8Reader(new java.io.ByteArrayInputStream(bytes))){lines(reader,value::line);}
        return value.finish(new FileRecord(true,bytes.length,sha(bytes)));
    }
    static Literals summarize(byte[] bytes,LiteralQuery query)throws IOException {
        require(bytes.length<=MAX_LOG_BYTES,"bounded original payload required");var value=new LiteralAccumulator(query);
        try(var reader=new PythonUtf8Reader(new java.io.ByteArrayInputStream(bytes))){lines(reader,value::line);}
        return value.finish(new FileRecord(true,bytes.length,sha(bytes)));
    }
    @FunctionalInterface private interface LineSink {void line(String line)throws IOException;}
    private FileRecord readOptional(Path path,long maximum,Instant deadline,LineSink sink)throws IOException {return regular(path)?read(path,maximum,deadline,sink):new FileRecord(false,0,null);}
    private static boolean regular(Path path)throws IOException {SharedSourceFiles.plainAncestors(path);return Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS);}
    private FileRecord read(Path path,long maximum,Instant deadline,LineSink sink)throws IOException {
        check(deadline);Path profile=authority.profile();if(!path.normalize().startsWith(profile))throw new IOException("diagnostic artifact escapes actual profile");
        var before=SharedSourceFiles.nativeFile(path);if(before.logicalBytes()>maximum)throw new IOException("refusing oversized fixed diagnostic artifact: "+path.getFileName());
        MessageDigest digest=digest();long count;
        try(var raw=new Counted(Files.newInputStream(path),digest,maximum,deadline)) {
            if(sink==null){byte[] buffer=new byte[65536];while(raw.read(buffer)!=-1)check(deadline);}
            else try(var reader=new PythonUtf8Reader(new BufferedInputStream(raw,65536))){lines(reader,sink);}
            count=raw.count;
        }
        if(count!=before.logicalBytes()||!before.equals(SharedSourceFiles.nativeFile(path)))throw new IOException("diagnostic original file identity/content metadata changed during read");
        check(deadline);return new FileRecord(true,count,HexFormat.of().formatHex(digest.digest()));
    }
    private final class Counted extends FilterInputStream {
        final MessageDigest digest;final long maximum;final Instant deadline;long count;
        Counted(InputStream source,MessageDigest digest,long maximum,Instant deadline){super(source);this.digest=digest;this.maximum=maximum;this.deadline=deadline;}
        @Override public int read()throws IOException {check(deadline);int value=in.read();if(value>=0){count=Math.addExact(count,1);if(count>maximum)throw new IOException("diagnostic source grew beyond fixed limit");digest.update((byte)value);}return value;}
        @Override public int read(byte[] bytes,int offset,int length)throws IOException {check(deadline);int size=in.read(bytes,offset,length);if(size>0){count=Math.addExact(count,size);if(count>maximum)throw new IOException("diagnostic source grew beyond fixed limit");digest.update(bytes,offset,size);}return size;}
    }
    private void check(Instant deadline)throws IOException {if(!authority.clock().instant().isBefore(deadline))throw new IOException("bounded engine diagnostics deadline elapsed");}
    private static MessageDigest digest(){try{return MessageDigest.getInstance("SHA-256");}catch(NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}
    private static String sha(byte[] bytes){return HexFormat.of().formatHex(digest().digest(bytes));}
    /** CPython splitlines includes VT/FF/FS/GS/RS/NEL/Unicode separators and removes one CRLF pair. */
    private static void lines(Reader source,LineSink sink)throws IOException {
        try(var reader=new BufferedReader(source,8192)){StringBuilder line=new StringBuilder();boolean carriage=false;int value;
            while((value=reader.read())!=-1){if(carriage&&value==10){carriage=false;continue;}carriage=false;
                if(value==10||value==11||value==12||value==13||value==28||value==29||value==30||value==133||value==8232||value==8233){sink.line(line.toString());line.setLength(0);carriage=value==13;}
                else line.append((char)value);}
            if(!line.isEmpty())sink.line(line.toString());}
    }
    /** CPython errors=replace consumes only the valid prefix of a malformed sequence, including surrogate encodings. */
    private static final class PythonUtf8Reader extends Reader {
        final PushbackInputStream bytes;int pending=-1;
        PythonUtf8Reader(InputStream bytes){this.bytes=new PushbackInputStream(bytes,1);}
        @Override public int read()throws IOException {
            if(pending>=0){int value=pending;pending=-1;return value;}int first=bytes.read();if(first<0||first<128)return first;
            int count,point;if(first>=194&&first<=223){count=2;point=first&31;}else if(first>=224&&first<=239){count=3;point=first&15;}else if(first>=240&&first<=244){count=4;point=first&7;}else return 65533;
            for(int i=1;i<count;i++){int next=bytes.read();if(next<0)return 65533;boolean bad=next<128||next>191
                    ||i==1&&(first==224&&next<160||first==237&&next>159||first==240&&next<144||first==244&&next>143);
                if(bad){bytes.unread(next);return 65533;}point=(point<<6)|(next&63);}
            if(point<=65535)return point;int supplementary=point-65536;pending=56320+(supplementary&1023);return 55296+(supplementary>>10);
        }
        @Override public int read(char[] target,int offset,int length)throws IOException {java.util.Objects.checkFromIndexSize(offset,length,target.length);if(length==0)return 0;int count=0;while(count<length){int value=read();if(value<0)return count==0?-1:count;target[offset+count++]=(char)value;}return count;}
        @Override public void close()throws IOException {bytes.close();}
    }
}
