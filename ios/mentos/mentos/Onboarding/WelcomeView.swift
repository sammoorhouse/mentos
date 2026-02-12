import SwiftUI

struct WelcomeView: View {
    @EnvironmentObject private var session: SessionStore

    var body: some View {
        VStack(spacing: 24) {
            Text("Welcome to Mentos")
                .font(.largeTitle.bold())
            Text("We’ll help you build better spending habits.")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 24)

            Button(action: continueTapped) {
                Text("Continue")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .padding(.horizontal, 32)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }

    private func continueTapped() {
        session.markWelcomeComplete()
        session.onboardingState = .needsMonzo
    }
}
