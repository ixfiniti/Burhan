
"use client";

import React from "react";

type MagicCardProps = {
  children: React.ReactNode;
  className?: string;
  gradientSize?: number;
  gradientColor?: string;
  gradientOpacity?: number;
};

export function MagicCard({
  children,
  className = "",
  gradientSize = 220,
  gradientColor = "#b89552",
  gradientOpacity = 0.10,
}: MagicCardProps) {
  const handleMouseMove = (
    event: React.MouseEvent<HTMLDivElement>,
  ) => {
    const target = event.currentTarget;
    const rect = target.getBoundingClientRect();

    target.style.setProperty(
      "--magic-card-x",
      `${event.clientX - rect.left}px`,
    );

    target.style.setProperty(
      "--magic-card-y",
      `${event.clientY - rect.top}px`,
    );
  };

  return (
    <div
      className={`group relative overflow-hidden ${className}`}
      onMouseMove={handleMouseMove}
      style={
        {
          "--magic-card-size": `${gradientSize}px`,
          "--magic-card-color": gradientColor,
          "--magic-card-opacity": gradientOpacity,
        } as React.CSSProperties
      }
    >
      {/* Cursor-following scholarly light */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: `
            radial-gradient(
              ${gradientSize}px circle at var(--magic-card-x) var(--magic-card-y),
              ${gradientColor} 0%,
              transparent 70%
            )
          `,
          opacity: gradientOpacity,
        }}
      />

      {/* Very subtle illuminated border */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 rounded-[inherit] opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: `
            radial-gradient(
              ${Math.max(gradientSize * 0.65, 120)}px circle
              at var(--magic-card-x) var(--magic-card-y),
              ${gradientColor},
              transparent 70%
            )
          `,
          opacity: gradientOpacity * 0.7,
          maskImage:
            "linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0)",
          maskComposite: "exclude",
          padding: "1px",
        }}
      />

      <div className="relative z-10 h-full">
        {children}
      </div>
    </div>
  );
}

