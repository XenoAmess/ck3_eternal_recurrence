"""Executable authorization model; never starts CK3 or mutates a checkout.

This is an independent oracle for proposal lifecycle tests. Native mechanics are
represented by an injected validator, and are fail-closed by default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from school_consent_data import POLICY


class Rejected(ValueError):
    pass


class Kind(Enum):
    JOIN = "join"
    DETACH = "detach"


@dataclass
class Member:
    identifier: str
    rite: str
    learning: int = 15
    alive: bool = True
    adult: bool = True
    imprisoned: bool = False
    player: bool = False
    landed: bool = True
    incapable: bool = False

    def elector(self) -> bool:
        return self.alive and self.adult and not self.imprisoned and not self.incapable and self.learning >= POLICY.min_learning


@dataclass
class School:
    identifier: str
    faith: str
    core: tuple[str, str, str]
    head_rule: str = "none"
    transition_until: int = 0
    retry_until: int = 0
    proposal_owner: str | None = None
    serial: int = 0
    county_count: int = 0
    holder: str | None = None
    retired_teacher: str | None = None
    teacher: str | None = None


@dataclass
class Faith:
    identifier: str
    main: str
    religion: str = "confucianism_religion"
    head: str | None = None
    core_doctrines: tuple[str, ...] = ("doctrine_no_head",)
    head_title: str | None = None
    owned_head_title: bool = False
    head_title_owner: str | None = None


@dataclass
class World:
    schools: dict[str, School]
    faiths: dict[str, Faith]
    members: dict[str, Member]
    gold: dict[str, int]
    piety: dict[str, int]
    day: int = 0
    native_observed: bool = False
    pair_divergence: dict[tuple[str, str], float] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)
    titles: dict[str, str] = field(default_factory=dict)
    retired_titles: set[str] = field(default_factory=set)

    def faith_schools(self, faith: str) -> set[str]:
        return {school.identifier for school in self.schools.values() if school.faith == faith}


@dataclass
class Proposal:
    actor: str
    moving_rite: str
    serial: int
    kind: Kind
    source_faith: str
    receiving_faith: str | None
    deadline: int
    terms_revision: int
    snapshot: tuple
    electorates: dict[str, frozenset[str]]
    affected_players: frozenset[str]
    nominees: dict[str, str]
    dormant_receivers: frozenset[str] = frozenset()
    holder_endorsements: dict[str, str] = field(default_factory=dict)
    ballots: dict[str, dict[str, bool]] = field(default_factory=dict)
    representative_signatures: dict[str, str] = field(default_factory=dict)
    player_consents: set[str] = field(default_factory=set)
    source_head_consent: str | None = None
    receiving_head_consent: str | None = None
    old_faith_permission: str | None = None
    phase: str = "ballot"
    callback_nonce: int = 0


def quorum(yes: int, total: int) -> bool:
    return total > 0 and yes * POLICY.quorum_denominator >= total * POLICY.quorum_numerator


NativeValidator = Callable[[World, Proposal], bool]


class ConsentController:
    def __init__(self, world: World, native_validator: NativeValidator | None = None):
        self.world = world
        self.native_validator = native_validator or (lambda _world, _proposal: False)
        self.proposals: dict[str, Proposal] = {}
        # Mirrors the persistent actor counter, separate from each rite's serial.
        self.callback_nonces: dict[str, int] = {}

    def _source(self, proposal: Proposal) -> Faith:
        return self.world.faiths[proposal.source_faith]

    def _snapshot(self, school: str, receiving: str | None) -> tuple:
        moving = self.world.schools[school]
        source = self.world.faiths[moving.faith]
        target = self.world.faiths[receiving] if receiving else None
        consulted = {school}
        if target:
            consulted |= self.world.faith_schools(target.identifier)
        return (
            moving.faith, source.main, source.head, source.core_doctrines, source.religion,
            source.head_title, source.owned_head_title, source.head_title_owner,
            tuple(sorted((title, holder) for title, holder in self.world.titles.items() if holder == source.head)),
            target.identifier if target else None, target.main if target else None,
            target.head if target else None, target.core_doctrines if target else None,
            target.religion if target else None,
            target.head_title if target else None,
            tuple(sorted(self.world.faith_schools(source.identifier))),
            tuple(sorted((identifier, self.world.schools[identifier].faith,
                          self.world.schools[identifier].core,
                          self.world.schools[identifier].head_rule,
                          self.world.schools[identifier].county_count,
                          self.world.schools[identifier].holder) for identifier in consulted)),
            tuple(sorted((identifier, member.rite) for identifier, member in self.world.members.items()
                         if member.alive and member.rite in consulted - {school})),
            tuple(sorted((identifier, member.rite) for identifier, member in self.world.members.items()
                         if member.elector() and member.rite in consulted)),
            tuple(sorted((identifier, member.rite) for identifier, member in self.world.members.items()
                         if member.player and member.alive and member.rite in consulted)),
        )

    def begin(self, actor: str, kind: Kind, receiving: str | None = None, terms_revision: int = 1) -> Proposal:
        world = self.world
        member = world.members[actor]
        if not member.player or not member.alive or not member.adult or member.imprisoned or member.incapable or not member.landed:
            raise Rejected("Only a capable landed adult player may initiate")
        school = world.schools[member.rite]
        source = world.faiths[school.faith]
        if source.religion != "confucianism_religion" or member.learning < POLICY.min_learning:
            raise Rejected("Initiator requires Confucian affiliation and learning")
        previous = self.proposals.get(school.identifier)
        if previous and previous.phase in {"ballot", "consent", "confirmed"}:
            if world.day < previous.deadline:
                raise Rejected("A live proposal already owns this school")
            self.cancel(previous, rejected=False)
        if world.day < school.transition_until or world.day < school.retry_until:
            raise Rejected("School cooldown survives succession and sponsor changes")
        if kind == Kind.JOIN:
            if receiving not in world.faiths or receiving == source.identifier:
                raise Rejected("Join needs another existing faith")
            if world.faiths[receiving].religion != source.religion:
                raise Rejected("Cross-religion migration is outside this proposal")
            if not world.faith_schools(receiving):
                raise Rejected("Receiving communion has no rites")
            # Main-rite replacement while other branches remain requires a separate
            # validated succession step; this candidate never improvises one.
            if source.main == school.identifier and len(world.faith_schools(source.identifier)) != 1:
                raise Rejected("Moving a multi-rite source main requires a separate succession proposal")
        elif receiving is not None or source.main == school.identifier:
            raise Rejected("Detach requires a non-main rite and no receiving faith")
        consulted = {school.identifier}
        if receiving:
            consulted |= world.faith_schools(receiving)
        electorates = {
            identifier: frozenset(identifier2 for identifier2, candidate in world.members.items()
                                 if candidate.rite == identifier and candidate.elector())
            for identifier in consulted
        }
        if not electorates[school.identifier]:
            raise Rejected("Source school needs an actual electorate")
        dormant = frozenset(identifier for identifier in consulted - {school.identifier}
                            if world.schools[identifier].county_count == 0
                            and not any(candidate.alive and candidate.rite == identifier
                                        for candidate in world.members.values()))
        for identifier in consulted:
            locked = world.schools[identifier]
            if locked.proposal_owner is not None:
                raise Rejected("Another round owns a consulted school")
            if identifier == school.identifier and (world.day < locked.transition_until or world.day < locked.retry_until):
                raise Rejected("A consulted school is still in its finite cooldown")
        affected = frozenset(identifier for identifier, candidate in world.members.items()
                             if candidate.player and candidate.alive and candidate.rite in consulted)
        school.serial += 1
        nominees = {school.identifier: actor}
        if receiving:
            receiving_main = world.faiths[receiving].main
            representatives = [identifier for identifier, candidate in world.members.items()
                               if candidate.rite == receiving_main and candidate.elector()]
            if not representatives:
                raise Rejected("Receiving communion needs an actual eligible main-rite representative")
            nominees.update({identifier: representatives[0] for identifier in consulted - {school.identifier}})
        for identifier in consulted:
            world.schools[identifier].proposal_owner = actor
        self.callback_nonces[actor] = self.callback_nonces.get(actor, 0) + 1
        proposal = Proposal(actor, school.identifier, school.serial, kind, source.identifier,
                            receiving, world.day + POLICY.proposal_days, terms_revision,
                            self._snapshot(school.identifier, receiving), electorates, affected, nominees,
                            dormant_receivers=dormant, callback_nonce=self.callback_nonces[actor])
        proposal.ballots = {identifier: {} for identifier in consulted}
        self.proposals[school.identifier] = proposal
        return proposal

    def _current(self, proposal: Proposal) -> None:
        world = self.world
        school = world.schools[proposal.moving_rite]
        actor = world.members[proposal.actor]
        if self.proposals.get(proposal.moving_rite) is not proposal or school.serial != proposal.serial:
            raise Rejected("Stale proposal generation")
        if proposal.phase not in {"ballot", "consent", "confirmed"} or world.day >= proposal.deadline:
            raise Rejected("Proposal closed or expired")
        if school.proposal_owner != proposal.actor or not actor.alive or not actor.player:
            raise Rejected("Proposal owner is no longer valid")
        if any(self.world.schools[identifier].proposal_owner != proposal.actor
               for identifier in proposal.electorates):
            raise Rejected("A receiving-school lock is no longer owned by this round")
        if not actor.adult or actor.imprisoned or actor.incapable or not actor.landed or actor.rite != school.identifier:
            raise Rejected("Initiator eligibility changed")
        if self._snapshot(proposal.moving_rite, proposal.receiving_faith) != proposal.snapshot:
            raise Rejected("Faith, head, doctrine, electorate or affected-player snapshot changed")

    def vote(self, proposal: Proposal, member: str, yes: bool, terms_revision: int) -> None:
        self._current(proposal)
        if terms_revision != proposal.terms_revision:
            raise Rejected("Vote refers to superseded terms")
        school = self.world.members[member].rite
        if member not in proposal.electorates.get(school, frozenset()):
            raise Rejected("Not in this school's snapshotted electorate")
        if member in proposal.ballots[school]:
            raise Rejected("Duplicate ballot")
        proposal.ballots[school][member] = bool(yes)

    def consent_player(self, proposal: Proposal, member: str, yes: bool) -> None:
        self._current(proposal)
        if member not in proposal.affected_players:
            raise Rejected("Player is outside the affected scope")
        if not yes:
            self.cancel(proposal, rejected=True)
        else:
            proposal.player_consents.add(member)

    def sign_school(self, proposal: Proposal, school: str, representative: str) -> None:
        self._current(proposal)
        if school != proposal.moving_rite:
            self.sign_receiving(proposal, representative)
            return
        electorate = proposal.electorates.get(school, frozenset())
        if representative != proposal.nominees.get(school) or representative not in electorate or proposal.ballots[school].get(representative) is not True:
            raise Rejected("Representative needs eligibility and an affirmative ballot")
        if not quorum(sum(proposal.ballots[school].values()), len(electorate)):
            raise Rejected("School has not reached two-thirds mandate")
        proposal.representative_signatures[school] = representative
        proposal.phase = "consent"

    def _school_mandated(self, proposal: Proposal, school: str) -> bool:
        electorate = proposal.electorates[school]
        if electorate:
            return quorum(sum(proposal.ballots[school].values()), len(electorate))
        holder = self.world.schools[school].holder
        return (school not in proposal.dormant_receivers and holder is not None
                and proposal.holder_endorsements.get(school) == holder
                and holder in self.world.members and self.world.members[holder].alive
                and self.world.members[holder].adult and not self.world.members[holder].incapable
                and self.world.members[holder].rite == school
                and proposal.player_consents == set(proposal.affected_players))

    def endorse_holder(self, proposal: Proposal, school: str, holder: str, yes: bool) -> None:
        self._current(proposal)
        if school == proposal.moving_rite or school not in proposal.electorates or proposal.electorates[school]:
            raise Rejected("Holder fallback is restricted to receiving schools with zero scholars")
        actual_holder = self.world.schools[school].holder
        member = self.world.members.get(holder)
        if school in proposal.dormant_receivers or holder != actual_holder or not member or not member.alive or not member.adult or member.incapable or member.rite != school:
            raise Rejected("A real current holder of this active rite must reply")
        if not yes:
            self.cancel(proposal, rejected=True)
        else:
            proposal.holder_endorsements[school] = holder

    def sign_receiving(self, proposal: Proposal, representative: str) -> None:
        self._current(proposal)
        if not proposal.receiving_faith:
            raise Rejected("Detach has no receiving representative")
        main = self.world.faiths[proposal.receiving_faith].main
        if representative != proposal.nominees.get(main) or proposal.ballots[main].get(representative) is not True:
            raise Rejected("Receiving representative needs the nominated identity and an affirmative ballot")
        if any(not self._school_mandated(proposal, identifier)
               for identifier in proposal.electorates
               if identifier != proposal.moving_rite and identifier not in proposal.dormant_receivers):
            raise Rejected("Each active receiving rite needs its own mandate")
        proposal.representative_signatures[main] = representative
        proposal.phase = "consent"

    def consent_head(self, proposal: Proposal, role: str, character: str, yes: bool) -> None:
        self._current(proposal)
        source = self._source(proposal)
        target = self.world.faiths[proposal.receiving_faith] if proposal.receiving_faith else None
        expected = source.head if role == "source" else target.head if role == "receiving" and target else None
        if not expected or character != expected or not self.world.members[character].alive:
            raise Rejected("Consent must come from the currently valid head")
        if not yes and role != "source":
            self.cancel(proposal, rejected=True)
            return
        if role == "source":
            proposal.source_head_consent = character if yes else None
        else:
            proposal.receiving_head_consent = character

    def consent_old_faith(self, proposal: Proposal, character: str, yes: bool) -> None:
        """Permission labels a detach peaceful; refusal does not veto autonomy."""
        self._current(proposal)
        if proposal.kind != Kind.DETACH or self._source(proposal).head != character:
            raise Rejected("Not the current old-faith head")
        if yes:
            proposal.old_faith_permission = character

    def ready(self, proposal: Proposal) -> None:
        self._current(proposal)
        required_signatures = {proposal.moving_rite}
        if proposal.receiving_faith:
            required_signatures.add(self.world.faiths[proposal.receiving_faith].main)
        if proposal.representative_signatures.keys() != required_signatures:
            raise Rejected("Source and receiving representatives must sign separately")
        for school in proposal.electorates:
            if school not in proposal.dormant_receivers and not self._school_mandated(proposal, school):
                raise Rejected("Mandate no longer meets quorum")
        if proposal.player_consents != set(proposal.affected_players):
            raise Rejected("All affected players need an explicit choice")
        source = self._source(proposal)
        if proposal.kind == Kind.JOIN:
            target = self.world.faiths[proposal.receiving_faith]
            if target.head and proposal.receiving_head_consent != target.head:
                raise Rejected("Receiving head has not consented")
            if source.core_doctrines != target.core_doctrines or (source.head != target.head and not self._can_retire(proposal)):
                raise Rejected("Native same-core-doctrines/same-head rules remain binding")
            divergence = self.world.pair_divergence.get((proposal.moving_rite, target.main))
            if divergence is None or divergence >= 100:
                raise Rejected("Missing or excessive actual cross-faith divergence")
        elif self.world.schools[proposal.moving_rite].head_rule not in {"none", "temporal"}:
            raise Rejected("This candidate supports only no-head or temporal-head detach")
        if not self.world.native_observed or not self.native_validator(self.world, proposal):
            raise Rejected("Native same-core/head rules and primitives are not yet verified")
        cost_gold = POLICY.join_gold if proposal.kind == Kind.JOIN else POLICY.detach_gold
        cost_piety = POLICY.join_piety if proposal.kind == Kind.JOIN else POLICY.detach_piety
        if self.world.gold.get(proposal.actor, 0) < cost_gold or self.world.piety.get(proposal.actor, 0) < cost_piety:
            raise Rejected("Costs are rechecked only at final commit")

    def commit(self, proposal: Proposal, new_faith_id: str | None = None) -> str:
        self.ready(proposal)
        world = self.world
        school = world.schools[proposal.moving_rite]
        source = self._source(proposal)
        if proposal.kind == Kind.JOIN:
            result = proposal.receiving_faith
            target_main = world.faiths[result].main
            if self._can_retire(proposal):
                school.retired_teacher = source.head
                world.retired_titles.add(source.head_title)
                del world.titles[source.head_title]
                source.head_title = None
                source.head = None
            school.faith = result
            if world.faiths[result].main != target_main:
                raise RuntimeError("Receiver main-rite invariant violated")
        else:
            if not new_faith_id or new_faith_id in world.faiths:
                raise Rejected("Native detach must return a fresh dynamic faith identity")
            result = new_faith_id
            world.faiths[result] = Faith(result, school.identifier, source.religion,
                                        core_doctrines=source.core_doctrines)
            school.faith = result
            if school.head_rule == "temporal":
                faith = world.faiths[result]
                faith.head = proposal.actor
                faith.head_title = f"owned-head:{result}"
                faith.owned_head_title = True
                faith.head_title_owner = result
                world.titles[faith.head_title] = proposal.actor
                school.teacher = proposal.actor
        world.gold[proposal.actor] -= POLICY.join_gold if proposal.kind == Kind.JOIN else POLICY.detach_gold
        world.piety[proposal.actor] -= POLICY.join_piety if proposal.kind == Kind.JOIN else POLICY.detach_piety
        school.transition_until = world.day + POLICY.transition_days
        for identifier in proposal.electorates:
            if world.schools[identifier].proposal_owner == proposal.actor:
                world.schools[identifier].proposal_owner = None
        proposal.phase = "committed"
        world.history.append({"rite": school.identifier, "serial": proposal.serial,
                              "kind": proposal.kind.value, "old_faith": proposal.source_faith,
                              "new_faith": result, "day": world.day,
                              "peaceful": proposal.kind == Kind.JOIN or proposal.old_faith_permission is not None,
                              "dormant_excluded": sorted(proposal.dormant_receivers),
                              "holder_endorsements": dict(proposal.holder_endorsements)})
        return result

    def _can_retire(self, proposal: Proposal) -> bool:
        source = self._source(proposal)
        target = self.world.faiths[proposal.receiving_faith] if proposal.receiving_faith else None
        return bool(target and self.world.faith_schools(source.identifier) == {proposal.moving_rite}
                    and source.main == proposal.moving_rite and source.head
                    and source.head in self.world.members and self.world.members[source.head].alive
                    and self.world.members[source.head].rite == proposal.moving_rite
                    and source.head_title and source.owned_head_title and source.head_title_owner == source.identifier
                    and self.world.titles.get(source.head_title) == source.head
                    and source.head_title != target.head_title)

    def cancel(self, proposal: Proposal, rejected: bool) -> None:
        school = self.world.schools[proposal.moving_rite]
        if self.proposals.get(proposal.moving_rite) is proposal:
            for identifier in proposal.electorates:
                if self.world.schools[identifier].proposal_owner == proposal.actor:
                    self.world.schools[identifier].proposal_owner = None
            if rejected:
                school.retry_until = self.world.day + POLICY.retry_days
        proposal.phase = "rejected" if rejected else "expired"
