package org.xar.ck3.control.build.runtime;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;

final class RootStartupInvocationTest {
    @TempDir Path temporary;
    @Test void actualExactFilesRoundtripAndReachOriginalThreeOrSixArgumentContract()throws Exception {
        Path startup=temporary.resolve("startup.json"),saved=temporary.resolve("saved.json");Files.writeString(startup,"{\"actual\":true}");Files.writeString(saved,"{\"saved\":true}");
        var first=ControlBuild.FileRef.measure(startup);var second=ControlBuild.FileRef.measure(saved);
        for(var optional:List.of(Optional.<ControlBuild.FileRef>empty(),Optional.of(second))) {
            var original=new RootStartupInvocation(first,optional);var decoded=RootStartupInvocation.decode(original.encode());assertEquals(original,decoded);
            var args=decoded.arguments();assertEquals(optional.isPresent()?6:3,args.size());assertEquals(first.path(),args.getFirst());assertEquals(Long.toString(first.bytes()),args.get(1));assertEquals(first.sha256(),args.get(2));
            if(optional.isPresent())assertEquals(List.of(second.path(),Long.toString(second.bytes()),second.sha256()),args.subList(3,6));
            assertThrows(UnsupportedOperationException.class,()->args.add("unreviewed"));
        }
    }
    @Test void strictCodecRejectsMissingNullStartupUnknownAndBooleanOrFloatByteCounts()throws Exception {
        Path source=temporary.resolve("startup.json");Files.writeString(source,"{}");var invocation=new RootStartupInvocation(ControlBuild.FileRef.measure(source),Optional.empty());
        var mapper=ControlBuild.strictMapper();var row=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(invocation.encode());
        for(String field:List.of("schema","startup","saved_request")) {var changed=row.deepCopy();changed.remove(field);assertThrows(Exception.class,()->RootStartupInvocation.decode(mapper.writeValueAsBytes(changed)));}
        for(var value:List.of(mapper.getNodeFactory().booleanNode(true),mapper.getNodeFactory().numberNode(2.0))) {
            var changed=row.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)changed.get("startup")).set("bytes",value);assertThrows(Exception.class,()->RootStartupInvocation.decode(mapper.writeValueAsBytes(changed)));
        }
        var extra=row.deepCopy();extra.put("started",true);assertThrows(Exception.class,()->RootStartupInvocation.decode(mapper.writeValueAsBytes(extra)));
        var nil=row.deepCopy();nil.putNull("startup");assertThrows(Exception.class,()->RootStartupInvocation.decode(mapper.writeValueAsBytes(nil)));
    }
}
