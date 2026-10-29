package org.xar.ck3.control.g2.common;

/** One pure Java adapter per milestone. Domain-owned typed codecs and existing applications retain business authority. */
public interface G2Domain {
    Milestone milestone();
    G2Response evaluate(G2Request request);
}
