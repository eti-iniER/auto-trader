interface UserAdminDetails {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  role: "USER" | "ADMIN";
  createdAt: Date;
  lastLogin: Date;
  mode: "DEMO" | "LIVE";
}
