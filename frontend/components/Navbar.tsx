"use client";

import { Menu, Newspaper, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { navigationItems } from "@/lib/navigation";

export function Navbar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
      <nav
        aria-label="Primary navigation"
        className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8"
      >
        <Link href="/" className="flex items-center gap-3" onClick={() => setIsOpen(false)}>
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-ink text-white">
            <Newspaper aria-hidden="true" className="h-5 w-5" />
          </span>
          <span className="min-w-0 text-sm font-semibold leading-tight text-ink sm:text-base">
            AI News Credibility
          </span>
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {navigationItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-md px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? "bg-slate-100 text-ink"
                    : "text-slate-600 hover:bg-slate-50 hover:text-ink"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </div>

        <button
          type="button"
          aria-label={isOpen ? "Close menu" : "Open menu"}
          className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-200 text-slate-700 md:hidden"
          onClick={() => setIsOpen((current) => !current)}
        >
          {isOpen ? <X aria-hidden="true" className="h-5 w-5" /> : <Menu aria-hidden="true" className="h-5 w-5" />}
        </button>
      </nav>

      {isOpen ? (
        <div className="border-t border-slate-200 bg-white md:hidden">
          <div className="mx-auto grid w-full max-w-7xl gap-1 px-4 py-3 sm:px-6">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsOpen(false)}
                  className={`rounded-md px-3 py-3 text-sm font-medium ${
                    isActive ? "bg-slate-100 text-ink" : "text-slate-600"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      ) : null}
    </header>
  );
}

