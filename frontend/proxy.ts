import { NextRequest, NextResponse } from "next/server";
import { COOKIE_NOMBRE, COOKIE_VALOR } from "@/lib/auth";

export function proxy(request: NextRequest) {
  const autenticado = request.cookies.get(COOKIE_NOMBRE)?.value === COOKIE_VALOR;
  const { pathname } = request.nextUrl;

  if (pathname.startsWith("/dashboard") && !autenticado) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (pathname === "/login" && autenticado) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/login"],
};
