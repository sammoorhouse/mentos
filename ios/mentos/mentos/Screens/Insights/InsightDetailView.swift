import SwiftUI

struct InsightDetailView: View {
    var title: String
    var bodyText: String

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Tokens.Spacing.l) {
                Text(title)
                    .font(Typography.display)
                    .trackingDisplay()
                    .foregroundStyle(Tokens.Color.textPrimary)
                Surface {
                    Text(bodyText)
                        .font(Typography.body)
                        .foregroundStyle(Tokens.Color.textSecondary)
                }
            }
            .padding(Tokens.Spacing.l)
        }
        .background(Tokens.Color.background)
    }
}
