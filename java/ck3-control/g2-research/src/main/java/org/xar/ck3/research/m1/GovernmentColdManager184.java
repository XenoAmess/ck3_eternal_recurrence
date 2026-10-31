package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentSharedManager167;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;

/** Same-memory owned normal composition; no native OS, TLS or Game qualification. */
public final class GovernmentColdManager184 {
    private GovernmentColdManager184() { }
    public static GovernmentCallee164Api.NormalReturn execute(GovernmentCallee164Api.Entry entry,
            GovernmentSharedManager167Api.Memory memory, Calls delegate,
            GovernmentThreadHeader178Api.Ports ports, GovernmentThreadHeader178Api.WaitBudget budget) {
        Objects.requireNonNull(entry); Objects.requireNonNull(memory); Objects.requireNonNull(delegate);
        Objects.requireNonNull(ports); Objects.requireNonNull(budget);
        long base=entry.imageBaseBits();
        GovernmentThreadHeader178Api.Ports waitPorts=GovernmentThreadWait179Calls.bind(base,memory,ports);
        Calls registry=GovernmentRegistry182Calls.bind(base,memory,delegate);
        Calls footerBase=GovernmentThreadFooter181Calls.bind(base,memory,registry,waitPorts);
        Calls getterFooter=new Calls() {
            @Override public long readGsQword58(){return footerBase.readGsQword58();}
            @Override public VolatileBits invoke(OpaqueCall call) {
                if(call.callSiteRva()!=0x2D888C6L||call.targetRva()!=0x4223A24L)
                    return footerBase.invoke(call);
                GovernmentCallee164Api.Entry child=new GovernmentCallee164Api.Entry(
                        base,call.rspBits()-8,call.volatileBits(),call.nonvolatileBits());
                GovernmentCallee164Api.NormalReturn result=GovernmentThreadFooter181.execute(child,memory,waitPorts);
                if(result.returnRipBits()!=base+0x2D888CBL||result.callerRspBits()!=call.rspBits()
                        ||!result.nonvolatileBits().equals(call.nonvolatileBits()))
                    throw new UnsupportedOperationException("unsupported record Footer normal return");
                return result.volatileBits();
            }
        };
        Calls record=GovernmentSharedRecord180Calls.bind(base,memory,getterFooter,waitPorts,budget);
        Calls header=GovernmentThreadHeader178Calls.bind(base,memory,record,waitPorts,budget);
        return GovernmentSharedManager167.execute(entry,memory,header);
    }
}
