package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.StrictJson;

/** One typed contract for original configured-profile diagnostics and literal counts. */
public final class EngineDiagnostics {
    public static final String SCHEMA="xar.ck3.engine-diagnostics/v1",LITERALS_SCHEMA="xar.ck3.engine-log-literals/v1";
    public static final int MAX_LOG_BYTES=64<<20,MAX_CRASH_TEXT_BYTES=2<<20,MAX_LINE_CHARS=2000;
    private EngineDiagnostics() { }
    public enum LogName {
        ERROR("error.log",true),DEBUG("debug.log",false),GAME("game.log",true),SYSTEM("system.log",false),GUI("gui_warnings.log",true);
        private final String wire;private final boolean fingerprints;
        LogName(String wire,boolean fingerprints){this.wire=wire;this.fingerprints=fingerprints;}
        public String wire(){return wire;}public boolean fingerprints(){return fingerprints;}
        public static LogName decode(String value){for(var name:values())if(name.wire.equals(value))return name;throw new IllegalArgumentException("fixed CK3 log name required");}
    }
    public enum CrashFile {
        EXCEPTION("exception.txt"),META("meta.yml"),MINIDUMP("minidump.dmp"),ERROR("logs/error.log"),DEBUG("logs/debug.log"),GAME("logs/game.log");
        private final String wire;CrashFile(String wire){this.wire=wire;}public String wire(){return wire;}
    }
    public enum MetaKey {
        AppName,AppVersion,DateTime,BuildType,Platform,Store,Architecture,OperatingSystem,SystemLanguage,SystemMemory,GPUName,GPUVendor,GPUDedicatedMemory,LaunchArguments;
        static Optional<MetaKey> find(String name){for(var key:values())if(key.name().equals(name))return Optional.of(key);return Optional.empty();}
    }
    public record Query(int fingerprintLimit,int tailLimit) {
        public Query{require(fingerprintLimit>=1&&fingerprintLimit<=100,"fingerprint_limit must be1..100");require(tailLimit>=1&&tailLimit<=100,"tail_limit must be1..100");}
    }
    public record LiteralQuery(LogName logName,List<String> literals,int sampleLimit) {
        public LiteralQuery {
            Objects.requireNonNull(logName);literals=List.copyOf(literals);require(literals.size()>=1&&literals.size()<=16,"literals must contain1..16 values");
            for(String value:literals)require(value!=null&&value.codePointCount(0,value.length())>=1&&value.codePointCount(0,value.length())<=160
                    &&value.indexOf(13)<0&&value.indexOf(10)<0&&value.indexOf(0)<0,"single-line bounded literal required");
            require(literals.stream().distinct().count()==literals.size(),"literals must be distinct");require(sampleLimit>=0&&sampleLimit<=5,"sample_limit must be0..5");
        }
    }
    public sealed interface LogRecord permits MissingLog,PresentLog { }
    public enum MissingLog implements LogRecord { INSTANCE }
    public record Severity(long fatal,long error,long warning){ }
    public record Fingerprint(long occurrences,String fingerprint,String sample){ }
    public record Fingerprints(long uniqueCount,List<Fingerprint> values,boolean truncated){public Fingerprints{values=List.copyOf(values);}}
    public record PresentLog(long bytes,String sha256,long lineCount,long nonemptyLineCount,Severity severity,
            List<String> milestones,List<String> tail,Optional<Fingerprints> fingerprints)implements LogRecord {
        public PresentLog{require(bytes>=0&&bytes<=MAX_LOG_BYTES,"bounded complete log required");digest(sha256);Objects.requireNonNull(severity);
            milestones=List.copyOf(milestones);tail=List.copyOf(tail);Objects.requireNonNull(fingerprints);}
    }
    public record FileRecord(boolean exists,long bytes,String sha256) {
        public FileRecord{require(bytes>=0,"nonnegative artifact bytes required");if(exists)digest(sha256);else require(bytes==0&&sha256==null,"missing artifact has zero bytes/null SHA");}
    }
    public record ExceptionRecord(String headline,List<String> stackTrace){public ExceptionRecord{stackTrace=List.copyOf(stackTrace);}}
    public record Crash(String name,ExceptionRecord exception,Map<MetaKey,String> meta,List<String> mods,Map<CrashFile,FileRecord> files) {
        public Crash{require(name.matches("ck3_[0-9]{8}_[0-9]{6}"),"fixed crash package name required");Objects.requireNonNull(exception);meta=Map.copyOf(meta);mods=List.copyOf(mods);files=Map.copyOf(files);require(files.size()==CrashFile.values().length,"complete fixed crash file inventory required");}
    }
    public record Crashes(boolean exists,List<Crash> packages){public Crashes{packages=List.copyOf(packages);require(packages.size()<=32,"at most32 crash packages allowed");}}
    public record Diagnostics(Path profile,Map<LogName,LogRecord> logs,Crashes crashes) {
        public Diagnostics{Objects.requireNonNull(profile);require(profile.isAbsolute(),"actual profile required");logs=Map.copyOf(logs);require(logs.size()==LogName.values().length,"all fixed logs required");Objects.requireNonNull(crashes);}
    }
    public record Sample(long lineNumber,String text){ }
    public record Match(String literal,long lineCount,List<Sample> samples){public Match{samples=List.copyOf(samples);}}
    public record Literals(LogName logName,boolean exists,long bytes,String sha256,long scannedLineCount,List<Match> matches) {
        public Literals{Objects.requireNonNull(logName);matches=List.copyOf(matches);if(exists){require(bytes>=0&&bytes<=MAX_LOG_BYTES,"bounded complete literal log required");digest(sha256);}else require(bytes==0&&sha256==null&&scannedLineCount==0&&matches.isEmpty(),"exact absent-log shape required");}
    }
    static void digest(String sha){require(sha!=null&&sha.matches("[0-9a-f]{64}"),"exact lowercase SHA256 required");}
    static void require(boolean value,String detail){if(!value)throw new IllegalArgumentException(detail);}
    public static RawJson encode(Diagnostics actual) {
        ObjectNode root=StrictJson.object();root.put("schema",SCHEMA);root.put("profile_dir",actual.profile().toString());var names=root.putArray("fixed_log_names");
        ObjectNode logs=root.putObject("logs");for(var name:LogName.values()){names.add(name.wire());logs.set(name.wire(),log(actual.logs().get(name)));}
        var crashes=root.putObject("crashes");crashes.put("exists",actual.crashes().exists());crashes.put("package_count",actual.crashes().packages().size());var packages=crashes.putArray("packages");
        for(var crash:actual.crashes().packages()) {
            var row=packages.addObject();row.put("package",crash.name());var exception=row.putObject("exception");
            if(crash.exception().headline()==null)exception.putNull("headline");else exception.put("headline",crash.exception().headline());
            var stack=exception.putArray("stack_trace");crash.exception().stackTrace().forEach(stack::add);
            var meta=row.putObject("meta");crash.meta().forEach((key,value)->meta.put(key.name(),value));var mods=row.putArray("mods");crash.mods().forEach(mods::add);
            var files=row.putObject("files");for(var name:CrashFile.values()){var value=crash.files().get(name);var file=files.putObject(name.wire());file.put("exists",value.exists());file.put("bytes",value.bytes());if(value.sha256()==null)file.putNull("sha256");else file.put("sha256",value.sha256());}
        }
        root.put("path_argument_accepted",false);root.put("regex_argument_accepted",false);root.put("read_only",true);return PublicDataJson.encode(root);
    }
    public static ObjectNode log(LogRecord actual) {
        ObjectNode row=StrictJson.object();row.put("exists",actual instanceof PresentLog);if(actual instanceof MissingLog)return row;
        var value=(PresentLog)actual;row.put("bytes",value.bytes());row.put("sha256",value.sha256());row.put("line_count",value.lineCount());row.put("nonempty_line_count",value.nonemptyLineCount());
        var severity=row.putObject("engine_severity_records");severity.put("fatal",value.severity().fatal());severity.put("error",value.severity().error());severity.put("warning",value.severity().warning());
        row.put("severity_count_semantics","log records, not independent bugs");var milestones=row.putArray("milestones");value.milestones().forEach(milestones::add);var tail=row.putArray("tail");value.tail().forEach(tail::add);
        value.fingerprints().ifPresent(groups->{row.put("unique_fingerprint_count",groups.uniqueCount());var entries=row.putArray("fingerprints");for(var group:groups.values()){var entry=entries.addObject();entry.put("occurrences",group.occurrences());entry.put("fingerprint",group.fingerprint());entry.put("sample",group.sample());}row.put("fingerprints_truncated",groups.truncated());row.put("fingerprint_count_semantics","normalized message groups, not confirmed independent bugs");});return row;
    }
    public static RawJson encode(Literals actual) {
        ObjectNode root=StrictJson.object();root.put("schema",LITERALS_SCHEMA);root.put("log_name",actual.logName().wire());root.put("exists",actual.exists());
        var matches=root.putArray("matches");for(var match:actual.matches()){var row=matches.addObject();row.put("literal",match.literal());row.put("line_count",match.lineCount());var samples=row.putArray("samples");for(var sample:match.samples()){var item=samples.addObject();item.put("line_number",sample.lineNumber());item.put("text",sample.text());}}
        if(actual.exists()){root.put("bytes",actual.bytes());root.put("sha256",actual.sha256());root.put("scanned_line_count",actual.scannedLineCount());root.put("match_count_semantics","lines containing each literal, not independent bugs");root.put("case_sensitive",true);root.put("regex_argument_accepted",false);root.put("path_argument_accepted",false);root.put("read_only",true);}return PublicDataJson.encode(root);
    }
}
