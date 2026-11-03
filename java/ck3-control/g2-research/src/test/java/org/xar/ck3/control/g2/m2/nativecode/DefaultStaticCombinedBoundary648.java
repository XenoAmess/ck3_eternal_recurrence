package org.xar.ck3.control.g2.m2.nativecode;

/** Mechanical aggregation of only the three new owner648 witnesses; no new scenario. */
public final class DefaultStaticCombinedBoundary648 {
    private DefaultStaticCombinedBoundary648() { }
    public static int verify() {
        int allocate=DefaultAllocateBoundary648.verify();
        if(allocate!=4)throw new AssertionError("D0 group count");
        int release=DefaultReleaseBoundary648.verify();
        if(release!=4)throw new AssertionError("C0 group count");
        int whole=Range16DefaultWholeBoundary648.verify();
        if(whole!=2)throw new AssertionError("whole638 group count");
        return allocate+release+whole;
    }
    public static void main(String[] args) {System.out.println(verify());}
}
