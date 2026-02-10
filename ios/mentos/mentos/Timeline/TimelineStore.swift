import Foundation

@MainActor
final class TimelineStore: ObservableObject {
    @Published private(set) var events: [TimelineEvent] = []
    @Published var isLoading = false
    @Published var selectedInsight: InsightPayload?

    private var lastLoadedAt: Date?

    func load() async {
        guard !isLoading else { return }
        isLoading = true
        defer { isLoading = false }

        // Placeholder for future API integration (/me, /monzo/status, /insights, /goals, /breakthroughs).
        let merged = demoTimeline()
        events = merged.sorted { lhs, rhs in
            if lhs.date == rhs.date { return lhs.priority > rhs.priority }
            return lhs.date > rhs.date
        }
        lastLoadedAt = .now
    }

    func refresh() async {
        await load()
    }

    func saveGoals(_ goals: [GoalItem]) async {
        let updateEvent = TimelineEvent(
            id: "goal-update-\(UUID().uuidString)",
            date: .now,
            type: .goalUpdate,
            payload: .goalUpdate(GoalPayload(title: "Goals updated", subtitle: "Pick what matters right now.", goals: goals)),
            priority: 90
        )
        events.insert(updateEvent, at: 0)
        events.sort { lhs, rhs in
            if lhs.date == rhs.date { return lhs.priority > rhs.priority }
            return lhs.date > rhs.date
        }
    }

    private func demoTimeline() -> [TimelineEvent] {
        let calendar = Calendar.current
        let now = Date()
        let day = { (offset: Int) in calendar.date(byAdding: .day, value: -offset, to: now) ?? now }

        let status = TimelineEvent(
            id: "status",
            date: now,
            type: .status,
            payload: .status(StatusPayload(isConnected: true, providerName: "Monzo", lastSyncText: "2h ago")),
            priority: 100
        )

        let weekly = TimelineEvent(
            id: "weekly",
            date: now.addingTimeInterval(-5),
            type: .weeklyProgress,
            payload: .weeklyProgress(WeeklyProgressPayload(dayLabels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], progress: [0.95, 0.7, 0.65, 0.8, 0.88, 0.92, 0.6], summary: "You're on track this week")),
            priority: 99
        )

        let goals: [GoalItem] = [
            .init(id: "save", title: "Save more money", icon: "sterlingsign.circle", progressText: "8 / 12", progress: 0.66),
            .init(id: "home", title: "Cook at home", icon: "fork.knife", progressText: "4 / 6", progress: 0.75)
        ]

        let feed: [TimelineEvent] = [
            .init(id: "bt-1", date: day(1), type: .breakthrough, payload: .breakthrough(BreakthroughPayload(title: "Breakthrough", metric: "£50 saved this week", detail: "You've saved £50 more than last week.", ctaTitle: "Realign goals")), priority: 95),
            .init(id: "goal-1", date: day(2), type: .goalUpdate, payload: .goalUpdate(GoalPayload(title: "Goal reached", subtitle: "You cooked at home 4 times", goals: goals)), priority: 70),
            .init(id: "insight-1", date: day(3), type: .insight, payload: .insight(InsightPayload(title: "Spending was lower at the weekend", body: "No takeaways in the last two days.", detail: "Weekend dining spend dropped 28% week-over-week.")), priority: 60)
        ]

        return [status, weekly] + (feed.isEmpty ? [emptyStateEvent()] : feed)
    }

    private func emptyStateEvent() -> TimelineEvent {
        TimelineEvent(
            id: "empty",
            date: .now,
            type: .emptyState,
            payload: .emptyState(EmptyStatePayload(title: "No insights yet", message: "Check back tomorrow after your nightly run.")),
            priority: 0
        )
    }
}
