import SwiftUI

struct GoalDetailView: View {
    var goal: GoalModel
    let weeks: [DSWeeklyScore] = (0..<6).map { idx in
        DSWeeklyScore(weekStart: Calendar.current.date(byAdding: .day, value: -idx * 7, to: .now) ?? .now, score: [2, 2, 1, 2, 0, 1][idx])
    }.reversed()

    var body: some View {
        ScrollView {
            DSConstrainedContent {
                VStack(alignment: .leading, spacing: DSSpacing.l) {
                    Text(goal.title).font(.dsTitle)
                    DSCard(title: "Progress") { DSProgressDots(weeks: weeks) }
                    DSCard(title: "Recent insights") {
                        VStack(alignment: .leading, spacing: DSSpacing.s) {
                            Text("You stayed below your weekly discretionary budget.")
                            Text("Weekend spending dropped by 12%.")
                        }
                        .font(.dsBody)
                    }
                }
                .padding(DSSpacing.l)
            }
        }
        .background(DS.Color.background)
    }
}
