import React from 'react';

export function Section({ title, subtitle, icon, count, children }: {
  title: string;
  subtitle?: string;
  icon: string;
  count?: number;
  children: React.ReactNode;
}) {
  return (
    <section className="animate-slide-up">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">{icon}</span>
        <h2 className="text-lg font-bold text-white">{title}</h2>
        {count !== undefined && (
          <span className="text-xs bg-zinc-700 text-zinc-300 px-2 py-0.5 rounded-full font-mono">{count}</span>
        )}
      </div>
      {subtitle && <p className="text-sm text-zinc-500 mb-4 -mt-2">{subtitle}</p>}
      {children}
    </section>
  );
}
