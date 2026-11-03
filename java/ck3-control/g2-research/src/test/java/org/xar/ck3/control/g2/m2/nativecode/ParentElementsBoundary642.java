package org.xar.ck3.control.g2.m2.nativecode;

/** Owner aggregation of six new wholeparent groups; no old verify entry is called. */
public final class ParentElementsBoundary642 {
    private ParentElementsBoundary642() { }
    public static int verify() {
        return ParentRamBoundary642.verify2()+ParentFpPrefixBoundary642.verify()+ParentProtocolBoundary642.verify();
    }
    public static void main(String[] args) {System.out.println(verify());}
}
