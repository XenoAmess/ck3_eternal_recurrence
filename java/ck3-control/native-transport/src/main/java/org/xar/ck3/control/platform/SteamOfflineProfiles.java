package org.xar.ck3.control.platform;

import java.util.HexFormat;
import java.util.List;

/** Exact profiles migrated from the existing shared native Steam provider; version alone grants nothing. */
final class SteamOfflineProfiles {
    record Anchor(int rva,String hex) { byte[] bytes(){return HexFormat.of().parseHex(hex);} }
    record Profile(String version,long bytes,String sha256,int imageSize,int valueRva,int managerRva,int trayOffset,List<Anchor> anchors) {
        Profile { anchors=List.copyOf(anchors); }
        Profile(String version,long bytes,String sha256,int imageSize,int valueRva,int managerRva,List<Anchor> anchors) {
            this(version,bytes,sha256,imageSize,valueRva,managerRva,0x154,anchors);
        }
    }
    static final List<Profile> ALL=List.of(
        new Profile("10.96.30.42",18962584,"cb387adefbbac64a3c1490d4275d00daf3a1e0219b4580726ef7681db7429278",19238912,0x1123627,0x1121AA0,List.of(
            new Anchor(0x616D0C,"440fb60513c9b000488d157d3b7400488bcbe81d9e3b00"),
            new Anchor(0x5D39B0,"40534883ec20488bd9e852d8f2ff488bc8488b10ff92880000008883e70100004883c4205bc3"),
            new Anchor(0x6869DF,"488d0d5acaa900e8c5cff4ff"),
            new Anchor(0x6158E4,"803d3cddb000007419488b0dacc1b0004533c0ba04000000e81fc7f6ff"),
            new Anchor(0x582038,"8bfa4c8bf1490f45f03b9154010000"),new Anchor(0x582071,"4189be54010000"))),
        new Profile("11.12.30.7",19449496,"1b9457943205dc3af0bd53463ba331cbd2a381388699705c02271aac7a2b1252",19730432,0x1194EC7,0x11932E0,List.of(
            new Anchor(0x63EA4C,"440fb6057364b500488d150da37700488bcbe83d703d00"),
            new Anchor(0x5F7D00,"40534883ec20488bd9e8c280f2ff488bc8488b10ff92880000008883870100004883c4205bc3"),
            new Anchor(0x6B2FFF,"488d0d3a1dae00e8f54cf4ff"),
            new Anchor(0x63D524,"803d9c79b500007419488b0dac5db5004533c0ba04000000e87f53f6ff"),
            new Anchor(0x5A28DE,"8bfa4c8bf13b9154010000"),new Anchor(0x5A290E,"4189be54010000"))),
        new Profile("11.15.70.27",19452568,"cd9226db4e6c28942df70c22c0475d91fdd62cba5f100baae2d65af57cabb610",19730432,0x1194EC7,0x11932E0,List.of(
            new Anchor(6548332,"440fb6055363b500488d155da67700488bcbe80d713d00"),
            new Anchor(6258192,"40534883ec20488bd9e8b280f2ff488bc8488b10ff92880000008883870100004883c4205bc3"),
            new Anchor(7024927,"488d0d1a1cae00e8e54cf4ff"),
            new Anchor(6542916,"803d7c78b500007419488b0d8c5cb5004533c0ba04000000e86f53f6ff"),
            new Anchor(5908974,"8bfa4c8bf13b9154010000"),new Anchor(5909022,"4189be54010000"))),
        new Profile("11.23.65.88",19675800,"2dfb0a5d50dd90667549cc7d413c7bfb0794c9af4ebaf08bf1cf7d938a11ea93",19959808,0x11ca0d7,0x11c8328,0x160,List.of(
            new Anchor(0x661b0c,"440fb605c385b600488d15c5297800488bcbe8dd0a3e00"),
            new Anchor(0x619840,"40534883ec20488bd9e862ebf1ff488bc8488b10ff92880000008883870100004883c4205bc3"),
            new Anchor(0x6d8daf,"488d0d9a11af00e8850af4ff"),
            new Anchor(0x660484,"803d4c9cb600007419488b0d947eb6004533c0ba04000000e83f0bf6ff"),
            new Anchor(0x5c0ffe,"8bfa4c8bf13b9160010000"),
            new Anchor(0x5c102e,"4189be60010000")))
    );
    private SteamOfflineProfiles(){ }
    static Profile select(String version,long bytes,String sha) {
        return ALL.stream().filter(p->p.version().equals(version)&&p.bytes()==bytes&&p.sha256().equals(sha)).findFirst()
            .orElseThrow(()->new IllegalArgumentException("Steam incarnation version and exact UI image are not one qualified profile"));
    }
}
