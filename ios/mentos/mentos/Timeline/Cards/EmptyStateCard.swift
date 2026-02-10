import SwiftUI

struct EmptyStateCard: View {
    let payload: EmptyStatePayload

    var body: some View {
        Surface {
            VStack(alignment: .leading, spacing: Tokens.Spacing.s) {
                Text(payload.title)
                    .font(Typography.title)
                    .foregroundStyle(Tokens.Color.textPrimary)
                Text(payload.message)
                    .font(Typography.body)
                    .foregroundStyle(Tokens.Color.textSecondary)
            }
        }
    }
}
