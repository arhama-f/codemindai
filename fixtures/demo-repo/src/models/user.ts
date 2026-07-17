export type UserRole = "admin" | "member" | "guest";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
}
