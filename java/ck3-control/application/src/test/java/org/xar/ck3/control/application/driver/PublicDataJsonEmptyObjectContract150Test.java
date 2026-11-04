package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.AbstractMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

import static org.junit.jupiter.api.Assertions.*;

public final class PublicDataJsonEmptyObjectContract150Test {
    @Test
    void preservesEmptyNodeMapCallbacks150() {
        var backing = new ObservedMap();
        var node = new ObjectNode(JsonNodeFactory.instance, backing);
        backing.resetCounts();

        assertArrayEquals(utf8("{}"), PublicDataJson.encode(node).bytes());
        assertEquals(0, backing.sizeCalls);
        assertEquals(0, backing.isEmptyCalls);
        assertTrue(backing.keySetCalls > 0);

        var failure = new IllegalStateException("caller field names unavailable");
        backing.keySetFailure = failure;
        backing.resetCounts();
        var thrown = assertThrows(IllegalStateException.class, () -> PublicDataJson.encode(node));
        assertSame(failure, thrown);
        assertEquals(0, backing.sizeCalls);
        assertEquals(0, backing.isEmptyCalls);
    }

    @Test
    void keepsNodeCallsFreshAndTypedContainersOwned150() {
        var backing = new LinkedHashMap<String, JsonNode>();
        var node = new ObjectNode(JsonNodeFactory.instance, backing);
        RawJson empty = PublicDataJson.encode(node);
        byte[] exported = empty.bytes();
        exported[0] = '!';
        assertArrayEquals(utf8("{}"), empty.bytes());

        backing.put("b", new ObjectNode(JsonNodeFactory.instance));
        backing.put("a", new ObjectNode(JsonNodeFactory.instance));
        assertArrayEquals(utf8("{\"a\":{},\"b\":{}}"), PublicDataJson.encode(node).bytes());
        assertArrayEquals(utf8("{}"), empty.bytes());
        backing.clear();
        assertArrayEquals(utf8("{}"), PublicDataJson.encode(node).bytes());

        var typedBacking = new LinkedHashMap<String, OpportunityJson.Value>();
        var typed = new OpportunityJson.Obj(typedBacking);
        var child = new OpportunityJson.Obj(Map.of());
        typedBacking.put("later", child);
        RawJson typedEmpty = PublicDataJson.encodeTyped(typed);
        assertArrayEquals(utf8("{}"), typedEmpty.bytes());
        byte[] typedExported = typedEmpty.bytes();
        typedExported[1] = '!';
        assertArrayEquals(utf8("{}"), typedEmpty.bytes());
        assertArrayEquals(utf8("{\"present\":{}}"), PublicDataJson.encodeTyped(typed.with("present", child)).bytes());
        assertArrayEquals(utf8("{}"), PublicDataJson.encodeTyped(typed).bytes());
    }

    private static byte[] utf8(String value) {
        return value.getBytes(StandardCharsets.UTF_8);
    }

    /** Correct live Map views and values; counters and one armed callback fault are observable. */
    private static final class ObservedMap extends AbstractMap<String, JsonNode> {
        private final LinkedHashMap<String, JsonNode> entries = new LinkedHashMap<>();
        private int sizeCalls;
        private int isEmptyCalls;
        private int keySetCalls;
        private RuntimeException keySetFailure;

        @Override public Set<Map.Entry<String, JsonNode>> entrySet() { return entries.entrySet(); }
        @Override public JsonNode put(String key, JsonNode value) { return entries.put(key, value); }
        @Override public JsonNode remove(Object key) { return entries.remove(key); }
        @Override public void clear() { entries.clear(); }
        @Override public int size() { sizeCalls++; return entries.size(); }
        @Override public boolean isEmpty() { isEmptyCalls++; return entries.isEmpty(); }
        @Override public Set<String> keySet() {
            keySetCalls++;
            if (keySetFailure != null) throw keySetFailure;
            return entries.keySet();
        }
        private void resetCounts() { sizeCalls = 0; isEmptyCalls = 0; keySetCalls = 0; }
    }
}
