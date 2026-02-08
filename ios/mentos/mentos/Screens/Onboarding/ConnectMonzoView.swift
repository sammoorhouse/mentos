import SwiftUI

struct ConnectMonzoView: View {
    var onConnect: () -> Void
    var onSkip: () -> Void

    var body: some View {
        OnboardingShell(
            title: "Connect Monzo",
            subtitle: "Securely connect to unlock weekly insights and progress.",
            buttonTitle: "Connect Monzo",
            action: onConnect
        ) {
            VStack(spacing: DSSpacing.l) {
                DSCard {
                    Text("We only use read access to help you understand patterns and habits.")
                        .font(.dsBody)
                        .foregroundStyle(DS.Color.textSecondary)
                }
                DSButton(title: "Skip for now", variant: .secondary, action: onSkip)
            }
        }
    }
}
