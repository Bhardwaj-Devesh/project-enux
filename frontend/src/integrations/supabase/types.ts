export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instanciate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "12.2.12 (cd3cf9e)"
  }
  public: {
    Tables: {
      asset_versions: {
        Row: {
          asset_id: string | null
          content_diff: string | null
          created_at: string | null
          id: string
          operation: string
          version_id: string | null
        }
        Insert: {
          asset_id?: string | null
          content_diff?: string | null
          created_at?: string | null
          id?: string
          operation: string
          version_id?: string | null
        }
        Update: {
          asset_id?: string | null
          content_diff?: string | null
          created_at?: string | null
          id?: string
          operation?: string
          version_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "asset_versions_asset_id_fkey"
            columns: ["asset_id"]
            isOneToOne: false
            referencedRelation: "playbook_assets"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "asset_versions_version_id_fkey"
            columns: ["version_id"]
            isOneToOne: false
            referencedRelation: "playbook_versions"
            referencedColumns: ["id"]
          },
        ]
      }
      commits: {
        Row: {
          author_id: string | null
          commit_type: string | null
          created_at: string
          diff_summary: string | null
          file_id: string | null
          id: string
          repo_id: string | null
          version_from: string | null
          version_to: string | null
        }
        Insert: {
          author_id?: string | null
          commit_type?: string | null
          created_at?: string
          diff_summary?: string | null
          file_id?: string | null
          id?: string
          repo_id?: string | null
          version_from?: string | null
          version_to?: string | null
        }
        Update: {
          author_id?: string | null
          commit_type?: string | null
          created_at?: string
          diff_summary?: string | null
          file_id?: string | null
          id?: string
          repo_id?: string | null
          version_from?: string | null
          version_to?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "commits_author_id_fkey"
            columns: ["author_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "commits_repo_id_fkey"
            columns: ["repo_id"]
            isOneToOne: false
            referencedRelation: "playbooks"
            referencedColumns: ["id"]
          },
        ]
      }
      content_reports: {
        Row: {
          created_at: string | null
          description: string | null
          id: string
          reason: string
          reported_playbook_id: string | null
          reporter_id: string | null
          resolved_at: string | null
          resolved_by: string | null
          status: string | null
        }
        Insert: {
          created_at?: string | null
          description?: string | null
          id?: string
          reason: string
          reported_playbook_id?: string | null
          reporter_id?: string | null
          resolved_at?: string | null
          resolved_by?: string | null
          status?: string | null
        }
        Update: {
          created_at?: string | null
          description?: string | null
          id?: string
          reason?: string
          reported_playbook_id?: string | null
          reporter_id?: string | null
          resolved_at?: string | null
          resolved_by?: string | null
          status?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "content_reports_reported_playbook_id_fkey"
            columns: ["reported_playbook_id"]
            isOneToOne: false
            referencedRelation: "playbooks"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "content_reports_reporter_id_fkey"
            columns: ["reporter_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "content_reports_resolved_by_fkey"
            columns: ["resolved_by"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      file_versions: {
        Row: {
          committed_by: string | null
          created_at: string
          diff_summary: string | null
          file_id: string | null
          id: string
          storage_path: string | null
          version_id: string
        }
        Insert: {
          committed_by?: string | null
          created_at?: string
          diff_summary?: string | null
          file_id?: string | null
          id?: string
          storage_path?: string | null
          version_id: string
        }
        Update: {
          committed_by?: string | null
          created_at?: string
          diff_summary?: string | null
          file_id?: string | null
          id?: string
          storage_path?: string | null
          version_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "file_versions_committed_by_fkey"
            columns: ["committed_by"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "file_versions_file_id_fkey"
            columns: ["file_id"]
            isOneToOne: false
            referencedRelation: "playbook_assets"
            referencedColumns: ["id"]
          },
        ]
      }
      playbook_assets: {
        Row: {
          asset_type: Database["public"]["Enums"]["asset_type"]
          content: string | null
          created_at: string | null
          current_version: string | null
          file_name: string
          file_path: string
          id: string
          playbook_id: string | null
          size_bytes: number | null
          storage_path: string | null
          updated_at: string | null
          versions: string[] | null
        }
        Insert: {
          asset_type: Database["public"]["Enums"]["asset_type"]
          content?: string | null
          created_at?: string | null
          current_version?: string | null
          file_name: string
          file_path: string
          id?: string
          playbook_id?: string | null
          size_bytes?: number | null
          storage_path?: string | null
          updated_at?: string | null
          versions?: string[] | null
        }
        Update: {
          asset_type?: Database["public"]["Enums"]["asset_type"]
          content?: string | null
          created_at?: string | null
          current_version?: string | null
          file_name?: string
          file_path?: string
          id?: string
          playbook_id?: string | null
          size_bytes?: number | null
          storage_path?: string | null
          updated_at?: string | null
          versions?: string[] | null
        }
        Relationships: [
          {
            foreignKeyName: "playbook_assets_playbook_id_fkey"
            columns: ["playbook_id"]
            isOneToOne: false
            referencedRelation: "playbooks"
            referencedColumns: ["id"]
          },
        ]
      }
      playbook_reviews: {
        Row: {
          created_at: string | null
          id: string
          playbook_id: string | null
          rating: number | null
          review_text: string | null
          reviewer_id: string | null
          updated_at: string | null
        }
        Insert: {
          created_at?: string | null
          id?: string
          playbook_id?: string | null
          rating?: number | null
          review_text?: string | null
          reviewer_id?: string | null
          updated_at?: string | null
        }
        Update: {
          created_at?: string | null
          id?: string
          playbook_id?: string | null
          rating?: number | null
          review_text?: string | null
          reviewer_id?: string | null
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "playbook_reviews_playbook_id_fkey"
            columns: ["playbook_id"]
            isOneToOne: false
            referencedRelation: "playbooks"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "playbook_reviews_reviewer_id_fkey"
            columns: ["reviewer_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      playbook_stars: {
        Row: {
          created_at: string | null
          id: string
          playbook_id: string | null
          user_id: string | null
        }
        Insert: {
          created_at?: string | null
          id?: string
          playbook_id?: string | null
          user_id?: string | null
        }
        Update: {
          created_at?: string | null
          id?: string
          playbook_id?: string | null
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "playbook_stars_playbook_id_fkey"
            columns: ["playbook_id"]
            isOneToOne: false
            referencedRelation: "playbooks"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "playbook_stars_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      playbook_tags: {
        Row: {
          id: string
          playbook_id: string | null
          tag_id: string | null
        }
        Insert: {
          id?: string
          playbook_id?: string | null
          tag_id?: string | null
        }
        Update: {
          id?: string
          playbook_id?: string | null
          tag_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "playbook_tags_playbook_id_fkey"
            columns: ["playbook_id"]
            isOneToOne: false
            referencedRelation: "playbooks"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "playbook_tags_tag_id_fkey"
            columns: ["tag_id"]
            isOneToOne: false
            referencedRelation: "tags"
            referencedColumns: ["id"]
          },
        ]
      }
      playbook_versions: {
        Row: {
          author_id: string | null
          commit_hash: string
          commit_message: string
          created_at: string | null
          id: string
          parent_version_id: string | null
          playbook_id: string | null
        }
        Insert: {
          author_id?: string | null
          commit_hash: string
          commit_message: string
          created_at?: string | null
          id?: string
          parent_version_id?: string | null
          playbook_id?: string | null
        }
        Update: {
          author_id?: string | null
          commit_hash?: string
          commit_message?: string
          created_at?: string | null
          id?: string
          parent_version_id?: string | null
          playbook_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "playbook_versions_author_id_fkey"
            columns: ["author_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "playbook_versions_parent_version_id_fkey"
            columns: ["parent_version_id"]
            isOneToOne: false
            referencedRelation: "playbook_versions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "playbook_versions_playbook_id_fkey"
            columns: ["playbook_id"]
            isOneToOne: false
            referencedRelation: "playbooks"
            referencedColumns: ["id"]
          },
        ]
      }
      playbooks: {
        Row: {
          author_id: string | null
          created_at: string | null
          default_branch: string | null
          description: string | null
          forked_from: string | null
          forks_count: number | null
          id: string
          language: string | null
          license: string | null
          size_bytes: number | null
          stage: string | null
          stars_count: number | null
          structure: Json | null
          title: string
          updated_at: string | null
          visibility: Database["public"]["Enums"]["playbook_visibility"] | null
        }
        Insert: {
          author_id?: string | null
          created_at?: string | null
          default_branch?: string | null
          description?: string | null
          forked_from?: string | null
          forks_count?: number | null
          id?: string
          language?: string | null
          license?: string | null
          size_bytes?: number | null
          stage?: string | null
          stars_count?: number | null
          structure?: Json | null
          title: string
          updated_at?: string | null
          visibility?: Database["public"]["Enums"]["playbook_visibility"] | null
        }
        Update: {
          author_id?: string | null
          created_at?: string | null
          default_branch?: string | null
          description?: string | null
          forked_from?: string | null
          forks_count?: number | null
          id?: string
          language?: string | null
          license?: string | null
          size_bytes?: number | null
          stage?: string | null
          stars_count?: number | null
          structure?: Json | null
          title?: string
          updated_at?: string | null
          visibility?: Database["public"]["Enums"]["playbook_visibility"] | null
        }
        Relationships: [
          {
            foreignKeyName: "playbooks_author_id_fkey"
            columns: ["author_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "playbooks_forked_from_fkey"
            columns: ["forked_from"]
            isOneToOne: false
            referencedRelation: "playbooks"
            referencedColumns: ["id"]
          },
        ]
      }
      profiles: {
        Row: {
          avatar_url: string | null
          bio: string | null
          company: string | null
          created_at: string | null
          full_name: string | null
          id: string
          interests: string[] | null
          last_login: string | null
          location: string | null
          recommender_suggestions: Json | null
          stage: string | null
          updated_at: string | null
          username: string
          website: string | null
        }
        Insert: {
          avatar_url?: string | null
          bio?: string | null
          company?: string | null
          created_at?: string | null
          full_name?: string | null
          id: string
          interests?: string[] | null
          last_login?: string | null
          location?: string | null
          recommender_suggestions?: Json | null
          stage?: string | null
          updated_at?: string | null
          username: string
          website?: string | null
        }
        Update: {
          avatar_url?: string | null
          bio?: string | null
          company?: string | null
          created_at?: string | null
          full_name?: string | null
          id?: string
          interests?: string[] | null
          last_login?: string | null
          location?: string | null
          recommender_suggestions?: Json | null
          stage?: string | null
          updated_at?: string | null
          username?: string
          website?: string | null
        }
        Relationships: []
      }
      pull_request_reviews: {
        Row: {
          comment: string | null
          created_at: string | null
          id: string
          pull_request_id: string | null
          reviewer_id: string | null
          status: string
        }
        Insert: {
          comment?: string | null
          created_at?: string | null
          id?: string
          pull_request_id?: string | null
          reviewer_id?: string | null
          status: string
        }
        Update: {
          comment?: string | null
          created_at?: string | null
          id?: string
          pull_request_id?: string | null
          reviewer_id?: string | null
          status?: string
        }
        Relationships: [
          {
            foreignKeyName: "pull_request_reviews_pull_request_id_fkey"
            columns: ["pull_request_id"]
            isOneToOne: false
            referencedRelation: "pull_requests"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "pull_request_reviews_reviewer_id_fkey"
            columns: ["reviewer_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      pull_requests: {
        Row: {
          additions_count: number | null
          ai_flags: Json | null
          ai_summary: string | null
          author_id: string | null
          closed_at: string | null
          created_at: string | null
          deletions_count: number | null
          description: string | null
          files_changed_count: number | null
          id: string
          merged_at: string | null
          source_branch: string | null
          source_playbook_id: string | null
          status: Database["public"]["Enums"]["pull_request_status"] | null
          target_branch: string | null
          target_playbook_id: string | null
          title: string
          updated_at: string | null
        }
        Insert: {
          additions_count?: number | null
          ai_flags?: Json | null
          ai_summary?: string | null
          author_id?: string | null
          closed_at?: string | null
          created_at?: string | null
          deletions_count?: number | null
          description?: string | null
          files_changed_count?: number | null
          id?: string
          merged_at?: string | null
          source_branch?: string | null
          source_playbook_id?: string | null
          status?: Database["public"]["Enums"]["pull_request_status"] | null
          target_branch?: string | null
          target_playbook_id?: string | null
          title: string
          updated_at?: string | null
        }
        Update: {
          additions_count?: number | null
          ai_flags?: Json | null
          ai_summary?: string | null
          author_id?: string | null
          closed_at?: string | null
          created_at?: string | null
          deletions_count?: number | null
          description?: string | null
          files_changed_count?: number | null
          id?: string
          merged_at?: string | null
          source_branch?: string | null
          source_playbook_id?: string | null
          status?: Database["public"]["Enums"]["pull_request_status"] | null
          target_branch?: string | null
          target_playbook_id?: string | null
          title?: string
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "pull_requests_author_id_fkey"
            columns: ["author_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "pull_requests_source_playbook_id_fkey"
            columns: ["source_playbook_id"]
            isOneToOne: false
            referencedRelation: "playbooks"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "pull_requests_target_playbook_id_fkey"
            columns: ["target_playbook_id"]
            isOneToOne: false
            referencedRelation: "playbooks"
            referencedColumns: ["id"]
          },
        ]
      }
      tags: {
        Row: {
          created_at: string
          id: string
          name: string
        }
        Insert: {
          created_at?: string
          id?: string
          name: string
        }
        Update: {
          created_at?: string
          id?: string
          name?: string
        }
        Relationships: []
      }
      user_roles: {
        Row: {
          created_at: string | null
          id: string
          role: Database["public"]["Enums"]["user_role"]
          user_id: string | null
        }
        Insert: {
          created_at?: string | null
          id?: string
          role?: Database["public"]["Enums"]["user_role"]
          user_id?: string | null
        }
        Update: {
          created_at?: string | null
          id?: string
          role?: Database["public"]["Enums"]["user_role"]
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "user_roles_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      get_user_role: {
        Args: { user_id: string }
        Returns: Database["public"]["Enums"]["user_role"]
      }
      is_playbook_accessible: {
        Args: { playbook_id: string; user_id: string }
        Returns: boolean
      }
    }
    Enums: {
      asset_type: "markdown" | "csv" | "xlsx" | "pptx" | "pdf" | "other"
      playbook_visibility: "public" | "private"
      pull_request_status: "open" | "closed" | "merged" | "draft"
      user_role: "user" | "moderator" | "admin"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      asset_type: ["markdown", "csv", "xlsx", "pptx", "pdf", "other"],
      playbook_visibility: ["public", "private"],
      pull_request_status: ["open", "closed", "merged", "draft"],
      user_role: ["user", "moderator", "admin"],
    },
  },
} as const
