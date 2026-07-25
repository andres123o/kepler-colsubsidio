"use client";

import { useActionState, useEffect, useState } from "react";
import { login } from "./actions";
import { MotorAnimation } from "@/components/MotorAnimation";

export default function LoginPage() {
  const [state, action, pending] = useActionState(login, undefined);
  // Controlado a propósito — un jurado probó el login y, al fallar el
  // primer intento, el campo de correo se vació sin ningún aviso claro
  // (React limpia los inputs no controlados después de una form action).
  // Solo la contraseña debe borrarse tras un error; el correo se repuebla.
  const [email, setEmail] = useState("");

  useEffect(() => {
    if (state?.email) setEmail(state.email);
  }, [state]);

  return (
    <main className="h-screen overflow-hidden grid grid-cols-1 md:grid-cols-2">
      <div className="hidden md:block relative h-full overflow-hidden">
        <MotorAnimation />
      </div>

      <div className="h-full overflow-hidden flex items-center justify-center px-6 py-12 bg-[#fffef7]">
        <div className="w-full max-w-sm">
          <h1 className="text-2xl font-semibold text-[#0a0a0a] mb-8">Iniciar sesión</h1>

          <form action={action} className="space-y-6">
            <input
              name="email"
              type="email"
              placeholder="Correo"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full bg-transparent border-0 border-b border-black/15 px-0.5 py-2 text-[#0a0a0a] text-sm placeholder-neutral-400 focus:outline-none focus:border-black/40 transition-colors"
            />
            <input
              name="password"
              type="password"
              placeholder="Contraseña"
              autoComplete="current-password"
              required
              className="w-full bg-transparent border-0 border-b border-black/15 px-0.5 py-2 text-[#0a0a0a] text-sm placeholder-neutral-400 focus:outline-none focus:border-black/40 transition-colors"
            />

            {state?.error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2.5">
                {state.error}
              </p>
            )}

            <button
              type="submit"
              disabled={pending}
              className="w-full bg-[#0a0a0a] hover:bg-neutral-800 disabled:opacity-60 text-[#fffef7] font-medium rounded-lg py-2.5 text-sm transition-colors mt-2"
            >
              {pending ? "Ingresando..." : "Iniciar sesión"}
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}
