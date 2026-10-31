package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Consumer adapting RequestDecode424d02c.Ports to RequestIndexedTails4247ffc.Ports. */
public final class RequestDecodeTailConsumer {
    private RequestDecodeTailConsumer() { }

    public static RequestDecode424d02c.Ports ports(long moduleBase, RequestIndexedTails4247ffc.Ports tails) {
        return new RequestDecode424d02c.Ports() {
            @Override
            public void call4247ffc(long knownRcx) {
                RequestIndexedTails4247ffc.call4247ffc(moduleBase, (int) knownRcx, tails);
            }

            @Override
            public void call4248050(long knownRcx, long liveRbx) {
                RequestIndexedTails4247ffc.call4248050(moduleBase, (int) knownRcx, liveRbx, tails);
            }
        };
    }
}
