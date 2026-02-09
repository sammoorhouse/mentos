import SwiftUI

struct SettingsView: View {
    var body: some View {
        ScrollView {
            DSConstrainedContent {
                VStack(spacing: DSSpacing.l) {
                    DSCard(title: "Debug") {
                        Text("Server: http://localhost:8000")
                            .font(.dsMonospace)
                    }
                    DSButton(title: "Disconnect Monzo", variant: .secondary, action: {})
                    DSButton(title: "Sign out", variant: .destructive, action: {})
                }
                .padding(DSSpacing.l)
            }
        }
        .background(DS.Color.background)
        .navigationTitle("Settings")
    }
}
