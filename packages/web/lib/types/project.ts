export interface Project {
  id: string;
  user_id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface ProjectCreate {
  name: string;
  user_id: string;
}

export interface ProjectUpdate {
  name?: string;
  status?: string;
}
