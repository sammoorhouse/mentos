import SwiftUI

struct BreakthroughCard: View {
    let payload: BreakthroughPayload
    let onRealignGoals: () -> Void

    var body: some View {
        Surface {
            VStack(alignment: .leading, spacing: Tokens.Spacing.s) {
                Text("Unlocked")
                    .font(Typography.caption)
                    .foregroundStyle(Tokens.Color.accent)
                Text(payload.title)
                    .font(Typography.title)
                    .foregroundStyle(Tokens.Color.textPrimary)
                Text(payload.metric)
                    .font(Typography.display)
                    .fontWeight(.semibold)
                    .minimumScaleFactor(0.7)
                    .lineLimit(1)
                    .foregroundStyle(Tokens.Color.accent)
                Text(payload.detail)
                    .font(Typography.body)
                    .foregroundStyle(Tokens.Color.textSecondary)
                    .padding(.bottom, Tokens.Spacing.s)

                Button(payload.ctaTitle, action: onRealignGoals)
                    .font(Typography.body.weight(.semibold))
                    .foregroundStyle(Tokens.Color.background)
                    .padding(.horizontal, Tokens.Spacing.l)
                    .padding(.vertical, Tokens.Spacing.s)
                    .background(Tokens.Color.accent)
                    .clipShape(Capsule())
            }
        }
    }
}
