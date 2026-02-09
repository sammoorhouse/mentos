import SwiftUI

struct InsightItem: Identifiable {
    let id = UUID()
    let title: String
    let preview: String
}

struct HomeView: View {
    let weekly: [DSWeeklyScore] = (0..<8).map { offset in
        DSWeeklyScore(weekStart: Calendar.current.date(byAdding: .day, value: -offset * 7, to: .now) ?? .now, score: [2, 1, 2, 0, 1, 2, 2, 1][offset])
    }.reversed()
    let latest = InsightItem(title: "Subscriptions are creeping up", preview: "Three monthly services renewed this week. Consider pausing one to rebalance.")

    var body: some View {
        ScrollView {
            DSConstrainedContent {
                VStack(alignment: .leading, spacing: DSSpacing.l) {
                    DSSectionHeader(title: "This week")
                    DSCard {
                        DSProgressDots(weeks: weekly)
                        Text(statusText)
                            .font(.dsBody)
                            .foregroundStyle(DS.Color.textSecondary)
                    }

                    DSCard(title: "Latest Insight") {
                        VStack(alignment: .leading, spacing: DSSpacing.s) {
                            Text(latest.title).font(.dsHeadline)
                            Text(latest.preview).font(.dsBody).foregroundStyle(DS.Color.textSecondary).lineLimit(2)
                        }
                    }

                    DSCard(title: "Connection") {
                        VStack(alignment: .leading, spacing: DSSpacing.s) {
                            Label("Monzo connected", systemImage: "checkmark.circle")
                            Text("Last sync: 2h ago")
                                .font(.dsCaption)
                                .foregroundStyle(DS.Color.textSecondary)
                            Text("Next run: tomorrow 08:00")
                                .font(.dsCaption)
                                .foregroundStyle(DS.Color.textSecondary)
                        }
                        .font(.dsBody)
                    }
                }
                .padding(DSSpacing.l)
            }
        }
        .background(DS.Color.background)
        .navigationTitle("Home")
    }

    private var statusText: String {
        let avg = weekly.suffix(3).map(\.score).reduce(0, +)
        if avg >= 5 { return "On track" }
        if avg >= 3 { return "Steady progress" }
        return "Quiet week"
    }
}
