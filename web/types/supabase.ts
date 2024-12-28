export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      // Add your database tables here
      profiles: {
        Row: {
          id: string;
          created_at: string;
          updated_at: string;
          email: string | null;
          name: string | null;
        };
        Insert: {
          id: string;
          created_at?: string;
          updated_at?: string;
          email?: string | null;
          name?: string | null;
        };
        Update: {
          id?: string;
          created_at?: string;
          updated_at?: string;
          email?: string | null;
          name?: string | null;
        };
      };
      // Add more tables as needed
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      [_ in never]: never;
    };
    Storage: {
      Buckets: {
        documents: {
          Row: {
            id: string;
            name: string;
            owner: string;
            created_at: string;
            updated_at: string;
            size: number;
            mime_type: string;
          };
          Insert: {
            name: string;
            owner?: string;
            mime_type?: string;
          };
          Update: {
            name?: string;
            owner?: string;
            mime_type?: string;
          };
        };
      };
    };
  };
}
