import SwiftUI

struct WelcomeView: View {
    var onContinue: () -> Void

    var body: some View {
        OnboardingShell(
            title: "Welcome",
            subtitle: "Mentos helps you build money habits with calm, weekly nudges.",
            buttonTitle: "Continue",
            action: onContinue
        ) {
            DSCard {
                Text("A cleaner financial pulse, without the noise.")
                    .font(.dsBody)
                    .foregroundStyle(DS.Color.textSecondary)
            }
        }
    }
}
