"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { HiOutlineArrowRightOnRectangle } from "react-icons/hi2";
import { logout } from "@/app/login/actions";

// Navbar por paneles — hoy "Campañas" y "Configuración", pero la lista está
// hecha para agregar paneles nuevos sin rehacer el layout (ej. "Monitoreo").
const PANELES = [
  { href: "/dashboard", label: "Campañas" },
  { href: "/dashboard/configuracion", label: "Configuración" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[#fffef7] flex">
      <aside className="w-56 shrink-0 bg-[#0a0a0a] flex flex-col h-screen sticky top-0">
        <div className="px-5 py-5 border-b border-white/10">
          <span className="text-sm font-semibold text-[#fffef7]">Colsubsidio</span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {PANELES.map((p) => (
            <Link
              key={p.href}
              href={p.href}
              className={clsx(
                "block px-3 py-2 rounded-lg text-sm transition-colors",
                pathname === p.href ? "bg-white/10 text-[#fffef7]" : "text-neutral-400 hover:bg-white/5 hover:text-neutral-100"
              )}
            >
              {p.label}
            </Link>
          ))}
        </nav>

        <div className="px-3 py-4 border-t border-white/10">
          <form action={logout}>
            <button
              type="submit"
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-neutral-400 hover:bg-white/5 hover:text-neutral-100 transition-colors"
            >
              Cerrar sesión
              <HiOutlineArrowRightOnRectangle className="w-4 h-4" />
            </button>
          </form>
        </div>
      </aside>

      <main className="flex-1 px-10 py-10 overflow-y-auto">{children}</main>
    </div>
  );
}
