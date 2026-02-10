import SwiftUI

struct WeeklyProgressCard: View {
    let payload: WeeklyProgressPayload

    var body: some View {
        Surface {
            VStack(alignment: .leading, spacing: Tokens.Spacing.m) {
                Text("This week")
                    .font(Typography.title)
                    .foregroundStyle(Tokens.Color.textPrimary)
                HStack(spacing: Tokens.Spacing.s) {
                    ForEach(Array(payload.progress.enumerated()), id: \.offset) { index, value in
                        VStack(spacing: Tokens.Spacing.xs) {
                            Circle()
                                .fill(value <= 0.01 ? Tokens.Color.separator : Tokens.Color.accent.opacity(value))
                                .frame(width: 16, height: 16)
                            if index < payload.dayLabels.count {
                                Text(payload.dayLabels[index])
                                    .font(Typography.caption)
                                    .foregroundStyle(Tokens.Color.textTertiary)
                            }
                        }
                    }
                }
                Text(payload.summary)
                    .font(Typography.body)
                    .foregroundStyle(Tokens.Color.textSecondary)
            }
        }
    }
}
