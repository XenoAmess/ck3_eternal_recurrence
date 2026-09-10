package com.xenoamess.ck3coa;

import java.util.Map;

public interface CoatOfArmsMcpClient {
    Object callTool(String toolName, Map<String, Object> arguments);
}
