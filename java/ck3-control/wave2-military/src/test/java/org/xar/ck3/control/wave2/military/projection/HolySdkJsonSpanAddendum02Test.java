package org.xar.ck3.control.wave2.military.projection;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

/** Actual byte-stream parser spans: strings may still be lazy when nextToken returns VALUE_STRING. */
final class HolySdkJsonSpanAddendum02Test {
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }

    @Test void nestedEscapedAndMultibyteStringsHaveCompleteOriginalByteSpans() {
        String token = "\"quote:\\\" slash:\\\\ line:\\n snow:" + Character.toString(0x96EA)
                + " compass:" + new String(Character.toChars(0x1F9ED)) + "\"";
        String escaped = "\"" + "\\" + "u96ea" + "\"";
        String meta = "{\"value\":" + token + ",\"items\":[\"head\",{\"inner\":" + token
                + "},\"tail\"],\"empty\":\"\",\"escaped\":" + escaped
                + ",\"signed\":-0.0,\"id\":18446744073709551615}";
        var source = new HolySdkJson.Source(utf8("{\"meta\":" + meta + ",\"last\":\"done\"}"));
        assertArrayEquals(utf8(token), source.token("/meta/value"));
        assertArrayEquals(utf8(token), source.token("/meta/items/1/inner"));
        assertArrayEquals(utf8("{\"inner\":" + token + "}"), source.token("/meta/items/1"));
        assertArrayEquals(utf8("\"head\""), source.token("/meta/items/0"));
        assertArrayEquals(utf8("\"tail\""), source.token("/meta/items/2"));
        assertArrayEquals(utf8("\"\""), source.token("/meta/empty"));
        assertArrayEquals(utf8(escaped), source.token("/meta/escaped"));
        assertArrayEquals(utf8("\"done\""), source.token("/last"));
        assertArrayEquals(utf8("-0.0"), source.token("/meta/signed"));
        assertArrayEquals(utf8("18446744073709551615"), source.token("/meta/id"));
        assertArrayEquals(utf8(meta), source.select("/meta").bytes());
        assertArrayEquals(utf8(token), source.select("/meta").token("/items/1/inner"));
    }

    @Test void relocatedStringAndNegativeZeroUseTheirActualCompleteTokens() {
        String token = "\"nested:\\\" " + Character.toString(0x96EA) + " \\\\ end\"";
        var source = new HolySdkJson.Source(utf8("{\"sdk\":{\"text\":" + token + ",\"signed\":-0.0}}"));
        ObjectNode result = StrictJson.object();
        result.set("moved", source.tree().at("/sdk/text"));
        result.set("negative", source.tree().at("/sdk/signed"));
        byte[] actual = source.merge(result, "/missing",
                Map.of("/moved", "/sdk/text", "/negative", "/sdk/signed"));
        assertArrayEquals(utf8("{\"moved\":" + token + ",\"negative\":-0.0}"), actual);
    }
}
