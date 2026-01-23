import type { ReactNode } from "react";

interface Props {
  /** Controls that sit in the title strip, on the right. */
  topRight?: ReactNode;
  /** Changing this key replays the entrance animation. */
  viewKey: string;
  animation: "right" | "left" | "up";
  /** Widen the column past the default cap on very wide windows. */
  wide?: boolean;
  children: ReactNode;
}

const ANIMATION = {
  right: "animate-page-right",
  left: "animate-page-left",
  up: "animate-page-up",
} as const;

/** The window itself: atmosphere, the strip that replaces the title bar, and
 * the scrolling column everything else is drawn into.
 *
 * Onboarding renders inside this too. It is the same window, so it has to keep
 * the same background and the same drag region; a first screen that cannot be
 * moved is the kind of detail that gives away a web page in a frame.
 */
export default function Shell({ topRight, viewKey, animation, wide, children }: Props) {
  return (
    <div className="relative flex h-full flex-col overflow-hidden">
      <div
        aria-hidden="true"
        className="orb animate-drift-a -left-32 -top-40 h-[300px] w-[300px] sm:h-[460px] sm:w-[460px]"
      >
        <div
          className="orb-bloom"
          style={{ background: "radial-gradient(circle, #a7e5d3 0%, transparent 70%)" }}
        />
      </div>
      <div
        aria-hidden="true"
        className="orb animate-drift-b -right-28 bottom-0 h-[260px] w-[260px] sm:h-[420px] sm:w-[420px]"
      >
        <div
          className="orb-bloom orb-bloom-slow"
          style={{ background: "radial-gradient(circle, #f4c5a8 0%, transparent 70%)" }}
        />
      </div>

      <div
        data-tauri-drag-region
        className="relative flex h-11 shrink-0 items-center justify-end px-6 sm:px-10 lg:px-16"
      >
        {topRight}
      </div>

      <main className="scroll-clean relative min-h-0 flex-1 overflow-y-auto px-6 pb-16 sm:px-10 lg:px-16">
        <div
          key={viewKey}
          className={`mx-auto max-w-content ${wide ? "wide:max-w-[1500px]" : ""} ${
            ANIMATION[animation]
          }`}
        >
          {children}
        </div>
      </main>
    </div>
  );
}
