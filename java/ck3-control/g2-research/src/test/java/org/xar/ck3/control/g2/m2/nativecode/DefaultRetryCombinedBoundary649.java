package org.xar.ck3.control.g2.m2.nativecode;

/** Mechanical aggregate of the four new owner649 witness families. */
public final class DefaultRetryCombinedBoundary649 {
    private DefaultRetryCombinedBoundary649() { }

    public static int verify() {
        int retry = DefaultRetryBoundary649.verify();
        int genericGuard = Retry60GenericGuardBoundary649.verify();
        int failure = DefaultRetryFailureBoundary649.verify();
        int tail = DefaultAllocateKnownRetryTailBoundary649.verify();
        if (retry != 3 || genericGuard != 2 || failure != 2 || tail != 1) {
            throw new AssertionError("Unexpected new649 family group count");
        }
        return retry + genericGuard + failure + tail;
    }

    public static void main(String[] args) { System.out.println(verify()); }
}
