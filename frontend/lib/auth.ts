// Única fuente de la cookie de sesión — antes estaba repetida (literal) en
// proxy.ts, app/page.tsx y app/login/actions.ts, sin ninguna razón para no
// compartirla (los 3 corren en el mismo proceso de Next.js).
export const COOKIE_NOMBRE = "colsubsidio-session";
export const COOKIE_VALOR = "authenticated";
