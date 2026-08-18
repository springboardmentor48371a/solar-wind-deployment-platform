// Mirrors backend/app/authz.py's role matrix. The backend is the real
// enforcement point — every one of these checks is re-verified server
// side on every request — but the UI needs the same logic so it never
// shows a "Create" or "Refresh" button to a role that will just get a
// 403 back. Showing a button that always fails is its own kind of bug.

export const FULL_ACCESS_ROLES = ['Administrator', 'Project Manager']
export const READ_ONLY_OVERSIGHT_ROLES = ['Investor / Developer', 'Government / Regulator']
export const READ_ALL_ROLES = [...FULL_ACCESS_ROLES, 'GIS Analyst', ...READ_ONLY_OVERSIGHT_ROLES]
export const ANALYSIS_ROLES = [...FULL_ACCESS_ROLES, 'GIS Analyst']
export const CAN_CREATE_ROLES = ['Renewable Energy Planner', 'Project Manager', 'Administrator']

export function canCreate(user) {
  return Boolean(user) && CAN_CREATE_ROLES.includes(user.role)
}

export function canWriteProject(user, project) {
  if (!user || !project) return false
  if (FULL_ACCESS_ROLES.includes(user.role)) return true
  return project.owner_id === user.id && CAN_CREATE_ROLES.includes(user.role)
}

export function canRunAnalysis(user, project) {
  if (!user || !project) return false
  if (ANALYSIS_ROLES.includes(user.role)) return true
  return project.owner_id === user.id && CAN_CREATE_ROLES.includes(user.role)
}
