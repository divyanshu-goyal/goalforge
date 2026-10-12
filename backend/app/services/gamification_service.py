from datetime import date, datetime, timezone

from app.db.repositories import GamificationRepository, GamificationState
from app.schemas.gamification import Achievement, GamificationProfile, Rank

BASE_XP = {
    "learning": 50,
    "practice": 50,
    "challenge": 250,
    "recovery": 100,
    "emergency": 200,
}
STREAK_BUFFS = {
    7: (110, "7-day streak bonus"),
    30: (120, "30-day streak bonus"),
}
RANK_REQUIREMENTS = {"E": 0, "D": 50, "C": 60, "B": 70, "A": 80, "S": 90}
BOSS_XP = 500
ACHIEVEMENT_DEFINITIONS = (
    ("first_quest", "First Quest", "Complete your first quest.", False),
    ("first_boss", "First Boss", "Complete your first Boss Battle.", False),
    ("thirty_day_streak", "30-Day Streak", "Maintain a 30-day active streak.", False),
    ("one_thousand_xp", "1000 XP", "Earn 1,000 total XP.", False),
    ("first_project", "First Project", "Complete your first project.", False),
    ("iron_will", "Iron Will", "A future hidden achievement.", True),
    ("path_walker", "Path Walker", "A future hidden achievement.", True),
    ("speed_hunter", "Speed Hunter", "A future hidden achievement.", True),
)


class GamificationError(ValueError):
    """Raised when a gamification event is invalid."""


