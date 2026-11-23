/** Landing page after sign-in, by role. */
export function homeFor(role: string) {
  return role === "parent" ? "/family" : "/insights";
}
