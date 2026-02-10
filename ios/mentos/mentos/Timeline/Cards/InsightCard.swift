import SwiftUI

struct InsightCard: View {
    let payload: InsightPayload

    var body: some View {
        Surface {
            VStack(alignment: .leading, spacing: Tokens.Spacing.s) {
                Text("Insight")
                    .font(Typography.caption)
                    .trackingCaption()
                    .foregroundStyle(Tokens.Color.textTertiary)
                Text(payload.title)
                    .font(Typography.title)
                    .foregroundStyle(Tokens.Color.textPrimary)
                Text(payload.body)
                    .font(Typography.body)
                    .foregroundStyle(Tokens.Color.textSecondary)
            }
        }
    }
}