class GamificationService:
    LEGACY_LEARNER_ID = "legacy"

    def __init__(self, repository: GamificationRepository | None = None) -> None:
        self.repository = repository or GamificationRepository()

    def _new_profile(self) -> GamificationProfile:
        return GamificationProfile(
            rank_requirements=RANK_REQUIREMENTS.copy(),
            achievements=[
                Achievement(
                    achievement_id=achievement_id,
                    name=name,
                    description=description,
                    hidden=hidden,
                    unlocked=False,
                )
                for achievement_id, name, description, hidden in ACHIEVEMENT_DEFINITIONS
            ],
        )

    def _load(self, learner_id: str | None) -> GamificationState:
        return self.repository.load(learner_id or self.LEGACY_LEARNER_ID, self._new_profile)

    def get_profile(self, learner_id: str | None = None) -> GamificationProfile:
        return self._load(learner_id).profile

    def get_achievements(self, learner_id: str | None = None) -> list[Achievement]:
        return self._load(learner_id).profile.achievements

    def get_mastery(self, learner_id: str | None = None) -> dict[str, float]:
        return self._load(learner_id).profile.mastery_by_skill.copy()

    def record_boss_completion(
        self,
        *,
        attempt_id: str,
        goal_id: str,
        skill_id: str,
        score: float,
        mastery_before: float,
        required_skill_mastery: dict[str, float],
        final_skill_id: str,
        goal_final_boss_passed: bool,
        learner_id: str | None = None,
    ) -> GamificationProfile:
        learner_key = learner_id or self.LEGACY_LEARNER_ID
        state = self._load(learner_key)
        profile = state.profile
        if attempt_id in state.processed_event_ids:
            return profile
        state.processed_event_ids.add(attempt_id)
        for required_skill_id, required_mastery in required_skill_mastery.items():
            profile.mastery_by_skill[required_skill_id] = max(
                profile.mastery_by_skill.get(required_skill_id, 0),
                required_mastery,
            )
        profile.mastery_by_skill[skill_id] = max(mastery_before, score)
        if skill_id not in profile.passed_boss_skills:
            profile.passed_boss_skills.append(skill_id)
        profile.total_xp += BOSS_XP
        profile.current_xp = profile.total_xp
        profile.last_boss_xp_awarded = BOSS_XP
        profile.last_boss_reason = f"{BOSS_XP} XP: Boss Battle for {skill_id} passed."
        self._update_level(profile)
        self._update_achievements(profile, boss_passed=True)
        self._update_rank_eligibility(profile, profile.mastery_by_skill)
        self._promote_one_rank(profile)
        if goal_final_boss_passed and goal_id not in profile.completed_goals:
            profile.completed_goals.append(goal_id)
        self.repository.save(learner_key, state)
        return profile

    def record_boss_failure(self, learner_id: str | None = None) -> None:
        learner_key = learner_id or self.LEGACY_LEARNER_ID
        state = self._load(learner_key)
        state.profile.last_boss_xp_awarded = 0
        state.profile.last_boss_reason = "Boss Battle failed. No XP awarded and mastery was unchanged."
        self.repository.save(learner_key, state)

    def record_quest_completion(
        self,
        *,
        quest_id: str,
        quest_type: str,
        completion_date: date,
        goal_id: str,
        mastery_by_skill: dict[str, float] | None = None,
        learner_id: str | None = None,
    ) -> GamificationProfile:
        learner_key = learner_id or self.LEGACY_LEARNER_ID
        state = self._load(learner_key)
        profile = state.profile
        if quest_id in state.processed_event_ids:
            return profile
        if quest_type not in BASE_XP:
            raise GamificationError(f"Unsupported quest type for XP: {quest_type}")

        state.processed_event_ids.add(quest_id)
        self._update_streak(profile, completion_date, state.shield_milestones_awarded)
        multiplier, buff = self._active_buff(profile)
        base_xp = BASE_XP[quest_type]
        awarded_xp = base_xp * multiplier // 100
        profile.total_xp += awarded_xp
        profile.current_xp = profile.total_xp
        profile.active_xp_multiplier = multiplier
        profile.active_buff = buff
        profile.last_xp_awarded = awarded_xp
        profile.last_xp_reason = f"{awarded_xp} XP: {quest_type.title()} quest completed. {buff}."
        profile.last_completed_quest_id = quest_id
        self._update_level(profile)
        self._update_achievements(profile)
        self._update_rank_eligibility(profile, mastery_by_skill or {})
        self.repository.save(learner_key, state)
        return profile

    def _update_streak(self, profile: GamificationProfile, completion_date: date, shields: set[int]) -> None:
        last_active = profile.last_active_date
        if last_active is None:
            profile.current_streak = 1
            profile.consecutive_missed_days = 0
        elif completion_date == last_active:
            return
        else:
            gap = (completion_date - last_active).days
            missed_days = max(gap - 1, 0)
            if missed_days == 0:
                profile.current_streak += 1
                profile.consecutive_missed_days = 0
            elif missed_days == 1 and profile.streak_shields:
                profile.streak_shields = 0
                profile.current_streak += 1
                profile.consecutive_missed_days = 0
            else:
                profile.current_streak = 1
                profile.consecutive_missed_days = missed_days
                profile.recovery_required = missed_days >= 2
                profile.roadmap_review_required = missed_days >= 5
                shields.clear()

        profile.last_active_date = completion_date
        profile.longest_streak = max(profile.longest_streak, profile.current_streak)
        self._award_streak_shield(profile, shields)

    def _award_streak_shield(self, profile: GamificationProfile, shields: set[int]) -> None:
        milestone = profile.current_streak // 14
        for milestone_number in range(1, milestone + 1):
            if milestone_number in shields:
                continue
            shields.add(milestone_number)
            if profile.streak_shields == 0:
                profile.streak_shields = 1

    def _active_buff(self, profile: GamificationProfile) -> tuple[int, str]:
        if profile.current_streak >= 30:
            return STREAK_BUFFS[30]
        if profile.current_streak >= 7:
            return STREAK_BUFFS[7]
        return 100, "No streak buff"

    def _update_level(self, profile: GamificationProfile) -> None:
        level = 1
        while profile.total_xp >= 50 * (level + 1) ** 2:
            level += 1
        profile.level = level
        profile.current_xp = profile.total_xp
        profile.next_level = level + 1
        profile.xp_for_next_level = 50 * (level + 1) ** 2
        current_threshold = 0 if level == 1 else 50 * level**2
        profile.xp_progress = profile.total_xp - current_threshold

    def _update_achievements(self, profile: GamificationProfile, boss_passed: bool = False) -> None:
        now = datetime.now(timezone.utc)
        unlocked = {achievement.achievement_id for achievement in profile.achievements if achievement.unlocked}
        should_unlock = set()
        if profile.last_completed_quest_id:
            should_unlock.add("first_quest")
        if profile.current_streak >= 30:
            should_unlock.add("thirty_day_streak")
        if profile.total_xp >= 1000:
            should_unlock.add("one_thousand_xp")
        if boss_passed:
            should_unlock.add("first_boss")
        for achievement in profile.achievements:
            if achievement.achievement_id in should_unlock and achievement.achievement_id not in unlocked:
                achievement.unlocked = True
                achievement.unlocked_at = now

    def _promote_one_rank(self, profile: GamificationProfile) -> None:
        ranks = list(RANK_REQUIREMENTS)
        current_index = ranks.index(profile.current_rank)
        eligible_index = ranks.index(profile.eligible_rank)
        if eligible_index > current_index:
            profile.current_rank = ranks[current_index + 1]  # type: ignore[assignment]

    def _update_rank_eligibility(self, profile: GamificationProfile, mastery_by_skill: dict[str, float]) -> None:
        if mastery_by_skill:
            average_mastery = sum(mastery_by_skill.values()) / len(mastery_by_skill)
            eligible: Rank = "E"
            for rank, threshold in RANK_REQUIREMENTS.items():
                if average_mastery >= threshold:
                    eligible = rank  # type: ignore[assignment]
            profile.eligible_rank = eligible


gamification_service = GamificationService()
