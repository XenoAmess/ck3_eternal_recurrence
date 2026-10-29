package org.xar.ck3.control.service.mcp;

import java.util.Objects;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** One original MCP descriptor consumes its exact same typed service route and public codec. */
public final class PublicMcpNativeAdapter {
    private PublicMcpNativeAdapter() { }
    public static <Q,R> void register(PublicMcpBindings directory, ToolDescriptor original, PublicBindings.TypedBinding<Q,R> actualBinding) {
        Objects.requireNonNull(actualBinding);
        McpJson.require(expectedServiceMethod(original.name()) == actualBinding.route().method(), "original MCP name is bound to a different public service method");
        directory.registerWithCall(original, actualBinding.route(), actualBinding.resultType(),
                call -> actualBinding.decode(arguments(call.arguments())), (call, result) -> {
                    var encoded = actualBinding.encode(result);
                    return switch (actualBinding.route().method()) {
                        case AUTO_TURN -> OriginalMcpPresenters.present(OriginalMcpPresenters.Entry.AUTO_TURN, call.arguments(), encoded);
                        case EXECUTE_STEP -> OriginalMcpPresenters.present(OriginalMcpPresenters.Entry.EXECUTE_STEP, call.arguments(), encoded);
                        case QUERY_ARMY_STRENGTHS -> OriginalMcpPresenters.present(OriginalMcpPresenters.Entry.ARMY_QUERY, call.arguments(), encoded);
                        default -> CallResult.fromBusinessJson(encoded);
                    };
                });
    }
    /** These aliases are actual original service calls; driver/offline routes use explicit registerDirect instead. */
    public static PublicMethod expectedServiceMethod(String publicName) {
        McpJson.toolName(publicName); McpJson.require(publicName.startsWith("ck3_"), "original ck3 tool name required");
        return switch (publicName) {
            case "ck3_get_capabilities" -> PublicMethod.CAPABILITIES;
            case "ck3_get_bridge_diagnostics" -> PublicMethod.BRIDGE_DIAGNOSTICS;
            case "ck3_take_snapshot" -> PublicMethod.SNAPSHOT;
            case "ck3_get_one_life_settlement" -> PublicMethod.ONE_LIFE_SETTLEMENT;
            case "ck3_get_war_state" -> PublicMethod.WAR_STATE;
            case "ck3_query_grant_title_picker_v1", "ck3_prepare_grant_title_picker_v1", "ck3_select_grant_title_picker_v1", "ck3_send_grant_title_picker_v1" -> PublicMethod.GRANT_TITLE_PICKER_V1;
            case "ck3_query_faith_power_ui_v1", "ck3_query_faith_power_tooltip_v1" -> PublicMethod.PRESENT_FAITH_POWER_UI_V1;
            case "ck3_query_player_realm_map_bounds_v1" -> PublicMethod.CENTER_MAP_ON_PLAYER_REALM_V1;
            case "ck3_convert_player_religion_private_v1" -> PublicMethod.SUBMIT_PLAYER_RELIGION_CONVERSION_PRIVATE_V1;
            case "ck3_submit_regular_maa_create" -> PublicMethod.SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1;
            case "ck3_query_player_ordinary_holy_war_declaration_context_v1" -> PublicMethod.QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1;
            case "ck3_submit_county_conversion_task" -> PublicMethod.SUBMIT_COUNTY_CONVERSION_TASK_PRIVATE_V1;
            case "ck3_query_county_conversion_task_result" -> PublicMethod.QUERY_COUNTY_CONVERSION_TASK_RESULT_PRIVATE_V1;
            default -> PublicMethod.exact(publicName.substring(4));
        };
    }
    public static PublicBindings.Arguments arguments(Arguments actual) {
        return switch (actual.presence()) {
            case MISSING -> new PublicBindings.Missing();
            case NULL -> new PublicBindings.Null();
            case VALUE -> new PublicBindings.Value(actual.original().orElseThrow());
        };
    }
}
