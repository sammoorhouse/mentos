import SwiftUI

struct DSRow: View {
    var icon: String
    var title: String
    var subtitle: String
    var trailingText: String? = nil
    var showChevron: Bool = true

    var body: some View {
        HStack(spacing: DSSpacing.m) {
            Image(systemName: icon)
                .frame(width: 22)
                .foregroundStyle(.accent)
            VStack(alignment: .leading, spacing: DSSpacing.xs) {
                Text(title).font(.dsBody.weight(.semibold))
                Text(subtitle).font(.dsCaption).foregroundStyle(DS.Color.textSecondary)
            }
            Spacer()
            if let trailingText {
                Text(trailingText).font(.dsCaption).foregroundStyle(DS.Color.textSecondary)
            }
            if showChevron {
                Image(systemName: "chevron.right").font(.caption).foregroundStyle(DS.Color.textSecondary)
            }
        }
        .padding(.vertical, DSSpacing.m)
        .padding(.horizontal, DSSpacing.l)
        .background(DS.Color.surface)
        .overlay(alignment: .bottom) { DSSeparator() }
    }
}
