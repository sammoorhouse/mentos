import SwiftUI

struct GoalModel: Identifiable {
    let id = UUID()
    let title: String
    let summary: String
}

struct GoalsListView: View {
    let goals = [
        GoalModel(title: "Reduce impulse buys", summary: "2 / 3 weeks on track"),
        GoalModel(title: "Emergency fund", summary: "Saved each week this month")
    ]

    var body: some View {
        ScrollView {
            DSConstrainedContent {
                VStack(spacing: DSSpacing.l) {
                    ForEach(goals) { goal in
                        NavigationLink {
                            GoalDetailView(goal: goal)
                        } label: {
                            DSCard {
                                VStack(alignment: .leading, spacing: DSSpacing.s) {
                                    Text(goal.title).font(.dsHeadline)
                                    Text(goal.summary).font(.dsCaption).foregroundStyle(DS.Color.textSecondary)
                                }
                            }
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(DSSpacing.l)
            }
        }
        .background(DS.Color.background)
        .navigationTitle("Goals")
    }
}
