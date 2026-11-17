package org.xar.ck3.control.nativebridge;

import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Exact request DATA only. An original requested ACK does not establish a natural process exit. */
public final class CoreApplicationExit {
    public static final String STEP="normal-exit-application-v1";
    public static final String CAPABILITY="game.command."+STEP;
    public static final String SCHEMA="ck3_1210_application_exit_v1";
    private CoreApplicationExit() { }

    public static NativeRequest request(CoreFrame.Partial frame) {
        var claim=CoreClockControl.claim(frame).put("schema",SCHEMA);
        var fields=StrictJson.object();fields.set("core_application_exit",claim);
        return new NativeRequest(STEP,CAPABILITY,new RawJson(StrictJson.canonical(fields)));
    }
}
