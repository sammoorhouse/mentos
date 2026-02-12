import Foundation

@MainActor
final class TimelineStore: ObservableObject {
    @Published private(set) var events: [TimelineEvent] = []
    @Published var isLoading = false
    @Published var selectedInsight: InsightPayload?
    @Published var statusText: String = "Checking status…"

    private var lastLoadedAt: Date?
    private var nextCursor: String?

    func load() async {
        guard !isLoading else { return }
        isLoading = true
        defer { isLoading = false }

        do {
            let page = try await APIClient.shared.getTimeline(cursor: nil, limit: 50)
            nextCursor = page.nextCursor

            let mapped = page.events.compactMap(mapEvent)
            var merged = mapped

            let status = try? await APIClient.shared.getMonzoStatus()
            if let statusPayload = statusPayload(from: status) {
                statusText = statusPayload.isConnected
                    ? "\(statusPayload.providerName) connected • Last sync \(statusPayload.lastSyncText)"
                    : "Connection needed"
                merged.insert(
                    TimelineEvent(
                        id: "status",
                        date: .now,
                        type: .status,
                        payload: .status(statusPayload),
                        priority: 100
                    ),
                    at: 0
                )
            } else {
                statusText = "Status unavailable"
            }

            events = (merged.isEmpty ? [emptyStateEvent()] : merged).sorted { lhs, rhs in
                if lhs.date == rhs.date { return lhs.priority > rhs.priority }
                return lhs.date > rhs.date
            }
            lastLoadedAt = .now
        } catch {
            statusText = "Status unavailable"
            events = [emptyStateEvent()]
        }
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

    private func emptyStateEvent() -> TimelineEvent {
        TimelineEvent(
            id: "empty",
            date: .now,
            type: .emptyState,
            payload: .emptyState(EmptyStatePayload(title: "No insights yet", message: "Check back tomorrow after your nightly run.")),
            priority: 0
        )
    }

    private func mapEvent(_ event: TimelineEventDTO) -> TimelineEvent? {
        switch event.type {
        case "weekly_progress":
            return mapWeekly(event)
        case "breakthrough":
            return mapBreakthrough(event)
        case "insight", "monthly_framing", "quarterly_review", "year_review", "streak_update", "streak_broken":
            return mapInsight(event)
        case "goal_update":
            if let goals = mapGoals(event) {
                return TimelineEvent(
                    id: event.id,
                    date: event.occurredAt,
                    type: .goalUpdate,
                    payload: .goalUpdate(GoalPayload(title: event.title, subtitle: event.body, goals: goals)),
                    priority: event.priority
                )
            }
            return mapInsight(event)
        case "status":
            return mapInsight(event)
        default:
            return mapInsight(event)
        }
    }

    private func mapWeekly(_ event: TimelineEventDTO) -> TimelineEvent? {
        let days = event.meta["days"]?.intArrayValue ?? []
        let padded = days + Array(repeating: 0, count: max(0, 7 - days.count))
        let progress = padded.prefix(7).map { score -> Double in
            switch score {
            case 2: return 1.0
            case 1: return 0.55
            default: return 0.0
            }
        }
        let labels = dayLabels(starting: event.occurredAt)
        return TimelineEvent(
            id: event.id,
            date: event.occurredAt,
            type: .weeklyProgress,
            payload: .weeklyProgress(WeeklyProgressPayload(dayLabels: labels, progress: progress, summary: event.body)),
            priority: event.priority
        )
    }

    private func mapBreakthrough(_ event: TimelineEventDTO) -> TimelineEvent {
        let streakLength = event.meta["streak_length"]?.intValue
        let metric = streakLength.map { "\($0)-day streak" } ?? event.title
        let cta = event.actions.first(where: { $0.kind == "primary" })?.label ?? "Realign goals"
        return TimelineEvent(
            id: event.id,
            date: event.occurredAt,
            type: .breakthrough,
            payload: .breakthrough(BreakthroughPayload(title: event.title, metric: metric, detail: event.body, ctaTitle: cta)),
            priority: event.priority
        )
    }

    private func mapInsight(_ event: TimelineEventDTO) -> TimelineEvent {
        let detail = event.meta["detail"]?.stringValue ?? event.body
        return TimelineEvent(
            id: event.id,
            date: event.occurredAt,
            type: .insight,
            payload: .insight(InsightPayload(title: event.title, body: event.body, detail: detail)),
            priority: event.priority
        )
    }

    private func mapGoals(_ event: TimelineEventDTO) -> [GoalItem]? {
        guard let goals = event.meta["goals"]?.arrayValue else { return nil }
        let mapped = goals.compactMap { item -> GoalItem? in
            guard case let .object(obj) = item else { return nil }
            guard let id = obj["id"]?.stringValue ?? obj["key"]?.stringValue,
                  let title = obj["title"]?.stringValue ?? obj["name"]?.stringValue else {
                return nil
            }
            let icon = obj["icon"]?.stringValue ?? "target"
            let progressText = obj["progress_text"]?.stringValue ?? obj["progressText"]?.stringValue ?? ""
            let progress = obj["progress"]?.doubleValue ?? 0
            return GoalItem(id: id, title: title, icon: icon, progressText: progressText, progress: progress)
        }
        return mapped.isEmpty ? nil : mapped
    }

    private func dayLabels(starting weekStart: Date) -> [String] {
        let calendar = Calendar.current
        return (0..<7).map { offset in
            let date = calendar.date(byAdding: .day, value: offset, to: weekStart) ?? weekStart
            return date.formatted(.dateTime.weekday(.short))
        }
    }

    private func statusPayload(from status: MonzoStatus?) -> StatusPayload? {
        guard let status else { return nil }
        let lastSyncText = relativeText(for: status.lastSyncAt)
        return StatusPayload(isConnected: status.connected, providerName: "Monzo", lastSyncText: lastSyncText)
    }

    private func relativeText(for date: Date?) -> String {
        guard let date else { return "not synced" }
        let seconds = Int(Date().timeIntervalSince(date))
        if seconds < 60 { return "just now" }
        let minutes = seconds / 60
        if minutes < 60 { return "\(minutes)m ago" }
        let hours = minutes / 60
        if hours < 24 { return "\(hours)h ago" }
        let days = hours / 24
        return "\(days)d ago"
    }
}
