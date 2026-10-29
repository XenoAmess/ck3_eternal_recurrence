package org.xar.ck3.control.wave3.development.wartimeconstructioncash;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m4.M4Research;

/** Pure host-fixture hook for the shared qualification launcher; this class has no main or writer. */
public final class M4HostFixtureProducer {
    public static final String ORIGINAL_SHA256 = "4b3cf840085e5f3d53e290b4ea862e1357a3341a55180ff3670675caa5f6a585";
    private M4HostFixtureProducer() { }

    public record Fixture(G2Request request, G2Response response, G2Request refusedRequest) {
        public byte[] requestUtf8() { return G2Wire.encodeRequest(request); }
        public byte[] expectedResultUtf8() { return response.result().bytes(); }
        public byte[] responseUtf8() { return G2Wire.encodeResponse(response); }
        public byte[] refusedRequestUtf8() { return G2Wire.encodeRequest(refusedRequest); }
    }

    public static Fixture produce(G2Source source) throws IOException {
        StrictJson.require(source.sourceRef().bytes() == 6379 && ORIGINAL_SHA256.equals(source.sourceRef().sha256()),
                "host sample source must identify the unchanged original31 corpus");
        JsonNode row = M4OriginalCorpus.wartimeCase("exact_ample_threshold");
        JsonNode original = row.get("request");
        var produced = M4WartimeInputProducer.produce(M4OriginalCorpus.context(original), M4OriginalCorpus.outlay(original));
        G2Request request = new G2Request("m4-exact-ample-threshold", Milestone.M4, source,
                ProjectionJson.object(produced.utf8(), M4Research.MAXIMUM_PAYLOAD_BYTES));
        // Exercise the actual common serialization route and the actual domain, rather than copying an expected result.
        G2Response response = new M4Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request)));
        StrictJson.require(row.get("expected").equals(StrictJson.parse(response.result().bytes())),
                "actual M4 host sample differs from the captured original producer");
        String raw = new String(produced.utf8(), StandardCharsets.UTF_8);
        String bad = raw.replaceFirst("\"construction_gold_raw\":[0-9]+", "\"construction_gold_raw\":23000000.0");
        StrictJson.require(!raw.equals(bad), "original host sample must carry the actual whole quoted cost");
        G2Request refused = new G2Request("m4-raw-float-refused", Milestone.M4, source,
                ProjectionJson.object(bad.getBytes(StandardCharsets.UTF_8), M4Research.MAXIMUM_PAYLOAD_BYTES));
        boolean rejected = false;
        try { new M4Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(refused))); }
        catch (IllegalArgumentException expected) { rejected = true; }
        StrictJson.require(rejected, "original floating cost token must be refused before policy evaluation");
        return new Fixture(request, response, refused);
    }
}
