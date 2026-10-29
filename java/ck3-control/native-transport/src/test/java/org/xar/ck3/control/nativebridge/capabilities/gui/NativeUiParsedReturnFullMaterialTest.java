package org.xar.ck3.control.nativebridge.capabilities.gui;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Authored packet DATA exercises the shared parser/serializer; no Native or Game admission. */
final class NativeUiParsedReturnFullMaterialTest {
    private static final String ID = "software-parsed-full-material";
    private static byte[] request(String step) throws java.io.IOException {
        return NativeWire.execute(ID, step, BigInteger.valueOf(3),
                StrictJson.canonical(StrictJson.object().put("window_kind", "combat").put("subject_id", 0)));
    }
    private static byte[] result(String id, boolean ok) throws java.io.IOException {
        var body = StrictJson.object().put("type", "command_result").put("protocol_version", 1)
                .put("request_id", id).put("ok", ok).put("error", ok ? "" : "original native refusal");
        body.putObject("result").put("schema", "software-result-data").put("nullable", (String) null).putArray("empty");
        return NativeWire.packet(StrictJson.canonical(body));
    }
    private static OpportunityJson.Obj before() {
        return new OpportunityJson.Obj(Map.of("snapshot_id", new OpportunityJson.Text("software-full-before"),
                "revision", new OpportunityJson.IntegerValue(BigInteger.valueOf(4)),
                "native_revision", new OpportunityJson.IntegerValue(BigInteger.valueOf(3))));
    }

    @Test void completeBeforeLongNumbersAndDecimalTokensRoundtripWithoutNativePromotion() throws Exception {
        var complete = before().with("long_integer", new OpportunityJson.IntegerValue(new BigInteger("9".repeat(70000))))
                .with("long_decimal", new OpportunityJson.DecimalValue("0." + "0".repeat(5000) + "1"))
                .with("negative_zero", new OpportunityJson.DecimalValue("-0.0"))
                .with("exponent", new OpportunityJson.DecimalValue("1e999"));
        RawJson material = PublicDataJson.encodeFullMaterial(complete);
        assertThrows(IllegalArgumentException.class, () -> new RawJson(material.bytes()));
        assertThrows(IllegalArgumentException.class, material::requireProtocolBound);
        byte[] outbound = request("query-ingame-ui-window-v1"), inbound = result(ID, true);
        RawJson wrapper = NativeUiParsedReturn.encode(outbound, inbound, complete);
        OpportunityJson.Obj decoded = NativeUiParsedReturn.decode(wrapper.bytes());
        assertEquals(complete, decoded.get("actual_pre_submission_snapshot"));
        assertEquals(new OpportunityJson.DecimalValue("-0.0"), OpportunityJson.object(decoded.get("actual_pre_submission_snapshot"), "before").get("negative_zero"));
        assertEquals(DriverJson.object(Arrays.copyOfRange(outbound, Integer.BYTES, outbound.length), NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES), decoded.get("request"));
        assertEquals(DriverJson.object(Arrays.copyOfRange(inbound, Integer.BYTES, inbound.length), NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES), decoded.get("original_parsed_command_result"));
        assertThrows(IllegalArgumentException.class, wrapper::requireProtocolBound);
        assertArrayEquals(wrapper.bytes(), PublicDataJson.encodeFullMaterial(decoded).bytes());
    }

    @Test void originalRefusalAndAllSixWrapperRolesRemainExact() throws Exception {
        RawJson wrapper = NativeUiParsedReturn.encode(request("navigate-ingame-ui-v1"), result(ID, false), before());
        OpportunityJson.Obj actual = NativeUiParsedReturn.decode(wrapper.bytes());
        var originalResult = OpportunityJson.object(actual.get("original_parsed_command_result"), "result");
        assertEquals(new OpportunityJson.Bool(false), originalResult.get("ok"));
        assertEquals(new OpportunityJson.Text("original native refusal"), originalResult.get("error"));
        assertEquals(new OpportunityJson.Text("unvalidated"), actual.get("validation_state"));
        assertEquals(new OpportunityJson.Bool(false), actual.get("wire_bytes_preserved"));
        assertEquals(6, actual.members().size());
        assertThrows(IllegalArgumentException.class, () -> NativeUiParsedReturn.encode(request("navigate-ingame-ui-v1"), result("foreign", false), before()));
        assertThrows(IllegalArgumentException.class, () -> NativeUiParsedReturn.encode(request("query-army-strengths-v1"), result(ID, true), before()));
        var wrongRole = actual.with("validation_state", new OpportunityJson.Text("validated"));
        assertThrows(IllegalArgumentException.class, () -> NativeUiParsedReturn.decode(PublicDataJson.encodeFullMaterial(wrongRole).bytes()));
        var falseWireClaim = actual.with("wire_bytes_preserved", new OpportunityJson.Bool(true));
        assertThrows(IllegalArgumentException.class, () -> NativeUiParsedReturn.decode(PublicDataJson.encodeFullMaterial(falseWireClaim).bytes()));
        var extra = actual.with("synthetic_after", before());
        assertThrows(IllegalArgumentException.class, () -> NativeUiParsedReturn.decode(PublicDataJson.encodeFullMaterial(extra).bytes()));
    }

    @Test void oneWholeArtifactCapacityAppliesToReferenceAndParserWithoutTruncation() {
        assertEquals(RawJson.MAXIMUM_BYTES, NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES);
        assertEquals(64 * 1024 * 1024, NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES);
        ExactRef maximum = new ExactRef("software-data:capacity-boundary", NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES, "a".repeat(64));
        assertEquals(maximum.bytes(), NativeUiParsedReturn.reference(maximum).get("bytes").longValue());
        assertThrows(IllegalArgumentException.class, () -> NativeUiParsedReturn.reference(new ExactRef("software-data:over", maximum.bytes() + 1, maximum.sha256())));
        assertThrows(IllegalArgumentException.class, () -> NativeUiParsedReturn.reference(new ExactRef("software-data:empty", 0, maximum.sha256())));
        byte[] oversized = new byte[NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES + 1];
        assertThrows(IllegalArgumentException.class, () -> NativeUiParsedReturn.decode(oversized));
        for (String invalid : new String[] {"{}[]", "{\"x\":1,\"x\":2}", "{\"x\":NaN}"})
            assertThrows(IllegalArgumentException.class, () -> NativeUiParsedReturn.decode(invalid.getBytes(StandardCharsets.UTF_8)));
    }
}
