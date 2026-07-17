import { User } from "../models/user";

export class UserService {
  private users: Map<string, User> = new Map();

  createUser(user: User): User {
    this.users.set(user.id, user);
    return user;
  }

  getUserById(id: string): User | undefined {
    return this.users.get(id);
  }

  listUsers(): User[] {
    return Array.from(this.users.values());
  }
}
