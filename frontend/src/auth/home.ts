/** Landing page after sign-in, by role. */
export function homeFor(role: string) {
  if (role === "parent") return "/family";
  if (role === "admin") return "/admin";
  return "/insights";
}
