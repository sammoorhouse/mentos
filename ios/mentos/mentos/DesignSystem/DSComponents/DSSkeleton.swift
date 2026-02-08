import SwiftUI

struct DSSkeleton: View {
    var height: CGFloat = 60

    var body: some View {
        RoundedRectangle(cornerRadius: DS.Radius.card, style: .continuous)
            .fill(DS.Color.surfaceElevated)
            .frame(height: height)
            .overlay {
                RoundedRectangle(cornerRadius: DS.Radius.card, style: .continuous)
                    .fill(.white.opacity(0.08))
            }
            .redacted(reason: .placeholder)
    }
}
