import SwiftUI

struct DSCard<Content: View>: View {
    var title: String? = nil
    var actionTitle: String? = nil
    var action: (() -> Void)? = nil
    var tapAction: (() -> Void)? = nil
    @ViewBuilder var content: Content

    var body: some View {
        let card = VStack(alignment: .leading, spacing: DSSpacing.m) {
            if title != nil || actionTitle != nil {
                HStack {
                    if let title {
                        Text(title)
                            .font(.dsHeadline)
                            .foregroundStyle(DS.Color.textPrimary)
                    }
                    Spacer()
                    if let actionTitle, let action {
                        Button(actionTitle, action: action)
                            .font(.dsCaption)
                    }
                }
            }
            content
        }
        .padding(DSSpacing.l)
        .background(DS.Color.surface, in: RoundedRectangle(cornerRadius: DS.Radius.card, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: DS.Radius.card, style: .continuous).stroke(DS.Color.separator.opacity(0.35), lineWidth: 0.5))

        if let tapAction {
            Button(action: tapAction) {
                card
            }
            .buttonStyle(.plain)
        } else {
            card
        }
    }
}
