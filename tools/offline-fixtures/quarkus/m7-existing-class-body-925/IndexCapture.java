package org.xar.fixture.indexnext;

import io.quarkus.deployment.annotations.BuildStep;
import io.quarkus.deployment.builditem.CombinedIndexBuildItem;
import io.quarkus.deployment.builditem.ServiceStartBuildItem;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.UUID;
import org.jboss.jandex.ClassInfo;
import org.jboss.jandex.DotName;
import org.jboss.jandex.IndexView;

/** Private diagnostic extension: consumes the actual augmentation item; never adds an indexed class. */
public final class IndexCapture {
    @BuildStep
    public ServiceStartBuildItem capture(CombinedIndexBuildItem actual) throws IOException {
        String nonce = System.getProperty("fixture.nonce");
        String mode = System.getProperty("fixture.mode");
        if (nonce == null || !nonce.matches("[a-f0-9-]{36}")
                || !"positive".equals(mode)) {
            throw new IllegalStateException("explicit private fixture identity required");
        }
        Path base = Path.of(System.getProperty("fixture.base")).toAbsolutePath().normalize();
        Path evidence = Path.of(System.getProperty("fixture.evidence")).toAbsolutePath().normalize();
        if (!evidence.startsWith(base) || evidence.equals(base) || !Files.isDirectory(evidence)) {
            throw new IllegalStateException("private existing evidence directory required");
        }
        // getComputingIndex() can resolve missing classes on demand and is deliberately not used.
        IndexView index = actual.getIndex();
        String first = "org.xar.fixture.indexnext.ProbeResource";
        String body = "{\"nonce\":" + quote(nonce) + ",\"mode\":" + quote(mode)
                + ",\"at_utc\":" + quote(Instant.now().toString())
                + ",\"pid\":" + ProcessHandle.current().pid()
                + ",\"index_class\":" + quote(index.getClass().getName())
                + ",\"index_identity\":" + System.identityHashCode(index)
                + ",\"uses_actual_CombinedIndexBuildItem_getIndex\":true"
                + ",\"uses_computing_index\":false,\"family\":["
                + entry(index, first) + "]}";
        Files.writeString(evidence.resolve("index-" + UUID.randomUUID() + ".json"), body + "\n",
                StandardOpenOption.CREATE_NEW);
        System.out.println("INDEX_NEXT_ACTUAL_AUGMENTATION " + body);
        // BuildStep documentation requires a consumed output; a void observer could be pruned.
        return new ServiceStartBuildItem("contracts-index-next-capture");
    }

    private static String entry(IndexView index, String name) {
        ClassInfo info = index.getClassByName(DotName.createSimple(name));
        return "{\"name\":" + quote(name) + ",\"present\":" + (info != null)
                + (info == null ? "" : ",\"flags\":" + info.flags() + ",\"fields\":" + info.fields().size()
                    + ",\"methods\":" + info.methods().size()) + "}";
    }

    private static String quote(String value) {
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\r", "\\r").replace("\n", "\\n") + "\"";
    }
}
