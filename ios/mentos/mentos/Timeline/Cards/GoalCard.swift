import SwiftUI

struct GoalCard: View {
    let payload: GoalPayload
    let onEditGoals: () -> Void

    var body: some View {
        Surface {
            VStack(alignment: .leading, spacing: Tokens.Spacing.m) {
                HStack {
                    Text(payload.title)
                        .font(Typography.title)
                        .foregroundStyle(Tokens.Color.textPrimary)
                    Spacer()
                    Menu {
                        Button("Edit goals", action: onEditGoals)
                    } label: {
                        Image(systemName: "ellipsis.circle")
                            .foregroundStyle(Tokens.Color.textSecondary)
                    }
                }

                Text(payload.subtitle)
                    .font(Typography.body)
                    .foregroundStyle(Tokens.Color.textSecondary)

                ForEach(payload.goals) { goal in
                    VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
                        HStack {
                            Label(goal.title, systemImage: goal.icon)
                                .font(Typography.body)
                                .foregroundStyle(Tokens.Color.textPrimary)
                            Spacer()
                            Text(goal.progressText)
                                .font(Typography.metric)
                                .foregroundStyle(Tokens.Color.textSecondary)
                        }
                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                Capsule().fill(Tokens.Color.separator)
                                Capsule().fill(Tokens.Color.accent)
                                    .frame(width: geo.size.width * goal.progress)
                            }
                        }
                        .frame(height: 6)
                    }
                }
            }
        }
    }
}
