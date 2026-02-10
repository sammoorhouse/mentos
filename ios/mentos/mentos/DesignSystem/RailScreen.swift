import SwiftUI

struct RailScreen<Content: View>: View {
    let title: String
    let statusText: String
    let content: Content

    init(title: String, statusText: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.statusText = statusText
        self.content = content()
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Tokens.Spacing.l) {
                VStack(alignment: .leading, spacing: Tokens.Spacing.s) {
                    Text(title)
                        .font(Typography.display)
                        .trackingDisplay()
                        .foregroundStyle(Tokens.Color.textPrimary)
                    Text(statusText)
                        .font(Typography.body)
                        .foregroundStyle(Tokens.Color.textSecondary)
                }
                .padding(.horizontal, Tokens.Spacing.l)
                .padding(.top, Tokens.Spacing.s)

                content
            }
            .padding(.bottom, Tokens.Spacing.xxl)
        }
        .scrollIndicators(.hidden)
        .background(Tokens.Color.background.ignoresSafeArea())
    }
}
