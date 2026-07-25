import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { COOKIE_NOMBRE, COOKIE_VALOR } from "@/lib/auth";

export default async function Home() {
  const cookieStore = await cookies();
  const autenticado = cookieStore.get(COOKIE_NOMBRE)?.value === COOKIE_VALOR;
  redirect(autenticado ? "/dashboard" : "/login");
}
