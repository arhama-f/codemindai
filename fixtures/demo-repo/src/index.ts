import { add, divide } from "./utils/math";
import { capitalize } from "./utils/string";
import { User } from "./models/user";
import { UserService } from "./services/userService";

const service = new UserService();

const demoUser: User = {
  id: "1",
  name: capitalize("ada lovelace"),
  email: "ada@example.com",
  role: "admin",
};

service.createUser(demoUser);

console.log(add(2, 3));
console.log(divide(10, 2));
