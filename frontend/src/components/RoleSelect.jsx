import { ALL_ROLES } from "../config/roles.js";

export default function RoleSelect({ name, value, onChange, required = false }) {
  return (
    <select name={name} value={value} onChange={onChange} required={required}>
      <option value="">Select Role</option>
      {ALL_ROLES.map((role) => (
        <option key={role} value={role}>
          {role}
        </option>
      ))}
    </select>
  );
}
