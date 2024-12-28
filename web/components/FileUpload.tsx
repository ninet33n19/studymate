"use client";

import { useState } from "react";
import { createBrowserClient } from "@supabase/ssr";
import { Database } from "@/types/supabase";

interface FileUploadProps {
  onUploadComplete?: (url: string) => void;
  bucketName?: string;
}

export default function FileUpload({
  onUploadComplete,
  bucketName = "documents",
}: FileUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const supabase = createBrowserClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    try {
      setIsUploading(true);
      setError(null);

      const file = event.target.files?.[0];
      if (!file) return;

      // Validate file type
      if (file.type !== "application/pdf") {
        throw new Error("Only PDF files are allowed");
      }

      // Validate file size (e.g., 5MB limit)
      const maxSize = 5 * 1024 * 1024; // 5MB in bytes
      if (file.size > maxSize) {
        throw new Error("File size must be less than 5MB");
      }

      // Create a unique file name
      const timestamp = new Date().getTime();
      const fileName = `${timestamp}-${file.name}`;

      // Upload file to Supabase storage
      const { data, error: uploadError } = await supabase.storage
        .from(bucketName)
        .upload(fileName, file);

      if (uploadError) {
        throw uploadError;
      }

      // Get public URL
      const {
        data: { publicUrl },
      } = supabase.storage.from(bucketName).getPublicUrl(fileName);

      if (onUploadComplete) {
        onUploadComplete(publicUrl);
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "Error uploading file");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="w-full">
      <label className="block mb-2 text-sm font-medium text-gray-900">
        Upload PDF Document
      </label>
      <input
        type="file"
        onChange={handleFileUpload}
        disabled={isUploading}
        className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none p-2"
        accept=".pdf"
      />
      {isUploading && (
        <div className="mt-2 text-sm text-blue-600">Uploading...</div>
      )}
      {error && <div className="mt-2 text-sm text-red-600">{error}</div>}
    </div>
  );
}
