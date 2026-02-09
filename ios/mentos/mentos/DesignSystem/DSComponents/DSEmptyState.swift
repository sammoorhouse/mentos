import SwiftUI

struct DSEmptyState: View {
    var icon: String
    var title: String
    var message: String

    var body: some View {
        VStack(spacing: DSSpacing.m) {
            Image(systemName: icon).font(.system(size: 30, weight: .medium))
            Text(title).font(.dsHeadline)
            Text(message).font(.dsBody).foregroundStyle(DS.Color.textSecondary).multilineTextAlignment(.center)
        }
        .padding(DSSpacing.xl)
        .frame(maxWidth: .infinity)
        .background(DS.Color.surface, in: RoundedRectangle(cornerRadius: DS.Radius.card, style: .continuous))
    }
}
