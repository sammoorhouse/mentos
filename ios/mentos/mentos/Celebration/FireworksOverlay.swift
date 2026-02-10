import SwiftUI

struct FireworksOverlay: View {
    let isActive: Bool
    let duration: TimeInterval = 1.2

    var body: some View {
        SwiftUI.TimelineView(.animation) { context in
            Canvas { canvas, size in
                guard isActive else { return }
                let t = context.date.timeIntervalSinceReferenceDate.truncatingRemainder(dividingBy: duration)
                let progress = t / duration
                for index in 0..<36 {
                    let angle = Double(index) / 36.0 * .pi * 2
                    let distance = (size.width * 0.18) * progress
                    let x = size.width * 0.5 + CGFloat(cos(angle) * distance)
                    let y = size.height * 0.25 + CGFloat(sin(angle) * distance)
                    let alpha = max(0, 1 - progress)
                    let rect = CGRect(x: x, y: y, width: 3, height: 3)
                    canvas.fill(Path(ellipseIn: rect), with: .color(Tokens.Color.accent.opacity(alpha)))
                }
            }
        }
        .allowsHitTesting(false)
        .ignoresSafeArea()
    }
}
