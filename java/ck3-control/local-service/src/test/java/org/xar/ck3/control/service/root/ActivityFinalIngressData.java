package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Arrays;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.M6SourceProducer;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Controlled software wire data, shaped by the actual retained C++ serializer; never a Game result. */
public final class ActivityFinalIngressData {
    public static final long FULL_ID = 0x0800_0102L;
    public static final BigInteger STAMP = new BigInteger("18446744073709551615");
    public static final String SOFTWARE_PROFILE_SHA = M6SourceProducer.EXE.toLowerCase(java.util.Locale.ROOT);
    public static final String SOFTWARE_PROFILE_ADAPTER = "ck3-1.20.0.4-msvc-x64";
    private ActivityFinalIngressData() {}

    public static ActivityNativeContracts.Installation installation(ExactRef controlledSource) {
        return new ActivityNativeContracts.Installation(Arrays.stream(ActivityNativeContracts.Query.values())
                .map(query -> new ActivityNativeContracts.Source(query, controlledSource)).toList(),
                (query, request) -> { /* Only the controlled fixture's source qualification is exercised. */ });
    }

    /** Returns the original native result token, before the transport adds command_result and request_id. */
    public static RawJson result() {
        ObjectNode root = StrictJson.object();
        root.put("step", ActivityNativeContracts.Query.HOSTED.step()).put("accepted", true)
                .put("status", "available").put("private_build", true).put("read_only", true)
                .put("advertised", false).put("backend_id", "native-headless");
        ObjectNode body = root.putObject(ActivityNativeContracts.Query.HOSTED.payloadKey());
        body.put("schema", "activity-feast-hosted-post-private-read-v1").put("snapshot_revision", 1)
                .put("date_raw", ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("actor_character_id", 73).put("read_only", true).put("advertised", false);
        ObjectNode balances = body.putObject("balances");
        for (String name : java.util.List.of("gold", "treasury", "piety", "barter_goods")) {
            balances.putObject(name).put("available", false).putNull("raw");
        }
        body.putArray("hosted_activities").addObject().put("activity_id", FULL_ID)
                .put("host_character_id", 73).put("activity_type_key", "activity_feast")
                .put("terminal_flags_observed", true).put("native_completed", true)
                .put("native_invalidated", false).put("native_completion_stamp_observed", true)
                .put("native_completion_stamp_raw", STAMP);
        body.putNull("native_terminal_observations");
        return new RawJson(StrictJson.canonical(root, 65_536));
    }
}
