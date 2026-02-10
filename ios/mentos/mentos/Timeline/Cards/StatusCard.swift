import SwiftUI

struct StatusCard: View {
    let payload: StatusPayload

    var body: some View {
        Surface {
            VStack(alignment: .leading, spacing: Tokens.Spacing.s) {
                Text("Connection")
                    .font(Typography.caption)
                    .trackingCaption()
                    .foregroundStyle(Tokens.Color.textTertiary)
                Text(payload.isConnected ? "\(payload.providerName) connected" : "Connection needed")
                    .font(Typography.title)
                    .trackingTitle()
                    .foregroundStyle(Tokens.Color.textPrimary)
                Text("Last sync \(payload.lastSyncText)")
                    .font(Typography.body)
                    .foregroundStyle(Tokens.Color.textSecondary)
            }
        }
    }
}
