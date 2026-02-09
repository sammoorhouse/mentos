import SwiftUI

struct OnboardingShell<Content: View>: View {
    var title: String
    var subtitle: String
    var buttonTitle: String
    var isButtonEnabled: Bool = true
    var action: () -> Void
    @ViewBuilder var content: Content

    var body: some View {
        VStack(spacing: DSSpacing.l) {
            DSConstrainedContent {
                VStack(alignment: .leading, spacing: DSSpacing.s) {
                    Text(title).font(.dsTitle)
                    Text(subtitle).font(.dsBody).foregroundStyle(DS.Color.textSecondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding(.top, DSSpacing.xl)

            DSConstrainedContent { content }
            Spacer(minLength: DSSpacing.l)
            DSConstrainedContent {
                DSButton(title: buttonTitle, isEnabled: isButtonEnabled, action: action)
            }
        }
        .padding(.horizontal, DSSpacing.l)
        .padding(.bottom, DSSpacing.l)
        .background(DS.Color.background.ignoresSafeArea())
        .animation(DS.Animation.spring, value: isButtonEnabled)
    }
}
