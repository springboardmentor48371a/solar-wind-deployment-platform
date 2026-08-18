import { ALL_ROLES } from "./roles.js";

export const navigationItems = [
  {
    label: "Dashboard",
    path: "/app/dashboard",
    allowedRoles: ALL_ROLES,
  },
  {
    label: "Projects",
    path: "/app/projects",
    allowedRoles: ALL_ROLES,
  },
  {
    label: "Sites",
    path: null,
    allowedRoles: ALL_ROLES,
    disabledText: "Managed inside projects",
  },
  {
    label: "Profile",
    path: "/profile",
    allowedRoles: ALL_ROLES,
  },
];
