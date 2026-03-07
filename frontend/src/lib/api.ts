import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post("/api/v1/auth/refresh/", {
            refresh,
          });
          localStorage.setItem("access_token", data.access);
          if (data.refresh) {
            localStorage.setItem("refresh_token", data.refresh);
          }
          original.headers.Authorization = `Bearer ${data.access}`;
          return api(original);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      } else {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// --- Auth ---
export async function login(username: string, password: string) {
  const { data } = await api.post("/auth/login/", { username, password });
  localStorage.setItem("access_token", data.access);
  localStorage.setItem("refresh_token", data.refresh);
  return data;
}

export async function getMe() {
  const { data } = await api.get("/auth/me/");
  return data;
}

export async function updateProfile(body: {
  first_name?: string;
  last_name?: string;
  email?: string;
}) {
  const { data } = await api.patch("/auth/me/", body);
  return data;
}

export async function changePassword(body: {
  old_password: string;
  new_password: string;
  new_password_confirm: string;
}) {
  const { data } = await api.post("/auth/change-password/", body);
  return data;
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.href = "/login";
}

// --- Projects ---
export async function getProjects() {
  const { data } = await api.get("/projects/");
  return data.results ?? data;
}

export async function getProject(slug: string) {
  const { data } = await api.get(`/projects/${slug}/`);
  return data;
}

export async function createProject(body: {
  name: string;
  description?: string;
  source_language?: string;
}) {
  const { data } = await api.post("/projects/", body);
  return data;
}

export async function deleteProject(slug: string) {
  await api.delete(`/projects/${slug}/`);
}

// --- Resources ---
export async function getResources(slug: string) {
  const { data } = await api.get(`/projects/${slug}/resources/`);
  return data;
}

export async function uploadResource(slug: string, file: File, fileFormat?: string) {
  const form = new FormData();
  form.append("file", file);
  if (fileFormat) form.append("file_format", fileFormat);
  const { data } = await api.post(`/projects/${slug}/resources/upload/`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

// --- Strings ---
export async function getStrings(
  slug: string,
  params?: Record<string, string>
) {
  const { data } = await api.get(`/projects/${slug}/strings/`, { params });
  return data;
}

export async function getStringDetail(slug: string, stringId: string) {
  const { data } = await api.get(`/projects/${slug}/strings/${stringId}/`);
  return data;
}

// --- Translations ---
export async function createTranslation(
  slug: string,
  stringId: string,
  body: { language_code: string; translated_text: string }
) {
  const { data } = await api.post(
    `/projects/${slug}/strings/${stringId}/translations/`,
    body
  );
  return data;
}

export async function updateTranslation(
  slug: string,
  stringId: string,
  language: string,
  body: { translated_text?: string; status?: string }
) {
  const { data } = await api.patch(
    `/projects/${slug}/strings/${stringId}/translations/${language}/`,
    body
  );
  return data;
}

// --- Progress ---
export async function getProgress(slug: string) {
  const { data } = await api.get(`/projects/${slug}/progress/`);
  return data;
}

// --- GitHub Integration ---
export async function getGitHubRepo(slug: string) {
  const { data } = await api.get(`/projects/${slug}/github/`);
  return data;
}

export async function linkGitHubRepo(
  slug: string,
  body: {
    owner: string;
    repo: string;
    branch?: string;
    base_path?: string;
    file_patterns?: string[];
    access_token?: string;
  }
) {
  const { data } = await api.put(`/projects/${slug}/github/`, body);
  return data;
}

export async function unlinkGitHubRepo(slug: string) {
  await api.delete(`/projects/${slug}/github/`);
}

export async function getGitHubFiles(slug: string) {
  const { data } = await api.get(`/projects/${slug}/github/files/`);
  return data;
}

export async function syncGitHubRepo(slug: string) {
  const { data } = await api.post(`/projects/${slug}/github/sync/`);
  return data;
}

// --- Suggestions ---
export async function getSuggestions(
  slug: string,
  stringId: string,
  language: string
) {
  const { data } = await api.get(
    `/projects/${slug}/strings/${stringId}/suggestions/`,
    { params: { language } }
  );
  return data;
}

// --- Users (admin) ---
export interface UserData {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  date_joined: string;
}

export async function createUser(body: {
  username: string;
  email: string;
  password: string;
  role?: string;
  first_name?: string;
  last_name?: string;
}) {
  const { data } = await api.post("/users/", body);
  return data as UserData;
}

export async function getUsers() {
  const { data } = await api.get("/users/");
  return (data.results ?? data) as UserData[];
}

export async function getUser(id: string) {
  const { data } = await api.get(`/users/${id}/`);
  return data as UserData;
}

export async function updateUser(
  id: string,
  body: { role?: string; is_active?: boolean; email?: string; first_name?: string; last_name?: string }
) {
  const { data } = await api.patch(`/users/${id}/`, body);
  return data as UserData;
}
