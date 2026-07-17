import { User } from "../models/user";

export interface UserCardProps {
  user: User;
  bio: string;
}

export function UserCard({ user, bio }: UserCardProps) {
  return (
    <div className="user-card">
      <h2>{user.name}</h2>
      <p>{user.email}</p>
      <span>{user.role}</span>
      {/* BUG: renders unsanitized bio HTML — planted for a later
          security-review phase. */}
      <div dangerouslySetInnerHTML={{ __html: bio }} />
    </div>
  );
}
