"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { COOKIE_NOMBRE, COOKIE_VALOR } from "@/lib/auth";

const ADMIN_EMAIL = "admin@colsubsidio.com";
const ADMIN_PASSWORD = "admin2024";

export interface LoginState {
  error?: string;
  email?: string;
}

export async function login(_prev: LoginState | undefined, formData: FormData): Promise<LoginState> {
  const email = (formData.get("email") as string).toLowerCase().trim();
  const password = formData.get("password") as string;

  if (email !== ADMIN_EMAIL || password !== ADMIN_PASSWORD) {
    // El email se devuelve para repoblar el campo — que la contraseña sí se
    // borre es esperado (higiene normal de login), pero hacer retipear el
    // correo también es fricción real que un jurado sin contexto lee como
    // "se rompió algo" (encontrado probando con un jurado real).
    return { error: "Correo o contraseña incorrectos", email };
  }

  const cookieStore = await cookies();
  cookieStore.set(COOKIE_NOMBRE, COOKIE_VALOR, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 12,
    sameSite: "lax",
  });

  redirect("/dashboard");
}

export async function logout(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(COOKIE_NOMBRE);
  redirect("/login");
}
