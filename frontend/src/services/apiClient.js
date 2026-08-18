const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

export function getGoogleLoginUrl() {
  return `${API_BASE_URL}/auth/google/login`;
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers ?? {});

  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  let data = null;
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    data = await response.json();
  }

  if (!response.ok) {
    const message = getErrorMessage(data, response.status);
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

function getErrorMessage(data, status) {
  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => item.msg).join(" ");
  }

  if (typeof data?.detail === "string") {
    return data.detail;
  }

  if (status === 401) {
    return "Invalid email or password.";
  }

  return "Something went wrong. Please try again.";
}

export const apiClient = {
  register(payload) {
    return request("/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },

  login(email, password) {
    const formData = new URLSearchParams();
    formData.set("username", email);
    formData.set("password", password);

    return request("/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    });
  },

  getCurrentUser() {
    return request("/auth/me");
  },

  getProjects() {
    return request("/projects");
  },

  getProject(projectId) {
    return request(`/projects/${projectId}`);
  },

  createProject(payload) {
    return request("/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },

  updateProject(projectId, payload) {
    return request(`/projects/${projectId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },

  deleteProject(projectId) {
    return request(`/projects/${projectId}`, {
      method: "DELETE",
    });
  },

  getProjectSites(projectId) {
    return request(`/projects/${projectId}/sites`);
  },

  createSite(projectId, payload) {
    return request(`/projects/${projectId}/sites`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },

  getSite(siteId) {
    return request(`/sites/${siteId}`);
  },

  updateSite(siteId, payload) {
    return request(`/sites/${siteId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },

  deleteSite(siteId) {
    return request(`/sites/${siteId}`, {
      method: "DELETE",
    });
  },

  getEnvironmentalData(siteId) {
    return request(`/sites/${siteId}/environmental-data`);
  },

  collectEnvironmentalData(siteId) {
    return request(`/sites/${siteId}/environmental-data/collect`, {
      method: "POST",
    });
  },

  createEnvironmentalData(siteId, data) {
    return request(`/sites/${siteId}/environmental-data`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
  },
};
