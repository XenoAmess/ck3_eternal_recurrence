package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Same fixed debug.log producer as the original host, bound to the prepared profile, with complete line counts. */
public final class FixtureQualificationLogs {
    public record Match(String literal,long lineCount) {
        public Match { StrictJson.text(literal);StrictJson.require(lineCount>=0,"nonnegative original line count required"); }
    }
    public record Observation(boolean exists,Optional<ExactRef> source,List<Match> matches) {
        public Observation {
            Objects.requireNonNull(source);matches=List.copyOf(matches);StrictJson.require(exists==source.isPresent()&&(exists||matches.isEmpty()),"missing logs cannot supply counts/source");
        }
        public ObjectNode toJson() {
            ObjectNode n=StrictJson.object();n.put("schema","xar.ck3.engine-log-literals/v1");n.put("log_name","debug.log");n.put("exists",exists);
            var rows=n.putArray("matches");for(Match m:matches){ObjectNode row=rows.addObject();row.put("literal",m.literal());row.put("line_count",m.lineCount());}
            if(exists){n.put("bytes",source.orElseThrow().bytes());n.put("sha256",source.orElseThrow().sha256());n.put("read_only",true);n.put("case_sensitive",true);}return n;
        }
        public boolean qualified(FrontendFixturePolicy policy) {
            if(!exists)return false;
            StrictJson.require(matches.stream().map(Match::literal).toList().equals(policy.allMarkers()),"exact requested ordered fixture literals required");
            for(Match row:matches) {
                if(policy.forbiddenLogMarkers().contains(row.literal())&&row.lineCount()>0)throw new IllegalStateException("actual fixture qualification emitted forbidden marker: "+row.literal());
                if(policy.requiredLogMarkers().contains(row.literal())&&row.lineCount()>1)throw new IllegalStateException("fixture initialization was observed more than once");
            }
            return matches.stream().filter(m->policy.requiredLogMarkers().contains(m.literal())).allMatch(m->m.lineCount()==1);
        }
        public boolean any() { return matches.stream().anyMatch(m->m.lineCount()>0); }
    }
    private FixtureQualificationLogs() { }
    public static Observation fromOriginal(ExactRef original,byte[] actual,FrontendFixturePolicy policy) {
        StrictJson.require(actual.length<=64*1024*1024&&actual.length==original.bytes()&&PreparedFixture.sha(actual).equals(original.sha256()),"archived complete original fixture logs differ");
        return new Observation(true,Optional.of(original),count(actual,policy.allMarkers()));
    }
    public static Observation observe(PreparedFixture fixture)throws IOException {
        fixture.verifySources();Path path=fixture.profileDirectory().resolve("logs/debug.log");
        if(!Files.isRegularFile(path))return new Observation(false,Optional.empty(),List.of());
        Path real=path.toRealPath();StrictJson.require(real.startsWith(fixture.profileDirectory()),"fixture log escaped actual bound profile");
        var held=SharedSourceFiles.observe(real);
        StrictJson.require(held.source().bytes()<=64L*1024*1024,"refusing oversized original CK3 log above64MiB");
        byte[] raw;try(var input=Files.newInputStream(real)){raw=input.readNBytes(64*1024*1024+1);}
        StrictJson.require(raw.length<=64*1024*1024&&raw.length==held.source().bytes()&&PreparedFixture.sha(raw).equals(held.source().sha256()),"actual complete fixture log changed during bounded read");
        List<Match> counts=count(raw,fixture.policy().allMarkers());
        SharedSourceFiles.assertUnchanged(held);var f=held.source();
        return new Observation(true,Optional.of(new ExactRef(f.path(),f.bytes(),f.sha256())),counts);
    }
    /** Original Python utf8(errors=replace).splitlines(), counting containing lines rather than occurrence count. */
    static List<Match> count(byte[] raw,List<String> literals) {
        String text=new String(raw,StandardCharsets.UTF_8);String[] lines=text.split("\\r\\n|[\\n\\r\\u000b\\u000c\\u001c-\\u001e\\u0085\\u2028\\u2029]",-1);
        int count=lines.length;if(count>0&&lines[count-1].isEmpty())count--;
        List<Match> result=new ArrayList<>();for(String literal:literals){long matches=0;for(int i=0;i<count;i++)if(lines[i].contains(literal))matches++;result.add(new Match(literal,matches));}return List.copyOf(result);
    }
}
