package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.Milestone;

/** The ticket wire carries only a lookup claim; Native/session/source objects are never accepted. */
public final class RootG2HandoffWire {
    public static final String HTTP_PATH = "/v1/g2-research/context/handoff";
    public static final int MAX_INPUT_BYTES = ProjectionJson.MAX_BYTES;
    public record Input(String ticketId, long childPid, String childCreationFiletimeDecimal,
            Milestone milestone, ProjectionJson payload) { }
    private RootG2HandoffWire() { }
    public static Input decode(byte[] raw) throws IOException {
        if (raw == null || raw.length < 1 || raw.length > MAX_INPUT_BYTES) { throw new IllegalArgumentException("bounded Root handoff request required"); }
        ProjectionJson.object(raw, ProjectionJson.MAX_BYTES);
        // The retained payload parser remains the existing common context wire; its token is copied exactly.
        ObjectNode row = (ObjectNode) new com.fasterxml.jackson.databind.ObjectMapper().readTree(raw);
        StrictJson.object(row, Set.of("ticket_id", "child_pid", "child_creation_filetime_decimal", "milestone", "payload"));
        String ticket = StrictJson.text(row.get("ticket_id"));
        StrictJson.require(ticket.matches("[0-9a-f]{64}"), "exact Root nonce required");
        long pid = StrictJson.integer(row.get("child_pid"), 1, 0xffff_ffffL);
        String birth = StrictJson.text(row.get("child_creation_filetime_decimal"));
        StrictJson.require(birth.matches("[1-9][0-9]{0,19}") && new java.math.BigInteger(birth).bitLength() <= 64, "canonical child FILETIME required");
        String milestone = StrictJson.text(row.get("milestone"));
        StrictJson.require(milestone.matches("G2-M[0-7]"), "closed pure milestone required");
        byte[] token = payload(raw);
        byte[] prefix = ("{\"milestone\":\"" + milestone + "\",\"payload\":").getBytes(StandardCharsets.UTF_8);
        byte[] contextInput = new byte[prefix.length + token.length + 1];
        System.arraycopy(prefix, 0, contextInput, 0, prefix.length); System.arraycopy(token, 0, contextInput, prefix.length, token.length);
        contextInput[contextInput.length - 1] = '}';
        G2CallContextWire.Input context = G2CallContextWire.decodeInput(contextInput);
        return new Input(ticket, pid, birth, context.milestone(), context.payload());
    }
    private static byte[] payload(byte[] raw) throws IOException {
        try (JsonParser parser = new JsonFactory().createParser(raw)) {
            if (parser.nextToken() != JsonToken.START_OBJECT) { throw new IllegalArgumentException("handoff object required"); }
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                String name = parser.currentName(); parser.nextToken();
                if ("payload".equals(name)) {
                    int first = Math.toIntExact(parser.currentTokenLocation().getByteOffset());
                    parser.skipChildren(); parser.finishToken();
                    return Arrays.copyOfRange(raw, first, Math.toIntExact(parser.currentLocation().getByteOffset()));
                }
                parser.skipChildren();
            }
        }
        throw new IllegalArgumentException("original payload token missing");
    }
}
